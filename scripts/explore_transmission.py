#!/usr/bin/env python3
"""
Script to explore the Senegal Electricity Transmission Network shapefile data
and understand its structure before importing it into the database.
"""

import os
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                       "data", "extracted_transmission")
SHAPEFILE_PATH = os.path.join(DATA_DIR, "Senegal Electricity Transmission Network.shp")

def explore_shapefile():
    """Explore the transmission network shapefile and print information about its structure."""
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
        
        # Plot the transmission network
        print("\n--- Creating plot ---")
        fig, ax = plt.subplots(figsize=(10, 10))
        gdf.plot(ax=ax, linewidth=1.5, color='blue')
        plt.title('Electricity Transmission Network in Senegal')
        plt.savefig(os.path.join(DATA_DIR, 'transmission_network_plot.png'))
        print(f"Plot saved to {os.path.join(DATA_DIR, 'transmission_network_plot.png')}")
        
        return gdf
    
    except Exception as e:
        print(f"Error reading shapefile: {e}")
        return None

def suggest_database_schema(gdf):
    """
    Based on the shapefile data, suggest a database schema for the transmission network.
    """
    if gdf is None:
        return
    
    print("\n--- Suggested Database Schema ---")
    print("CREATE TABLE transmission_lines (")
    print("    line_id BIGSERIAL PRIMARY KEY,")
    print("    geometry GEOMETRY(LINESTRING, 4326),")
    
    # Add columns based on the shapefile attributes
    for col in gdf.columns:
        if col != 'geometry':
            dtype = gdf[col].dtype
            if pd.api.types.is_integer_dtype(dtype):
                print(f"    {col.lower()} INTEGER,")
            elif pd.api.types.is_float_dtype(dtype):
                print(f"    {col.lower()} NUMERIC,")
            else:
                print(f"    {col.lower()} VARCHAR(255),")
    
    print("    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP")
    print(");")
    
    print("\nCREATE INDEX idx_transmission_lines_geom ON transmission_lines USING GIST (geometry);")

if __name__ == "__main__":
    print("Exploring Senegal Electricity Transmission Network shapefile...")
    gdf = explore_shapefile()
    
    if gdf is not None:
        suggest_database_schema(gdf)
