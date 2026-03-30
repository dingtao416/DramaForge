"""
DramaForge - Global Configuration
Loads settings from .env file with validation.
All AI services are unified through laozhang.ai API gateway.
"""

from pathlib import Path
from typing import Literal, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ----- Server -----
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True
    secret_key: str = "change-me-in-production"

    # ----- Database -----
    database_url: str = "sqlite:///./storage/dramaforge.db"

    # ----- Redis -----
    redis_url: str = "redis://localhost:6379/0"

    # =============================================
    # Unified API Gateway - laozhang.ai
    # All AI services go through this single gateway
    # =============================================
    laozhang_api_key: str = ""
    laozhang_base_url: str = "https://api.laozhang.ai/v1"

    # ----- LLM (Text Generation) -----
    # Supported: gpt-4.1, gpt-4o, claude-sonnet-4-20250514, gemini-2.5-pro,
    #            deepseek-v3, deepseek-r1, qwen-max, etc.
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096

    # ----- Image Generation -----
    # Supported models & pricing:
    #   sora-image       - $0.01/张 (性价比之王, 推荐批量)
    #   flux-pro         - $0.035/张 (灵活比例 3:7~7:3)
    #   flux-max         - $0.07/张 (最高质量)
    #   nano-banana      - $0.025/张 (Base64输出)
    #   nano-banana-pro  - $0.05/张 (4K高清)
    #   gpt-image-1      - 按Token计费
    image_model: str = "sora-image"
    image_size: str = "1024x1792"  # Vertical for short drama

    # ----- TTS (Text-to-Speech) -----
    # Models: tts-1 (标准, 快速) | tts-1-hd (高清, 更自然)
    # Voices: alloy, echo, fable, onyx, nova, shimmer
    tts_model: str = "tts-1-hd"
    tts_default_voice: str = "nova"
    tts_speed: float = 1.0  # 0.25 ~ 4.0

    # ----- Video Generation (Sora 2) -----
    # Sync models: sora_video2, sora_video2-landscape,
    #              sora_video2-15s, sora_video2-landscape-15s
    # Async models: sora-2 ($0.15/次), sora-2-pro ($0.8/次, 1080P)
    video_model: str = "sora-2"
    video_size: str = "1280x720"  # 1280x720 横屏 | 720x1280 竖屏
    video_seconds: str = "10"  # "10" 或 "15"
    video_use_async: bool = True  # 推荐使用异步API，失败不扣费
    video_poll_interval: int = 5  # 异步轮询间隔(秒)
    video_timeout: int = 600  # 异步超时(秒)

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
    def images_path(self) -> Path:
        path = self.storage_path / "images"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def audio_path(self) -> Path:
        path = self.storage_path / "audio"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def videos_path(self) -> Path:
        path = self.storage_path / "videos"
        path.mkdir(parents=True, exist_ok=True)
        return path

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton
settings = Settings()
