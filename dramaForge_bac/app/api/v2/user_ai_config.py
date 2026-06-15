"""
DramaForge v2.0 — User AI Configuration API
=============================================
Endpoints for managing user API keys and model preferences.
Supports both "relay" mode (one key for all) and "multi-key" mode.
"""

from __future__ import annotations

from datetime import datetime

import httpx
from fastapi import APIRouter, HTTPException, status
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.security import CurrentUser, DbSession
from app.models.user import User
from app.models.user_ai_config import UserAPIKey, UserModelConfig

router = APIRouter(prefix="/user-ai", tags=["User AI Config"])


# ═══════════════════════════════════════════════════════════════════
# Request / Response schemas
# ═══════════════════════════════════════════════════════════════════

class APIKeyCreate(BaseModel):
    name: str = Field(..., max_length=100, description="Display name")
    base_url: str = Field(..., max_length=500, description="API endpoint URL")
    api_key: str = Field(..., max_length=500, description="API key")
    capabilities: str = Field(default="chat,image,video,tts", max_length=200, description="Supported capabilities")
    is_default: bool = Field(default=False, description="Is default provider")


class APIKeyUpdate(BaseModel):
    name: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    capabilities: str | None = None
    is_default: bool | None = None
    enabled: bool | None = None


class ModelConfigCreate(BaseModel):
    capability_type: str = Field(..., description="chat / image / video / tts")
    model_id: str = Field(..., max_length=100, description="API model name")
    display_name: str = Field(..., max_length=100, description="Human-readable name")
    is_default: bool = Field(default=False, description="Is default for this capability type")


class ModelConfigUpdate(BaseModel):
    model_id: str | None = None
    display_name: str | None = None
    is_default: bool | None = None
    enabled: bool | None = None


class ModelConfigResponse(BaseModel):
    id: int
    api_key_id: int
    capability_type: str
    model_id: str
    display_name: str
    is_default: bool
    enabled: bool

    class Config:
        from_attributes = True


class APIKeyResponse(BaseModel):
    id: int
    name: str
    base_url: str
    api_key_masked: str
    capabilities: list[str]
    is_default: bool
    enabled: bool
    models: list[ModelConfigResponse]
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class TestResult(BaseModel):
    success: bool
    message: str
    models_found: int = 0


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════

def _mask_key(key: str) -> str:
    """Mask API key for display: sk-abc...xyz"""
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}****{key[-4:]}"


def _to_response(key: UserAPIKey) -> APIKeyResponse:
    return APIKeyResponse(
        id=key.id,
        name=key.name,
        base_url=key.base_url,
        api_key_masked=_mask_key(key.api_key),
        capabilities=(key.capabilities or "").split(","),
        is_default=key.is_default,
        enabled=key.enabled,
        models=[ModelConfigResponse.model_validate(m) for m in key.models],
        created_at=key.created_at,
    )


async def _load_user_keys(db: DbSession, user_id: int) -> list[UserAPIKey]:
    stmt = (
        select(UserAPIKey)
        .where(UserAPIKey.user_id == user_id)
        .options(selectinload(UserAPIKey.models))
        .order_by(UserAPIKey.is_default.desc(), UserAPIKey.id)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _get_key_or_404(db: DbSession, key_id: int, user_id: int) -> UserAPIKey:
    stmt = (
        select(UserAPIKey)
        .where(UserAPIKey.id == key_id, UserAPIKey.user_id == user_id)
        .options(selectinload(UserAPIKey.models))
    )
    result = await db.execute(stmt)
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    return key


# ═══════════════════════════════════════════════════════════════════
# API Key CRUD
# ═══════════════════════════════════════════════════════════════════

@router.get("/keys", response_model=list[APIKeyResponse])
async def list_keys(user: CurrentUser, db: DbSession):
    """Get all API keys for the current user."""
    keys = await _load_user_keys(db, user.id)
    return [_to_response(k) for k in keys]


@router.post("/keys", response_model=APIKeyResponse, status_code=201)
async def create_key(data: APIKeyCreate, user: CurrentUser, db: DbSession):
    """Create a new API key configuration."""
    key = UserAPIKey(
        user_id=user.id,
        name=data.name,
        base_url=data.base_url.rstrip("/"),
        api_key=data.api_key,
        capabilities=data.capabilities,
        is_default=data.is_default,
    )
    db.add(key)
    await db.flush()
    await db.refresh(key, ["models"])
    return _to_response(key)


@router.put("/keys/{key_id}", response_model=APIKeyResponse)
async def update_key(key_id: int, data: APIKeyUpdate, user: CurrentUser, db: DbSession):
    """Update an API key configuration."""
    key = await _get_key_or_404(db, key_id, user.id)

    if data.name is not None:
        key.name = data.name
    if data.base_url is not None:
        key.base_url = data.base_url.rstrip("/")
    if data.api_key is not None:
        key.api_key = data.api_key
    if data.capabilities is not None:
        key.capabilities = data.capabilities
    if data.is_default is not None:
        key.is_default = data.is_default
    if data.enabled is not None:
        key.enabled = data.enabled

    await db.flush()
    await db.refresh(key, ["models"])
    return _to_response(key)


@router.delete("/keys/{key_id}", status_code=204)
async def delete_key(key_id: int, user: CurrentUser, db: DbSession):
    """Delete an API key and all its model configs."""
    key = await _get_key_or_404(db, key_id, user.id)
    await db.delete(key)
    await db.flush()


# ═══════════════════════════════════════════════════════════════════
# Test Connection
# ═══════════════════════════════════════════════════════════════════

@router.post("/keys/{key_id}/test", response_model=TestResult)
async def test_connection(key_id: int, user: CurrentUser, db: DbSession):
    """Test if the API key and URL are valid by calling /v1/models."""
    key = await _get_key_or_404(db, key_id, user.id)

    # Ensure base_url ends with /v1
    base = key.base_url.rstrip("/")
    if not base.endswith("/v1"):
        base = base + "/v1"

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{base}/models",
                headers={"Authorization": f"Bearer {key.api_key}"},
            )
            if resp.status_code == 200:
                data = resp.json()
                count = len(data.get("data", []))
                return TestResult(success=True, message=f"连接成功，发现 {count} 个模型", models_found=count)
            else:
                return TestResult(success=False, message=f"HTTP {resp.status_code}: {resp.text[:200]}")
    except httpx.ConnectError:
        return TestResult(success=False, message="无法连接到服务器，请检查 URL")
    except Exception as e:
        return TestResult(success=False, message=f"连接失败: {str(e)[:200]}")


