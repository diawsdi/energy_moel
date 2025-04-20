import os
import glob
import zipfile
import geopandas as gpd
import pandas as pd
import logging
from tqdm import tqdm
import json
from pathlib import Path

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR_BASE = os.path.join(WORKSPACE_DIR, 'data', 'oemapsenergydata')
OUTPUT_DIR = os.path.join(WORKSPACE_DIR, 'processed_data')
BATCH_DIR = os.path.join(OUTPUT_DIR, 'batches')
TARGET_YEAR = 2023
COUNTRY_CODE = 'SEN'  # ISO 3166-1 alpha-3 for Senegal
BATCH_SIZE = 3  # Process 3 zip files per batch to avoid memory issues

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(BATCH_DIR, exist_ok=True)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def find_geom_zip_files(base_dir):
    """Finds all *_geoms.zip files recursively within the base directory."""
    search_pattern = os.path.join(base_dir, '**', '*_geoms.zip')
    zip_files = glob.glob(search_pattern, recursive=True)
    logging.info(f"Found {len(zip_files)} '*_geoms.zip' files in {base_dir}")
    return zip_files

def extract_geojson_from_zip(zip_path, temp_extract_dir='temp_geojson'):
    """Extracts the first .geojson file found within a zip archive."""
    os.makedirs(temp_extract_dir, exist_ok=True)
    geojson_path = None
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            geojson_files = [f for f in zip_ref.namelist() if f.lower().endswith('.geojson')]
            if not geojson_files:
                logging.warning(f"No .geojson file found in {zip_path}")
                return None
            # Extract the first geojson found
            geojson_filename = geojson_files[0]
            zip_ref.extract(geojson_filename, temp_extract_dir)
            geojson_path = os.path.join(temp_extract_dir, geojson_filename)
            logging.debug(f"Extracted {geojson_filename} from {zip_path} to {temp_extract_dir}")
    except zipfile.BadZipFile:
        logging.error(f"Bad zip file: {zip_path}")
    except Exception as e:
        logging.error(f"Error extracting {zip_path}: {e}")
    return geojson_path

def clean_and_transform_geojson(gdf, grid_id):
    """Clean and transform the GeoDataFrame to match the database schema."""
    # Create a copy to avoid modifying the original
    gdf_clean = gdf.copy()
    
    # 1. Filter invalid geometries
    gdf_clean = gdf_clean[gdf_clean.geometry.is_valid]
    gdf_clean = gdf_clean[~gdf_clean.geometry.is_empty]
    
    # 2. Map columns to our database schema
    # Here is our mapping (source_column -> target_column):
    # - geometry -> footprint
    # - area_in_meters -> (keep as is)
    # - cons (kWh/month) * 12 -> energy_demand_kwh (converting monthly to annual)
    # - elec access (%) > threshold -> has_access (boolean based on threshold)
    
    # Create new columns
    gdf_clean['year'] = TARGET_YEAR
    gdf_clean['energy_demand_kwh'] = gdf_clean['cons (kWh/month)'] * 12  # Monthly to annual
    
    # The elec access values appear to be percentages but with small values (3-5%)
    # Let's use a threshold of 3.5% for determining has_access (yes/no)
    gdf_clean['has_access'] = (gdf_clean['elec access (%)'] > 3.5)
    
    gdf_clean['building_type'] = None  # Not available in source data
    gdf_clean['data_source'] = f"oemapsenergydata_grid_{grid_id}"
    gdf_clean['grid_node_id'] = None  # Will need to be linked later
    
    # 3. Select only the columns we need for our schema
    cols_to_keep = [
        'geometry',                  # Will be renamed to 'footprint' in the database
        'area_in_meters',
        'year', 
        'energy_demand_kwh',
        'has_access',
        'building_type',
        'data_source',
        'grid_node_id',
        # Optional: Keep original ID fields for reference?
        'id',
        'origin_id'
    ]
    
    # Return the cleaned dataframe with selected columns
    return gdf_clean[cols_to_keep]

