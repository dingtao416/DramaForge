"""
DramaForge AI Hub - Data Models
Pydantic models for all AI service requests and responses.
Callers use these typed models — never raw dicts.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# Chat / LLM
# ─────────────────────────────────────────────

class ChatMessage(BaseModel):
    """A single message in a conversation."""
    role: str = "user"  # system | user | assistant
    content: str | list[Any] = ""


class ChatRequest(BaseModel):
    """Parameters for a chat completion request."""
    messages: list[ChatMessage]
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    response_format: Optional[dict] = None
    stream: bool = False


class ChatResponse(BaseModel):
    """Result of a chat completion."""
    content: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    finish_reason: str = ""


# ─────────────────────────────────────────────
# Image Generation
# ─────────────────────────────────────────────

class ImageRequest(BaseModel):
    """Parameters for an image generation request."""
    prompt: str
    model: Optional[str] = None
    size: Optional[str] = None  # e.g. "1024x1792"
    n: int = 1
    response_format: str = "b64_json"  # "b64_json" | "url"


class ImageResponse(BaseModel):
    """Result of an image generation."""
    image_path: str
    image_url: Optional[str] = None
    model: str = ""
    revised_prompt: Optional[str] = None


# ─────────────────────────────────────────────
# TTS (Text-to-Speech)
# ─────────────────────────────────────────────

class TTSRequest(BaseModel):
    """Parameters for a TTS request."""
    text: str
    model: Optional[str] = None   # tts-1 | tts-1-hd
    voice: Optional[str] = None   # alloy | echo | fable | onyx | nova | shimmer
    speed: Optional[float] = None  # 0.25 ~ 4.0
    response_format: str = "mp3"  # mp3 | opus | aac | flac | wav | pcm


class TTSResponse(BaseModel):
    """Result of a TTS generation."""
    audio_path: str
    model: str = ""
    voice: str = ""
    duration: Optional[float] = None  # estimated seconds


# ─────────────────────────────────────────────
# STT (Speech-to-Text)
# ─────────────────────────────────────────────

class STTRequest(BaseModel):
    """Parameters for a speech-to-text request."""
    audio_path: str
    model: Optional[str] = None  # gpt-4o-transcribe | whisper-1
    language: Optional[str] = None
    response_format: str = "json"  # json | text | srt | verbose_json | vtt


class STTResponse(BaseModel):
    """Result of a speech-to-text transcription."""
    text: str
    language: Optional[str] = None
    duration: Optional[float] = None
    segments: Optional[list[dict]] = None


# ─────────────────────────────────────────────
# Video Generation (Sora 2)
# ─────────────────────────────────────────────

class VideoStatus(str, Enum):
    """Status of an async video generation task."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoRequest(BaseModel):
    """Parameters for a video generation request."""
    prompt: str
    model: Optional[str] = None   # sora-2 | sora-2-pro
    size: Optional[str] = None    # "1280x720" | "720x1280"
    seconds: Optional[str] = None  # "10" | "15"
    use_async: Optional[bool] = None  # True=async API, False=sync API


class VideoResponse(BaseModel):
    """Result of a video generation."""
    video_path: str
    video_url: Optional[str] = None
    model: str = ""
    status: VideoStatus = VideoStatus.COMPLETED
    duration: Optional[float] = None
    task_id: Optional[str] = None


class VideoTaskStatus(BaseModel):
    """Status of an async video generation task."""
    task_id: str
    status: VideoStatus
    video_url: Optional[str] = None
    progress: Optional[float] = None  # 0.0 ~ 1.0
    error: Optional[str] = None
