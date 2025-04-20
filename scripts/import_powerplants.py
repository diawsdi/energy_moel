#!/usr/bin/env python3
"""
Script to import power plants data from a shapefile into the PostgreSQL/PostGIS database.
"""

import os
import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import datetime

# Load environment variables
load_dotenv()

# Database connection parameters
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
# Use localhost and the mapped port (5438) to connect to the Docker container
DB_HOST = "localhost"
DB_PORT = "5438"  # This is the mapped port in docker-compose.dev.yml
DB_NAME = os.getenv("POSTGRES_DB", "energy_model")

# Set paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                       "data", "extracted_powerplants")
SHAPEFILE_PATH = os.path.join(DATA_DIR, "SEN_PowerPlants.shp")

def create_power_plants_table(engine):
    """Create the power_plants table if it doesn't exist."""
    with engine.connect() as conn:
        # Check if PostGIS extension is enabled
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        
        # Create the power_plants table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS power_plants (
                plant_id BIGSERIAL PRIMARY KEY,
                location geometry(Point, 4326),
                plant_name VARCHAR(255),
                year INTEGER,
                plant_type VARCHAR(50),
                capacity_mw NUMERIC,
                annual_gen_gwh NUMERIC,
                status VARCHAR(50),
                country VARCHAR(100),
                iso_code VARCHAR(10),
                data_source VARCHAR(100),
                last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create spatial index
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_power_plants_geom 
            ON power_plants USING GIST (location);
        """))
        
        conn.commit()
        print("Power plants table created successfully")

def import_power_plants(engine):
    """Import power plants data from shapefile to database."""
    try:
        # Read the shapefile
        gdf = gpd.read_file(SHAPEFILE_PATH)
        print(f"Read {len(gdf)} power plants from shapefile")
        
        # If CRS is not set, assume it's WGS 84 (EPSG:4326)
        if gdf.crs is None:
            gdf = gdf.set_crs(epsg=4326)
        elif gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs(epsg=4326)
        
        # Map shapefile columns to database columns
        gdf_transformed = pd.DataFrame()
        gdf_transformed['location'] = gdf['geometry']
        gdf_transformed['plant_name'] = gdf['PLANT']
        gdf_transformed['plant_type'] = gdf['GEN_TYPE']
        gdf_transformed['capacity_mw'] = gdf['SUM_MW']
        gdf_transformed['status'] = gdf['STATUS']
        gdf_transformed['country'] = gdf['COUNTRY']
        gdf_transformed['iso_code'] = gdf['ISO']
        
        # Set default values for missing columns
        current_year = datetime.datetime.now().year
        gdf_transformed['year'] = current_year  # Assume current year as default
        gdf_transformed['data_source'] = 'SEN_PowerPlants.shp'
        
        # Check if table has existing data
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM power_plants"))
            count = result.scalar()
            
            if count > 0:
                print(f"Power plants table already has {count} records.")
                user_input = input("Do you want to continue and potentially add duplicate records? (y/n): ")
                if user_input.lower() != 'y':
                    print("Import aborted by user")
                    return
        
        # Import data to database using SQLAlchemy
        # Convert geometry to WKT format for insertion
        gdf_transformed['geometry_wkt'] = gdf_transformed['location'].apply(lambda geom: geom.wkt)
        
        # Create a connection and begin a transaction
        with engine.begin() as conn:
            for _, row in gdf_transformed.iterrows():
                # Insert each power plant
                conn.execute(text("""
                    INSERT INTO power_plants 
                    (location, plant_name, year, plant_type, capacity_mw, status, country, iso_code, data_source)
                    VALUES (
                        ST_GeomFromText(:geometry_wkt, 4326),
                        :plant_name,
                        :year,
                        :plant_type,
                        :capacity_mw,
                        :status,
                        :country,
                        :iso_code,
                        :data_source
                    )
                """), {
                    'geometry_wkt': row['geometry_wkt'],
                    'plant_name': row['plant_name'],
                    'year': row['year'],
                    'plant_type': row['plant_type'],
                    'capacity_mw': row['capacity_mw'],
                    'status': row['status'],
                    'country': row['country'],
                    'iso_code': row['iso_code'],
                    'data_source': row['data_source']
                })
        
        print(f"Successfully imported {len(gdf)} power plants to database")
        
    except Exception as e:
        print(f"Error importing power plants: {e}")

def main():
    """Main function to run the import process."""
    print("Starting power plants import...")
    
    # Create database connection
    connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)
    
    try:
        # Create table if it doesn't exist
        create_power_plants_table(engine)
        
        # Import data
        import_power_plants(engine)
        
        print("Power plants import completed successfully")
        
    except Exception as e:
        print(f"Error in import process: {e}")
    
    finally:
        engine.dispose()

if __name__ == "__main__":
    main()
