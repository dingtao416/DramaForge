"""
DramaForge v2.0 — Assets Schemas (Character + SceneLocation)
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.character import CharacterRole


# ── Character ──

class CharacterDetail(BaseModel):
    id: int
    project_id: int
    name: str
    role: CharacterRole = CharacterRole.SUPPORTING
    description: Optional[str] = ""
    voice_desc: Optional[str] = ""
    reference_images: list[str] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[CharacterRole] = None
    description: Optional[str] = None
    voice_desc: Optional[str] = None
    reference_images: Optional[list[str]] = None


class CharacterRegenerateRequest(BaseModel):
    prompt: Optional[str] = None


# ── SceneLocation ──

class SceneDetail(BaseModel):
    id: int
    project_id: int
    name: str
    description: Optional[str] = ""
    time_of_day: Optional[str] = "day"
    interior: bool = True
    reference_images: list[str] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class SceneUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    time_of_day: Optional[str] = None
    interior: Optional[bool] = None
    reference_images: Optional[list[str]] = None


class SceneRegenerateRequest(BaseModel):
    prompt: Optional[str] = None


# ── Asset generation ──

class AssetsGenerateRequest(BaseModel):
    """Trigger generation of all characters + scenes from approved script."""
    force: bool = Field(default=False, description="Force re-generation even if assets exist")
