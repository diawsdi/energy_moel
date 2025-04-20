#!/usr/bin/env python3
"""
Script to import grid lines from the Senegal Electricity Transmission Network
and link them to the grid nodes in the PostgreSQL/PostGIS database.
"""

import os
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, MultiLineString
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

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
                       "data", "extracted_transmission")
SHAPEFILE_PATH = os.path.join(DATA_DIR, "Senegal Electricity Transmission Network.shp")

def get_node_ids(conn, from_name, to_name):
    """Get the node IDs for the from and to nodes based on their names."""
    from_node_id = None
    to_node_id = None
    
    if from_name:
        result = conn.execute(text(
            "SELECT node_id FROM grid_nodes WHERE node_name = :node_name"
        ), {"node_name": from_name})
        row = result.fetchone()
        if row:
            from_node_id = row[0]
    
    if to_name:
        result = conn.execute(text(
            "SELECT node_id FROM grid_nodes WHERE node_name = :node_name"
        ), {"node_name": to_name})
        row = result.fetchone()
        if row:
            to_node_id = row[0]
    
    return from_node_id, to_node_id

def convert_multilinestring_to_linestring(geometry):
    """Convert MultiLineString to LineString by concatenating all segments."""
    if geometry is None:
        return None
    
    if isinstance(geometry, LineString):
        return geometry
    
    if isinstance(geometry, MultiLineString):
        # Collect all coordinates from all linestrings
        all_coords = []
        for line in geometry.geoms:
            all_coords.extend(list(line.coords))
        
        # Create a new LineString with all coordinates
        if all_coords:
            return LineString(all_coords)
    
    return None

def import_grid_lines(engine):
    """Import grid lines from the transmission network shapefile and link to nodes."""
    try:
        # Read the shapefile
        gdf = gpd.read_file(SHAPEFILE_PATH)
        print(f"Read {len(gdf)} transmission lines from shapefile")
        
        # If CRS is not set, assume it's WGS 84 (EPSG:4326)
        if gdf.crs is None:
            gdf = gdf.set_crs(epsg=4326)
        elif gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs(epsg=4326)
        
        # Check if table has existing data
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM grid_lines"))
            count = result.scalar()
            
            if count > 0:
                print(f"Grid lines table already has {count} records.")
                user_input = input("Do you want to continue and potentially add duplicate records? (y/n): ")
                if user_input.lower() != 'y':
                    print("Import aborted by user")
                    return
        
        # Import lines to database
        with engine.begin() as conn:
            lines_imported = 0
            
            for idx, row in gdf.iterrows():
                # Convert MultiLineString to LineString if needed
                geometry = convert_multilinestring_to_linestring(row.geometry)
                
                if geometry is None:
                    print(f"Skipping line {idx}: Invalid geometry")
                    continue
                
                # Get from and to node names
                from_name = row.get('FROM_NM')
                to_name = row.get('TO_NM')
                
                # Get node IDs
                from_node_id, to_node_id = get_node_ids(conn, from_name, to_name)
                
                # Insert the grid line
                conn.execute(text("""
                    INSERT INTO grid_lines 
                    (path, from_node_id, to_node_id, from_node_name, to_node_name, 
                     voltage_kv, status, country, project_name, data_source)
                    VALUES (
                        ST_GeomFromText(:geometry_wkt, 4326),
                        :from_node_id,
                        :to_node_id,
                        :from_node_name,
                        :to_node_name,
                        :voltage_kv,
                        :status,
                        :country,
                        :project_name,
                        :data_source
                    )
                """), {
                    'geometry_wkt': geometry.wkt,
                    'from_node_id': from_node_id,
                    'to_node_id': to_node_id,
                    'from_node_name': from_name,
                    'to_node_name': to_name,
                    'voltage_kv': row.get('VOLTAGE_KV'),
                    'status': row.get('STATUS'),
                    'country': row.get('COUNTRY'),
                    'project_name': row.get('PROJECT_NM'),
                    'data_source': row.get('SOURCES')
                })
                
                lines_imported += 1
        
        print(f"Successfully imported {lines_imported} grid lines to database")
        
    except Exception as e:
        print(f"Error importing grid lines: {e}")

def main():
    """Main function to run the import process."""
    print("Starting grid lines import...")
    
    # Create database connection
    connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)
    
    try:
        # Import lines to database
        import_grid_lines(engine)
        
        print("Grid lines import completed successfully")
        
    except Exception as e:
        print(f"Error in import process: {e}")
    
    finally:
        engine.dispose()

if __name__ == "__main__":
    main()
