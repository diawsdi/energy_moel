#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Enable PostGIS extensions
    CREATE EXTENSION IF NOT EXISTS postgis;
    CREATE EXTENSION IF NOT EXISTS postgis_topology;

    -- Drop existing objects if they exist
    DROP INDEX IF EXISTS idx_buildings_energy_geom;
    DROP INDEX IF EXISTS idx_buildings_energy_year;
    DROP INDEX IF EXISTS idx_buildings_energy_has_access;
    DROP INDEX IF EXISTS idx_buildings_energy_building_type;
    DROP INDEX IF EXISTS idx_buildings_energy_grid_node_id;
    DROP INDEX IF EXISTS ix_buildings_energy_id;
    DROP TABLE IF EXISTS buildings_energy;
    DROP TABLE IF EXISTS alembic_version;
EOSQL

echo "PostGIS extensions enabled and cleaned up any existing tables" 