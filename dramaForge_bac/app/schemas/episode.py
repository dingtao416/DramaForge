"""
DramaForge v2.0 — Episode Schemas
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EpisodeOverview(BaseModel):
    """Summary view of an episode for list display."""
    id: int
    number: int
    title: Optional[str] = ""
    is_approved: bool = False
    character_count: int = 0
    scene_count: int = 0
    segment_count: int = 0
    total_duration: float = 0.0
    created_at: datetime

    model_config = {"from_attributes": True}


class EpisodeDetail(BaseModel):
    """Full episode detail with content."""
    id: int
    script_id: int
    number: int
    title: Optional[str] = ""
    content: Optional[str] = ""
    is_approved: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}
