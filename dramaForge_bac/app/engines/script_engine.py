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
    build_repair_prompt,
    build_structured_prompt,
    build_upload_analysis_prompt,
)


UPLOAD_EXTRACTION_WARNING = "角色/场景未能自动解析，可手动补充或重新解析"


class ScriptValidationError(ValueError):
    def __init__(self, issues: list[str]):
        self.issues = issues
        super().__init__("Script validation failed: " + "; ".join(issues))


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
        return await self._parse_generated_script(
            raw_json=raw_json,
            project_id=project.id,
            expected_episodes=total_episodes,
            chat_model=chat_model,
            chat_api_key=chat_api_key,
            chat_base_url=chat_base_url,
            chat_options=chat_options,
        )

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
            result = await self._parse_generated_script(
                raw_json=raw_json,
                project_id=project.id,
                expected_episodes=total_episodes,
                chat_model=chat_model,
                chat_api_key=chat_api_key,
                chat_base_url=chat_base_url,
                chat_options=chat_options,
            )
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
        *,
        chat_model: str = None,
        chat_api_key: str = None,
        chat_base_url: str = None,
        chat_options: dict[str, Any] | None = None,
    ) -> dict:
        """
        Parse an uploaded file (.docx/.doc/.txt) into structured script data.

        Returns:
            dict with keys: script, episodes, characters, scenes
        """
        full_text = await self.parse_uploaded_file(file_path)

        logger.info(f"ScriptEngine: parsing docx ({len(full_text)} chars)")

        episode_contents = self._split_episodes(full_text, total_episodes)
        warnings: list[str] = []
        rule_analysis = self._build_rule_upload_analysis(
            full_text=full_text,
            episode_contents=episode_contents,
        )
        has_rule_assets = bool(rule_analysis.get("characters")) and bool(rule_analysis.get("scenes"))
        if not has_rule_assets:
            warnings.append(UPLOAD_EXTRACTION_WARNING)

        try:
            analysis = await self._analyze_uploaded_script(
                full_text=full_text,
                total_episodes=total_episodes,
                chat_model=chat_model,
                chat_api_key=chat_api_key,
                chat_base_url=chat_base_url,
                chat_options=chat_options,
            )
            raw_json = self._build_uploaded_script_json(
                analysis=analysis,
                full_text=full_text,
                episode_contents=episode_contents,
                total_episodes=total_episodes,
                project=project,
                warnings=warnings,
                rule_analysis=rule_analysis,
            )
            return self._parse_script(
                raw_json,
                project.id,
                expected_episodes=total_episodes,
                require_counts=False,
                require_assets=False,
                require_refs=False,
                require_outline=False,
            )
        except Exception as exc:
            logger.warning(f"ScriptEngine: uploaded script asset extraction failed: {exc}")

        raw_json = self._build_uploaded_script_json(
            analysis=rule_analysis,
            full_text=full_text,
            episode_contents=episode_contents,
            total_episodes=total_episodes,
            project=project,
            warnings=warnings,
            rule_analysis=rule_analysis,
        )
        return self._parse_script(
            raw_json,
            project.id,
            expected_episodes=total_episodes,
            require_counts=False,
            require_assets=False,
            require_refs=False,
            require_outline=False,
        )

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

    async def _parse_generated_script(
        self,
        *,
        raw_json: dict,
        project_id: int,
        expected_episodes: int,
        chat_model: str = None,
        chat_api_key: str = None,
        chat_base_url: str = None,
        chat_options: dict[str, Any] | None = None,
    ) -> dict:
        try:
            return self._parse_script(raw_json, project_id, expected_episodes=expected_episodes)
        except ScriptValidationError as exc:
            logger.warning(f"ScriptEngine: structured script validation failed: {exc.issues}")
            repaired_json = await self._repair_script_json(
                raw_json=raw_json,
                issues=exc.issues,
                expected_episodes=expected_episodes,
                chat_model=chat_model,
                chat_api_key=chat_api_key,
                chat_base_url=chat_base_url,
                chat_options=chat_options,
            )

        try:
            return self._parse_script(repaired_json, project_id, expected_episodes=expected_episodes)
        except ScriptValidationError as exc:
            raise ValueError("Script validation failed: " + "; ".join(exc.issues)) from exc

    async def _repair_script_json(
        self,
        *,
        raw_json: dict,
        issues: list[str],
        expected_episodes: int,
        chat_model: str = None,
        chat_api_key: str = None,
        chat_base_url: str = None,
        chat_options: dict[str, Any] | None = None,
    ) -> dict:
        messages = build_repair_prompt(raw_json, issues, expected_episodes)
        resp = await ai_hub.chat.complete(
            messages=messages,
            temperature=0.2,
            max_tokens=6000 + expected_episodes * 2500,
            model=chat_model,
            api_key=chat_api_key,
            base_url=chat_base_url,
            **_extra_chat_kwargs(chat_options),
        )
        return self._parse_json_from_text(resp.content)

    async def _analyze_uploaded_script(
        self,
        *,
        full_text: str,
        total_episodes: int,
        chat_model: str = None,
        chat_api_key: str = None,
        chat_base_url: str = None,
        chat_options: dict[str, Any] | None = None,
    ) -> dict:
        messages = build_upload_analysis_prompt(full_text, total_episodes)
        resp = await ai_hub.chat.complete(
            messages=messages,
            temperature=0.2,
            max_tokens=3000 + total_episodes * 500,
            model=chat_model,
            api_key=chat_api_key,
            base_url=chat_base_url,
            **_extra_chat_kwargs(chat_options),
        )
        return self._parse_json_from_text(resp.content)

    def _build_uploaded_script_json(
        self,
        *,
        analysis: dict,
        full_text: str,
        episode_contents: list[str],
        total_episodes: int,
        project: Project,
        warnings: list[str],
        rule_analysis: dict | None = None,
    ) -> dict:
        field_analysis = rule_analysis or self._build_rule_upload_analysis(
            full_text=full_text,
            episode_contents=episode_contents,
        )
        field_characters = field_analysis.get("characters", []) if isinstance(field_analysis.get("characters"), list) else []
        field_scenes = field_analysis.get("scenes", []) if isinstance(field_analysis.get("scenes"), list) else []
        field_episodes = field_analysis.get("episodes", []) if isinstance(field_analysis.get("episodes"), list) else []

        analysis_episodes = {}
        for ep in analysis.get("episodes", []) if isinstance(analysis.get("episodes"), list) else []:
            if isinstance(ep, dict):
                analysis_episodes[self._to_int(ep.get("number"), len(analysis_episodes) + 1)] = ep
        field_episode_refs = {}
        for ep in field_episodes:
            if isinstance(ep, dict):
                field_episode_refs[self._to_int(ep.get("number"), len(field_episode_refs) + 1)] = ep

        episodes = []
        for index, content in enumerate(episode_contents):
            number = index + 1
            ep_info = analysis_episodes.get(number, {})
            field_ep_info = field_episode_refs.get(number, {})
            episodes.append({
                "number": number,
                "title": ep_info.get("title") or f"第{number}集",
                "content": content,
                "character_refs": field_ep_info.get("character_refs", []),
                "scene_refs": field_ep_info.get("scene_refs", []),
            })

        synopsis = full_text[:200] + "..." if len(full_text) > 200 else full_text
        return {
            "counts": analysis.get("counts") or {
                "episode_count": total_episodes,
                "character_count": len(field_characters),
                "scene_count": len(field_scenes),
            },
            "script_summary": {
                "custom_episode_count": total_episodes,
                "story_type": project.genre.value if project.genre else "",
                "story_overview": synopsis,
                "core_hook": "",
                "one_sentence_story": "",
            },
            "protagonist": field_characters[0].get("name", "") if field_characters else "",
            "genre": project.genre.value if project.genre else "",
            "synopsis": synopsis,
            "background": "",
            "setting": "",
            "one_liner": "",
            "characters": field_characters,
            "scenes": field_scenes,
            "episodes": episodes,
            "warnings": warnings,
        }

    def _build_rule_upload_analysis(
        self,
        *,
        full_text: str,
        episode_contents: list[str],
    ) -> dict:
        character_names = self._extract_characters(full_text)
        scene_names = self._extract_scenes(full_text)
        characters = [
            {"name": name, "role": "protagonist" if index == 0 else "supporting", "description": ""}
            for index, name in enumerate(character_names)
        ]
        scenes = [
            {"name": name, "description": "", "time_of_day": "day", "interior": True}
            for name in scene_names
        ]
        episodes = []
        for index, content in enumerate(episode_contents):
            episodes.append({
                "number": index + 1,
                "title": f"第{index + 1}集",
                "character_refs": [name for name in character_names if name in content],
                "scene_refs": [name for name in scene_names if name in content],
            })
        return {
            "counts": {
                "episode_count": len(episode_contents),
                "character_count": len(characters),
                "scene_count": len(scenes),
            },
            "protagonist": character_names[0] if character_names else "",
            "characters": characters,
            "scenes": scenes,
            "episodes": episodes,
        }

    def _parse_script(
        self,
        raw_json: dict,
        project_id: int,
        *,
        expected_episodes: int | None = None,
        require_counts: bool = True,
        require_assets: bool = True,
        require_refs: bool = True,
        require_outline: bool = True,
    ) -> dict:
        """
        Parse LLM JSON output into structured data suitable for DB insertion.
        """
        normalized = self._normalize_script_json(
            raw_json,
            expected_episodes=expected_episodes,
            require_counts=require_counts,
            require_assets=require_assets,
            require_refs=require_refs,
            require_outline=require_outline,
        )
        script_summary = raw_json.get("script_summary") or {}
        script_data = {
            "protagonist": normalized.get("protagonist", ""),
            "genre": normalized.get("genre", ""),
            "synopsis": raw_json.get("synopsis") or script_summary.get("story_overview", ""),
            "background": normalized.get("background", ""),
            "setting": normalized.get("setting") or script_summary.get("core_hook", ""),
            "one_liner": normalized.get("one_liner") or script_summary.get("one_sentence_story", ""),
            "raw_content": json.dumps(normalized, ensure_ascii=False),
        }

        episodes_data = []
        for ep in normalized.get("episodes", []):
            episodes_data.append({
                "number": ep.get("number", len(episodes_data) + 1),
                "title": ep.get("title", f"第{len(episodes_data) + 1}集"),
                "content": ep.get("content", ""),
            })

        characters_data = []
        for ch in normalized.get("characters", []):
            characters_data.append({
                "name": ch.get("name", ""),
                "role": ch.get("role", "supporting"),
                "description": ch.get("description", ""),
            })

        scenes_data = []
        for sc in normalized.get("scenes", []):
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
            "warnings": normalized.get("warnings", []),
        }

    def _normalize_script_json(
        self,
        raw_json: dict,
        *,
        expected_episodes: int | None,
        require_counts: bool,
        require_assets: bool,
        require_refs: bool,
        require_outline: bool,
    ) -> dict:
        issues: list[str] = []
        if not isinstance(raw_json, dict):
            raise ScriptValidationError(["root must be a JSON object"])

        characters = self._normalize_characters(raw_json.get("characters"))
        scenes = self._normalize_scenes(raw_json.get("scenes"))
        episodes = self._normalize_episodes(raw_json.get("episodes"))
        outline = raw_json.get("episode_outline") if isinstance(raw_json.get("episode_outline"), list) else []

        if expected_episodes is not None and len(episodes) != expected_episodes:
            issues.append(f"episodes length must be {expected_episodes}, got {len(episodes)}")
        if require_outline and expected_episodes is not None and len(outline) != expected_episodes:
            issues.append(f"episode_outline length must be {expected_episodes}, got {len(outline)}")
        if require_assets and not characters:
            issues.append("characters must include at least one item")
        if require_assets and not scenes:
            issues.append("scenes must include at least one item")

        counts = raw_json.get("counts")
        computed_counts = {
            "episode_count": len(episodes),
            "character_count": len(characters),
            "scene_count": len(scenes),
        }
        if require_counts:
            if not isinstance(counts, dict):
                issues.append("counts must be present")
            else:
                for key, expected in computed_counts.items():
                    actual = self._to_int(counts.get(key), -1)
                    if actual != expected:
                        issues.append(f"counts.{key} must be {expected}, got {counts.get(key)}")

        character_names = {character["name"] for character in characters}
        scene_names = {scene["name"] for scene in scenes}
        for episode in episodes:
            character_refs = episode.get("character_refs", [])
            scene_refs = episode.get("scene_refs", [])
            if require_refs and not character_refs:
                issues.append(f"episode {episode.get('number')} must include character_refs")
            if require_refs and not scene_refs:
                issues.append(f"episode {episode.get('number')} must include scene_refs")
            for ref in character_refs:
                if ref not in character_names:
                    issues.append(f"episode {episode.get('number')} references unknown character: {ref}")
            for ref in scene_refs:
                if ref not in scene_names:
                    issues.append(f"episode {episode.get('number')} references unknown scene: {ref}")

        if issues:
            raise ScriptValidationError(issues)

        normalized = dict(raw_json)
        normalized["counts"] = computed_counts
        normalized["characters"] = characters
        normalized["scenes"] = scenes
        normalized["episodes"] = episodes
        normalized["episode_outline"] = outline
        normalized["warnings"] = raw_json.get("warnings", []) if isinstance(raw_json.get("warnings"), list) else []
        return normalized

    def _normalize_characters(self, value: Any) -> list[dict]:
        result: list[dict] = []
        seen: set[str] = set()
        for item in value if isinstance(value, list) else []:
            if not isinstance(item, dict):
                continue
            name = self._clean_name(item.get("name"))
            if not name or name in seen:
                continue
            seen.add(name)
            result.append({
                "name": name,
                "role": self._normalize_role(item.get("role")),
                "description": str(item.get("description") or ""),
            })
        return result

    def _normalize_scenes(self, value: Any) -> list[dict]:
        result: list[dict] = []
        seen: set[str] = set()
        for item in value if isinstance(value, list) else []:
            if not isinstance(item, dict):
                continue
            name = self._clean_scene_name(item.get("name"))
            if not name or name in seen:
                continue
            seen.add(name)
            result.append({
                "name": name,
                "description": str(item.get("description") or ""),
                "time_of_day": str(item.get("time_of_day") or "day"),
                "interior": bool(item.get("interior", True)),
            })
        return result

    def _normalize_episodes(self, value: Any) -> list[dict]:
        result: list[dict] = []
        for index, item in enumerate(value if isinstance(value, list) else []):
            if not isinstance(item, dict):
                continue
            result.append({
                "number": self._to_int(item.get("number"), index + 1),
                "title": str(item.get("title") or f"第{index + 1}集"),
                "content": str(item.get("content") or ""),
                "character_refs": self._normalize_refs(item.get("character_refs"), self._clean_name),
                "scene_refs": self._normalize_refs(item.get("scene_refs"), self._clean_scene_name),
            })
        return result

    @staticmethod
    def _normalize_refs(value: Any, cleaner) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for item in value if isinstance(value, list) else []:
            name = cleaner(item)
            if name and name not in seen:
                seen.add(name)
                result.append(name)
        return result

    @staticmethod
    def _normalize_role(value: Any) -> str:
        role = str(value or "supporting").strip()
        valid = {item.value for item in CharacterRole}
        return role if role in valid else CharacterRole.SUPPORTING.value

    @staticmethod
    def _clean_name(value: Any) -> str:
        return re.sub(r"\s+", "", str(value or "").strip())[:100]

    @staticmethod
    def _clean_scene_name(value: Any) -> str:
        return re.sub(r"\s+", " ", str(value or "").strip())[:100]

    @staticmethod
    def _to_int(value: Any, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _extract_characters(self, text: str) -> list[str]:
        """Extract character names only from explicit upload fields."""
        names: list[str] = []
        seen: set[str] = set()

        def add_name(value: str) -> None:
            name = self._clean_character_candidate(value)
            if name and name not in seen:
                seen.add(name)
                names.append(name)

        list_patterns = [
            r'^\s*(?:[-*]\s*)?(?:\*\*)?(?:出场人物|人物|角色表|角色清单|主要角色)(?:\*\*)?\s*[：:]\s*(.+?)\s*$',
            r'^\s*(?:[-*]\s*)?(?:\*\*)?(?:出场人物|人物|角色表|角色清单|主要角色)\s*[：:]\s*\*\*\s*(.+?)\s*$',
        ]
        for pattern in list_patterns:
            for match in re.findall(pattern, text, re.MULTILINE):
                for part in re.split(r'[、,，/／|｜]+', match):
                    add_name(part)

        section_headers = re.compile(r'^\s*(?:#{1,6}\s*)?(?:\*\*)?(?:角色表|角色清单|主要角色)(?:\*\*)?\s*$')
        stop_headers = re.compile(r'^\s*(?:#{1,6}\s*)?(?:第\s*\d+\s*集|场景|场景表|场景清单|拍摄场景|正文|剧本正文)\b')
        in_section = False
        for line in text.splitlines():
            stripped = line.strip()
            if section_headers.match(stripped):
                in_section = True
                continue
            if not in_section:
                continue
            if not stripped:
                in_section = False
                continue
            if stop_headers.match(stripped):
                in_section = False
                continue
            match = re.match(r'^\s*(?:[-*•]\s*|\d+[.、]\s*)?(.+?)\s*(?:[：:\-—]|$)', stripped)
            if match:
                add_name(match.group(1))

        return names[:20]

    def _extract_scenes(self, text: str) -> list[str]:
        """Extract scene names only from explicit upload fields."""
        scenes: list[str] = []
        seen: set[str] = set()

        def add_scene(value: str) -> None:
            name = self._clean_scene_candidate(value)
            if name and name not in seen:
                seen.add(name)
                scenes.append(name)

        patterns = [
            r'^\s*(?:[-*]\s*)?\*\*(?:场景|场景表|场景清单|拍摄场景)[一二三四五六七八九十\d]*[：:]\*\*\s*(.+?)\s*$',
            r'^\s*(?:[-*]\s*)?\*\*(?:场景|场景表|场景清单|拍摄场景)[一二三四五六七八九十\d]*[：:]\s*(.+?)\*\*\s*$',
            r'^\s*(?:[-*]\s*)?(?:场景|场景表|场景清单|拍摄场景)[一二三四五六七八九十\d]*[：:]\s*(.+?)\s*$',
        ]
        for pattern in patterns:
            for match in re.findall(pattern, text, re.IGNORECASE | re.MULTILINE):
                parts = re.split(r'[、,，/／|｜]+', match)
                for part in parts:
                    add_scene(part)

        section_headers = re.compile(r'^\s*(?:#{1,6}\s*)?(?:\*\*)?(?:场景表|场景清单|拍摄场景)(?:\*\*)?\s*$', re.IGNORECASE)
        stop_headers = re.compile(r'^\s*(?:#{1,6}\s*)?(?:第\s*\d+\s*集|角色表|角色清单|主要角色|出场人物|人物|正文|剧本正文)\b')
        in_section = False
        for line in text.splitlines():
            stripped = line.strip()
            if section_headers.match(stripped):
                in_section = True
                continue
            if not in_section:
                continue
            if not stripped:
                in_section = False
                continue
            if stop_headers.match(stripped):
                in_section = False
                continue
            match = re.match(r'^\s*(?:[-*•]\s*|\d+[.、]\s*)?(.+?)\s*(?:[：:\-—]|$)', stripped)
            if match:
                add_scene(match.group(1))

        return scenes[:20]

    @staticmethod
    def _clean_character_candidate(value: str) -> str:
        text = re.sub(r'[（(].*?[）)]', '', str(value or "")).strip()
        text = re.split(r'[：:\-—]', text, maxsplit=1)[0]
        name = re.sub(r'[*_`"“”\'（）()【】\[\]]', '', text).strip()
        name = re.sub(r'\s+', '', name)
        blocked = {
            "旁白", "场景", "标题", "提示", "备注", "注", "音乐", "本集关键词", "本集爽点",
            "前情提要", "本集钩子", "下集预告", "出场人物", "人物", "角色表",
            "角色清单", "主要角色", "剧本", "作者", "类型", "题材", "字数", "时间",
            "地点", "年代", "风格", "集数", "场次", "场景表", "场景清单", "拍摄场景",
            "内景", "外景", "闪入", "闪回", "切入", "切至", "淡入", "淡出",
        }
        if not name or name in blocked or len(name) > 12:
            return ""
        if re.match(r'^第\d+集$', name):
            return ""
        if any(token in name for token in ("场景", "内景", "外景", "音乐提示", "声音", "批注")):
            return ""
        return name

    @staticmethod
    def _clean_scene_candidate(value: str) -> str:
        text = re.sub(r'[*_`"“”]', '', str(value or "")).strip()
        text = re.sub(r'\s+', ' ', text)
        text = text.strip(" ：:-—")
        blocked = {
            "（按时间顺序）", "(按时间顺序)", "按时间顺序",
            "（按出场顺序）", "(按出场顺序)", "按出场顺序",
        }
        if text in blocked:
            return ""
        if "·" in text:
            parts = [part.strip() for part in text.split("·") if part.strip()]
            if len(parts) >= 2 and re.search(r'内景|外景|INT|EXT', parts[0], re.IGNORECASE):
                text = parts[1]
            elif parts:
                text = parts[0]
        text = re.sub(r'^(内景|外景|日|夜|晨|昏|INT\.|EXT\.|INT\./EXT\.)\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(
            r'\s*(清晨|凌晨|早晨|上午|中午|午后|下午|傍晚|黄昏|深夜|夜晚|白天|日间|夜间|日|夜|晨|昏|DAY|NIGHT)$',
            '',
            text,
            flags=re.IGNORECASE,
        ).strip()
        text = text.strip(" ：:-—")
        if not text or len(text) > 30:
            return ""
        return text

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
