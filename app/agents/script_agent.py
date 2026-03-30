"""
DramaForge - Script Agent
Agent for generating drama scripts and outlines.
"""

from typing import Any, Optional

from loguru import logger

from app.agents.base_agent import BaseAgent
from app.llm.prompts.script import build_outline_prompt, build_script_prompt


class ScriptAgent(BaseAgent):
    """Agent responsible for generating drama scripts."""

    def __init__(self):
        super().__init__(name="ScriptAgent")

    async def execute(self, **kwargs) -> Any:
        """Generate a script based on parameters."""
        action = kwargs.get("action", "generate_script")
        if action == "generate_outline":
            return await self.generate_outline(**kwargs)
        else:
            return await self.generate_script(**kwargs)

    async def generate_outline(
        self,
        genre: str,
        topic: str,
        total_episodes: int = 1,
        duration: int = 60,
        **kwargs,
    ) -> dict:
        """
        Generate a drama outline with characters and episode summaries.

        Returns:
            Dict containing title, synopsis, characters, and episodes.
        """
        logger.info(
            f"Generating outline | genre={genre} topic={topic} "
            f"episodes={total_episodes}"
        )

        messages = build_outline_prompt(
            genre=genre,
            topic=topic,
            total_episodes=total_episodes,
            duration=duration,
        )

        result = await self._call_llm_json(messages, max_tokens=8192)
        logger.info(f"Outline generated | title={result.get('title', 'N/A')}")
        return result

    async def generate_script(
        self,
        genre: str,
        topic: str,
        duration: int = 60,
        episode: int = 1,
        total_episodes: int = 1,
        outline: str = "",
        characters: list[dict] = None,
        style: str = "",
        **kwargs,
    ) -> str:
        """
        Generate a full script for a single episode.

        Returns:
            Script content as string.
        """
        logger.info(
            f"Generating script | genre={genre} topic={topic} "
            f"episode={episode}/{total_episodes}"
        )

        messages = build_script_prompt(
            genre=genre,
            topic=topic,
            duration=duration,
            episode=episode,
            total_episodes=total_episodes,
            outline=outline,
            characters=characters,
            style=style,
        )

        result = await self._call_llm(messages, max_tokens=8192, temperature=0.8)
        logger.info(f"Script generated | length={len(result)} chars")
        return result