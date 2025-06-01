import uuid
import json
import os
import tempfile
import shutil
from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from geoalchemy2.shape import from_shape
from shapely.geometry import shape, mapping

from app.api import deps
from app.models.projects import Project as ProjectModel, ProjectArea as ProjectAreaModel
from app.schemas.projects import (
    Project, ProjectCreate, ProjectUpdate,
    ProjectArea, ProjectAreaCreate, ProjectAreaUpdate,
    ProjectWithStats, ProjectAreaWithStats
)

router = APIRouter()


@router.post("/", response_model=Project)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(deps.get_db),
    current_user: str = Depends(deps.get_current_user),
) -> Project:
    """Create a new project."""
    db_project = ProjectModel(
        id=str(uuid.uuid4()),
        **project.dict(),
        created_by=current_user,
        status="draft",
        updated_at=func.now()
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
    projects = db.query(ProjectModel).offset(skip).limit(limit).all()
    
    # Process projects to handle special fields
    for project in projects:
        if hasattr(project, 'areas') and project.areas:
            for area in project.areas:
                # Convert WKBElement to GeoJSON dict
                if hasattr(area.geometry, '__geo_interface__'):
                    area.geometry = mapping(area.geometry)
                
                # Ensure metadata is a dict
                if area.area_metadata is None:
                    area.area_metadata = {}
    
    return projects


@router.get("/{project_id}", response_model=Project)
def get_project(
    project_id: str,
    db: Session = Depends(deps.get_db),
) -> Project:
    """Get a project by ID."""
    # Get project with basic info
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project


@router.get("/{project_id}/stats", response_model=ProjectWithStats)
def get_project_stats(
    project_id: str,
    db: Session = Depends(deps.get_db),
) -> ProjectWithStats:
    """Get statistics for a project."""
    # Get project with basic info
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
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
    db_project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    for field, value in project_update.dict(exclude_unset=True).items():
        setattr(db_project, field, value)
    
    db.commit()
    db.refresh(db_project)
    return db_project


@router.get("/{project_id}/areas", response_model=List[ProjectArea])
def get_project_areas(
    project_id: str,
    db: Session = Depends(deps.get_db),
) -> List[ProjectArea]:
    """Get all areas for a project."""
    # Verify project exists
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get all areas for the project
    areas = db.query(ProjectAreaModel).filter(ProjectAreaModel.project_id == project_id).all()
    return areas


@router.post("/{project_id}/areas", response_model=Union[ProjectArea, List[ProjectArea]])
def add_project_area(
    project_id: str,
    area: ProjectAreaCreate,
    db: Session = Depends(deps.get_db),
) -> Union[ProjectArea, List[ProjectArea]]:
    """Add an area to a project using direct GeoJSON input."""
    # Verify project exists
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Extract geometries from the input
    geometries = []
    
    # Check if we have a FeatureCollection
    if area.geometry.get("type") == "FeatureCollection":
        if area.geometry.get("features") and len(area.geometry["features"]) > 0:
            for feature in area.geometry["features"]:
                if feature.get("geometry"):
                    geometries.append(feature.get("geometry"))
    # Check if we have a Feature
    elif area.geometry.get("type") == "Feature":
        if area.geometry.get("geometry"):
            geometries.append(area.geometry.get("geometry"))
    # Check if we have a direct geometry
    elif "type" in area.geometry and area.geometry["type"] in ["Polygon", "MultiPolygon"]:
        geometries.append(area.geometry)
    
    # Validate we have at least one geometry
    if not geometries:
        raise HTTPException(status_code=400, detail="Invalid geometry format or no geometries found")
    
    # Import required libraries
    import json
    from shapely.geometry import shape, mapping, Polygon, MultiPolygon
    from shapely.ops import unary_union
    from geoalchemy2.shape import from_shape
    import shapely.wkt
    
    # Create areas for each geometry
    created_areas = []
    
    for i, geometry in enumerate(geometries):
        # Calculate area in square kilometers
        area_sq_km = None
        try:
            # Use PostGIS to calculate area
            geom_shape = shape(geometry)
            # Convert to geography type for accurate area calculation in square meters
            area_query = db.execute(
                text("SELECT ST_Area(ST_Transform(ST_GeomFromGeoJSON(:geojson), 3857))/1000000 as area_sq_km"),
                {"geojson": json.dumps(geometry)}
            ).fetchone()
            area_sq_km = area_query.area_sq_km if area_query else None
        except Exception as e:
            # Log the error but continue
            print(f"Error calculating area: {e}")
        
        # Create a shapely geometry from the GeoJSON
        geom_shape = shape(geometry)
        
        # Convert to MultiPolygon if it's a Polygon
        if isinstance(geom_shape, Polygon):
            geom_shape = MultiPolygon([geom_shape])
        
        # Create WKB element for database storage
        wkb_element = from_shape(geom_shape, srid=4326)  # Use SRID 4326 for WGS84
        
        # Create area dict excluding geometry and metadata which we'll handle separately
        area_dict = area.dict(exclude={'geometry', 'metadata'})
        
        # Create area name with index if multiple geometries
        if len(geometries) > 1:
            area_dict["name"] = f"{area_dict['name']} ({i+1})"
        
        # Update metadata to include feature index if multiple geometries
        metadata = area.metadata or {}
        if len(geometries) > 1:
            metadata["feature_index"] = i
        
        # Create new area
        db_area = ProjectAreaModel(
            id=str(uuid.uuid4()),
            **area_dict,
            geometry=wkb_element,  # Use the converted geometry
            area_metadata=metadata,  # Map metadata to area_metadata
            project_id=project_id,
            processing_status="completed",
            area_sq_km=area_sq_km,
            updated_at=func.now()
        )
        db.add(db_area)
        created_areas.append(db_area)
    
    # Commit all areas at once
    db.commit()
    
    # Refresh all areas to get their created_at timestamps
    for area in created_areas:
        db.refresh(area)
    
    # If only one area was created, return it as an object
    # Otherwise return the list of areas
    if len(created_areas) == 1:
        return created_areas[0]
    else:
        return created_areas


@router.get("/{project_id}/areas/{area_id}", response_model=ProjectArea)
def get_project_area(
    project_id: str,
    area_id: str,
    db: Session = Depends(deps.get_db),
) -> ProjectArea:
    """Get a specific project area by ID."""
    db_area = (
        db.query(ProjectAreaModel)
        .filter(ProjectAreaModel.project_id == project_id, ProjectAreaModel.id == area_id)
        .first()
    )
    if not db_area:
        raise HTTPException(status_code=404, detail="Project area not found")
    
    return db_area


@router.get("/{project_id}/areas/{area_id}/stats", response_model=ProjectAreaWithStats)
def get_project_area_stats(
    project_id: str,
    area_id: str,
    db: Session = Depends(deps.get_db),
) -> ProjectAreaWithStats:
    """Get statistics for a specific project area."""
    # Get the project area
    db_area = (
        db.query(ProjectAreaModel)
        .filter(ProjectAreaModel.project_id == project_id, ProjectAreaModel.id == area_id)
        .first()
    )
    if not db_area:
        raise HTTPException(status_code=404, detail="Project area not found")
    
    # Calculate statistics for the area
    stats_query = """
    SELECT 
        COUNT(*) as total_buildings,
        SUM(CASE WHEN be.predicted_electrified = 1 THEN 1 ELSE 0 END) as electrified_buildings,
        SUM(CASE WHEN be.predicted_electrified = 0 OR be.predicted_electrified IS NULL THEN 1 ELSE 0 END) as unelectrified_buildings,
        AVG(be.consumption_kwh_month) as avg_consumption_kwh_month,
        AVG(be.energy_demand_kwh) as avg_energy_demand_kwh_year
    FROM buildings_energy be
    WHERE ST_Contains(ST_GeomFromGeoJSON(:geometry), be.geom)
    """
    
    stats = db.execute(
        text(stats_query), 
        {"geometry": json.dumps(db_area.geometry)}
    ).fetchone()
    
    # Combine area info with statistics
    return ProjectAreaWithStats(
        **db_area.__dict__,
        total_buildings=stats.total_buildings or 0,
        electrified_buildings=stats.electrified_buildings or 0,
        unelectrified_buildings=stats.unelectrified_buildings or 0,
        avg_consumption_kwh_month=stats.avg_consumption_kwh_month or 0,
        avg_energy_demand_kwh_year=stats.avg_energy_demand_kwh_year or 0
    )


@router.put("/{project_id}/areas/{area_id}", response_model=ProjectArea)
def update_project_area(
    project_id: str,
    area_id: str,
    area_update: ProjectAreaUpdate,
    db: Session = Depends(deps.get_db),
) -> ProjectArea:
    """Update a project area."""
    db_area = (
        db.query(ProjectAreaModel)
        .filter(ProjectAreaModel.project_id == project_id, ProjectAreaModel.id == area_id)
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
        db.query(ProjectAreaModel)
        .filter(ProjectAreaModel.project_id == project_id, ProjectAreaModel.id == area_id)
        .first()
    )
    if not db_area:
        raise HTTPException(status_code=404, detail="Project area not found")
    
    db.delete(db_area)
    db.commit()
    return {"status": "success"} 


@router.post("/{project_id}/areas/geojson-upload", response_model=ProjectArea)
async def upload_geojson_area(
    project_id: str,
    name: str = Form(...),
    area_type: str = Form(...),
    file: UploadFile = File(...),
    simplify: Optional[bool] = Form(False),
    simplification_tolerance: Optional[float] = Form(None),
    db: Session = Depends(deps.get_db),
) -> ProjectArea:
    """Upload a GeoJSON file to create a new project area.
    
    Accepts GeoJSON files containing Feature or FeatureCollection with Polygon or MultiPolygon geometries.
    """
    # Verify project exists
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Validate file extension
    if not file.filename.lower().endswith('.geojson') and not file.filename.lower().endswith('.json'):
        raise HTTPException(status_code=400, detail="File must be a GeoJSON file (.geojson or .json)")
    
    # Read and parse the GeoJSON file
    try:
        contents = await file.read()
        geojson_data = json.loads(contents)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid GeoJSON file: {str(e)}")
    
    # Extract geometry from GeoJSON
    geometry = None
    if geojson_data.get('type') == 'FeatureCollection':
        # Extract first feature with a valid geometry
        for feature in geojson_data.get('features', []):
            if feature.get('geometry', {}).get('type') in ['Polygon', 'MultiPolygon']:
                geometry = feature['geometry']
                break
    elif geojson_data.get('type') == 'Feature':
        if geojson_data.get('geometry', {}).get('type') in ['Polygon', 'MultiPolygon']:
            geometry = geojson_data['geometry']
    elif geojson_data.get('type') in ['Polygon', 'MultiPolygon']:
        geometry = geojson_data
    
    if not geometry:
        raise HTTPException(status_code=400, detail="No valid Polygon or MultiPolygon geometry found in GeoJSON")
    
    # Convert to MultiPolygon if it's a Polygon
    if geometry['type'] == 'Polygon':
        geometry = {
            'type': 'MultiPolygon',
            'coordinates': [geometry['coordinates']]
        }
    
    # Apply simplification if requested
    if simplify and simplification_tolerance:
        try:
            geom_shape = shape(geometry)
            simplified_shape = geom_shape.simplify(simplification_tolerance, preserve_topology=True)
            geometry = mapping(simplified_shape)
        except Exception as e:
            # Log the error but continue with original geometry
            print(f"Error simplifying geometry: {e}")
    
    # Calculate area in square kilometers
    area_sq_km = None
    try:
        # Use PostGIS to calculate area
        area_query = db.execute(
            text("SELECT ST_Area(ST_Transform(ST_GeomFromGeoJSON(:geojson), 3857))/1000000 as area_sq_km"),
            {"geojson": json.dumps(geometry)}
        ).fetchone()
        area_sq_km = area_query.area_sq_km if area_query else None
    except Exception as e:
        # Log the error but continue
        print(f"Error calculating area: {e}")
    
    # Create new area
    db_area = ProjectAreaModel(
        id=str(uuid.uuid4()),
        project_id=project_id,
        name=name,
        area_type=area_type,
        geometry=geometry,
        source_type="geojson_upload",
        original_filename=file.filename,
        processing_status="completed",
        simplification_tolerance=simplification_tolerance if simplify else None,
        area_sq_km=area_sq_km,
        metadata={}
    )
    db.add(db_area)
    db.commit()
    db.refresh(db_area)
    return db_area


@router.post("/{project_id}/areas/shapefile-upload", response_model=ProjectArea)
async def upload_shapefile_area(
    project_id: str,
    name: str = Form(...),
    area_type: str = Form(...),
    file: UploadFile = File(...),
    simplify: Optional[bool] = Form(False),
    simplification_tolerance: Optional[float] = Form(None),
    db: Session = Depends(deps.get_db),
) -> ProjectArea:
    """Upload a zipped shapefile to create a new project area.
    
    Accepts zipped shapefiles containing polygon geometries.
    The zip file should contain at least .shp, .shx, and .dbf files.
    """
    # Verify project exists
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Validate file extension
    if not file.filename.lower().endswith('.zip'):
        raise HTTPException(status_code=400, detail="File must be a zipped shapefile (.zip)")
    
    # Create a temporary directory to extract the shapefile
    temp_dir = tempfile.mkdtemp()
    try:
        # Save the uploaded zip file
        zip_path = os.path.join(temp_dir, file.filename)
        with open(zip_path, "wb") as buffer:
            contents = await file.read()
            buffer.write(contents)
        
        # Extract the zip file
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find the .shp file
        shp_files = [f for f in os.listdir(temp_dir) if f.lower().endswith('.shp')]
        if not shp_files:
            raise HTTPException(status_code=400, detail="No .shp file found in the zip archive")
        
        # Read the shapefile using Fiona
        import fiona
        from fiona.crs import from_epsg
        
        shp_path = os.path.join(temp_dir, shp_files[0])
        with fiona.open(shp_path) as source:
            # Check if the shapefile contains polygon features
            if source.schema['geometry'] not in ['Polygon', 'MultiPolygon']:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Shapefile must contain Polygon or MultiPolygon geometries, found {source.schema['geometry']}"
                )
            
            # Read the first feature
            features = list(source)
            if not features:
                raise HTTPException(status_code=400, detail="Shapefile contains no features")
            
            # Convert to GeoJSON
            feature = features[0]
            geometry = feature['geometry']
            
            # Convert to MultiPolygon if it's a Polygon
            if geometry['type'] == 'Polygon':
                geometry = {
                    'type': 'MultiPolygon',
                    'coordinates': [geometry['coordinates']]
                }
            
            # Apply simplification if requested
            if simplify and simplification_tolerance:
                try:
                    geom_shape = shape(geometry)
                    simplified_shape = geom_shape.simplify(simplification_tolerance, preserve_topology=True)
                    geometry = mapping(simplified_shape)
                except Exception as e:
                    # Log the error but continue with original geometry
                    print(f"Error simplifying geometry: {e}")
            
            # Calculate area in square kilometers
            area_sq_km = None
            try:
                # Use PostGIS to calculate area
                area_query = db.execute(
                    text("SELECT ST_Area(ST_Transform(ST_GeomFromGeoJSON(:geojson), 3857))/1000000 as area_sq_km"),
                    {"geojson": json.dumps(geometry)}
                ).fetchone()
                area_sq_km = area_query.area_sq_km if area_query else None
            except Exception as e:
                # Log the error but continue
                print(f"Error calculating area: {e}")
            
            # Create new area
            db_area = ProjectAreaModel(
                id=str(uuid.uuid4()),
                project_id=project_id,
                name=name,
                area_type=area_type,
                geometry=geometry,
                source_type="shapefile",
                original_filename=file.filename,
                processing_status="completed",
                simplification_tolerance=simplification_tolerance if simplify else None,
                area_sq_km=area_sq_km,
                metadata={}
            )
            db.add(db_area)
            db.commit()
            db.refresh(db_area)
            return db_area
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing shapefile: {str(e)}")
    
    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)