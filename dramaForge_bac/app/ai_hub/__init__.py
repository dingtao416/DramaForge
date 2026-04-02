"""
DramaForge AI Hub - Unified AI Service Gateway
================================================

All AI capabilities through one entry point, powered by laozhang.ai.

Usage:
    from app.ai_hub import ai_hub

    # ── Text Generation (LLM) ──
    answer = await ai_hub.chat.ask("写一个悬疑故事开头")
    data   = await ai_hub.chat.ask_json("列出3个角色，返回JSON")
    resp   = await ai_hub.chat.complete(messages=[...])
    data   = await ai_hub.chat.complete_json(messages=[...])
    async for chunk in ai_hub.chat.stream(messages=[...]):
        print(chunk, end="")

    # ── Image Generation ──
    img = await ai_hub.image.generate("樱花树下的女孩", "out.png")
    imgs = await ai_hub.image.generate_batch(prompts, "output_dir/")

    # ── Text-to-Speech ──
    audio = await ai_hub.tts.speak("你好世界", "hello.mp3")
    audios = await ai_hub.tts.speak_batch(items, "output_dir/")
    voices = ai_hub.tts.list_voices()

    # ── Video Generation (Sora 2) ──
    video = await ai_hub.video.generate("海边日落漫步", "sunset.mp4")
    status = await ai_hub.video.get_task_status(task_id)

    # ── Lifecycle ──
    await ai_hub.close()   # Call on app shutdown
"""

from __future__ import annotations

from app.ai_hub._client import BaseClient
from app.ai_hub.chat import ChatService
from app.ai_hub.image import ImageService
from app.ai_hub.prompt import PromptService
from app.ai_hub.tts import TTSService
from app.ai_hub.video import VideoService

# Re-export models for convenience
from app.ai_hub._models import (
    ChatMessage,
    ChatResponse,
    ImageResponse,
    TTSResponse,
    VideoResponse,
    VideoStatus,
    VideoTaskStatus,
)

# Re-export errors
from app.ai_hub._client import (
    HubClientError,
    AuthError,
    QuotaError,
    RateLimitError,
    ModelError,
)


class AIHub:
    """
    Facade - single entry point for all AI services.

    Instantiated as a module-level singleton `ai_hub`.
    Each sub-service is a lazy attribute (created on first access).
    """

    def __init__(self):
        self._chat: ChatService | None = None
        self._image: ImageService | None = None
        self._prompt: PromptService | None = None
        self._tts: TTSService | None = None
        self._video: VideoService | None = None

    # ──────────── Sub-service accessors (lazy init) ────────────

    @property
    def chat(self) -> ChatService:
        """Text generation (LLM) service."""
        if self._chat is None:
            self._chat = ChatService()
        return self._chat

    @property
    def image(self) -> ImageService:
        """Image generation service."""
        if self._image is None:
            self._image = ImageService()
        return self._image

    @property
    def prompt(self) -> PromptService:
        """Prompt optimization & construction service."""
        if self._prompt is None:
            self._prompt = PromptService()
        return self._prompt

    @property
    def tts(self) -> TTSService:
        """Text-to-Speech service."""
        if self._tts is None:
            self._tts = TTSService()
        return self._tts

    @property
    def video(self) -> VideoService:
        """Video generation (Sora 2) service."""
        if self._video is None:
            self._video = VideoService()
        return self._video

    # ──────────── Lifecycle ────────────

    async def close(self):
        """Gracefully shutdown all HTTP clients. Call on app exit."""
        await BaseClient.close()


# Module-level singleton - import this
ai_hub = AIHub()


__all__ = [
    # The singleton
    "ai_hub",
    "AIHub",
    # Services
    "PromptService",
    # Models
    "ChatMessage",
    "ChatResponse",
    "ImageResponse",
    "TTSResponse",
    "VideoResponse",
    "VideoStatus",
    "VideoTaskStatus",
    # Errors
    "HubClientError",
    "AuthError",
    "QuotaError",
    "RateLimitError",
    "ModelError",
]
