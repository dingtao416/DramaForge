"""Resolve user media/chat model configuration."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.ai_config import (
    has_capability,
    normalize_api_base_url,
    normalize_optional_string,
)
from app.core.config import settings
from app.models.media_generation import AIModelConfig, AIProviderConfig, MediaCapability
from app.models.user_ai_config import UserAPIKey, UserModelConfig


@dataclass
class ResolvedModel:
    api_key: str | None
    base_url: str | None
    model_id: str
    provider_type: str | None = None
    auth_type: str | None = None
    headers: dict | None = None
    config: dict | None = None
    raw_params: dict | None = None
    provider_id: int | None = None


_SYSTEM_DEFAULTS = {
    "chat": settings.llm_model,
    "image": settings.image_model,
    "video": settings.video_model,
    "tts": settings.tts_model,
}


class UserModelResolver:
    """Resolve model/provider credentials for a capability."""

    async def resolve(
        self,
        db: AsyncSession,
        user_id: int,
        capability_type: str,
        model_hint: str | None = None,
    ) -> ResolvedModel:
        capability_type = (capability_type or "").strip().lower()
        model_hint = normalize_optional_string(model_hint)

        if capability_type in {"chat", "image", "video"}:
            resolved = await self._resolve_provider_model(db, user_id, capability_type, model_hint)
            if resolved:
                return resolved
            if capability_type != "chat":
                return self._fallback_media_model(capability_type)

        return await self._resolve_legacy_model(db, user_id, capability_type, model_hint)

    async def _resolve_provider_model(
        self,
        db: AsyncSession,
        user_id: int,
        capability_type: str,
        model_hint: str | None,
    ) -> ResolvedModel | None:
        capability = MediaCapability(capability_type)
        stmt = (
            select(AIModelConfig, AIProviderConfig)
            .join(AIProviderConfig, AIModelConfig.provider_id == AIProviderConfig.id)
            .where(
                AIProviderConfig.user_id == user_id,
                AIProviderConfig.enabled == True,
                AIModelConfig.enabled == True,
                AIModelConfig.capability == capability,
            )
            .order_by(
                AIModelConfig.is_default.desc(),
                AIProviderConfig.priority.asc(),
                AIModelConfig.id.asc(),
            )
        )
        if model_hint:
            hinted = await db.execute(stmt.where(AIModelConfig.model_id == model_hint))
            row = hinted.first()
            if row:
                model, provider = row
                return self._to_resolved_media(model, provider)

        result = await db.execute(stmt)
        row = result.first()
        if row:
            model, provider = row
            return self._to_resolved_media(model, provider)

        return None

    def _fallback_media_model(self, capability_type: str) -> ResolvedModel:
        fallback_model = settings.image_model if capability_type == "image" else settings.video_model
        return ResolvedModel(
            api_key=normalize_optional_string(settings.laozhang_api_key),
            base_url=normalize_api_base_url(settings.laozhang_base_url),
            model_id=normalize_optional_string(fallback_model) or fallback_model,
            provider_type="openai_compatible",
            auth_type="bearer",
            headers={},
            config={},
            raw_params={},
        )

    def _to_resolved_media(
        self,
        model: AIModelConfig,
        provider: AIProviderConfig,
    ) -> ResolvedModel:
        return ResolvedModel(
            api_key=normalize_optional_string(provider.api_key),
            base_url=normalize_optional_string(provider.base_url),
            model_id=normalize_optional_string(model.model_id) or model.model_id,
            provider_type=normalize_optional_string(provider.provider_type),
            auth_type=normalize_optional_string(provider.auth_type) or "bearer",
            headers=provider.headers_json or {},
            config=provider.config_json or {},
            raw_params=model.default_params_json or {},
            provider_id=provider.id,
        )

    async def _resolve_legacy_model(
        self,
        db: AsyncSession,
        user_id: int,
        capability_type: str,
        model_hint: str | None,
    ) -> ResolvedModel:
        stmt = (
            select(UserAPIKey)
            .where(UserAPIKey.user_id == user_id, UserAPIKey.enabled == True)
            .options(selectinload(UserAPIKey.models))
        )
        result = await db.execute(stmt)
        api_keys = result.scalars().all()

        default_model: UserModelConfig | None = None
        default_key: UserAPIKey | None = None
        for key in api_keys:
            if not has_capability(key.capabilities, capability_type):
                continue
            for model in key.models:
                if model.capability_type == capability_type and model.is_default and model.enabled:
                    default_model = model
                    default_key = key
                    break
            if default_model:
                break

        if model_hint:
            for key in api_keys:
                if not has_capability(key.capabilities, capability_type):
                    continue
                for model in key.models:
                    if (
                        normalize_optional_string(model.model_id) == model_hint
                        and model.capability_type == capability_type
                        and model.enabled
                    ):
                        return ResolvedModel(
                            api_key=normalize_optional_string(key.api_key),
                            base_url=normalize_api_base_url(key.base_url),
                            model_id=model_hint,
                        )
            if default_key:
                return ResolvedModel(
                    api_key=normalize_optional_string(default_key.api_key),
                    base_url=normalize_api_base_url(default_key.base_url),
                    model_id=model_hint,
                )
            return ResolvedModel(api_key=None, base_url=None, model_id=model_hint)

        if default_model and default_key:
            return ResolvedModel(
                api_key=normalize_optional_string(default_key.api_key),
                base_url=normalize_api_base_url(default_key.base_url),
                model_id=normalize_optional_string(default_model.model_id) or default_model.model_id,
            )

        return ResolvedModel(
            api_key=None,
            base_url=None,
            model_id=normalize_optional_string(_SYSTEM_DEFAULTS.get(capability_type, "gpt-4.1-mini"))
            or "gpt-4.1-mini",
        )

    async def resolve_all(self, db: AsyncSession, user_id: int) -> dict[str, ResolvedModel]:
        return {cap: await self.resolve(db, user_id, cap) for cap in ("chat", "image", "video", "tts")}


user_model_resolver = UserModelResolver()
