"""
DramaForge v2.0 — User AI Configuration ORM Models
====================================================
User-configured API keys and model preferences.
Supports both "relay" mode (one key for all) and "multi-key" mode.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class UserAPIKey(Base):
    """User's API key configuration — one row per key/provider."""
    __tablename__ = "user_api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)          # Display name
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)      # API endpoint
    api_key: Mapped[str] = mapped_column(String(500), nullable=False)       # API key
    capabilities: Mapped[str] = mapped_column(String(200), nullable=False, default="chat,image,video,tts")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationship
    models: Mapped[list["UserModelConfig"]] = relationship(
        back_populates="api_key_ref", cascade="all, delete-orphan"
    )


class UserModelConfig(Base):
    """User's model preference under a specific API key — one row per capability type."""
    __tablename__ = "user_model_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    api_key_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_api_keys.id"), nullable=False, index=True)
    capability_type: Mapped[str] = mapped_column(String(20), nullable=False)   # chat / image / video / tts
    model_id: Mapped[str] = mapped_column(String(100), nullable=False)         # API model name
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)     # Human-readable name
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationship
    api_key_ref: Mapped["UserAPIKey"] = relationship(back_populates="models")
