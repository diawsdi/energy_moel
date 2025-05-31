from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from app.api import deps

router = APIRouter()

class VillageSearchResult(BaseModel):
    id: str
    display_name: str  # Will contain "village name - (commune name)"
    name: str
    commune_name: str
    longitude: float
    latitude: float

@router.get("/search", response_model=List[VillageSearchResult])
def search_villages(
    query: str = Query(..., description="Search text for village name"),
    limit: int = Query(10, description="Maximum number of results to return"),
    db: Session = Depends(deps.get_db),
) -> List[VillageSearchResult]:
    """
    Search for villages by name, returns results with commune information.
    The display name will be in the format: 'Village Name - (Commune Name)'
    """
    search_query = text("""
        SELECT 
            v.id,
            v.name as village_name,
            a.name as commune_name,
            ST_X(v.geometry) as longitude,
            ST_Y(v.geometry) as latitude
        FROM village_points v
        JOIN administrative_boundaries a ON ST_Contains(a.geom, v.geometry)
        WHERE 
            a.level = 'commune'
            AND (
                unaccent(v.name) ILIKE unaccent(:search)
                OR unaccent(v.name) ILIKE unaccent(:partial_search)
            )
        ORDER BY 
            CASE 
                WHEN unaccent(v.name) ILIKE unaccent(:search) THEN 0 
                ELSE 1 
            END,
            length(v.name)
        LIMIT :limit
    """)
    
    results = db.execute(
        search_query,
        {
            "search": f"{query}",
            "partial_search": f"%{query}%",
            "limit": limit
        }
    ).fetchall()
    
    return [
        VillageSearchResult(
            id=row.id,
            name=row.village_name,
            commune_name=row.commune_name,
            display_name=f"{row.village_name} - ({row.commune_name})",
            longitude=row.longitude,
            latitude=row.latitude
        )
        for row in results
    ] 