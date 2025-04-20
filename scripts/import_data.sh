#!/bin/bash
set -e

# This script handles the import of building energy data
# It ensures the database exists and is properly configured before importing

echo "Checking database connection..."
if ! psql -h db -U "$POSTGRES_USER" -c '\l' | grep -q "$POSTGRES_DB"; then
    echo "Creating database $POSTGRES_DB..."
    psql -h db -U "$POSTGRES_USER" -c "CREATE DATABASE $POSTGRES_DB;"
    
    # Enable PostGIS extensions
    echo "Enabling PostGIS extensions..."
    psql -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "CREATE EXTENSION IF NOT EXISTS postgis; CREATE EXTENSION IF NOT EXISTS postgis_topology;"
fi

echo "Setting up database schema..."
# Create the buildings_energy table if it doesn't exist
psql -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<-EOSQL
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
EOSQL

echo "Checking for batch files..."
# Check if there are any batch files to import
BATCH_DIR="/app/processed_data/batches"
if [ ! -d "$BATCH_DIR" ]; then
    echo "Creating batch directory..."
    mkdir -p "$BATCH_DIR"
fi

BATCH_COUNT=$(find "$BATCH_DIR" -name "*.gpkg" | wc -l)
if [ "$BATCH_COUNT" -eq 0 ]; then
    echo "No batch files found in $BATCH_DIR. Please add .gpkg files to this directory."
    echo "You can use sample data or create test data for development."
    exit 0
fi

echo "Found $BATCH_COUNT batch files. Starting import process..."
# Run the Python import script
python /app/scripts/import_buildings_to_db.py

echo "Import process completed."
