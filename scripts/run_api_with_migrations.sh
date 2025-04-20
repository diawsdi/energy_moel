#!/bin/bash
set -e

echo "Waiting for database to be ready..."
# Wait for the database to be ready
for i in {1..30}; do
    if pg_isready -h db -U "$POSTGRES_USER"; then
        echo "Database server is ready!"
        break
    fi
    echo "Waiting for database server... ($i/30)"
    sleep 2
done

# Check if database exists, create it if it doesn't
if ! PGPASSWORD="$POSTGRES_PASSWORD" psql -h db -U "$POSTGRES_USER" -lqt | cut -d \| -f 1 | grep -qw "$POSTGRES_DB"; then
    echo "Database $POSTGRES_DB does not exist. Creating..."
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h db -U "$POSTGRES_USER" -c "CREATE DATABASE $POSTGRES_DB;"
    echo "Database $POSTGRES_DB created."
    
    # Enable PostGIS extensions
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "CREATE EXTENSION IF NOT EXISTS postgis; CREATE EXTENSION IF NOT EXISTS postgis_topology;"
    echo "PostGIS extensions enabled."
else
    echo "Database $POSTGRES_DB already exists."
fi

echo "Applying database migrations..."
# Run migrations but don't fail if they already exist
alembic upgrade head || echo "Migrations may have been applied already, continuing..."

echo "Starting FastAPI server..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 