"""
DramaForge v2.0 — Projects API
================================
CRUD endpoints for project management.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectList, ProjectDetail

router = APIRouter()


@router.post("/projects", response_model=ProjectDetail, status_code=201)
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new project."""
    project = Project(**body.model_dump())
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


@router.get("/projects", response_model=list[ProjectList])
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List all projects with pagination."""
    stmt = (
        select(Project)
        .order_by(Project.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/projects/{project_id}", response_model=ProjectDetail)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get project details by ID."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/projects/{project_id}", response_model=ProjectDetail)
async def update_project(
    project_id: int,
    body: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a project."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)

    await db.flush()
    await db.refresh(project)
    return project


@router.post("/projects/seed-examples", response_model=list[ProjectDetail])
async def seed_example_projects(
    db: AsyncSession = Depends(get_db),
):
    """
    Create example projects for demonstration.
    Idempotent: skips if example projects already exist.
    """
    # Check if examples already exist
    result = await db.execute(
        select(Project).where(Project.title.like("从弃女到巅峰%"))
    )
    if result.scalar_one_or_none():
        # Return all existing projects
        all_result = await db.execute(
            select(Project).order_by(Project.updated_at.desc()).limit(10)
        )
        return all_result.scalars().all()

    examples = [
        Project(
            title="从弃女到巅峰：苏家千金归来",
            description="苏家千金被陷害沦为弃女，凭借智慧与毅力一步步重回巅峰，揭开惊天阴谋。",
            style="realistic",
            genre="revenge",
            status="assets",
            script_type="dialogue",
            aspect_ratio="9:16",
        ),
        Project(
            title="末世：我以为我是废柴，其实我是神",
            description="末世来临，被所有人看不起的废柴觉醒了最强能力，逆天改命。",
            style="cinematic",
            genre="fantasy",
            status="script",
            script_type="dialogue",
            aspect_ratio="9:16",
        ),
        Project(
            title="都市大圣：战神觉醒",
            description="退伍战神重回都市，面对家族危机和商业阴谋，以雷霆手段守护至亲。",
            style="realistic",
            genre="urban",
            status="script",
            script_type="dialogue",
            aspect_ratio="9:16",
        ),
    ]

    for proj in examples:
        db.add(proj)
    await db.flush()

    for proj in examples:
        await db.refresh(proj)

    return examples


@router.delete("/projects/{project_id}", status_code=204)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a project and all related data."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await db.delete(project)
    await db.flush()
