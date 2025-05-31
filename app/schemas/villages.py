from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class VillagePointBase(BaseModel):
    name: str
    commune_id: str
    geometry: dict  # GeoJSON Point format


class VillagePointCreate(VillagePointBase):
    pass


class VillagePointUpdate(VillagePointBase):
    name: Optional[str] = None
    commune_id: Optional[str] = None
    geometry: Optional[dict] = None


class VillagePoint(VillagePointBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class AdminBoundaryInfo(BaseModel):
    id: str
    name: str
    level: str


class VillagePointSearch(BaseModel):
    id: str = Field(..., description="Unique identifier of the village")
    name: str = Field(..., description="Name of the village")
    geometry: dict = Field(..., description="GeoJSON Point geometry of the village")
    distance_km: Optional[float] = Field(None, description="Distance from search point in kilometers")
    
    # Administrative boundary information
    commune: AdminBoundaryInfo = Field(..., description="Commune information")
    arrondissement: Optional[AdminBoundaryInfo] = Field(None, description="Arrondissement information")
    department: Optional[AdminBoundaryInfo] = Field(None, description="Department information")
    region: Optional[AdminBoundaryInfo] = Field(None, description="Region information")


class VillageSearchResponse(BaseModel):
    total: int = Field(..., description="Total number of villages matching the search criteria")
    items: List[VillagePointSearch] = Field(..., description="List of villages") 