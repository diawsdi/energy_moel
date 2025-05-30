#!/usr/bin/env python3
"""
Script to import 2025 grid infrastructure data including:
- Grid lines
- Grid nodes (substations)
- Power plants

This script imports data from the 2025gridline directory and updates
the energy model database with the latest grid infrastructure.
Uses the new schema with year column and JSON properties.
"""

import os
import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import json
from shapely.geometry import LineString, Point, shape
import datetime
import numpy as np

# Load environment variables
load_dotenv()

# Database connection parameters
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = "localhost"
DB_PORT = "5438"  # This is the mapped port in docker-compose.dev.yml
DB_NAME = os.getenv("POSTGRES_DB", "energy_model")

# Set paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                       "data", "2025gridline")
GRID_LINES_PATH = os.path.join(DATA_DIR, "Grid_Lines.geojson")
SUBSTATIONS_PATH = os.path.join(DATA_DIR, "Substations_HT.geojson")
POWER_PLANTS_PATH = os.path.join(DATA_DIR, "Power_Plants.geojson")

# Target year for this dataset
TARGET_YEAR = 2025

def create_database_connection():
    """Create and return a database connection engine"""
    connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(connection_string)

def import_substations(engine):
    """Import substations as grid nodes from the 2025 data"""
    print("Importing substations as grid nodes...")
    
    try:
        # Read the GeoJSON file
        gdf = gpd.read_file(SUBSTATIONS_PATH)
        print(f"Read {len(gdf)} substations from GeoJSON")
        
        # If CRS is not set, assume it's WGS 84 (EPSG:4326)
        if gdf.crs is None:
            gdf = gdf.set_crs(epsg=4326)
        elif gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs(epsg=4326)
        
        # Import data to database
        with engine.begin() as conn:
            nodes_imported = 0
            
            for _, row in gdf.iterrows():
                # Extract properties as a JSON object, excluding the geometry
                properties = row.to_dict()
                if 'geometry' in properties:
                    del properties['geometry']
                
                # Handle NaN values by replacing them with None (will be null in JSON)
                for key, value in properties.items():
                    if isinstance(value, float) and np.isnan(value):
                        properties[key] = None
                
                # Convert geometry to WKT for insertion
                geometry_wkt = row['geometry'].wkt
                
                # Insert the grid node
                conn.execute(text("""
                    INSERT INTO grid_nodes 
                    (year, location, properties)
                    VALUES (
                        :year,
                        ST_GeomFromText(:geometry_wkt, 4326),
                        :properties
                    )
                """), {
                    'year': TARGET_YEAR,
                    'geometry_wkt': geometry_wkt,
                    'properties': json.dumps(properties)
                })
                nodes_imported += 1
        
        print(f"Successfully imported {nodes_imported} grid nodes to database")
        
    except Exception as e:
        print(f"Error importing substations: {e}")

def import_grid_lines(engine):
    """Import grid lines from the 2025 data"""
    print("Importing grid lines...")
    
    try:
        # Read the GeoJSON file
        gdf = gpd.read_file(GRID_LINES_PATH)
        print(f"Read {len(gdf)} grid lines from GeoJSON")
        
        # If CRS is not set, assume it's WGS 84 (EPSG:4326)
        if gdf.crs is None:
            gdf = gdf.set_crs(epsg=4326)
        elif gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs(epsg=4326)
        
        # Import data to database
        with engine.begin() as conn:
            lines_imported = 0
            
            for idx, row in gdf.iterrows():
                # Extract properties as a JSON object, excluding the geometry
                properties = row.to_dict()
                if 'geometry' in properties:
                    del properties['geometry']
                
                # Handle NaN values by replacing them with None (will be null in JSON)
                for key, value in properties.items():
                    if isinstance(value, float) and np.isnan(value):
                        properties[key] = None
                
                # Add additional metadata
                properties['data_source'] = '2025gridline/Grid_Lines.geojson'
                properties['import_date'] = datetime.datetime.now().isoformat()
                
                # Ensure the geometry is a LineString
                if isinstance(row['geometry'], LineString):
                    # Convert geometry to WKT for insertion
                    geometry_wkt = row['geometry'].wkt
                    
                    # Insert the grid line
                    conn.execute(text("""
                        INSERT INTO grid_lines 
                        (year, path, properties)
                        VALUES (
                            :year,
                            ST_GeomFromText(:geometry_wkt, 4326),
                            :properties
                        )
                    """), {
                        'year': TARGET_YEAR,
                        'geometry_wkt': geometry_wkt,
                        'properties': json.dumps(properties)
                    })
                    lines_imported += 1
                    
                    # Print progress
                    if lines_imported % 100 == 0:
                        print(f"Imported {lines_imported} lines so far...")
        
        print(f"Successfully imported {lines_imported} grid lines to database")
        
    except Exception as e:
        print(f"Error importing grid lines: {e}")

