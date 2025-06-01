from typing import List, Dict, Any, Optional, Tuple, Union
from shapely.geometry import Polygon, MultiPolygon, shape, mapping
from shapely.validation import make_valid
from shapely.ops import unary_union
import json
import uuid
from datetime import datetime


class GeometryProcessingError(Exception):
    """Custom exception for geometry processing errors"""
    pass


class ProcessedGeometry:
    """Container for processed geometry with metadata"""
    def __init__(
        self,
        geometry: Dict[str, Any],
        area_sq_km: float,
        name: str,
        metadata: Dict[str, Any],
        source_info: Dict[str, Any]
    ):
        self.geometry = geometry
        self.area_sq_km = area_sq_km
        self.name = name
        self.metadata = metadata
        self.source_info = source_info


class GeometryProcessor:
    """
    Robust geometry processor for handling all geometry input scenarios.
    Supports single/multiple geometries from UI drawing, GeoJSON, and Shapefiles.
    """
    
    SUPPORTED_GEOMETRY_TYPES = ["Polygon", "MultiPolygon"]
    
    def __init__(self, area_calculation_func=None):
        """
        Initialize the geometry processor.
        
        Args:
            area_calculation_func: Optional function to calculate area in sq km
                                 Should accept GeoJSON geometry and return float
        """
        self.area_calculation_func = area_calculation_func
    
    def process_geometry_input(
        self,
        geometry_input: Union[Dict[str, Any], List[Dict[str, Any]]],
        base_name: str,
        area_type: str = "custom",
        source_type: str = "api",
        source_filename: Optional[str] = None,
        merge_overlapping: bool = False,
        simplification_tolerance: Optional[float] = None
    ) -> List[ProcessedGeometry]:
        """
        Main entry point for processing geometry input from any source.
        
        Args:
            geometry_input: Can be:
                - Single GeoJSON geometry dict
                - Single GeoJSON Feature dict  
                - GeoJSON FeatureCollection dict
                - List of any of the above
            base_name: Base name for created areas
            area_type: Type of area (village, custom, etc.)
            source_type: Source of geometry (ui_draw, geojson_upload, shapefile, api)
            source_filename: Original filename if from file upload
            merge_overlapping: Whether to merge overlapping geometries
            simplification_tolerance: Tolerance for geometry simplification
            
        Returns:
            List of ProcessedGeometry objects
        """
        try:
            # Normalize input to list format
            normalized_inputs = self._normalize_input(geometry_input)
            
            # Extract geometries from normalized inputs
            extracted_geometries = []
            for input_item in normalized_inputs:
                geometries = self._extract_geometries_from_input(input_item)
                extracted_geometries.extend(geometries)
            
            if not extracted_geometries:
                raise GeometryProcessingError("No valid geometries found in input")
            
            # Validate and clean geometries
            valid_geometries = []
            for geom_data in extracted_geometries:
                try:
                    validated = self._validate_and_clean_geometry(geom_data)
                    if validated:
                        valid_geometries.append(validated)
                except Exception as e:
                    # Log warning but continue with other geometries
                    print(f"Warning: Skipping invalid geometry: {e}")
                    continue
            
            if not valid_geometries:
                raise GeometryProcessingError("No valid geometries after validation")
            
            # Apply simplification if requested
            if simplification_tolerance:
                valid_geometries = self._apply_simplification(valid_geometries, simplification_tolerance)
            
            # Merge overlapping geometries if requested
            if merge_overlapping and len(valid_geometries) > 1:
                valid_geometries = self._merge_overlapping_geometries(valid_geometries)
            
            # Create ProcessedGeometry objects
            processed_geometries = []
            for i, geom_data in enumerate(valid_geometries):
                processed = self._create_processed_geometry(
                    geom_data,
                    base_name,
                    i,
                    len(valid_geometries),
                    area_type,
                    source_type,
                    source_filename
                )
                processed_geometries.append(processed)
            
            return processed_geometries
            
        except Exception as e:
            raise GeometryProcessingError(f"Failed to process geometry input: {str(e)}")
    
    def _normalize_input(self, geometry_input: Union[Dict, List]) -> List[Dict]:
        """Normalize input to a list of dictionaries"""
        if isinstance(geometry_input, list):
            return geometry_input
        elif isinstance(geometry_input, dict):
            return [geometry_input]
        else:
            raise GeometryProcessingError(f"Unsupported input type: {type(geometry_input)}")
    
    def _extract_geometries_from_input(self, input_item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract geometries from a single input item (Feature, FeatureCollection, or direct geometry)"""
        geometries = []
        
        if not isinstance(input_item, dict) or "type" not in input_item:
            raise GeometryProcessingError("Invalid GeoJSON: missing 'type' field")
        
        geom_type = input_item.get("type")
        
        if geom_type == "FeatureCollection":
            # Handle FeatureCollection
            features = input_item.get("features", [])
            if not features:
                raise GeometryProcessingError("FeatureCollection has no features")
            
            for i, feature in enumerate(features):
                if not isinstance(feature, dict):
                    continue
                
                if feature.get("type") != "Feature":
                    continue
                
                geometry = feature.get("geometry")
                if geometry and self._is_supported_geometry_type(geometry.get("type")):
                    geometry_with_metadata = {
                        "geometry": geometry,
                        "properties": feature.get("properties", {}),
                        "feature_index": i
                    }
                    geometries.append(geometry_with_metadata)
        
        elif geom_type == "Feature":
            # Handle single Feature
            geometry = input_item.get("geometry")
            if geometry and self._is_supported_geometry_type(geometry.get("type")):
                geometry_with_metadata = {
                    "geometry": geometry,
                    "properties": input_item.get("properties", {}),
                    "feature_index": 0
                }
                geometries.append(geometry_with_metadata)
        
        elif geom_type in self.SUPPORTED_GEOMETRY_TYPES:
            # Handle direct geometry
            geometry_with_metadata = {
                "geometry": input_item,
                "properties": {},
                "feature_index": 0
            }
            geometries.append(geometry_with_metadata)
        
        elif geom_type == "GeometryCollection":
            # Handle GeometryCollection
            geom_list = input_item.get("geometries", [])
            for i, geom in enumerate(geom_list):
                if self._is_supported_geometry_type(geom.get("type")):
                    geometry_with_metadata = {
                        "geometry": geom,
                        "properties": {},
                        "feature_index": i
                    }
                    geometries.append(geometry_with_metadata)
        
        else:
            raise GeometryProcessingError(f"Unsupported geometry type: {geom_type}")
        
        return geometries
    
    def _is_supported_geometry_type(self, geom_type: str) -> bool:
        """Check if geometry type is supported"""
        return geom_type in self.SUPPORTED_GEOMETRY_TYPES
    
    def _validate_and_clean_geometry(self, geom_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate and clean a geometry, converting Polygon to MultiPolygon"""
        try:
            geometry = geom_data["geometry"]
            
            # Create shapely geometry
            shapely_geom = shape(geometry)
            
            # Validate geometry
            if not shapely_geom.is_valid:
                # Try to fix invalid geometry
                shapely_geom = make_valid(shapely_geom)
                if not shapely_geom.is_valid:
                    raise GeometryProcessingError("Cannot fix invalid geometry")
            
            # Check if geometry is empty or has zero area
            if shapely_geom.is_empty or shapely_geom.area == 0:
                raise GeometryProcessingError("Geometry is empty or has zero area")
            
            # Convert to MultiPolygon if it's a Polygon
            if isinstance(shapely_geom, Polygon):
                shapely_geom = MultiPolygon([shapely_geom])
            elif not isinstance(shapely_geom, MultiPolygon):
                raise GeometryProcessingError(f"Unsupported geometry type after validation: {type(shapely_geom)}")
            
            # Convert back to GeoJSON
            clean_geometry = mapping(shapely_geom)
            
            # Update the geometry data
            geom_data["geometry"] = clean_geometry
            geom_data["shapely_geometry"] = shapely_geom
            
            return geom_data
            
        except Exception as e:
            raise GeometryProcessingError(f"Geometry validation failed: {str(e)}")
    
    def _apply_simplification(
        self, 
        geometries: List[Dict[str, Any]], 
        tolerance: float
    ) -> List[Dict[str, Any]]:
        """Apply simplification to geometries"""
        simplified_geometries = []
        
        for geom_data in geometries:
            try:
                shapely_geom = geom_data["shapely_geometry"]
                simplified = shapely_geom.simplify(tolerance, preserve_topology=True)
                
                # Ensure it's still valid after simplification
                if simplified.is_valid and not simplified.is_empty:
                    geom_data["geometry"] = mapping(simplified)
                    geom_data["shapely_geometry"] = simplified
                    geom_data["simplified"] = True
                    geom_data["simplification_tolerance"] = tolerance
                    simplified_geometries.append(geom_data)
                else:
                    # Use original if simplification failed
                    geom_data["simplified"] = False
                    simplified_geometries.append(geom_data)
                    
            except Exception as e:
                # Use original if simplification failed
                geom_data["simplified"] = False
                simplified_geometries.append(geom_data)
                print(f"Warning: Simplification failed: {e}")
        
        return simplified_geometries
    
    def _merge_overlapping_geometries(self, geometries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge overlapping geometries into single geometries"""
        if len(geometries) <= 1:
            return geometries
        
        try:
            # Extract shapely geometries
            shapely_geoms = [geom_data["shapely_geometry"] for geom_data in geometries]
            
            # Find overlapping groups
            merged_groups = []
            processed = set()
            
            for i, geom1 in enumerate(shapely_geoms):
                if i in processed:
                    continue
                
                # Start a new group with this geometry
                current_group = [i]
                current_union = geom1
                
                # Find all geometries that overlap with current union
                for j, geom2 in enumerate(shapely_geoms):
                    if j <= i or j in processed:
                        continue
                    
                    if current_union.intersects(geom2):
                        current_group.append(j)
                        union_result = unary_union([current_union, geom2])
                        
                        # Ensure union result is valid and convert to MultiPolygon if needed
                        if isinstance(union_result, Polygon):
                            current_union = MultiPolygon([union_result])
                        elif isinstance(union_result, MultiPolygon):
                            current_union = union_result
                        else:
                            # Handle other geometry types (GeometryCollection, etc.)
                            try:
                                # Try to extract polygons from the result
                                polygons = []
                                if hasattr(union_result, 'geoms'):
                                    for geom in union_result.geoms:
                                        if isinstance(geom, Polygon):
                                            polygons.append(geom)
                                        elif isinstance(geom, MultiPolygon):
                                            polygons.extend(geom.geoms)
                                if polygons:
                                    current_union = MultiPolygon(polygons)
                                else:
                                    # Fallback: use original union result as is
                                    current_union = union_result
                            except Exception:
                                # Fallback: use original union result
                                current_union = union_result
                
                # Mark all geometries in this group as processed
                for idx in current_group:
                    processed.add(idx)
                
                merged_groups.append({
                    "indices": current_group,
                    "merged_geometry": current_union
                })
            
            # Create merged geometry data
            merged_geometries = []
            for group in merged_groups:
                # Use metadata from first geometry in group
                first_idx = group["indices"][0]
                base_geom_data = geometries[first_idx].copy()
                
                # Update geometry - ensure it's MultiPolygon
                merged_geom = group["merged_geometry"]
                if isinstance(merged_geom, Polygon):
                    merged_geom = MultiPolygon([merged_geom])
                
                base_geom_data["geometry"] = mapping(merged_geom)
                base_geom_data["shapely_geometry"] = merged_geom
                
                # Update metadata to indicate merge
                base_geom_data["merged_from_count"] = len(group["indices"])
                base_geom_data["merged_indices"] = group["indices"]
                
                merged_geometries.append(base_geom_data)
            
            return merged_geometries
            
        except Exception as e:
            print(f"Warning: Merge failed, returning original geometries: {e}")
            return geometries
    
    def _calculate_area_sq_km(self, geometry: Dict[str, Any]) -> float:
        """Calculate area in square kilometers"""
        if self.area_calculation_func:
            try:
                return self.area_calculation_func(geometry)
            except Exception as e:
                print(f"Warning: Area calculation failed: {e}")
        
        # Fallback: use shapely for approximate calculation
        try:
            shapely_geom = shape(geometry)
            # This is very approximate - assumes WGS84 coordinates
            area_deg_sq = shapely_geom.area
            # Very rough conversion (1 degree ≈ 111 km at equator)
            area_sq_km = area_deg_sq * (111.0 ** 2)
            return area_sq_km
        except Exception:
            return 0.0
    
    def _create_processed_geometry(
        self,
        geom_data: Dict[str, Any],
        base_name: str,
        index: int,
        total_count: int,
        area_type: str,
        source_type: str,
        source_filename: Optional[str]
    ) -> ProcessedGeometry:
        """Create a ProcessedGeometry object from geometry data"""
        
        geometry = geom_data["geometry"]
        
        # Calculate area
        area_sq_km = self._calculate_area_sq_km(geometry)
        
        # Generate name
        if total_count > 1:
            name = f"{base_name} ({index + 1})"
        else:
            name = base_name
        
        # Build metadata
        metadata = {
            "feature_index": geom_data.get("feature_index", 0),
            "properties": geom_data.get("properties", {}),
            "processing_timestamp": datetime.now().isoformat(),
            "geometry_validation": {
                "was_simplified": geom_data.get("simplified", False),
                "simplification_tolerance": geom_data.get("simplification_tolerance"),
                "was_merged": geom_data.get("merged_from_count", 0) > 1,
                "merged_from_count": geom_data.get("merged_from_count", 1)
            }
        }
        
        # Build source info
        source_info = {
            "source_type": source_type,
            "source_filename": source_filename,
            "processing_method": "geometry_processor_v1"
        }
        
        return ProcessedGeometry(
            geometry=geometry,
            area_sq_km=area_sq_km,
            name=name,
            metadata=metadata,
            source_info=source_info
        )
    
    @staticmethod
    def validate_geometry_input(geometry_input: Any) -> Tuple[bool, str]:
        """
        Validate geometry input without processing.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not isinstance(geometry_input, (dict, list)):
                return False, "Input must be a dictionary or list"
            
            if isinstance(geometry_input, list):
                if not geometry_input:
                    return False, "Input list is empty"
                for item in geometry_input:
                    if not isinstance(item, dict):
                        return False, "All items in list must be dictionaries"
            
            if isinstance(geometry_input, dict):
                geometry_input = [geometry_input]
            
            for item in geometry_input:
                if "type" not in item:
                    return False, "Missing 'type' field in GeoJSON"
                
                geom_type = item.get("type")
                if geom_type not in ["Feature", "FeatureCollection", "Polygon", "MultiPolygon", "GeometryCollection"]:
                    return False, f"Unsupported geometry type: {geom_type}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def get_geometry_info(geometry_input: Union[Dict, List]) -> Dict[str, Any]:
        """
        Get information about geometry input without processing.
        
        Returns:
            Dictionary with geometry statistics and info
        """
        try:
            processor = GeometryProcessor()
            normalized = processor._normalize_input(geometry_input)
            
            total_features = 0
            geometry_types = []
            has_properties = False
            
            for item in normalized:
                geom_type = item.get("type")
                
                if geom_type == "FeatureCollection":
                    features = item.get("features", [])
                    total_features += len(features)
                    for feature in features:
                        geom = feature.get("geometry", {})
                        if geom.get("type"):
                            geometry_types.append(geom.get("type"))
                        if feature.get("properties"):
                            has_properties = True
                            
                elif geom_type == "Feature":
                    total_features += 1
                    geom = item.get("geometry", {})
                    if geom.get("type"):
                        geometry_types.append(geom.get("type"))
                    if item.get("properties"):
                        has_properties = True
                        
                elif geom_type in ["Polygon", "MultiPolygon"]:
                    total_features += 1
                    geometry_types.append(geom_type)
                    
                elif geom_type == "GeometryCollection":
                    geoms = item.get("geometries", [])
                    total_features += len(geoms)
                    for geom in geoms:
                        if geom.get("type"):
                            geometry_types.append(geom.get("type"))
            
            return {
                "total_features": total_features,
                "geometry_types": list(set(geometry_types)),
                "supported_types": [t for t in geometry_types if t in ["Polygon", "MultiPolygon"]],
                "has_properties": has_properties,
                "will_create_areas": len([t for t in geometry_types if t in ["Polygon", "MultiPolygon"]])
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "total_features": 0,
                "geometry_types": [],
                "supported_types": [],
                "has_properties": False,
                "will_create_areas": 0
            }