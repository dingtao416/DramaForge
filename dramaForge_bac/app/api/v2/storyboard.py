"""
DramaForge v2.0 — Storyboard API
==================================
Endpoints for storyboard generation, editing, segment video generation,
and episode composition.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from loguru import logger

from app.core.database import get_db
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
from app.core.security import CurrentUser, DbSession
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

router = APIRouter()


def _media_options(resolved) -> dict:
    if not resolved.provider_type:
        return {}
    return {
        "provider_type": resolved.provider_type,
        "auth_type": resolved.auth_type or "bearer",
        "headers": resolved.headers or {},
        "config": resolved.config or {},
        "raw_params": resolved.raw_params or {},
    }


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


@router.post("/projects/{project_id}/episodes/{episode_id}/storyboard")
async def generate_storyboard(
    project_id: int,
    episode_id: int,
    user: CurrentUser,
    db: DbSession,
    body: StoryboardGenerateRequest = StoryboardGenerateRequest(),
):
    """Generate storyboard (segments + shots) for an episode via AI."""
    # Consume credits for storyboard generation
    await require_credits(db, user.id, "storyboard_gen", description="分镜自动生成")
    await db.commit()  # release write lock before the AI call

    episode = await _get_episode(project_id, episode_id, db)
    characters, scenes = await _get_project_assets(project_id, db)

    if not episode.content:
        raise HTTPException(status_code=400, detail="Episode has no content")

    # Remove existing segments if force regenerate
    if body.force:
        existing = await db.execute(
            select(Segment).where(Segment.episode_id == episode_id)
        )
        for seg in existing.scalars().all():
            await db.delete(seg)
        await db.flush()

    chat_resolved = await user_model_resolver.resolve(db, user.id, "chat")

    # Generate via VideoEngine
    segments = await video_engine.generate_episode(
        episode=episode,
        characters=characters,
        scenes=scenes,
        project_id=project_id,
        shots_per_segment=body.shots_per_segment,
        chat_model=chat_resolved.model_id,
        chat_api_key=chat_resolved.api_key,
        chat_base_url=chat_resolved.base_url,
        chat_options=chat_resolved.raw_params or {},
    )

    # Persist to DB
    for segment in segments:
        db.add(segment)
    await db.flush()

    total_shots = sum(len(seg.shots) for seg in segments)
    return {
        "message": "Storyboard generated",
        "segments": len(segments),
        "total_shots": total_shots,
    }


@router.get("/projects/{project_id}/episodes/{episode_id}/storyboard", response_model=StoryboardDetail)
async def get_storyboard(
    project_id: int,
    episode_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get the full storyboard for an episode."""
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
    db: AsyncSession = Depends(get_db),
):
    """Edit a shot's details."""
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

    for key, value in update_data.items():
        setattr(shot, key, value)

    await db.flush()
    await db.refresh(shot)
    return shot


@router.post("/projects/{project_id}/episodes/{episode_id}/segments/{segment_id}/generate")
async def generate_segment(
    project_id: int,
    episode_id: int,
    segment_id: int,
    user: CurrentUser,
    db: DbSession,
):
    """Generate assets and video for a single segment."""
    # Video generation: charge for 5s default video per segment
    await require_credits(db, user.id, "video_default_5s", description="分镜视频生成")
    await db.commit()  # release write lock before the AI call

    segment = await db.get(Segment, segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    # Load shots
    stmt = select(Shot).where(Shot.segment_id == segment_id).order_by(Shot.index)
    result = await db.execute(stmt)
    segment.shots = list(result.scalars().all())

    characters, scenes = await _get_project_assets(project_id, db)
    episode = await _get_episode(project_id, episode_id, db)
    image_resolved = await user_model_resolver.resolve(db, user.id, "image")
    tts_resolved = await user_model_resolver.resolve(db, user.id, "tts")
    video_resolved = await user_model_resolver.resolve(db, user.id, "video")

    # Generate assets (image + audio per shot)
    await video_engine.generate_segment_assets(
        segment=segment,
        characters=characters,
        scenes=scenes,
        project_id=project_id,
        ep_num=episode.number,
        image_model=image_resolved.model_id,
        image_api_key=image_resolved.api_key,
        image_base_url=image_resolved.base_url,
        image_options=_media_options(image_resolved),
        tts_model=tts_resolved.model_id,
        tts_api_key=tts_resolved.api_key,
        tts_base_url=tts_resolved.base_url,
    )

    # Compose the segment video from shot assets
    try:
        await video_engine._generate_segment_video(
            segment,
            project_id,
            episode.number,
            video_model=video_resolved.model_id,
            video_api_key=video_resolved.api_key,
            video_base_url=video_resolved.base_url,
            video_options=_media_options(video_resolved),
        )
    except Exception:
        segment.status = SegmentStatus.FAILED
        await db.flush()
        raise

    await db.flush()
    return {"message": "Segment generated", "status": segment.status.value}


@router.post("/projects/{project_id}/episodes/{episode_id}/segments/{segment_id}/regenerate")
async def regenerate_segment(
    project_id: int,
    episode_id: int,
    segment_id: int,
    user: CurrentUser,
    db: DbSession,
):
    """Regenerate a segment (assets + video)."""
    await require_credits(db, user.id, "video_default_5s", description="分镜视频重新生成")
    await db.commit()  # release write lock before the AI call

    segment = await db.get(Segment, segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    stmt = select(Shot).where(Shot.segment_id == segment_id).order_by(Shot.index)
    result = await db.execute(stmt)
    segment.shots = list(result.scalars().all())

    characters, scenes = await _get_project_assets(project_id, db)
    episode = await _get_episode(project_id, episode_id, db)
    image_resolved = await user_model_resolver.resolve(db, user.id, "image")
    tts_resolved = await user_model_resolver.resolve(db, user.id, "tts")
    video_resolved = await user_model_resolver.resolve(db, user.id, "video")

    segment.status = SegmentStatus.GENERATING
    await video_engine.generate_segment_assets(
        segment=segment,
        characters=characters,
        scenes=scenes,
        project_id=project_id,
        ep_num=episode.number,
        image_model=image_resolved.model_id,
        image_api_key=image_resolved.api_key,
        image_base_url=image_resolved.base_url,
        image_options=_media_options(image_resolved),
        tts_model=tts_resolved.model_id,
        tts_api_key=tts_resolved.api_key,
        tts_base_url=tts_resolved.base_url,
    )
    try:
        await video_engine._generate_segment_video(
            segment,
            project_id,
            episode.number,
            video_model=video_resolved.model_id,
            video_api_key=video_resolved.api_key,
            video_base_url=video_resolved.base_url,
            video_options=_media_options(video_resolved),
        )
    except Exception:
        segment.status = SegmentStatus.FAILED
        raise

    await db.flush()
    return {"message": "Segment regenerated", "status": segment.status.value}


@router.post("/projects/{project_id}/episodes/{episode_id}/compose")
async def compose_episode(
    project_id: int,
    episode_id: int,
    user: CurrentUser,
    db: DbSession,
    body: ComposeRequest = ComposeRequest(),
):
    """Compose all segments into a full episode video with optional quality/BGM/subtitle options."""
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
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.status = ProjectStep.COMPLETED
    await db.flush()

    return {"message": "Project exported", "status": ProjectStep.COMPLETED.value}


# ═══════════════════════════════════════════════════════════════════
# P1-3: BGM upload
# ═══════════════════════════════════════════════════════════════════

@router.post("/projects/{project_id}/bgm/upload")
async def upload_bgm(
    project_id: int,
    file: UploadFile = File(...),
    user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
):
    """Upload a background music file for the project."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

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
