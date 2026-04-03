"""
DramaForge v2.0 — Models Package
==================================
Unified export: ``from app.models import Project, Character, ...``

All enums and ORM models are re-exported here so that:
1. Other modules have a single import point.
2. ``Base.metadata`` sees every table when ``init_db()`` is called.
"""

# ── ORM Models ──
from app.models.project import Project
from app.models.script import Script
from app.models.episode import Episode
from app.models.character import Character
from app.models.scene import SceneLocation
from app.models.segment import Segment
from app.models.shot import Shot
from app.models.user import User, Conversation, Message

# ── Enums (re-export from their home modules) ──
from app.models.project import ProjectStep, VideoStyle, DramaGenre
from app.models.character import CharacterRole
from app.models.segment import SegmentStatus
from app.models.shot import CameraType, CameraMovement
from app.models.user import UserStatus, MessageRole

__all__ = [
    # Models
    "Project",
    "Script",
    "Episode",
    "Character",
    "SceneLocation",
    "Segment",
    "Shot",
    "User",
    "Conversation",
    "Message",
    # Enums
    "ProjectStep",
    "VideoStyle",
    "DramaGenre",
    "CharacterRole",
    "SegmentStatus",
    "CameraType",
    "CameraMovement",
    "UserStatus",
    "MessageRole",
]