"""
DramaForge - Image Agent
Agent for generating images — delegates to AI Hub image service.
"""

from typing import Any

from loguru import logger

from app.ai_hub import ai_hub


class ImageAgent:
    """Agent responsible for generating images from text prompts."""

    def __init__(self):
        self.name = "ImageAgent"
        logger.info(f"Agent [{self.name}] initialized")

    async def execute(self, **kwargs) -> Any:
        """Generate an image."""
        return await self.generate_image(**kwargs)

    async def generate_image(
        self,
        prompt: str,
        output_path: str,
        size: str = None,
        model: str = None,
        **kwargs,
    ) -> dict:
        """
        Generate an image from a text prompt.

        Returns:
            Dict with image_path (and optionally image_url, model).
        """
        result = await ai_hub.image.generate(
            prompt=prompt,
            output_path=output_path,
            model=model,
            size=size,
        )
        return result.model_dump()