import uuid
import json
import os
import tempfile
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text, func
import zipfile
import geopandas as gpd
from shapely.geometry import shape, mapping, Polygon, MultiPolygon
from geoalchemy2.shape import from_shape

from app.api import deps
from app.models.projects import Project as ProjectModel, ProjectArea as ProjectAreaModel
from app.schemas.projects import ProjectArea, ProjectAreaCreate

router = APIRouter()


@router.post("/{project_id}/upload/geojson", response_model=ProjectArea)
async def upload_geojson(
    project_id: str,
    name: str = Form(...),
    area_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
) -> ProjectArea:
    """Upload a GeoJSON file to create a project area."""
    # Verify project exists
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Validate file type
    if not file.filename.lower().endswith('.geojson') and not file.filename.lower().endswith('.json'):
        raise HTTPException(status_code=400, detail="Invalid file format. Only GeoJSON files are accepted.")
    
    # Create temp directory to store the uploaded file
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, file.filename)
        
        # Save the uploaded file
        with open(temp_file_path, "wb") as temp_file:
            content = await file.read()
            temp_file.write(content)
        
        try:
            # Read the GeoJSON file
            with open(temp_file_path, "r") as f:
                geojson_data = json.load(f)
            
            # Extract geometries from GeoJSON
            geometries = []
            
            if geojson_data.get("type") == "FeatureCollection":
                # Get all features' geometries
                if geojson_data.get("features") and len(geojson_data["features"]) > 0:
                    for feature in geojson_data["features"]:
                        if feature.get("geometry"):
                            geometries.append(feature.get("geometry"))
            elif geojson_data.get("type") == "Feature":
                if geojson_data.get("geometry"):
                    geometries.append(geojson_data.get("geometry"))
            elif "type" in geojson_data and geojson_data["type"] in ["Polygon", "MultiPolygon"]:
                geometries.append(geojson_data)
            
            if not geometries:
                raise HTTPException(status_code=400, detail="Invalid GeoJSON format or no geometries found")
            
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
                
                # Create metadata with source information
                metadata = {
                    "source": "geojson_upload",
                    "filename": file.filename,
                    "feature_index": i
                }
                
                # Create area name with index if multiple geometries
                area_name = name
                if len(geometries) > 1:
                    area_name = f"{name} ({i+1})"
                
                # Create new area
                db_area = ProjectAreaModel(
                    id=str(uuid.uuid4()),
                    name=area_name,
                    area_type=area_type,
                    geometry=wkb_element,
                    area_metadata=metadata,
                    project_id=project_id,
                    source_type="geojson_upload",
                    original_filename=file.filename,
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
            
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing GeoJSON file: {str(e)}")


@router.post("/{project_id}/upload/shapefile", response_model=ProjectArea)
async def upload_shapefile(
    project_id: str,
    name: str = Form(...),
    area_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
) -> ProjectArea:
    """Upload a zipped shapefile to create a project area."""
    # Verify project exists
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Validate file type
    if not file.filename.lower().endswith('.zip'):
        raise HTTPException(status_code=400, detail="Invalid file format. Only zipped shapefiles are accepted.")
    
    # Create temp directory to store and extract the uploaded file
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, file.filename)
        extract_dir = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        
        # Save the uploaded file
        with open(temp_file_path, "wb") as temp_file:
            content = await file.read()
            temp_file.write(content)
        
        try:
            # Extract the zip file
            with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Find the .shp file (recursively search in all subdirectories)
            shp_files = []
            for root, dirs, files in os.walk(extract_dir):
                for filename in files:
                    if filename.lower().endswith('.shp'):
                        shp_files.append(os.path.join(root, filename))
            
            if not shp_files:
                raise HTTPException(status_code=400, detail="No shapefile (.shp) found in the zip archive")
            
            # Use the first shapefile found
            shp_path = shp_files[0]
            
            # Read the shapefile using geopandas
            gdf = gpd.read_file(shp_path)
            
            # Check if there are any features
            if len(gdf) == 0:
                raise HTTPException(status_code=400, detail="Shapefile contains no features")
            
            # Create areas for each geometry in the shapefile
            created_areas = []
            
            for i, row in gdf.iterrows():
                geom = row.geometry
                
                # Skip invalid geometries
                if geom is None or not geom.is_valid:
                    continue
                
                # Convert to GeoJSON
                geojson = mapping(geom)
                
                # Calculate area in square kilometers
                area_sq_km = None
                try:
                    # Use PostGIS to calculate area
                    area_query = db.execute(
                        text("SELECT ST_Area(ST_Transform(ST_GeomFromGeoJSON(:geojson), 3857))/1000000 as area_sq_km"),
                        {"geojson": json.dumps(geojson)}
                    ).fetchone()
                    area_sq_km = area_query.area_sq_km if area_query else None
                except Exception as e:
                    # Log the error but continue
                    print(f"Error calculating area: {e}")
                
                # Convert to MultiPolygon if it's a Polygon
                if isinstance(geom, Polygon):
                    geom = MultiPolygon([geom])
                
                # Create WKB element for database storage
                wkb_element = from_shape(geom, srid=4326)  # Use SRID 4326 for WGS84
                
                # Extract attributes from this row
                attributes = {k: str(v) for k, v in row.items() if k != 'geometry'}
                
                # Create metadata with source information
                metadata = {
                    "source": "shapefile",
                    "filename": file.filename,
                    "feature_index": i,
                    "attributes": attributes
                }
                
                # Create area name with index if multiple geometries
                area_name = name
                if len(gdf) > 1:
                    area_name = f"{name} ({i+1})"
                
                # Create new area
                db_area = ProjectAreaModel(
                    id=str(uuid.uuid4()),
                    name=area_name,
                    area_type=area_type,
                    geometry=wkb_element,
                    area_metadata=metadata,
                    project_id=project_id,
                    source_type="shapefile",
                    original_filename=file.filename,
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
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing shapefile: {str(e)}")
