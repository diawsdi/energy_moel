#!/usr/bin/env python3
"""
Script to import 2025 grid infrastructure data including:
- Grid lines
- Substations (grid nodes)
- Power plants

This script imports data from the 2025gridline directory and updates
the energy model database with the latest grid infrastructure.
"""

import os
import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import datetime
import numpy as np
from shapely.geometry import LineString, Point

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

def create_database_connection():
    """Create and return a database connection engine"""
    connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(connection_string)

def import_substations(engine):
    """Import substations (grid nodes) from the 2025 data"""
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
        
        # Transform the data to match the grid_nodes schema
        nodes_df = pd.DataFrame()
        nodes_df['geometry'] = gdf['geometry']
        nodes_df['node_name'] = gdf['Nom_poste'].fillna(gdf['NOM'])
        
        # Extract voltage from kV_max
        nodes_df['voltage_kv'] = pd.to_numeric(gdf['kV_max'], errors='coerce')
        
        # Set node type based on voltage
        def determine_node_type(voltage):
            if pd.isna(voltage):
                return 'Unknown'
            elif voltage >= 225:
                return 'Transmission Substation'
            elif voltage >= 90:
                return 'High Voltage Substation'
            elif voltage >= 30:
                return 'Medium Voltage Substation'
            else:
                return 'Distribution Substation'
        
        nodes_df['node_type'] = nodes_df['voltage_kv'].apply(determine_node_type)
        nodes_df['status'] = gdf['Status'].fillna('Unknown')
        nodes_df['data_source'] = '2025gridline/Substations_HT.geojson'
        
        # Check if table has existing data
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM grid_nodes"))
            count = result.scalar()
            print(f"Grid nodes table currently has {count} records.")
            
            # Ask for confirmation before importing
            user_input = input("Do you want to continue with importing the new substations? (y/n): ")
            if user_input.lower() != 'y':
                print("Import aborted by user")
                return
        
        # Import data to database
        with engine.begin() as conn:
            nodes_imported = 0
            
            for _, row in nodes_df.iterrows():
                # Convert geometry to WKT for insertion
                geometry_wkt = row['geometry'].wkt
                
                # Insert the grid node
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
                    'geometry_wkt': geometry_wkt,
                    'node_name': row['node_name'],
                    'node_type': row['node_type'],
                    'voltage_kv': row['voltage_kv'],
                    'status': row['status'],
                    'data_source': row['data_source']
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
        
        # Check if table has existing data
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM grid_lines"))
            count = result.scalar()
            print(f"Grid lines table currently has {count} records.")
            
            # Ask for confirmation before importing
            user_input = input("Do you want to continue with importing the new grid lines? (y/n): ")
            if user_input.lower() != 'y':
                print("Import aborted by user")
                return
            
            # Get node mapping for connecting lines to nodes
            result = conn.execute(text("""
                SELECT node_id, node_name, ST_AsText(location) as location_wkt 
                FROM grid_nodes
            """))
            nodes = result.fetchall()
            
            # Create a dictionary of node names to node IDs
            node_name_to_id = {row[1]: row[0] for row in nodes if row[1]}
            
            # Also create a spatial index of nodes for line endpoints that don't have names
            node_points = {row[0]: wkt_to_point(row[2]) for row in nodes}

        # Transform the data to match the grid_lines schema
        lines_df = pd.DataFrame()
        lines_df['geometry'] = gdf['geometry']
        
        # Most of the lines don't have explicit from/to node information
        # We'll set default values and then try to find closest nodes later
        lines_df['voltage_kv'] = 225  # Default to 225kV for high-tension lines
        lines_df['status'] = gdf.get('Status', 'Existing')
        lines_df['country'] = 'Senegal'
        lines_df['project_name'] = '2025 Grid Expansion'
        lines_df['data_source'] = '2025gridline/Grid_Lines.geojson'
        
        # Import data to database
        with engine.begin() as conn:
            lines_imported = 0
            
            for idx, row in lines_df.iterrows():
                # Convert geometry to WKT for insertion
                geometry_wkt = row['geometry'].wkt
                
                # Try to find the closest nodes to the line start and end points
                if isinstance(row['geometry'], LineString):
                    start_point = Point(row['geometry'].coords[0])
                    end_point = Point(row['geometry'].coords[-1])
                    
                    # Find closest nodes (simplified approach)
                    from_node_id, to_node_id = None, None
                    from_node_name, to_node_name = None, None
                    
                    # For a production system, we would use proper spatial queries here
                    # This is a simplified approach for demonstration purposes
                    from_node_id = find_closest_node_id(node_points, start_point)
                    to_node_id = find_closest_node_id(node_points, end_point)
                    
                    # Get node names (if we have the IDs)
                    if from_node_id:
                        result = conn.execute(text("""
                            SELECT node_name FROM grid_nodes WHERE node_id = :node_id
                        """), {'node_id': from_node_id})
                        row_result = result.fetchone()
                        if row_result:
                            from_node_name = row_result[0]
                    
                    if to_node_id:
                        result = conn.execute(text("""
                            SELECT node_name FROM grid_nodes WHERE node_id = :node_id
                        """), {'node_id': to_node_id})
                        row_result = result.fetchone()
                        if row_result:
                            to_node_name = row_result[0]
                    
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
                        'geometry_wkt': geometry_wkt,
                        'from_node_id': from_node_id,
                        'to_node_id': to_node_id,
                        'from_node_name': from_node_name,
                        'to_node_name': to_node_name,
                        'voltage_kv': row['voltage_kv'],
                        'status': row['status'],
                        'country': row['country'],
                        'project_name': row['project_name'],
                        'data_source': row['data_source']
                    })
                    lines_imported += 1
                    
                    # Print progress
                    if lines_imported % 100 == 0:
                        print(f"Imported {lines_imported} lines so far...")
        
        print(f"Successfully imported {lines_imported} grid lines to database")
        
    except Exception as e:
        print(f"Error importing grid lines: {e}")