# ═══════════════════════════════════════════════════════════════════
# Model Config CRUD
# ═══════════════════════════════════════════════════════════════════

@router.get("/keys/{key_id}/models", response_model=list[ModelConfigResponse])
async def list_models(key_id: int, user: CurrentUser, db: DbSession):
    """Get all model configs under an API key."""
    key = await _get_key_or_404(db, key_id, user.id)
    return [ModelConfigResponse.model_validate(m) for m in key.models]


@router.post("/keys/{key_id}/models", response_model=ModelConfigResponse, status_code=201)
async def create_model(key_id: int, data: ModelConfigCreate, user: CurrentUser, db: DbSession):
    """Add a model config under an API key."""
    key = await _get_key_or_404(db, key_id, user.id)

    # Validate capability_type
    valid_types = {"chat", "image", "video", "tts"}
    if data.capability_type not in valid_types:
        raise HTTPException(400, f"Invalid capability_type: {data.capability_type}. Must be one of {valid_types}")

    model = UserModelConfig(
        api_key_id=key.id,
        capability_type=data.capability_type,
        model_id=data.model_id,
        display_name=data.display_name,
        is_default=data.is_default,
    )
    db.add(model)
    await db.flush()
    await db.refresh(model)
    return ModelConfigResponse.model_validate(model)


@router.put("/models/{model_id}", response_model=ModelConfigResponse)
async def update_model(model_id: int, data: ModelConfigUpdate, user: CurrentUser, db: DbSession):
    """Update a model config."""
    stmt = select(UserModelConfig).where(UserModelConfig.id == model_id)
    result = await db.execute(stmt)
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(404, "Model config not found")

    # Verify ownership
    key = await _get_key_or_404(db, model.api_key_id, user.id)

    if data.model_id is not None:
        model.model_id = data.model_id
    if data.display_name is not None:
        model.display_name = data.display_name
    if data.is_default is not None:
        model.is_default = data.is_default
    if data.enabled is not None:
        model.enabled = data.enabled

    await db.flush()
    await db.refresh(model)
    return ModelConfigResponse.model_validate(model)


@router.delete("/models/{model_id}", status_code=204)
async def delete_model(model_id: int, user: CurrentUser, db: DbSession):
    """Delete a model config."""
    stmt = select(UserModelConfig).where(UserModelConfig.id == model_id)
    result = await db.execute(stmt)
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(404, "Model config not found")

    # Verify ownership
    await _get_key_or_404(db, model.api_key_id, user.id)

    await db.delete(model)
    await db.flush()


@router.put("/models/{model_id}/set-default", response_model=ModelConfigResponse)
async def set_default_model(model_id: int, user: CurrentUser, db: DbSession):
    """Set a model as the default for its capability type."""
    stmt = select(UserModelConfig).where(UserModelConfig.id == model_id)
    result = await db.execute(stmt)
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(404, "Model config not found")

    key = await _get_key_or_404(db, model.api_key_id, user.id)

    # Unset other defaults for the same capability type under this user
    all_keys = await _load_user_keys(db, user.id)
    for k in all_keys:
        for m in k.models:
            if m.capability_type == model.capability_type and m.id != model.id:
                m.is_default = False

    model.is_default = True
    await db.flush()
    await db.refresh(model)
    return ModelConfigResponse.model_validate(model)


# ═══════════════════════════════════════════════════════════════════
# Defaults
# ═══════════════════════════════════════════════════════════════════

