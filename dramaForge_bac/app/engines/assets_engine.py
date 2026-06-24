"""
DramaForge v2.0 — Assets Engine
=================================
Generates character images and scene images from script data.
Uses AI Hub for description generation and image generation.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from loguru import logger

from app.ai_hub import ai_hub
from app.models.character import Character
from app.models.scene import SceneLocation
from app.models.script import Script
from app.prompts.character_prompts import (
    build_character_desc_prompt,
    build_scene_desc_prompt,
    build_image_prompt_optimize,
)
from app.services.storage import storage


class ImageGenerationError(Exception):
    """Raised when all image generation variants fail."""


class AssetsEngine:
    """Engine for generating character and scene visual assets."""

    async def generate_all_assets(
        self,
        script: Script,
        characters: list[Character],
        scenes: list[SceneLocation],
        project_id: int,
        chat_model: str = None,
        chat_api_key: str = None,
        chat_base_url: str = None,
        chat_options: dict | None = None,
        image_model: str = None,
        image_api_key: str = None,
        image_base_url: str = None,
        image_options: dict | None = None,
    ) -> tuple[list[Character], list[SceneLocation]]:
        """
        Generate descriptions and images for all characters and scenes in parallel.

        Returns:
            Tuple of (updated characters, updated scenes)
        """
        logger.info(
            f"AssetsEngine: generating {len(characters)} characters + "
            f"{len(scenes)} scenes for project={project_id}"
        )

        synopsis = script.synopsis or ""

        # Generate descriptions & images concurrently
        char_tasks = [
            self._generate_character(
                ch, synopsis, project_id,
                chat_model=chat_model, chat_api_key=chat_api_key, chat_base_url=chat_base_url,
                chat_options=chat_options,
                image_model=image_model, image_api_key=image_api_key, image_base_url=image_base_url,
                image_options=image_options,
            )
            for ch in characters
        ]
        scene_tasks = [
            self._generate_scene(
                sc, script, project_id,
                chat_model=chat_model, chat_api_key=chat_api_key, chat_base_url=chat_base_url,
                chat_options=chat_options,
                image_model=image_model, image_api_key=image_api_key, image_base_url=image_base_url,
                image_options=image_options,
            )
            for sc in scenes
        ]

        # Gather all results — errors don't stop the batch
        char_results = await asyncio.gather(*char_tasks, return_exceptions=True)
        scene_results = await asyncio.gather(*scene_tasks, return_exceptions=True)

        # Process results
        updated_chars = []
        for ch, result in zip(characters, char_results):
            if isinstance(result, Exception):
                logger.error(f"Failed to generate character '{ch.name}': {result}")
                updated_chars.append(ch)
            else:
                updated_chars.append(result)

        updated_scenes = []
        for sc, result in zip(scenes, scene_results):
            if isinstance(result, Exception):
                logger.error(f"Failed to generate scene '{sc.name}': {result}")
                updated_scenes.append(sc)
            else:
                updated_scenes.append(result)

        return updated_chars, updated_scenes

    async def _generate_character(
        self,
        character: Character,
        synopsis: str,
        project_id: int,
        chat_model: str = None,
        chat_api_key: str = None,
        chat_base_url: str = None,
        chat_options: dict | None = None,
        image_model: str = None,
        image_api_key: str = None,
        image_base_url: str = None,
        image_options: dict | None = None,
    ) -> Character:
        """Generate description and image for a single character."""
        logger.info(f"AssetsEngine: generating character '{character.name}'")

        # Step 1: Generate description via LLM
        messages = build_character_desc_prompt(
            character_name=character.name,
            character_role=character.role.value if character.role else "supporting",
            script_synopsis=synopsis,
        )

        desc_data = await ai_hub.chat.complete_json(
            messages=messages,
            temperature=0.5,
            model=chat_model,
            api_key=chat_api_key,
            base_url=chat_base_url,
            **_extra_chat_kwargs(chat_options),
        )

        # Update character fields
        character.description = desc_data.get("role_description", character.description)
        character.voice_desc = desc_data.get("voice", character.voice_desc)

        # Step 2: Generate character image
        image_prompt = desc_data.get("image_prompt", "")
        if image_prompt:
            image_path = storage.character_image_path(project_id, character.id, 0)
            result = await ai_hub.image.generate(
                prompt=image_prompt,
                output_path=str(image_path),
                model=image_model,
                api_key=image_api_key,
                base_url=image_base_url,
                **(image_options or {}),
            )
            character.reference_images = [storage.get_url(image_path)]

        return character

    async def _generate_scene(
        self,
        scene: SceneLocation,
        script: Script,
        project_id: int,
        chat_model: str = None,
        chat_api_key: str = None,
        chat_base_url: str = None,
        chat_options: dict | None = None,
        image_model: str = None,
        image_api_key: str = None,
        image_base_url: str = None,
        image_options: dict | None = None,
    ) -> SceneLocation:
        """Generate description and image for a single scene."""
        logger.info(f"AssetsEngine: generating scene '{scene.name}'")

        # Step 1: Generate description via LLM
        messages = build_scene_desc_prompt(
            scene_name=scene.name,
            story_background=script.background or "",
            story_setting=script.setting or "",
            time_of_day=scene.time_of_day or "day",
            interior=scene.interior,
        )

        desc_data = await ai_hub.chat.complete_json(
            messages=messages,
            temperature=0.5,
            model=chat_model,
            api_key=chat_api_key,
            base_url=chat_base_url,
            **_extra_chat_kwargs(chat_options),
        )

        # Update scene description
        scene.description = desc_data.get("description", scene.description)

        # Step 2: Generate scene image(s)
        image_prompts = desc_data.get("image_prompts", [])
        urls = []
        for idx, prompt in enumerate(image_prompts[:2]):  # Max 2 images
            image_path = storage.scene_image_path(project_id, scene.id, idx)
            try:
                await ai_hub.image.generate(
                    prompt=prompt,
                    output_path=str(image_path),
                    model=image_model,
                    api_key=image_api_key,
                    base_url=image_base_url,
                    **(image_options or {}),
                )
                urls.append(storage.get_url(image_path))
            except Exception as e:
                logger.warning(f"Scene image {idx} failed: {e}")

        if urls:
            scene.reference_images = urls

        return scene

    async def regenerate_character_image(
        self,
        character: Character,
        project_id: int,
        prompt: Optional[str] = None,
        variant_count: int = 1,
        *,
        image_model: str = None,
        image_api_key: str = None,
        image_base_url: str = None,
        image_options: dict | None = None,
        # ── Enhanced context for prompt optimization ──
        visual_description: str = "",
        drama_style: str = "realistic",
        aspect_ratio: str = "9:16",
        optimize_prompt: bool = False,
        chat_model: str = None,
        chat_api_key: str = None,
        chat_base_url: str = None,
        chat_options: dict | None = None,
    ) -> list[str]:
        """Regenerate a character's image with optional AI prompt optimization.

        When optimize_prompt=True, uses a chat LLM to refine the image prompt
        by combining character description + visual description + drama style
        into a high-quality English image prompt.

        Returns:
            List of generated image URLs.

        Raises:
            ImageGenerationError: if ALL variants fail.
        """
        # ── Step 0: Optimize prompt via chat LLM if requested ──
        if optimize_prompt and chat_model:
            logger.info(
                f"AssetsEngine: optimizing prompt for character '{character.name}' "
                f"visual='{visual_description[:50] if visual_description else 'default'}'"
            )
            optimize_messages = build_image_prompt_optimize(
                character_name=character.name,
                character_role=character.role.value if character.role else "supporting",
                character_description=character.description or "",
                visual_name=visual_description[:30] if visual_description else "标准形象",
                visual_description=visual_description or prompt or "",
                drama_style=drama_style,
                aspect_ratio=aspect_ratio,
                extra_guidance=prompt or "",
            )
            try:
                optimized = await ai_hub.chat.complete(
                    messages=optimize_messages,
                    temperature=0.6,
                    max_tokens=400,
                    model=chat_model,
                    api_key=chat_api_key,
                    base_url=chat_base_url,
                    **_extra_chat_kwargs(chat_options),
                )
                prompt = optimized.strip()
                logger.info(f"AssetsEngine: optimized prompt ({len(prompt)} chars)")
            except Exception as e:
                logger.warning(f"AssetsEngine: prompt optimization failed, using raw prompt: {e}")

        # ── Build default prompt if still empty ──
        if not prompt:
            parts = [f"Portrait of {character.name}"]
            if character.description:
                parts.append(character.description)
            if visual_description:
                parts.append(f"Visual style: {visual_description}")
            parts.append("High quality, detailed, digital art.")
            prompt = ". ".join(parts)

        urls = []
        errors: list[str] = []
        for i in range(variant_count):
            # Slightly vary each prompt
            varied_prompt = prompt
            if variant_count > 1:
                variants = [
                    f"{prompt} — variant A: soft lighting, warm tones.",
                    f"{prompt} — variant B: dramatic lighting, rich contrast.",
                    f"{prompt} — variant C: natural lighting, muted colors.",
                    f"{prompt} — variant D: cinematic lighting, cool tones.",
                ]
                varied_prompt = variants[i % len(variants)]

            image_path = storage.character_image_path(project_id, character.id, i)
            try:
                await ai_hub.image.generate(
                    prompt=varied_prompt, output_path=str(image_path),
                    model=image_model, api_key=image_api_key, base_url=image_base_url,
                    **(image_options or {}),
                )
                urls.append(storage.get_url(image_path))
            except Exception as e:
                err_msg = f"Variant {i}: {e}"
                logger.warning(f"Character image {err_msg}")
                errors.append(err_msg)

        if urls:
            character.reference_images = urls
            if errors:
                logger.warning(
                    f"Character '{character.name}' (id={character.id}): "
                    f"{len(urls)}/{variant_count} variants succeeded, {len(errors)} failed"
                )
        else:
            detail = "; ".join(errors) if errors else "unknown error"
            raise ImageGenerationError(
                f"Character '{character.name}' (id={character.id}): "
                f"all {variant_count} variant(s) failed — {detail}"
            )

        return urls

    async def regenerate_scene_image(
        self,
        scene: SceneLocation,
        project_id: int,
        prompt: Optional[str] = None,
        variant_count: int = 1,
        *,
        image_model: str = None,
        image_api_key: str = None,
        image_base_url: str = None,
        image_options: dict | None = None,
    ) -> list[str]:
        """Regenerate a scene's image with optional variants.

        Returns:
            List of generated image URLs.

        Raises:
            ImageGenerationError: if ALL variants fail.
        """
        if not prompt:
            prompt = (
                f"Scene: {scene.name}. {scene.description or 'A dramatic scene'}. "
                f"Cinematic, atmospheric, detailed environment."
            )

        urls = []
        errors: list[str] = []
        for i in range(variant_count):
            varied_prompt = prompt
            if variant_count > 1:
                variants = [
                    f"{prompt} — variant A: golden hour, warm atmosphere.",
                    f"{prompt} — variant B: overcast, moody atmosphere.",
                    f"{prompt} — variant C: bright daylight, crisp details.",
                    f"{prompt} — variant D: night scene, atmospheric lighting.",
                ]
                varied_prompt = variants[i % len(variants)]

            image_path = storage.scene_image_path(project_id, scene.id, i)
            try:
                await ai_hub.image.generate(
                    prompt=varied_prompt, output_path=str(image_path),
                    model=image_model, api_key=image_api_key, base_url=image_base_url,
                    **(image_options or {}),
                )
                urls.append(storage.get_url(image_path))
            except Exception as e:
                err_msg = f"Variant {i}: {e}"
                logger.warning(f"Scene image {err_msg}")
                errors.append(err_msg)

        if urls:
            scene.reference_images = urls
            if errors:
                logger.warning(
                    f"Scene '{scene.name}' (id={scene.id}): "
                    f"{len(urls)}/{variant_count} variants succeeded, {len(errors)} failed"
                )
        else:
            detail = "; ".join(errors) if errors else "unknown error"
            raise ImageGenerationError(
                f"Scene '{scene.name}' (id={scene.id}): "
                f"all {variant_count} variant(s) failed — {detail}"
            )

        return urls


# Module-level singleton
assets_engine = AssetsEngine()


def _extra_chat_kwargs(options: dict | None) -> dict:
    blocked = {"model", "messages", "temperature", "max_tokens", "response_format", "stream"}
    return {k: v for k, v in (options or {}).items() if k not in blocked}
