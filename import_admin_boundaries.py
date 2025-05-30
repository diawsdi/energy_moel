#!/usr/bin/env python3
import os
import json
import requests
import psycopg2
from psycopg2.extras import execute_values
import geopandas as gpd
import pandas as pd
from io import BytesIO

# Database connection parameters
DB_PARAMS = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5438"),
    "database": os.environ.get("DB_NAME", "energy_model"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "password")
}

# Admin boundaries endpoints
with open('admin_boundaries.json', 'r') as f:
    admin_endpoints = json.load(f)

# Admin levels mapping
ADMIN_LEVELS = {
    "region": 1,
    "department": 2,
    "arrondissement": 3,
    "commune": 4
}

# Create required tables
def create_tables():
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()
    
    # Drop existing tables (optional - comment this out if you want to keep existing data)
    print("Dropping existing tables...")
    cursor.execute("""
    DROP TABLE IF EXISTS building_statistics CASCADE;
    DROP TABLE IF EXISTS administrative_boundaries CASCADE;
    """)
    
    # Create administrative_boundaries table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS administrative_boundaries (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        level TEXT NOT NULL, -- 'region', 'department', 'arrondissement', 'commune'
        level_num INTEGER NOT NULL, -- 1, 2, 3, 4
        parent_id TEXT REFERENCES administrative_boundaries(id),
        geom GEOMETRY(MULTIPOLYGON, 4326) NOT NULL
    );
    """)
    
    # Create building_statistics table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS building_statistics (
        id SERIAL PRIMARY KEY,
        admin_id TEXT REFERENCES administrative_boundaries(id),
        total_buildings INTEGER DEFAULT 0,
        electrified_buildings INTEGER DEFAULT 0,
        high_confidence_50 INTEGER DEFAULT 0,
        high_confidence_60 INTEGER DEFAULT 0,
        high_confidence_70 INTEGER DEFAULT 0,
        high_confidence_80 INTEGER DEFAULT 0,
        high_confidence_85 INTEGER DEFAULT 0,
        high_confidence_90 INTEGER DEFAULT 0,
        unelectrified_buildings INTEGER DEFAULT 0,
        electrification_rate FLOAT DEFAULT 0,
        high_confidence_rate_50 FLOAT DEFAULT 0,
        high_confidence_rate_60 FLOAT DEFAULT 0,
        high_confidence_rate_70 FLOAT DEFAULT 0,
        high_confidence_rate_80 FLOAT DEFAULT 0,
        high_confidence_rate_85 FLOAT DEFAULT 0,
        high_confidence_rate_90 FLOAT DEFAULT 0,
        avg_consumption_kwh_month FLOAT DEFAULT 0,
        avg_energy_demand_kwh_year FLOAT DEFAULT 0,
        updated_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(admin_id)
    );
    """)
    
    # Create spatial indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS admin_boundaries_geom_idx ON administrative_boundaries USING GIST(geom);")
    cursor.execute("CREATE INDEX IF NOT EXISTS admin_boundaries_level_idx ON administrative_boundaries(level);")
    cursor.execute("CREATE INDEX IF NOT EXISTS admin_boundaries_parent_idx ON administrative_boundaries(parent_id);")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("Tables created successfully")

