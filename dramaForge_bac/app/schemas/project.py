"""
DramaForge v2.0 — Project Schemas
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.project import DramaGenre, ProjectStep, VideoStyle


# ── Create / Update ──

class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = ""
    style: VideoStyle = VideoStyle.REALISTIC
    aspect_ratio: str = "9:16"
    genre: DramaGenre = DramaGenre.OTHER
    script_type: str = "dialogue"


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    style: Optional[VideoStyle] = None
    aspect_ratio: Optional[str] = None
    genre: Optional[DramaGenre] = None
    script_type: Optional[str] = None
    status: Optional[ProjectStep] = None


# ── Response ──

class ProjectList(BaseModel):
    id: int
    title: str
    description: Optional[str] = ""
    style: VideoStyle
    genre: DramaGenre
    status: ProjectStep
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectDetail(ProjectList):
    aspect_ratio: str = "9:16"
    script_type: str = "dialogue"

    model_config = {"from_attributes": True}
