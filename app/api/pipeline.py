"""
DramaForge - Pipeline API
REST API endpoints for triggering pipeline stages.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.database import (
    Storyboard,
    StoryboardStatus,
    get_db,
)
from app.pipeline.orchestrator import PipelineOrchestrator

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


# ==================== Schemas ====================

class OutlineRequest(BaseModel):
    project_id: int


class ScriptRequest(BaseModel):
    project_id: int
    episode: int = 1
    outline: str = ""


class StoryboardRequest(BaseModel):
    script_id: int


class ApproveStoryboardsRequest(BaseModel):
    storyboard_ids: list[int]


class GenerateAssetsRequest(BaseModel):
    script_id: int


class ComposeVideoRequest(BaseModel):
    script_id: int


# ==================== Endpoints ====================

@router.post("/outline")
async def generate_outline(data: OutlineRequest, db: Session = Depends(get_db)):
    """Stage 1: Generate a drama outline for a project."""
    pipeline = PipelineOrchestrator(db=db)
    try:
        result = await pipeline.generate_outline(project_id=data.project_id)
        return {"status": "success", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Outline generation failed: {e}")


@router.post("/script")
async def generate_script(data: ScriptRequest, db: Session = Depends(get_db)):
    """Stage 2: Generate a script for a specific episode."""
    pipeline = PipelineOrchestrator(db=db)
    try:
        script = await pipeline.generate_script(
            project_id=data.project_id,
            episode=data.episode,
            outline=data.outline,
        )
        return {
            "status": "success",
            "data": {
                "script_id": script.id,
                "episode": script.episode,
                "content": script.content,
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Script generation failed: {e}")


@router.post("/storyboards")
async def generate_storyboards(data: StoryboardRequest, db: Session = Depends(get_db)):
    """Stage 3: Generate storyboard panels from a script."""
    pipeline = PipelineOrchestrator(db=db)
    try:
        storyboards = await pipeline.generate_storyboards(script_id=data.script_id)
        return {
            "status": "success",
            "data": [
                {
                    "id": sb.id,
                    "sequence": sb.sequence,
                    "scene_description": sb.scene_description,
                    "image_prompt": sb.image_prompt,
                    "narration": sb.narration,
                    "dialogue": sb.dialogue,
                    "duration": sb.duration,
                    "transition": sb.transition,
                    "status": sb.status.value,
                }
                for sb in storyboards
            ],
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storyboard generation failed: {e}")


@router.post("/storyboards/approve")
async def approve_storyboards(data: ApproveStoryboardsRequest, db: Session = Depends(get_db)):
    """Approve storyboard panels for asset generation."""
    storyboards = (
        db.query(Storyboard)
        .filter(Storyboard.id.in_(data.storyboard_ids))
        .all()
    )

    if not storyboards:
        raise HTTPException(status_code=404, detail="No storyboards found")

    for sb in storyboards:
        sb.status = StoryboardStatus.APPROVED

    db.commit()
    return {
        "status": "success",
        "message": f"{len(storyboards)} storyboards approved",
    }


@router.post("/generate-images")
async def generate_images(data: GenerateAssetsRequest, db: Session = Depends(get_db)):
    """Stage 4a: Generate images for all approved storyboards."""
    pipeline = PipelineOrchestrator(db=db)
    try:
        results = await pipeline.generate_images(script_id=data.script_id)
        return {
            "status": "success",
            "data": {"images_generated": len(results)},
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {e}")


@router.post("/generate-audio")
async def generate_audio(data: GenerateAssetsRequest, db: Session = Depends(get_db)):
    """Stage 4b: Generate TTS audio for all image-ready storyboards."""
    pipeline = PipelineOrchestrator(db=db)
    try:
        results = await pipeline.generate_audio(script_id=data.script_id)
        return {
            "status": "success",
            "data": {"audio_generated": len(results)},
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio generation failed: {e}")


@router.post("/compose-video")
async def compose_video(data: ComposeVideoRequest, db: Session = Depends(get_db)):
    """Stage 5: Compose the final video."""
    pipeline = PipelineOrchestrator(db=db)
    try:
        video = await pipeline.compose_video(script_id=data.script_id)
        return {
            "status": "success",
            "data": {
                "video_id": video.id,
                "video_path": video.video_path,
                "duration": video.duration,
                "resolution": video.resolution,
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video composition failed: {e}")
