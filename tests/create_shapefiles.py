import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
import pandas as pd
import os
import zipfile
import tempfile
import shutil

def create_test_shapefiles():
    """Create test shapefiles for project area testing"""
    
    # Create output directory
    output_dir = "file_test"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Single feature shapefile
    single_geom = Polygon([
        (-16.5, 14.5),
        (-16.3, 14.5), 
        (-16.3, 14.7),
        (-16.5, 14.7),
        (-16.5, 14.5)
    ])
    
    single_data = {
        'name': ['Single Test Village'],
        'population': [1200],
        'region': ['Dakar'],
        'area_type': ['village'],
        'electrified': [False],
        'priority': ['high'],
        'geometry': [single_geom]
    }
    
    single_gdf = gpd.GeoDataFrame(single_data, crs='EPSG:4326')
    
    # Multiple features shapefile
    multi_geoms = [
        Polygon([(-16.8, 14.2), (-16.6, 14.2), (-16.6, 14.4), (-16.8, 14.4), (-16.8, 14.2)]),
        Polygon([(-16.4, 14.1), (-16.2, 14.1), (-16.2, 14.3), (-16.4, 14.3), (-16.4, 14.1)]),
        MultiPolygon([
            Polygon([(-16.0, 14.6), (-15.9, 14.6), (-15.9, 14.7), (-16.0, 14.7), (-16.0, 14.6)]),
            Polygon([(-16.0, 14.8), (-15.9, 14.8), (-15.9, 14.9), (-16.0, 14.9), (-16.0, 14.8)])
        ]),
        Polygon([(-15.7, 13.8), (-15.5, 13.8), (-15.5, 14.0), (-15.7, 14.0), (-15.7, 13.8)]),
        Polygon([(-15.3, 14.5), (-15.1, 14.5), (-15.1, 14.7), (-15.3, 14.7), (-15.3, 14.5)])
    ]
    
    multi_data = {
        'name': ['Village Alpha', 'Village Beta', 'Village Gamma Complex', 'Village Delta', 'Village Epsilon'],
        'population': [850, 1500, 2200, 650, 980],
        'region': ['Dakar', 'Thies', 'Saint-Louis', 'Fatick', 'Diourbel'], 
        'area_type': ['village'] * 5,
        'electrified': [True, False, True, False, True],
        'priority': ['medium', 'high', 'low', 'high', 'medium'],
        'roads': [True, False, True, True, True],
        'water': [True, True, True, False, True],
        'school': [True, False, True, True, False],
        'geometry': multi_geoms
    }
    
    multi_gdf = gpd.GeoDataFrame(multi_data, crs='EPSG:4326')
    
    # Create temporary directories for shapefiles
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Save single feature shapefile
        single_shp_dir = os.path.join(temp_dir, 'onefeature')
        os.makedirs(single_shp_dir)
        single_shp_path = os.path.join(single_shp_dir, 'onefeature.shp')
        single_gdf.to_file(single_shp_path)
        
        # Zip single feature shapefile
        with zipfile.ZipFile(os.path.join(output_dir, 'onefeature.zip'), 'w') as zip_file:
            for root, dirs, files in os.walk(single_shp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    zip_file.write(file_path, os.path.basename(file_path))
        
        # Save multiple features shapefile
        multi_shp_dir = os.path.join(temp_dir, 'manyfeature')
        os.makedirs(multi_shp_dir)
        multi_shp_path = os.path.join(multi_shp_dir, 'manyfeature.shp')
        multi_gdf.to_file(multi_shp_path)
        
        # Zip multiple features shapefile
        with zipfile.ZipFile(os.path.join(output_dir, 'manyfeature.zip'), 'w') as zip_file:
            for root, dirs, files in os.walk(multi_shp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    zip_file.write(file_path, os.path.basename(file_path))
        
        print("Successfully created:")
        print("- onefeature.zip (1 polygon)")
        print("- manyfeature.zip (5 polygons)")
        
    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    create_test_shapefiles()