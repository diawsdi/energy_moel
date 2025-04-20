#!/bin/bash

# This script imports building data into the PostgreSQL database using Docker

# Ensure .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found. Please create it from .env.example"
    exit 1
fi

# Import environment variables
source .env

# Check if containers are running
if ! docker-compose ps | grep -q "api"; then
    echo "Starting containers..."
    docker-compose up -d
    # Wait for db to be ready
    echo "Waiting for database to be ready..."
    sleep 10
fi

# Run import script inside the API container
echo "Importing building data to database..."
docker-compose exec api python scripts/import_buildings_to_db.py "$@"

echo "Import completed!" 