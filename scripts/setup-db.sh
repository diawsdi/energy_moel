#!/bin/bash
set -e

# This script sets up the database for the Energy Model project
# It creates the database if it doesn't exist, enables PostGIS extensions,
# and creates the necessary tables and indexes

# Function to check if database exists
database_exists() {
  psql -U "$POSTGRES_USER" -lqt | cut -d \| -f 1 | grep -qw "$POSTGRES_DB"
}

# Function to create database if it doesn't exist
create_database_if_not_exists() {
  if ! database_exists; then
    echo "Creating database $POSTGRES_DB..."
    psql -U "$POSTGRES_USER" -c "CREATE DATABASE $POSTGRES_DB;"
    echo "Database $POSTGRES_DB created."
  else
    echo "Database $POSTGRES_DB already exists."
  fi
}

# Create database if it doesn't exist
create_database_if_not_exists

# Connect to the database and set up schema
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<-EOSQL
    -- Enable PostGIS extensions
    CREATE EXTENSION IF NOT EXISTS postgis;
    CREATE EXTENSION IF NOT EXISTS postgis_topology;
    
    -- Create buildings_energy table if it doesn't exist
    CREATE TABLE IF NOT EXISTS buildings_energy (
        id SERIAL PRIMARY KEY,
        geom GEOMETRY(MULTIPOLYGON, 4326) NOT NULL,
        area_in_meters FLOAT,
        year INTEGER NOT NULL,
        energy_demand_kwh FLOAT,
        has_access BOOLEAN,
        building_type VARCHAR,
        data_source VARCHAR,
        grid_node_id VARCHAR,
        origin_id VARCHAR,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
    );
    
    -- Create indexes if they don't exist
    CREATE INDEX IF NOT EXISTS idx_buildings_energy_geom ON buildings_energy USING gist (geom);
    CREATE INDEX IF NOT EXISTS idx_buildings_energy_year ON buildings_energy (year);
    CREATE INDEX IF NOT EXISTS idx_buildings_energy_has_access ON buildings_energy (has_access);
    CREATE INDEX IF NOT EXISTS idx_buildings_energy_building_type ON buildings_energy (building_type);
    CREATE INDEX IF NOT EXISTS idx_buildings_energy_grid_node_id ON buildings_energy (grid_node_id);
    CREATE INDEX IF NOT EXISTS ix_buildings_energy_id ON buildings_energy (id);
    
    -- Create alembic_version table if it doesn't exist (for migrations)
    CREATE TABLE IF NOT EXISTS alembic_version (
        version_num VARCHAR(32) NOT NULL,
        CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
    );
    
    -- Insert initial version if table is empty
    INSERT INTO alembic_version (version_num)
    SELECT '001'
    WHERE NOT EXISTS (SELECT 1 FROM alembic_version);
EOSQL

echo "Database setup complete. PostGIS extensions enabled and tables created."
