from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from geoalchemy2.elements import WKBElement


class ProjectAreaBase(BaseModel):
    name: str
    area_type: str  # 'village' or 'custom'
    geometry: dict  # GeoJSON MultiPolygon format
    metadata: Optional[dict] = None
    source_type: Optional[str] = None  # 'drawn', 'geojson_upload', 'shapefile'


class ProjectAreaCreate(ProjectAreaBase):
    original_filename: Optional[str] = None
    simplification_tolerance: Optional[float] = None


class ProjectAreaUpdate(ProjectAreaBase):
    name: Optional[str] = None
    area_type: Optional[str] = None
    geometry: Optional[dict] = None
    source_type: Optional[str] = None
    metadata: Optional[dict] = None
    original_filename: Optional[str] = None
    simplification_tolerance: Optional[float] = None


class ProjectArea(ProjectAreaBase):
    id: str
    project_id: str
    original_filename: Optional[str] = None
    processing_status: Optional[str] = None
    simplification_tolerance: Optional[float] = None
    area_sq_km: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
    
    @validator('geometry', pre=True)
    def validate_geometry(cls, v):
        if isinstance(v, WKBElement):
            from shapely import wkb
            from shapely.geometry import mapping
            try:
                geom = wkb.loads(bytes(v.data))
                return mapping(geom)
            except Exception as e:
                print(f"Error converting WKBElement to GeoJSON: {e}")
                return {}
        return v
        
    @validator('metadata', pre=True)
    def validate_metadata(cls, v):
        if v is None:
            return {}
        if hasattr(v, 'items'):
            return dict(v)
        # Handle area_metadata from SQLAlchemy model
        if hasattr(v, 'area_metadata'):
            metadata = v.area_metadata
            if metadata is None:
                return {}
            if hasattr(metadata, 'items'):
                return dict(metadata)
        return {}


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


class ProjectAreaWithStats(ProjectArea):
    total_buildings: int
    electrified_buildings: int
    unelectrified_buildings: int
    avg_consumption_kwh_month: float
    avg_energy_demand_kwh_year: float 