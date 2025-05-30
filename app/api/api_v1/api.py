from fastapi import APIRouter

from app.api.api_v1.endpoints import buildings, metrics

api_router = APIRouter()
api_router.include_router(buildings.router, prefix="/buildings", tags=["buildings"]) 
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"]) 