# Download and import boundaries for each admin level
def import_admin_boundaries():
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()
    
    # Process levels in order from highest (region) to lowest (commune)
    for level_name in ["region", "department", "arrondissement", "commune"]:
        print(f"Importing {level_name} boundaries...")
        
        # Download GeoJSON from API
        response = requests.get(admin_endpoints[level_name])
        if response.status_code != 200:
            print(f"Failed to download {level_name} boundaries: {response.status_code}")
            continue
        
        # Load GeoJSON into GeoDataFrame
        try:
            gdf = gpd.read_file(BytesIO(response.content))
        except Exception as e:
            print(f"Error parsing GeoJSON for {level_name}: {e}")
            continue
        
        # Ensure required columns exist
        required_columns = ['id', 'name']
        parent_id_required = level_name != "region"  # parent_id not required for regions
        
        if parent_id_required:
            required_columns.append('parent_id')
            
        if not all(col in gdf.columns for col in required_columns):
            missing = [col for col in required_columns if col not in gdf.columns]
            print(f"Missing required columns for {level_name}: {missing}")
            continue
        
        # Ensure geometry is in EPSG:4326
        if gdf.crs and gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs("EPSG:4326")
        
        # Convert geometry to MultiPolygon if needed
        gdf['geom'] = gdf['geometry'].apply(lambda g: 
            g if g.geom_type == 'MultiPolygon' else 
            g.__class__([g]) if g.geom_type == 'Polygon' else None
        )
        
        # Insert data into the database
        for _, row in gdf.iterrows():
            admin_id = str(row['id']) if row['id'] is not None else None
            name = row['name']
            
            # For regions, always set parent_id to NULL
            if level_name == "region":
                parent_id = None
                if 'parent_id' in row and row['parent_id'] is not None and not pd.isna(row['parent_id']):
                    print(f"Warning: Region '{name}' has parent_id '{row['parent_id']}'. Setting to NULL as regions are top-level.")
            else:
                # For other levels, validate parent_id exists in the database
                parent_id = str(row['parent_id']) if row['parent_id'] is not None and not pd.isna(row['parent_id']) else None
                
                # Check if parent_id exists in the database
                if parent_id is not None:
                    cursor.execute("SELECT 1 FROM administrative_boundaries WHERE id = %s", (parent_id,))
                    if not cursor.fetchone():
                        print(f"Warning: {level_name} '{name}' has parent_id '{parent_id}' which is not in the database. Setting to NULL.")
                        parent_id = None
            
            # Convert geometry to WKT format
            wkt = row['geom'].wkt if row['geom'] else None
            
            if wkt and admin_id:
                cursor.execute("""
                INSERT INTO administrative_boundaries 
                (id, name, level, level_num, parent_id, geom)
                VALUES (%s, %s, %s, %s, %s, ST_GeomFromText(%s, 4326))
                ON CONFLICT (id) DO UPDATE
                SET name = EXCLUDED.name, 
                    parent_id = EXCLUDED.parent_id,
                    geom = EXCLUDED.geom
                RETURNING id
                """, (
                    admin_id,
                    name, 
                    level_name, 
                    ADMIN_LEVELS[level_name],
                    parent_id, 
                    wkt
                ))
                
                admin_id_inserted = cursor.fetchone()[0]
                
                cursor.execute("""
                INSERT INTO building_statistics (admin_id)
                VALUES (%s)
                ON CONFLICT (admin_id) DO NOTHING
                """, (admin_id_inserted,))
        
        conn.commit()
        print(f"Successfully imported {level_name} boundaries")
    
    cursor.close()
    conn.close()

