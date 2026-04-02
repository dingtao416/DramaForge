"""
DramaForge v2.0 — Storyboard API
==================================
Endpoints for storyboard generation, editing, segment video generation,
and episode composition.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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

router = APIRouter()


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
    body: StoryboardGenerateRequest = StoryboardGenerateRequest(),
    db: AsyncSession = Depends(get_db),
):
    """Generate storyboard (segments + shots) for an episode via AI."""
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

    # Generate via VideoEngine
    segments = await video_engine.generate_episode(
        episode=episode,
        characters=characters,
        scenes=scenes,
        project_id=project_id,
        shots_per_segment=body.shots_per_segment,
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
    db: AsyncSession = Depends(get_db),
):
    """Generate assets and video for a single segment."""
    segment = await db.get(Segment, segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    # Load shots
    stmt = select(Shot).where(Shot.segment_id == segment_id).order_by(Shot.index)
    result = await db.execute(stmt)
    segment.shots = list(result.scalars().all())

    characters, scenes = await _get_project_assets(project_id, db)
    episode = await _get_episode(project_id, episode_id, db)

    # Generate assets
    await video_engine.generate_segment_assets(
        segment=segment,
        characters=characters,
        scenes=scenes,
        project_id=project_id,
        ep_num=episode.number,
    )

    await db.flush()
    return {"message": "Segment assets generated", "status": segment.status.value}


@router.post("/projects/{project_id}/episodes/{episode_id}/segments/{segment_id}/regenerate")
async def regenerate_segment(
    project_id: int,
    episode_id: int,
    segment_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Regenerate a segment (assets + video)."""
    segment = await db.get(Segment, segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    stmt = select(Shot).where(Shot.segment_id == segment_id).order_by(Shot.index)
    result = await db.execute(stmt)
    segment.shots = list(result.scalars().all())

    characters, scenes = await _get_project_assets(project_id, db)
    episode = await _get_episode(project_id, episode_id, db)

    await video_engine.regenerate_segment(
        segment=segment,
        characters=characters,
        scenes=scenes,
        project_id=project_id,
        ep_num=episode.number,
    )

    await db.flush()
    return {"message": "Segment regenerated", "status": segment.status.value}


@router.post("/projects/{project_id}/episodes/{episode_id}/compose")
async def compose_episode(
    project_id: int,
    episode_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Compose all segments into a full episode video."""
    episode = await _get_episode(project_id, episode_id, db)

    stmt = (
        select(Segment)
        .where(Segment.episode_id == episode_id)
        .order_by(Segment.index)
    )
    result = await db.execute(stmt)
    segments = list(result.scalars().all())

    completed = [s for s in segments if s.status == SegmentStatus.COMPLETED]
    if not completed:
        raise HTTPException(status_code=400, detail="No completed segments to compose")

    video_url = await video_engine.compose_full_episode(
        segments=completed,
        project_id=project_id,
        ep_num=episode.number,
    )

    return {"message": "Episode composed", "video_url": video_url}


@router.post("/projects/{project_id}/export")
async def export_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Export project — mark as completed."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.status = ProjectStep.COMPLETED
    await db.flush()

    return {"message": "Project exported", "status": ProjectStep.COMPLETED.value}