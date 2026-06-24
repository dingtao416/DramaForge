"""
DramaForge v2.0 — Storyboard API
==================================
Endpoints for storyboard generation, editing, segment video generation,
and episode composition.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import set_committed_value
from loguru import logger

from app.core.database import get_db, AsyncSessionLocal
from app.models.project import Project, ProjectStep
from app.models.script import Script
from app.models.episode import Episode
from app.models.segment import Segment, SegmentStatus
from app.models.shot import Shot
from app.models.character import Character
from app.models.scene import SceneLocation
from app.schemas.storyboard import (
    StoryboardDetail,
    StoryboardGenerateRequest,
    ShotUpdate,
    ShotDetail,
    SegmentDetail,
)
from app.engines.video_engine import video_engine
from app.services.user_model_resolver import user_model_resolver
from app.services.storage import storage
from app.core.security import CurrentUser, DbSession, get_user_project
from app.core.billing_deps import require_credits

MAX_BGM_UPLOAD_BYTES = 50 * 1024 * 1024
ALLOWED_AUDIO_EXTENSIONS = {"mp3", "wav", "m4a", "aac", "ogg"}
ALLOWED_AUDIO_CONTENT_TYPES = {
    "audio/mpeg",
    "audio/wav",
    "audio/x-wav",
    "audio/mp4",
    "audio/aac",
    "audio/ogg",
}
STORYBOARD_PROGRESS: dict[int, dict[str, object]] = {}


def _set_storyboard_progress(episode_id: int, status: str, progress: int, message: str) -> None:
    STORYBOARD_PROGRESS[episode_id] = {
        "status": status,
        "progress": max(0, min(100, progress)),
        "message": message,
    }


class ComposeRequest(BaseModel):
    """Request to compose a full episode video."""
    quality: str = Field(default="high", pattern="^(low|medium|high)$", description="视频质量: low, medium, high")
    resolution: Optional[str] = Field(default=None, pattern=r"^\d{3,4}x\d{3,4}$", description="输出分辨率，如 720x1280")
    subtitle_text: Optional[str] = Field(default=None, max_length=500, description="叠加字幕文本")
    subtitle_font_size: int = Field(default=24, ge=12, le=72)
    subtitle_position: str = Field(default="bottom", pattern="^(top|bottom)$", description="字幕位置: top, bottom")
    bgm_volume: float = Field(default=0.15, ge=0.0, le=1.0, description="背景音乐音量比例")

    @field_validator("resolution")
    @classmethod
    def validate_resolution_bounds(cls, value: str | None) -> str | None:
        if not value:
            return value
        width, height = (int(part) for part in value.split("x", 1))
        if width > 4096 or height > 4096:
            raise ValueError("resolution cannot exceed 4096x4096")
        return value


class SegmentGenerateRequest(BaseModel):
    video_model_config_id: Optional[int] = None
    resolution: Optional[str] = Field(
        default=None,
        pattern=r"^(\d{3,4}x\d{3,4}|\d{3,4}p)$",
        description="视频分辨率或尺寸，如 720x1280、1280x720、1080p",
    )
    aspect_ratio: Optional[str] = Field(
        default=None,
        pattern=r"^\d{1,2}:\d{1,2}$",
        description="视频比例，如 9:16、16:9、1:1",
    )

    @field_validator("resolution")
    @classmethod
    def validate_generation_resolution(cls, value: str | None) -> str | None:
        if not value or "x" not in value:
            return value
        width, height = (int(part) for part in value.split("x", 1))
        if width > 4096 or height > 4096:
            raise ValueError("resolution cannot exceed 4096x4096")
        return value


router = APIRouter()


def _media_options(resolved) -> dict:
    if not resolved.provider_type:
        return {}
    config = dict(resolved.config or {})
    config["model_capabilities"] = dict(resolved.capabilities or {})
    return {
        "provider_type": resolved.provider_type,
        "auth_type": resolved.auth_type or "bearer",
        "headers": resolved.headers or {},
        "config": config,
        "raw_params": resolved.raw_params or {},
    }


def _list_capability(caps: dict, key: str) -> list[str]:
    value = caps.get(key) or []
    if isinstance(value, str):
        value = value.replace("\n", ",").split(",")
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _supported_video_sizes(caps: dict, model_id: str | None) -> list[str]:
    configured = _list_capability(caps, "video_supported_sizes")
    if configured:
        return configured
    return []


def _supports_video_size(caps: dict, model_id: str | None) -> bool:
    return bool(caps.get("video_size") or _list_capability(caps, "video_supported_sizes"))


def _supports_video_aspect_ratio(caps: dict) -> bool:
    return bool(caps.get("video_aspect_ratio"))


def _video_generation_options(resolved, body: SegmentGenerateRequest | None) -> dict:
    options = _media_options(resolved)
    if not body:
        return options

    caps = dict(resolved.capabilities or {})
    if body.resolution:
        supported_sizes = _supported_video_sizes(caps, resolved.model_id)
        if _supports_video_size(caps, resolved.model_id) and (not supported_sizes or body.resolution in supported_sizes):
            options["size"] = body.resolution
        else:
            logger.info(
                f"Video generation: dropping resolution={body.resolution} "
                f"for model={resolved.model_id}; model does not declare support"
            )
    if body.aspect_ratio:
        if _supports_video_aspect_ratio(caps):
            options["aspect_ratio"] = body.aspect_ratio
        else:
            logger.info(
                f"Video generation: dropping aspect_ratio={body.aspect_ratio} "
                f"for model={resolved.model_id}; model does not declare support"
            )
    return options


async def _resolve_video_model(db: AsyncSession, user_id: int, body: SegmentGenerateRequest | None):
    model_config_id = body.video_model_config_id if body else None
    if model_config_id:
        resolved = await user_model_resolver.resolve_provider_model_by_id(
            db,
            user_id,
            model_config_id,
            "video",
        )
        if not resolved:
            raise HTTPException(status_code=400, detail="Selected video model is unavailable")
        return resolved
    return await user_model_resolver.resolve(db, user_id, "video")


async def _read_upload_limited(file: UploadFile, max_bytes: int) -> bytes:
    content = bytearray()
    while chunk := await file.read(1024 * 1024):
        content.extend(chunk)
        if len(content) > max_bytes:
            raise HTTPException(status_code=413, detail="Uploaded file is too large")
    return bytes(content)


async def _get_episode(project_id: int, episode_id: int, db: AsyncSession) -> Episode:
    """Helper to fetch and validate an episode."""
    episode = await db.get(Episode, episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    # Verify via script → project chain
    script = await db.get(Script, episode.script_id)
    if not script or script.project_id != project_id:
        raise HTTPException(status_code=404, detail="Episode not found in this project")
    return episode


async def _get_project_assets(project_id: int, db: AsyncSession):
    """Get characters and scenes for a project."""
    chars = await db.execute(
        select(Character).where(Character.project_id == project_id)
    )
    scenes = await db.execute(
        select(SceneLocation).where(SceneLocation.project_id == project_id)
    )
    return list(chars.scalars().all()), list(scenes.scalars().all())


async def _load_segment_shots(segment: Segment, db: AsyncSession) -> list[Shot]:
    stmt = select(Shot).where(Shot.segment_id == segment.id).order_by(Shot.index)
    result = await db.execute(stmt)
    shots = list(result.scalars().all())
    set_committed_value(segment, "shots", shots)
    return shots


async def _background_generate_storyboard(
    project_id: int,
    episode_id: int,
    user_id: int,
    shots_per_segment: int = 5,
):
    """Background task: generate storyboard segments and shots via AI."""
    async with AsyncSessionLocal() as db:
        try:
            _set_storyboard_progress(episode_id, "generating", 10, "加载剧集内容")
            episode = await db.get(Episode, episode_id)
            if not episode:
                logger.error(f"Background: episode {episode_id} not found for storyboard generation")
                _set_storyboard_progress(episode_id, "failed", 100, "剧集不存在")
                return

            _set_storyboard_progress(episode_id, "generating", 20, "读取角色与场景")
            characters, scenes = await _get_project_assets(project_id, db)

            if not episode.content:
                logger.error(f"Background: episode {episode_id} has no content")
                _set_storyboard_progress(episode_id, "failed", 100, "剧集正文为空")
                return

            _set_storyboard_progress(episode_id, "generating", 32, "连接剧本模型")
            chat_resolved = await user_model_resolver.resolve(db, user_id, "chat")

            _set_storyboard_progress(episode_id, "generating", 48, "生成分镜结构")
            segments = await video_engine.generate_episode(
                episode=episode,
                characters=characters,
                scenes=scenes,
                project_id=project_id,
                shots_per_segment=shots_per_segment,
                chat_model=chat_resolved.model_id,
                chat_api_key=chat_resolved.api_key,
                chat_base_url=chat_resolved.base_url,
                chat_options=chat_resolved.raw_params or {},
            )

            _set_storyboard_progress(episode_id, "generating", 88, "写入分镜结果")
            for segment in segments:
                db.add(segment)
            await db.commit()

            total_shots = sum(len(seg.shots) for seg in segments)
            logger.info(
                f"Background: storyboard generated for episode {episode_id} "
                f"— {len(segments)} segments, {total_shots} shots"
            )
            _set_storyboard_progress(episode_id, "completed", 100, "分镜生成完成")
        except Exception as e:
            logger.error(f"Background: storyboard generation failed for episode {episode_id}: {e}")
            await db.rollback()
            _set_storyboard_progress(episode_id, "failed", 100, str(e)[:120] or "分镜生成失败")


@router.post("/projects/{project_id}/episodes/{episode_id}/storyboard")
async def generate_storyboard(
    project_id: int,
    episode_id: int,
    user: CurrentUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
    body: StoryboardGenerateRequest = StoryboardGenerateRequest(),
):
    """Generate storyboard (segments + shots) for an episode via AI (async)."""
    # Verify project ownership
    await get_user_project(project_id, user, db)

    # Consume credits for storyboard generation
    await require_credits(db, user.id, "storyboard_gen", description="分镜自动生成")
    await db.commit()  # release write lock before background task

    episode = await _get_episode(project_id, episode_id, db)

    if not episode.content:
        raise HTTPException(status_code=400, detail="Episode has no content")

    _set_storyboard_progress(episode_id, "generating", 5, "分镜任务已提交")

    # Remove existing segments if force regenerate
    if body.force:
        _set_storyboard_progress(episode_id, "generating", 8, "清理旧分镜")
        existing = await db.execute(
            select(Segment).where(Segment.episode_id == episode_id)
        )
        for seg in existing.scalars().all():
            await db.delete(seg)
        await db.commit()

    # Fire background task
    background_tasks.add_task(
        _background_generate_storyboard,
        project_id=project_id,
        episode_id=episode_id,
        user_id=user.id,
        shots_per_segment=body.shots_per_segment,
    )

    return {
        "message": "Storyboard generation started",
        "status": "generating",
    }


@router.get("/projects/{project_id}/episodes/{episode_id}/storyboard/status")
async def get_storyboard_generation_status(
    project_id: int,
    episode_id: int,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get storyboard generation progress for an episode."""
    await get_user_project(project_id, user, db)
    await _get_episode(project_id, episode_id, db)
    progress = STORYBOARD_PROGRESS.get(episode_id)
    if progress:
        return progress

    result = await db.execute(
        select(Segment.id).where(Segment.episode_id == episode_id).limit(1)
    )
    if result.first():
        return {
            "status": "completed",
            "progress": 100,
            "message": "分镜已生成",
        }
    return {
        "status": "idle",
        "progress": 0,
        "message": "尚未生成分镜",
    }


