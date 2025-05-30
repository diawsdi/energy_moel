#!/usr/bin/env python3
import os
import geopandas as gpd
import psycopg2
from sqlalchemy import create_engine
import datetime
from shapely.geometry import MultiPolygon

# Database connection parameters
DB_HOST = "localhost"
DB_PORT = "5438"
DB_NAME = "energy_model"
DB_USER = "postgres"
DB_PASS = "password"  # Updated password from .env file

# Create the SQLAlchemy engine
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

# Single file to test
test_file = "data/electrification_2025_data/441617_processed_predictions.gpkg"

print(f"Processing {test_file}")

# Read GeoPackage
gdf = gpd.read_file(test_file)

# Display information
print(f"Number of records: {len(gdf)}")
print(f"Columns: {gdf.columns.tolist()}")
print(f"Geometry column name: {gdf.geometry.name}")
print(f"CRS: {gdf.crs}")
print(f"Geometry type: {gdf.geometry.iloc[0].geom_type}")

# Rename columns to match database schema
if 'cons (kWh/month)' in gdf.columns:
    gdf = gdf.rename(columns={
        'cons (kWh/month)': 'consumption_kwh_month',
        'std cons (kWh/month)': 'std_consumption_kwh_month'
    })

# Add necessary fields
gdf['year'] = 2025
gdf['has_access'] = gdf['predicted_electrified'].apply(lambda x: True if x == 1 else False)
gdf['energy_demand_kwh'] = gdf['consumption_kwh_month'] * 12
gdf['building_type'] = None
gdf['data_source'] = 'electrification_2025_model'
gdf['grid_node_id'] = None

# Set timestamps
current_time = datetime.datetime.now()
gdf['created_at'] = current_time
gdf['updated_at'] = current_time

# Handle geometry column and convert Polygon to MultiPolygon
gdf = gdf.rename(columns={gdf.geometry.name: 'geom'}).set_geometry('geom')

# Convert Polygon to MultiPolygon
def convert_to_multipolygon(geom):
    if geom.geom_type == 'Polygon':
        return MultiPolygon([geom])
    return geom

gdf['geom'] = gdf['geom'].apply(convert_to_multipolygon)

# Check CRS
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

# Select only needed columns
gdf = gdf[columns_to_keep]

# Print first row for verification
print("\nFirst row data:")
first_row = gdf.iloc[0]
for col in columns_to_keep:
    if col != 'geom':
        print(f"{col}: {first_row[col]}")
print(f"Geometry type after conversion: {gdf.geometry.iloc[0].geom_type}")

# Try to insert data
try:
    print("\nInserting data into PostgreSQL...")
    gdf.to_postgis(
        name='buildings_energy',
        con=engine,
        if_exists='append',
        index=False
    )
    print(f"Successfully imported {len(gdf)} buildings")
except Exception as e:
    print(f"Error inserting data: {str(e)}")

print("Script completed") 