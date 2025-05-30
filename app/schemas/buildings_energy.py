from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from shapely.geometry import MultiPolygon
import json

class GeometryModel(BaseModel):
    type: str = "MultiPolygon"
    coordinates: List[List[List[List[float]]]]

class BuildingBase(BaseModel):
    area_in_meters: Optional[float] = None
    year: int
    energy_demand_kwh: Optional[float] = None
    has_access: Optional[bool] = None
    building_type: Optional[str] = None
    data_source: Optional[str] = None
    grid_node_id: Optional[str] = None
    origin_id: Optional[str] = None

    # ML prediction fields
    predicted_prob: Optional[float] = None
    predicted_electrified: Optional[int] = None
    
    # Energy consumption fields
    consumption_kwh_month: Optional[float] = None
    std_consumption_kwh_month: Optional[float] = None
    
    # Origin information
    origin: Optional[str] = None

class BuildingCreate(BuildingBase):
    geom: Dict[str, Any]  # GeoJSON-like structure

class BuildingUpdate(BuildingBase):
    geom: Optional[Dict[str, Any]] = None

class BuildingInDBBase(BuildingBase):
    id: int
    geom: str  # WKT representation
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class Building(BuildingInDBBase):
    pass

class BuildingInDB(BuildingInDBBase):
    pass

class BuildingMetadata(BaseModel):
    total_count: int
    has_access_count: int
    no_access_count: int
    avg_energy_demand: float
    min_energy_demand: float
    max_energy_demand: float
    year_distribution: Dict[int, int]
    electrified_count: Optional[int] = None
    avg_consumption_kwh_month: Optional[float] = None
    high_confidence_electrified: Optional[int] = None  # buildings with high prediction probability

# For statistics
class BuildingStats(BaseModel):
    total_count: int
    building_types: Dict[str, int]
    access_counts: Dict[str, int]
    electrification_rate: Optional[float] = None
    avg_consumption: Optional[float] = None
    confidence_levels: Optional[Dict[str, int]] = None
    
    class Config:
        orm_mode = True

# For spatial queries
class BoundingBox(BaseModel):
    minx: float = Field(..., description="Minimum X coordinate (longitude)")
    miny: float = Field(..., description="Minimum Y coordinate (latitude)")
    maxx: float = Field(..., description="Maximum X coordinate (longitude)")
    maxy: float = Field(..., description="Maximum Y coordinate (latitude)")
    srid: int = Field(4326, description="Spatial Reference System ID")

class SpatialFilter(BaseModel):
    bbox: Optional[BoundingBox] = None
    distance: Optional[float] = None
    point: Optional[List[float]] = None  # [lon, lat] 