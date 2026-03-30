"""
DramaForge - Pipeline Orchestrator
Orchestrates the full workflow: Script → Storyboard → Images → TTS → Video.
Supports human-in-the-loop review at key stages.
"""

from pathlib import Path
from typing import Optional

from loguru import logger
from sqlalchemy.orm import Session

from app.agents import ImageAgent, ScriptAgent, StoryboardAgent, TTSAgent, VideoAgent
from app.models.database import (
    Character,
    GeneratedVideo,
    Project,
    ProjectStatus,
    Script,
    Storyboard,
    StoryboardStatus,
)
from config import settings


class PipelineOrchestrator:
    """
    Orchestrates the short drama production pipeline.

    Pipeline stages:
    1. Generate outline (optional) → Human review
    2. Generate script → Human review
    3. Generate storyboards → Human review
    4. Generate images for each storyboard panel
    5. Generate TTS audio for each panel
    6. Compose final video
    """

    def __init__(self, db: Session):
        self.db = db
        self.script_agent = ScriptAgent()
        self.storyboard_agent = StoryboardAgent()
        self.image_agent = ImageAgent()
        self.tts_agent = TTSAgent()
        self.video_agent = VideoAgent()

    # ==================== Stage 1: Outline ====================

    async def generate_outline(self, project_id: int) -> dict:
        """Generate a drama outline for a project."""
        project = self.db.query(Project).get(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        result = await self.script_agent.generate_outline(
            genre=project.genre.value if project.genre else "other",
            topic=project.description or project.title,
            total_episodes=project.target_episodes,
            duration=project.target_duration,
        )

        # Save characters from outline
        if result.get("characters"):
            for char_data in result["characters"]:
                character = Character(
                    project_id=project.id,
                    name=char_data["name"],
                    description=char_data.get("description", ""),
                    appearance=char_data.get("appearance", ""),
                )
                self.db.add(character)

        self.db.commit()
        logger.info(f"Outline generated for project {project_id}")
        return result

    # ==================== Stage 2: Script ====================

    async def generate_script(self, project_id: int, episode: int = 1, outline: str = "") -> Script:
        """Generate a script for a specific episode."""
        project = self.db.query(Project).get(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Get characters
        characters = self.db.query(Character).filter_by(project_id=project_id).all()
        char_list = [
            {"name": c.name, "description": c.description, "appearance": c.appearance}
            for c in characters
        ]

        content = await self.script_agent.generate_script(
            genre=project.genre.value if project.genre else "other",
            topic=project.description or project.title,
            duration=project.target_duration,
            episode=episode,
            total_episodes=project.target_episodes,
            outline=outline,
            characters=char_list,
            style=project.style_prompt or "",
        )

        # Save to database
        script = Script(
            project_id=project.id,
            episode=episode,
            content=content,
            outline=outline,
        )
        self.db.add(script)
        project.status = ProjectStatus.SCRIPT_READY
        self.db.commit()

        logger.info(f"Script generated | project={project_id} episode={episode}")
        return script

    # ==================== Stage 3: Storyboards ====================

    async def generate_storyboards(self, script_id: int) -> list[Storyboard]:
        """Generate storyboard panels from a script."""
        script = self.db.query(Script).get(script_id)
        if not script:
            raise ValueError(f"Script {script_id} not found")

        project = self.db.query(Project).get(script.project_id)
        characters = self.db.query(Character).filter_by(project_id=project.id).all()
        char_list = [
            {"name": c.name, "appearance": c.appearance}
            for c in characters
        ]

        storyboard_data = await self.storyboard_agent.generate_storyboards(
            script_content=script.content,
            style_prompt=project.style_prompt or "anime style, high quality, cinematic",
            characters=char_list,
        )

        # Save to database
        db_storyboards = []
        for sb_data in storyboard_data:
            sb = Storyboard(
                script_id=script.id,
                sequence=sb_data["sequence"],
                scene_description=sb_data.get("scene_description", ""),
                narration=sb_data.get("narration", ""),
                dialogue=sb_data.get("dialogue", ""),
                image_prompt=sb_data.get("image_prompt", ""),
                duration=sb_data.get("duration", 5.0),
                transition=sb_data.get("transition", "crossfade"),
                status=StoryboardStatus.PENDING,
            )
            self.db.add(sb)
            db_storyboards.append(sb)

        project.status = ProjectStatus.STORYBOARD_READY
        self.db.commit()

        logger.info(f"Storyboards generated | script={script_id} count={len(db_storyboards)}")
        return db_storyboards

    # ==================== Stage 4: Generate Assets ====================

    async def generate_images(self, script_id: int) -> list[dict]:
        """Generate images for all approved storyboards of a script."""
        storyboards = (
            self.db.query(Storyboard)
            .filter_by(script_id=script_id, status=StoryboardStatus.APPROVED)
            .order_by(Storyboard.sequence)
            .all()
        )

        if not storyboards:
            raise ValueError(f"No approved storyboards for script {script_id}")

        script = self.db.query(Script).get(script_id)
        project = self.db.query(Project).get(script.project_id)

        results = []
        for sb in storyboards:
            sb.status = StoryboardStatus.IMAGE_GENERATING
            self.db.commit()

            output_path = str(
                settings.images_path / f"project_{project.id}" / f"sb_{sb.id}.png"
            )

            try:
                result = await self.image_agent.generate_image(
                    prompt=sb.image_prompt,
                    output_path=output_path,
                )
                sb.image_path = result["image_path"]
                sb.status = StoryboardStatus.IMAGE_READY
                results.append(result)
            except Exception as e:
                logger.error(f"Image generation failed for storyboard {sb.id}: {e}")
                sb.status = StoryboardStatus.APPROVED  # Reset to allow retry

            self.db.commit()

        logger.info(f"Images generated | script={script_id} count={len(results)}")
        return results

    async def generate_audio(self, script_id: int) -> list[dict]:
        """Generate TTS audio for all image-ready storyboards."""
        storyboards = (
            self.db.query(Storyboard)
            .filter_by(script_id=script_id, status=StoryboardStatus.IMAGE_READY)
            .order_by(Storyboard.sequence)
            .all()
        )

        script = self.db.query(Script).get(script_id)
        project = self.db.query(Project).get(script.project_id)

        results = []
        for sb in storyboards:
            # Combine narration and dialogue for TTS
            text = sb.dialogue or sb.narration
            if not text:
                sb.status = StoryboardStatus.AUDIO_READY
                self.db.commit()
                continue

            sb.status = StoryboardStatus.AUDIO_GENERATING
            self.db.commit()

            output_path = str(
                settings.audio_path / f"project_{project.id}" / f"sb_{sb.id}.mp3"
            )

            try:
                result = await self.tts_agent.generate_audio(
                    text=text,
                    output_path=output_path,
                )
                sb.audio_path = result["audio_path"]
                sb.audio_duration = result.get("duration")
                sb.subtitle_path = result.get("subtitle_path")
                sb.status = StoryboardStatus.AUDIO_READY
                results.append(result)
            except Exception as e:
                logger.error(f"TTS generation failed for storyboard {sb.id}: {e}")
                sb.status = StoryboardStatus.IMAGE_READY  # Reset

            self.db.commit()

        logger.info(f"Audio generated | script={script_id} count={len(results)}")
        return results

    # ==================== Stage 5: Compose Video ====================

    async def compose_video(self, script_id: int) -> GeneratedVideo:
        """Compose the final video from all completed storyboard panels."""
        storyboards = (
            self.db.query(Storyboard)
            .filter_by(script_id=script_id)
            .filter(
                Storyboard.status.in_([
                    StoryboardStatus.AUDIO_READY,
                    StoryboardStatus.COMPLETED,
                ])
            )
            .order_by(Storyboard.sequence)
            .all()
        )

        if not storyboards:
            raise ValueError(f"No completed storyboards for script {script_id}")

        script = self.db.query(Script).get(script_id)
        project = self.db.query(Project).get(script.project_id)

        # Prepare storyboard data for video agent
        sb_data = []
        for sb in storyboards:
            sb_data.append({
                "sequence": sb.sequence,
                "image_path": sb.image_path,
                "audio_path": sb.audio_path,
                "audio_duration": sb.audio_duration,
                "duration": sb.duration,
                "narration": sb.narration,
                "dialogue": sb.dialogue,
                "transition": sb.transition,
            })

        output_path = str(
            settings.videos_path / f"project_{project.id}" / f"episode_{script.episode}.mp4"
        )

        project.status = ProjectStatus.GENERATING
        self.db.commit()

        try:
            result = await self.video_agent.compose_video(
                storyboards=sb_data,
                output_path=output_path,
            )

            # Save to database
            video = GeneratedVideo(
                project_id=project.id,
                script_id=script.id,
                video_path=result["video_path"],
                duration=result["duration"],
                resolution=result["resolution"],
                status="completed",
            )
            self.db.add(video)

            # Mark storyboards as completed
            for sb in storyboards:
                sb.status = StoryboardStatus.COMPLETED

            project.status = ProjectStatus.COMPLETED
            self.db.commit()

            logger.info(f"Video composed | project={project.id} script={script_id}")
            return video

        except Exception as e:
            project.status = ProjectStatus.FAILED
            self.db.commit()
            logger.error(f"Video composition failed: {e}")
            raise
