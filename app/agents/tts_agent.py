"""
DramaForge - TTS Agent
Agent for generating speech audio — delegates to AI Hub TTS service.
"""

from typing import Any, Optional

from loguru import logger

from app.ai_hub import ai_hub


class TTSAgent:
    """Agent responsible for text-to-speech generation."""

    def __init__(self):
        self.name = "TTSAgent"
        logger.info(f"Agent [{self.name}] initialized")

    async def execute(self, **kwargs) -> Any:
        """Generate audio for text."""
        return await self.generate_audio(**kwargs)

    async def generate_audio(
        self,
        text: str,
        output_path: str,
        voice: Optional[str] = None,
        **kwargs,
    ) -> dict:
        """
        Generate audio from text.

        Returns:
            Dict with audio_path and duration.
        """
        result = await ai_hub.tts.speak(
            text=text,
            output_path=output_path,
            voice=voice,
        )
        return result.model_dump()

    @staticmethod
    def list_voices() -> dict[str, str]:
        """List available TTS voices."""
        return ai_hub.tts.list_voices()
