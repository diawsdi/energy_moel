#!/usr/bin/env python3
"""
Script to explore the power plants shapefile data and understand its structure
before importing it into the database.
"""

import os
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                       "data", "extracted_powerplants")
SHAPEFILE_PATH = os.path.join(DATA_DIR, "SEN_PowerPlants.shp")

def explore_shapefile():
    """Explore the power plants shapefile and print information about its structure."""
    print(f"Reading shapefile from: {SHAPEFILE_PATH}")
    
    # Read the shapefile
    try:
        gdf = gpd.read_file(SHAPEFILE_PATH)
        print(f"Successfully read shapefile with {len(gdf)} features")
        
        # Print basic information
        print("\n--- Shapefile Information ---")
        print(f"CRS: {gdf.crs}")
        print(f"Geometry type: {gdf.geometry.type.unique()}")
        print(f"Bounding box: {gdf.total_bounds}")
        
        # Print column information
        print("\n--- Columns ---")
        for col in gdf.columns:
            if col != 'geometry':
                unique_vals = gdf[col].unique()
                print(f"{col}: {gdf[col].dtype}")
                print(f"  Sample values: {unique_vals[:min(5, len(unique_vals))]}")
                print(f"  Null values: {gdf[col].isna().sum()}")
                print()
        
        # Print sample records
        print("\n--- Sample Records ---")
        pd.set_option('display.max_columns', None)
        print(gdf.head(3))
        
        # Plot the power plants
        print("\n--- Creating plot ---")
        fig, ax = plt.subplots(figsize=(10, 10))
        gdf.plot(ax=ax, markersize=50, color='red')
        plt.title('Power Plants in Senegal')
        plt.savefig(os.path.join(DATA_DIR, 'power_plants_plot.png'))
        print(f"Plot saved to {os.path.join(DATA_DIR, 'power_plants_plot.png')}")
        
        return gdf
    
    except Exception as e:
        print(f"Error reading shapefile: {e}")
        return None

def map_columns_to_db_schema(gdf):
    """
    Map the columns from the shapefile to our database schema.
    Print the mapping and any missing or extra columns.
    """
    if gdf is None:
        return
    
    # Define our database schema columns
    db_columns = [
        'plant_id',
        'location',
        'plant_name',
        'year',
        'plant_type',
        'capacity_mw',
        'annual_gen_gwh',
        'grid_node_id',
        'data_source'
    ]
    
    # Get the shapefile columns
    shapefile_columns = [col for col in gdf.columns if col != 'geometry']
    
    print("\n--- Column Mapping Analysis ---")
    print("Database schema columns:")
    for col in db_columns:
        print(f"  - {col}")
    
    print("\nShapefile columns:")
    for col in shapefile_columns:
        print(f"  - {col}")
    
    print("\nPossible mappings:")
    # Try to suggest mappings based on column names
    mappings = {}
    for db_col in db_columns:
        if db_col == 'location':
            mappings[db_col] = 'geometry'
            continue
            
        # Look for exact matches
        if db_col in shapefile_columns:
            mappings[db_col] = db_col
            continue
            
        # Look for partial matches
        matches = [col for col in shapefile_columns if db_col.lower() in col.lower() or col.lower() in db_col.lower()]
        if matches:
            mappings[db_col] = matches[0]
            continue
            
        mappings[db_col] = None
    
    for db_col, shapefile_col in mappings.items():
        if shapefile_col:
            print(f"  - {db_col} -> {shapefile_col}")
        else:
            print(f"  - {db_col} -> No match found")
    
    print("\nUnmapped shapefile columns:")
    unmapped = [col for col in shapefile_columns if col not in mappings.values()]
    for col in unmapped:
        print(f"  - {col}")

if __name__ == "__main__":
    print("Exploring power plants shapefile...")
    gdf = explore_shapefile()
    
    if gdf is not None:
        map_columns_to_db_schema(gdf)
