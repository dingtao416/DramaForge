"""User media provider configuration API."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.ai_hub.media_adapters import MediaProviderSettings, get_media_adapter
from app.core.ai_config import normalize_optional_string
from app.core.config import settings
from app.core.security import CurrentUser, DbSession
from app.models.media_generation import (
    AIModelConfig,
    AIProviderConfig,
    MediaCapability,
    MediaGenerationJob,
    MediaJobStatus,
)
from app.services.media_generation_service import media_generation_service
from app.tasks.media_generation_tasks import enqueue_media_job


router = APIRouter(prefix="/user-ai", tags=["User AI Config"])

PROVIDER_TYPES = {
    "openai_compatible",
    "openai_native",
    "replicate",
    "fal",
    "fal_ai",
    "runway",
    "luma",
    "volcengine_ark",
    "volces",
    "dashscope",
    "google_vertex",
    "vertex",
}


class ProviderCreate(BaseModel):
    name: str = Field(..., max_length=100)
    provider_type: str = Field(..., max_length=50)
    auth_type: str = Field(default="bearer", max_length=50)
    base_url: str = Field(default="", max_length=500)
    api_key: str = Field(default="", max_length=1000)
    enabled: bool = True
    priority: int = 100
    headers_json: dict[str, str] = Field(default_factory=dict)
    config_json: dict[str, Any] = Field(default_factory=dict)


class ProviderUpdate(BaseModel):
    name: str | None = None
    provider_type: str | None = None
    auth_type: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    enabled: bool | None = None
    priority: int | None = None
    headers_json: dict[str, str] | None = None
    config_json: dict[str, Any] | None = None


class ModelCreate(BaseModel):
    capability: MediaCapability
    model_id: str = Field(..., max_length=200)
    display_name: str = Field(..., max_length=100)
    is_default: bool = False
    enabled: bool = True
    default_params_json: dict[str, Any] = Field(default_factory=dict)
    param_schema_json: dict[str, Any] = Field(default_factory=dict)
    capabilities_json: dict[str, Any] = Field(default_factory=dict)


class ModelUpdate(BaseModel):
    capability: MediaCapability | None = None
    model_id: str | None = None
    display_name: str | None = None
    is_default: bool | None = None
    enabled: bool | None = None
    default_params_json: dict[str, Any] | None = None
    param_schema_json: dict[str, Any] | None = None
    capabilities_json: dict[str, Any] | None = None


class ModelResponse(BaseModel):
    id: int
    provider_id: int
    capability: MediaCapability
    model_id: str
    display_name: str
    is_default: bool
    enabled: bool
    default_params_json: dict[str, Any]
    param_schema_json: dict[str, Any]
    capabilities_json: dict[str, Any]

    class Config:
        from_attributes = True


class ProviderResponse(BaseModel):
    id: int
    name: str
    provider_type: str
    auth_type: str
    base_url: str
    api_key_masked: str
    enabled: bool
    priority: int
    headers_json: dict[str, Any]
    config_json: dict[str, Any]
    models: list[ModelResponse]
    created_at: datetime | None = None


class ProviderTestResult(BaseModel):
    success: bool
    message: str
    models_found: int = 0


class JobCreate(BaseModel):
    capability: MediaCapability
    prompt: str
    model_id: str | None = None
    output_path: str | None = None
    request_json: dict[str, Any] = Field(default_factory=dict)


class JobResponse(BaseModel):
    id: int
    capability: MediaCapability
    provider_id: int | None
    model_id: str
    provider_job_id: str | None
    status: MediaJobStatus
    progress: int
    request_json: dict[str, Any]
    response_json: dict[str, Any]
    result_assets_json: list[Any]
    error: str | None
    created_at: datetime | None
    updated_at: datetime | None

    class Config:
        from_attributes = True


def _mask_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}****{key[-4:]}"


def _normalize_provider_type(provider_type: str) -> str:
    normalized = (provider_type or "").strip().lower()
    if normalized not in PROVIDER_TYPES:
        raise HTTPException(400, f"Unsupported provider_type: {provider_type}")
    return normalized


def _to_provider_response(provider: AIProviderConfig) -> ProviderResponse:
    return ProviderResponse(
        id=provider.id,
        name=provider.name,
        provider_type=provider.provider_type,
        auth_type=provider.auth_type,
        base_url=provider.base_url,
        api_key_masked=_mask_key(provider.api_key),
        enabled=provider.enabled,
        priority=provider.priority,
        headers_json=provider.headers_json or {},
        config_json=provider.config_json or {},
        models=[ModelResponse.model_validate(m) for m in provider.models],
        created_at=provider.created_at,
    )


async def _load_providers(db: DbSession, user_id: int) -> list[AIProviderConfig]:
    stmt = (
        select(AIProviderConfig)
        .where(AIProviderConfig.user_id == user_id)
        .options(selectinload(AIProviderConfig.models))
        .order_by(AIProviderConfig.priority.asc(), AIProviderConfig.id.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _get_provider(db: DbSession, provider_id: int, user_id: int) -> AIProviderConfig:
    stmt = (
        select(AIProviderConfig)
        .where(AIProviderConfig.id == provider_id, AIProviderConfig.user_id == user_id)
        .options(selectinload(AIProviderConfig.models))
    )
    result = await db.execute(stmt)
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(404, "Provider not found")
    return provider


async def _get_model(db: DbSession, model_id: int, user_id: int) -> AIModelConfig:
    stmt = (
        select(AIModelConfig)
        .join(AIProviderConfig)
        .where(AIModelConfig.id == model_id, AIProviderConfig.user_id == user_id)
    )
    result = await db.execute(stmt)
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(404, "Model not found")
    return model


@router.get("/providers", response_model=list[ProviderResponse])
async def list_providers(user: CurrentUser, db: DbSession):
    return [_to_provider_response(p) for p in await _load_providers(db, user.id)]


@router.post("/providers", response_model=ProviderResponse, status_code=201)
async def create_provider(data: ProviderCreate, user: CurrentUser, db: DbSession):
    provider = AIProviderConfig(
        user_id=user.id,
        name=normalize_optional_string(data.name) or data.name,
        provider_type=_normalize_provider_type(data.provider_type),
        auth_type=(data.auth_type or "bearer").strip().lower(),
        base_url=normalize_optional_string(data.base_url) or "",
        api_key=normalize_optional_string(data.api_key) or "",
        enabled=data.enabled,
        priority=data.priority,
        headers_json=data.headers_json,
        config_json=data.config_json,
    )
    db.add(provider)
    await db.flush()
    await db.refresh(provider, ["models"])
    return _to_provider_response(provider)


@router.put("/providers/{provider_id}", response_model=ProviderResponse)
async def update_provider(provider_id: int, data: ProviderUpdate, user: CurrentUser, db: DbSession):
    provider = await _get_provider(db, provider_id, user.id)
    update = data.model_dump(exclude_unset=True)
    if "provider_type" in update:
        update["provider_type"] = _normalize_provider_type(update["provider_type"])
    if "auth_type" in update and update["auth_type"]:
        update["auth_type"] = update["auth_type"].strip().lower()
    for key, value in update.items():
        if key in {"name", "base_url", "api_key"} and value is not None:
            value = normalize_optional_string(value) or ""
        setattr(provider, key, value)
    await db.flush()
    await db.refresh(provider, ["models"])
    return _to_provider_response(provider)


@router.delete("/providers/{provider_id}", status_code=204)
async def delete_provider(provider_id: int, user: CurrentUser, db: DbSession):
    provider = await _get_provider(db, provider_id, user.id)
    await db.delete(provider)
    await db.flush()


@router.post("/providers/{provider_id}/test", response_model=ProviderTestResult)
async def test_provider(provider_id: int, user: CurrentUser, db: DbSession):
    provider = await _get_provider(db, provider_id, user.id)
    try:
        adapter = get_media_adapter(
            MediaProviderSettings(
                provider_type=provider.provider_type,
                auth_type=provider.auth_type,
                base_url=provider.base_url,
                api_key=provider.api_key,
                headers=provider.headers_json or {},
                config=provider.config_json or {},
            )
        )
        result = await adapter.test_connection()
        return ProviderTestResult(
            success=bool(result.get("success")),
            message=str(result.get("message") or "Connection tested"),
            models_found=int(result.get("models_found") or 0),
        )
    except Exception as e:
        return ProviderTestResult(success=False, message=str(e)[:300])


@router.post("/providers/{provider_id}/discover")
async def discover_models(provider_id: int, user: CurrentUser, db: DbSession):
    provider = await _get_provider(db, provider_id, user.id)
    adapter = get_media_adapter(
        MediaProviderSettings(
            provider_type=provider.provider_type,
            auth_type=provider.auth_type,
            base_url=provider.base_url,
            api_key=provider.api_key,
            headers=provider.headers_json or {},
            config=provider.config_json or {},
        )
    )
    models = await adapter.list_models()
    return {"models": models, "count": len(models)}


@router.get("/providers/{provider_id}/models", response_model=list[ModelResponse])
async def list_models(provider_id: int, user: CurrentUser, db: DbSession):
    provider = await _get_provider(db, provider_id, user.id)
    return [ModelResponse.model_validate(m) for m in provider.models]


@router.post("/providers/{provider_id}/models", response_model=ModelResponse, status_code=201)
async def create_model(provider_id: int, data: ModelCreate, user: CurrentUser, db: DbSession):
    await _get_provider(db, provider_id, user.id)
    model = AIModelConfig(provider_id=provider_id, **data.model_dump())
    db.add(model)
    await db.flush()
    await db.refresh(model)
    if model.is_default:
        await _unset_other_defaults(db, model)
    return ModelResponse.model_validate(model)


@router.put("/models/{model_id}", response_model=ModelResponse)
async def update_model(model_id: int, data: ModelUpdate, user: CurrentUser, db: DbSession):
    model = await _get_model(db, model_id, user.id)
    for key, value in data.model_dump(exclude_unset=True).items():
        if key in {"model_id", "display_name"} and value is not None:
            value = normalize_optional_string(value) or ""
        setattr(model, key, value)
    await db.flush()
    if model.is_default:
        await _unset_other_defaults(db, model)
    await db.refresh(model)
    return ModelResponse.model_validate(model)


@router.delete("/models/{model_id}", status_code=204)
async def delete_model(model_id: int, user: CurrentUser, db: DbSession):
    model = await _get_model(db, model_id, user.id)
    await db.delete(model)
    await db.flush()


@router.put("/models/{model_id}/set-default", response_model=ModelResponse)
async def set_default_model(model_id: int, user: CurrentUser, db: DbSession):
    model = await _get_model(db, model_id, user.id)
    model.is_default = True
    await _unset_other_defaults(db, model)
    await db.flush()
    await db.refresh(model)
    return ModelResponse.model_validate(model)


async def _unset_other_defaults(db: DbSession, model: AIModelConfig) -> None:
    stmt = (
        select(AIModelConfig)
        .join(AIProviderConfig)
        .where(
            AIProviderConfig.user_id == (
                select(AIProviderConfig.user_id)
                .where(AIProviderConfig.id == model.provider_id)
                .scalar_subquery()
            ),
            AIModelConfig.capability == model.capability,
            AIModelConfig.id != model.id,
        )
    )
    result = await db.execute(stmt)
    for other in result.scalars().all():
        other.is_default = False


@router.get("/defaults")
async def get_defaults(user: CurrentUser, db: DbSession):
    defaults = {}
    providers = await _load_providers(db, user.id)
    for provider in providers:
        if not provider.enabled:
            continue
        for model in provider.models:
            if model.enabled and model.is_default and model.capability.value not in defaults:
                defaults[model.capability.value] = {
                    "model_id": model.model_id,
                    "display_name": model.display_name,
                    "provider_name": provider.name,
                    "provider_type": provider.provider_type,
                    "base_url": provider.base_url,
                }
    return defaults


@router.get("/jobs", response_model=list[JobResponse])
async def list_jobs(user: CurrentUser, db: DbSession, limit: int = Query(default=50, ge=1, le=200)):
    result = await db.execute(
        select(MediaGenerationJob)
        .where(MediaGenerationJob.user_id == user.id)
        .order_by(MediaGenerationJob.id.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, user: CurrentUser, db: DbSession):
    job = await db.get(MediaGenerationJob, job_id)
    if not job or job.user_id != user.id:
        raise HTTPException(404, "Job not found")
    return job


@router.post("/jobs", response_model=JobResponse, status_code=201)
async def create_job(data: JobCreate, user: CurrentUser, db: DbSession):
    if data.capability == MediaCapability.CHAT:
        raise HTTPException(400, "Text generation does not use media jobs")
    output_path = data.output_path
    if not output_path:
        ext = "png" if data.capability == MediaCapability.IMAGE else "mp4"
        output_path = str(Path(settings.storage_dir) / "media_jobs" / f"job_pending.{ext}")
    job = await media_generation_service.create_job(
        db=db,
        user_id=user.id,
        capability=data.capability.value,
        prompt=data.prompt,
        output_path=output_path,
        model_hint=data.model_id,
        request_json=data.request_json,
    )
    await db.commit()

    try:
        queue_job_id = await enqueue_media_job(job.id)
    except Exception as e:
        job.status = MediaJobStatus.FAILED
        job.error = f"Failed to enqueue media generation job: {e}"[:2000]
        job.progress = 100
        await db.commit()
        raise HTTPException(
            status_code=503,
            detail={"job_id": job.id, "message": job.error},
        ) from e

    request_json = dict(job.request_json or {})
    request_json["_queue_job_id"] = queue_job_id
    job.request_json = request_json
    await db.commit()
    await db.refresh(job)
    return job


@router.get("/catalog")
async def get_catalog():
    from app.data.model_catalog import BUILTIN_CATALOG

    return BUILTIN_CATALOG


@router.post("/catalog/import", response_model=ProviderResponse, status_code=201)
async def import_from_catalog(catalog_index: int, user: CurrentUser, db: DbSession):
    from app.data.model_catalog import BUILTIN_CATALOG

    if catalog_index < 0 or catalog_index >= len(BUILTIN_CATALOG):
        raise HTTPException(400, f"Invalid catalog index: {catalog_index}")
    template = BUILTIN_CATALOG[catalog_index]
    provider = AIProviderConfig(
        user_id=user.id,
        name=template["name"],
        provider_type=_normalize_provider_type(template["provider_type"]),
        auth_type=template.get("auth_type", "bearer"),
        base_url=template.get("base_url", ""),
        api_key="",
        enabled=True,
        priority=template.get("priority", 100),
        headers_json=template.get("headers_json", {}),
        config_json=template.get("config_json", {}),
    )
    db.add(provider)
    await db.flush()
    for item in template.get("models", []):
        db.add(
            AIModelConfig(
                provider_id=provider.id,
                capability=MediaCapability(item["capability"]),
                model_id=item["model_id"],
                display_name=item["display_name"],
                is_default=item.get("is_default", False),
                default_params_json=item.get("default_params_json", {}),
                param_schema_json=item.get("param_schema_json", {}),
                capabilities_json=item.get("capabilities_json", {}),
            )
        )
    await db.flush()
    await db.refresh(provider, ["models"])
    return _to_provider_response(provider)
