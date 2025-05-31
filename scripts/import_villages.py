#!/usr/bin/env python3
import os
import json
import uuid
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_PARAMS = {
    "host": "localhost",
    "port": "5438",
    "database": "energy_model",
    "user": "postgres",
    "password": "password"
}

def create_db_engine():
    """Create database engine."""
    return create_engine(
        f"postgresql://{DB_PARAMS['user']}:{DB_PARAMS['password']}@{DB_PARAMS['host']}:{DB_PARAMS['port']}/{DB_PARAMS['database']}"
    )

def recreate_village_points_table(engine):
    """Recreate the village_points table with updated structure."""
    with engine.connect() as conn:
        # Drop the existing table if it exists
        conn.execute(text("DROP TABLE IF EXISTS village_points CASCADE"))
        
        # Create the village_points table without commune_id
        conn.execute(text("""
        CREATE TABLE village_points (
            id VARCHAR PRIMARY KEY,
            name VARCHAR NOT NULL,
            geometry geometry(Point, 4326) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX village_points_geom_idx ON village_points USING GIST(geometry);
        CREATE INDEX village_points_name_idx ON village_points (name);
        """))
        
        conn.commit()
        print("Recreated village_points table")

def import_villages():
    """Import villages from GeoJSON file."""
    print("Starting village import...")
    
    # Read GeoJSON file
    file_path = "data/Village.geojson"
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Create database engine
    engine = create_db_engine()
    
    # Recreate the table with new structure
    recreate_village_points_table(engine)
    
    # Prepare data for bulk insert
    values = []
    
    # Process villages
    for feature in data['features']:
        props = feature['properties']
        geom = feature['geometry']
        
        # Create a unique ID
        village_id = str(uuid.uuid4())
        
        # Extract properties
        name = props['LOCALITE']
        
        values.append({
            'id': village_id,
            'name': name,
            'geometry': json.dumps(geom)
        })
        
        # Print progress
        if len(values) % 100 == 0:
            print(f"Processed {len(values)} villages...")
    
    # Bulk insert data
    with engine.connect() as conn:
        # Insert in batches of 100
        batch_size = 100
        for i in range(0, len(values), batch_size):
            batch = values[i:i + batch_size]
            
            # Prepare the insert statement
            insert_stmt = text("""
                INSERT INTO village_points (id, name, geometry)
                VALUES (:id, :name, ST_SetSRID(ST_GeomFromGeoJSON(:geometry), 4326))
            """)
            
            conn.execute(insert_stmt, batch)
            conn.commit()
            print(f"Imported {min(i + batch_size, len(values))} of {len(values)} villages")
    
    print("\nImport Summary:")
    print(f"Total villages processed: {len(data['features'])}")
    print(f"Successfully imported: {len(values)}")

if __name__ == "__main__":
    import_villages() 