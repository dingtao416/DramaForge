"""
DramaForge v2.0 — Storage Service
===================================
Manages file storage paths, downloads from URLs, and serves asset URLs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import httpx
from loguru import logger

from app.core.config import settings


class StorageService:
    """Centralized file storage management."""

    # ── Path Builders ─────────────────────────────────────────────

    def project_path(self, project_id: int) -> Path:
        """Root directory for a project's generated assets."""
        p = settings.projects_path / str(project_id)
        p.mkdir(parents=True, exist_ok=True)
        return p

    def character_image_path(
        self, project_id: int, char_id: int, idx: int = 0
    ) -> Path:
        p = self.project_path(project_id) / "characters"
        p.mkdir(parents=True, exist_ok=True)
        return p / f"char_{char_id}_{idx:03d}.png"

    def scene_image_path(
        self, project_id: int, scene_id: int, idx: int = 0
    ) -> Path:
        p = self.project_path(project_id) / "scenes"
        p.mkdir(parents=True, exist_ok=True)
        return p / f"scene_{scene_id}_{idx:03d}.png"

    def shot_image_path(
        self, project_id: int, ep_num: int, shot_idx: int
    ) -> Path:
        p = self.project_path(project_id) / f"ep{ep_num:03d}" / "images"
        p.mkdir(parents=True, exist_ok=True)
        return p / f"shot_{shot_idx:04d}.png"

    def shot_audio_path(
        self, project_id: int, ep_num: int, shot_idx: int
    ) -> Path:
        p = self.project_path(project_id) / f"ep{ep_num:03d}" / "audio"
        p.mkdir(parents=True, exist_ok=True)
        return p / f"shot_{shot_idx:04d}.mp3"

    def segment_video_path(
        self, project_id: int, ep_num: int, seg_idx: int
    ) -> Path:
        p = self.project_path(project_id) / f"ep{ep_num:03d}" / "segments"
        p.mkdir(parents=True, exist_ok=True)
        return p / f"segment_{seg_idx:04d}.mp4"

    def episode_video_path(
        self, project_id: int, ep_num: int
    ) -> Path:
        p = self.project_path(project_id) / f"ep{ep_num:03d}"
        p.mkdir(parents=True, exist_ok=True)
        return p / f"episode_{ep_num:03d}_final.mp4"

    def upload_path(self, project_id: int, filename: str) -> Path:
        p = self.project_path(project_id) / "uploads"
        p.mkdir(parents=True, exist_ok=True)
        return p / filename

    # ── File Operations ───────────────────────────────────────────

    async def save_from_url(self, url: str, dest: Path) -> Path:
        """Download a remote file and save to local path."""
        dest.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Storage: downloading {url[:80]}... → {dest}")

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            dest.write_bytes(resp.content)

        logger.info(f"Storage: saved {len(resp.content)} bytes → {dest}")
        return dest

    async def save_from_bytes(self, data: bytes, dest: Path) -> Path:
        """Save raw bytes to local path."""
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        logger.info(f"Storage: saved {len(data)} bytes → {dest}")
        return dest

    def get_url(self, path: Path | str) -> str:
        """
        Convert a local file path to an accessible URL.
        Assumes the storage directory is mounted at /storage.
        """
        path = Path(path)
        try:
            relative = path.relative_to(Path(settings.storage_dir).resolve())
        except ValueError:
            try:
                relative = path.relative_to(settings.storage_dir)
            except ValueError:
                # Fallback: use full path as relative
                relative = path

        return f"/storage/{relative.as_posix()}"

    def exists(self, path: Path) -> bool:
        """Check if a file exists."""
        return path.exists()

    def delete(self, path: Path) -> bool:
        """Delete a file if it exists."""
        if path.exists():
            path.unlink()
            return True
        return False


# Module-level singleton
storage = StorageService()
