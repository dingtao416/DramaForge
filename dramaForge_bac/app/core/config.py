"""
DramaForge v2.0 — Global Configuration
Loads settings from .env file with validation.
All AI services are unified through laozhang.ai API gateway.
"""

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ----- Server -----
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True
    secret_key: str = "change-me-in-production"

    # ----- Database -----
    database_url: str = "sqlite+aiosqlite:///./storage/dramaforge.db"

    # ----- Redis -----
    redis_url: str = "redis://localhost:6379/0"

    # =============================================
    # Unified API Gateway — laozhang.ai
    # =============================================
    laozhang_api_key: str = ""
    laozhang_base_url: str = "https://api.laozhang.ai/v1"

    # ----- LLM (Text Generation) -----
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096

    # ----- Image Generation -----
    image_model: str = "sora-image"
    image_size: str = "1024x1792"

    # ----- TTS (Text-to-Speech) -----
    tts_model: str = "tts-1-hd"
    tts_default_voice: str = "nova"
    tts_speed: float = 1.0

    # ----- Video Generation -----
    video_model: str = "veo-3.1-fast"
    video_size: str = "1280x720"
    video_seconds: str = "10"
    video_use_async: bool = True
    video_poll_interval: int = 5
    video_timeout: int = 600

    # ----- FFmpeg -----
    ffmpeg_path: str = "ffmpeg"

    # ----- Storage -----
    storage_dir: str = "./storage"

    @property
    def storage_path(self) -> Path:
        path = Path(self.storage_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def projects_path(self) -> Path:
        path = self.storage_path / "projects"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def assets_path(self) -> Path:
        path = self.storage_path / "assets"
        path.mkdir(parents=True, exist_ok=True)
        return path

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton
settings = Settings()
