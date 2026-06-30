"""Storyboard generation orchestration and progress state."""

from __future__ import annotations

import json

import redis.asyncio as aioredis
from loguru import logger
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.engines.video_engine import video_engine
from app.models.character import Character
from app.models.episode import Episode
from app.models.scene import SceneLocation
from app.models.segment import Segment
from app.models.script import Script
from app.services.user_model_resolver import user_model_resolver

STORYBOARD_PROGRESS_TTL_SECONDS = 60 * 60


def _progress_key(project_id: int, episode_id: int, user_id: int | None = None) -> str:
    if user_id is not None:
        return f"storyboard:generation:{user_id}:{project_id}:{episode_id}"
    return f"storyboard:generation:{project_id}:{episode_id}"


def _legacy_progress_keys(episode_id: int, user_id: int) -> list[str]:
    return [
        f"storyboard:generation:{episode_id}",
        f"storyboard:generation:{user_id}:{episode_id}",
    ]


async def set_storyboard_progress(project_id: int, episode_id: int, status: str, progress: int, message: str, *, user_id: int | None = None) -> None:
    redis = aioredis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    try:
        cancelled = False
        try:
            raw = await redis.get(_progress_key(project_id, episode_id, user_id))
            if raw:
                existing = json.loads(raw)
                if isinstance(existing, dict):
                    cancelled = bool(existing.get("cancelled") or existing.get("status") == "cancelled")
        except Exception:
            pass

        data = {
            "status": "cancelled" if cancelled and status == "generating" else status,
            "progress": max(0, min(100, progress)),
            "message": message,
        }
        if cancelled or status == "cancelled":
            data["cancelled"] = True

        key = _progress_key(project_id, episode_id, user_id)
        await redis.set(
            key,
            json.dumps(data, ensure_ascii=False),
            ex=STORYBOARD_PROGRESS_TTL_SECONDS,
        )
    except Exception as exc:
        logger.warning("Failed to write storyboard progress for episode {}: {}", episode_id, exc)
    finally:
        await redis.close()


async def get_storyboard_progress(project_id: int, episode_id: int, *, user_id: int | None = None) -> dict[str, object] | None:
    redis = aioredis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    try:
        raw = await redis.get(_progress_key(project_id, episode_id, user_id))
    except Exception as exc:
        logger.warning("Failed to read storyboard progress for episode {}: {}", episode_id, exc)
        return None
    finally:
        await redis.close()

    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return data


async def cancel_storyboard_generation(project_id: int, episode_id: int, *, user_id: int | None = None) -> None:
    """Set a cancellation flag on the storyboard generation progress entry."""
    current = await get_storyboard_progress(project_id, episode_id, user_id=user_id)
    if not current:
        return
    await set_storyboard_progress(
        project_id,
        episode_id,
        "cancelled",
        int(current.get("progress", 0) or 0),
        "分镜生成已取消",
        user_id=user_id,
    )


async def is_storyboard_cancelled(project_id: int, episode_id: int, *, user_id: int | None = None) -> bool:
    """Check if the storyboard generation for this episode has been cancelled."""
    progress = await get_storyboard_progress(project_id, episode_id, user_id=user_id)
    if not progress:
        return False
    return bool(progress.get("cancelled") or progress.get("status") == "cancelled")


async def _get_project_assets(project_id: int, db: AsyncSession):
    chars = await db.execute(
        select(Character).where(Character.project_id == project_id)
    )
    scenes = await db.execute(
        select(SceneLocation).where(SceneLocation.project_id == project_id)
    )
    return list(chars.scalars().all()), list(scenes.scalars().all())


