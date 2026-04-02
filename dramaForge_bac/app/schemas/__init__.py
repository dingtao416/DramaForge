"""
DramaForge v2.0 — Schemas Package
===================================
Unified export: ``from app.schemas import ProjectCreate, ScriptDetail, ...``
"""

from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectList,
    ProjectDetail,
)
from app.schemas.script import (
    ScriptGenerateRequest,
    ScriptUploadRequest,
    ScriptUpdate,
    ScriptDetail,
    EpisodeBrief,
    EpisodeUpdate,
)
from app.schemas.assets import (
    CharacterDetail,
    CharacterUpdate,
    CharacterRegenerateRequest,
    SceneDetail,
    SceneUpdate,
    SceneRegenerateRequest,
    AssetsGenerateRequest,
)
from app.schemas.episode import (
    EpisodeOverview,
    EpisodeDetail,
)
from app.schemas.storyboard import (
    ShotCharacterRef,
    ShotDetail,
    ShotUpdate,
    SegmentDetail,
    StoryboardDetail,
    StoryboardGenerateRequest,
)

__all__ = [
    # Project
    "ProjectCreate", "ProjectUpdate", "ProjectList", "ProjectDetail",
    # Script
    "ScriptGenerateRequest", "ScriptUploadRequest", "ScriptUpdate",
    "ScriptDetail", "EpisodeBrief", "EpisodeUpdate",
    # Assets
    "CharacterDetail", "CharacterUpdate", "CharacterRegenerateRequest",
    "SceneDetail", "SceneUpdate", "SceneRegenerateRequest",
    "AssetsGenerateRequest",
    # Episode
    "EpisodeOverview", "EpisodeDetail",
    # Storyboard
    "ShotCharacterRef", "ShotDetail", "ShotUpdate",
    "SegmentDetail", "StoryboardDetail", "StoryboardGenerateRequest",
]