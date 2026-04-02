"""
DramaForge v2.0 — Script Engine
=================================
Core logic for generating, parsing, and managing drama scripts.
Handles both AI-generated and uploaded (docx) scripts.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

from loguru import logger

from app.ai_hub import ai_hub
from app.models.project import Project
from app.models.script import Script
from app.models.episode import Episode
from app.models.character import Character, CharacterRole
from app.models.scene import SceneLocation
from app.prompts.script_prompts import (
    NARRATION_REWRITE_PROMPT,
    SCRIPT_STRUCTURED_SYSTEM,
    build_structured_prompt,
)


class ScriptEngine:
    """Engine for creating and manipulating scripts."""

    # ── Public API ────────────────────────────────────────────────

    async def create_from_text(
        self,
        user_input: str,
        project: Project,
        *,
        genre: str = None,
        total_episodes: int = 1,
        duration: int = 60,
    ) -> dict:
        """
        AI-generate a structured script from user's creative input.

        Returns:
            dict with keys: script, episodes, characters, scenes
        """
        genre = genre or project.genre.value if project.genre else "其他"
        style = project.style.value if project.style else "写实"

        messages = build_structured_prompt(
            user_input=user_input,
            genre=genre,
            total_episodes=total_episodes,
            duration=duration,
            style=style,
        )

        logger.info(f"ScriptEngine: generating script for project={project.id}")

        raw_json = await ai_hub.chat.complete_json(
            messages=messages,
            temperature=0.7,
            max_tokens=8192,
        )

        return self._parse_script(raw_json, project.id)

    async def create_from_docx(
        self,
        file_path: str | Path,
        project: Project,
        total_episodes: int = 1,
    ) -> dict:
        """
        Parse an uploaded .docx file into structured script data.

        Returns:
            dict with keys: script, episodes, characters, scenes
        """
        try:
            from docx import Document
        except ImportError:
            raise ImportError("python-docx is required for docx parsing")

        doc = Document(str(file_path))
        full_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())

        logger.info(f"ScriptEngine: parsing docx ({len(full_text)} chars)")

        # Extract character names and scenes from the raw text
        character_names = self._extract_characters(full_text)
        scene_names = self._extract_scenes(full_text)

        # Split into episodes (heuristic: by "第X集" or equal split)
        episode_contents = self._split_episodes(full_text, total_episodes)

        # Build result
        script_data = {
            "protagonist": character_names[0] if character_names else "",
            "genre": project.genre.value if project.genre else "",
            "synopsis": full_text[:200] + "..." if len(full_text) > 200 else full_text,
            "background": "",
            "setting": "",
            "one_liner": "",
            "raw_content": full_text,
        }

        episodes_data = [
            {"number": i + 1, "title": f"第{i + 1}集", "content": content}
            for i, content in enumerate(episode_contents)
        ]

        characters_data = [
            {"name": name, "role": "protagonist" if i == 0 else "supporting", "description": ""}
            for i, name in enumerate(character_names)
        ]

        scenes_data = [
            {"name": name, "description": "", "time_of_day": "day", "interior": True}
            for name in scene_names
        ]

        return {
            "script": script_data,
            "episodes": episodes_data,
            "characters": characters_data,
            "scenes": scenes_data,
        }

    async def rewrite_to_narration(self, script_content: str) -> str:
        """
        Rewrite a dialogue-style script into narration style.

        Returns:
            Narration-style script text.
        """
        prompt = NARRATION_REWRITE_PROMPT.format(script_content=script_content)

        logger.info("ScriptEngine: rewriting to narration style")

        result = await ai_hub.chat.ask(
            prompt,
            system=SCRIPT_STRUCTURED_SYSTEM.replace("JSON", "纯文本"),
            temperature=0.5,
            max_tokens=4096,
        )
        return result

    # ── Internal Helpers ──────────────────────────────────────────

    def _parse_script(self, raw_json: dict, project_id: int) -> dict:
        """
        Parse LLM JSON output into structured data suitable for DB insertion.
        """
        script_data = {
            "protagonist": raw_json.get("protagonist", ""),
            "genre": raw_json.get("genre", ""),
            "synopsis": raw_json.get("synopsis", ""),
            "background": raw_json.get("background", ""),
            "setting": raw_json.get("setting", ""),
            "one_liner": raw_json.get("one_liner", ""),
            "raw_content": json.dumps(raw_json, ensure_ascii=False),
        }

        episodes_data = []
        for ep in raw_json.get("episodes", []):
            episodes_data.append({
                "number": ep.get("number", len(episodes_data) + 1),
                "title": ep.get("title", f"第{len(episodes_data) + 1}集"),
                "content": ep.get("content", ""),
            })

        characters_data = []
        for ch in raw_json.get("characters", []):
            characters_data.append({
                "name": ch.get("name", ""),
                "role": ch.get("role", "supporting"),
                "description": ch.get("description", ""),
            })

        scenes_data = []
        for sc in raw_json.get("scenes", []):
            scenes_data.append({
                "name": sc.get("name", ""),
                "description": sc.get("description", ""),
                "time_of_day": sc.get("time_of_day", "day"),
                "interior": sc.get("interior", True),
            })

        return {
            "script": script_data,
            "episodes": episodes_data,
            "characters": characters_data,
            "scenes": scenes_data,
        }

    def _extract_characters(self, text: str) -> list[str]:
        """Extract character names from raw script text using heuristics."""
        # Pattern: "角色名：" or "【角色名】"
        patterns = [
            r'^([^\s:：]{1,10})[：:](?!\s*$)',   # 角色名：对白
            r'【([^】]{1,10})】',                   # 【角色名】
        ]
        names = set()
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            for m in matches:
                name = m.strip()
                # Filter out common non-character words
                if name and name not in ("旁白", "场景", "标题", "提示", "备注", "注"):
                    names.add(name)
        return list(names)[:10]  # Cap at 10 characters

    def _extract_scenes(self, text: str) -> list[str]:
        """Extract scene names from raw script text using heuristics."""
        # Pattern: "场景1：XXX" or "**场景：XXX**"
        patterns = [
            r'场景\d*[：:]\s*(.+?)(?:\n|$)',
            r'\*\*场景\d*[：:]\s*(.+?)\*\*',
        ]
        scenes = set()
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for m in matches:
                name = m.strip().rstrip("*")
                if name:
                    scenes.add(name)
        return list(scenes)[:10]

    def _split_episodes(self, text: str, total_episodes: int) -> list[str]:
        """Split text into episodes by markers or equal length."""
        # Try splitting by "第X集"
        parts = re.split(r'第\s*\d+\s*集', text)
        parts = [p.strip() for p in parts if p.strip()]

        if len(parts) >= total_episodes:
            return parts[:total_episodes]

        # Fall back to equal-length split
        if total_episodes == 1:
            return [text]

        chunk_size = len(text) // total_episodes
        episodes = []
        for i in range(total_episodes):
            start = i * chunk_size
            end = start + chunk_size if i < total_episodes - 1 else len(text)
            episodes.append(text[start:end])
        return episodes


# Module-level singleton
script_engine = ScriptEngine()
