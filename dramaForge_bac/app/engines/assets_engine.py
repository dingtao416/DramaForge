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
)
from app.services.storage import storage


class AssetsEngine:
    """Engine for generating character and scene visual assets."""

    async def generate_all_assets(
        self,
        script: Script,
        characters: list[Character],
        scenes: list[SceneLocation],
        project_id: int,
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
            self._generate_character(ch, synopsis, project_id)
            for ch in characters
        ]
        scene_tasks = [
            self._generate_scene(sc, script, project_id)
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
            )
            character.reference_images = [storage.get_url(image_path)]

        return character

    async def _generate_scene(
        self,
        scene: SceneLocation,
        script: Script,
        project_id: int,
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
    ) -> str:
        """Regenerate a character's image with an optional custom prompt."""
        if not prompt:
            prompt = (
                f"Portrait of {character.name}: {character.description or 'a character'}. "
                f"High quality, detailed, digital art."
            )

        image_path = storage.character_image_path(project_id, character.id, 0)
        await ai_hub.image.generate(prompt=prompt, output_path=str(image_path))
        url = storage.get_url(image_path)
        character.reference_images = [url]
        return url

    async def regenerate_scene_image(
        self,
        scene: SceneLocation,
        project_id: int,
        prompt: Optional[str] = None,
    ) -> str:
        """Regenerate a scene's image with an optional custom prompt."""
        if not prompt:
            prompt = (
                f"Scene: {scene.name}. {scene.description or 'A dramatic scene'}. "
                f"Cinematic, atmospheric, detailed environment."
            )

        image_path = storage.scene_image_path(project_id, scene.id, 0)
        await ai_hub.image.generate(prompt=prompt, output_path=str(image_path))
        url = storage.get_url(image_path)
        scene.reference_images = [url]
        return url


# Module-level singleton
assets_engine = AssetsEngine()
