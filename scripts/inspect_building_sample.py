import os
import glob
import zipfile
import geopandas as gpd
import pandas as pd
import logging

# Similar configuration as in the main script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR_BASE = os.path.join(WORKSPACE_DIR, 'data', 'oemapsenergydata')
OUTPUT_DIR = os.path.join(WORKSPACE_DIR, 'processed_data')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_and_inspect_sample(num_files=1):
    """Extract and inspect a sample of building data from a limited number of zip files."""
    # Find geom_zip files
    search_pattern = os.path.join(DATA_DIR_BASE, '**', '*_geoms.zip')
    zip_files = glob.glob(search_pattern, recursive=True)
    logging.info(f"Found {len(zip_files)} '*_geoms.zip' files. Will inspect {num_files} for a sample.")
    
    if not zip_files:
        logging.warning("No zip files found. Exiting.")
        return
    
    # Use the first few files as a sample
    sample_files = zip_files[:num_files]
    temp_extract_dir = os.path.join(SCRIPT_DIR, 'temp_extract_sample')
    os.makedirs(temp_extract_dir, exist_ok=True)
    
    # Process each sample file
    for zip_file_path in sample_files:
        logging.info(f"Processing {zip_file_path} for inspection...")
        
        try:
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                geojson_files = [f for f in zip_ref.namelist() if f.lower().endswith('.geojson')]
                if not geojson_files:
                    logging.warning(f"No .geojson file found in {zip_file_path}")
                    continue
                
                # Extract the first geojson found
                geojson_filename = geojson_files[0]
                zip_ref.extract(geojson_filename, temp_extract_dir)
                geojson_path = os.path.join(temp_extract_dir, geojson_filename)
                
                # Read the geojson file
                gdf = gpd.read_file(geojson_path)
                
                # Detailed inspection
                logging.info(f"GeoDataFrame from {os.path.basename(zip_file_path)} has shape: {gdf.shape}")
                logging.info(f"CRS: {gdf.crs}")
                logging.info(f"Columns: {gdf.columns.tolist()}")
                
                # Data type information
                logging.info("Data types:")
                for col in gdf.columns:
                    unique_vals = gdf[col].nunique()
                    na_count = gdf[col].isna().sum()
                    logging.info(f"  {col}: {gdf[col].dtype}, {unique_vals} unique values, {na_count} NAs")
                
                # Print sample data for each column
                logging.info("Sample values for each column:")
                for col in gdf.columns:
                    if col != 'geometry':  # Skip geometry which would be verbose
                        sample_vals = gdf[col].dropna().head(5).tolist()
                        logging.info(f"  {col}: {sample_vals}")
                
                # Show first few rows
                logging.info(f"First 5 rows:\n{gdf.head(5).to_string()}")
                
                # Clean up extracted file
                os.remove(geojson_path)
                
                # Save a small sample (100 rows) as a CSV for easy inspection
                sample_csv = os.path.join(OUTPUT_DIR, f"{os.path.basename(zip_file_path).replace('.zip', '_sample.csv')}")
                # Convert geometry to WKT to save it in CSV
                gdf_sample = gdf.head(100).copy()
                gdf_sample['geometry_wkt'] = gdf_sample['geometry'].apply(lambda x: x.wkt if x else None)
                gdf_sample = pd.DataFrame(gdf_sample.drop(columns=['geometry']))
                gdf_sample.to_csv(sample_csv, index=False)
                logging.info(f"Saved sample of 100 rows to {sample_csv}")
                
        except Exception as e:
            logging.error(f"Error processing {zip_file_path}: {e}")
    
    # Clean up temp directory if empty
    try:
        if os.path.exists(temp_extract_dir) and not os.listdir(temp_extract_dir):
            os.rmdir(temp_extract_dir)
    except Exception as e:
        logging.error(f"Error cleaning up: {e}")
    
    logging.info("Inspection complete.")

if __name__ == "__main__":
    # Inspect 3 files for a good sample
    extract_and_inspect_sample(num_files=3) 