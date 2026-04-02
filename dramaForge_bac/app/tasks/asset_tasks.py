"""
DramaForge v2.0 — Asset Generation Tasks
==========================================
Async background tasks for asset generation.
Uses simple asyncio tasks (can be upgraded to arq/celery later).
"""

from __future__ import annotations

import asyncio
from typing import Optional

from loguru import logger

from app.core.database import AsyncSessionLocal
from app.models.project import Project
from app.models.script import Script
from app.models.character import Character
from app.models.scene import SceneLocation
from app.engines.assets_engine import assets_engine

from sqlalchemy import select


# Task registry for tracking active tasks
_active_tasks: dict[str, asyncio.Task] = {}


async def generate_all_assets_task(project_id: int) -> dict:
    """
    Background task: generate all character + scene assets for a project.

    Returns:
        dict with counts of generated characters and scenes.
    """
    task_id = f"assets_{project_id}"
    logger.info(f"Task [{task_id}]: starting asset generation")

    async with AsyncSessionLocal() as db:
        try:
            # Load data
            project = await db.get(Project, project_id)
            if not project:
                raise ValueError(f"Project {project_id} not found")

            script_result = await db.execute(
                select(Script).where(Script.project_id == project_id)
            )
            script = script_result.scalar_one_or_none()
            if not script:
                raise ValueError("No script found")

            chars_result = await db.execute(
                select(Character).where(Character.project_id == project_id)
            )
            characters = list(chars_result.scalars().all())

            scenes_result = await db.execute(
                select(SceneLocation).where(SceneLocation.project_id == project_id)
            )
            scenes = list(scenes_result.scalars().all())

            # Generate
            updated_chars, updated_scenes = await assets_engine.generate_all_assets(
                script=script,
                characters=characters,
                scenes=scenes,
                project_id=project_id,
            )

            await db.commit()

            result = {
                "status": "completed",
                "characters": len(updated_chars),
                "scenes": len(updated_scenes),
            }
            logger.info(f"Task [{task_id}]: completed — {result}")
            return result

        except Exception as e:
            await db.rollback()
            logger.error(f"Task [{task_id}]: failed — {e}")
            return {"status": "failed", "error": str(e)}
        finally:
            _active_tasks.pop(task_id, None)


async def regenerate_character_task(
    char_id: int,
    project_id: int,
    prompt: Optional[str] = None,
) -> dict:
    """Background task: regenerate a single character's image."""
    task_id = f"regen_char_{char_id}"
    logger.info(f"Task [{task_id}]: starting character regeneration")

    async with AsyncSessionLocal() as db:
        try:
            character = await db.get(Character, char_id)
            if not character:
                raise ValueError(f"Character {char_id} not found")

            url = await assets_engine.regenerate_character_image(
                character=character,
                project_id=project_id,
                prompt=prompt,
            )

            await db.commit()

            result = {"status": "completed", "image_url": url}
            logger.info(f"Task [{task_id}]: completed")
            return result

        except Exception as e:
            await db.rollback()
            logger.error(f"Task [{task_id}]: failed — {e}")
            return {"status": "failed", "error": str(e)}
        finally:
            _active_tasks.pop(task_id, None)


def schedule_assets_task(project_id: int) -> str:
    """Schedule an asset generation task. Returns task ID."""
    task_id = f"assets_{project_id}"
    if task_id in _active_tasks:
        return task_id  # Already running

    task = asyncio.create_task(generate_all_assets_task(project_id))
    _active_tasks[task_id] = task
    return task_id


def schedule_character_regen_task(
    char_id: int, project_id: int, prompt: Optional[str] = None
) -> str:
    """Schedule a character regeneration task. Returns task ID."""
    task_id = f"regen_char_{char_id}"
    if task_id in _active_tasks:
        return task_id

    task = asyncio.create_task(
        regenerate_character_task(char_id, project_id, prompt)
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
