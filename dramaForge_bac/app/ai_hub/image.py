"""Image generation service with adapter-backed provider support."""

from __future__ import annotations

import base64
import re
from pathlib import Path

import httpx
from loguru import logger

from app.ai_hub._client import BaseClient, HubClientError
from app.ai_hub._models import ImageResponse
from app.ai_hub.media_adapters import (
    MediaProviderSettings,
    MediaRequest,
    get_media_adapter,
)
from app.core.ai_config import normalize_optional_string
from app.core.config import settings


CHAT_COMPLETIONS_IMAGE_MODELS = {
    "sora_image",
    "sora-image",
    "gpt-4o-image",
}
RATIO_MARKER_RE = re.compile(r"(?:【|\[)(?:2:3|3:2|1:1)(?:】|\])")
SIZE_RE = re.compile(r"^\s*(\d+)\s*x\s*(\d+)\s*$", re.IGNORECASE)


def _is_chat_completions_image_model(model: str) -> bool:
    return (model or "").strip().lower() in CHAT_COMPLETIONS_IMAGE_MODELS


def _ratio_for_size(size: str | None) -> str:
    match = SIZE_RE.match(size or "")
    if not match:
        return "2:3"
    width = int(match.group(1))
    height = int(match.group(2))
    if width == height:
        return "1:1"
    if width > height:
        return "3:2"
    return "2:3"


def _prompt_with_ratio_marker(prompt: str, size: str | None) -> str:
    if RATIO_MARKER_RE.search(prompt):
        return prompt
    return f"{prompt}【{_ratio_for_size(size)}】"


