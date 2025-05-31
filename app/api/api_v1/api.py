from fastapi import APIRouter

from app.api.api_v1.endpoints import buildings, metrics, villages

api_router = APIRouter()
api_router.include_router(buildings.router, prefix="/buildings", tags=["buildings"]) 
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"]) 
api_router.include_router(villages.router, prefix="/villages", tags=["villages"]) 