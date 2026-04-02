"""
DramaForge v2.0 — Segment ORM Model
=====================================
Belongs to Episode (1:N). A segment groups consecutive shots into
one composited video clip.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.episode import Episode
    from app.models.shot import Shot


class SegmentStatus(str, enum.Enum):
    """Generation status of a video segment."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class Segment(Base):
    __tablename__ = "segments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    episode_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False
    )

    index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[SegmentStatus] = mapped_column(
        Enum(SegmentStatus), default=SegmentStatus.PENDING
    )

    video_url: Mapped[Optional[str]] = mapped_column(String(500), default=None)
    audio_url: Mapped[Optional[str]] = mapped_column(String(500), default=None)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), default=None)
    duration: Mapped[Optional[float]] = mapped_column(Float, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # ── Relationships ──
    episode: Mapped["Episode"] = relationship(
        "Episode", back_populates="segments"
    )
    shots: Mapped[list["Shot"]] = relationship(
        "Shot", back_populates="segment",
        cascade="all, delete-orphan",
        order_by="Shot.index",
    )

    def __repr__(self) -> str:
        return f"<Segment id={self.id} index={self.index} status={self.status.value}>"