async def _download_image_url(url: str, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        out.write_bytes(resp.content)


class ImageService:
    """Image generation service for storyboard and asset visuals."""

    async def generate(
        self,
        prompt: str,
        output_path: str,
        *,
        model: str = None,
        size: str = None,
        api_key: str = None,
        base_url: str = None,
        provider_type: str = None,
        auth_type: str = "bearer",
        headers: dict | None = None,
        config: dict | None = None,
        raw_params: dict | None = None,
        **kwargs,
    ) -> ImageResponse:
        use_model = normalize_optional_string(model) or settings.image_model
        use_size = normalize_optional_string(size) or settings.image_size
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"image.generate | provider={provider_type or 'openai_compatible'} "
            f"model={use_model} size={use_size} prompt_len={len(prompt)}"
        )

        if provider_type:
            return await self._generate_with_adapter(
                prompt=prompt,
                out=out,
                model=use_model,
                size=use_size,
                api_key=api_key,
                base_url=base_url,
                provider_type=provider_type,
                auth_type=auth_type,
                headers=headers or {},
                config=config or {},
                raw_params={**(raw_params or {}), **kwargs},
            )

        if _is_chat_completions_image_model(use_model):
            return await self._generate_chat(prompt, out, use_model, use_size, api_key, base_url)

        try:
            return await self._generate_b64(prompt, out, use_model, use_size, api_key, base_url)
        except Exception as e:
            logger.warning(f"b64_json not supported, trying url: {e}")
        try:
            return await self._generate_url(prompt, out, use_model, use_size, api_key, base_url)
        except Exception as e:
            logger.warning(f"url not supported, trying chat endpoint: {e}")
        return await self._generate_chat(prompt, out, use_model, use_size, api_key, base_url)

    async def generate_batch(
        self,
        prompts: list[str],
        output_dir: str,
        *,
        model: str = None,
        size: str = None,
        prefix: str = "img",
        api_key: str = None,
        base_url: str = None,
        provider_type: str = None,
        auth_type: str = "bearer",
        headers: dict | None = None,
        config: dict | None = None,
        raw_params: dict | None = None,
    ) -> list[ImageResponse | dict]:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        results = []
        for idx, prompt in enumerate(prompts, 1):
            path = str(out_dir / f"{prefix}_{idx:03d}.png")
            try:
                results.append(
                    await self.generate(
                        prompt=prompt,
                        output_path=path,
                        model=model,
                        size=size,
                        api_key=api_key,
                        base_url=base_url,
                        provider_type=provider_type,
                        auth_type=auth_type,
                        headers=headers,
                        config=config,
                        raw_params=raw_params,
                    )
                )
            except Exception as e:
                logger.error(f"image batch [{idx}/{len(prompts)}] FAIL: {e}")
                results.append({"error": str(e), "prompt": prompt[:80]})
        return results

    async def _generate_with_adapter(
        self,
        *,
        prompt: str,
        out: Path,
        model: str,
        size: str,
        api_key: str | None,
        base_url: str | None,
        provider_type: str,
        auth_type: str,
        headers: dict,
        config: dict,
        raw_params: dict,
    ) -> ImageResponse:
        adapter = get_media_adapter(
            MediaProviderSettings(
                provider_type=provider_type,
                auth_type=auth_type,
                base_url=base_url or "",
                api_key=api_key or "",
                headers=headers,
                config=config,
            )
        )
        result = await adapter.submit_image(
            MediaRequest(prompt=prompt, model_id=model, size=size, raw_params=raw_params)
        )
        if result.status != "succeeded":
            if not result.provider_job_id:
                raise HubClientError(
                    result.error or f"Image generation did not complete: {result.status}",
                    status_code=0,
                )
            import asyncio

            for _ in range(60):
                await asyncio.sleep(2)
                result = await adapter.get_status(result.provider_job_id)
                if result.status in {"succeeded", "failed", "cancelled"}:
                    break
        if result.status != "succeeded":
            raise HubClientError(result.error or f"Image generation failed: {result.status}", status_code=0)
        await adapter.download_result(result, out)
        asset = result.assets[0] if result.assets else {}
        return ImageResponse(image_path=str(out), image_url=asset.get("url"), model=model)

    async def _generate_chat(
        self,
        prompt: str,
        out: Path,
        model: str,
        size: str,
        api_key: str = None,
        base_url: str = None,
    ) -> ImageResponse:
        client = BaseClient.openai(api_key, base_url)
        chat_prompt = _prompt_with_ratio_marker(prompt, size)
        resp = await BaseClient.with_retry(
            lambda: client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": chat_prompt}],
            ),
            label=f"image-chat:{model}",
        )
        if not resp.choices:
            raise HubClientError(f"Chat image API returned empty choices for model '{model}'.", status_code=0)
        content = resp.choices[0].message.content or ""
        urls = re.findall(r"!\[.*?\]\((https?://[^)]+)\)", content)
        if not urls:
            urls = re.findall(r"(https?://[^\s<>\"]+\.(?:png|jpg|jpeg|webp|gif))", content, re.I)
        if not urls:
            raise HubClientError(f"No image URL found in chat response. Content preview: {content[:200]}", status_code=0)
        await _download_image_url(urls[0], out)
        return ImageResponse(image_path=str(out), image_url=urls[0], model=model)

    async def _generate_b64(
        self,
        prompt: str,
        out: Path,
        model: str,
        size: str,
        api_key: str = None,
        base_url: str = None,
    ) -> ImageResponse:
        client = BaseClient.openai(api_key, base_url)
        resp = await BaseClient.with_retry(
            lambda: client.images.generate(
                model=model,
                prompt=prompt,
                n=1,
                size=size,
                response_format="b64_json",
            ),
            label=f"image:{model}",
        )
        if not resp.data:
            raise HubClientError(f"API returned empty data for image model '{model}'.", status_code=0)
        out.write_bytes(base64.b64decode(resp.data[0].b64_json))
        return ImageResponse(
            image_path=str(out),
            image_url=getattr(resp.data[0], "url", None),
            model=model,
            revised_prompt=getattr(resp.data[0], "revised_prompt", None),
        )

    async def _generate_url(
        self,
        prompt: str,
        out: Path,
        model: str,
        size: str,
        api_key: str = None,
        base_url: str = None,
    ) -> ImageResponse:
        client = BaseClient.openai(api_key, base_url)
        resp = await BaseClient.with_retry(
            lambda: client.images.generate(
                model=model,
                prompt=prompt,
                n=1,
                size=size,
                response_format="url",
            ),
            label=f"image:{model}",
        )
        if not resp.data:
            raise HubClientError(f"API returned empty data for image model '{model}'.", status_code=0)
        url = resp.data[0].url
        await _download_image_url(url, out)
        return ImageResponse(
            image_path=str(out),
            image_url=url,
            model=model,
            revised_prompt=getattr(resp.data[0], "revised_prompt", None),
        )
