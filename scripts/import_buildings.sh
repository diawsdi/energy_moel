#!/bin/bash

# Make the script executable
chmod +x scripts/import_buildings_data.py

# Install necessary Python packages
pip install geopandas psycopg2-binary sqlalchemy tqdm numpy

# Run the import script
python scripts/import_buildings_data.py 