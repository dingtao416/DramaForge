"""
DramaForge v2.0 — Storyboard Schemas (Shot + Segment)
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.segment import SegmentStatus


# ── Shot ──

class ShotCharacterRef(BaseModel):
    """A character reference inside a Shot."""
    char_id: int
    appearance_idx: int = 0
    action: str = ""


class ShotDetail(BaseModel):
    id: int
    segment_id: int
    index: int
    duration: Optional[float] = 5.0
    time_of_day: Optional[str] = "day"
    scene_ref: Optional[str] = ""
    camera_type: Optional[str] = "medium"
    camera_angle: Optional[str] = "eye_level"
    camera_movement: Optional[str] = "static"
    characters: list[ShotCharacterRef] = []
    dialogue: Optional[str] = ""
    voice_style: Optional[str] = ""
    background: Optional[str] = ""
    transition: Optional[str] = "cut"
    image_prompt: Optional[str] = ""
    video_prompt: Optional[str] = ""
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ShotUpdate(BaseModel):
    duration: Optional[float] = None
    time_of_day: Optional[str] = None
    scene_ref: Optional[str] = None
    camera_type: Optional[str] = None
    camera_angle: Optional[str] = None
    camera_movement: Optional[str] = None
    characters: Optional[list[ShotCharacterRef]] = None
    dialogue: Optional[str] = None
    voice_style: Optional[str] = None
    background: Optional[str] = None
    transition: Optional[str] = None
    image_prompt: Optional[str] = None
    video_prompt: Optional[str] = None


# ── Segment ──

class SegmentDetail(BaseModel):
    id: int
    episode_id: int
    index: int
    status: SegmentStatus = SegmentStatus.PENDING
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: Optional[float] = None
    shots: list[ShotDetail] = []
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Storyboard (full view) ──

class StoryboardDetail(BaseModel):
    """Complete storyboard for an episode: all segments with their shots."""
    episode_id: int
    episode_title: Optional[str] = ""
    segments: list[SegmentDetail] = []
    total_duration: float = 0.0
    total_shots: int = 0


class StoryboardGenerateRequest(BaseModel):
    """Request to generate storyboard from episode content."""
    shots_per_segment: int = Field(default=5, ge=1, le=20)
    force: bool = False
