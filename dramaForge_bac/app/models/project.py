"""
DramaForge v2.0 — Project ORM Model
=====================================
Central entity: every script, character, scene belongs to a Project.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.script import Script
    from app.models.character import Character
    from app.models.scene import SceneLocation


# ──────────── Enums ────────────────────────────────────────────────

class ProjectStep(str, enum.Enum):
    """Current workflow step of a project."""
    SCRIPT = "script"           # Step 1 — 剧本大纲
    ASSETS = "assets"           # Step 2 — 角色与场景
    STORYBOARD = "storyboard"   # Step 3 — 分镜生成
    COMPLETED = "completed"     # All done


class VideoStyle(str, enum.Enum):
    """Visual style for generated video."""
    REALISTIC = "realistic"
    ANIME = "anime"
    CARTOON = "cartoon"
    CINEMATIC = "cinematic"
    WATERCOLOR = "watercolor"
    INK_WASH = "ink_wash"


class DramaGenre(str, enum.Enum):
    """Genre classification of the drama."""
    ROMANCE = "romance"         # 甜宠
    SUSPENSE = "suspense"       # 悬疑
    COMEDY = "comedy"           # 搞笑
    FANTASY = "fantasy"         # 奇幻
    URBAN = "urban"             # 都市
    HISTORICAL = "historical"   # 古装
    REVENGE = "revenge"         # 复仇
    THRILLER = "thriller"       # 惊悚
    OTHER = "other"


# ──────────── ORM Model ───────────────────────────────────────────

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, default="")
    style: Mapped[VideoStyle] = mapped_column(
        Enum(VideoStyle), default=VideoStyle.REALISTIC
    )
    aspect_ratio: Mapped[str] = mapped_column(String(20), default="9:16")
    genre: Mapped[DramaGenre] = mapped_column(
        Enum(DramaGenre), default=DramaGenre.OTHER
    )
    status: Mapped[ProjectStep] = mapped_column(
        Enum(ProjectStep), default=ProjectStep.SCRIPT
    )
    script_type: Mapped[str] = mapped_column(
        String(20), default="dialogue"  # "dialogue" | "narration"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ──
    script: Mapped[Optional["Script"]] = relationship(
        "Script", back_populates="project", uselist=False,
        cascade="all, delete-orphan",
    )
    characters: Mapped[list["Character"]] = relationship(
        "Character", back_populates="project",
        cascade="all, delete-orphan",
    )
    scenes: Mapped[list["SceneLocation"]] = relationship(
        "SceneLocation", back_populates="project",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} title='{self.title}' status={self.status.value}>"
