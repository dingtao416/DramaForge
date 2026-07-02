"""Persistent media generation job service."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_hub.media_adapters import MediaProviderSettings, MediaRequest, get_media_adapter
from app.core.config import settings
from app.models.media_generation import (
    AIModelConfig,
    AIProviderConfig,
    MediaCapability,
    MediaGenerationJob,
    MediaJobStatus,
)
from app.services.storage import storage
from app.services.user_model_resolver import ResolvedModel, user_model_resolver


def _friendly_media_error(error: Exception | str) -> str:
    text = str(error)
    if "Concurrency limit exceeded" in text or "rate_limit_error" in text or "当前图片生成并发已满" in text:
        return "当前图片生成并发已满，请稍后重试。"
    if "images-only group" in text or "/v1/images/generations" in text:
        return "当前图片模型密钥只能用于图片接口，请关闭聊天回退后重试。"
    return text


class MediaGenerationService:
    async def mark_job_cancelled(
        self,
        *,
        db: AsyncSession,
        job_id: int,
    ) -> MediaGenerationJob:
        job = await db.get(MediaGenerationJob, job_id)
        if not job:
            raise ValueError(f"Media generation job {job_id} not found")
        job.status = MediaJobStatus.CANCELLED
        job.progress = max(job.progress or 0, 100)
        job.error = None
        await db.flush()
        return job

    async def create_job(
        self,
        *,
        db: AsyncSession,
        user_id: int,
        capability: str,
        prompt: str,
        output_path: str,
        model_hint: str | None = None,
        request_json: dict[str, Any] | None = None,
    ) -> MediaGenerationJob:
        resolved = await user_model_resolver.resolve(db, user_id, capability, model_hint=model_hint)
        job_request = {"prompt": prompt, **(request_json or {})}
        job = MediaGenerationJob(
            user_id=user_id,
            capability=MediaCapability(capability),
            provider_id=resolved.provider_id,
            model_id=resolved.model_id,
            status=MediaJobStatus.QUEUED,
            progress=0,
            request_json=job_request,
        )
        db.add(job)
        await db.flush()

        job_request["_output_path"] = str(self._output_path(job, output_path))
        job.request_json = job_request
        await db.flush()
        return job

    async def create_and_run(
        self,
        *,
        db: AsyncSession,
        user_id: int,
        capability: str,
        prompt: str,
        output_path: str,
        model_hint: str | None = None,
        request_json: dict[str, Any] | None = None,
    ) -> MediaGenerationJob:
        job = await self.create_job(
            db=db,
            user_id=user_id,
            capability=capability,
            prompt=prompt,
            output_path=output_path,
            model_hint=model_hint,
            request_json=request_json,
        )
        try:
            await self.run_existing_job(db=db, job=job)
        except Exception as e:
            await db.refresh(job)
            if job.status == MediaJobStatus.CANCELLED:
                return job
            job.status = MediaJobStatus.FAILED
            job.error = _friendly_media_error(e)[:2000]
            job.progress = 100
            await db.flush()
        return job

    async def run_existing_job(
        self,
        *,
        db: AsyncSession,
        job: MediaGenerationJob,
        resolved: ResolvedModel | None = None,
        output_path: str | None = None,
    ) -> MediaGenerationJob:
        await db.refresh(job)
        if job.status == MediaJobStatus.CANCELLED:
            return job

        resolved = resolved or await self._resolve_job_model(db, job)
        output_path = output_path or job.request_json.get("_output_path")
        if not output_path:
            output_path = str(self._output_path(job, f"job_pending.{job.capability.value}"))

        adapter_config = dict(resolved.config or {})
        adapter_config["model_capabilities"] = resolved.capabilities or {}
        adapter = get_media_adapter(
            MediaProviderSettings(
                provider_type=resolved.provider_type or "openai_compatible",
                auth_type=resolved.auth_type or "bearer",
                base_url=resolved.base_url or "",
                api_key=resolved.api_key or "",
                headers=resolved.headers or {},
                config=adapter_config,
            )
        )
        request = MediaRequest(
            prompt=job.request_json.get("prompt", ""),
            model_id=resolved.model_id,
            size=job.request_json.get("size") or settings.image_size,
            resolution=job.request_json.get("resolution") or settings.video_size,
            duration=job.request_json.get("duration") or settings.video_seconds,
            aspect_ratio=job.request_json.get("aspect_ratio"),
            fps=job.request_json.get("fps"),
            seed=job.request_json.get("seed"),
            quality=job.request_json.get("quality"),
            input_images=job.request_json.get("input_images") or [],
            first_frame=job.request_json.get("first_frame"),
            last_frame=job.request_json.get("last_frame"),
            reference_images=job.request_json.get("reference_images") or [],
            mask=job.request_json.get("mask"),
            raw_params={**(resolved.raw_params or {}), **(job.request_json.get("raw_params") or {})},
        )
        job.status = MediaJobStatus.RUNNING
        job.progress = 10
        await db.flush()
        await db.commit()

        if job.capability == MediaCapability.IMAGE:
            result = await adapter.submit_image(request)
        else:
            result = await adapter.submit_video(request)
        await db.refresh(job)
        if job.status == MediaJobStatus.CANCELLED:
            return job
        job.provider_job_id = result.provider_job_id
        job.response_json = result.response
        job.progress = max(20, result.progress)
        job.status = _job_status(result.status)
        await db.flush()

        elapsed = 0
        while job.status in {MediaJobStatus.QUEUED, MediaJobStatus.RUNNING} and job.provider_job_id:
            import asyncio

            await asyncio.sleep(settings.video_poll_interval)
            elapsed += settings.video_poll_interval
            await db.refresh(job)
            if job.status == MediaJobStatus.CANCELLED:
                return job
            result = await adapter.get_status(job.provider_job_id)
            job.response_json = result.response
            job.progress = result.progress
            job.status = _job_status(result.status)
            if elapsed >= settings.video_timeout:
                job.status = MediaJobStatus.FAILED
                job.error = "Generation timed out"
                break
            await db.flush()

        if job.status == MediaJobStatus.SUCCEEDED:
            await db.refresh(job)
            if job.status == MediaJobStatus.CANCELLED:
                return job
            await adapter.download_result(result, output_path)
            await db.refresh(job)
            if job.status == MediaJobStatus.CANCELLED:
                return job
            job.result_assets_json = [
                {
                    "type": job.capability.value,
                    "url": storage.get_url(output_path),
                    "provider_url": (result.assets[0] or {}).get("url") if result.assets else None,
                }
            ]
            job.progress = 100
        elif result.error:
            job.error = result.error

        await db.flush()
        return job

    async def run_job_by_id(self, *, db: AsyncSession, job_id: int) -> MediaGenerationJob:
        job = await db.get(MediaGenerationJob, job_id)
        if not job:
            raise ValueError(f"Media generation job {job_id} not found")
        try:
            return await self.run_existing_job(db=db, job=job)
        except Exception as e:
            await db.refresh(job)
            if job.status == MediaJobStatus.CANCELLED:
                return job
            job.status = MediaJobStatus.FAILED
            job.error = _friendly_media_error(e)[:2000]
            job.progress = 100
            await db.flush()
            return job

    def _output_path(self, job: MediaGenerationJob, output_path: str) -> Path:
        path = Path(output_path)
        if path.name.startswith("job_pending"):
            ext = ".png" if job.capability == MediaCapability.IMAGE else ".mp4"
            path = Path(settings.storage_dir) / "media_jobs" / f"job_{job.id}{ext}"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    async def _resolve_job_model(
        self,
        db: AsyncSession,
        job: MediaGenerationJob,
    ) -> ResolvedModel:
        if job.provider_id:
            stmt = (
                select(AIModelConfig, AIProviderConfig)
                .join(AIProviderConfig, AIModelConfig.provider_id == AIProviderConfig.id)
                .where(
                    AIProviderConfig.id == job.provider_id,
                    AIProviderConfig.user_id == job.user_id,
                    AIProviderConfig.enabled == True,
                    AIModelConfig.model_id == job.model_id,
                    AIModelConfig.capability == job.capability,
                    AIModelConfig.enabled == True,
                )
            )
            result = await db.execute(stmt)
            row = result.first()
            if row:
                model, provider = row
                return user_model_resolver._to_resolved_media(model, provider)
            raise ValueError("Configured media provider/model is no longer available")

        return await user_model_resolver.resolve(
            db,
            job.user_id,
            job.capability.value,
            model_hint=job.model_id,
        )


def _job_status(status: str) -> MediaJobStatus:
    return {
        "created": MediaJobStatus.CREATED,
        "queued": MediaJobStatus.QUEUED,
        "running": MediaJobStatus.RUNNING,
        "succeeded": MediaJobStatus.SUCCEEDED,
        "failed": MediaJobStatus.FAILED,
        "cancelled": MediaJobStatus.CANCELLED,
    }.get(status, MediaJobStatus.RUNNING)


media_generation_service = MediaGenerationService()
