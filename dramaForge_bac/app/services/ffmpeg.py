"""
DramaForge v2.0 — FFmpeg Composition Service
==============================================
Video composition operations using FFmpeg subprocess calls.
"""

from __future__ import annotations

import asyncio
import re
import tempfile
from pathlib import Path
from typing import Optional

from loguru import logger

from app.core.config import settings

RESOLUTION_RE = re.compile(r"^(\d{3,4})x(\d{3,4})$")

# — Color grading presets for time_of_day (Phase 3) —
_COLOR_GRADING: dict[str, str | None] = {
    "day": None,
    "dusk": "colorbalance=rs=0.1:gs=-0.05:bs=-0.1,eq=brightness=-0.05",
    "night": "colorbalance=rs=-0.2:gs=-0.15:bs=0.05,eq=brightness=-0.15:contrast=1.2",
    "dawn": "colorbalance=rs=0.15:gs=0.05:bs=-0.05,eq=saturation=0.8",
    "golden_hour": "colorbalance=rs=0.2:gs=0.1:bs=-0.2,hue=h=5:s=1.1",
    "overcast": "eq=saturation=0.6:brightness=-0.05:contrast=0.9",
    "indoor": "colorbalance=rs=0.05:gs=0.02:bs=0.08",
    "indoor_warm": "colorbalance=rs=0.15:gs=0.05:bs=-0.1",
    "indoor_cold": "colorbalance=rs=-0.1:gs=0.0:bs=0.15",
}

# — Ken Burns zoompan expression templates —
# fps: frames per second, frames = fps * duration, rate = zoom_step per frame
def _zoom_in_expr(frames: int, fps: int, w: int, h: int, rate: float = 0.0005) -> str:
    return f"zoompan=z='min(zoom+{rate},1.05)':d={frames}:s={w}x{h}:fps={fps}"

def _zoom_out_expr(frames: int, fps: int, w: int, h: int, rate: float = 0.0005) -> str:
    return f"zoompan=z='if(eq(n,0),1.05,max(zoom-{rate},1.0))':d={frames}:s={w}x{h}:fps={fps}"

def _pan_expr(frames: int, fps: int, w: int, h: int) -> str:
    return f"zoompan=z=1.05:x='iw/2-(iw/zoom/2)+sin(n*0.02)*40':d={frames}:s={w}x{h}:fps={fps}"

def _tilt_expr(frames: int, fps: int, w: int, h: int) -> str:
    return f"zoompan=z=1.05:y='ih/2-(ih/zoom/2)+sin(n*0.02)*40':d={frames}:s={w}x{h}:fps={fps}"

_ZOOM_FUNCS = {
    "zoom_in": _zoom_in_expr,
    "zoom_out": _zoom_out_expr,
    "dolly": lambda f, fp, w, h: _zoom_in_expr(f, fp, w, h, rate=0.0003),
    "pan": _pan_expr,
    "tracking": _pan_expr,
    "tilt": _tilt_expr,
}


