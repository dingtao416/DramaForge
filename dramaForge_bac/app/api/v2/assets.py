"""
DramaForge v2.0 — Assets API
==============================
Endpoints for character/scene asset generation, editing, and management.
Also includes global asset library endpoints (Spec 18).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.project import Project, ProjectStep
from app.models.script import Script
from app.models.character import Character
from app.models.scene import SceneLocation
from app.schemas.assets import (
    CharacterDetail,
    CharacterUpdate,
    CharacterRegenerateRequest,
    SceneDetail,
    SceneUpdate,
    SceneRegenerateRequest,
    AssetsGenerateRequest,
)
from app.engines.assets_engine import assets_engine
from app.core.security import CurrentUser, DbSession
from app.core.billing_deps import require_credits

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════
# Project-scoped assets (Spec 15)
# ═══════════════════════════════════════════════════════════════════

@router.post("/projects/{project_id}/assets/generate")
async def generate_assets(
    project_id: int,
    user: CurrentUser,
    db: DbSession,
    body: AssetsGenerateRequest = AssetsGenerateRequest(),
):
    """Generate all character + scene assets from the approved script."""
    # Each asset generation counts as image_default cost
    # We charge once up-front; could be per-image in future
    await require_credits(db, user.id, "image_default", description="素材批量生成")

    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get script
    stmt = select(Script).where(Script.project_id == project_id)
    result = await db.execute(stmt)
    script = result.scalar_one_or_none()
    if not script:
        raise HTTPException(status_code=400, detail="No script found. Generate a script first.")

    # Get characters and scenes
    chars_result = await db.execute(
        select(Character).where(Character.project_id == project_id)
    )
    characters = list(chars_result.scalars().all())

    scenes_result = await db.execute(
        select(SceneLocation).where(SceneLocation.project_id == project_id)
    )
    scenes = list(scenes_result.scalars().all())

    if not characters and not scenes:
        raise HTTPException(status_code=400, detail="No characters or scenes found.")

    # Generate assets
    updated_chars, updated_scenes = await assets_engine.generate_all_assets(
        script=script,
        characters=characters,
        scenes=scenes,
        project_id=project_id,
    )

    await db.flush()

    return {
        "message": "Assets generated successfully",
        "characters": len(updated_chars),
        "scenes": len(updated_scenes),
    }


@router.get("/projects/{project_id}/characters", response_model=list[CharacterDetail])
async def list_characters(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """List all characters for a project."""
    result = await db.execute(
        select(Character).where(Character.project_id == project_id)
    )
    return result.scalars().all()


@router.put("/projects/{project_id}/characters/{char_id}", response_model=CharacterDetail)
async def update_character(
    project_id: int,
    char_id: int,
    body: CharacterUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Edit a character's details."""
    character = await db.get(Character, char_id)
    if not character or character.project_id != project_id:
        raise HTTPException(status_code=404, detail="Character not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(character, key, value)

    await db.flush()
    await db.refresh(character)
    return character


@router.post("/projects/{project_id}/characters/{char_id}/regenerate", response_model=CharacterDetail)
async def regenerate_character(
    project_id: int,
    char_id: int,
    user: CurrentUser,
    db: DbSession,
    body: CharacterRegenerateRequest = CharacterRegenerateRequest(),
):
    """Regenerate a character's image."""
    await require_credits(db, user.id, "image_default", description="角色图片重新生成")

    character = await db.get(Character, char_id)
    if not character or character.project_id != project_id:
        raise HTTPException(status_code=404, detail="Character not found")

    await assets_engine.regenerate_character_image(
        character=character,
        project_id=project_id,
        prompt=body.prompt,
    )

    await db.flush()
    await db.refresh(character)
    return character


@router.get("/projects/{project_id}/scenes", response_model=list[SceneDetail])
async def list_scenes(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """List all scenes for a project."""
    result = await db.execute(
        select(SceneLocation).where(SceneLocation.project_id == project_id)
    )
    return result.scalars().all()


@router.put("/projects/{project_id}/scenes/{scene_id}", response_model=SceneDetail)
async def update_scene(
    project_id: int,
    scene_id: int,
    body: SceneUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Edit a scene's details."""
    scene = await db.get(SceneLocation, scene_id)
    if not scene or scene.project_id != project_id:
        raise HTTPException(status_code=404, detail="Scene not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(scene, key, value)

    await db.flush()
    await db.refresh(scene)
    return scene


@router.post("/projects/{project_id}/scenes/{scene_id}/regenerate", response_model=SceneDetail)
async def regenerate_scene(
    project_id: int,
    scene_id: int,
    user: CurrentUser,
    db: DbSession,
    body: SceneRegenerateRequest = SceneRegenerateRequest(),
):
    """Regenerate a scene's image."""
    await require_credits(db, user.id, "image_default", description="场景图片重新生成")

    scene = await db.get(SceneLocation, scene_id)
    if not scene or scene.project_id != project_id:
        raise HTTPException(status_code=404, detail="Scene not found")

    await assets_engine.regenerate_scene_image(
        scene=scene,
        project_id=project_id,
        prompt=body.prompt,
    )

    await db.flush()
    await db.refresh(scene)
    return scene


@router.post("/projects/{project_id}/assets/approve")
async def approve_assets(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Approve all assets and advance project to Step 3 (Storyboard)."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.status = ProjectStep.STORYBOARD
    await db.flush()

    return {"message": "Assets approved", "status": ProjectStep.STORYBOARD.value}


# ═══════════════════════════════════════════════════════════════════
# Global asset library (Spec 18)
# ═══════════════════════════════════════════════════════════════════

@router.get("/assets", response_model=list[CharacterDetail])
async def list_global_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    role: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List all character assets across projects (global library)."""
    stmt = select(Character).offset(skip).limit(limit)
    if role:
        stmt = stmt.where(Character.role == role)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/assets/characters", response_model=list[CharacterDetail])
async def list_global_characters(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List all characters across all projects."""
    stmt = select(Character).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.delete("/assets/{asset_id}", status_code=204)
async def delete_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete an asset by ID."""
    # Try character first, then scene
    character = await db.get(Character, asset_id)
    if character:
        await db.delete(character)
        await db.flush()
        return

    scene = await db.get(SceneLocation, asset_id)
    if scene:
        await db.delete(scene)
        await db.flush()
        return

    raise HTTPException(status_code=404, detail="Asset not found")