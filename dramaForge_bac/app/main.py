"""
DramaForge v2.0 — Application Entry Point
"""
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from sqlalchemy import text

from app.api.v2 import projects, scripts, assets, episodes, storyboard, websocket, users, chat, billing, payment, user_ai_config
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown hooks."""
    # ── Startup ──
    # Import all models so Base.metadata is populated
    import app.models  # noqa: F401
    from app.core.database import init_db, close_db, async_engine
    from app.ai_hub import ai_hub

    logger.info("DramaForge v2.0 starting up...")

    # Ensure storage directory exists
    Path(settings.storage_dir).mkdir(parents=True, exist_ok=True)

    # Create database tables
    await init_db()
    logger.info("Database initialized")

    # Seed default billing plans
    from app.services.billing_service import seed_plans
    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        await seed_plans(session)
    logger.info("Billing plans seeded")

    yield  # ── Application running ──

    # ── Shutdown ──
    await ai_hub.close()
    await close_db()
    logger.info("DramaForge v2.0 shut down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="DramaForge",
        description="AI-powered short drama video generation platform",
        version="2.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )

    # ── CORS: configurable origins from env (P3-1) ──
    cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request timing middleware (P3-3) ──
    @app.middleware("http")
    async def timing_middleware(request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        elapsed_ms = (time.time() - start) * 1000
        # Log slow requests (>1s) at warning level
        if elapsed_ms > 1000:
            logger.warning(f"SLOW {request.method} {request.url.path} — {elapsed_ms:.0f}ms")
        else:
            logger.debug(f"{request.method} {request.url.path} — {elapsed_ms:.0f}ms")
        response.headers["X-Response-Time"] = f"{elapsed_ms:.0f}ms"
        return response

    # ── API v2 routers ──────────────────────────────────────────
    prefix = "/api/v2"
    app.include_router(projects.router,   prefix=prefix, tags=["Projects"])
    app.include_router(scripts.router,    prefix=prefix, tags=["Scripts"])
    app.include_router(assets.router,     prefix=prefix, tags=["Assets"])
    app.include_router(episodes.router,   prefix=prefix, tags=["Episodes"])
    app.include_router(storyboard.router, prefix=prefix, tags=["Storyboard"])
    app.include_router(websocket.router,  prefix=prefix, tags=["WebSocket"])
    app.include_router(users.router,      prefix=prefix, tags=["User"])
    app.include_router(chat.router,       prefix=prefix, tags=["Chat"])
    app.include_router(billing.router,    prefix=prefix, tags=["Billing"])
    app.include_router(payment.router,       prefix=prefix, tags=["Payment"])
    app.include_router(user_ai_config.router, prefix=prefix, tags=["User AI Config"])

    # ── Static files (generated assets) ─────────────────────────
    storage_dir = Path(settings.storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/storage", StaticFiles(directory=str(storage_dir)), name="storage")

    # ── Health check (upgraded P3-3) ──
    @app.get("/api/health")
    async def health_check():
        db_ok = False
        redis_ok = False
        try:
            from app.core.database import async_engine
            async with async_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            db_ok = True
        except Exception:
            pass
        try:
            import redis.asyncio as aioredis
            r = aioredis.from_url(settings.redis_url)
            await r.ping()
            await r.close()
            redis_ok = True
        except Exception:
            pass

        all_ok = db_ok  # Redis is optional
        status_code = 200 if all_ok else 503
        return JSONResponse(
            content={
                "status": "ok" if all_ok else "degraded",
                "version": "2.0.0",
                "checks": {
                    "database": "ok" if db_ok else "failed",
                    "redis": "ok" if redis_ok else "unavailable",
                },
            },
            status_code=status_code,
        )

    # ═══════════════════════════════════════════════════════════════
    # P3-2: Global exception handlers
    # ═══════════════════════════════════════════════════════════════

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.warning(f"HTTP {exc.status_code} on {request.method} {request.url.path}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "code": exc.status_code,
                "detail": exc.detail,
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        logger.warning(f"ValueError on {request.method} {request.url.path}: {exc}")
        return JSONResponse(
            status_code=400,
            content={"error": True, "code": 400, "detail": str(exc)},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "code": 500,
                "detail": "服务器内部错误，请稍后重试" if not settings.debug else str(exc),
            },
        )

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
