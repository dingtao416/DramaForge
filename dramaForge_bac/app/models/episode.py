"""
DramaForge v2.0 — Episode ORM Model
=====================================
Belongs to Script (1:N). Each episode holds one chunk of the story.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.script import Script
    from app.models.segment import Segment


class Episode(Base):
    __tablename__ = "episodes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    script_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False
    )

    number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(200), default="")
    content: Mapped[Optional[str]] = mapped_column(Text, default="")

    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # ── Relationships ──
    script: Mapped["Script"] = relationship(
        "Script", back_populates="episodes"
    )
    segments: Mapped[list["Segment"]] = relationship(
        "Segment", back_populates="episode",
        cascade="all, delete-orphan",
        order_by="Segment.index",
    )

    def __repr__(self) -> str:
        return f"<Episode id={self.id} number={self.number} title='{self.title}'>"