# Calculate statistics for each administrative area
def calculate_statistics():
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()
    
    # First calculate statistics for communes (lowest level)
    print("Calculating statistics for communes...")
    cursor.execute("""
    UPDATE building_statistics bs
    SET 
        total_buildings = subquery.total_buildings,
        electrified_buildings = subquery.electrified_buildings,
        high_confidence_50 = subquery.high_confidence_50,
        high_confidence_60 = subquery.high_confidence_60,
        high_confidence_70 = subquery.high_confidence_70,
        high_confidence_80 = subquery.high_confidence_80,
        high_confidence_85 = subquery.high_confidence_85,
        high_confidence_90 = subquery.high_confidence_90,
        unelectrified_buildings = subquery.unelectrified_buildings,
        electrification_rate = CASE 
            WHEN subquery.total_buildings > 0 
            THEN (subquery.electrified_buildings::float / subquery.total_buildings::float) * 100 
            ELSE 0 
        END,
        high_confidence_rate_50 = CASE 
            WHEN subquery.total_buildings > 0 
            THEN (subquery.high_confidence_50::float / subquery.total_buildings::float) * 100 
            ELSE 0 
        END,
        high_confidence_rate_60 = CASE 
            WHEN subquery.total_buildings > 0 
            THEN (subquery.high_confidence_60::float / subquery.total_buildings::float) * 100 
            ELSE 0 
        END,
        high_confidence_rate_70 = CASE 
            WHEN subquery.total_buildings > 0 
            THEN (subquery.high_confidence_70::float / subquery.total_buildings::float) * 100 
            ELSE 0 
        END,
        high_confidence_rate_80 = CASE 
            WHEN subquery.total_buildings > 0 
            THEN (subquery.high_confidence_80::float / subquery.total_buildings::float) * 100 
            ELSE 0 
        END,
        high_confidence_rate_85 = CASE 
            WHEN subquery.total_buildings > 0 
            THEN (subquery.high_confidence_85::float / subquery.total_buildings::float) * 100 
            ELSE 0 
        END,
        high_confidence_rate_90 = CASE 
            WHEN subquery.total_buildings > 0 
            THEN (subquery.high_confidence_90::float / subquery.total_buildings::float) * 100 
            ELSE 0 
        END,
        avg_consumption_kwh_month = subquery.avg_consumption_kwh_month,
        avg_energy_demand_kwh_year = subquery.avg_energy_demand_kwh_year,
        updated_at = NOW()
    FROM (
        SELECT 
            ab.id as admin_id,
            COUNT(be.*) as total_buildings,
            SUM(CASE WHEN be.predicted_electrified = 1 THEN 1 ELSE 0 END) as electrified_buildings,
            SUM(CASE WHEN be.predicted_electrified = 1 AND be.predicted_prob > 0.5 THEN 1 ELSE 0 END) as high_confidence_50,
            SUM(CASE WHEN be.predicted_electrified = 1 AND be.predicted_prob > 0.6 THEN 1 ELSE 0 END) as high_confidence_60,
            SUM(CASE WHEN be.predicted_electrified = 1 AND be.predicted_prob > 0.7 THEN 1 ELSE 0 END) as high_confidence_70,
            SUM(CASE WHEN be.predicted_electrified = 1 AND be.predicted_prob > 0.8 THEN 1 ELSE 0 END) as high_confidence_80,
            SUM(CASE WHEN be.predicted_electrified = 1 AND be.predicted_prob > 0.85 THEN 1 ELSE 0 END) as high_confidence_85,
            SUM(CASE WHEN be.predicted_electrified = 1 AND be.predicted_prob > 0.9 THEN 1 ELSE 0 END) as high_confidence_90,
            SUM(CASE WHEN be.predicted_electrified = 0 OR be.predicted_electrified IS NULL THEN 1 ELSE 0 END) as unelectrified_buildings,
            AVG(be.consumption_kwh_month) as avg_consumption_kwh_month,
            AVG(be.energy_demand_kwh) as avg_energy_demand_kwh_year
        FROM 
            administrative_boundaries ab
        LEFT JOIN 
            buildings_energy be ON ST_Contains(ab.geom, be.geom)
        WHERE 
            ab.level = 'commune'
        GROUP BY 
            ab.id
    ) as subquery
    WHERE 
        bs.admin_id = subquery.admin_id
    """)
    
    conn.commit()
    print("Commune statistics calculated")
    
    # Now aggregate statistics up the hierarchy (arrondissement, department, region)
    for level_name in ["arrondissement", "department", "region"]:
        print(f"Aggregating statistics for {level_name}...")
        cursor.execute("""
        UPDATE building_statistics bs
        SET 
            total_buildings = subquery.total_buildings,
            electrified_buildings = subquery.electrified_buildings,
            high_confidence_50 = subquery.high_confidence_50,
            high_confidence_60 = subquery.high_confidence_60,
            high_confidence_70 = subquery.high_confidence_70,
            high_confidence_80 = subquery.high_confidence_80,
            high_confidence_85 = subquery.high_confidence_85,
            high_confidence_90 = subquery.high_confidence_90,
            unelectrified_buildings = subquery.unelectrified_buildings,
            electrification_rate = CASE 
                WHEN subquery.total_buildings > 0 
                THEN (subquery.electrified_buildings::float / subquery.total_buildings::float) * 100 
                ELSE 0 
            END,
            high_confidence_rate_50 = CASE 
                WHEN subquery.total_buildings > 0 
                THEN (subquery.high_confidence_50::float / subquery.total_buildings::float) * 100 
                ELSE 0 
            END,
            high_confidence_rate_60 = CASE 
                WHEN subquery.total_buildings > 0 
                THEN (subquery.high_confidence_60::float / subquery.total_buildings::float) * 100 
                ELSE 0 
            END,
            high_confidence_rate_70 = CASE 
                WHEN subquery.total_buildings > 0 
                THEN (subquery.high_confidence_70::float / subquery.total_buildings::float) * 100 
                ELSE 0 
            END,
            high_confidence_rate_80 = CASE 
                WHEN subquery.total_buildings > 0 
                THEN (subquery.high_confidence_80::float / subquery.total_buildings::float) * 100 
                ELSE 0 
            END,
            high_confidence_rate_85 = CASE 
                WHEN subquery.total_buildings > 0 
                THEN (subquery.high_confidence_85::float / subquery.total_buildings::float) * 100 
                ELSE 0 
            END,
            high_confidence_rate_90 = CASE 
                WHEN subquery.total_buildings > 0 
                THEN (subquery.high_confidence_90::float / subquery.total_buildings::float) * 100 
                ELSE 0 
            END,
            avg_consumption_kwh_month = subquery.avg_consumption_kwh_month,
            avg_energy_demand_kwh_year = subquery.avg_energy_demand_kwh_year,
            updated_at = NOW()
        FROM (
            SELECT 
                parent.id as admin_id,
                SUM(child_stats.total_buildings) as total_buildings,
                SUM(child_stats.electrified_buildings) as electrified_buildings,
                SUM(child_stats.high_confidence_50) as high_confidence_50,
                SUM(child_stats.high_confidence_60) as high_confidence_60,
                SUM(child_stats.high_confidence_70) as high_confidence_70,
                SUM(child_stats.high_confidence_80) as high_confidence_80,
                SUM(child_stats.high_confidence_85) as high_confidence_85,
                SUM(child_stats.high_confidence_90) as high_confidence_90,
                SUM(child_stats.unelectrified_buildings) as unelectrified_buildings,
                AVG(child_stats.avg_consumption_kwh_month) as avg_consumption_kwh_month,
                AVG(child_stats.avg_energy_demand_kwh_year) as avg_energy_demand_kwh_year
            FROM 
                administrative_boundaries parent
            JOIN 
                administrative_boundaries child ON child.parent_id = parent.id
            JOIN 
                building_statistics child_stats ON child_stats.admin_id = child.id
            WHERE 
                parent.level = %s
            GROUP BY 
                parent.id
        ) as subquery
        WHERE 
            bs.admin_id = subquery.admin_id
        """, (level_name,))
        
        conn.commit()
        print(f"{level_name} statistics aggregated")
    
    cursor.close()
    conn.close()

