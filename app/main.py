"""
DramaForge - AI Short Drama Engine
FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.api import pipeline_router, projects_router
from app.models.database import init_db
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown."""
    # Startup
    logger.info("🎬 DramaForge - AI Short Drama Engine starting up...")
    init_db()
    logger.info("✅ Database initialized")

    # Ensure storage directories exist
    settings.storage_path
    settings.images_path
    settings.audio_path
    settings.videos_path
    logger.info(f"✅ Storage directory: {settings.storage_dir}")

    logger.info(f"🤖 Default LLM: {settings.default_llm_provider}")
    logger.info(f"🖼️  Image provider: {settings.image_provider}")
    logger.info(f"🔊 TTS provider: {settings.tts_provider}")
    logger.info("🚀 DramaForge is ready!")

    yield

    # Shutdown
    logger.info("👋 DramaForge shutting down...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="DramaForge - AI Short Drama Engine",
        description="AI-powered short drama production platform with script generation, "
                    "storyboarding, image synthesis, TTS, and video composition.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files for serving generated assets
    app.mount("/storage", StaticFiles(directory=settings.storage_dir), name="storage")

    # Register API routers
    app.include_router(projects_router)
    app.include_router(pipeline_router)

    # Health check
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": "DramaForge",
            "version": "0.1.0",
            "llm_provider": settings.default_llm_provider,
            "image_provider": settings.image_provider,
            "tts_provider": settings.tts_provider,
        }

    return app


# Create the app instance
app = create_app()
