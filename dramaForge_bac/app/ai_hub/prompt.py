"""
DramaForge v2.0 — AI Hub Prompt Service
=========================================
Builds and optimizes prompts for image/video generation from shot data.
"""

from __future__ import annotations

from typing import Optional

from loguru import logger

from app.ai_hub._client import BaseClient
from app.ai_hub.chat import ChatService


class PromptService:
    """Prompt optimization and construction for visual asset generation."""

    def __init__(self):
        self._chat: ChatService | None = None

    @property
    def chat(self) -> ChatService:
        if self._chat is None:
            self._chat = ChatService()
        return self._chat

    async def optimize(self, raw_prompt: str, context: str = "") -> str:
        """
        Optimize a raw prompt for better AI image/video generation results.

        Args:
            raw_prompt: The original prompt text.
            context: Additional context (style, scene info, etc.).

        Returns:
            Optimized English prompt string.
        """
        system = (
            "You are a prompt engineering expert. Optimize the given prompt for "
            "AI image/video generation. Output ONLY the optimized English prompt, "
            "no explanations. The prompt should be detailed, vivid, and include "
            "artistic direction (lighting, composition, style)."
        )
        user = f"Optimize this prompt:\n\n{raw_prompt}"
        if context:
            user += f"\n\nContext: {context}"

        result = await self.chat.ask(user, system=system, temperature=0.3)
        logger.info(f"PromptService: optimized prompt ({len(raw_prompt)} → {len(result)} chars)")
        return result.strip()

    async def build_image_prompt(
        self,
        shot: dict,
        characters: list[dict],
        scenes: list[dict],
        style: str = "realistic",
    ) -> str:
        """
        Build a complete image generation prompt from shot data.

        Args:
            shot: Shot data dict with scene_ref, characters, background, etc.
            characters: List of character dicts with name, description, reference_images.
            scenes: List of scene dicts with name, description.
            style: Visual style (realistic, anime, etc.).

        Returns:
            Complete English prompt for image generation.
        """
        parts = []

        # Style prefix
        style_map = {
            "realistic": "Photorealistic, cinematic",
            "anime": "Anime style, Studio Ghibli inspired",
            "cartoon": "3D cartoon style, Pixar-like",
            "cinematic": "Cinematic, film still, dramatic lighting",
            "watercolor": "Watercolor painting style, artistic",
            "ink_wash": "Chinese ink wash painting style, traditional",
        }
        parts.append(style_map.get(style, "High quality"))

        # Scene
        scene_ref = shot.get("scene_ref", "")
        for sc in scenes:
            if sc.get("name") == scene_ref:
                parts.append(f"Setting: {sc.get('description', scene_ref)}")
                break
        else:
            if scene_ref:
                parts.append(f"Setting: {scene_ref}")

        # Characters
        shot_chars = shot.get("characters", [])
        for sc in shot_chars:
            char_id = sc.get("char_id")
            action = sc.get("action", "")
            for ch in characters:
                if ch.get("id") == char_id:
                    desc = ch.get("description", ch.get("name", ""))
                    parts.append(f"Character: {desc}")
                    if action:
                        parts.append(f"Action: {action}")
                    break

        # Camera
        camera = shot.get("camera_type", "medium")
        angle = shot.get("camera_angle", "eye_level")
        parts.append(f"Camera: {camera} shot, {angle} angle")

        # Background/atmosphere
        bg = shot.get("background", "")
        if bg:
            parts.append(f"Atmosphere: {bg}")

        # Time of day
        tod = shot.get("time_of_day", "day")
        parts.append(f"Time: {tod}")

        prompt = ". ".join(parts) + "."
        return prompt

    async def build_video_prompt(
        self,
        shot: dict,
        characters: list[dict],
        scenes: list[dict],
    ) -> str:
        """
        Build a video generation prompt from shot data.
        Focuses on motion and camera movement descriptions.

        Returns:
            Complete English prompt for video generation.
        """
        parts = []

        # Base image description
        image_prompt = await self.build_image_prompt(shot, characters, scenes)
        parts.append(image_prompt)

        # Camera movement
        movement = shot.get("camera_movement", "static")
        if movement != "static":
            movement_desc = {
                "pan": "Camera slowly pans across the scene",
                "tilt": "Camera tilts up/down revealing the scene",
                "zoom_in": "Camera smoothly zooms in",
                "zoom_out": "Camera pulls back zooming out",
                "dolly": "Camera moves alongside the subject",
                "tracking": "Camera tracks following the subject's movement",
                "handheld": "Slight handheld camera shake for realism",
            }
            parts.append(movement_desc.get(movement, f"Camera: {movement}"))

        # Duration hint
        duration = shot.get("duration", 5)
        parts.append(f"Duration: {duration} seconds of smooth motion")

        return " | ".join(parts)