@router.get("/defaults")
async def get_defaults(user: CurrentUser, db: DbSession):
    """Get the default model for each capability type."""
    keys = await _load_user_keys(db, user.id)
    defaults = {}

    for key in keys:
        if not key.enabled:
            continue
        for model in key.models:
            if model.is_default and model.enabled and model.capability_type not in defaults:
                defaults[model.capability_type] = {
                    "model_id": model.model_id,
                    "display_name": model.display_name,
                    "provider_name": key.name,
                    "base_url": key.base_url,
                }

    return defaults


# ═══════════════════════════════════════════════════════════════════
# Auto-discover models from /v1/models
# ═══════════════════════════════════════════════════════════════════

@router.post("/keys/{key_id}/discover")
async def discover_models(key_id: int, user: CurrentUser, db: DbSession):
    """
    Auto-discover models from the provider's /v1/models endpoint.
    Automatically adds the first model of each capability type as the default.
    """
    key = await _get_key_or_404(db, key_id, user.id)

    # Ensure base_url ends with /v1 for OpenAI-compatible endpoints
    base = key.base_url.rstrip("/")
    if not base.endswith("/v1"):
        base = base + "/v1"

    # Fetch models from provider
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{base}/models",
                headers={"Authorization": f"Bearer {key.api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        raise HTTPException(400, f"Failed to fetch models: {str(e)[:200]}")

    raw_models = data.get("data", [])
    if not raw_models:
        return {"added": 0, "models": []}

    # Classify and pick first model per capability type
    by_type: dict[str, list[str]] = {}
    for item in raw_models:
        model_id = item.get("id", "")
        cap_type = _classify_model(model_id)
        if cap_type:
            by_type.setdefault(cap_type, []).append(model_id)

    # Check which types already have models configured
    existing_types = set()
    for m in key.models:
        if m.enabled:
            existing_types.add(m.capability_type)

    # Only add models for types that are NOT already configured
    added = []
    for cap_type, model_ids in by_type.items():
        if cap_type in existing_types:
            continue  # Already configured, skip
        first_model = model_ids[0]
        model = UserModelConfig(
            api_key_id=key.id,
            capability_type=cap_type,
            model_id=first_model,
            display_name=first_model,
            is_default=True,
        )
        db.add(model)
        added.append({
            "model_id": first_model,
            "capability_type": cap_type,
            "display_name": first_model,
            "is_default": True,
        })

    await db.flush()

    return {
        "added": len(added),
        "models": added,
        "available": {cap: ids for cap, ids in by_type.items()},
    }


# ═══════════════════════════════════════════════════════════════════
# Built-in Catalog
# ═══════════════════════════════════════════════════════════════════

@router.get("/catalog")
async def get_catalog():
    """Get built-in provider templates for quick setup."""
    from app.data.model_catalog import BUILTIN_CATALOG
    return BUILTIN_CATALOG


@router.post("/catalog/import", response_model=APIKeyResponse, status_code=201)
async def import_from_catalog(catalog_index: int, user: CurrentUser, db: DbSession):
    """Import a provider template from the built-in catalog."""
    from app.data.model_catalog import BUILTIN_CATALOG

    if catalog_index < 0 or catalog_index >= len(BUILTIN_CATALOG):
        raise HTTPException(400, f"Invalid catalog index: {catalog_index}")

    template = BUILTIN_CATALOG[catalog_index]

    # Create the API key
    key = UserAPIKey(
        user_id=user.id,
        name=template["name"],
        base_url=template["base_url"],
        api_key="",  # User must fill in
        capabilities=template["capabilities"],
        is_default=template.get("is_default", False),
    )
    db.add(key)
    await db.flush()

    # Create model configs
    for m in template.get("models", []):
        model = UserModelConfig(
            api_key_id=key.id,
            capability_type=m["capability_type"],
            model_id=m["model_id"],
            display_name=m["display_name"],
            is_default=m.get("is_default", False),
        )
        db.add(model)

    await db.flush()
    await db.refresh(key, ["models"])
    return _to_response(key)


def _classify_model(model_id: str) -> str | None:
    """Classify a model ID into a capability type based on naming patterns."""
    mid = model_id.lower()

    # Video models
    video_keywords = ["video", "sora", "veo", "kling", "seedance", "runway", "pika", "vidu", "hailuo", "wan"]
    if any(kw in mid for kw in video_keywords):
        return "video"

    # Image models
    image_keywords = ["image", "dall-e", "dalle", "midjourney", "stable-diffusion", "flux", "ideogram", "sora-image"]
    if any(kw in mid for kw in image_keywords):
        return "image"

    # TTS models
    tts_keywords = ["tts", "speech", "audio"]
    if any(kw in mid for kw in tts_keywords):
        return "tts"

    # Chat/LLM models (default for known LLM prefixes)
    chat_keywords = ["gpt", "claude", "gemini", "qwen", "deepseek", "glm", "kimi", "llama", "mistral", "mixtral"]
    if any(kw in mid for kw in chat_keywords):
        return "chat"

    # Unknown → default to chat
    return "chat"
