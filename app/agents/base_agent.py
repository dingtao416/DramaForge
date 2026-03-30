"""
DramaForge - Base Agent
Abstract base class for all agents.
Now powered by AI Hub — agents never touch HTTP clients directly.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from loguru import logger

from app.ai_hub import ai_hub


class BaseAgent(ABC):
    """Base class for all DramaForge agents."""

    def __init__(self, name: str):
        self.name = name
        self.hub = ai_hub
        logger.info(f"Agent [{self.name}] initialized")

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the agent's main task."""
        pass

    async def _call_llm(self, messages: list[dict], **kwargs) -> str:
        """Convenience method to call LLM via AI Hub."""
        logger.info(f"Agent [{self.name}] calling LLM...")
        resp = await self.hub.chat.complete(messages=messages, **kwargs)
        return resp.content

    async def _call_llm_json(self, messages: list[dict], **kwargs) -> dict:
        """Convenience method to call LLM and get JSON response via AI Hub."""
        logger.info(f"Agent [{self.name}] calling LLM (JSON mode)...")
        return await self.hub.chat.complete_json(messages=messages, **kwargs)
