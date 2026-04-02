"""
DramaForge v2.0 — Character ORM Model
=======================================
Belongs to Project (1:N). Represents a character in the drama.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.project import Project


class CharacterRole(str, enum.Enum):
    """Role type of a character in the drama."""
    PROTAGONIST = "protagonist"   # 主角
    ANTAGONIST = "antagonist"     # 反派
    SUPPORTING = "supporting"     # 配角
    EXTRA = "extra"               # 群演
    NARRATOR = "narrator"         # 旁白


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[CharacterRole] = mapped_column(
        Enum(CharacterRole), default=CharacterRole.SUPPORTING
    )
    description: Mapped[Optional[str]] = mapped_column(Text, default="")
    voice_desc: Mapped[Optional[str]] = mapped_column(String(200), default="")
    reference_images: Mapped[Optional[list]] = mapped_column(
        JSON, default=list  # List of image URL strings
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # ── Relationships ──
    project: Mapped["Project"] = relationship(
        "Project", back_populates="characters"
    )

    def __repr__(self) -> str:
        return f"<Character id={self.id} name='{self.name}' role={self.role.value}>"
