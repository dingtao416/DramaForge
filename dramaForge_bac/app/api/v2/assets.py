"""
DramaForge v2.0 — Assets API
==============================
Endpoints for character/scene asset generation, editing, and management.
Also includes global asset library endpoints (Spec 18).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Form
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
from app.services.user_model_resolver import user_model_resolver
from app.core.security import CurrentUser, DbSession
from app.core.billing_deps import require_credits
from app.models.character import CharacterRole
from app.services.storage import storage as storage_service

router = APIRouter()

MAX_IMAGE_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_ASSET_UPLOAD_BYTES = 50 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
ALLOWED_IMAGE_CONTENT_TYPES = {"image/png", "image/jpeg", "image/webp"}
ALLOWED_ASSET_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "mp4", "mov", "webm"}
ALLOWED_ASSET_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/webp",
    "video/mp4",
    "video/quicktime",
    "video/webm",
}


def _media_options(resolved) -> dict:
    if not resolved.provider_type:
        return {}
    return {
        "provider_type": resolved.provider_type,
        "auth_type": resolved.auth_type or "bearer",
        "headers": resolved.headers or {},
        "config": resolved.config or {},
        "raw_params": resolved.raw_params or {},
    }


async def _read_upload_limited(file: UploadFile, max_bytes: int) -> bytes:
    content = bytearray()
    while chunk := await file.read(1024 * 1024):
        content.extend(chunk)
        if len(content) > max_bytes:
            raise HTTPException(status_code=413, detail="Uploaded file is too large")
    return bytes(content)


def _validated_upload_extension(
    file: UploadFile,
    allowed_extensions: set[str],
    allowed_content_types: set[str],
) -> str:
    ext = (file.filename or "").rsplit(".", 1)[-1].lower() if file.filename else ""
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Unsupported file extension")
    if file.content_type not in allowed_content_types:
        raise HTTPException(status_code=400, detail="Unsupported file content type")
    return ext


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

    # Resolve user's chat + image models
    chat_resolved = await user_model_resolver.resolve(db, user.id, "chat")
    image_resolved = await user_model_resolver.resolve(db, user.id, "image")

    # Generate assets
    updated_chars, updated_scenes = await assets_engine.generate_all_assets(
        script=script,
        characters=characters,
        scenes=scenes,
        project_id=project_id,
        chat_model=chat_resolved.model_id,
        chat_api_key=chat_resolved.api_key,
        chat_base_url=chat_resolved.base_url,
        image_model=image_resolved.model_id,
        image_api_key=image_resolved.api_key,
        image_base_url=image_resolved.base_url,
        image_options=_media_options(image_resolved),
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

    # Resolve user's image model & credentials
    resolved = await user_model_resolver.resolve(db, user.id, "image")

    await assets_engine.regenerate_character_image(
        character=character,
        project_id=project_id,
        prompt=body.prompt,
        variant_count=body.variant_count,
        image_model=resolved.model_id,
        image_api_key=resolved.api_key,
        image_base_url=resolved.base_url,
        image_options=_media_options(resolved),
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

    # Resolve user's image model & credentials
    resolved = await user_model_resolver.resolve(db, user.id, "image")

    await assets_engine.regenerate_scene_image(
        scene=scene,
        project_id=project_id,
        prompt=body.prompt,
        variant_count=body.variant_count,
        image_model=resolved.model_id,
        image_api_key=resolved.api_key,
        image_base_url=resolved.base_url,
        image_options=_media_options(resolved),
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


@router.post("/assets/characters", response_model=CharacterDetail, status_code=201)
async def create_global_character(
    name: str = Form(...),
    project_id: int = Form(...),
    description: str = Form(""),
    role: str = Form("extra"),
    gender: str = Form(""),
    age: str = Form(""),
    image: UploadFile | None = File(None),
    user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
):
    """Create a new character in the global library (requires project context)."""
    # Validate project exists
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Resolve role
    try:
        char_role = CharacterRole(role)
    except ValueError:
        char_role = CharacterRole.EXTRA

    # Build character description
    desc_parts = [description]
    if gender:
        desc_parts.insert(0, f"性别：{gender}")
    if age:
        desc_parts.insert(0, f"年龄：{age}")
    full_desc = "；".join(filter(None, desc_parts))

    # Save image if provided
    image_urls: list[str] = []
    if image and image.filename:
        ext = _validated_upload_extension(
            image,
            ALLOWED_IMAGE_EXTENSIONS,
            ALLOWED_IMAGE_CONTENT_TYPES,
        )
        img_bytes = await _read_upload_limited(image, MAX_IMAGE_UPLOAD_BYTES)
        # Store in project path
        import uuid
        img_path = storage_service.project_path(project_id) / f"char_{uuid.uuid4().hex[:8]}.{ext}"
        img_path.parent.mkdir(parents=True, exist_ok=True)
        img_path.write_bytes(img_bytes)
        image_urls.append(storage_service.get_url(str(img_path)))

    character = Character(
        project_id=project_id,
        name=name.strip(),
        role=char_role,
        description=full_desc,
        reference_images=image_urls,
    )
    db.add(character)
    await db.flush()
    await db.refresh(character)
    return character


@router.post("/assets/upload", status_code=201)
async def upload_global_asset(
    project_id: int = Form(...),
    file: UploadFile = File(...),
    name: str = Form(""),
    asset_type: str = Form("character"),
    user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
):
    """Upload an image/video asset to the global library."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if asset_type not in {"character", "scene"}:
        raise HTTPException(status_code=400, detail="asset_type must be character or scene")

    # Save file
    import uuid
    ext = _validated_upload_extension(
        file,
        ALLOWED_ASSET_EXTENSIONS,
        ALLOWED_ASSET_CONTENT_TYPES,
    )
    fname = f"upload_{uuid.uuid4().hex[:8]}.{ext}"
    file_path = storage_service.project_path(project_id) / fname
    file_path.parent.mkdir(parents=True, exist_ok=True)
    content = await _read_upload_limited(file, MAX_ASSET_UPLOAD_BYTES)
    file_path.write_bytes(content)
    url = storage_service.get_url(str(file_path))

    # Create character or scene record
    display_name = name.strip() or file.filename.rsplit(".", 1)[0]
    if asset_type == "scene":
        asset = SceneLocation(
            project_id=project_id,
            name=display_name,
            reference_images=[url],
        )
    else:
        asset = Character(
            project_id=project_id,
            name=display_name,
            role=CharacterRole.EXTRA,
            reference_images=[url],
        )
    db.add(asset)
    await db.flush()
    await db.refresh(asset)

    return {"id": asset.id, "name": display_name, "url": url, "type": asset_type}


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
