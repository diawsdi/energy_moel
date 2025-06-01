from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class SourceType(str, Enum):
    """Enumeration of source types for project areas"""
    UI_DRAW = "ui_draw"
    API_ENHANCED = "api_enhanced"
    GEOJSON_UPLOAD = "geojson_upload_enhanced"
    SHAPEFILE_UPLOAD = "shapefile_enhanced"
    BATCH_UPLOAD = "batch_upload"
    BATCH_UPLOAD_MERGED = "batch_upload_merged"


class AreaType(str, Enum):
    """Enumeration of area types"""
    VILLAGE = "village"
    CUSTOM = "custom"
    REGION = "region"
    ADMINISTRATIVE = "administrative"


class GeometryType(str, Enum):
    """Supported geometry types"""
    POLYGON = "Polygon"
    MULTIPOLYGON = "MultiPolygon"
    FEATURE = "Feature"
    FEATURE_COLLECTION = "FeatureCollection"
    GEOMETRY_COLLECTION = "GeometryCollection"


class ProcessingStatus(str, Enum):
    """Processing status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    VALIDATED = "validated"


class GeometryValidationInfo(BaseModel):
    """Information about geometry validation and processing"""
    was_simplified: bool = False
    simplification_tolerance: Optional[float] = None
    was_merged: bool = False
    merged_from_count: int = 1
    was_validated: bool = True
    validation_errors: List[str] = []


class ProcessingMetadata(BaseModel):
    """Metadata about geometry processing"""
    feature_index: int = 0
    properties: Dict[str, Any] = {}
    processing_timestamp: str
    geometry_validation: GeometryValidationInfo
    source_properties: Dict[str, Any] = {}


class SourceInfo(BaseModel):
    """Information about the source of the geometry"""
    source_type: SourceType
    source_filename: Optional[str] = None
    processing_method: str = "geometry_processor_v1"
    upload_timestamp: Optional[str] = None


class GeometryInputRequest(BaseModel):
    """Request model for enhanced geometry input"""
    geometry: Union[Dict[str, Any], List[Dict[str, Any]]] = Field(
        ..., 
        description="Geometry input (Feature, FeatureCollection, direct geometry, or list of any)"
    )
    name: str = Field(..., min_length=1, max_length=255, description="Base name for created areas")
    area_type: AreaType = Field(AreaType.CUSTOM, description="Type of area to create")
    merge_overlapping: bool = Field(False, description="Whether to merge overlapping geometries")
    simplification_tolerance: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=0.01, 
        description="Tolerance for geometry simplification (0.0-0.01)"
    )
    preserve_properties: bool = Field(True, description="Whether to preserve feature properties")
    validate_only: bool = Field(False, description="Only validate, don't create areas")

    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

    @validator('simplification_tolerance')
    def validate_tolerance(cls, v):
        if v is not None and (v < 0 or v > 0.01):
            raise ValueError('Simplification tolerance must be between 0.0 and 0.01')
        return v


class BatchUploadRequest(BaseModel):
    """Request model for batch file upload"""
    base_name: str = Field("Uploaded Area", description="Base name for created areas")
    area_type: AreaType = Field(AreaType.CUSTOM, description="Type of areas to create")
    merge_all: bool = Field(False, description="Merge all geometries from all files")
    merge_per_file: bool = Field(False, description="Merge geometries within each file")
    simplification_tolerance: Optional[float] = Field(None, description="Simplification tolerance")
    max_files: int = Field(10, ge=1, le=50, description="Maximum number of files to process")


class EstimatedArea(BaseModel):
    """Information about an estimated area"""
    name: str
    area_sq_km: float
    geometry_type: str
    has_properties: bool
    feature_index: int = 0
    properties_preview: Dict[str, Any] = {}


class GeometryValidationResponse(BaseModel):
    """Response model for geometry validation"""
    is_valid: bool
    error_message: str = ""
    warnings: List[str] = []
    geometry_info: Dict[str, Any] = {}
    validation_details: Dict[str, Any] = {}


class GeometryAnalysisResponse(BaseModel):
    """Response model for geometry analysis"""
    total_features: int
    geometry_types: List[str]
    supported_types: List[str]
    unsupported_types: List[str] = []
    has_properties: bool
    will_create_areas: int
    estimated_areas: List[EstimatedArea] = []
    total_estimated_area_sq_km: float = 0.0
    processing_options: Dict[str, Any] = {}


class ProcessedGeometryInfo(BaseModel):
    """Information about a processed geometry"""
    name: str
    area_sq_km: float
    geometry_type: str
    feature_count: int = 1
    processing_metadata: ProcessingMetadata
    source_info: SourceInfo


class EnhancedProjectAreaBase(BaseModel):
    """Enhanced base model for project areas"""
    name: str = Field(..., min_length=1, max_length=255)
    area_type: AreaType
    geometry: Dict[str, Any]
    processing_metadata: Optional[ProcessingMetadata] = None
    source_info: Optional[SourceInfo] = None


class EnhancedProjectAreaCreate(EnhancedProjectAreaBase):
    """Enhanced create model for project areas"""
    merge_with_existing: bool = Field(False, description="Merge with existing overlapping areas")
    validate_before_create: bool = Field(True, description="Validate geometry before creation")


class EnhancedProjectAreaUpdate(BaseModel):
    """Enhanced update model for project areas"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    area_type: Optional[AreaType] = None
    geometry: Optional[Dict[str, Any]] = None
    processing_metadata: Optional[ProcessingMetadata] = None
    reprocess_geometry: bool = Field(False, description="Reprocess geometry with current settings")


