"""
DramaForge v2.0 — Episodes API
================================
Endpoints for episode management and statistics.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.script import Script
from app.models.episode import Episode
from app.models.segment import Segment
from app.models.shot import Shot
from app.schemas.episode import EpisodeOverview, EpisodeDetail

router = APIRouter()


@router.get("/projects/{project_id}/episodes", response_model=list[EpisodeOverview])
async def list_episodes(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """List all episodes with statistics (character count, scene count, etc.)."""
    # Get script for the project
    stmt = (
        select(Script)
        .where(Script.project_id == project_id)
        .options(selectinload(Script.episodes))
    )
    result = await db.execute(stmt)
    script = result.scalar_one_or_none()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    episodes_data = []
    for ep in script.episodes:
        # Count segments and shots
        seg_stmt = select(Segment).where(Segment.episode_id == ep.id)
        seg_result = await db.execute(seg_stmt)
        segments = seg_result.scalars().all()

        total_shots = 0
        total_duration = 0.0
        unique_chars = set()
        unique_scenes = set()

        for seg in segments:
            shot_stmt = select(Shot).where(Shot.segment_id == seg.id)
            shot_result = await db.execute(shot_stmt)
            shots = shot_result.scalars().all()
            total_shots += len(shots)
            for shot in shots:
                if shot.duration:
                    total_duration += shot.duration
                if shot.scene_ref:
                    unique_scenes.add(shot.scene_ref)
                if shot.characters:
                    for ch in shot.characters:
                        if isinstance(ch, dict) and "char_id" in ch:
                            unique_chars.add(ch["char_id"])

        episodes_data.append(
            EpisodeOverview(
                id=ep.id,
                number=ep.number,
                title=ep.title,
                is_approved=ep.is_approved,
                character_count=len(unique_chars),
                scene_count=len(unique_scenes),
                segment_count=len(segments),
                total_duration=total_duration,
                created_at=ep.created_at,
            )
        )

    return episodes_data


@router.get("/projects/{project_id}/episodes/{episode_id}", response_model=EpisodeDetail)
async def get_episode(
    project_id: int,
    episode_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get full episode details."""
    episode = await db.get(Episode, episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    # Verify it belongs to the right project
    stmt = select(Script).where(Script.id == episode.script_id)
    result = await db.execute(stmt)
    script = result.scalar_one_or_none()
    if not script or script.project_id != project_id:
        raise HTTPException(status_code=404, detail="Episode not found in this project")

    return episode