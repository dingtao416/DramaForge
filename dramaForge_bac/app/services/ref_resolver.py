"""
DramaForge v2.0 — Reference Resolver
======================================
Resolves @mentions in text: @角色名 → character object, @场景名 → scene object.
Used during storyboard generation to link shots to actual character/scene data.
"""

from __future__ import annotations

import re
from typing import Optional

from loguru import logger

from app.models.character import Character
from app.models.scene import SceneLocation


class RefResolver:
    """Resolves @references in prompt templates and shot descriptions."""

    def __init__(
        self,
        characters: list[Character],
        scenes: list[SceneLocation],
    ):
        # Build lookup indexes
        self._char_by_name: dict[str, Character] = {
            c.name: c for c in characters
        }
        self._char_by_id: dict[int, Character] = {
            c.id: c for c in characters
        }
        self._scene_by_name: dict[str, SceneLocation] = {
            s.name: s for s in scenes
        }
        self._scene_by_id: dict[int, SceneLocation] = {
            s.id: s for s in scenes
        }

    def resolve_character(self, ref: str) -> Optional[Character]:
        """
        Resolve a character reference.

        Args:
            ref: Character name (with or without '@' prefix)

        Returns:
            Character object or None.
        """
        name = ref.lstrip("@").strip()
        char = self._char_by_name.get(name)
        if not char:
            # Fuzzy match: partial name
            for cname, c in self._char_by_name.items():
                if name in cname or cname in name:
                    char = c
                    break
        return char

    def resolve_character_by_id(self, char_id: int) -> Optional[Character]:
        """Resolve by ID."""
        return self._char_by_id.get(char_id)

    def resolve_scene(self, ref: str) -> Optional[SceneLocation]:
        """
        Resolve a scene reference.

        Args:
            ref: Scene name (with or without '@' prefix)

        Returns:
            SceneLocation object or None.
        """
        name = ref.lstrip("@").strip()
        scene = self._scene_by_name.get(name)
        if not scene:
            # Fuzzy match
            for sname, s in self._scene_by_name.items():
                if name in sname or sname in name:
                    scene = s
                    break
        return scene

    def resolve_scene_by_id(self, scene_id: int) -> Optional[SceneLocation]:
        """Resolve by ID."""
        return self._scene_by_id.get(scene_id)

    def resolve_prompt(self, template: str) -> str:
        """
        Replace all @references in a template string with actual descriptions.

        Pattern: @角色名 or @场景名
        Replaces with the character/scene description.

        Args:
            template: Text containing @references.

        Returns:
            Text with all @references replaced.
        """
        def _replace_ref(match: re.Match) -> str:
            name = match.group(1)

            # Try character first
            char = self.resolve_character(name)
            if char:
                desc = char.description or char.name
                return desc

            # Then try scene
            scene = self.resolve_scene(name)
            if scene:
                desc = scene.description or scene.name
                return desc

            # Unresolved — keep original
            logger.warning(f"RefResolver: unresolved reference @{name}")
            return f"@{name}"

        # Match @followed_by_non_whitespace (Chinese/English chars)
        return re.sub(r'@([\w\u4e00-\u9fff]+)', _replace_ref, template)

    @property
    def characters(self) -> list[Character]:
        """All characters in the resolver."""
        return list(self._char_by_name.values())

    @property
    def scenes(self) -> list[SceneLocation]:
        """All scenes in the resolver."""
        return list(self._scene_by_name.values())