def wkt_to_point(wkt):
    """Convert a WKT representation of a point to a Point object"""
    # Simple parsing for POINT(lon lat) format
    if wkt.startswith('POINT('):
        coords = wkt.replace('POINT(', '').replace(')', '').split()
        if len(coords) >= 2:
            try:
                return Point(float(coords[0]), float(coords[1]))
            except ValueError:
                return None
    return None

def find_closest_node_id(node_points, target_point):
    """Find the ID of the closest node to the target point"""
    min_dist = float('inf')
    closest_id = None
    
    for node_id, point in node_points.items():
        if point is not None:
            dist = point.distance(target_point)
            if dist < min_dist:
                min_dist = dist
                closest_id = node_id
    
    # Only return if the node is reasonably close (arbitrary threshold)
    # For a real application, this threshold should be carefully tuned
    if min_dist < 0.1:  # ~11 km at the equator
        return closest_id
    return None

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
        
        # Transform the data to match the power_plants schema
        plants_df = pd.DataFrame()
        plants_df['location'] = gdf['geometry']
        plants_df['plant_name'] = gdf['NOM']
        
        # Determine plant type from name or other fields
        def determine_plant_type(name):
            name = str(name).lower()
            if 'solaire' in name or 'solar' in name:
                return 'SOLAR'
            elif 'eolien' in name or 'wind' in name:
                return 'WIND'
            elif 'hydro' in name:
                return 'HYDRO'
            elif 'charbon' in name or 'coal' in name:
                return 'COAL'
            elif 'gaz' in name or 'gas' in name:
                return 'GAS'
            else:
                return 'THERMAL'  # Default to thermal
        
        plants_df['plant_type'] = plants_df['plant_name'].apply(determine_plant_type)
        
        # Extract capacity from name or set default
        def extract_capacity(name):
            name = str(name)
            try:
                # Look for patterns like "60MW", "420 Kilowatts", etc.
                if 'mw' in name.lower() or 'megawatt' in name.lower():
                    for part in name.split():
                        try:
                            return float(part.strip())
                        except ValueError:
                            continue
                elif 'kw' in name.lower() or 'kilowatt' in name.lower():
                    for part in name.split():
                        try:
                            # Convert kW to MW
                            return float(part.strip()) / 1000
                        except ValueError:
                            continue
            except:
                pass
            return None  # Default if we can't extract capacity
        
        plants_df['capacity_mw'] = plants_df['plant_name'].apply(extract_capacity)
        plants_df['status'] = gdf.get('Status', 'Operational')
        plants_df['country'] = 'Senegal'
        plants_df['iso_code'] = 'SEN'
        plants_df['year'] = 2025  # Set the year to 2025 for this dataset
        plants_df['data_source'] = '2025gridline/Power_Plants.geojson'
        
        # Check if table has existing data
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM power_plants"))
            count = result.scalar()
            print(f"Power plants table currently has {count} records.")
            
            # Ask for confirmation before importing
            user_input = input("Do you want to continue with importing the new power plants? (y/n): ")
            if user_input.lower() != 'y':
                print("Import aborted by user")
                return
        
        # Import data to database
        with engine.begin() as conn:
            plants_imported = 0
            
            for _, row in plants_df.iterrows():
                # Convert geometry to WKT for insertion
                geometry_wkt = row['location'].wkt
                
                # Skip if it's a duplicate plant (same name and location)
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM power_plants 
                    WHERE plant_name = :plant_name
                    AND ST_DWithin(
                        location, 
                        ST_GeomFromText(:geometry_wkt, 4326),
                        0.01  -- ~1km at equator
                    )
                """), {
                    'plant_name': row['plant_name'],
                    'geometry_wkt': geometry_wkt
                })
                count = result.scalar()
                
                if count > 0:
                    print(f"Skipping duplicate plant: {row['plant_name']}")
                    continue
                
                # Insert the power plant
                conn.execute(text("""
                    INSERT INTO power_plants 
                    (location, plant_name, year, plant_type, capacity_mw, 
                     status, country, iso_code, data_source)
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
                    'geometry_wkt': geometry_wkt,
                    'plant_name': row['plant_name'],
                    'year': row['year'],
                    'plant_type': row['plant_type'],
                    'capacity_mw': row['capacity_mw'],
                    'status': row['status'],
                    'country': row['country'],
                    'iso_code': row['iso_code'],
                    'data_source': row['data_source']
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
        # First import substations (grid nodes)
        import_substations(engine)
        
        # Then import grid lines (which reference the nodes)
        import_grid_lines(engine)
        
        # Finally import power plants
        import_power_plants(engine)
        
        print("2025 grid infrastructure data import completed successfully")
        
    except Exception as e:
        print(f"Error in import process: {e}")
    
    finally:
        engine.dispose()

if __name__ == "__main__":
    main() 