class EnhancedProjectArea(EnhancedProjectAreaBase):
    """Enhanced project area model with full information"""
    id: str
    project_id: str
    original_filename: Optional[str] = None
    processing_status: ProcessingStatus
    simplification_tolerance: Optional[float] = None
    area_sq_km: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Enhanced fields
    geometry_hash: Optional[str] = None
    validation_status: str = "unknown"
    error_log: List[str] = []

    class Config:
        from_attributes = True
        use_enum_values = True


class ProjectAreaStats(BaseModel):
    """Statistics for project areas"""
    total_buildings: int = 0
    electrified_buildings: int = 0
    unelectrified_buildings: int = 0
    avg_consumption_kwh_month: float = 0.0
    avg_energy_demand_kwh_year: float = 0.0
    electrification_rate: float = 0.0
    confidence_metrics: Dict[str, float] = {}


class EnhancedProjectAreaWithStats(EnhancedProjectArea):
    """Enhanced project area with statistics"""
    stats: ProjectAreaStats
    last_stats_update: Optional[datetime] = None


class BatchOperationResult(BaseModel):
    """Result of a batch operation"""
    total_files_processed: int
    successful_areas_created: int
    failed_files: List[str] = []
    warnings: List[str] = []
    created_areas: List[EnhancedProjectArea] = []
    processing_summary: Dict[str, Any] = {}


class FileUploadInfo(BaseModel):
    """Information about an uploaded file"""
    filename: str
    file_size: int
    content_type: str
    geometry_preview: Optional[GeometryAnalysisResponse] = None
    processing_options: Dict[str, Any] = {}


class BatchPreviewResponse(BaseModel):
    """Preview response for batch operations"""
    files_info: List[FileUploadInfo]
    total_estimated_areas: int
    total_estimated_area_sq_km: float
    recommended_settings: Dict[str, Any] = {}
    warnings: List[str] = []


class GeometryOperationRequest(BaseModel):
    """Request for geometry operations"""
    operation: str = Field(..., description="Operation type (merge, split, simplify, validate)")
    area_ids: List[str] = Field(..., description="List of area IDs to operate on")
    parameters: Dict[str, Any] = Field({}, description="Operation-specific parameters")


class GeometryOperationResponse(BaseModel):
    """Response for geometry operations"""
    operation: str
    success: bool
    affected_areas: List[str] = []
    created_areas: List[EnhancedProjectArea] = []
    deleted_areas: List[str] = []
    messages: List[str] = []
    operation_metadata: Dict[str, Any] = {}


class AreaComparisonResult(BaseModel):
    """Result of comparing two areas"""
    area1_id: str
    area2_id: str
    overlap_area_sq_km: float
    overlap_percentage_area1: float
    overlap_percentage_area2: float
    relationship: str  # "disjoint", "contains", "within", "overlaps", "touches"
    can_merge: bool
    merge_would_create_area_sq_km: float


class ProjectGeometryValidationReport(BaseModel):
    """Comprehensive validation report for project geometries"""
    project_id: str
    total_areas: int
    valid_areas: int
    invalid_areas: int
    areas_with_warnings: int
    validation_issues: List[Dict[str, Any]] = []
    recommendations: List[str] = []
    overall_status: str
    validation_timestamp: datetime


class EnhancedProjectAreaSearchRequest(BaseModel):
    """Request model for searching project areas"""
    project_id: Optional[str] = None
    area_types: Optional[List[AreaType]] = None
    source_types: Optional[List[SourceType]] = None
    min_area_sq_km: Optional[float] = None
    max_area_sq_km: Optional[float] = None
    has_buildings: Optional[bool] = None
    processing_status: Optional[List[ProcessingStatus]] = None
    search_text: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


class EnhancedProjectAreaSearchResponse(BaseModel):
    """Response model for area search"""
    total_count: int
    filtered_count: int
    areas: List[EnhancedProjectArea]
    search_metadata: Dict[str, Any] = {}
    aggregations: Dict[str, Any] = {}