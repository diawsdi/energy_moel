from fastapi import APIRouter

from app.api.api_v1.endpoints import buildings, metrics, villages, projects, project_uploads, project_areas_enhanced

api_router = APIRouter()
api_router.include_router(buildings.router, prefix="/buildings", tags=["buildings"]) 
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"]) 
api_router.include_router(villages.router, prefix="/villages", tags=["villages"]) 
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(project_uploads.router, prefix="/projects", tags=["project-uploads"])
api_router.include_router(project_areas_enhanced.router, prefix="/projects", tags=["project-areas-enhanced"])
