from datetime import datetime
from typing import Any

from fastapi.encoders import jsonable_encoder
from geoalchemy2.elements import WKBElement
from shapely import wkb
from shapely.geometry import mapping


def custom_jsonable_encoder(obj: Any, **kwargs) -> Any:
    """Custom JSON encoder that handles WKBElement and other special types."""
    
    # Handle WKBElement (PostGIS geometry)
    if isinstance(obj, WKBElement):
        try:
            geom = wkb.loads(bytes(obj.data))
            return mapping(geom)
        except Exception as e:
            print(f"Error converting WKBElement to GeoJSON: {e}")
            return {}
    
    # Use the default encoder for other types
    return jsonable_encoder(obj, **kwargs)
