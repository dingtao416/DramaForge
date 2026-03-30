"""
DramaForge - Video Agent
Agent for video production with two capabilities:
  1. AI video generation (Sora 2) — via AI Hub
  2. Local video composition (moviepy) — stitch images + audio + subtitles
"""

from pathlib import Path
from typing import Any, Optional

from loguru import logger
from moviepy import (
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    concatenate_videoclips,
)

from app.ai_hub import ai_hub
from config import settings


class VideoAgent:
    """Agent responsible for video generation and composition."""

    def __init__(self):
        self.name = "VideoAgent"
        self.default_resolution = (1080, 1920)  # Vertical video for short drama
        self.default_fps = 30
        logger.info(f"Agent [{self.name}] initialized")

    async def execute(self, **kwargs) -> Any:
        """Compose final video."""
        return await self.compose_video(**kwargs)

    # ──────────── AI Video Generation (Sora 2) ────────────

    async def generate_video(
        self,
        prompt: str,
        output_path: str,
        **kwargs,
    ) -> dict:
        """
        Generate a video clip from a text prompt using Sora 2.

        Returns:
            Dict with video_path, video_url, status, etc.
        """
        result = await ai_hub.video.generate(
            prompt=prompt,
            output_path=output_path,
            **kwargs,
        )
        return result.model_dump()

    # ──────────── Local Video Composition ────────────

    async def compose_video(
        self,
        storyboards: list[dict],
        output_path: str,
        resolution: tuple[int, int] = None,
        fps: int = None,
        **kwargs,
    ) -> dict:
        """
        Compose a video from storyboard assets (images + audio + subtitles).

        Args:
            storyboards: List of storyboard dicts with image_path, audio_path, etc.
            output_path: Path for the output video file.
            resolution: Video resolution (width, height).
            fps: Frames per second.

        Returns:
            Dict with video_path and duration.
        """
        resolution = resolution or self.default_resolution
        fps = fps or self.default_fps
        width, height = resolution

        logger.info(
            f"Composing video | panels={len(storyboards)} "
            f"resolution={width}x{height}"
        )

        clips = []
        for sb in storyboards:
            image_path = sb.get("image_path")
            audio_path = sb.get("audio_path")
            duration = sb.get("audio_duration") or sb.get("duration", 5.0)
            narration = sb.get("narration", "")
            dialogue = sb.get("dialogue", "")

            if not image_path or not Path(image_path).exists():
                logger.warning(f"Skipping panel {sb.get('sequence')}: no image")
                continue

            # Create image clip
            img_clip = (
                ImageClip(image_path)
                .resized((width, height))
                .with_duration(duration)
            )

            # Add audio if available
            if audio_path and Path(audio_path).exists():
                audio_clip = AudioFileClip(audio_path)
                # Adjust image duration to match audio
                duration = audio_clip.duration
                img_clip = img_clip.with_duration(duration)
                img_clip = img_clip.with_audio(audio_clip)

            # Add subtitle text
            subtitle_text = dialogue or narration
            if subtitle_text:
                txt_clip = (
                    TextClip(
                        text=subtitle_text,
                        font_size=36,
                        color="white",
                        stroke_color="black",
                        stroke_width=2,
                        size=(width - 80, None),
                        method="caption",
                        font="Arial",
                    )
                    .with_duration(duration)
                    .with_position(("center", height - 200))
                )
                img_clip = CompositeVideoClip([img_clip, txt_clip])

            clips.append(img_clip)

        if not clips:
            raise ValueError("No valid clips to compose video")

        # Concatenate all clips
        final = concatenate_videoclips(clips, method="compose")

        # Write output
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Writing video to {output_path}...")
        final.write_videofile(
            str(output_file),
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            logger=None,  # Suppress moviepy's verbose output
        )

        total_duration = final.duration
        final.close()

        logger.info(f"Video composed | path={output_path} duration={total_duration:.1f}s")

        return {
            "video_path": str(output_file),
            "duration": total_duration,
            "resolution": f"{width}x{height}",
        }