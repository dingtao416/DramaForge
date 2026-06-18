"""Media provider, model, and generation job models."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class MediaCapability(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"


class MediaJobStatus(str, enum.Enum):
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AIProviderConfig(Base):
    """User-owned media provider connection settings."""

    __tablename__ = "ai_provider_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    auth_type: Mapped[str] = mapped_column(String(50), nullable=False, default="bearer")
    base_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    api_key: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    headers_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    config_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    models: Mapped[list["AIModelConfig"]] = relationship(
        back_populates="provider", cascade="all, delete-orphan"
    )


class AIModelConfig(Base):
    """Media model metadata and default parameter schema."""

    __tablename__ = "ai_model_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ai_provider_configs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    capability: Mapped[MediaCapability] = mapped_column(Enum(MediaCapability), nullable=False, index=True)
    model_id: Mapped[str] = mapped_column(String(200), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    default_params_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    param_schema_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    capabilities_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    provider: Mapped[AIProviderConfig] = relationship(back_populates="models")


class MediaGenerationJob(Base):
    """Persistent image/video generation job state."""

    __tablename__ = "media_generation_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    capability: Mapped[MediaCapability] = mapped_column(Enum(MediaCapability), nullable=False, index=True)
    provider_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("ai_provider_configs.id"), nullable=True)
    model_id: Mapped[str] = mapped_column(String(200), nullable=False)
    provider_job_id: Mapped[str | None] = mapped_column(String(300), nullable=True, index=True)
    status: Mapped[MediaJobStatus] = mapped_column(
        Enum(MediaJobStatus), nullable=False, default=MediaJobStatus.CREATED, index=True
    )
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    request_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    response_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    result_assets_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
