"""
DramaForge v2.0 — Script ORM Model
====================================
One-to-one with Project. Holds the full structured script data.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.episode import Episode


class Script(Base):
    __tablename__ = "scripts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    protagonist: Mapped[Optional[str]] = mapped_column(String(100), default="")
    genre: Mapped[Optional[str]] = mapped_column(String(50), default="")
    synopsis: Mapped[Optional[str]] = mapped_column(Text, default="")
    background: Mapped[Optional[str]] = mapped_column(Text, default="")
    setting: Mapped[Optional[str]] = mapped_column(Text, default="")
    one_liner: Mapped[Optional[str]] = mapped_column(String(200), default="")
    raw_content: Mapped[Optional[str]] = mapped_column(Text, default="")

    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # ── Relationships ──
    project: Mapped["Project"] = relationship(
        "Project", back_populates="script"
    )
    episodes: Mapped[list["Episode"]] = relationship(
        "Episode", back_populates="script",
        cascade="all, delete-orphan",
        order_by="Episode.number",
    )

    def __repr__(self) -> str:
        return f"<Script id={self.id} project_id={self.project_id} approved={self.is_approved}>"
