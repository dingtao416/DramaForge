"""
DramaForge v2.0 — FFmpeg Composition Service
==============================================
Video composition operations using FFmpeg subprocess calls.
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import Optional

from loguru import logger

from app.core.config import settings


class FFmpegService:
    """FFmpeg-based video composition operations."""

    @property
    def ffmpeg(self) -> str:
        return settings.ffmpeg_path

    async def _run(self, cmd: list[str]) -> str:
        """Run an FFmpeg command asynchronously."""
        logger.debug(f"FFmpeg: {' '.join(cmd)}")
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_msg = stderr.decode(errors="replace")
            logger.error(f"FFmpeg error (code {proc.returncode}): {error_msg[:500]}")
            raise RuntimeError(f"FFmpeg failed: {error_msg[:200]}")

        return stdout.decode(errors="replace")

    async def compose_static_video(
        self,
        image_path: str,
        audio_path: Optional[str],
        duration: float,
        output_path: str,
    ) -> str:
        """
        Compose a static video from an image + optional audio.

        The image is displayed for the given duration (or audio length).
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        cmd = [self.ffmpeg, "-y"]

        # Input: loop image
        cmd.extend(["-loop", "1", "-i", image_path])

        if audio_path:
            cmd.extend(["-i", audio_path])
            # Use audio duration if available, otherwise fall back to specified
            cmd.extend([
                "-c:v", "libx264",
                "-tune", "stillimage",
                "-c:a", "aac",
                "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-shortest",
                "-t", str(duration),
                output_path,
            ])
        else:
            cmd.extend([
                "-c:v", "libx264",
                "-tune", "stillimage",
                "-pix_fmt", "yuv420p",
                "-t", str(duration),
                "-an",
                output_path,
            ])

        await self._run(cmd)
        logger.info(f"FFmpeg: static video → {output_path}")
        return output_path

    async def concat_segments(
        self,
        segment_paths: list[str],
        output_path: str,
    ) -> str:
        """
        Concatenate multiple video segments into one.

        Uses the FFmpeg concat demuxer.
        """
        if not segment_paths:
            raise ValueError("No segments to concatenate")

        if len(segment_paths) == 1:
            # Just copy
            import shutil
            shutil.copy2(segment_paths[0], output_path)
            return output_path

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Create concat file list
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            for path in segment_paths:
                # FFmpeg concat demuxer needs escaped paths
                safe_path = path.replace("'", "'\\''")
                f.write(f"file '{safe_path}'\n")
            concat_file = f.name

        cmd = [
            self.ffmpeg, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            output_path,
        ]

        try:
            await self._run(cmd)
        finally:
            Path(concat_file).unlink(missing_ok=True)

        logger.info(f"FFmpeg: concat {len(segment_paths)} segments → {output_path}")
        return output_path

    async def add_subtitle(
        self,
        video_path: str,
        subtitle_text: str,
        output_path: str,
        font_size: int = 24,
        position: str = "bottom",
    ) -> str:
        """Add burned-in subtitle text to a video."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Escape special characters for FFmpeg drawtext
        safe_text = subtitle_text.replace("'", "\\'").replace(":", "\\:")

        y_pos = "h-th-40" if position == "bottom" else "40"

        cmd = [
            self.ffmpeg, "-y",
            "-i", video_path,
            "-vf", (
                f"drawtext=text='{safe_text}'"
                f":fontsize={font_size}"
                f":fontcolor=white"
                f":borderw=2"
                f":bordercolor=black"
                f":x=(w-tw)/2"
                f":y={y_pos}"
            ),
            "-c:a", "copy",
            output_path,
        ]

        await self._run(cmd)
        logger.info(f"FFmpeg: subtitle added → {output_path}")
        return output_path

    async def compose_episode(
        self,
        segment_paths: list[str],
        output_path: str,
        bgm_path: Optional[str] = None,
    ) -> str:
        """
        Compose a full episode from segments, optionally with background music.
        """
        # First concatenate all segments
        if bgm_path:
            # Concat then mix BGM
            temp_concat = str(Path(output_path).parent / "_temp_concat.mp4")
            await self.concat_segments(segment_paths, temp_concat)

            # Mix BGM at lower volume
            cmd = [
                self.ffmpeg, "-y",
                "-i", temp_concat,
                "-i", bgm_path,
                "-filter_complex",
                "[0:a]volume=1.0[a1];[1:a]volume=0.15[a2];[a1][a2]amix=inputs=2:duration=first[aout]",
                "-map", "0:v",
                "-map", "[aout]",
                "-c:v", "copy",
                "-c:a", "aac",
                output_path,
            ]
            try:
                await self._run(cmd)
            finally:
                Path(temp_concat).unlink(missing_ok=True)
        else:
            await self.concat_segments(segment_paths, output_path)

        logger.info(f"FFmpeg: episode composed → {output_path}")
        return output_path

    async def get_duration(self, file_path: str) -> float:
        """Get the duration of a media file in seconds."""
        cmd = [
            self.ffmpeg.replace("ffmpeg", "ffprobe"),
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path,
        ]
        try:
            output = await self._run(cmd)
            return float(output.strip())
        except Exception:
            return 0.0


# Module-level singleton
ffmpeg_service = FFmpegService()
