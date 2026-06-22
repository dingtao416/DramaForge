"""Provider adapters for image and video generation."""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
from loguru import logger

from app.core.ai_config import normalize_api_base_url, normalize_optional_string


class MediaAdapterError(RuntimeError):
    """Raised when a provider adapter cannot complete a request."""


@dataclass(slots=True)
class MediaProviderSettings:
    provider_type: str
    auth_type: str = "bearer"
    base_url: str = ""
    api_key: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class MediaRequest:
    prompt: str
    model_id: str
    size: str | None = None
    aspect_ratio: str | None = None
    resolution: str | None = None
    duration: int | float | str | None = None
    fps: int | None = None
    seed: int | None = None
    quality: str | None = None
    input_images: list[str] = field(default_factory=list)
    first_frame: str | None = None
    last_frame: str | None = None
    reference_images: list[str] = field(default_factory=list)
    mask: str | None = None
    raw_params: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class MediaResult:
    status: str
    provider_job_id: str | None = None
    assets: list[dict[str, Any]] = field(default_factory=list)
    progress: int = 0
    response: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    @property
    def completed(self) -> bool:
        return self.status == "succeeded"


def _join_url(base_url: str, path: str) -> str:
    base = (base_url or "").rstrip("/")
    suffix = path if path.startswith("/") else f"/{path}"
    return f"{base}{suffix}"


def _extract_urls(text: str, extensions: str = r"png|jpg|jpeg|webp|gif|mp4|mov|webm") -> list[str]:
    markdown = re.findall(r"!\[.*?\]\((https?://[^)]+)\)", text or "")
    bare = re.findall(rf"(https?://[^\s<>\"')]+\.(?:{extensions})(?:\?[^\s<>\"')]+)?)", text or "", re.I)
    return list(dict.fromkeys(markdown + bare))


class BaseMediaAdapter:
    """Base adapter with shared HTTP helpers and result downloading."""

    timeout = 600

    def __init__(self, settings: MediaProviderSettings):
        self.settings = settings

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", **(self.settings.headers or {})}
        api_key = normalize_optional_string(self.settings.api_key)
        if not api_key:
            logger.warning(
                f"Media adapter ({self.settings.provider_type}): no API key configured — "
                f"requests to {self.settings.base_url} will fail with 401"
            )
            return headers
        if self.settings.auth_type == "api-key":
            key_name = self.settings.config.get("api_key_header", "X-API-Key")
            auth_prefix = normalize_optional_string(self.settings.config.get("auth_prefix"))
            headers[key_name] = f"{auth_prefix} {api_key}" if auth_prefix else api_key
        elif self.settings.auth_type == "query":
            pass
        else:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    def _url(self, path: str) -> str:
        return _join_url(self.settings.base_url, path)

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(self._url(path), headers=self._headers(), json=payload)
            if resp.status_code >= 400:
                raise MediaAdapterError(f"HTTP {resp.status_code}: {resp.text[:500]}")
            return resp.json()

    async def _get(self, path_or_url: str) -> dict[str, Any]:
        url = path_or_url if path_or_url.startswith("http") else self._url(path_or_url)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, headers=self._headers())
            if resp.status_code >= 400:
                raise MediaAdapterError(f"HTTP {resp.status_code}: {resp.text[:500]}")
            return resp.json()

    async def submit_image(self, request: MediaRequest) -> MediaResult:
        raise MediaAdapterError(f"{self.settings.provider_type} does not support image generation")

    async def submit_video(self, request: MediaRequest) -> MediaResult:
        raise MediaAdapterError(f"{self.settings.provider_type} does not support video generation")

    async def get_status(self, provider_job_id: str) -> MediaResult:
        raise MediaAdapterError(f"{self.settings.provider_type} does not expose task status")

    async def test_connection(self) -> dict[str, Any]:
        return {"success": bool(self.settings.base_url), "message": "Adapter configured"}

    async def list_models(self) -> list[str]:
        return []

    async def download_result(self, result: MediaResult, output_path: str | Path) -> Path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        if not result.assets:
            raise MediaAdapterError("Provider result did not contain downloadable assets")
        asset = result.assets[0]
        if asset.get("b64"):
            out.write_bytes(base64.b64decode(asset["b64"]))
            return out
        url = asset.get("url")
        if not url:
            raise MediaAdapterError("Provider result asset has no url or base64 data")
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            out.write_bytes(resp.content)
        return out


