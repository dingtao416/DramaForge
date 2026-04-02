"""
DramaForge v2.0 — Video Engine
================================
Full pipeline: episode → storyboard split → asset generation →
video strategy decision → segment composition → episode assembly.

Covers Spec 22 (storyboard split), Spec 23 (asset gen), Spec 24 (strategy),
Spec 26 (full pipeline orchestration).
"""

from __future__ import annotations

import asyncio
from typing import Optional

from loguru import logger

from app.ai_hub import ai_hub
from app.models.episode import Episode
from app.models.segment import Segment, SegmentStatus
from app.models.shot import Shot
from app.models.character import Character
from app.models.scene import SceneLocation
from app.prompts.storyboard_prompts import build_storyboard_prompt, build_asset_context
from app.services.ref_resolver import RefResolver
from app.services.storage import storage


class VideoEngine:
    """
    Core engine for the video generation pipeline.

    Pipeline stages:
    ① LLM splits episode → Shot[]
    ② @reference resolution
    ③ Parallel image + audio generation per shot
    ④ Video strategy decision per segment
    ⑤ Segment video composition
    ⑥ Episode-level assembly
    """

    # ═══════════════════════════════════════════════════════════════
    # Spec 22: Storyboard split
    # ═══════════════════════════════════════════════════════════════

    async def split_storyboard(
        self,
        episode: Episode,
        characters: list[Character],
        scenes: list[SceneLocation],
        shots_per_segment: int = 5,
    ) -> list[dict]:
        """
        Use LLM to split an episode into structured segments and shots.

        Returns:
            List of segment dicts, each containing a list of shot dicts.
        """
        logger.info(f"VideoEngine: splitting storyboard for episode={episode.id}")

        # Build asset context strings
        char_dicts = [
            {"name": c.name, "role": c.role.value if c.role else "", "description": c.description or ""}
            for c in characters
        ]
        scene_dicts = [
            {"name": s.name, "description": s.description or "",
             "time_of_day": s.time_of_day or "day", "interior": s.interior}
            for s in scenes
        ]
        chars_ctx, scenes_ctx = build_asset_context(char_dicts, scene_dicts)

        # Build prompt
        messages = build_storyboard_prompt(
            episode_title=episode.title or f"第{episode.number}集",
            episode_content=episode.content or "",
            characters_context=chars_ctx,
            scenes_context=scenes_ctx,
            shots_per_segment=shots_per_segment,
        )

        # Call LLM
        raw = await ai_hub.chat.complete_json(
            messages=messages,
            temperature=0.5,
            max_tokens=8192,
        )

        # Parse and resolve references
        resolver = RefResolver(characters, scenes)
        segments = raw.get("segments", [])
        return self._resolve_segments(segments, resolver, characters)

    def _resolve_segments(
        self,
        raw_segments: list[dict],
        resolver: RefResolver,
        characters: list[Character],
    ) -> list[dict]:
        """Resolve @references in raw LLM output and map to char IDs."""
        resolved = []
        for seg_data in raw_segments:
            shots = []
            for shot_data in seg_data.get("shots", []):
                # Resolve character references → char_id
                resolved_chars = []
                for ch_ref in shot_data.get("characters", []):
                    name = ch_ref.get("name", "").lstrip("@")
                    char = resolver.resolve_character(name)
                    if char:
                        resolved_chars.append({
                            "char_id": char.id,
                            "appearance_idx": 0,
                            "action": ch_ref.get("action", ""),
                        })

                # Resolve scene reference
                scene_ref = shot_data.get("scene_ref", "").lstrip("@")

                shots.append({
                    "duration": shot_data.get("duration", 5),
                    "time_of_day": shot_data.get("time_of_day", "day"),
                    "scene_ref": scene_ref,
                    "camera_type": shot_data.get("camera_type", "medium"),
                    "camera_angle": shot_data.get("camera_angle", "eye_level"),
                    "camera_movement": shot_data.get("camera_movement", "static"),
                    "characters": resolved_chars,
                    "dialogue": shot_data.get("dialogue", ""),
                    "voice_style": shot_data.get("voice_style", ""),
                    "background": shot_data.get("background", ""),
                    "transition": shot_data.get("transition", "cut"),
                })

            resolved.append({
                "title": seg_data.get("title", ""),
                "shots": shots,
            })
        return resolved

    def _build_asset_context(
        self, characters: list[Character], scenes: list[SceneLocation]
    ) -> str:
        """Build a text summary of available assets for context."""
        parts = ["Available Characters:"]
        for ch in characters:
            parts.append(f"  - {ch.name} ({ch.role.value if ch.role else 'unknown'})")

        parts.append("\nAvailable Scenes:")
        for sc in scenes:
            parts.append(f"  - {sc.name} ({sc.time_of_day or 'day'})")

        return "\n".join(parts)

    # ═══════════════════════════════════════════════════════════════
    # Spec 23: Shot asset generation
    # ═══════════════════════════════════════════════════════════════

    async def _generate_shot_assets(
        self,
        shot: Shot,
        characters: list[Character],
        scenes: list[SceneLocation],
        project_id: int,
        ep_num: int,
        style: str = "realistic",
    ) -> Shot:
        """Generate image and audio for a single shot in parallel."""
        logger.info(f"VideoEngine: generating assets for shot={shot.id}")

        # Build prompts
        shot_dict = {
            "scene_ref": shot.scene_ref,
            "characters": shot.characters or [],
            "camera_type": shot.camera_type,
            "camera_angle": shot.camera_angle,
            "camera_movement": shot.camera_movement,
            "background": shot.background,
            "time_of_day": shot.time_of_day,
            "duration": shot.duration,
        }
        char_dicts = [
            {"id": c.id, "name": c.name, "description": c.description or ""}
            for c in characters
        ]
        scene_dicts = [
            {"name": s.name, "description": s.description or ""}
            for s in scenes
        ]

        # Build image prompt
        image_prompt = await ai_hub.prompt.build_image_prompt(
            shot=shot_dict, characters=char_dicts, scenes=scene_dicts, style=style
        )
        shot.image_prompt = image_prompt

        # Parallel: image + audio
        tasks = []

        # Image generation task
        image_path = storage.shot_image_path(project_id, ep_num, shot.index)
        tasks.append(self._gen_image(image_prompt, str(image_path)))

        # Audio generation task (if there's dialogue)
        audio_path = None
        if shot.dialogue:
            audio_path = storage.shot_audio_path(project_id, ep_num, shot.index)
            tasks.append(self._gen_audio(shot.dialogue, str(audio_path), shot.voice_style))
        else:
            tasks.append(asyncio.sleep(0))  # placeholder

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process image result
        if not isinstance(results[0], Exception):
            shot.image_url = storage.get_url(image_path)
        else:
            logger.error(f"Image gen failed for shot {shot.id}: {results[0]}")

        # Process audio result
        if audio_path and not isinstance(results[1], Exception):
            shot.audio_url = storage.get_url(audio_path)
        elif audio_path and isinstance(results[1], Exception):
            logger.error(f"Audio gen failed for shot {shot.id}: {results[1]}")

        return shot

    async def _gen_image(self, prompt: str, output_path: str):
        """Generate an image."""
        return await ai_hub.image.generate(prompt=prompt, output_path=output_path)

    async def _gen_audio(self, text: str, output_path: str, voice_style: str = ""):
        """Generate TTS audio."""
        return await ai_hub.tts.speak(text=text, output_path=output_path)

    # ═══════════════════════════════════════════════════════════════
    # Spec 24: Video strategy decision
    # ═══════════════════════════════════════════════════════════════

    def _decide_video_strategy(self, segment: Segment) -> str:
        """
        Decide the video generation strategy for a segment.

        Returns:
            "ai_video" — use AI video generation (motion shots)
            "img2video" — convert image to video with Ken Burns
            "static_compose" — static image + audio via FFmpeg
        """
        if not segment.shots:
            return "static_compose"

        # Check if any shot has camera movement
        has_motion = any(
            (s.camera_movement and s.camera_movement != "static")
            for s in segment.shots
        )

        if has_motion:
            return "ai_video"

        return "static_compose"

    async def _generate_segment_video(
        self,
        segment: Segment,
        project_id: int,
        ep_num: int,
    ) -> str:
        """Generate video for a segment based on strategy."""
        from app.services.ffmpeg import ffmpeg_service

        strategy = self._decide_video_strategy(segment)
        logger.info(f"VideoEngine: segment={segment.id} strategy={strategy}")

        output_path = storage.segment_video_path(project_id, ep_num, segment.index)

        if strategy == "static_compose":
            # Compose each shot: image + audio → clip, then concat
            clip_paths = []
            for shot in segment.shots:
                if shot.image_url:
                    image_file = storage.storage_path_from_url(shot.image_url) if hasattr(storage, 'storage_path_from_url') else shot.image_url
                    audio_file = shot.audio_url if shot.audio_url else None
                    clip_path = storage.segment_video_path(
                        project_id, ep_num, segment.index
                    ).parent / f"shot_{shot.index:04d}.mp4"

                    await ffmpeg_service.compose_static_video(
                        image_path=str(image_file),
                        audio_path=str(audio_file) if audio_file else None,
                        duration=shot.duration or 5.0,
                        output_path=str(clip_path),
                    )
                    clip_paths.append(str(clip_path))

            if clip_paths:
                await ffmpeg_service.concat_segments(clip_paths, str(output_path))

        elif strategy == "ai_video":
            # Use AI video generation for the first shot's prompt
            if segment.shots:
                shot = segment.shots[0]
                video_prompt = shot.video_prompt or shot.image_prompt or ""
                if video_prompt:
                    result = await ai_hub.video.generate(
                        prompt=video_prompt,
                        output_path=str(output_path),
                    )

        segment.video_url = storage.get_url(output_path)
        segment.status = SegmentStatus.COMPLETED
        return str(output_path)

    # ═══════════════════════════════════════════════════════════════
    # Spec 26: Full generation pipeline
    # ═══════════════════════════════════════════════════════════════

    async def generate_episode(
        self,
        episode: Episode,
        characters: list[Character],
        scenes: list[SceneLocation],
        project_id: int,
        style: str = "realistic",
        shots_per_segment: int = 5,
    ) -> list[Segment]:
        """
        Full pipeline: generate all segments and shots for an episode.

        Steps:
        1. Split storyboard via LLM
        2. Create Segment + Shot ORM objects
        3. Generate assets (image + audio) for each shot
        4. Generate video for each segment
        """
        logger.info(f"VideoEngine: full pipeline for episode={episode.id}")

        # Step 1: Split storyboard
        segments_data = await self.split_storyboard(
            episode, characters, scenes, shots_per_segment
        )

        # Step 2: Create ORM objects (caller is responsible for DB session)
        segments = []
        for seg_idx, seg_data in enumerate(segments_data):
            segment = Segment(
                episode_id=episode.id,
                index=seg_idx,
                status=SegmentStatus.PENDING,
            )
            shots = []
            for shot_idx, shot_data in enumerate(seg_data.get("shots", [])):
                shot = Shot(
                    index=shot_idx,
                    **{k: v for k, v in shot_data.items()
                       if k in ("duration", "time_of_day", "scene_ref", "camera_type",
                                "camera_angle", "camera_movement", "characters",
                                "dialogue", "voice_style", "background", "transition")},
                )
                shots.append(shot)

            segment.shots = shots
            segments.append(segment)

        return segments

    async def generate_segment_assets(
        self,
        segment: Segment,
        characters: list[Character],
        scenes: list[SceneLocation],
        project_id: int,
        ep_num: int,
        style: str = "realistic",
    ) -> Segment:
        """Generate all shot assets for a segment."""
        segment.status = SegmentStatus.GENERATING

        for shot in segment.shots:
            try:
                await self._generate_shot_assets(
                    shot, characters, scenes, project_id, ep_num, style
                )
            except Exception as e:
                logger.error(f"Shot asset generation failed: {e}")

        # Build video prompt for motion shots
        for shot in segment.shots:
            if shot.camera_movement and shot.camera_movement != "static":
                shot_dict = {
                    "scene_ref": shot.scene_ref,
                    "characters": shot.characters or [],
                    "camera_type": shot.camera_type,
                    "camera_angle": shot.camera_angle,
                    "camera_movement": shot.camera_movement,
                    "background": shot.background,
                    "time_of_day": shot.time_of_day,
                    "duration": shot.duration,
                }
                char_dicts = [{"id": c.id, "name": c.name, "description": c.description or ""} for c in characters]
                scene_dicts = [{"name": s.name, "description": s.description or ""} for s in scenes]
                shot.video_prompt = await ai_hub.prompt.build_video_prompt(
                    shot=shot_dict, characters=char_dicts, scenes=scene_dicts
                )

        return segment

    async def regenerate_segment(
        self,
        segment: Segment,
        characters: list[Character],
        scenes: list[SceneLocation],
        project_id: int,
        ep_num: int,
    ) -> Segment:
        """Regenerate a single segment's assets and video."""
        segment.status = SegmentStatus.GENERATING

        await self.generate_segment_assets(
            segment, characters, scenes, project_id, ep_num
        )

        try:
            await self._generate_segment_video(segment, project_id, ep_num)
        except Exception as e:
            logger.error(f"Segment video generation failed: {e}")
            segment.status = SegmentStatus.FAILED

        return segment

    async def compose_full_episode(
        self,
        segments: list[Segment],
        project_id: int,
        ep_num: int,
        bgm_path: Optional[str] = None,
    ) -> str:
        """Compose all segments into a full episode video."""
        from app.services.ffmpeg import ffmpeg_service

        output_path = storage.episode_video_path(project_id, ep_num)

        segment_paths = [
            str(storage.segment_video_path(project_id, ep_num, seg.index))
            for seg in segments
            if seg.video_url
        ]

        if not segment_paths:
            raise ValueError("No segment videos to compose")

        await ffmpeg_service.compose_episode(
            segment_paths=segment_paths,
            output_path=str(output_path),
            bgm_path=bgm_path,
        )

        return storage.get_url(output_path)


# Module-level singleton
video_engine = VideoEngine()