def _escape_drawtext(value: str) -> str:
    return (
        value
        .replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace("%", "\\%")
        .replace("\n", "\\n")
        .replace("\r", "")
    )


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
        camera_movement: str = "static",
        time_of_day: str = "day",
        subtitle_text: Optional[str] = None,
        subtitle_font_size: int = 28,
        output_width: int = 1080,
        output_height: int = 1920,
        fps: int = 30,
    ) -> str:
        """
        Compose a static video from an image + optional audio.

        Supports Ken Burns effect (zoompan), per-shot subtitle overlay,
        and time-of-day colour grading.

        Args:
            image_path: Path to the input image.
            audio_path: Optional path to audio file (TTS dialogue).
            duration: Video duration in seconds.
            output_path: Where to write the output .mp4.
            camera_movement: One of static / zoom_in / zoom_out / pan / tilt / dolly / tracking.
            time_of_day: One of day / dusk / night / dawn / golden_hour / overcast / indoor / indoor_warm / indoor_cold.
            subtitle_text: Optional dialogue text to burn onto the frame.
            subtitle_font_size: Font size for subtitle text.
            output_width: Output video width (default 1080 for 9:16 portrait).
            output_height: Output video height.
            fps: Frames per second.
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        cmd = [self.ffmpeg, "-y"]

        # Input: loop image
        cmd.extend(["-loop", "1", "-i", image_path])

        if audio_path:
            cmd.extend(["-i", audio_path])

        # — Build video filter chain —
        vf_parts: list[str] = []
        frames = int(fps * duration)

        # 1. Ken Burns / zoompan effect
        zoom_fn = _ZOOM_FUNCS.get(camera_movement)
        if zoom_fn:
            vf_parts.append(zoom_fn(frames, fps, output_width, output_height))

        # 2. Subtitle overlay
        if subtitle_text:
            safe_text = _escape_drawtext(subtitle_text)
            vf_parts.append(
                f"drawtext=text='{safe_text}'"
                f":fontsize={subtitle_font_size}"
                f":fontcolor=white"
                f":borderw=2"
                f":bordercolor=black@0.6"
                f":x=(w-tw)/2"
                f":y=h-th-60"
            )

        # 3. Colour grading (time_of_day)
        color_filter = _COLOR_GRADING.get(time_of_day)
        if color_filter:
            vf_parts.append(color_filter)

        vf_str = ",".join(vf_parts) if vf_parts else None

        # — Build output encoding params —
        cmd.extend([
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
        ])

        if vf_str:
            if camera_movement != "static":
                # zoompan outputs at the target fps — no need for -tune stillimage
                cmd.extend(["-preset", "medium", "-crf", "18"])
            else:
                cmd.extend(["-tune", "stillimage", "-preset", "medium", "-crf", "18"])
            cmd.extend(["-vf", vf_str])
        else:
            cmd.extend(["-tune", "stillimage", "-preset", "medium", "-crf", "18"])

        if audio_path:
            cmd.extend([
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                "-t", str(duration),
            ])
        else:
            cmd.extend([
                "-an",
                "-t", str(duration),
            ])

        cmd.append(output_path)

        await self._run(cmd)
        logger.info(
            f"FFmpeg: static video → {output_path} "
            f"(movement={camera_movement} tod={time_of_day} "
            f"subtitle={'yes' if subtitle_text else 'no'})"
        )
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

    # — xfade transition name mapping —
    _XFADE_MAP: dict[str, str] = {
        "cut": "fade",           # minimal-duration fade (treated specially)
        "fade": "fade",
        "dissolve": "dissolve",
        "fade_to_black": "fadeblack",
        "fade_to_white": "fadewhite",
        "wipe_left": "wipeleft",
        "wipe_right": "wiperight",
        "wipe_up": "wipeup",
        "wipe_down": "wipedown",
        "slide_left": "slideright",
        "slide_right": "slideleft",
        "slide_up": "slideup",
        "slide_down": "slidedown",
        "radial": "radial",
        "circle_open": "circleopen",
        "circle_close": "circleclose",
        "rectangular": "rectcrop",
    }

    async def concat_with_transitions(
        self,
        clips: list[tuple[str, str, float]],  # (path, transition_type, duration_s)
        output_path: str,
        transition_duration: float = 0.5,
        output_width: int = 1080,
        output_height: int = 1920,
        fps: int = 30,
    ) -> str:
        """
        Concatenate video clips with smooth transitions between them.

        Uses the xfade filter for video transitions and acrossfade for audio.
        Clips without an audio track get silent audio generated on the fly.

        Args:
            clips: List of (file_path, transition_type, duration_seconds).
                   transition_type is applied *before* this clip (i.e. the
                   transition from the previous clip into this one).
            output_path: Where to write the concatenated .mp4.
            transition_duration: Duration of each transition in seconds.
            output_width: Normalised output width.
            output_height: Normalised output height.
            fps: Normalised frame rate.
        """
        n = len(clips)
        if n == 0:
            raise ValueError("No clips to concatenate")
        if n == 1:
            import shutil
            shutil.copy2(clips[0][0], output_path)
            return output_path

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # — Build input list —
        cmd = [self.ffmpeg, "-y"]
        for path, _, _ in clips:
            cmd.extend(["-i", path])

        # — Build filter_complex —
        filter_parts: list[str] = []
        video_labels: list[str] = []
        audio_labels: list[str] = []

        # Normalise each input (fps + scale + pad)
        for i in range(n):
            label_v = f"v{i}"
            label_a = f"a{i}"
            filter_parts.append(
                f"[{i}:v]setpts=PTS-STARTPTS,fps={fps},"
                f"scale={output_width}:{output_height}:force_original_aspect_ratio=decrease,"
                f"pad={output_width}:{output_height}:(ow-iw)/2:(oh-ih)/2,"
                f"format=yuv420p[{label_v}]"
            )
            # Generate silent audio for streams without audio
            dur = clips[i][2]
            filter_parts.append(
                f"[{i}:a]aformat=sample_rates=44100:channel_layouts=stereo,"
                f"apad,atrim=0:{dur}[{label_a}]"
            )
            video_labels.append(label_v)
            audio_labels.append(label_a)

        # Chain video xfades
        prev_v = video_labels[0]
        cumulative = clips[0][2]  # total duration so far (excluding transitions)
        vid_result = prev_v

        for i in range(1, n):
            trans_type = clips[i][1] or "cut"
            xfade_name = self._XFADE_MAP.get(trans_type, "dissolve")
            out_v = f"v_out_{i}"

            # For "cut" use an imperceptibly short xfade (1 frame)
            td = transition_duration if trans_type != "cut" else (1.0 / fps)

            offset = cumulative - td
            if offset < 0:
                offset = 0.0

            filter_parts.append(
                f"[{prev_v}][{video_labels[i]}]"
                f"xfade=transition={xfade_name}:duration={td}:offset={offset}"
                f"[{out_v}]"
            )
            prev_v = out_v
            vid_result = out_v
            cumulative += clips[i][2] - td

        # Chain audio acrossfades
        prev_a = audio_labels[0]
        aud_result = prev_a

        for i in range(1, n):
            trans_type = clips[i][1] or "cut"
            out_a = f"a_out_{i}"
            td = transition_duration if trans_type != "cut" else (1.0 / fps)

            filter_parts.append(
                f"[{prev_a}][{audio_labels[i]}]"
                f"acrossfade=d={td}:c1=tri:c2=tri"
                f"[{out_a}]"
            )
            prev_a = out_a
            aud_result = out_a

        filter_complex = ";".join(filter_parts)

        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", f"[{vid_result}]",
            "-map", f"[{aud_result}]",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path,
        ])

        await self._run(cmd)
        logger.info(
            f"FFmpeg: concat_with_transitions {n} clips → {output_path}"
        )
        return output_path

    async def mix_audio_with_ducking(
        self,
        main_audio_path: str,
        bgm_path: str,
        output_path: str,
        bgm_volume: float = 0.15,
        dialogue_volume: float = 1.0,
        duck_threshold: float = 0.1,
        duck_reduction: float = 6.0,
        attack: float = 0.01,
        release: float = 0.5,
    ) -> str:
        """
        Mix dialogue audio with background music using sidechain compression.

        When dialogue is present the BGM volume is automatically reduced (ducked).
        Uses FFmpeg sidechaincompress filter.

        Args:
            main_audio_path: Primary audio (dialogue / TTS mix).
            bgm_path: Background music file to duck.
            output_path: Where to write the mixed audio.
            bgm_volume: Base BGM volume ratio (0.0–1.0).
            dialogue_volume: Dialogue volume ratio (0.0–1.0).
            duck_threshold: dB threshold above which ducking triggers.
            duck_reduction: dB to reduce BGM when dialogue is active.
            attack: How fast ducking engages (seconds).
            release: How fast ducking releases (seconds).
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            self.ffmpeg, "-y",
            "-i", main_audio_path,
            "-i", bgm_path,
            "-filter_complex",
            (
                f"[0:a]volume={dialogue_volume}[main];"
                f"[1:a]volume={bgm_volume}[bgm];"
                f"[main]asplit[main_out][side];"
                f"[bgm][side]sidechaincompress="
                f"threshold={duck_threshold}:ratio=10:"
                f"attack={attack}:release={release}[bgm_ducked];"
                f"[main_out][bgm_ducked]amix=inputs=2:duration=first:"
                f"dropout_transition=2[aout]"
            ),
            "-map", "[aout]",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path,
        ]

        await self._run(cmd)
        logger.info(
            f"FFmpeg: audio ducking → {output_path} "
            f"(bgm_vol={bgm_volume} duck={duck_reduction}dB)"
        )
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

        # Escape special characters for FFmpeg drawtext filter syntax.
        safe_text = _escape_drawtext(subtitle_text)

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
        bgm_volume: float = 0.15,
        quality: str = "high",
        resolution: str = None,
        subtitle_text: Optional[str] = None,
        subtitle_font_size: int = 24,
        subtitle_position: str = "bottom",
    ) -> str:
        """
        Compose a full episode from segments.

        Args:
            segment_paths: Ordered list of segment video files.
            output_path: Where to write the final video.
            bgm_path: Optional background music audio file.
            bgm_volume: BGM volume ratio (0.0–1.0).
            quality: 'low' | 'medium' | 'high' — controls CRF.
            resolution: e.g. '720x1280', '1080x1920'. None = no scaling.
            subtitle_text: Optional subtitle text to overlay.
            subtitle_font_size: Font size for subtitle.
            subtitle_position: 'top' | 'bottom'.
        """
        quality_crf = {"low": 28, "medium": 23, "high": 18}.get(quality, 18)
        quality_preset = {"low": "ultrafast", "medium": "medium", "high": "slow"}.get(quality, "slow")

        # Build video filter chain
        vf_parts = []
        if resolution:
            match = RESOLUTION_RE.fullmatch(resolution)
            if not match:
                raise ValueError("resolution must use WIDTHxHEIGHT format")
            w, h = match.groups()
            vf_parts.append(f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2")
        if subtitle_text:
            safe_text = _escape_drawtext(subtitle_text)
            y = "h-th-40" if subtitle_position == "bottom" else "40"
            vf_parts.append(
                f"drawtext=text='{safe_text}':fontsize={subtitle_font_size}"
                f":fontcolor=white:borderw=2:bordercolor=black"
                f":x=(w-tw)/2:y={y}"
            )
        vf_str = ",".join(vf_parts) if vf_parts else None

        # First concatenate all segments
        temp_concat = str(Path(output_path).parent / "_temp_concat.mp4")
        await self.concat_segments(segment_paths, temp_concat)

        try:
            if bgm_path:
                # Use -filter_complex for audio mixing; -vf for video filtering
                cmd = [
                    self.ffmpeg, "-y",
                    "-i", temp_concat,
                    "-i", bgm_path,
                    "-filter_complex",
                    f"[0:a]volume=1.0[a1];[1:a]volume={bgm_volume}[a2];[a1][a2]amix=inputs=2:duration=first[aout]",
                    "-map", "0:v",
                    "-map", "[aout]",
                    "-c:v", "libx264",
                    "-crf", str(quality_crf),
                    "-preset", quality_preset,
                    "-c:a", "aac",
                    "-b:a", "192k",
                ]
                if vf_str:
                    cmd.extend(["-vf", vf_str])
                cmd.append(output_path)
            else:
                cmd = [
                    self.ffmpeg, "-y",
                    "-i", temp_concat,
                    "-c:v", "libx264",
                    "-crf", str(quality_crf),
                    "-preset", quality_preset,
                    "-c:a", "aac",
                    "-b:a", "192k",
                ]
                if vf_str:
                    cmd.extend(["-vf", vf_str])
                cmd.append(output_path)

            await self._run(cmd)
        finally:
            Path(temp_concat).unlink(missing_ok=True)

        labels = [f"q={quality}"]
        if bgm_path:
            labels.append("+bgm")
        if subtitle_text:
            labels.append("+sub")
        if resolution:
            labels.append(f"@{resolution}")
        logger.info(f"FFmpeg: episode composed ({' '.join(labels)}) → {output_path}")
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
