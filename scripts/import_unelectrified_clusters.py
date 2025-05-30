#!/usr/bin/env python3
import os
import json
import psycopg2
from psycopg2.extras import Json
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = "localhost"
DB_PORT = "5438"  # This is the mapped port in docker-compose.dev.yml
DB_NAME = os.getenv("POSTGRES_DB", "energy_model")

def import_unelectrified_clusters(file_path, year=2025, db_params=None):
    """
    Imports unelectrified clusters from GeoJSON file into PostgreSQL database.
    
    Args:
        file_path (str): Path to the GeoJSON file
        year (int): Year to assign to the imported clusters
        db_params (dict): Database connection parameters
    """
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found")
        return
    
    # Default database parameters
    if db_params is None:
        db_params = {
            'dbname': DB_NAME,
            'user': DB_USER,
            'password': DB_PASSWORD,
            'host': DB_HOST,
            'port': DB_PORT
        }
    
    print(f"Reading GeoJSON file: {file_path}")
    with open(file_path, 'r') as f:
        try:
            geojson_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error parsing GeoJSON file: {e}")
            return
    
    # Connect to the database
    try:
        print(f"Connecting to database: {db_params['host']}:{db_params['port']}/{db_params['dbname']}")
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        print("Connected to the database")
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return
    
    # First clear existing data for this year to avoid duplicates
    try:
        cursor.execute("DELETE FROM unelectrified_clusters WHERE year = %s", (year,))
        print(f"Cleared existing clusters for year {year}")
    except Exception as e:
        print(f"Error clearing existing data: {e}")
        conn.rollback()
        conn.close()
        return
    
    # Process and insert features
    features = geojson_data.get('features', [])
    inserted_count = 0
    error_count = 0
    
    for feature in features:
        try:
            properties = feature.get('properties', {})
            geometry = feature.get('geometry', {})
            
            # Extract properties
            cluster_id = properties.get('cluster_id')
            total_buildings = properties.get('total_buildings')
            total_energy_kwh = properties.get('total_energy_kwh')
            avg_energy_kwh = properties.get('avg_energy_kwh')
            
            # Convert GeoJSON geometry to PostGIS format
            geom_str = json.dumps(geometry)
            
            # Insert into database
            cursor.execute("""
                INSERT INTO unelectrified_clusters 
                (year, area, properties, total_buildings, total_energy_kwh, avg_energy_kwh)
                VALUES (%s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326), %s, %s, %s, %s)
            """, (
                year, 
                geom_str, 
                Json(properties),
                total_buildings,
                total_energy_kwh,
                avg_energy_kwh
            ))
            inserted_count += 1
            
            # Commit every 100 records to avoid large transactions
            if inserted_count % 100 == 0:
                conn.commit()
                print(f"Inserted {inserted_count} clusters...")
                
        except Exception as e:
            error_count += 1
            print(f"Error processing feature: {e}")
            # Continue with next feature rather than aborting the whole import
            conn.rollback()
    
    # Final commit for remaining records
    conn.commit()
    
    print(f"Import completed. Inserted {inserted_count} clusters with {error_count} errors.")
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Import unelectrified clusters from GeoJSON')
    parser.add_argument('--file', required=True, help='Path to GeoJSON file')
    parser.add_argument('--year', type=int, default=2025, help='Year to assign to imported clusters (default: 2025)')
    parser.add_argument('--host', default=DB_HOST, help='Database host')
    parser.add_argument('--port', default=DB_PORT, help='Database port')
    parser.add_argument('--dbname', default=DB_NAME, help='Database name')
    parser.add_argument('--user', default=DB_USER, help='Database user')
    parser.add_argument('--password', default=DB_PASSWORD, help='Database password')
    
    args = parser.parse_args()
    
    db_params = {
        'dbname': args.dbname,
        'user': args.user,
        'password': args.password,
        'host': args.host,
        'port': args.port
    }
    
    import_unelectrified_clusters(args.file, args.year, db_params) 