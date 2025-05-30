#!/usr/bin/env python3
import os
import glob
import geopandas as gpd
import psycopg2
from sqlalchemy import create_engine
from tqdm import tqdm
import numpy as np
import datetime
from shapely.geometry import MultiPolygon

# Database connection parameters - use the port mapping from docker-compose
DB_HOST = "localhost"  # Changed to localhost since we're running outside the container
DB_PORT = "5438"       # Port mapped to the host (from docker-compose.dev.yml)
DB_NAME = "energy_model"
DB_USER = "postgres"
DB_PASS = "password"   # Password from .env file

# Directory containing the GeoPackage files
DATA_DIR = "data/electrification_2025_data"

# Create the SQLAlchemy engine
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

# Get list of all GeoPackage files
gpkg_files = glob.glob(os.path.join(DATA_DIR, "*.gpkg"))
print(f"Found {len(gpkg_files)} GeoPackage files")

# Counter for total buildings processed
total_buildings = 0

# Helper function to convert Polygon to MultiPolygon
def convert_to_multipolygon(geom):
    if geom is None:
        return None
    if geom.geom_type == 'Polygon':
        return MultiPolygon([geom])
    return geom

# Process each file
for gpkg_file in tqdm(gpkg_files):
    try:
        # Print file being processed
        file_name = os.path.basename(gpkg_file)
        print(f"\nProcessing {file_name}")
        
        # Read GeoPackage
        gdf = gpd.read_file(gpkg_file)
        
        # Skip if empty
        if len(gdf) == 0:
            print(f"Skipping empty file: {file_name}")
            continue
        
        # Rename columns to match database schema
        if 'cons (kWh/month)' in gdf.columns:
            gdf = gdf.rename(columns={
                'cons (kWh/month)': 'consumption_kwh_month',
                'std cons (kWh/month)': 'std_consumption_kwh_month'
            })
        else:
            print(f"Required columns missing in {file_name}")
            continue
        
        # Add necessary fields
        gdf['year'] = 2025  # Set the year to 2025
        
        # Map predicted_electrified to has_access
        gdf['has_access'] = gdf['predicted_electrified'].apply(lambda x: True if x == 1 else False)
        
        # Calculate energy_demand_kwh (yearly estimation based on monthly consumption)
        gdf['energy_demand_kwh'] = gdf['consumption_kwh_month'] * 12
        
        # Set building_type as NULL for now
        gdf['building_type'] = None
        
        # Set current timestamp for created_at and updated_at
        current_time = datetime.datetime.now()
        gdf['created_at'] = current_time
        gdf['updated_at'] = current_time
        
        # Set data_source and grid_node_id fields
        gdf['data_source'] = 'electrification_2025_model'
        gdf['grid_node_id'] = None
        
        # Rename the geometry column to 'geom' for PostgreSQL compatibility
        gdf = gdf.rename(columns={gdf.geometry.name: 'geom'}).set_geometry('geom')
        
        # Convert Polygon geometries to MultiPolygon
        gdf['geom'] = gdf['geom'].apply(convert_to_multipolygon)
        
        # Check CRS and set to EPSG:4326 if needed
        if gdf.crs is None:
            gdf = gdf.set_crs(epsg=4326)
        elif gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)
            
        # Columns to keep
        columns_to_keep = [
            'geom', 'area_in_meters', 'year', 'energy_demand_kwh', 
            'has_access', 'building_type', 'created_at', 'updated_at',
            'predicted_prob', 'predicted_electrified', 'consumption_kwh_month', 
            'std_consumption_kwh_month', 'origin', 'origin_id', 'data_source', 'grid_node_id'
        ]
        
        # Make sure all necessary columns exist
        for col in columns_to_keep:
            if col not in gdf.columns and col != 'geom':
                gdf[col] = None
                
        # Select only the columns needed for the database
        gdf = gdf[columns_to_keep]
        
        # Insert data into PostgreSQL
        try:
            gdf.to_postgis(
                name='buildings_energy',
                con=engine,
                if_exists='append',
                index=False
            )
            
            # Update counter
            total_buildings += len(gdf)
            print(f"Imported {len(gdf)} buildings from {file_name}")
        except Exception as e:
            print(f"Error inserting data from {file_name}: {str(e)}")
        
    except Exception as e:
        print(f"Error processing {gpkg_file}: {str(e)}")

print(f"\nTotal buildings imported: {total_buildings}")

# Create indexes for better query performance (if needed)
try:
    with engine.connect() as connection:
        connection.execute("ANALYZE buildings_energy;")
        print("Analyzed the buildings_energy table")
except Exception as e:
    print(f"Error analyzing table: {str(e)}")

print("Import completed successfully") 