class OpenAICompatibleAdapter(BaseMediaAdapter):
    """OpenAI-compatible media adapter for relays and aggregators.

    By default, normalizes base_url to include /v1 (OpenAI convention).
    Set config.skip_v1_normalization = true on the provider to disable this
    (e.g. for Azure AI Foundry which uses bare endpoints like /videos).
    """

    def _normalized_base_url(self) -> str:
        """Return the base URL, normalized for OpenAI convention unless opt-out."""
        if self.settings.config.get("skip_v1_normalization"):
            return (self.settings.base_url or "").rstrip("/")
        return normalize_api_base_url(self.settings.base_url) or ""

    def _url(self, path: str) -> str:
        return _join_url(self._normalized_base_url(), path)

    async def submit_image(self, request: MediaRequest) -> MediaResult:
        payload = {
            "model": request.model_id,
            "prompt": request.prompt,
            "n": request.raw_params.get("n", 1),
            **request.raw_params,
        }
        if request.size:
            payload["size"] = request.size
        payload.setdefault("response_format", "b64_json")
        try:
            logger.info(
                f"Image adapter → POST {self._url('/images/generations')} "
                f"model={request.model_id} size={request.size}"
            )
            data = await self._post("/images/generations", payload)
            return _image_result_from_openai_data(data)
        except MediaAdapterError as image_error:
            # Don't fallback to chat for auth errors — fail fast
            if "401" in str(image_error) or "403" in str(image_error):
                raise
            logger.warning(
                f"Image API failed ({image_error}), falling back to chat → "
                f"POST {self._url('/chat/completions')}"
            )
            try:
                data = await self._post(
                    "/chat/completions",
                    {
                        "model": request.model_id,
                        "messages": [{"role": "user", "content": request.prompt}],
                    },
                )
                content = (((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "")
                urls = _extract_urls(content, extensions=r"png|jpg|jpeg|webp|gif")
                if not urls:
                    raise MediaAdapterError(f"Image API failed and chat response had no image URL: {image_error}")
                return MediaResult(status="succeeded", assets=[{"type": "image", "url": urls[0]}], response=data)
            except Exception as chat_error:
                raise MediaAdapterError(
                    f"Image generation failed — "
                    f"Image API error: {image_error}. Chat fallback error: {chat_error}"
                ) from image_error

    async def submit_video(self, request: MediaRequest) -> MediaResult:
        payload = {"model": request.model_id, "prompt": request.prompt, **request.raw_params}
        if request.size or request.resolution:
            payload["size"] = request.size or request.resolution
        if request.duration is not None:
            payload["seconds"] = str(request.duration)
        if request.first_frame:
            payload["input_reference"] = {"image_url": request.first_frame}
        try:
            data = await self._post("/videos", payload)
            task_id = data.get("id") or data.get("task_id")
            status = _normalize_status(data.get("status"))
            if task_id and status != "succeeded":
                return MediaResult(status=status, provider_job_id=task_id, progress=int(data.get("progress") or 0), response=data)
            urls = _urls_from_any(data)
            if urls:
                return MediaResult(status="succeeded", assets=[{"type": "video", "url": urls[0]}], response=data)
        except MediaAdapterError as video_error:
            # Don't fallback to chat for auth errors
            if "401" in str(video_error) or "403" in str(video_error):
                raise
            logger.warning(
                f"Video API failed ({video_error}), falling back to chat → "
                f"POST {self._url('/chat/completions')}"
            )
        try:
            data = await self._post(
                "/chat/completions",
                {"model": request.model_id, "messages": [{"role": "user", "content": request.prompt}]},
            )
            content = (((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "")
            urls = _extract_urls(content, extensions=r"mp4|mov|webm")
            if not urls:
                raise MediaAdapterError("Video response did not contain a video URL")
            return MediaResult(status="succeeded", assets=[{"type": "video", "url": urls[0]}], response=data)
        except Exception as chat_error:
            raise MediaAdapterError(
                f"Video generation failed — "
                f"Video API error: {video_error if 'video_error' in dir() else 'unknown'}. "
                f"Chat fallback error: {chat_error}"
            )

    async def get_status(self, provider_job_id: str) -> MediaResult:
        data = await self._get(f"/videos/{provider_job_id}")
        status = _normalize_status(data.get("status"))
        urls = _urls_from_any(data)
        assets = [{"type": "video", "url": urls[0]}] if urls else []
        return MediaResult(
            status=status,
            provider_job_id=provider_job_id,
            progress=int(data.get("progress") or (100 if status == "succeeded" else 0)),
            assets=assets,
            response=data,
            error=_error_from_response(data),
        )

    @staticmethod
    def _extract_model_list(data: Any) -> list[dict[str, Any]]:
        """Normalize /models response: some providers return a plain list, others wrap in {"data": [...]}."""
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            items = data.get("data") or []
            return items if isinstance(items, list) else []
        return []

    async def test_connection(self) -> dict[str, Any]:
        data = await self._get("/models")
        models = self._extract_model_list(data)
        return {"success": True, "message": "Connection succeeded", "models_found": len(models)}

    async def list_models(self) -> list[str]:
        data = await self._get("/models")
        return [item.get("id") for item in self._extract_model_list(data) if item.get("id")]


class OpenAINativeAdapter(OpenAICompatibleAdapter):
    """OpenAI native adapter with Sora content download support."""

    async def download_result(self, result: MediaResult, output_path: str | Path) -> Path:
        if result.provider_job_id and not result.assets:
            out = Path(output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(self._url(f"/videos/{result.provider_job_id}/content"), headers=self._headers())
                resp.raise_for_status()
                out.write_bytes(resp.content)
            return out
        return await super().download_result(result, output_path)


class ReplicateAdapter(BaseMediaAdapter):
    async def submit_image(self, request: MediaRequest) -> MediaResult:
        return await self._submit_prediction(request, "image")

    async def submit_video(self, request: MediaRequest) -> MediaResult:
        return await self._submit_prediction(request, "video")

    async def _submit_prediction(self, request: MediaRequest, asset_type: str) -> MediaResult:
        input_payload = {"prompt": request.prompt, **request.raw_params}
        for key, value in {
            "image": request.first_frame or (request.input_images[0] if request.input_images else None),
            "duration": request.duration,
            "aspect_ratio": request.aspect_ratio,
            "seed": request.seed,
        }.items():
            if value is not None:
                input_payload[key] = value
        if "/" in request.model_id and ":" not in request.model_id:
            data = await self._post(f"/models/{request.model_id}/predictions", {"input": input_payload})
        else:
            data = await self._post("/predictions", {"version": request.model_id, "input": input_payload})
        return _task_or_asset_result(data, asset_type)

    async def get_status(self, provider_job_id: str) -> MediaResult:
        data = await self._get(f"/predictions/{provider_job_id}")
        return _task_or_asset_result(data, "asset", provider_job_id=provider_job_id)


class FalAdapter(BaseMediaAdapter):
    async def submit_image(self, request: MediaRequest) -> MediaResult:
        return await self._submit(request, "image")

    async def submit_video(self, request: MediaRequest) -> MediaResult:
        return await self._submit(request, "video")

    async def _submit(self, request: MediaRequest, asset_type: str) -> MediaResult:
        payload = {"prompt": request.prompt, **request.raw_params}
        if request.first_frame:
            payload["image_url"] = request.first_frame
        endpoint = self.settings.config.get("submit_path") or f"/{request.model_id}"
        data = await self._post(endpoint, payload)
        return _task_or_asset_result(data, asset_type)

    async def get_status(self, provider_job_id: str) -> MediaResult:
        status_path = self.settings.config.get("status_path", "/queue/requests/{id}/status").format(id=provider_job_id)
        data = await self._get(status_path)
        return _task_or_asset_result(data, "asset", provider_job_id=provider_job_id)


class TaskEndpointAdapter(BaseMediaAdapter):
    """Config-driven task adapter for Runway, Luma, Volcengine, DashScope, Vertex, etc."""

    async def submit_image(self, request: MediaRequest) -> MediaResult:
        return await self._submit(request, "image")

    async def submit_video(self, request: MediaRequest) -> MediaResult:
        return await self._submit(request, "video")

    async def _submit(self, request: MediaRequest, asset_type: str) -> MediaResult:
        payload = {
            "model": request.model_id,
            "prompt": request.prompt,
            **request.raw_params,
        }
        for key, value in {
            "size": request.size,
            "aspect_ratio": request.aspect_ratio,
            "resolution": request.resolution,
            "duration": request.duration,
            "fps": request.fps,
            "seed": request.seed,
            "quality": request.quality,
            "image_url": request.first_frame or (request.input_images[0] if request.input_images else None),
            "first_frame_url": request.first_frame,
            "last_frame_url": request.last_frame,
            "reference_image_urls": request.reference_images or None,
        }.items():
            if value not in (None, [], ""):
                payload[key] = value
        submit_path = self.settings.config.get("submit_path", "/generations")
        data = await self._post(submit_path, payload)
        return _task_or_asset_result(data, asset_type)

    async def get_status(self, provider_job_id: str) -> MediaResult:
        status_path = self.settings.config.get("status_path", "/generations/{id}").format(id=provider_job_id)
        data = await self._get(status_path)
        return _task_or_asset_result(data, "asset", provider_job_id=provider_job_id)


def get_media_adapter(settings: MediaProviderSettings) -> BaseMediaAdapter:
    provider_type = (settings.provider_type or "openai_compatible").lower()
    adapter_cls = {
        "openai_compatible": OpenAICompatibleAdapter,
        "openai_native": OpenAINativeAdapter,
        "replicate": ReplicateAdapter,
        "fal": FalAdapter,
        "fal_ai": FalAdapter,
        "runway": TaskEndpointAdapter,
        "luma": TaskEndpointAdapter,
        "volcengine_ark": TaskEndpointAdapter,
        "volces": TaskEndpointAdapter,
        "dashscope": TaskEndpointAdapter,
        "google_vertex": TaskEndpointAdapter,
        "vertex": TaskEndpointAdapter,
    }.get(provider_type)
    if not adapter_cls:
        raise MediaAdapterError(f"Unsupported provider_type: {provider_type}")
    return adapter_cls(settings)


def _normalize_status(status: Any) -> str:
    text = str(status or "").lower()
    if text in {"succeeded", "success", "completed", "complete", "done"}:
        return "succeeded"
    if text in {"failed", "failure", "error", "cancelled", "canceled"}:
        return "cancelled" if "cancel" in text else "failed"
    if text in {"queued", "pending", "starting", "submitted"}:
        return "queued"
    return "running"


def _image_result_from_openai_data(data: dict[str, Any]) -> MediaResult:
    items = data.get("data") or []
    if not items:
        raise MediaAdapterError("Image provider returned empty data")
    first = items[0]
    if first.get("b64_json"):
        return MediaResult(status="succeeded", assets=[{"type": "image", "b64": first["b64_json"]}], response=data)
    if first.get("url"):
        return MediaResult(status="succeeded", assets=[{"type": "image", "url": first["url"]}], response=data)
    raise MediaAdapterError("Image provider result had neither b64_json nor url")


def _task_or_asset_result(data: dict[str, Any], asset_type: str, provider_job_id: str | None = None) -> MediaResult:
    job_id = provider_job_id or data.get("id") or data.get("task_id") or data.get("request_id")
    status = _normalize_status(data.get("status") or data.get("state") or data.get("task_status"))
    urls = _urls_from_any(data)
    assets = [{"type": asset_type, "url": url} for url in urls]
    if assets and status not in {"failed", "cancelled"}:
        status = "succeeded"
    return MediaResult(
        status=status,
        provider_job_id=job_id,
        assets=assets,
        progress=int(data.get("progress") or data.get("percent") or (100 if status == "succeeded" else 0)),
        response=data,
        error=_error_from_response(data),
    )


def _urls_from_any(data: Any) -> list[str]:
    urls: list[str] = []
    if isinstance(data, str):
        return _extract_urls(data)
    if isinstance(data, list):
        for item in data:
            urls.extend(_urls_from_any(item))
    elif isinstance(data, dict):
        for key in ("url", "video_url", "image_url", "output_url", "file_url", "download_url"):
            value = data.get(key)
            if isinstance(value, str) and value.startswith("http"):
                urls.append(value)
        output = data.get("output")
        if isinstance(output, str) and output.startswith("http"):
            urls.append(output)
        else:
            urls.extend(_urls_from_any(output))
        for key in ("data", "result", "results", "assets", "images", "videos"):
            urls.extend(_urls_from_any(data.get(key)))
    return list(dict.fromkeys(urls))


def _error_from_response(data: dict[str, Any]) -> str | None:
    error = data.get("error") or data.get("message")
    if isinstance(error, dict):
        return str(error.get("message") or error)
    if error:
        return str(error)
    return None
