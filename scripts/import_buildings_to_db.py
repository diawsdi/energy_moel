#!/usr/bin/env python3
"""
Import buildings data from GeoPackage files to PostgreSQL database.
"""

import os
import json
import logging
import time
import argparse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from geoalchemy2 import WKTElement
import geopandas as gpd
from shapely.wkt import loads
from dotenv import load_dotenv
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.buildings_energy import BuildingsEnergy
from app.db.base import Base
from app.db.session import engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def ensure_postgis(engine):
    """Ensure PostGIS extension is installed."""
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        conn.commit()
        logger.info("PostGIS extension enabled")


def create_tables(engine):
    """Create tables in the database."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")


def get_batch_files():
    """Get a list of all batch GeoPackage files."""
    batch_dir = Path("processed_data/batches")
    return sorted(list(batch_dir.glob("*.gpkg")))


def import_batch(engine, batch_file, batch_num, total_batches):
    """Import a single batch file into the database."""
    logger.info(f"Processing batch {batch_num}/{total_batches}: {batch_file.name}")
    
    start_time = time.time()
    
    # Read the GeoPackage file
    try:
        gdf = gpd.read_file(batch_file)
        logger.info(f"Read {len(gdf)} records from {batch_file.name}")
    except Exception as e:
        logger.error(f"Error reading {batch_file}: {e}")
        return 0
    
    # Create a session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Prepare batch of records for insert
        records = []
        for _, row in gdf.iterrows():
            # Convert geometry to WKT format for PostGIS
            geom_wkt = WKTElement(row.geometry.wkt, srid=4326)
            
            # Create BuildingsEnergy object
            building = BuildingsEnergy(
                geom=geom_wkt,
                area_in_meters=row.area_in_meters,
                year=row.year,
                energy_demand_kwh=row.energy_demand_kwh,
                has_access=row.has_access,
                building_type=row.building_type if hasattr(row, 'building_type') else None,
                data_source=row.data_source,
                grid_node_id=row.grid_node_id if hasattr(row, 'grid_node_id') else None,
                origin_id=row.origin_id,
            )
            records.append(building)
        
        # Bulk insert
        session.bulk_save_objects(records)
        session.commit()
        
        elapsed_time = time.time() - start_time
        logger.info(f"Imported {len(records)} buildings from {batch_file.name} in {elapsed_time:.2f} seconds")
        
        return len(records)
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error importing {batch_file}: {e}")
        return 0
    
    finally:
        session.close()


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Import building data to PostgreSQL")
    parser.add_argument("--recreate-tables", action="store_true", help="Drop and recreate tables")
    parser.add_argument("--batch-start", type=int, default=1, help="Starting batch number")
    parser.add_argument("--batch-end", type=int, help="Ending batch number")
    args = parser.parse_args()
    
    start_time = time.time()
    
    # Ensure PostGIS is installed
    logger.info("Ensuring PostGIS extension is installed...")
    ensure_postgis(engine)
    
    # Recreate tables if requested
    if args.recreate_tables:
        logger.info("Dropping and recreating tables...")
        Base.metadata.drop_all(bind=engine)
        create_tables(engine)
    else:
        # Just make sure tables exist
        create_tables(engine)
    
    # Get all batch files
    batch_files = get_batch_files()
    total_batches = len(batch_files)
    logger.info(f"Found {total_batches} batch files")
    
    # Filter batch files based on provided arguments
    start_batch = args.batch_start - 1  # Convert to 0-based index
    end_batch = args.batch_end if args.batch_end is not None else total_batches
    
    if start_batch < 0:
        start_batch = 0
    if end_batch > total_batches:
        end_batch = total_batches
    
    batch_files = batch_files[start_batch:end_batch]
    
    # Import each batch
    total_imported = 0
    for i, batch_file in enumerate(batch_files, start=start_batch+1):
        imported = import_batch(engine, batch_file, i, total_batches)
        total_imported += imported
    
    elapsed_time = time.time() - start_time
    logger.info(f"Import completed. Added {total_imported} buildings in {elapsed_time:.2f} seconds")


if __name__ == "__main__":
    main() 