"""
DramaForge AI Hub - TTS Service
Text-to-Speech via laozhang.ai OpenAI-compatible endpoint.

Models:  tts-1 (standard, fast) | tts-1-hd (HD, more natural)
Voices:  alloy (中�? | echo (�? | fable (英式) |
         onyx (低沉�? | nova (�? | shimmer (柔和�?
Formats: mp3 | opus | aac | flac | wav | pcm

Docs: https://docs.laozhang.ai/
"""

from __future__ import annotations

import struct
from pathlib import Path
from typing import Optional

from loguru import logger

from app.core.config import settings
from app.ai_hub._client import BaseClient
from app.ai_hub._models import TTSResponse


class TTSService:
    """Text-to-Speech service - generates narration & dialogue audio."""

    # Voice descriptions for convenience
    VOICES = {
        "alloy": "中性嗓音，适合旁白",
        "echo": "成熟男声",
        "fable": "英式男声，适合讲故事",
        "onyx": "低沉男声，稳重",
        "nova": "年轻女声，活泼",
        "shimmer": "柔和女声，温和",
    }

    async def speak(
        self,
        text: str,
        output_path: str,
        *,
        model: str = None,
        voice: str = None,
        speed: float = None,
        response_format: str = "mp3",
    ) -> TTSResponse:
        """
        Convert text to speech audio file.

        Args:
            text: Text to synthesize.
            output_path: Where to save the audio file.
            model: TTS model (default from config).
            voice: Voice name (default from config).
            speed: Playback speed 0.25~4.0 (default from config).
            response_format: Audio format (mp3/opus/aac/flac/wav/pcm).

        Returns:
            TTSResponse with audio_path, duration estimate, etc.
        """
        use_model = model or settings.tts_model
        use_voice = voice or settings.tts_default_voice
        use_speed = speed if speed is not None else settings.tts_speed

        logger.info(
            f"tts.speak | model={use_model} voice={use_voice} "
            f"speed={use_speed} text_len={len(text)} fmt={response_format}"
        )

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        client = BaseClient.openai()

        resp = await BaseClient.with_retry(
            lambda: client.audio.speech.create(
                model=use_model,
                voice=use_voice,
                input=text,
                speed=use_speed,
                response_format=response_format,
            ),
            label=f"tts:{use_model}",
        )

        # Stream response to file
        audio_bytes = resp.content
        out.write_bytes(audio_bytes)

        # Estimate duration from file size
        duration = _estimate_duration(audio_bytes, response_format)

        logger.info(
            f"tts.speak done | path={out} "
            f"size={len(audio_bytes)} duration≈{duration:.1f}s"
        )

        return TTSResponse(
            audio_path=str(out),
            model=use_model,
            voice=use_voice,
            duration=duration,
        )

    async def speak_batch(
        self,
        items: list[dict],
        output_dir: str,
        *,
        model: str = None,
        voice: str = None,
        prefix: str = "audio",
    ) -> list[TTSResponse | dict]:
        """
        Batch TTS generation.

        Args:
            items: List of dicts with "text" key (and optional "voice" key).
            output_dir: Directory to save audio files.
            model: TTS model.
            voice: Default voice (can be overridden per item).
            prefix: Filename prefix.

        Returns:
            List of TTSResponse (or error dicts on failure).
        """
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        results = []
        total = len(items)
        for idx, item in enumerate(items, 1):
            text = item.get("text", "")
            if not text:
                continue

            path = str(out_dir / f"{prefix}_{idx:03d}.mp3")
            item_voice = item.get("voice", voice)

            try:
                result = await self.speak(
                    text=text,
                    output_path=path,
                    model=model,
                    voice=item_voice,
                )
                results.append(result)
                logger.info(f"tts batch [{idx}/{total}] OK")
            except Exception as e:
                logger.error(f"tts batch [{idx}/{total}] FAIL: {e}")
                results.append({"error": str(e), "text": text[:50]})

        return results

    def list_voices(self) -> dict[str, str]:
        """Return available voices and their descriptions."""
        return self.VOICES.copy()


# ──────────── Helpers ────────────

def _estimate_duration(audio_bytes: bytes, fmt: str) -> float:
    """Rough duration estimate from file size and format bitrate."""
    size = len(audio_bytes)
    # Average bitrates (bytes/sec)
    bitrate_map = {
        "mp3": 16_000,   # ~128kbps
        "opus": 8_000,   # ~64kbps
        "aac": 16_000,
        "flac": 80_000,
        "wav": 176_400,  # 44.1kHz 16bit stereo
        "pcm": 32_000,   # 16kHz 16bit mono
    }
    bps = bitrate_map.get(fmt, 16_000)
    return max(0.1, size / bps)
