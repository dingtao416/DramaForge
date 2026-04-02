"""
DramaForge AI Hub - Video Service
Video generation via laozhang.ai - supports Sora 2, Veo 3, Veo 3.1.

Model Strategy:
  - Primary model tried first
  - On failure, automatically falls back to backup models
  - Sync API (chat completions) preferred for stability
  - Async API (/videos) as option for sora-2 / sora-2-pro

Available Models (by cost-effectiveness):
  ┌──────────────────────────┬────────┬─────────────────────────────�?  �?Model ID                 �?API    �?Notes                       �?  ├──────────────────────────┼────────┼─────────────────────────────�?  �?veo-3.1-fast             �?sync   �?�?Best speed/quality ratio �?  �?veo-3.1                  �?sync   �?Highest quality (Veo 3.1)   �?  �?veo-3.1-landscape        �?sync   �?Landscape version           �?  �?veo-3.1-landscape-fast   �?sync   �?Landscape fast              �?  �?veo3-fast                �?sync   �?Veo 3 fast                  �?  �?veo3                     �?sync   �?Veo 3 standard              �?  �?veo3-pro                 �?sync   �?Veo 3 pro (best Veo qual)   �?  �?sora_video2              �?sync   �?Sora 2 portrait             �?  �?sora_video2-landscape    �?sync   �?Sora 2 landscape            �?  �?sora_video2-portrait     �?sync   �?Sora 2 portrait explicit    �?  �?sora_video2-15s          �?sync   �?Sora 2 portrait 15s         �?  �?sora_video2-landscape-15s�?sync   �?Sora 2 landscape 15s        �?  �?sora_video2-portrait-15s �?sync   �?Sora 2 portrait 15s         �?  �?sora-2-character         �?sync   �?Sora 2 character animation  �?  �?sora-2                   �?async  �?$0.15 (unstable under load) �?  �?sora-2-pro               �?async  �?$0.8, 1080P (async only)    �?  └──────────────────────────┴────────┴─────────────────────────────�?
Docs: https://docs.laozhang.ai/api-capabilities/sora2/
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Optional

import httpx
from loguru import logger

from app.core.config import settings
from app.ai_hub._client import BaseClient, HubClientError
from app.ai_hub._models import VideoResponse, VideoStatus, VideoTaskStatus


# ─── Model registry ───

# Models that use the async /v1/videos API
ASYNC_MODELS = {"sora-2", "sora-2-pro"}

# All known sync models (via /v1/chat/completions)
SYNC_MODELS = {
    # Veo 3.1
    "veo-3.1", "veo-3.1-fast",
    "veo-3.1-landscape", "veo-3.1-landscape-fast",
    "veo-3.1-fl", "veo-3.1-landscape-fl",
    # Veo 3
    "veo3", "veo3-fast", "veo3-pro", "veo3-pro-frames",
    # Sora 2
    "sora_video2", "sora_video2-landscape", "sora_video2-portrait",
    "sora_video2-15s", "sora_video2-landscape-15s", "sora_video2-portrait-15s",
    "sora-2-character",
}

# Default fallback chain (ordered by cost-effectiveness)
DEFAULT_FALLBACK_CHAIN = [
    "veo-3.1-fast",
    "veo3-fast",
    "sora_video2-landscape",
    "veo-3.1",
    "veo3",
]


class VideoService:
    """
    Video generation service with multi-model support & auto-fallback.

    Usage:
        video = await video_svc.generate("prompt", "output.mp4")
        video = await video_svc.generate("prompt", "out.mp4", model="veo3-pro")
    """

    def __init__(self):
        # Build fallback chain: primary + configured fallbacks
        self._fallback_chain = self._build_fallback_chain()
        logger.info(
            f"VideoService | primary={settings.video_model} "
            f"fallback_chain={[m for m in self._fallback_chain]}"
        )

    # ──────────── Public API ────────────

    async def generate(
        self,
        prompt: str,
        output_path: str,
        *,
        model: str = None,
        size: str = None,
        seconds: str = None,
        use_async: bool = None,
        fallback: bool = True,
    ) -> VideoResponse:
        """
        Generate a video from a text prompt with auto-fallback.

        Tries the primary model first. If it fails and fallback=True,
        automatically tries backup models from the fallback chain.

        Args:
            prompt: Text description of the video.
            output_path: Where to save the mp4 file.
            model: Override video model (skips fallback chain if set).
            size: Video dimensions (for async API).
            seconds: Duration "10" or "15" (for async API).
            use_async: Force async mode. Auto-detected if None.
            fallback: Whether to try backup models on failure.

        Returns:
            VideoResponse with video_path, video_url, model, etc.
        """
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        # If explicit model given, just try that one
        if model:
            return await self._try_model(prompt, out, model, size, seconds, use_async)

        # Otherwise, walk the fallback chain
        models_to_try = self._fallback_chain if fallback else [self._fallback_chain[0]]
        last_error = None

        for idx, try_model in enumerate(models_to_try, 1):
            try:
                logger.info(
                    f"video.generate | trying [{idx}/{len(models_to_try)}] "
                    f"model={try_model}"
                )
                result = await self._try_model(
                    prompt, out, try_model, size, seconds, use_async
                )
                if idx > 1:
                    logger.info(
                        f"video.generate | fallback succeeded with {try_model}"
                    )
                return result

            except Exception as e:
                last_error = e
                logger.warning(
                    f"video.generate | model={try_model} failed: {e}"
                )
                if idx < len(models_to_try):
                    logger.info(f"video.generate | trying next fallback...")

        raise HubClientError(
            f"All {len(models_to_try)} video models failed. "
            f"Last error: {last_error}",
            status_code=0,
        )

    async def get_task_status(self, task_id: str) -> VideoTaskStatus:
        """Query status of an async video task."""
        http = BaseClient.http()
        resp = await http.get(f"/videos/{task_id}")
        resp.raise_for_status()
        data = resp.json()

        status_map = {
            "pending": VideoStatus.PENDING,
            "processing": VideoStatus.GENERATING,
            "completed": VideoStatus.COMPLETED,
            "failed": VideoStatus.FAILED,
        }

        video_url = None
        if data.get("data") and isinstance(data["data"], list):
            for item in data["data"]:
                if item.get("url"):
                    video_url = item["url"]
                    break

        raw_error = data.get("error")
        if isinstance(raw_error, dict):
            error_msg = raw_error.get("message", str(raw_error))
        else:
            error_msg = str(raw_error) if raw_error else None

        return VideoTaskStatus(
            task_id=task_id,
            status=status_map.get(data.get("status", "pending"), VideoStatus.PENDING),
            video_url=video_url,
            error=error_msg,
        )

    def list_models(self) -> dict[str, list[str]]:
        """List all available video models by category."""
        return {
            "sync": sorted(SYNC_MODELS),
            "async": sorted(ASYNC_MODELS),
            "fallback_chain": list(self._fallback_chain),
        }

    # ──────────── Internal ────────────

    async def _try_model(
        self,
        prompt: str,
        out: Path,
        model: str,
        size: str = None,
        seconds: str = None,
        use_async: bool = None,
    ) -> VideoResponse:
        """Try generating video with a single model."""
        is_async_model = model in ASYNC_MODELS
        force_async = use_async if use_async is not None else is_async_model

        if force_async and is_async_model:
            return await self._async_generate(
                prompt, out, model,
                size or settings.video_size,
                seconds or settings.video_seconds,
            )
        else:
            return await self._sync_generate(prompt, out, model)

    async def _sync_generate(
        self, prompt: str, out: Path, model: str
    ) -> VideoResponse:
        """Sync video gen via chat completions endpoint."""
        logger.info(f"video sync | model={model}")
        client = BaseClient.openai()

        resp = await BaseClient.with_retry(
            lambda: client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            ),
            retries=1,
            label=f"video-sync:{model}",
        )

        content = resp.choices[0].message.content
        video_url = self._extract_video_url(content)

        if video_url:
            await self._download_file(video_url, out)
            logger.info(f"video saved (sync) | model={model} path={out}")
            return VideoResponse(
                video_path=str(out),
                video_url=video_url,
                model=model,
                status=VideoStatus.COMPLETED,
            )
        else:
            raise HubClientError(
                f"No video URL in response from {model}: {content[:200]}",
                status_code=0,
            )

    async def _async_generate(
        self, prompt: str, out: Path, model: str, size: str, seconds: str
    ) -> VideoResponse:
        """Async video gen: submit -> poll -> download."""
        http = BaseClient.http()

        logger.info(f"video async submit | model={model}")
        submit_resp = await BaseClient.with_retry(
            lambda: http.post("/videos", json={
                "model": model, "prompt": prompt,
                "size": size, "seconds": seconds,
            }),
            label=f"video-submit:{model}",
        )
        submit_resp.raise_for_status()
        submit_data = submit_resp.json()

        task_id = submit_data.get("id") or submit_data.get("task_id")
        if not task_id:
            raise HubClientError(f"No task_id: {submit_data}", status_code=0)

        logger.info(f"video task submitted | task_id={task_id}")

        poll_interval = settings.video_poll_interval
        timeout = settings.video_timeout
        elapsed = 0

        while elapsed < timeout:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

            status = await self.get_task_status(task_id)
            logger.debug(
                f"video poll | task={task_id} status={status.status} "
                f"elapsed={elapsed}s"
            )

            if status.status == VideoStatus.COMPLETED and status.video_url:
                await self._download_file(status.video_url, out)
                logger.info(f"video generated (async) | task={task_id} path={out}")
                return VideoResponse(
                    video_path=str(out), video_url=status.video_url,
                    model=model, status=VideoStatus.COMPLETED, task_id=task_id,
                )
            elif status.status == VideoStatus.FAILED:
                raise HubClientError(
                    f"Async video failed: {status.error}", status_code=0
                )

        raise HubClientError(
            f"Async video timed out ({timeout}s, task={task_id})", status_code=0
        )

    # ──────────── Helpers ────────────

    def _build_fallback_chain(self) -> list[str]:
        """Build fallback chain: configured primary + defaults (deduplicated)."""
        primary = settings.video_model
        chain = [primary]
        for m in DEFAULT_FALLBACK_CHAIN:
            if m not in chain:
                chain.append(m)
        return chain

    @staticmethod
    def _extract_video_url(content: str) -> Optional[str]:
        """Extract a video URL from LLM response content."""
        if not content:
            return None
        patterns = [
            r'(https?://[^\s\])"]+\.mp4[^\s\])"]*)',
            r'(https?://[^\s\])"]+/video[^\s\])"]*)',
            r'(https?://[^\s\])"]+)',
        ]
        for p in patterns:
            m = re.search(p, content)
            if m:
                return m.group(1)
        return content.strip() if content.startswith("http") else None

    @staticmethod
    async def _download_file(url: str, out: Path):
        """Download file from URL."""
        logger.debug(f"downloading | url={url[:80]}... -> {out}")
        async with httpx.AsyncClient(timeout=300) as dl:
            resp = await dl.get(url)
            resp.raise_for_status()
            out.write_bytes(resp.content)
        logger.debug(f"downloaded | size={out.stat().st_size}")