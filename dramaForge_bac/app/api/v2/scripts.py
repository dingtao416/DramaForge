"""
DramaForge v2.0 — Scripts API
===============================
Endpoints for script generation, upload, editing, and approval.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.project import Project, ProjectStep
from app.models.script import Script
from app.models.episode import Episode
from app.models.character import Character, CharacterRole
from app.models.scene import SceneLocation
from app.schemas.script import (
    ScriptGenerateRequest,
    ScriptDetail,
    ScriptUpdate,
    EpisodeUpdate,
)
from app.engines.script_engine import script_engine
from app.services.storage import storage

router = APIRouter()


async def _get_project(project_id: int, db: AsyncSession) -> Project:
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


async def _get_script(project_id: int, db: AsyncSession) -> Script:
    stmt = (
        select(Script)
        .where(Script.project_id == project_id)
        .options(selectinload(Script.episodes))
    )
    result = await db.execute(stmt)
    script = result.scalar_one_or_none()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script


@router.post("/projects/{project_id}/script/generate", response_model=ScriptDetail)
async def generate_script(
    project_id: int,
    body: ScriptGenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    """AI-generate a structured script from user input."""
    project = await _get_project(project_id, db)

    # Remove existing script if any
    existing = await db.execute(
        select(Script).where(Script.project_id == project_id)
    )
    old_script = existing.scalar_one_or_none()
    if old_script:
        await db.delete(old_script)
        await db.flush()

    # Generate via ScriptEngine
    result = await script_engine.create_from_text(
        user_input=body.user_input,
        project=project,
        genre=body.genre,
        total_episodes=body.total_episodes,
        duration=body.duration_per_episode,
    )

    # Create Script ORM object
    script = Script(project_id=project_id, **result["script"])
    db.add(script)
    await db.flush()

    # Create Episodes
    for ep_data in result["episodes"]:
        episode = Episode(script_id=script.id, **ep_data)
        db.add(episode)

    # Create Characters
    for ch_data in result["characters"]:
        role_str = ch_data.pop("role", "supporting")
        try:
            role = CharacterRole(role_str)
        except ValueError:
            role = CharacterRole.SUPPORTING
        character = Character(
            project_id=project_id,
            role=role,
            **ch_data,
        )
        db.add(character)

    # Create Scenes
    for sc_data in result["scenes"]:
        scene = SceneLocation(project_id=project_id, **sc_data)
        db.add(scene)

    await db.flush()
    await db.refresh(script, attribute_names=["episodes"])
    return script


@router.post("/projects/{project_id}/script/upload", response_model=ScriptDetail)
async def upload_script(
    project_id: int,
    file: UploadFile = File(...),
    total_episodes: int = 1,
    db: AsyncSession = Depends(get_db),
):
    """Upload a .docx script file."""
    project = await _get_project(project_id, db)

    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are supported")

    # Save uploaded file
    dest = storage.upload_path(project_id, file.filename)
    content = await file.read()
    await storage.save_from_bytes(content, dest)

    # Parse via ScriptEngine
    result = await script_engine.create_from_docx(
        file_path=dest,
        project=project,
        total_episodes=total_episodes,
    )

    # Remove existing script
    existing = await db.execute(
        select(Script).where(Script.project_id == project_id)
    )
    old_script = existing.scalar_one_or_none()
    if old_script:
        await db.delete(old_script)
        await db.flush()

    # Create Script + Episodes
    script = Script(project_id=project_id, **result["script"])
    db.add(script)
    await db.flush()

    for ep_data in result["episodes"]:
        db.add(Episode(script_id=script.id, **ep_data))

    for ch_data in result["characters"]:
        role_str = ch_data.pop("role", "supporting")
        try:
            role = CharacterRole(role_str)
        except ValueError:
            role = CharacterRole.SUPPORTING
        db.add(Character(project_id=project_id, role=role, **ch_data))

    for sc_data in result["scenes"]:
        db.add(SceneLocation(project_id=project_id, **sc_data))

    await db.flush()
    await db.refresh(script, attribute_names=["episodes"])
    return script


@router.get("/projects/{project_id}/script", response_model=ScriptDetail)
async def get_script(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get the script for a project."""
    return await _get_script(project_id, db)


@router.put("/projects/{project_id}/script", response_model=ScriptDetail)
async def update_script(
    project_id: int,
    body: ScriptUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Edit script metadata."""
    script = await _get_script(project_id, db)

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(script, key, value)

    await db.flush()
    await db.refresh(script, attribute_names=["episodes"])
    return script


@router.put("/projects/{project_id}/episodes/{episode_id}", response_model=ScriptDetail)
async def update_episode(
    project_id: int,
    episode_id: int,
    body: EpisodeUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Edit an episode's content."""
    episode = await db.get(Episode, episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(episode, key, value)

    await db.flush()
    return await _get_script(project_id, db)


@router.post("/projects/{project_id}/script/rewrite-narration", response_model=ScriptDetail)
async def rewrite_narration(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Rewrite script from dialogue to narration style."""
    script = await _get_script(project_id, db)

    # Collect all episode content
    all_content = "\n\n".join(
        ep.content for ep in script.episodes if ep.content
    )
    if not all_content:
        raise HTTPException(status_code=400, detail="No script content to rewrite")

    narration = await script_engine.rewrite_to_narration(all_content)

    # Update the first episode's content (or all if single-episode)
    if len(script.episodes) == 1:
        script.episodes[0].content = narration
    else:
        # For multi-episode, rewrite each separately (simplified: store in raw)
        script.raw_content = narration

    await db.flush()
    await db.refresh(script, attribute_names=["episodes"])
    return script


@router.post("/projects/{project_id}/script/approve", response_model=ScriptDetail)
async def approve_script(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Approve the script and advance project to Step 2 (Assets)."""
    script = await _get_script(project_id, db)

    script.is_approved = True
    for ep in script.episodes:
        ep.is_approved = True

    # Advance project status
    project = await _get_project(project_id, db)
    project.status = ProjectStep.ASSETS

    await db.flush()
    await db.refresh(script, attribute_names=["episodes"])
    return script