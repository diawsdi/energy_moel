#!/usr/bin/env python3
"""
Script to update the database schemas for grid infrastructure tables.
This script will:
1. Drop the existing tables
2. Create new tables with a simplified structure:
   - ID column
   - Year column
   - Geometry column
   - Properties JSON column for all other attributes
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = "localhost"
DB_PORT = "5438"  # This is the mapped port in docker-compose.dev.yml
DB_NAME = os.getenv("POSTGRES_DB", "energy_model")

def create_database_connection():
    """Create and return a database connection engine"""
    connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(connection_string)

def update_schemas(engine):
    """Update the database schemas to the new structure"""
    with engine.begin() as conn:
        print("Dropping existing tables...")
        # Drop existing tables (grid_lines first due to foreign key constraints)
        conn.execute(text("DROP TABLE IF EXISTS grid_lines CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS grid_nodes CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS power_plants CASCADE;"))
        
        print("Creating new grid_nodes table...")
        # Create new grid_nodes table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS grid_nodes (
                node_id BIGSERIAL PRIMARY KEY,
                year INTEGER NOT NULL,
                location geometry(Point, 4326) NOT NULL,
                properties JSONB DEFAULT '{}'::jsonb
            );
            
            CREATE INDEX IF NOT EXISTS idx_grid_nodes_geom ON grid_nodes USING GIST (location);
            CREATE INDEX IF NOT EXISTS idx_grid_nodes_year ON grid_nodes (year);
        """))
        
        print("Creating new grid_lines table...")
        # Create new grid_lines table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS grid_lines (
                line_id BIGSERIAL PRIMARY KEY,
                year INTEGER NOT NULL,
                path geometry(LineString, 4326) NOT NULL,
                properties JSONB DEFAULT '{}'::jsonb
            );
            
            CREATE INDEX IF NOT EXISTS idx_grid_lines_geom ON grid_lines USING GIST (path);
            CREATE INDEX IF NOT EXISTS idx_grid_lines_year ON grid_lines (year);
        """))
        
        print("Creating new power_plants table...")
        # Create new power_plants table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS power_plants (
                plant_id BIGSERIAL PRIMARY KEY,
                year INTEGER NOT NULL,
                location geometry(Point, 4326) NOT NULL,
                properties JSONB DEFAULT '{}'::jsonb
            );
            
            CREATE INDEX IF NOT EXISTS idx_power_plants_geom ON power_plants USING GIST (location);
            CREATE INDEX IF NOT EXISTS idx_power_plants_year ON power_plants (year);
        """))
        
        print("Schema update completed successfully.")

def main():
    """Main function to update the database schemas"""
    print("Starting database schema update...")
    
    # Create database connection
    engine = create_database_connection()
    
    try:
        # Update schemas
        update_schemas(engine)
        
        print("Database schema update completed successfully")
        
    except Exception as e:
        print(f"Error in schema update process: {e}")
    
    finally:
        engine.dispose()

if __name__ == "__main__":
    main() 