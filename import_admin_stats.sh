#!/bin/bash
set -e

# Create and activate virtual environment
if [ ! -d "./venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv ./venv
fi

echo "Activating virtual environment..."
source ./venv/bin/activate

# Install required packages
echo "Installing required Python packages..."
pip install psycopg2-binary geopandas pandas requests

# Run the import script
echo "Importing administrative boundaries and calculating statistics..."
python import_admin_boundaries.py

# Restart Martin to apply changes
echo "Restarting Martin to apply changes..."
docker-compose -f docker-compose.dev.yml restart martin

# Deactivate virtual environment
echo "Deactivating virtual environment..."
deactivate

echo "Done! Administrative statistics are now available." 