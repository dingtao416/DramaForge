"""
DramaForge v2.0 — Video Generation Tasks
==========================================
Async background tasks for video segment generation and episode composition.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.models.episode import Episode
from app.models.segment import Segment, SegmentStatus
from app.models.shot import Shot
from app.models.character import Character
from app.models.scene import SceneLocation
from app.models.script import Script
from app.engines.video_engine import video_engine


# Task registry
_active_tasks: dict[str, asyncio.Task] = {}


async def generate_segment_task(
    segment_id: int,
    project_id: int,
    episode_id: int,
) -> dict:
    """
    Background task: generate assets + video for a single segment.
    Pushes progress updates via the task result.
    """
    task_id = f"segment_{segment_id}"
    logger.info(f"Task [{task_id}]: starting segment generation")

    async with AsyncSessionLocal() as db:
        try:
            # Load segment with shots
            stmt = (
                select(Segment)
                .where(Segment.id == segment_id)
                .options(selectinload(Segment.shots))
            )
            result = await db.execute(stmt)
            segment = result.scalar_one_or_none()
            if not segment:
                raise ValueError(f"Segment {segment_id} not found")

            # Load episode
            episode = await db.get(Episode, episode_id)
            if not episode:
                raise ValueError(f"Episode {episode_id} not found")

            # Load assets
            chars_result = await db.execute(
                select(Character).where(Character.project_id == project_id)
            )
            characters = list(chars_result.scalars().all())

            scenes_result = await db.execute(
                select(SceneLocation).where(SceneLocation.project_id == project_id)
            )
            scenes = list(scenes_result.scalars().all())

            # Generate
            segment.status = SegmentStatus.GENERATING
            await db.flush()

            await video_engine.generate_segment_assets(
                segment=segment,
                characters=characters,
                scenes=scenes,
                project_id=project_id,
                ep_num=episode.number,
            )

            # Try generating video
            try:
                await video_engine._generate_segment_video(
                    segment, project_id, episode.number
                )
            except Exception as ve:
                logger.warning(f"Video composition failed (non-fatal): {ve}")
                segment.status = SegmentStatus.COMPLETED  # Assets done, video optional

            await db.commit()

            result_data = {
                "status": "completed",
                "segment_id": segment_id,
                "video_url": segment.video_url,
            }
            logger.info(f"Task [{task_id}]: completed")
            return result_data

        except Exception as e:
            await db.rollback()
            logger.error(f"Task [{task_id}]: failed — {e}")
            return {"status": "failed", "error": str(e)}
        finally:
            _active_tasks.pop(task_id, None)


async def compose_episode_task(
    episode_id: int,
    project_id: int,
) -> dict:
    """
    Background task: compose all completed segments into a full episode.
    """
    task_id = f"compose_{episode_id}"
    logger.info(f"Task [{task_id}]: starting episode composition")

    async with AsyncSessionLocal() as db:
        try:
            episode = await db.get(Episode, episode_id)
            if not episode:
                raise ValueError(f"Episode {episode_id} not found")

            stmt = (
                select(Segment)
                .where(Segment.episode_id == episode_id)
                .where(Segment.status == SegmentStatus.COMPLETED)
                .order_by(Segment.index)
            )
            result = await db.execute(stmt)
            segments = list(result.scalars().all())

            if not segments:
                raise ValueError("No completed segments to compose")

            video_url = await video_engine.compose_full_episode(
                segments=segments,
                project_id=project_id,
                ep_num=episode.number,
            )

            await db.commit()

            result_data = {
                "status": "completed",
                "episode_id": episode_id,
                "video_url": video_url,
            }
            logger.info(f"Task [{task_id}]: completed")
            return result_data

        except Exception as e:
            await db.rollback()
            logger.error(f"Task [{task_id}]: failed — {e}")
            return {"status": "failed", "error": str(e)}
        finally:
            _active_tasks.pop(task_id, None)


def schedule_segment_task(
    segment_id: int, project_id: int, episode_id: int
) -> str:
    """Schedule a segment generation task. Returns task ID."""
    task_id = f"segment_{segment_id}"
    if task_id in _active_tasks:
        return task_id

    task = asyncio.create_task(
        generate_segment_task(segment_id, project_id, episode_id)
    )
    _active_tasks[task_id] = task
    return task_id


def schedule_compose_task(episode_id: int, project_id: int) -> str:
    """Schedule an episode composition task. Returns task ID."""
    task_id = f"compose_{episode_id}"
    if task_id in _active_tasks:
        return task_id

    task = asyncio.create_task(
        compose_episode_task(episode_id, project_id)
    )
    _active_tasks[task_id] = task
    return task_id


def get_task_status(task_id: str) -> dict:
    """Get the status of an active task."""
    task = _active_tasks.get(task_id)
    if not task:
        return {"task_id": task_id, "status": "not_found"}
    if task.done():
        try:
            result = task.result()
            return {"task_id": task_id, **result}
        except Exception as e:
            return {"task_id": task_id, "status": "failed", "error": str(e)}
    return {"task_id": task_id, "status": "running"}
