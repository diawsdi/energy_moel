#!/usr/bin/env python3
import os
import json
import psycopg2
from psycopg2.extras import Json
import argparse
from dotenv import load_dotenv
import glob

# Load environment variables
load_dotenv()

# Database connection parameters
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = "localhost"
DB_PORT = "5438"  # This is the mapped port in docker-compose.dev.yml
DB_NAME = os.getenv("POSTGRES_DB", "energy_model")

def import_unelectrified_buildings(directory_path, db_params=None):
    """
    Imports unelectrified buildings from multiple GeoJSON files into PostgreSQL database.
    
    Args:
        directory_path (str): Path to the directory containing GeoJSON files
        db_params (dict): Database connection parameters
    """
    if not os.path.exists(directory_path):
        print(f"Error: Directory {directory_path} not found")
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
    
    # Connect to the database
    try:
        print(f"Connecting to database: {db_params['host']}:{db_params['port']}/{db_params['dbname']}")
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        print("Connected to the database")
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return
    
    # First clear existing data to avoid duplicates
    try:
        cursor.execute("DELETE FROM unelectrified_buildings")
        print("Cleared existing buildings data")
    except Exception as e:
        print(f"Error clearing existing data: {e}")
        conn.rollback()
        conn.close()
        return
    
    # Get list of all GeoJSON files in the directory
    geojson_files = glob.glob(os.path.join(directory_path, "*.geojson"))
    print(f"Found {len(geojson_files)} GeoJSON files to process")
    
    total_inserted = 0
    total_errors = 0
    
    # Process each file
    for file_path in geojson_files:
        file_name = os.path.basename(file_path)
        print(f"Processing file: {file_name}")
        
        # Read the GeoJSON file
        with open(file_path, 'r') as f:
            try:
                geojson_data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error parsing GeoJSON file {file_name}: {e}")
                continue
        
        # Process and insert features
        features = geojson_data.get('features', [])
        inserted_count = 0
        error_count = 0
        
        for feature in features:
            try:
                properties = feature.get('properties', {})
                geometry = feature.get('geometry', {})
                
                # Extract properties with proper column names
                origin = properties.get('origin')
                origin_id = properties.get('origin_id')
                origin_origin_id = properties.get('origin_origin_id')
                area_in_meters = properties.get('area_in_meters')
                n_bldgs_1km_away = properties.get('n_bldgs_1km_away')
                lulc2023_built_area_n1 = properties.get('lulc2023_built_area_N1')
                lulc2023_rangeland_n1 = properties.get('lulc2023_rangeland_N1')
                lulc2023_crops_n1 = properties.get('lulc2023_crops_N1')
                lulc2023_built_area_n11 = properties.get('lulc2023_built_area_N11')
                lulc2023_rangeland_n11 = properties.get('lulc2023_rangeland_N11')
                lulc2023_crops_n11 = properties.get('lulc2023_crops_N11')
                ntl2023_n1 = properties.get('ntl2023_N1')
                ntl2023_n11 = properties.get('ntl2023_N11')
                ookla_fixed_20230101_avg_d_kbps = properties.get('ookla_fixed_20230101_avg_d_kbps')
                ookla_fixed_20230101_devices = properties.get('ookla_fixed_20230101_devices')
                ookla_mobile_20230101_avg_d_kbps = properties.get('ookla_mobile_20230101_avg_d_kbps')
                ookla_mobile_20230101_devices = properties.get('ookla_mobile_20230101_devices')
                predicted_prob = properties.get('predicted_prob')
                predicted_electrified = properties.get('predicted_electrified')
                
                # Handle consumption data - note the different format in source vs table
                # In the GeoJSON, it's "cons (kWh/month)" but in DB it's "consumption_kwh_month"
                consumption_kwh_month = properties.get('cons (kWh/month)')
                std_consumption_kwh_month = properties.get('std cons (kWh/month)')
                
                # Convert GeoJSON geometry to PostGIS format
                geom_str = json.dumps(geometry)
                
                # Insert into database
                cursor.execute("""
                    INSERT INTO unelectrified_buildings 
                    (origin, origin_id, origin_origin_id, area_in_meters, n_bldgs_1km_away, 
                    lulc2023_built_area_n1, lulc2023_rangeland_n1, lulc2023_crops_n1, 
                    lulc2023_built_area_n11, lulc2023_rangeland_n11, lulc2023_crops_n11, 
                    ntl2023_n1, ntl2023_n11, 
                    ookla_fixed_20230101_avg_d_kbps, ookla_fixed_20230101_devices, 
                    ookla_mobile_20230101_avg_d_kbps, ookla_mobile_20230101_devices, 
                    predicted_prob, predicted_electrified, consumption_kwh_month, 
                    std_consumption_kwh_month, geom)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                    ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))
                """, (
                    origin, origin_id, origin_origin_id, area_in_meters, n_bldgs_1km_away,
                    lulc2023_built_area_n1, lulc2023_rangeland_n1, lulc2023_crops_n1,
                    lulc2023_built_area_n11, lulc2023_rangeland_n11, lulc2023_crops_n11,
                    ntl2023_n1, ntl2023_n11,
                    ookla_fixed_20230101_avg_d_kbps, ookla_fixed_20230101_devices,
                    ookla_mobile_20230101_avg_d_kbps, ookla_mobile_20230101_devices,
                    predicted_prob, predicted_electrified, consumption_kwh_month,
                    std_consumption_kwh_month, geom_str
                ))
                inserted_count += 1
            except Exception as e:
                error_count += 1
                if error_count < 10:  # Limit error output to avoid overwhelming logs
                    print(f"Error inserting building: {e}")
                elif error_count == 10:
                    print("Additional errors will not be displayed...")
        
        # Commit changes for this file
        conn.commit()
        
        total_inserted += inserted_count
        total_errors += error_count
        print(f"Processed {file_name}: Inserted {inserted_count} buildings, {error_count} errors")
    
    print(f"Import completed: Total {total_inserted} buildings inserted, {total_errors} errors")
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Import unelectrified buildings from GeoJSON files')
    parser.add_argument('--directory', required=True, help='Path to directory containing GeoJSON files')
    
    # Database connection parameters
    parser.add_argument('--db-host', help='Database host')
    parser.add_argument('--db-port', help='Database port')
    parser.add_argument('--db-name', help='Database name')
    parser.add_argument('--db-user', help='Database user')
    parser.add_argument('--db-password', help='Database password')
    
    args = parser.parse_args()
    
    # Override default database parameters if provided
    db_params = None
    if any([args.db_host, args.db_port, args.db_name, args.db_user, args.db_password]):
        db_params = {
            'dbname': args.db_name or DB_NAME,
            'user': args.db_user or DB_USER,
            'password': args.db_password or DB_PASSWORD,
            'host': args.db_host or DB_HOST,
            'port': args.db_port or DB_PORT
        }
    
    import_unelectrified_buildings(args.directory, db_params)
