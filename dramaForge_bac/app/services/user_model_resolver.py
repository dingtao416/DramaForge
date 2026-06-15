"""
DramaForge v2.0 — User Model Resolver
=======================================
Resolves which API key + model to use for a given capability type.
Priority: user config → system default (config.py).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.user_ai_config import UserAPIKey, UserModelConfig


@dataclass
class ResolvedModel:
    """Resolved provider + model for a capability type."""
    api_key: str | None      # None → use system default
    base_url: str | None     # None → use system default
    model_id: str            # Actual model name for API call


# System defaults from config.py
_SYSTEM_DEFAULTS = {
    "chat": settings.llm_model,
    "image": settings.image_model,
    "video": settings.video_model,
    "tts": settings.tts_model,
}


def _normalize_url(url: str | None) -> str | None:
    """Ensure URL ends with /v1 for OpenAI-compatible endpoints."""
    if not url:
        return url
    url = url.rstrip("/")
    if not url.endswith("/v1"):
        url = url + "/v1"
    return url


class UserModelResolver:
    """Resolves user-configured models with fallback to system defaults."""

    async def resolve(
        self,
        db: AsyncSession,
        user_id: int,
        capability_type: str,
        model_hint: str | None = None,
    ) -> ResolvedModel:
        """
        Resolve the provider + model for a capability type.

        Priority:
        1. model_hint (explicitly specified by caller)
        2. User's default model for this capability type
        3. System default (config.py)
        """
        # Load user's API keys with models eagerly
        stmt = (
            select(UserAPIKey)
            .where(UserAPIKey.user_id == user_id, UserAPIKey.enabled == True)
            .options(selectinload(UserAPIKey.models))
        )
        result = await db.execute(stmt)
        api_keys = result.scalars().all()

        # Find the default model config for this capability type
        default_model: UserModelConfig | None = None
        default_key: UserAPIKey | None = None

        for key in api_keys:
            if capability_type not in (key.capabilities or "").split(","):
                continue
            for model in key.models:
                if model.capability_type == capability_type and model.is_default and model.enabled:
                    default_model = model
                    default_key = key
                    break
            if default_model:
                break

        # If model_hint is specified, try to find it in user's configs
        if model_hint:
            for key in api_keys:
                if capability_type not in (key.capabilities or "").split(","):
                    continue
                for model in key.models:
                    if model.model_id == model_hint and model.capability_type == capability_type and model.enabled:
                        return ResolvedModel(
                            api_key=key.api_key,
                            base_url=_normalize_url(key.base_url),
                            model_id=model_hint,
                        )
            # model_hint not found in user configs → use it with user's default key
            if default_key:
                return ResolvedModel(
                    api_key=default_key.api_key,
                    base_url=_normalize_url(default_key.base_url),
                    model_id=model_hint,
                )
            # No user config at all → use model_hint with system defaults
            return ResolvedModel(api_key=None, base_url=None, model_id=model_hint)

        # No hint → use user's default
        if default_model and default_key:
            return ResolvedModel(
                api_key=default_key.api_key,
                base_url=default_key.base_url,
                model_id=default_model.model_id,
            )

        # No user config → system default
        return ResolvedModel(
            api_key=None,
            base_url=None,
            model_id=_SYSTEM_DEFAULTS.get(capability_type, "gpt-4.1-mini"),
        )

    async def resolve_all(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> dict[str, ResolvedModel]:
        """Resolve all 4 capability types at once."""
        result = {}
        for cap in ("chat", "image", "video", "tts"):
            result[cap] = await self.resolve(db, user_id, cap)
        return result


# Module-level singleton
user_model_resolver = UserModelResolver()
