from typing import Any, List, Optional, Union, Dict
from fastapi import APIRouter, Depends, HTTPException, Body, Query, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from pydantic import BaseModel, Field
import json
import tempfile
import os
import zipfile
import uuid

from app.api import deps
from app.models.projects import Project as ProjectModel, ProjectArea as ProjectAreaModel
from app.schemas.projects import ProjectArea, ProjectAreaCreate
from app.utils.geometry_processor import GeometryProcessor, GeometryProcessingError, ProcessedGeometry
from geoalchemy2.shape import from_shape
from shapely.geometry import shape

router = APIRouter()


class GeometryInputRequest(BaseModel):
    """Request model for geometry input"""
    geometry: Union[Dict[str, Any], List[Dict[str, Any]]] = Field(..., description="Geometry input (Feature, FeatureCollection, or direct geometry)")
    name: str = Field(..., description="Base name for created areas")
    area_type: str = Field("custom", description="Type of area (village, custom, etc.)")
    merge_overlapping: bool = Field(False, description="Whether to merge overlapping geometries")
    simplification_tolerance: Optional[float] = Field(None, description="Tolerance for geometry simplification")


class GeometryAnalysisRequest(BaseModel):
    """Request model for geometry analysis"""
    geometry_input: Union[Dict[str, Any], List[Dict[str, Any]]] = Field(..., description="Geometry to analyze")
    base_name: str = Field("Area", description="Base name for area estimation")


class GeometryValidationResponse(BaseModel):
    """Response model for geometry validation"""
    is_valid: bool
    error_message: str = ""
    geometry_info: Dict[str, Any] = {}


class GeometryInfoResponse(BaseModel):
    """Response model for geometry information"""
    total_features: int
    geometry_types: List[str]
    supported_types: List[str]
    has_properties: bool
    will_create_areas: int
    estimated_areas: List[Dict[str, Any]] = []


def get_area_calculation_func(db: Session):
    """Create area calculation function using PostGIS"""
    def calculate_area(geometry: Dict[str, Any]) -> float:
        try:
            area_query = db.execute(
                text("SELECT ST_Area(ST_Transform(ST_GeomFromGeoJSON(:geojson), 3857))/1000000 as area_sq_km"),
                {"geojson": json.dumps(geometry)}
            ).fetchone()
            return float(area_query.area_sq_km) if area_query and area_query.area_sq_km else 0.0
        except Exception as e:
            print(f"PostGIS area calculation failed: {e}")
            return 0.0
    return calculate_area


@router.post("/{project_id}/areas/enhanced", response_model=Union[ProjectArea, List[ProjectArea]])
def create_project_areas_enhanced(
    project_id: str,
    request: GeometryInputRequest,
    db: Session = Depends(deps.get_db),
) -> Union[ProjectArea, List[ProjectArea]]:
    """
    Enhanced project area creation with robust geometry processing.
    
    Supports:
    - Single or multiple geometries from UI drawing
    - GeoJSON Features and FeatureCollections
    - Direct Polygon/MultiPolygon geometries
    - Geometry validation and cleaning
    - Optional merging of overlapping areas
    - Optional geometry simplification
    """
    # Verify project exists
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        # Initialize geometry processor with PostGIS area calculation
        area_calc_func = get_area_calculation_func(db)
        processor = GeometryProcessor(area_calculation_func=area_calc_func)
        
        # Process the geometry input
        processed_geometries = processor.process_geometry_input(
            geometry_input=request.geometry,
            base_name=request.name,
            area_type=request.area_type,
            source_type="drawn",
            merge_overlapping=request.merge_overlapping,
            simplification_tolerance=request.simplification_tolerance
        )
        
        if not processed_geometries:
            raise HTTPException(status_code=400, detail="No valid geometries could be processed")
        
        # Create database records
        created_areas = []
        for processed_geom in processed_geometries:
            # Convert to shapely for database storage
            shapely_geom = shape(processed_geom.geometry)
            wkb_element = from_shape(shapely_geom, srid=4326)
            
            # Create new area
            db_area = ProjectAreaModel(
                id=str(uuid.uuid4()),
                project_id=project_id,
                name=processed_geom.name,
                area_type=processed_geom.source_info.get("area_type", request.area_type),
                geometry=wkb_element,
                area_metadata=processed_geom.metadata,
                source_type="drawn",
                processing_status="completed",
                simplification_tolerance=request.simplification_tolerance,
                area_sq_km=processed_geom.area_sq_km,
                updated_at=func.now()
            )
            db.add(db_area)
            created_areas.append(db_area)
        
        # Commit all areas
        db.commit()
        
        # Refresh areas to get timestamps
        for area in created_areas:
            db.refresh(area)
        
        # Return single area or list based on count
        if len(created_areas) == 1:
            return created_areas[0]
        else:
            return created_areas
            
    except GeometryProcessingError as e:
        raise HTTPException(status_code=400, detail=f"Geometry processing error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating project areas: {str(e)}")


