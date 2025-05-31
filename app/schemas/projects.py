from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ProjectAreaBase(BaseModel):
    name: str
    area_type: str  # 'village' or 'custom'
    geometry: dict  # GeoJSON MultiPolygon format
    reference_village_id: Optional[str] = None
    metadata: Optional[dict] = None


class ProjectAreaCreate(ProjectAreaBase):
    pass


class ProjectAreaUpdate(ProjectAreaBase):
    name: Optional[str] = None
    area_type: Optional[str] = None
    geometry: Optional[dict] = None


class ProjectArea(ProjectAreaBase):
    id: str
    project_id: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    organization_type: str  # 'government' or 'private'


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(ProjectBase):
    name: Optional[str] = None
    organization_type: Optional[str] = None
    status: Optional[str] = None


class Project(ProjectBase):
    id: str
    status: str
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime]
    areas: List[ProjectArea]

    class Config:
        from_attributes = True


class ProjectWithStats(Project):
    total_buildings: int
    electrified_buildings: int
    unelectrified_buildings: int
    avg_consumption_kwh_month: float
    avg_energy_demand_kwh_year: float 