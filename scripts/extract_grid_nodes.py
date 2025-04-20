#!/usr/bin/env python3
"""
Script to extract grid nodes from the Senegal Electricity Transmission Network
and import them into the PostgreSQL/PostGIS database.
"""

import os
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point, LineString, MultiLineString
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
                       "data", "extracted_transmission")
SHAPEFILE_PATH = os.path.join(DATA_DIR, "Senegal Electricity Transmission Network.shp")

def create_grid_nodes_table(engine):
    """Create the grid_nodes table if it doesn't exist."""
    with engine.connect() as conn:
        # Check if PostGIS extension is enabled
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        
        # Create the grid_nodes table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS grid_nodes (
                node_id BIGSERIAL PRIMARY KEY,
                location geometry(Point, 4326),
                node_name VARCHAR(255),
                node_type VARCHAR(50),
                voltage_kv INTEGER,
                status VARCHAR(50),
                data_source VARCHAR(100),
                last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create spatial index
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_grid_nodes_geom 
            ON grid_nodes USING GIST (location);
        """))
        
        conn.commit()
        print("Grid nodes table created successfully")

def create_grid_lines_table(engine):
    """Create the grid_lines table if it doesn't exist."""
    with engine.connect() as conn:
        # Create the grid_lines table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS grid_lines (
                line_id BIGSERIAL PRIMARY KEY,
                path geometry(LineString, 4326),
                from_node_id BIGINT,
                to_node_id BIGINT,
                from_node_name VARCHAR(255),
                to_node_name VARCHAR(255),
                voltage_kv INTEGER,
                status VARCHAR(50),
                country VARCHAR(50),
                project_name VARCHAR(255),
                data_source VARCHAR(100),
                last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (from_node_id) REFERENCES grid_nodes(node_id) ON DELETE SET NULL,
                FOREIGN KEY (to_node_id) REFERENCES grid_nodes(node_id) ON DELETE SET NULL
            );
        """))
        
        # Create spatial index
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_grid_lines_geom 
            ON grid_lines USING GIST (path);
        """))
        
        conn.commit()
        print("Grid lines table created successfully")

def extract_endpoints(geometry):
    """Extract the start and end points of a LineString or MultiLineString geometry."""
    if geometry is None:
        return None, None
    
    if isinstance(geometry, LineString):
        start_point = Point(geometry.coords[0])
        end_point = Point(geometry.coords[-1])
        return start_point, end_point
    
    elif isinstance(geometry, MultiLineString):
        # For MultiLineString, find the overall start and end points
        # This is a simplification - in reality, you might want more complex logic
        all_coords = []
        for line in geometry.geoms:
            all_coords.extend(list(line.coords))
        
        if all_coords:
            start_point = Point(all_coords[0])
            end_point = Point(all_coords[-1])
            return start_point, end_point
    
    return None, None

def extract_nodes_from_transmission_lines():
    """Extract grid nodes from the transmission network shapefile."""
    try:
        # Read the shapefile
        gdf = gpd.read_file(SHAPEFILE_PATH)
        print(f"Read {len(gdf)} transmission lines from shapefile")
        
        # If CRS is not set, assume it's WGS 84 (EPSG:4326)
        if gdf.crs is None:
            gdf = gdf.set_crs(epsg=4326)
        elif gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs(epsg=4326)
        
        # Create a list to store node information
        nodes = []
        
        # Process each transmission line
        for idx, row in gdf.iterrows():
            # Extract start and end points
            start_point, end_point = extract_endpoints(row.geometry)
            
            # Get node names
            from_name = row.get('FROM_NM')
            to_name = row.get('TO_NM')
            
            # Get voltage and status
            voltage = row.get('VOLTAGE_KV')
            status = row.get('STATUS')
            data_source = row.get('SOURCES')
            
            # Add start node if it has a name
            if start_point and from_name:
                nodes.append({
                    'geometry': start_point,
                    'node_name': from_name,
                    'node_type': 'Substation',  # Assuming all named points are substations
                    'voltage_kv': voltage,
                    'status': status,
                    'data_source': data_source
                })
            
            # Add end node if it has a name
            if end_point and to_name:
                nodes.append({
                    'geometry': end_point,
                    'node_name': to_name,
                    'node_type': 'Substation',  # Assuming all named points are substations
                    'voltage_kv': voltage,
                    'status': status,
                    'data_source': data_source
                })
        
        # Create a GeoDataFrame from the nodes
        if nodes:
            nodes_gdf = gpd.GeoDataFrame(nodes, geometry='geometry', crs="EPSG:4326")
            
            # Remove duplicate nodes based on name and close proximity
            # First, create a spatial index
            nodes_gdf['x'] = nodes_gdf.geometry.x
            nodes_gdf['y'] = nodes_gdf.geometry.y
            
            # Group by node name and take the first occurrence
            nodes_gdf = nodes_gdf.drop_duplicates(subset=['node_name'])
            
            print(f"Extracted {len(nodes_gdf)} unique grid nodes")
            return nodes_gdf
        else:
            print("No nodes with names found in the transmission network")
            return None
    
    except Exception as e:
        print(f"Error extracting nodes: {e}")
        return None

def import_grid_nodes(engine, nodes_gdf):
    """Import grid nodes to the database."""
    if nodes_gdf is None or len(nodes_gdf) == 0:
        print("No nodes to import")
        return
    
    try:
        # Check if table has existing data
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM grid_nodes"))
            count = result.scalar()
            
            if count > 0:
                print(f"Grid nodes table already has {count} records.")
                user_input = input("Do you want to continue and potentially add duplicate records? (y/n): ")
                if user_input.lower() != 'y':
                    print("Import aborted by user")
                    return
        
        # Import nodes to database
        with engine.begin() as conn:
            for _, row in nodes_gdf.iterrows():
                # Insert each node
                conn.execute(text("""
                    INSERT INTO grid_nodes 
                    (location, node_name, node_type, voltage_kv, status, data_source)
                    VALUES (
                        ST_GeomFromText(:geometry_wkt, 4326),
                        :node_name,
                        :node_type,
                        :voltage_kv,
                        :status,
                        :data_source
                    )
                """), {
                    'geometry_wkt': row.geometry.wkt,
                    'node_name': row.node_name,
                    'node_type': row.node_type,
                    'voltage_kv': row.voltage_kv,
                    'status': row.status,
                    'data_source': row.data_source
                })
        
        print(f"Successfully imported {len(nodes_gdf)} grid nodes to database")
        
    except Exception as e:
        print(f"Error importing grid nodes: {e}")

def main():
    """Main function to run the extraction and import process."""
    print("Starting grid nodes extraction and import...")
    
    # Create database connection
    connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)
    
    try:
        # Create tables if they don't exist
        create_grid_nodes_table(engine)
        create_grid_lines_table(engine)
        
        # Extract nodes from transmission lines
        nodes_gdf = extract_nodes_from_transmission_lines()
        
        # Import nodes to database
        if nodes_gdf is not None:
            import_grid_nodes(engine, nodes_gdf)
        
        print("Grid nodes extraction and import completed successfully")
        
    except Exception as e:
        print(f"Error in extraction and import process: {e}")
    
    finally:
        engine.dispose()

if __name__ == "__main__":
    main()
