"""
DramaForge - Projects API
REST API endpoints for project management.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.database import (
    DramaGenre,
    Project,
    ProjectStatus,
    get_db,
)

router = APIRouter(prefix="/api/projects", tags=["projects"])


# ==================== Schemas ====================

class ProjectCreate(BaseModel):
    title: str
    description: Optional[str] = None
    genre: DramaGenre = DramaGenre.OTHER
    target_duration: int = 60
    target_episodes: int = 1
    style_prompt: Optional[str] = None
    llm_provider: Optional[str] = None


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    genre: Optional[DramaGenre] = None
    target_duration: Optional[int] = None
    target_episodes: Optional[int] = None
    style_prompt: Optional[str] = None
    llm_provider: Optional[str] = None


class ProjectResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    genre: str
    status: str
    target_duration: int
    target_episodes: int
    style_prompt: Optional[str]
    llm_provider: Optional[str]

    class Config:
        from_attributes = True


# ==================== Endpoints ====================

@router.post("/", response_model=ProjectResponse)
async def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new short drama project."""
    project = Project(
        title=data.title,
        description=data.description,
        genre=data.genre,
        target_duration=data.target_duration,
        target_episodes=data.target_episodes,
        style_prompt=data.style_prompt,
        llm_provider=data.llm_provider,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/", response_model=list[ProjectResponse])
async def list_projects(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all projects, optionally filtered by status."""
    query = db.query(Project)
    if status:
        query = query.filter(Project.status == status)
    return query.order_by(Project.id.desc()).all()


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, db: Session = Depends(get_db)):
    """Get a single project by ID."""
    project = db.query(Project).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
):
    """Update a project."""
    project = db.query(Project).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}")
async def delete_project(project_id: int, db: Session = Depends(get_db)):
    """Delete a project and all related data."""
    project = db.query(Project).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()
    return {"message": f"Project {project_id} deleted"}
