"""
DramaForge v2.0 — SceneLocation ORM Model
===========================================
Belongs to Project (1:N). A physical location / backdrop for shots.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.project import Project


class SceneLocation(Base):
    __tablename__ = "scene_locations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, default="")
    time_of_day: Mapped[Optional[str]] = mapped_column(String(50), default="day")
    interior: Mapped[bool] = mapped_column(Boolean, default=True)
    reference_images: Mapped[Optional[list]] = mapped_column(
        JSON, default=list  # List of image URL strings
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # ── Relationships ──
    project: Mapped["Project"] = relationship(
        "Project", back_populates="scenes"
    )

    def __repr__(self) -> str:
        return f"<SceneLocation id={self.id} name='{self.name}'>"
