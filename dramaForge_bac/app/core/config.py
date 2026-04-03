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

    # ----- JWT Authentication -----
    jwt_secret_key: str = "dramaforge-jwt-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 1 day
    jwt_refresh_expire_days: int = 7

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
    llm_model: str = "gpt-4.1-mini"          # 默认对话：快速、低成本 ($0.40/M)
    llm_model_creative: str = "gpt-4o"        # 剧本创作：创意能力强
    llm_model_deep: str = "claude-sonnet-4-20250514"  # 深度编剧：长文本最佳
    llm_model_fast: str = "glm-4.5-flash"     # 极速回复：$0.01/M 接近免费
    llm_model_value: str = "deepseek-v3.1"    # 高性价比：中文理解好
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096

    # ----- Image Generation -----
    image_model: str = "gpt-image-1-mini"     # 默认：OpenAI 原生，质量好
    image_model_hq: str = "midjourney-imagine" # 高质量：Midjourney 艺术级
    image_model_text: str = "ideogram-v3"     # 文字渲染：海报/字幕
    image_size: str = "1024x1792"             # 竖版 9:16

    # ----- TTS (Text-to-Speech) -----
    tts_model: str = "tts-1-hd"
    tts_default_voice: str = "nova"
    tts_speed: float = 1.0

    # ----- Video Generation -----
    video_model: str = "seedance-2.0"         # 默认：火山引擎 SeeDance 高性价比
    video_model_hq: str = "kling-v2.1"        # 高质量：可灵最新版
    video_model_fast: str = "veo-3.1-fast"    # 快速出片：Google VEO
    video_model_i2v: str = "wan-v2.1-i2v"     # 图生视频：阿里万象
    video_size: str = "720x1280"              # 竖版 9:16
    video_aspect_ratio: str = "9:16"
    video_seconds: str = "5"
    video_use_async: bool = True
    video_poll_interval: int = 5
    video_timeout: int = 600

    # ----- FFmpeg -----
    ffmpeg_path: str = "ffmpeg"

    # ----- Payment: WeChat Pay -----
    wechat_mch_id: str = ""
    wechat_api_key_v3: str = ""
    wechat_app_id: str = ""
    wechat_serial_no: str = ""
    wechat_cert_path: str = ""

    # ----- Payment: Alipay -----
    alipay_app_id: str = ""
    alipay_private_key_path: str = ""
    alipay_public_key_path: str = ""

    # ----- Payment: Douyin Pay -----
    douyin_app_id: str = ""
    douyin_app_secret: str = ""
    douyin_merchant_id: str = ""
    douyin_salt: str = ""

    # ----- Payment: General -----
    payment_notify_base_url: str = "https://api.dramaforge.com"

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
