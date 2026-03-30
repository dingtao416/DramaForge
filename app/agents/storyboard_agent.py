"""
DramaForge - Storyboard Agent
Agent for splitting scripts into storyboard panels.
"""

from typing import Any, Optional

from loguru import logger

from app.agents.base_agent import BaseAgent
from app.llm.prompts.storyboard import build_storyboard_prompt


class StoryboardAgent(BaseAgent):
    """Agent responsible for generating storyboard panels from scripts."""

    def __init__(self):
        super().__init__(name="StoryboardAgent")

    async def execute(self, **kwargs) -> Any:
        """Generate storyboards from a script."""
        return await self.generate_storyboards(**kwargs)

    async def generate_storyboards(
        self,
        script_content: str,
        style_prompt: str = "anime style, high quality, cinematic",
        characters: list[dict] = None,
        **kwargs,
    ) -> list[dict]:
        """
        Split a script into storyboard panels.

        Args:
            script_content: The full script text.
            style_prompt: Visual style description for image generation.
            characters: List of character dicts with name and appearance.

        Returns:
            List of storyboard dicts with sequence, descriptions, prompts, etc.
        """
        logger.info(
            f"Generating storyboards | script_length={len(script_content)} chars"
        )

        messages = build_storyboard_prompt(
            script_content=script_content,
            style_prompt=style_prompt,
            characters=characters,
        )

        result = await self._call_llm_json(messages, max_tokens=8192)

        storyboards = result.get("storyboards", [])
        logger.info(f"Storyboards generated | count={len(storyboards)}")

        # Validate and clean up
        for i, sb in enumerate(storyboards):
            sb["sequence"] = i + 1  # Ensure sequential numbering
            if not sb.get("duration"):
                sb["duration"] = 5.0
            if not sb.get("transition"):
                sb["transition"] = "crossfade"

        return storyboards