# Create views for vector tiles
def create_vector_tile_views():
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()
    
    # Create view for vector tiles
    cursor.execute("""
    DROP VIEW IF EXISTS admin_statistics_view;
    CREATE VIEW admin_statistics_view AS
    SELECT 
        ab.id, 
        ab.name, 
        ab.level, 
        ab.level_num,
        ab.parent_id, 
        bs.total_buildings, 
        bs.electrified_buildings, 
        bs.high_confidence_50,
        bs.high_confidence_60,
        bs.high_confidence_70,
        bs.high_confidence_80,
        bs.high_confidence_85,
        bs.high_confidence_90,
        bs.unelectrified_buildings,
        bs.electrification_rate, 
        bs.high_confidence_rate_50,
        bs.high_confidence_rate_60,
        bs.high_confidence_rate_70,
        bs.high_confidence_rate_80,
        bs.high_confidence_rate_85,
        bs.high_confidence_rate_90,
        bs.avg_consumption_kwh_month, 
        bs.avg_energy_demand_kwh_year,
        ab.geom
    FROM 
        administrative_boundaries ab
    JOIN 
        building_statistics bs ON ab.id = bs.admin_id;
    """)
    
    # Create materialized view for better performance
    cursor.execute("""
    DROP MATERIALIZED VIEW IF EXISTS admin_statistics_materialized;
    CREATE MATERIALIZED VIEW admin_statistics_materialized AS
    SELECT * FROM admin_statistics_view;
    
    CREATE INDEX IF NOT EXISTS admin_stats_mat_level_idx ON admin_statistics_materialized(level);
    CREATE INDEX IF NOT EXISTS admin_stats_mat_geom_idx ON admin_statistics_materialized USING GIST(geom);
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("Vector tile views created")

if __name__ == "__main__":
    print("Creating database tables...")
    create_tables()
    
    print("Importing administrative boundaries...")
    import_admin_boundaries()
    
    print("Calculating statistics...")
    calculate_statistics()
    
    print("Creating vector tile views...")
    create_vector_tile_views()
    
    print("Done!") 