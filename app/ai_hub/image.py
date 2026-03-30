"""
DramaForge AI Hub - Image Service
Image generation via laozhang.ai OpenAI-compatible endpoint.

Supported models & pricing (per image):
    sora-image       $0.01   (best value, recommended for batch)
    flux-pro         $0.035  (flexible aspect ratio 3:7~7:3)
    flux-max         $0.07   (highest quality)
    nano-banana      $0.025  (base64 output)
    nano-banana-pro  $0.05   (4K HD)
    gpt-image-1      token   (OpenAI native)

Docs: https://docs.laozhang.ai/api-capabilities/image-generation-guide
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional

import httpx
from loguru import logger

from config import settings
from app.ai_hub._client import BaseClient
from app.ai_hub._models import ImageResponse


class ImageService:
    """Image generation service — produces storyboard visuals."""

    async def generate(
        self,
        prompt: str,
        output_path: str,
        *,
        model: str = None,
        size: str = None,
        **kwargs,
    ) -> ImageResponse:
        """
        Generate an image and save to disk.

        Args:
            prompt: Text description of the desired image.
            output_path: Where to save the PNG file.
            model: Image model (default from config).
            size: Image dimensions e.g. "1024x1792".

        Returns:
            ImageResponse with image_path, image_url, etc.
        """
        use_model = model or settings.image_model
        use_size = size or settings.image_size

        logger.info(
            f"image.generate | model={use_model} size={use_size} "
            f"prompt_len={len(prompt)}"
        )

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        # Try b64_json first (works for most models)
        try:
            return await self._generate_b64(prompt, out, use_model, use_size)
        except Exception as e:
            logger.warning(f"b64_json not supported, falling back to url: {e}")
            return await self._generate_url(prompt, out, use_model, use_size)

    async def generate_batch(
        self,
        prompts: list[str],
        output_dir: str,
        *,
        model: str = None,
        size: str = None,
        prefix: str = "img",
    ) -> list[ImageResponse | dict]:
        """
        Generate multiple images. Failures are logged but don't stop the batch.

        Returns:
            List of ImageResponse (or error dicts on failure).
        """
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        results = []
        total = len(prompts)
        for idx, prompt in enumerate(prompts, 1):
            path = str(out_dir / f"{prefix}_{idx:03d}.png")
            try:
                result = await self.generate(
                    prompt=prompt, output_path=path, model=model, size=size
                )
                results.append(result)
                logger.info(f"image batch [{idx}/{total}] ✓")
            except Exception as e:
                logger.error(f"image batch [{idx}/{total}] ✗ {e}")
                results.append({"error": str(e), "prompt": prompt[:80]})

        return results

    # ──────────── Internal ────────────

    async def _generate_b64(
        self, prompt: str, out: Path, model: str, size: str
    ) -> ImageResponse:
        """Generate with base64 response → decode & save."""
        client = BaseClient.openai()

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

        b64 = resp.data[0].b64_json
        image_bytes = base64.b64decode(b64)
        out.write_bytes(image_bytes)

        url = getattr(resp.data[0], "url", None)
        revised = getattr(resp.data[0], "revised_prompt", None)

        logger.info(f"image saved (b64) | path={out}")
        return ImageResponse(
            image_path=str(out), image_url=url, model=model, revised_prompt=revised
        )

    async def _generate_url(
        self, prompt: str, out: Path, model: str, size: str
    ) -> ImageResponse:
        """Generate with URL response → download & save."""
        client = BaseClient.openai()

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

        url = resp.data[0].url
        revised = getattr(resp.data[0], "revised_prompt", None)

        # Download
        async with httpx.AsyncClient(timeout=120) as dl:
            img_resp = await dl.get(url)
            img_resp.raise_for_status()
            out.write_bytes(img_resp.content)

        logger.info(f"image saved (url) | path={out}")
        return ImageResponse(
            image_path=str(out), image_url=url, model=model, revised_prompt=revised
        )
