"""
DramaForge v2.0 — Shot ORM Model
==================================
The atomic unit of video generation. Each Shot produces one image + audio,
which are then composed into a video clip.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.segment import Segment


class CameraType(str, enum.Enum):
    """Type of camera shot."""
    CLOSE_UP = "close_up"           # 特写
    MEDIUM = "medium"               # 中景
    FULL = "full"                   # 全景
    WIDE = "wide"                   # 远景
    EXTREME_CLOSE = "extreme_close" # 大特写
    OVER_SHOULDER = "over_shoulder" # 过肩
    POV = "pov"                     # 主观视角
    AERIAL = "aerial"              # 航拍


class CameraMovement(str, enum.Enum):
    """Camera movement style."""
    STATIC = "static"         # 固定
    PAN = "pan"               # 摇
    TILT = "tilt"             # 俯仰
    ZOOM_IN = "zoom_in"       # 推
    ZOOM_OUT = "zoom_out"     # 拉
    DOLLY = "dolly"           # 移
    TRACKING = "tracking"     # 跟
    HANDHELD = "handheld"     # 手持


class Shot(Base):
    __tablename__ = "shots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    segment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("segments.id", ondelete="CASCADE"), nullable=False
    )

    index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration: Mapped[Optional[float]] = mapped_column(Float, default=5.0)
    time_of_day: Mapped[Optional[str]] = mapped_column(String(50), default="day")

    # Scene & Camera
    scene_ref: Mapped[Optional[str]] = mapped_column(String(100), default="")
    camera_type: Mapped[Optional[str]] = mapped_column(String(50), default="medium")
    camera_angle: Mapped[Optional[str]] = mapped_column(String(50), default="eye_level")
    camera_movement: Mapped[Optional[str]] = mapped_column(String(50), default="static")

    # Characters in this shot: [{char_id, appearance_idx, action}]
    characters: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    # Dialogue & Audio
    dialogue: Mapped[Optional[str]] = mapped_column(Text, default="")
    voice_style: Mapped[Optional[str]] = mapped_column(String(100), default="")

    # Visuals
    background: Mapped[Optional[str]] = mapped_column(Text, default="")
    transition: Mapped[Optional[str]] = mapped_column(String(50), default="cut")

    # AI Prompts
    image_prompt: Mapped[Optional[str]] = mapped_column(Text, default="")
    video_prompt: Mapped[Optional[str]] = mapped_column(Text, default="")

    # Generated asset URLs
    image_url: Mapped[Optional[str]] = mapped_column(String(500), default=None)
    audio_url: Mapped[Optional[str]] = mapped_column(String(500), default=None)
    video_url: Mapped[Optional[str]] = mapped_column(String(500), default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # ── Relationships ──
    segment: Mapped["Segment"] = relationship(
        "Segment", back_populates="shots"
    )

    def __repr__(self) -> str:
        return f"<Shot id={self.id} index={self.index} duration={self.duration}>"
