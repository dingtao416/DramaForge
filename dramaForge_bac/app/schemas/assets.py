"""
DramaForge v2.0 — Assets Schemas (Character + SceneLocation)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

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
    reference_images: list[Any] = []  # [{url, name, is_primary}]
    created_at: datetime

    model_config = {"from_attributes": True}


class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[CharacterRole] = None
    description: Optional[str] = None
    voice_desc: Optional[str] = None
    reference_images: Optional[list[Any]] = None  # [{url, name, is_primary}]


class CharacterCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    role: CharacterRole = CharacterRole.SUPPORTING
    description: Optional[str] = ""
    voice_desc: Optional[str] = ""


class CharacterRegenerateRequest(BaseModel):
    prompt: Optional[str] = None
    variant_count: int = Field(default=1, ge=1, le=4, description="生成变体数量，>1 时生成多张图供选择")
    appearance_type: str = Field(default="standard", description="形象类型，如 standard/turnaround_front/stage_early")
    image_name: Optional[str] = Field(default=None, description="生成后写入 reference_images 的显示名称")
    # ── Enhanced context ──
    visual_description: Optional[str] = Field(default="", description="当前形象的描述，用于AI生成prompt")
    optimize_prompt: bool = Field(default=False, description="是否使用文本LLM优化图像生成提示词")


# ── SceneLocation ──

class SceneDetail(BaseModel):
    id: int
    project_id: int
    name: str
    description: Optional[str] = ""
    time_of_day: Optional[str] = "day"
    interior: bool = True
    reference_images: list[Any] = []  # [{url, name, is_primary}]
    created_at: datetime

    model_config = {"from_attributes": True}


class AssetLibraryItem(BaseModel):
    id: int
    uid: str
    type: Literal["character", "scene"]
    project_id: int
    name: str
    role: Optional[CharacterRole] = None
    description: Optional[str] = ""
    voice_desc: Optional[str] = ""
    time_of_day: Optional[str] = None
    interior: Optional[bool] = None
    reference_images: list[Any] = []
    created_at: datetime


class SceneUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    time_of_day: Optional[str] = None
    interior: Optional[bool] = None
    reference_images: Optional[list[Any]] = None  # [{url, name, is_primary}]


class SceneCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = ""
    time_of_day: str = "day"
    interior: bool = True


class SceneRegenerateRequest(BaseModel):
    prompt: Optional[str] = None
    variant_count: int = Field(default=1, ge=1, le=4, description="生成变体数量，>1 时生成多张图供选择")
    state_type: str = Field(default="default", description="场景状态类型，如 default/day/night/damaged")
    image_name: Optional[str] = Field(default=None, description="生成后写入 reference_images 的显示名称")


# ── Asset generation ──

class AssetsGenerateRequest(BaseModel):
    """Trigger generation of all characters + scenes from approved script."""
    force: bool = Field(default=False, description="Force re-generation even if assets exist")
