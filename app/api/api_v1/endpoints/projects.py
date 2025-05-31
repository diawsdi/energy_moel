from typing import List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.api import deps
from app.schemas.projects import (
    Project, ProjectCreate, ProjectUpdate,
    ProjectArea, ProjectAreaCreate, ProjectAreaUpdate,
    ProjectWithStats
)

router = APIRouter()


@router.post("/", response_model=Project)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(deps.get_db),
    current_user: str = Depends(deps.get_current_user),
) -> Project:
    """Create a new project."""
    db_project = Project(
        **project.dict(),
        created_by=current_user
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.get("/", response_model=List[Project])
def list_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: str = Depends(deps.get_current_user),
) -> List[Project]:
    """List all projects."""
    projects = db.query(Project).offset(skip).limit(limit).all()
    return projects


@router.get("/{project_id}", response_model=ProjectWithStats)
def get_project(
    project_id: str,
    db: Session = Depends(deps.get_db),
) -> ProjectWithStats:
    """Get a project by ID with statistics."""
    # Get project with basic info
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Calculate statistics for all areas in the project
    stats_query = """
    SELECT 
        COUNT(*) as total_buildings,
        SUM(CASE WHEN be.predicted_electrified = 1 THEN 1 ELSE 0 END) as electrified_buildings,
        SUM(CASE WHEN be.predicted_electrified = 0 OR be.predicted_electrified IS NULL THEN 1 ELSE 0 END) as unelectrified_buildings,
        AVG(be.consumption_kwh_month) as avg_consumption_kwh_month,
        AVG(be.energy_demand_kwh) as avg_energy_demand_kwh_year
    FROM project_areas pa
    JOIN buildings_energy be ON ST_Contains(pa.geometry, be.geom)
    WHERE pa.project_id = :project_id
    """
    
    stats = db.execute(text(stats_query), {"project_id": project_id}).fetchone()
    
    # Combine project info with statistics
    return ProjectWithStats(
        **project.__dict__,
        total_buildings=stats.total_buildings or 0,
        electrified_buildings=stats.electrified_buildings or 0,
        unelectrified_buildings=stats.unelectrified_buildings or 0,
        avg_consumption_kwh_month=stats.avg_consumption_kwh_month or 0,
        avg_energy_demand_kwh_year=stats.avg_energy_demand_kwh_year or 0
    )


@router.put("/{project_id}", response_model=Project)
def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    db: Session = Depends(deps.get_db),
    current_user: str = Depends(deps.get_current_user),
) -> Project:
    """Update a project."""
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    for field, value in project_update.dict(exclude_unset=True).items():
        setattr(db_project, field, value)
    
    db.commit()
    db.refresh(db_project)
    return db_project


@router.post("/{project_id}/areas", response_model=ProjectArea)
def add_project_area(
    project_id: str,
    area: ProjectAreaCreate,
    db: Session = Depends(deps.get_db),
) -> ProjectArea:
    """Add an area to a project."""
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create new area
    db_area = ProjectArea(
        **area.dict(),
        project_id=project_id
    )
    db.add(db_area)
    db.commit()
    db.refresh(db_area)
    return db_area


@router.put("/{project_id}/areas/{area_id}", response_model=ProjectArea)
def update_project_area(
    project_id: str,
    area_id: str,
    area_update: ProjectAreaUpdate,
    db: Session = Depends(deps.get_db),
) -> ProjectArea:
    """Update a project area."""
    db_area = (
        db.query(ProjectArea)
        .filter(ProjectArea.project_id == project_id, ProjectArea.id == area_id)
        .first()
    )
    if not db_area:
        raise HTTPException(status_code=404, detail="Project area not found")
    
    for field, value in area_update.dict(exclude_unset=True).items():
        setattr(db_area, field, value)
    
    db.commit()
    db.refresh(db_area)
    return db_area


@router.delete("/{project_id}/areas/{area_id}")
def delete_project_area(
    project_id: str,
    area_id: str,
    db: Session = Depends(deps.get_db),
) -> dict:
    """Delete a project area."""
    db_area = (
        db.query(ProjectArea)
        .filter(ProjectArea.project_id == project_id, ProjectArea.id == area_id)
        .first()
    )
    if not db_area:
        raise HTTPException(status_code=404, detail="Project area not found")
    
    db.delete(db_area)
    db.commit()
    return {"status": "success"} 