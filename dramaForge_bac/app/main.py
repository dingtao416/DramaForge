"""
DramaForge v2.0 — Application Entry Point
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.api.v2 import projects, scripts, assets, episodes, storyboard, websocket, users, chat, billing, payment
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown hooks."""
    # ── Startup ──
    # Import all models so Base.metadata is populated
    import app.models  # noqa: F401
    from app.core.database import init_db, close_db
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

    # CORS — allow frontend dev server
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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
    app.include_router(payment.router,    prefix=prefix, tags=["Payment"])

    # ── Static files (generated assets) ─────────────────────────
    storage_dir = Path(settings.storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/storage", StaticFiles(directory=str(storage_dir)), name="storage")

    @app.get("/api/health")
    async def health_check():
        return {"status": "ok", "version": "2.0.0"}

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