def process_batch(zip_files_batch, batch_index):
    """Process a batch of zip files and save to a GeoJSON file."""
    all_buildings_gdfs = []
    temp_extract_path = os.path.join(SCRIPT_DIR, 'temp_geojson')
    
    for zip_file_path in tqdm(zip_files_batch, desc=f"Processing Batch {batch_index+1}"):
        logging.info(f"Processing {zip_file_path}...")
        grid_id = os.path.basename(os.path.dirname(zip_file_path)).replace('grid_', '')
        
        geojson_file_path = extract_geojson_from_zip(zip_file_path, temp_extract_path)
        
        if geojson_file_path:
            try:
                # Read the geojson file
                gdf = gpd.read_file(geojson_file_path)
                logging.info(f"Read {len(gdf)} features from {os.path.basename(geojson_file_path)}")
                
                if not gdf.empty:
                    # Clean and transform the data
                    gdf_clean = clean_and_transform_geojson(gdf, grid_id)
                    all_buildings_gdfs.append(gdf_clean)
                
                # Clean up the extracted file
                os.remove(geojson_file_path)
            except Exception as e:
                logging.error(f"Failed to read or process {geojson_file_path}: {e}")
        else:
            logging.warning(f"Skipping {zip_file_path} as no GeoJSON was extracted.")
    
    # Clean up temp directory
    try:
        if os.path.exists(temp_extract_path) and not os.listdir(temp_extract_path):
            os.rmdir(temp_extract_path)
    except OSError as e:
        logging.error(f"Error removing temp directory {temp_extract_path}: {e}")
    
    if not all_buildings_gdfs:
        logging.warning(f"No building data could be processed in batch {batch_index+1}. Skipping.")
        return None
    
    # Combine all GeoDataFrames in this batch
    combined_gdf = gpd.GeoDataFrame(pd.concat(all_buildings_gdfs, ignore_index=True), 
                                 crs=all_buildings_gdfs[0].crs)
    
    logging.info(f"Batch {batch_index+1} combined GeoDataFrame shape: {combined_gdf.shape}")
    
    # Save this batch to a GeoPackage file (more efficient than GeoJSON for large files)
    batch_filename = os.path.join(BATCH_DIR, f'senegal_buildings_{TARGET_YEAR}_batch_{batch_index+1}.gpkg')
    combined_gdf.to_file(batch_filename, driver='GPKG')
    logging.info(f"Saved batch {batch_index+1} to {batch_filename}")
    
    # Return info about this batch for the manifest
    return {
        'batch_index': batch_index + 1,
        'filename': os.path.basename(batch_filename),
        'num_files_processed': len(zip_files_batch),
        'num_buildings': len(combined_gdf),
        'crs': str(combined_gdf.crs)
    }

def create_manifest(batches_info):
    """Create a manifest file summarizing all the batches processed."""
    manifest = {
        'country_code': COUNTRY_CODE,
        'year': TARGET_YEAR,
        'total_batches': len(batches_info),
        'total_buildings': sum(batch['num_buildings'] for batch in batches_info),
        'crs': batches_info[0]['crs'] if batches_info else None,
        'batches': batches_info,
        'schema': {
            'geometry': 'Polygon representing building footprint',
            'area_in_meters': 'Building area in square meters',
            'year': 'Year of data',
            'energy_demand_kwh': 'Annual energy demand in kWh',
            'has_access': 'Boolean indicating if building likely has electricity access',
            'building_type': 'Type of building (not available in source data)',
            'data_source': 'Source of the data',
            'grid_node_id': 'Foreign key to grid_nodes table (to be linked later)',
            'id': 'Original ID from source data',
            'origin_id': 'Original external ID from source data'
        }
    }
    
    # Save manifest as JSON
    manifest_path = os.path.join(OUTPUT_DIR, f'buildings_{COUNTRY_CODE}_{TARGET_YEAR}_manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logging.info(f"Created manifest file at {manifest_path}")
    
    return manifest

def main():
    logging.info("Starting building data processing script with batch processing...")
    
    # Find all zip files
    zip_files = find_geom_zip_files(DATA_DIR_BASE)
    
    if not zip_files:
        logging.warning("No zip files found to process. Exiting.")
        return
    
    # Process in batches to avoid memory issues
    num_batches = (len(zip_files) + BATCH_SIZE - 1) // BATCH_SIZE  # Ceiling division
    logging.info(f"Processing {len(zip_files)} files in {num_batches} batches of {BATCH_SIZE} files each.")
    
    batches_info = []
    
    for i in range(num_batches):
        start_idx = i * BATCH_SIZE
        end_idx = min((i + 1) * BATCH_SIZE, len(zip_files))
        batch_files = zip_files[start_idx:end_idx]
        
        logging.info(f"Processing batch {i+1}/{num_batches} with {len(batch_files)} zip files.")
        batch_info = process_batch(batch_files, i)
        
        if batch_info:
            batches_info.append(batch_info)
    
    # Create a manifest file with information about all batches
    if batches_info:
        manifest = create_manifest(batches_info)
        logging.info(f"Processed {manifest['total_buildings']} buildings across {manifest['total_batches']} batches.")
    else:
        logging.warning("No data was processed successfully.")
    
    logging.info("Building data processing script finished.")

if __name__ == "__main__":
    main() 