@router.post("/{project_id}/areas/upload-enhanced")
async def upload_file_enhanced(
    project_id: str,
    name: str = Form(...),
    area_type: str = Form("custom"),
    merge_overlapping: bool = Form(False),
    simplification_tolerance: Optional[float] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
) -> Union[ProjectArea, List[ProjectArea]]:
    """
    Enhanced file upload with robust geometry processing.
    
    Supports:
    - GeoJSON files (.geojson, .json)
    - Zipped shapefiles (.zip)
    - Multiple features in files
    - Geometry validation and cleaning
    - Optional merging and simplification
    """
    # Verify project exists
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    filename = file.filename.lower()
    
    try:
        if filename.endswith(('.geojson', '.json')):
            # Handle GeoJSON file
            content = await file.read()
            geojson_data = json.loads(content)
            source_type = "geojson_upload"
            
        elif filename.endswith('.zip'):
            # Handle shapefile
            geojson_data = await _process_shapefile_upload(file)
            source_type = "shapefile"
            
        else:
            raise HTTPException(
                status_code=400, 
                detail="Unsupported file format. Only .geojson, .json, and .zip files are supported."
            )
        
        # Initialize geometry processor
        area_calc_func = get_area_calculation_func(db)
        processor = GeometryProcessor(area_calculation_func=area_calc_func)
        
        # Process geometries
        processed_geometries = processor.process_geometry_input(
            geometry_input=geojson_data,
            base_name=name,
            area_type=area_type,
            source_type="geojson_upload",
            source_filename=file.filename,
            merge_overlapping=merge_overlapping,
            simplification_tolerance=simplification_tolerance
        )
        
        if not processed_geometries:
            raise HTTPException(status_code=400, detail="No valid geometries found in uploaded file")
        
        # Create database records
        created_areas = []
        for processed_geom in processed_geometries:
            shapely_geom = shape(processed_geom.geometry)
            wkb_element = from_shape(shapely_geom, srid=4326)
            
            db_area = ProjectAreaModel(
                id=str(uuid.uuid4()),
                project_id=project_id,
                name=processed_geom.name,
                area_type=area_type,
                geometry=wkb_element,
                area_metadata=processed_geom.metadata,
                source_type="geojson_upload",
                original_filename=file.filename,
                processing_status="completed",
                simplification_tolerance=simplification_tolerance,
                area_sq_km=processed_geom.area_sq_km,
                updated_at=func.now()
            )
            db.add(db_area)
            created_areas.append(db_area)
        
        db.commit()
        
        for area in created_areas:
            db.refresh(area)
        
        if len(created_areas) == 1:
            return created_areas[0]
        else:
            return created_areas
            
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in uploaded file")
    except GeometryProcessingError as e:
        raise HTTPException(status_code=400, detail=f"Geometry processing error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing uploaded file: {str(e)}")


@router.post("/validate-geometry", response_model=GeometryValidationResponse)
def validate_geometry(
    geometry_input: Union[Dict[str, Any], List[Dict[str, Any]]] = Body(..., description="Geometry to validate")
) -> GeometryValidationResponse:
    """
    Validate geometry input without creating areas.
    Useful for frontend validation before submission.
    """
    try:
        is_valid, error_message = GeometryProcessor.validate_geometry_input(geometry_input)
        geometry_info = GeometryProcessor.get_geometry_info(geometry_input) if is_valid else {}
        
        return GeometryValidationResponse(
            is_valid=is_valid,
            error_message=error_message,
            geometry_info=geometry_info
        )
    except Exception as e:
        return GeometryValidationResponse(
            is_valid=False,
            error_message=f"Validation failed: {str(e)}",
            geometry_info={}
        )


