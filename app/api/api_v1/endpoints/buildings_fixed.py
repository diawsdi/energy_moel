from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from geoalchemy2.shape import to_shape
from geoalchemy2 import WKTElement
from shapely.geometry import box, Point
import json

from app import schemas
from app.models.buildings_energy import BuildingsEnergy
from app.db.deps import get_db

router = APIRouter()


@router.get("/", response_model=List[schemas.Building])
def read_buildings(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    year: Optional[int] = None,
    has_access: Optional[bool] = None,
    building_type: Optional[str] = None,
) -> Any:
    """
    Retrieve buildings with pagination and filtering.
    """
    query = db.query(BuildingsEnergy)
    
    # Apply filters
    if year:
        query = query.filter(BuildingsEnergy.year == year)
    if has_access is not None:
        query = query.filter(BuildingsEnergy.has_access == has_access)
    if building_type:
        query = query.filter(BuildingsEnergy.building_type == building_type)
    
    buildings = query.offset(skip).limit(limit).all()
    
    # Convert to GeoJSON
    result = []
    for building in buildings:
        building_dict = {c.name: getattr(building, c.name) for c in building.__table__.columns if c.name != 'geom'}
        # Convert geometry to WKT format
        shape = to_shape(building.geom)
        building_dict["geom"] = shape.wkt
        result.append(building_dict)
    
    return result


@router.get("/bbox", response_model=List[schemas.Building])
def read_buildings_in_bbox(
    minx: float = Query(..., description="Minimum longitude"),
    miny: float = Query(..., description="Minimum latitude"),
    maxx: float = Query(..., description="Maximum longitude"),
    maxy: float = Query(..., description="Maximum latitude"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> Any:
    """
    Retrieve buildings within a bounding box.
    """
    # Create a bounding box
    bbox = box(minx, miny, maxx, maxy)
    wkt_bbox = WKTElement(bbox.wkt, srid=4326)
    
    # Query buildings within the bounding box
    query = db.query(BuildingsEnergy).filter(
        func.ST_Intersects(BuildingsEnergy.geom, wkt_bbox)
    )
    
    buildings = query.offset(skip).limit(limit).all()
    
    # Convert to GeoJSON
    result = []
    for building in buildings:
        building_dict = {c.name: getattr(building, c.name) for c in building.__table__.columns if c.name != 'geom'}
        # Convert geometry to WKT format
        shape = to_shape(building.geom)
        building_dict["geom"] = shape.wkt
        result.append(building_dict)
    
    return result


@router.get("/stats", response_model=schemas.BuildingStats)
def get_buildings_statistics(
    db: Session = Depends(get_db),
    year: Optional[int] = None,
) -> Any:
    """
    Get statistics about buildings.
    """
    query = db.query(BuildingsEnergy)
    
    # Apply year filter if provided
    if year:
        query = query.filter(BuildingsEnergy.year == year)
    
    # Count total buildings
    total_count = query.count()
    
    # Count buildings by type
    building_types = (
        db.query(
            BuildingsEnergy.building_type,
            func.count(BuildingsEnergy.id).label("count")
        )
        .filter(BuildingsEnergy.building_type.isnot(None))
        .group_by(BuildingsEnergy.building_type)
        .all()
    )
    
    # Count buildings by access
    access_counts = (
        db.query(
            BuildingsEnergy.has_access,
            func.count(BuildingsEnergy.id).label("count")
        )
        .group_by(BuildingsEnergy.has_access)
        .all()
    )
    
    return {
        "total_count": total_count,
        "building_types": {bt.building_type: bt.count for bt in building_types},
        "access_counts": {
            "has_access": next((ac.count for ac in access_counts if ac.has_access), 0),
            "no_access": next((ac.count for ac in access_counts if not ac.has_access), 0)
        }
    }
