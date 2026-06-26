"""
DramaForge v2.0 — Script Schemas
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Request ──

class ScriptGenerateRequest(BaseModel):
    """User input for AI script generation."""
    user_input: str = Field(..., min_length=1, description="故事构想 / 主题描述")
    genre: Optional[str] = None
    total_episodes: int = Field(default=1, ge=1, le=50)
    duration_per_episode: int = Field(default=60, ge=10, le=600)
    preserve_episodes: bool = Field(
        default=False,
        description="保留已有剧集及其下游分镜数据；为 True 时仅更新剧本元数据与剧集内容，不删除已有剧集",
    )


class ScriptUploadRequest(BaseModel):
    """Metadata for uploaded .docx script."""
    total_episodes: int = Field(default=1, ge=1, le=50)


class ScriptUpdate(BaseModel):
    protagonist: Optional[str] = None
    genre: Optional[str] = None
    synopsis: Optional[str] = None
    background: Optional[str] = None
    setting: Optional[str] = None
    one_liner: Optional[str] = None
    raw_content: Optional[str] = None


class EpisodeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


# ── Response ──

class EpisodeBrief(BaseModel):
    id: int
    number: int
    title: Optional[str] = ""
    content: Optional[str] = ""
    is_approved: bool = False

    model_config = {"from_attributes": True}


class ScriptDetail(BaseModel):
    id: int
    project_id: int
    protagonist: Optional[str] = ""
    genre: Optional[str] = ""
    synopsis: Optional[str] = ""
    background: Optional[str] = ""
    setting: Optional[str] = ""
    one_liner: Optional[str] = ""
    raw_content: Optional[str] = ""
    is_approved: bool = False
    created_at: datetime
    episodes: list[EpisodeBrief] = []
    warnings: list[str] = []

    model_config = {"from_attributes": True}
