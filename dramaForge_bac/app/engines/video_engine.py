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
from app.ai_hub.chat import _parse_json as parse_json_from_llm
from app.models.episode import Episode
from app.models.segment import Segment, SegmentStatus
from app.models.shot import Shot
from app.models.character import Character
from app.models.scene import SceneLocation
from app.prompts.storyboard_prompts import (
    build_storyboard_prompt,
    build_storyboard_repair_prompt,
    build_asset_context,
)
from app.services.ref_resolver import RefResolver
from app.services.storage import storage
from app.services.video_reference_capabilities import (
    append_reference_instructions,
    reference_image_payload,
    supports_visual_references,
)


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
        chat_model: str = None,
        chat_api_key: str = None,
        chat_base_url: str = None,
        chat_options: dict | None = None,
        script: Script | None = None,
    ) -> list[dict]:
        """
        Use LLM to split an episode into structured segments and shots.

        Returns:
            List of segment dicts, each containing a list of shot dicts.
        """
        logger.info(f"VideoEngine: splitting storyboard for episode={episode.id}")

        # Build asset context strings (include reference_images for visual hints)
        char_dicts = [
            {
                "name": c.name,
                "role": c.role.value if c.role else "",
                "description": c.description or "",
                "reference_images": c.reference_images or [],
            }
            for c in characters
        ]
        scene_dicts = [
            {
                "name": s.name,
                "description": s.description or "",
                "time_of_day": s.time_of_day or "day",
                "interior": s.interior,
                "reference_images": s.reference_images or [],
            }
            for s in scenes
        ]
        chars_ctx, scenes_ctx = build_asset_context(char_dicts, scene_dicts)

        # Build Story Bible context
        bible_context = ""
        if script:
            parts = []
            if script.premise:
                parts.append(f"核心命题：{script.premise}")
            if script.visual_style_rules:
                parts.append(f"视觉风格规则：{script.visual_style_rules}")
            if script.character_relationships:
                parts.append(f"人物关系：{script.character_relationships}")
            if script.episode_arc:
                parts.append(f"分集节奏：{script.episode_arc}")
            if script.continuity_notes:
                parts.append(f"连续性要求：{script.continuity_notes}")
            bible_context = "\n".join(parts)

        # Build prompt
        messages = build_storyboard_prompt(
            episode_title=episode.title or f"第{episode.number}集",
            episode_content=episode.content or "",
            characters_context=chars_ctx,
            scenes_context=scenes_ctx,
            shots_per_segment=shots_per_segment,
            story_bible_context=bible_context,
        )

        # Call LLM
        resp = await ai_hub.chat.complete(
            messages=messages,
            temperature=0.5,
            max_tokens=8192,
            response_format={"type": "json_object"},
            model=chat_model,
            api_key=chat_api_key,
            base_url=chat_base_url,
            **_extra_chat_kwargs(chat_options),
        )
        raw = await self._parse_storyboard_json(
            resp.content,
            chat_model=chat_model,
            chat_api_key=chat_api_key,
            chat_base_url=chat_base_url,
            chat_options=chat_options,
        )

        # Parse and resolve references
        resolver = RefResolver(characters, scenes)
        segments = raw.get("segments", [])
        return self._resolve_segments(segments, resolver, characters)

    async def _parse_storyboard_json(
        self,
        raw_output: str,
        *,
        chat_model: str = None,
        chat_api_key: str = None,
        chat_base_url: str = None,
        chat_options: dict | None = None,
    ) -> dict:
        try:
            return parse_json_from_llm(raw_output)
        except ValueError as exc:
            logger.warning(
                "VideoEngine: storyboard JSON parse failed; repairing once. error={} length={}",
                exc,
                len(raw_output),
            )

        repaired = await ai_hub.chat.complete(
            messages=build_storyboard_repair_prompt(raw_output),
            temperature=0.1,
            max_tokens=10000,
            response_format={"type": "json_object"},
            model=chat_model,
            api_key=chat_api_key,
            base_url=chat_base_url,
            **_extra_chat_kwargs(chat_options),
        )
        try:
            return parse_json_from_llm(repaired.content)
        except ValueError as exc:
            raise ValueError("Storyboard JSON validation failed after repair") from exc

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
        image_model: str = None,
        image_api_key: str = None,
        image_base_url: str = None,
        image_options: dict | None = None,
        tts_model: str = None,
        tts_api_key: str = None,
        tts_base_url: str = None,
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
        tasks.append(self._gen_image(
            image_prompt, str(image_path),
            model=image_model, api_key=image_api_key, base_url=image_base_url,
            image_options=image_options,
        ))

        # Audio generation task (if there's dialogue)
        audio_path = None
        if shot.dialogue:
            audio_path = storage.shot_audio_path(project_id, ep_num, shot.index)
            tasks.append(self._gen_audio(
                shot.dialogue, str(audio_path), shot.voice_style,
                model=tts_model, api_key=tts_api_key, base_url=tts_base_url,
            ))
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

    async def generate_shot_assets(
        self,
        shot: Shot,
        characters: list[Character],
        scenes: list[SceneLocation],
        project_id: int,
        ep_num: int,
        style: str = "realistic",
        image_model: str = None,
        image_api_key: str = None,
        image_base_url: str = None,
        image_options: dict | None = None,
        tts_model: str = None,
        tts_api_key: str = None,
        tts_base_url: str = None,
    ) -> Shot:
        """Generate image/audio assets and motion prompt for one shot."""
        await self._generate_shot_assets(
            shot,
            characters,
            scenes,
            project_id,
            ep_num,
            style,
            image_model=image_model,
            image_api_key=image_api_key,
            image_base_url=image_base_url,
            image_options=image_options,
            tts_model=tts_model,
            tts_api_key=tts_api_key,
            tts_base_url=tts_base_url,
        )

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
            char_dicts = [
                {"id": c.id, "name": c.name, "description": c.description or ""}
                for c in characters
            ]
            scene_dicts = [
                {"name": s.name, "description": s.description or ""}
                for s in scenes
            ]
            shot.video_prompt = await ai_hub.prompt.build_video_prompt(
                shot=shot_dict, characters=char_dicts, scenes=scene_dicts
            )

        return shot

    async def _gen_image(self, prompt: str, output_path: str,
                         model: str = None, api_key: str = None, base_url: str = None,
                         image_options: dict | None = None):
        """Generate an image."""
        return await ai_hub.image.generate(
            prompt=prompt, output_path=output_path,
            model=model, api_key=api_key, base_url=base_url,
            **(image_options or {}),
        )

    async def _gen_audio(self, text: str, output_path: str, voice_style: str = "",
                         model: str = None, api_key: str = None, base_url: str = None):
        """Generate TTS audio."""
        return await ai_hub.tts.speak(
            text=text, output_path=output_path,
            model=model, api_key=api_key, base_url=base_url,
        )

    async def generate_shot_video_only(
        self,
        shot: Shot,
        segment: Segment,
        characters: list[Character],
        scenes: list[SceneLocation],
        project_id: int,
        ep_num: int,
        video_model: str = None,
        video_api_key: str = None,
        video_base_url: str = None,
        video_options: dict | None = None,
        video_capabilities: dict | None = None,
    ) -> Shot:
        """Generate one shot video directly, then extract its first frame."""
        from app.services.ffmpeg import ffmpeg_service

        duration = shot.duration or 5.0
        shot_clip = storage.shot_video_path(project_id, ep_num, segment.index, shot.index)
        video_prompt = shot.video_prompt or shot.image_prompt or ""

        if not video_prompt:
            shot_dict = {
                "scene_ref": shot.scene_ref,
                "characters": shot.characters or [],
                "camera_type": shot.camera_type,
                "camera_angle": shot.camera_angle,
                "camera_movement": shot.camera_movement,
                "background": shot.background,
                "time_of_day": shot.time_of_day,
                "duration": duration,
                "dialogue": shot.dialogue,
            }
            char_dicts = [
                {"id": c.id, "name": c.name, "description": c.description or ""}
                for c in characters
            ]
            scene_dicts = [
                {"name": s.name, "description": s.description or ""}
                for s in scenes
            ]
            video_prompt = await ai_hub.prompt.build_video_prompt(
                shot=shot_dict,
                characters=char_dicts,
                scenes=scene_dicts,
            )
            shot.video_prompt = video_prompt

        reference_payload = reference_image_payload(
            shot.visual_references or [],
            video_capabilities,
        )
        if reference_payload:
            video_prompt = append_reference_instructions(
                video_prompt,
                shot.visual_references or [],
                video_capabilities,
            )
        elif shot.visual_references and not supports_visual_references(video_capabilities):
            logger.warning(
                f"VideoEngine: shot={shot.id} visual references ignored; "
                "selected video model does not support reference images"
            )

        await ai_hub.video.generate(
            prompt=video_prompt,
            output_path=str(shot_clip),
            model=video_model,
            api_key=video_api_key,
            base_url=video_base_url,
            seconds=str(duration),
            raw_params=(video_options or {}).get("raw_params") or {},
            **{
                k: v
                for k, v in (video_options or {}).items()
                if k != "raw_params"
            },
            **reference_payload,
        )

        shot.video_url = storage.get_url(shot_clip)
        shot.shot_status = "completed"

        frame_path = storage.shot_image_path(project_id, ep_num, shot.id)
        try:
            await ffmpeg_service.extract_first_frame(str(shot_clip), str(frame_path))
            shot.image_url = storage.get_url(frame_path)
        except Exception as e:
            logger.warning(f"VideoEngine: shot={shot.id} first frame extraction failed: {e}")

        return shot

    async def generate_segment_videos_only(
        self,
        segment: Segment,
        characters: list[Character],
        scenes: list[SceneLocation],
        project_id: int,
        ep_num: int,
        video_model: str = None,
        video_api_key: str = None,
        video_base_url: str = None,
        video_options: dict | None = None,
        video_capabilities: dict | None = None,
    ) -> Segment:
        """Generate videos for all shots in a segment without image/TTS generation."""
        segment.status = SegmentStatus.GENERATING
        sem = asyncio.Semaphore(4)

        async def _generate_one(shot: Shot) -> None:
            async with sem:
                try:
                    await self.generate_shot_video_only(
                        shot=shot,
                        segment=segment,
                        characters=characters,
                        scenes=scenes,
                        project_id=project_id,
                        ep_num=ep_num,
                        video_model=video_model,
                        video_api_key=video_api_key,
                        video_base_url=video_base_url,
                        video_options=video_options,
                        video_capabilities=video_capabilities,
                    )
                except Exception as e:
                    logger.error(f"VideoEngine: shot={shot.id} video generation failed: {e}")
                    shot.shot_status = "failed"
                    shot.error_message = str(e)[:500]

        await asyncio.gather(*[_generate_one(shot) for shot in segment.shots])
        return segment

    # ═══════════════════════════════════════════════════════════════
    # Spec 24: Video strategy decision
    # ═══════════════════════════════════════════════════════════════

    def _decide_video_strategy(self, segment: Segment) -> str:
        """
        (deprecated) Decide the video generation strategy for a segment.
        Kept for backward compatibility.  Prefer per-shot strategy via
        :meth:`_decide_shot_strategy`.
        """
        if not segment.shots:
            return "static_compose"
        has_motion = any(
            (s.camera_movement and s.camera_movement != "static")
            for s in segment.shots
        )
        if has_motion:
            return "ai_video"
        return "static_compose"

    def _decide_shot_strategy(self, shot: Shot) -> str:
        """
        Decide the video generation strategy for a single shot.

        Returns:
            "ai_video" — use AI video generation (Sora / Veo / etc.)
            "static_compose" — image + optional audio via FFmpeg
        """
        has_motion = shot.camera_movement and shot.camera_movement != "static"
        has_prompt = bool(shot.video_prompt or shot.image_prompt)
        if has_motion and has_prompt:
            return "ai_video"
        return "static_compose"

    async def _generate_shot_video(
        self,
        shot: Shot,
        segment: Segment,
        project_id: int,
        ep_num: int,
        video_model: str = None,
        video_api_key: str = None,
        video_base_url: str = None,
        video_options: dict | None = None,
        video_capabilities: dict | None = None,
        reuse_existing: bool = False,
    ) -> tuple[int, str | None, str, float]:
        """
        Generate or reuse one shot video.

        Returns (shot_index, clip_path_or_None, transition, duration).
        """
        from app.services.ffmpeg import ffmpeg_service

        duration = shot.duration or 5.0
        transition = shot.transition or "cut"
        shot_clip = storage.shot_video_path(project_id, ep_num, segment.index, shot.index)

        existing_clip = storage.storage_path_from_url(shot.video_url)
        if reuse_existing:
            if existing_clip and existing_clip.exists():
                return (shot.index, str(existing_clip), transition, duration)
            return (shot.index, None, transition, duration)

        strategy = self._decide_shot_strategy(shot)
        if strategy == "ai_video":
            video_prompt = shot.video_prompt or shot.image_prompt or ""
            reference_payload = reference_image_payload(
                shot.visual_references or [],
                video_capabilities,
            )
            if reference_payload:
                video_prompt = append_reference_instructions(
                    video_prompt,
                    shot.visual_references or [],
                    video_capabilities,
                )
            elif shot.visual_references and not supports_visual_references(video_capabilities):
                logger.warning(
                    f"VideoEngine: shot={shot.id} visual references ignored; "
                    "selected video model does not support reference images"
                )
            if video_prompt:
                logger.info(
                    f"VideoEngine: shot={shot.id} ai_video prompt_len={len(video_prompt)}"
                )
                try:
                    await ai_hub.video.generate(
                        prompt=video_prompt,
                        output_path=str(shot_clip),
                        model=video_model,
                        api_key=video_api_key,
                        base_url=video_base_url,
                        seconds=str(duration),
                        raw_params=(video_options or {}).get("raw_params") or {},
                        **{
                            k: v
                            for k, v in (video_options or {}).items()
                            if k != "raw_params"
                        },
                        **reference_payload,
                    )
                    shot.video_url = storage.get_url(shot_clip)
                    shot.shot_status = "completed"
                    return (shot.index, str(shot_clip), transition, duration)
                except Exception as e:
                    logger.error(f"VideoEngine: shot={shot.id} ai_video FAILED: {e}")
                    shot.shot_status = "failed"
                    shot.error_message = str(e)[:500]

        image_file = storage.storage_path_from_url(shot.image_url)
        if not image_file:
            logger.warning(f"VideoEngine: shot={shot.id} no image")
            shot.shot_status = "failed"
            shot.error_message = "No image asset for shot video generation"
            return (shot.index, None, transition, duration)

        audio_file = (
            storage.storage_path_from_url(shot.audio_url)
            if shot.audio_url
            else None
        )

        try:
            await ffmpeg_service.compose_static_video(
                image_path=str(image_file),
                audio_path=str(audio_file) if audio_file else None,
                duration=duration,
                output_path=str(shot_clip),
                camera_movement=shot.camera_movement or "static",
                time_of_day=shot.time_of_day or "day",
                subtitle_text=shot.dialogue or None,
            )
            shot.video_url = storage.get_url(shot_clip)
            shot.shot_status = "completed"
            return (shot.index, str(shot_clip), transition, duration)
        except Exception as e:
            logger.error(f"VideoEngine: shot={shot.id} static_compose FAILED: {e}")
            shot.shot_status = "failed"
            shot.error_message = str(e)[:500]
            return (shot.index, None, transition, duration)

    async def _generate_segment_video(
        self,
        segment: Segment,
        project_id: int,
        ep_num: int,
        video_model: str = None,
        video_api_key: str = None,
        video_base_url: str = None,
        video_options: dict | None = None,
        video_capabilities: dict | None = None,
        reuse_existing_shots: bool = False,
    ) -> str:
        """
        Compose a segment video from its shots.

        Per-shot strategy:
        - static_compose: image + audio → clip (Ken Burns + subtitle + colour)
        - ai_video:       AI video generation for motion shots

        All shot clips are composed in parallel, then concatenated with
        smooth transitions (xfade).  Failed shots produce a placeholder.
        """
        from app.services.ffmpeg import ffmpeg_service

        output_path = storage.segment_video_path(project_id, ep_num, segment.index)
        seg_dir = output_path.parent

        # ── 1. Compose each shot clip in parallel ──
        sem = asyncio.Semaphore(4)  # Limit concurrent FFmpeg processes

        async def _compose_one_shot(shot: Shot) -> tuple[int, str | None, str, float]:
            async with sem:
                return await self._generate_shot_video(
                    shot,
                    segment,
                    project_id,
                    ep_num,
                    video_model=video_model,
                    video_api_key=video_api_key,
                    video_base_url=video_base_url,
                    video_options=video_options,
                    video_capabilities=video_capabilities,
                    reuse_existing=reuse_existing_shots,
                )

        # Run all shots in parallel
        results = await asyncio.gather(
            *[_compose_one_shot(s) for s in segment.shots],
            return_exceptions=True,
        )

        # ── 2. Collect results; generate placeholders for failures ──
        clip_data: list[tuple[str, str, float]] = []
        failed_shots = 0

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"VideoEngine: shot composition exception: {result}")
                failed_shots += 1
                continue

            shot_idx, clip_path, transition, duration = result
            if clip_path:
                clip_data.append((clip_path, transition, duration))
            else:
                # Generate a placeholder clip for the failed shot
                placeholder = seg_dir / f"shot_{shot_idx:04d}_placeholder.mp4"
                try:
                    await self._create_placeholder_clip(
                        str(placeholder), duration, shot_idx
                    )
                    clip_data.append((str(placeholder), "cut", duration))
                except Exception as e:
                    logger.error(f"VideoEngine: placeholder clip failed: {e}")
                failed_shots += 1

        if not clip_data:
            raise ValueError(f"No clips generated for segment {segment.id}")

        # ── 3. Concatenate with transitions ──
        await ffmpeg_service.concat_with_transitions(
            clip_data, str(output_path), transition_duration=0.5
        )

        # ── 4. Optional: mix segment with BGM (ducking) ──
        bgm_dir = storage.project_path(project_id) / "bgm"
        bgm_path = None
        if bgm_dir.exists():
            for ext in ("mp3", "wav", "m4a", "aac", "ogg"):
                candidate = bgm_dir / f"background.{ext}"
                if candidate.exists():
                    bgm_path = str(candidate)
                    break

        if bgm_path:
            try:
                mixed_output = seg_dir / f"segment_{segment.index:04d}_mixed.mp4"
                # Extract audio from composed video, mix with BGM, mux back
                await ffmpeg_service.mix_audio_with_ducking(
                    main_audio_path=str(output_path),
                    bgm_path=bgm_path,
                    output_path=str(mixed_output),
                )
                # Replace with mixed version
                import shutil
                shutil.move(str(mixed_output), str(output_path))
                logger.info(
                    f"VideoEngine: segment={segment.id} BGM ducking applied"
                )
            except Exception as e:
                logger.warning(
                    f"VideoEngine: segment={segment.id} BGM ducking failed: {e}"
                )

        # ── 5. Finalise ──
        segment.video_url = storage.get_url(output_path)
        if failed_shots > 0:
            segment.status = SegmentStatus.PARTIAL
            logger.warning(
                f"VideoEngine: segment={segment.id} PARTIAL — "
                f"{failed_shots}/{len(segment.shots)} shots failed"
            )
        else:
            segment.status = SegmentStatus.COMPLETED

        return str(output_path)

    async def _create_placeholder_clip(
        self, output_path: str, duration: float, shot_index: int,
        width: int = 1080, height: int = 1920,
    ) -> str:
        """Create a placeholder video for a failed shot."""
        from app.services.ffmpeg import ffmpeg_service

        cmd = [
            ffmpeg_service.ffmpeg, "-y",
            "-f", "lavfi",
            "-i", f"color=c=black:s={width}x{height}:d={duration}:r=30",
            "-vf",
            (
                f"drawtext=text='Shot {shot_index}: Generation Failed'"
                f":fontcolor=red:fontsize=36"
                f":x=(w-tw)/2:y=(h-th)/2,"
                f"drawtext=text='(Placeholder)'"
                f":fontcolor=gray:fontsize=24"
                f":x=(w-tw)/2:y=(h-th)/2+40"
            ),
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "28",
            "-pix_fmt", "yuv420p",
            "-an",
            output_path,
        ]
        await ffmpeg_service._run(cmd)
        logger.info(f"VideoEngine: placeholder clip → {output_path}")
        return output_path

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
        chat_model: str = None,
        chat_api_key: str = None,
        chat_base_url: str = None,
        chat_options: dict | None = None,
        image_model: str = None,
        image_api_key: str = None,
        image_base_url: str = None,
        image_options: dict | None = None,
        tts_model: str = None,
        tts_api_key: str = None,
        tts_base_url: str = None,
        video_model: str = None,
        video_api_key: str = None,
        video_base_url: str = None,
        script: Script | None = None,
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
            episode, characters, scenes, shots_per_segment,
            chat_model=chat_model, chat_api_key=chat_api_key, chat_base_url=chat_base_url,
            chat_options=chat_options,
            script=script,
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
        image_model: str = None,
        image_api_key: str = None,
        image_base_url: str = None,
        image_options: dict | None = None,
        tts_model: str = None,
        tts_api_key: str = None,
        tts_base_url: str = None,
    ) -> Segment:
        """Generate all shot assets for a segment."""
        segment.status = SegmentStatus.GENERATING

        sem = asyncio.Semaphore(4)

        async def _generate_one(shot: Shot) -> None:
            async with sem:
                await self.generate_shot_assets(
                    shot, characters, scenes, project_id, ep_num, style,
                    image_model=image_model, image_api_key=image_api_key, image_base_url=image_base_url,
                    image_options=image_options,
                    tts_model=tts_model, tts_api_key=tts_api_key, tts_base_url=tts_base_url,
                )

        results = await asyncio.gather(
            *[_generate_one(shot) for shot in segment.shots],
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Shot asset generation failed: {result}")

        for shot in segment.shots:
            try:
                if not shot.image_url:
                    shot.shot_status = "failed"
            except Exception as e:
                logger.error(f"Shot asset status update failed: {e}")

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
        quality: str = "high",
        resolution: Optional[str] = None,
        subtitle_text: Optional[str] = None,
        subtitle_font_size: int = 24,
        subtitle_position: str = "bottom",
        bgm_volume: float = 0.15,
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
            bgm_volume=bgm_volume,
            quality=quality,
            resolution=resolution,
            subtitle_text=subtitle_text,
            subtitle_font_size=subtitle_font_size,
            subtitle_position=subtitle_position,
        )

        return storage.get_url(output_path)


# Module-level singleton
video_engine = VideoEngine()


def _extra_chat_kwargs(options: dict | None) -> dict:
    blocked = {"model", "messages", "temperature", "max_tokens", "response_format", "stream"}
    return {k: v for k, v in (options or {}).items() if k not in blocked}