async def _get_episode_for_project(project_id: int, episode_id: int, db: AsyncSession) -> Episode | None:
    stmt = (
        select(Episode)
        .join(Script, Episode.script_id == Script.id)
        .where(Episode.id == episode_id, Script.project_id == project_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def run_storyboard_generation(
    *,
    project_id: int,
    episode_id: int,
    user_id: int,
    shots_per_segment: int = 5,
) -> dict[str, object]:
    async with AsyncSessionLocal() as db:
        try:
            await set_storyboard_progress(project_id, episode_id, "generating", 10, "加载剧集内容", user_id=user_id)
            episode = await _get_episode_for_project(project_id, episode_id, db)
            if not episode:
                logger.error("Storyboard generation: episode {} not found", episode_id)
                await set_storyboard_progress(project_id, episode_id, "failed", 100, "剧集不存在", user_id=user_id)
                return {"episode_id": episode_id, "status": "failed"}

            await set_storyboard_progress(project_id, episode_id, "generating", 20, "读取角色与场景", user_id=user_id)
            characters, scenes = await _get_project_assets(project_id, db)

            if not episode.content:
                logger.error("Storyboard generation: episode {} has no content", episode_id)
                await set_storyboard_progress(project_id, episode_id, "failed", 100, "剧集正文为空", user_id=user_id)
                return {"episode_id": episode_id, "status": "failed"}

            if await is_storyboard_cancelled(project_id, episode_id, user_id=user_id):
                await set_storyboard_progress(project_id, episode_id, "cancelled", 100, "分镜生成已取消", user_id=user_id)
                return {"episode_id": episode_id, "status": "cancelled"}

            await set_storyboard_progress(project_id, episode_id, "generating", 32, "连接剧本模型", user_id=user_id)
            chat_resolved = await user_model_resolver.resolve(db, user_id, "chat")

            if await is_storyboard_cancelled(project_id, episode_id, user_id=user_id):
                await set_storyboard_progress(project_id, episode_id, "cancelled", 100, "分镜生成已取消", user_id=user_id)
                return {"episode_id": episode_id, "status": "cancelled"}

            await set_storyboard_progress(project_id, episode_id, "generating", 48, "生成分镜结构", user_id=user_id)
            # Load script for Story Bible context
            script_stmt = select(Script).where(Script.project_id == project_id)
            script_result = await db.execute(script_stmt)
            script = script_result.scalar_one_or_none()

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
                script=script,
            )

            if await is_storyboard_cancelled(project_id, episode_id, user_id=user_id):
                await set_storyboard_progress(project_id, episode_id, "cancelled", 100, "分镜生成已取消", user_id=user_id)
                return {"episode_id": episode_id, "status": "cancelled"}

            if not await _get_episode_for_project(project_id, episode_id, db):
                logger.warning("Storyboard generation: episode {} disappeared before write", episode_id)
                await set_storyboard_progress(project_id, episode_id, "failed", 100, "剧集已被删除，分镜生成中止", user_id=user_id)
                return {"episode_id": episode_id, "status": "failed"}

            await set_storyboard_progress(project_id, episode_id, "generating", 88, "写入分镜结果", user_id=user_id)
            for segment in segments:
                db.add(segment)
            await db.commit()

            total_shots = sum(len(seg.shots) for seg in segments)
            logger.info(
                "Storyboard generated for episode {}: {} segments, {} shots",
                episode_id,
                len(segments),
                total_shots,
            )
            await set_storyboard_progress(project_id, episode_id, "completed", 100, "分镜生成完成", user_id=user_id)
            return {
                "episode_id": episode_id,
                "status": "completed",
                "segments": len(segments),
                "shots": total_shots,
            }
        except IntegrityError:
            logger.error(
                "Storyboard generation: FOREIGN KEY constraint failed for episode {} — "
                "the episode or its parent project may have been deleted during generation",
                episode_id,
            )
            await db.rollback()
            await set_storyboard_progress(project_id, episode_id, "failed", 100, "剧集已被删除，分镜生成中止", user_id=user_id)
            return {"episode_id": episode_id, "status": "failed", "error": "Episode or project deleted during generation"}
        except Exception as exc:
            logger.error("Storyboard generation failed for episode {}: {}", episode_id, exc)
            await db.rollback()
            await set_storyboard_progress(project_id, episode_id, "failed", 100, str(exc)[:120] or "分镜生成失败", user_id=user_id)
            return {"episode_id": episode_id, "status": "failed", "error": str(exc)[:2000]}


async def cleanup_project_storyboard_progress(project_id: int, user_id: int, episode_ids: list[int] | None = None) -> None:
    """Delete all Redis progress keys for a project's episodes on project deletion.

    Call this after deleting a project to ensure stale storyboard progress
    does not leak into future projects.
    """
    redis = aioredis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    try:
        patterns = [
            f"storyboard:generation:{user_id}:{project_id}:*",
            f"storyboard:generation:{project_id}:*",
        ]
        deleted = 0
        for pattern in patterns:
            cursor = 0
            while True:
                cursor, keys = await redis.scan(cursor, match=pattern, count=100)
                if keys:
                    for key in keys:
                        await redis.delete(key)
                        deleted += 1
                if cursor == 0:
                    break
        for episode_id in episode_ids or []:
            for key in _legacy_progress_keys(episode_id, user_id):
                deleted += await redis.delete(key)
        if deleted:
            logger.info(
                "Cleaned up {} storyboard progress keys for project {} (user {})",
                deleted, project_id, user_id,
            )
    except Exception as exc:
        logger.warning(
            "Failed to clean up storyboard progress for project {}: {}",
            project_id, exc,
        )
    finally:
        await redis.close()
