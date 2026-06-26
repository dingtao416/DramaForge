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
from typing import Any, AsyncIterator, Optional

from loguru import logger

from app.ai_hub import ai_hub
from app.ai_hub.chat import _parse_json as parse_json_from_llm  # robust LLM JSON parser
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
        chat_model: str = None,
        chat_api_key: str = None,
        chat_base_url: str = None,
        chat_options: dict[str, Any] | None = None,
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

        # Dynamic max_tokens: base 6000 + 2500 per episode (Chinese ~1.5 tokens/char)
        max_tokens = 6000 + total_episodes * 2500

        # Use complete + manual JSON parse instead of complete_json
        # to avoid response_format constraint that some API endpoints don't support
        resp = await ai_hub.chat.complete(
            messages=messages,
            temperature=0.7,
            max_tokens=max_tokens,
            model=chat_model,
            api_key=chat_api_key,
            base_url=chat_base_url,
            **_extra_chat_kwargs(chat_options),
        )

        raw_json = self._parse_json_from_text(resp.content)
        return self._parse_script(raw_json, project.id)

    async def create_from_text_stream(
        self,
        user_input: str,
        project: Project,
        *,
        genre: str = None,
        total_episodes: int = 1,
        duration: int = 60,
        chat_model: str = None,
        chat_api_key: str = None,
        chat_base_url: str = None,
        chat_options: dict[str, Any] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        AI-generate a structured script with streaming progress.

        Yields:
            {"type": "content", "data": "chunk..."}
            {"type": "done", "data": {script, episodes, characters, scenes}}
            {"type": "error", "data": "error message"}
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

        max_tokens = 6000 + total_episodes * 2500

        logger.info(f"ScriptEngine: generating script (stream) for project={project.id}")

        try:
            full_content = ""
            async for chunk in ai_hub.chat.stream(
                messages=messages,
                temperature=0.7,
                max_tokens=max_tokens,
                model=chat_model,
                api_key=chat_api_key,
                base_url=chat_base_url,
                **_extra_chat_kwargs(chat_options),
            ):
                full_content += chunk
                yield {"type": "content", "data": chunk}

            raw_json = self._parse_json_from_text(full_content)
            result = self._parse_script(raw_json, project.id)
            yield {"type": "done", "data": result}

        except Exception as exc:
            logger.error(f"ScriptEngine stream error: {exc}")
            yield {"type": "error", "data": str(exc)}

    async def parse_uploaded_file(self, file_path: str | Path) -> str:
        """
        Extract plain text from an uploaded file (.docx / .doc / .txt).

        Returns:
            Full text content of the file.
        """
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext == ".txt":
            return path.read_text(encoding="utf-8")

        if ext in (".docx", ".doc"):
            try:
                from docx import Document
            except ImportError:
                raise ImportError("python-docx is required for document parsing")

            try:
                doc = Document(str(path))
                full_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
                if not full_text:
                    raise ValueError("No text extracted from document")
                return full_text
            except Exception:
                # Fallback for .doc or unparseable files: try basic text extraction
                try:
                    raw = path.read_bytes()
                    # Filter printable ASCII and common CJK from binary
                    text = raw.decode("utf-8", errors="ignore")
                    # Remove excessive non-text characters
                    import re
                    text = re.sub(r'[^一-鿿　-〿＀-￯a-zA-Z0-9\s\n\r,.;:!?、。；：！？…—""''（）【】《》\-\+]', '', text)
                    text = re.sub(r'\n{3,}', '\n\n', text)
                    text = re.sub(r' {3,}', '  ', text)
                    if len(text.strip()) > 100:
                        return text.strip()
                except Exception:
                    pass
                raise ValueError("无法解析该文件，请转换为 .docx 或 .txt 格式后重试")

        raise ValueError(f"不支持的文件格式: {ext}")

    async def create_from_docx(
        self,
        file_path: str | Path,
        project: Project,
        total_episodes: int = 1,
    ) -> dict:
        """
        Parse an uploaded file (.docx/.doc/.txt) into structured script data.

        Returns:
            dict with keys: script, episodes, characters, scenes
        """
        full_text = await self.parse_uploaded_file(file_path)

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

    async def rewrite_to_narration_stream(
        self, script_content: str,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Rewrite a dialogue-style script into narration style with streaming.

        Yields:
            {"type": "content", "data": "chunk..."}
            {"type": "done", "data": "full narration text"}
            {"type": "error", "data": "error message"}
        """
        prompt = NARRATION_REWRITE_PROMPT.format(script_content=script_content)

        logger.info("ScriptEngine: rewriting to narration style (stream)")

        messages = [
            {"role": "system", "content": SCRIPT_STRUCTURED_SYSTEM.replace("JSON", "纯文本")},
            {"role": "user", "content": prompt},
        ]

        try:
            full_content = ""
            async for chunk in ai_hub.chat.stream(
                messages=messages,
                temperature=0.5,
                max_tokens=4096,
            ):
                full_content += chunk
                yield {"type": "content", "data": chunk}

            yield {"type": "done", "data": full_content}

        except Exception as exc:
            logger.error(f"ScriptEngine rewrite stream error: {exc}")
            yield {"type": "error", "data": str(exc)}

    # ── Internal Helpers ──────────────────────────────────────────

    @staticmethod
    def _parse_json_from_text(text: str) -> dict:
        """Extract and parse JSON from LLM output, using the robust shared parser."""
        return parse_json_from_llm(text)

    def _parse_script(self, raw_json: dict, project_id: int) -> dict:
        """
        Parse LLM JSON output into structured data suitable for DB insertion.
        """
        script_summary = raw_json.get("script_summary") or {}
        script_data = {
            "protagonist": raw_json.get("protagonist", ""),
            "genre": raw_json.get("genre", ""),
            "synopsis": raw_json.get("synopsis") or script_summary.get("story_overview", ""),
            "background": raw_json.get("background", ""),
            "setting": raw_json.get("setting") or script_summary.get("core_hook", ""),
            "one_liner": raw_json.get("one_liner") or script_summary.get("one_sentence_story", ""),
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


def _extra_chat_kwargs(options: dict[str, Any] | None) -> dict[str, Any]:
    blocked = {"model", "messages", "temperature", "max_tokens", "response_format", "stream"}
    return {k: v for k, v in (options or {}).items() if k not in blocked}