@router.get("/projects/{project_id}/episodes/{episode_id}/storyboard", response_model=StoryboardDetail)
async def get_storyboard(
    project_id: int,
    episode_id: int,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get the full storyboard for an episode."""
    await get_user_project(project_id, user, db)
    episode = await _get_episode(project_id, episode_id, db)

    # Load segments with shots
    stmt = (
        select(Segment)
        .where(Segment.episode_id == episode_id)
        .options(selectinload(Segment.shots))
        .order_by(Segment.index)
    )
    result = await db.execute(stmt)
    segments = result.scalars().all()

    total_duration = 0.0
    total_shots = 0
    for seg in segments:
        for shot in seg.shots:
            total_shots += 1
            if shot.duration:
                total_duration += shot.duration

    return StoryboardDetail(
        episode_id=episode_id,
        episode_title=episode.title,
        segments=[SegmentDetail.model_validate(seg) for seg in segments],
        total_duration=total_duration,
        total_shots=total_shots,
    )


@router.put("/projects/{project_id}/episodes/{episode_id}/shots/{shot_id}", response_model=ShotDetail)
async def update_shot(
    project_id: int,
    episode_id: int,
    shot_id: int,
    body: ShotUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Edit a shot's details."""
    await get_user_project(project_id, user, db)
    shot = await db.get(Shot, shot_id)
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")

    update_data = body.model_dump(exclude_unset=True)
    # Convert ShotCharacterRef to dicts for JSON storage
    if "characters" in update_data and update_data["characters"] is not None:
        update_data["characters"] = [
            c.model_dump() if hasattr(c, "model_dump") else c
            for c in update_data["characters"]
        ]
    if "visual_references" in update_data and update_data["visual_references"] is not None:
        update_data["visual_references"] = [
            ref.model_dump() if hasattr(ref, "model_dump") else ref
            for ref in update_data["visual_references"]
        ]

    for key, value in update_data.items():
        setattr(shot, key, value)

    await db.flush()
    await db.refresh(shot)
    return shot


async def _background_generate_segment(
    segment_id: int,
    project_id: int,
    episode_number: int,
    user_id: int,
    video_model_config_id: Optional[int] = None,
    resolution: Optional[str] = None,
    aspect_ratio: Optional[str] = None,
):
    """Background task: generate assets and video for a segment."""
    async with AsyncSessionLocal() as db:
        try:
            segment = await db.get(Segment, segment_id)
            if not segment:
                logger.error(f"Background: segment {segment_id} not found")
                return

            await _load_segment_shots(segment, db)

            characters, scenes = await _get_project_assets(project_id, db)

            body = SegmentGenerateRequest(
                video_model_config_id=video_model_config_id,
                resolution=resolution,
                aspect_ratio=aspect_ratio,
            ) if video_model_config_id or resolution or aspect_ratio else None
            video_resolved = await _resolve_video_model(db, user_id, body)
            video_options = _video_generation_options(video_resolved, body)

            await video_engine.generate_segment_videos_only(
                segment=segment,
                characters=characters,
                scenes=scenes,
                project_id=project_id,
                ep_num=episode_number,
                video_model=video_resolved.model_id,
                video_api_key=video_resolved.api_key,
                video_base_url=video_resolved.base_url,
                video_options=video_options,
                video_capabilities=video_resolved.capabilities or {},
            )

            await video_engine._generate_segment_video(
                segment,
                project_id,
                episode_number,
                video_model=video_resolved.model_id,
                video_api_key=video_resolved.api_key,
                video_base_url=video_resolved.base_url,
                video_options=video_options,
                video_capabilities=video_resolved.capabilities or {},
                reuse_existing_shots=True,
            )

            await db.commit()
            logger.info(f"Background: segment {segment_id} generation completed")
        except Exception as e:
            logger.error(f"Background: segment {segment_id} generation failed: {e}")
            await db.rollback()
            # Mark as failed in a new transaction
            try:
                segment = await db.get(Segment, segment_id)
                if segment:
                    segment.status = SegmentStatus.FAILED
                    await db.commit()
            except Exception as mark_err:
                logger.error(f"Background: failed to mark segment {segment_id} as failed: {mark_err}")


async def _background_generate_shot(
    shot_id: int,
    project_id: int,
    episode_number: int,
    user_id: int,
    video_model_config_id: Optional[int] = None,
    resolution: Optional[str] = None,
    aspect_ratio: Optional[str] = None,
):
    """Background task: generate assets and video for one shot."""
    async with AsyncSessionLocal() as db:
        try:
            shot = await db.get(Shot, shot_id)
            if not shot:
                logger.error(f"Background: shot {shot_id} not found")
                return

            segment = await db.get(Segment, shot.segment_id)
            if not segment:
                logger.error(f"Background: segment for shot {shot_id} not found")
                return

            await _load_segment_shots(segment, db)

            characters, scenes = await _get_project_assets(project_id, db)

            body = SegmentGenerateRequest(
                video_model_config_id=video_model_config_id,
                resolution=resolution,
                aspect_ratio=aspect_ratio,
            ) if video_model_config_id or resolution or aspect_ratio else None
            video_resolved = await _resolve_video_model(db, user_id, body)
            video_options = _video_generation_options(video_resolved, body)

            shot.shot_status = "generating"
            segment.status = SegmentStatus.GENERATING

            await video_engine.generate_shot_video_only(
                shot=shot,
                segment=segment,
                characters=characters,
                scenes=scenes,
                project_id=project_id,
                ep_num=episode_number,
                video_model=video_resolved.model_id,
                video_api_key=video_resolved.api_key,
                video_base_url=video_resolved.base_url,
                video_options=video_options,
                video_capabilities=video_resolved.capabilities or {},
            )

            all_shot_videos_ready = all(s.video_url for s in segment.shots)
            if all_shot_videos_ready:
                await video_engine._generate_segment_video(
                    segment,
                    project_id,
                    episode_number,
                    video_model=video_resolved.model_id,
                    video_api_key=video_resolved.api_key,
                    video_base_url=video_resolved.base_url,
                    video_options=video_options,
                    video_capabilities=video_resolved.capabilities or {},
                    reuse_existing_shots=True,
                )
            elif shot.video_url:
                segment.status = SegmentStatus.PARTIAL

            await db.commit()
            logger.info(f"Background: shot {shot_id} generation completed")
        except Exception as e:
            import traceback
            logger.error(f"Background: shot {shot_id} generation failed: {e}\n{traceback.format_exc()}")
            try:
                await db.rollback()
            except Exception as rollback_err:
                logger.error(f"Background: rollback after shot {shot_id} failure also failed: {rollback_err}")
            try:
                shot = await db.get(Shot, shot_id)
                if shot:
                    shot.shot_status = "failed"
                    shot.error_message = str(e)[:500]
                    segment = await db.get(Segment, shot.segment_id)
                    if segment:
                        segment.status = SegmentStatus.PARTIAL
                    await db.commit()
            except Exception as mark_err:
                logger.error(f"Background: failed to mark shot {shot_id} as failed: {mark_err}")


@router.post("/projects/{project_id}/episodes/{episode_id}/segments/{segment_id}/generate")
async def generate_segment(
    project_id: int,
    episode_id: int,
    segment_id: int,
    user: CurrentUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
    body: SegmentGenerateRequest | None = None,
):
    """Generate assets and video for a single segment (async)."""
    # Verify project ownership
    await get_user_project(project_id, user, db)

    # Video generation: charge for 5s default video per segment
    await require_credits(db, user.id, "video_default_5s", description="分镜视频生成")
    await db.commit()  # release write lock before background task

    segment = await db.get(Segment, segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    episode = await _get_episode(project_id, episode_id, db)

    # Mark as generating and commit
    segment.status = SegmentStatus.GENERATING
    await db.commit()

    # Fire background task
    background_tasks.add_task(
        _background_generate_segment,
        segment_id=segment_id,
        project_id=project_id,
        episode_number=episode.number,
        user_id=user.id,
        video_model_config_id=body.video_model_config_id if body else None,
        resolution=body.resolution if body else None,
        aspect_ratio=body.aspect_ratio if body else None,
    )

    return {"message": "Segment generation started", "status": "generating"}


@router.post("/projects/{project_id}/episodes/{episode_id}/shots/{shot_id}/generate")
async def generate_shot(
    project_id: int,
    episode_id: int,
    shot_id: int,
    user: CurrentUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
    body: SegmentGenerateRequest | None = None,
):
    """Generate assets and video for a single shot (async)."""
    await get_user_project(project_id, user, db)
    await require_credits(db, user.id, "video_default_5s", description="分镜视频生成")
    await db.commit()

    shot = await db.get(Shot, shot_id)
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")

    segment = await db.get(Segment, shot.segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    episode = await _get_episode(project_id, episode_id, db)

    shot.shot_status = "generating"
    segment.status = SegmentStatus.GENERATING
    await db.commit()

    background_tasks.add_task(
        _background_generate_shot,
        shot_id=shot_id,
        project_id=project_id,
        episode_number=episode.number,
        user_id=user.id,
        video_model_config_id=body.video_model_config_id if body else None,
        resolution=body.resolution if body else None,
        aspect_ratio=body.aspect_ratio if body else None,
    )

    return {"message": "Shot generation started", "status": "generating"}


async def _background_regenerate_segment(
    segment_id: int,
    project_id: int,
    episode_number: int,
    user_id: int,
    video_model_config_id: Optional[int] = None,
    resolution: Optional[str] = None,
    aspect_ratio: Optional[str] = None,
):
    """Background task: regenerate assets and video for a segment."""
    async with AsyncSessionLocal() as db:
        try:
            segment = await db.get(Segment, segment_id)
            if not segment:
                logger.error(f"Background: segment {segment_id} not found for regenerate")
                return

            await _load_segment_shots(segment, db)

            characters, scenes = await _get_project_assets(project_id, db)

            body = SegmentGenerateRequest(
                video_model_config_id=video_model_config_id,
                resolution=resolution,
                aspect_ratio=aspect_ratio,
            ) if video_model_config_id or resolution or aspect_ratio else None
            video_resolved = await _resolve_video_model(db, user_id, body)
            video_options = _video_generation_options(video_resolved, body)

            segment.status = SegmentStatus.GENERATING
            await video_engine.generate_segment_videos_only(
                segment=segment,
                characters=characters,
                scenes=scenes,
                project_id=project_id,
                ep_num=episode_number,
                video_model=video_resolved.model_id,
                video_api_key=video_resolved.api_key,
                video_base_url=video_resolved.base_url,
                video_options=video_options,
                video_capabilities=video_resolved.capabilities or {},
            )

            await video_engine._generate_segment_video(
                segment,
                project_id,
                episode_number,
                video_model=video_resolved.model_id,
                video_api_key=video_resolved.api_key,
                video_base_url=video_resolved.base_url,
                video_options=video_options,
                video_capabilities=video_resolved.capabilities or {},
                reuse_existing_shots=True,
            )

            await db.commit()
            logger.info(f"Background: segment {segment_id} regeneration completed")
        except Exception as e:
            logger.error(f"Background: segment {segment_id} regeneration failed: {e}")
            await db.rollback()
            try:
                segment = await db.get(Segment, segment_id)
                if segment:
                    segment.status = SegmentStatus.FAILED
                    await db.commit()
            except Exception as mark_err:
                logger.error(f"Background: failed to mark segment {segment_id} as failed: {mark_err}")


@router.post("/projects/{project_id}/episodes/{episode_id}/segments/{segment_id}/regenerate")
async def regenerate_segment(
    project_id: int,
    episode_id: int,
    segment_id: int,
    user: CurrentUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
    body: SegmentGenerateRequest | None = None,
):
    """Regenerate a segment (assets + video) — async."""
    await get_user_project(project_id, user, db)
    await require_credits(db, user.id, "video_default_5s", description="分镜视频重新生成")
    await db.commit()  # release write lock before background task

    segment = await db.get(Segment, segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    episode = await _get_episode(project_id, episode_id, db)

    segment.status = SegmentStatus.GENERATING
    await db.commit()

    background_tasks.add_task(
        _background_regenerate_segment,
        segment_id=segment_id,
        project_id=project_id,
        episode_number=episode.number,
        user_id=user.id,
        video_model_config_id=body.video_model_config_id if body else None,
        resolution=body.resolution if body else None,
        aspect_ratio=body.aspect_ratio if body else None,
    )

    return {"message": "Segment regeneration started", "status": "generating"}


@router.post("/projects/{project_id}/episodes/{episode_id}/compose")
async def compose_episode(
    project_id: int,
    episode_id: int,
    user: CurrentUser,
    db: DbSession,
    body: ComposeRequest = ComposeRequest(),
):
    """Compose all segments into a full episode video with optional quality/BGM/subtitle options."""
    # Verify project ownership
    await get_user_project(project_id, user, db)

    # Compositing costs credits
    await require_credits(db, user.id, "video_default_5s", description="剧集合成")
    await db.commit()  # release write lock before the compose operation

    episode = await _get_episode(project_id, episode_id, db)

    stmt = (
        select(Segment)
        .where(Segment.episode_id == episode_id)
        .order_by(Segment.index)
    )
    result = await db.execute(stmt)
    segments = list(result.scalars().all())

    completed = [s for s in segments if s.status in (SegmentStatus.COMPLETED, SegmentStatus.PARTIAL)]
    if not completed:
        raise HTTPException(status_code=400, detail="No completed segments to compose")

    # Resolve BGM path (either user-uploaded or from project bgm)
    bgm_path = None
    if body.bgm_volume > 0:
        # Check if project has a BGM uploaded (any audio format)
        bgm_dir = storage.project_path(project_id) / "bgm"
        if bgm_dir.exists():
            for ext in ("mp3", "wav", "m4a", "aac", "ogg"):
                candidate = bgm_dir / f"background.{ext}"
                if candidate.exists():
                    bgm_path = str(candidate)
                    break

    video_url = await video_engine.compose_full_episode(
        segments=completed,
        project_id=project_id,
        ep_num=episode.number,
        bgm_path=bgm_path,
        quality=body.quality,
        resolution=body.resolution,
        subtitle_text=body.subtitle_text,
        subtitle_font_size=body.subtitle_font_size,
        subtitle_position=body.subtitle_position,
        bgm_volume=body.bgm_volume,
    )

    return {"message": "Episode composed", "video_url": video_url}


@router.post("/projects/{project_id}/export")
async def export_project(
    project_id: int,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Export project — mark as completed."""
    project = await get_user_project(project_id, user, db)

    project.status = ProjectStep.COMPLETED
    await db.flush()

    return {"message": "Project exported", "status": ProjectStep.COMPLETED.value}


# ═══════════════════════════════════════════════════════════════════
# P1-3: BGM upload
# ═══════════════════════════════════════════════════════════════════

@router.post("/projects/{project_id}/bgm/upload")
async def upload_bgm(
    project_id: int,
    user: CurrentUser,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a background music file for the project."""
    project = await get_user_project(project_id, user, db)

    # Validate file type
    ext = (file.filename or "").rsplit(".", 1)[-1].lower() if file.filename else ""
    if ext not in ("mp3", "wav", "m4a", "aac", "ogg"):
        raise HTTPException(status_code=400, detail="Unsupported audio format. Use mp3, wav, m4a, aac, or ogg.")
    if file.content_type not in ALLOWED_AUDIO_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported audio content type.")

    bgm_dir = storage.project_path(project_id) / "bgm"
    bgm_dir.mkdir(parents=True, exist_ok=True)
    dest = bgm_dir / f"background.{ext}"

    content = await _read_upload_limited(file, MAX_BGM_UPLOAD_BYTES)
    dest.write_bytes(content)

    logger.info(f"BGM uploaded for project {project_id}: {file.filename} ({len(content)} bytes)")

    return {
        "message": "BGM uploaded",
        "filename": file.filename,
        "size": len(content),
        "url": storage.get_url(dest),
    }


# ═══════════════════════════════════════════════════════════════════
# P0-1: Video download
# ═══════════════════════════════════════════════════════════════════

@router.get("/projects/{project_id}/episodes/{episode_id}/download")
async def download_episode_video(
    project_id: int,
    episode_id: int,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Download the composed episode video file."""
    await get_user_project(project_id, user, db)
    episode = await _get_episode(project_id, episode_id, db)

    video_path = storage.episode_video_path(project_id, episode.number)
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found. Please compose the episode first.")

    # Determine filename
    filename = f"episode_{episode.number:03d}.mp4"
    if episode.title:
        safe_title = "".join(c for c in episode.title if c.isalnum() or c in "._- ")
        filename = f"{safe_title}.mp4"

    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ═══════════════════════════════════════════════════════════════════
# P2-4: Batch shot update
# ═══════════════════════════════════════════════════════════════════

class BatchShotUpdate(BaseModel):
    """Batch update multiple shots with the same settings."""
    shot_ids: list[int] = Field(..., min_length=1, max_length=50)
    camera_type: Optional[str] = None
    camera_angle: Optional[str] = None
    camera_movement: Optional[str] = None
    transition: Optional[str] = None
    time_of_day: Optional[str] = None
    voice_style: Optional[str] = None


@router.put("/projects/{project_id}/episodes/{episode_id}/shots/batch")
async def batch_update_shots(
    project_id: int,
    episode_id: int,
    body: BatchShotUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Apply the same settings to multiple shots at once."""
    await get_user_project(project_id, user, db)
    episode = await _get_episode(project_id, episode_id, db)

    update_data = body.model_dump(exclude_unset=True, exclude={"shot_ids"})
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    updated = 0
    for shot_id in body.shot_ids:
        shot = await db.get(Shot, shot_id)
        if not shot:
            continue
        segment = await db.get(Segment, shot.segment_id)
        if not segment or segment.episode_id != episode.id:
            continue
        for key, value in update_data.items():
            setattr(shot, key, value)
        updated += 1

    await db.flush()
    return {"message": f"Updated {updated} shots", "updated_count": updated}


# ═══════════════════════════════════════════════════════════════════
# P0-3: Manual shot add / delete
# ═══════════════════════════════════════════════════════════════════

@router.post("/projects/{project_id}/episodes/{episode_id}/segments/{segment_id}/shots", response_model=ShotDetail, status_code=201)
async def create_shot(
    project_id: int,
    episode_id: int,
    segment_id: int,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Add a new shot to a segment manually."""
    await get_user_project(project_id, user, db)
    episode = await _get_episode(project_id, episode_id, db)

    segment = await db.get(Segment, segment_id)
    if not segment or segment.episode_id != episode.id:
        raise HTTPException(status_code=404, detail="Segment not found")

    # Determine the next index
    stmt = select(Shot).where(Shot.segment_id == segment_id).order_by(Shot.index.desc())
    result = await db.execute(stmt)
    last_shot = result.scalars().first()
    next_index = (last_shot.index + 1) if last_shot else 0

    shot = Shot(
        segment_id=segment_id,
        index=next_index,
        duration=5.0,
        time_of_day="day",
        scene_ref="",
        camera_type="medium",
        camera_angle="eye_level",
        camera_movement="static",
        characters=[],
        dialogue="",
        voice_style="",
        background="",
        transition="cut",
    )
    db.add(shot)
    await db.flush()
    await db.refresh(shot)
    return shot


@router.delete("/projects/{project_id}/episodes/{episode_id}/shots/{shot_id}", status_code=204)
async def delete_shot(
    project_id: int,
    episode_id: int,
    shot_id: int,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Delete a shot from the storyboard."""
    await get_user_project(project_id, user, db)
    episode = await _get_episode(project_id, episode_id, db)

    shot = await db.get(Shot, shot_id)
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")

    # Verify the shot belongs to this episode
    segment = await db.get(Segment, shot.segment_id)
    if not segment or segment.episode_id != episode.id:
        raise HTTPException(status_code=404, detail="Shot not found in this episode")

    # Re-index remaining shots in the segment
    stmt = select(Shot).where(
        Shot.segment_id == shot.segment_id,
        Shot.index > shot.index,
    ).order_by(Shot.index)
    result = await db.execute(stmt)
    for later_shot in result.scalars().all():
        later_shot.index -= 1

    await db.delete(shot)
    await db.flush()