@router.post("/analyze-geometry", response_model=GeometryInfoResponse)
def analyze_geometry(
    request: GeometryAnalysisRequest,
    db: Session = Depends(deps.get_db),
) -> GeometryInfoResponse:
    """
    Analyze geometry input and provide detailed information about what would be created.
    Useful for showing preview information to users.
    """
    try:
        # Get basic geometry info
        geometry_info = GeometryProcessor.get_geometry_info(request.geometry_input)
        
        # Create processor for detailed analysis
        area_calc_func = get_area_calculation_func(db)
        processor = GeometryProcessor(area_calculation_func=area_calc_func)
        
        # Simulate processing to get area estimates
        estimated_areas = []
        try:
            processed_geometries = processor.process_geometry_input(
                geometry_input=request.geometry_input,
                base_name=request.base_name,
                area_type="custom",
                source_type="analysis"
            )
            
            for i, processed_geom in enumerate(processed_geometries):
                estimated_areas.append({
                    "name": processed_geom.name,
                    "area_sq_km": round(processed_geom.area_sq_km, 3),
                    "geometry_type": processed_geom.geometry.get("type", "Unknown"),
                    "has_properties": bool(processed_geom.metadata.get("properties", {}))
                })
                
        except Exception as e:
            print(f"Area estimation failed: {e}")
        
        return GeometryInfoResponse(
            total_features=geometry_info.get("total_features", 0),
            geometry_types=geometry_info.get("geometry_types", []),
            supported_types=geometry_info.get("supported_types", []),
            has_properties=geometry_info.get("has_properties", False),
            will_create_areas=geometry_info.get("will_create_areas", 0),
            estimated_areas=estimated_areas
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Analysis failed: {str(e)}")


@router.post("/{project_id}/areas/batch-upload")
async def batch_upload_files(
    project_id: str,
    files: List[UploadFile] = File(...),
    base_name: str = Form("Uploaded Area"),
    area_type: str = Form("custom"),
    merge_all: bool = Form(False),
    merge_per_file: bool = Form(False),
    simplification_tolerance: Optional[float] = Form(None),
    db: Session = Depends(deps.get_db),
) -> List[ProjectArea]:
    """
    Upload multiple files and create project areas.
    
    Args:
        files: List of files to upload
        base_name: Base name for created areas
        area_type: Type of areas to create
        merge_all: Merge all geometries from all files into single areas
        merge_per_file: Merge geometries within each file
        simplification_tolerance: Optional simplification tolerance
    """
    # Verify project exists
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    all_geometries = []
    file_geometries = {}
    
    try:
        # Process all files
        for file in files:
            filename = file.filename.lower()
            
            if filename.endswith(('.geojson', '.json')):
                content = await file.read()
                geojson_data = json.loads(content)
            elif filename.endswith('.zip'):
                geojson_data = await _process_shapefile_upload(file)
            else:
                continue  # Skip unsupported files
            
            file_geometries[file.filename] = geojson_data
            all_geometries.append(geojson_data)
        
        if not all_geometries:
            raise HTTPException(status_code=400, detail="No valid geometry files found")
        
        # Initialize processor
        area_calc_func = get_area_calculation_func(db)
        processor = GeometryProcessor(area_calculation_func=area_calc_func)
        
        created_areas = []
        
        if merge_all:
            # Process all geometries together
            processed_geometries = processor.process_geometry_input(
                geometry_input=all_geometries,
                base_name=base_name,
                area_type=area_type,
                source_type="geojson_upload",
                merge_overlapping=True,
                simplification_tolerance=simplification_tolerance
            )
            
            for processed_geom in processed_geometries:
                db_area = _create_area_from_processed(
                    processed_geom, project_id, area_type, "geojson_upload", db
                )
                created_areas.append(db_area)
        
        else:
            # Process each file separately
            for filename, geojson_data in file_geometries.items():
                file_base_name = f"{base_name} - {filename}"
                
                processed_geometries = processor.process_geometry_input(
                    geometry_input=geojson_data,
                    base_name=file_base_name,
                    area_type=area_type,
                    source_type="geojson_upload",
                    source_filename=filename,
                    merge_overlapping=merge_per_file,
                    simplification_tolerance=simplification_tolerance
                )
                
                for processed_geom in processed_geometries:
                    db_area = _create_area_from_processed(
                        processed_geom, project_id, area_type, "geojson_upload", db, filename
                    )
                    created_areas.append(db_area)
        
        # Commit all areas
        db.commit()
        
        # Refresh areas
        for area in created_areas:
            db.refresh(area)
        
        return created_areas
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch upload failed: {str(e)}")


async def _process_shapefile_upload(file: UploadFile) -> Dict[str, Any]:
    """Process uploaded shapefile and return GeoJSON data"""
    import geopandas as gpd
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp()
    try:
        # Save and extract zip file
        zip_path = os.path.join(temp_dir, file.filename)
        with open(zip_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find shapefile
        shp_files = [f for f in os.listdir(temp_dir) if f.lower().endswith('.shp')]
        if not shp_files:
            raise Exception("No .shp file found in zip archive")
        
        # Read shapefile
        shp_path = os.path.join(temp_dir, shp_files[0])
        gdf = gpd.read_file(shp_path)
        
        if len(gdf) == 0:
            raise Exception("Shapefile contains no features")
        
        # Convert to GeoJSON
        geojson_str = gdf.to_json()
        return json.loads(geojson_str)
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def _create_area_from_processed(
    processed_geom: ProcessedGeometry,
    project_id: str,
    area_type: str,
    source_type: str,
    db: Session,
    filename: Optional[str] = None
) -> ProjectAreaModel:
    """Helper function to create ProjectAreaModel from ProcessedGeometry"""
    shapely_geom = shape(processed_geom.geometry)
    wkb_element = from_shape(shapely_geom, srid=4326)
    
    # Ensure source_type is valid
    valid_source_types = ['drawn', 'geojson_upload', 'shapefile']
    if source_type not in valid_source_types:
        source_type = 'drawn'
    
    return ProjectAreaModel(
        id=str(uuid.uuid4()),
        project_id=project_id,
        name=processed_geom.name,
        area_type=area_type,
        geometry=wkb_element,
        area_metadata=processed_geom.metadata,
        source_type=source_type,
        original_filename=filename,
        processing_status="completed",
        area_sq_km=processed_geom.area_sq_km,
        updated_at=func.now()
    )