"""arq worker tasks for persistent media generation jobs."""

from __future__ import annotations

from loguru import logger
from arq.connections import RedisSettings, create_pool

from app.core.config import settings
from app.core.database import AsyncSessionLocal, close_db
from app.services.media_generation_service import media_generation_service


async def run_media_generation_job(ctx: dict, job_id: int) -> dict:
    """Run a persisted image/video generation job by id."""
    async with AsyncSessionLocal() as db:
        job = await media_generation_service.run_job_by_id(db=db, job_id=job_id)
        await db.commit()
        logger.info("Media job {} finished with status {}", job.id, job.status.value)
        return {
            "job_id": job.id,
            "status": job.status.value,
            "progress": job.progress,
            "error": job.error,
        }


async def enqueue_media_job(job_id: int) -> str:
    """Enqueue a media job on Redis/arq and return the arq job id."""
    redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    try:
        queued = await redis.enqueue_job("run_media_generation_job", job_id)
        if queued is None:
            raise RuntimeError("arq rejected media generation job")
        return queued.job_id
    finally:
        await redis.close()


async def shutdown(ctx: dict) -> None:
    await close_db()


class WorkerSettings:
    functions = [run_media_generation_job]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    on_shutdown = shutdown