def import_power_plants(engine):
    """Import power plants from the 2025 data"""
    print("Importing power plants...")
    
    try:
        # Read the GeoJSON file
        gdf = gpd.read_file(POWER_PLANTS_PATH)
        print(f"Read {len(gdf)} power plants from GeoJSON")
        
        # If CRS is not set, assume it's WGS 84 (EPSG:4326)
        if gdf.crs is None:
            gdf = gdf.set_crs(epsg=4326)
        elif gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs(epsg=4326)
        
        # Import data to database
        with engine.begin() as conn:
            plants_imported = 0
            
            for _, row in gdf.iterrows():
                # Extract properties as a JSON object, excluding the geometry
                properties = row.to_dict()
                if 'geometry' in properties:
                    del properties['geometry']
                
                # Handle NaN values by replacing them with None (will be null in JSON)
                for key, value in properties.items():
                    if isinstance(value, float) and np.isnan(value):
                        properties[key] = None
                
                # Add additional metadata
                properties['data_source'] = '2025gridline/Power_Plants.geojson'
                properties['import_date'] = datetime.datetime.now().isoformat()
                
                # Determine plant type from name for the properties
                name = str(properties.get('NOM', '')).lower()
                if 'solaire' in name or 'solar' in name:
                    properties['plant_type'] = 'SOLAR'
                elif 'eolien' in name or 'wind' in name:
                    properties['plant_type'] = 'WIND'
                elif 'hydro' in name:
                    properties['plant_type'] = 'HYDRO'
                elif 'charbon' in name or 'coal' in name:
                    properties['plant_type'] = 'COAL'
                elif 'gaz' in name or 'gas' in name:
                    properties['plant_type'] = 'GAS'
                else:
                    properties['plant_type'] = 'THERMAL'  # Default to thermal
                
                # Convert geometry to WKT for insertion
                geometry_wkt = row['geometry'].wkt
                
                # Insert the power plant
                conn.execute(text("""
                    INSERT INTO power_plants 
                    (year, location, properties)
                    VALUES (
                        :year,
                        ST_GeomFromText(:geometry_wkt, 4326),
                        :properties
                    )
                """), {
                    'year': TARGET_YEAR,
                    'geometry_wkt': geometry_wkt,
                    'properties': json.dumps(properties)
                })
                plants_imported += 1
        
        print(f"Successfully imported {plants_imported} power plants to database")
        
    except Exception as e:
        print(f"Error importing power plants: {e}")

def main():
    """Main function to run the import process."""
    print("Starting 2025 grid infrastructure data import...")
    
    # Create database connection
    engine = create_database_connection()
    
    try:
        # Import substations (grid nodes)
        import_substations(engine)
        
        # Import grid lines
        import_grid_lines(engine)
        
        # Import power plants
        import_power_plants(engine)
        
        print("2025 grid infrastructure data import completed successfully")
        
    except Exception as e:
        print(f"Error in import process: {e}")
    
    finally:
        engine.dispose()

if __name__ == "__main__":
    main() 