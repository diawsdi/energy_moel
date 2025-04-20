import os
import glob
import zipfile
import geopandas as gpd
import logging
import json
from tqdm import tqdm  # For progress bar

# --- Configuration ---
# Adjust DATA_DIR_BASE to point to the correct location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR_BASE = os.path.join(WORKSPACE_DIR, 'data', 'oemapsenergydata') # Updated path to the data directory
OUTPUT_DIR = os.path.join(WORKSPACE_DIR, 'processed_data') # Where to potentially save cleaned data
TARGET_YEAR = 2023
COUNTRY_CODE = 'SEN' # ISO 3166-1 alpha-3 for Senegal

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Helper Functions ---

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

def clean_geojson_data(gdf):
    """Performs initial cleaning and transformation on the GeoDataFrame."""
    # TODO: Implement cleaning logic based on data inspection
    # Example cleaning steps (adjust based on actual data):
    # 1. Rename columns to match database schema?
    #    e.g., gdf.rename(columns={'demand': 'energy_demand_kwh'}, inplace=True)
    # 2. Handle missing values (impute, drop?)
    #    e.g., gdf['energy_demand_kwh'].fillna(0, inplace=True)
    # 3. Ensure correct data types
    #    e.g., gdf['energy_demand_kwh'] = gdf['energy_demand_kwh'].astype(float)
    # 4. Add missing columns required by the database schema
    #    gdf['year'] = TARGET_YEAR
    #    gdf['country_code'] = COUNTRY_CODE # If using multi-country schema
    #    gdf['has_access'] = gdf['has_access'].astype(bool) # Example, adjust based on source data
    #    gdf['data_source'] = 'oemapsenergydata_model' # Or derive from file path?
    # 5. Validate geometries
    gdf = gdf[gdf.geometry.is_valid]
    gdf = gdf[~gdf.geometry.is_empty]
    # 6. Reproject if necessary (e.g., to WGS 84 - EPSG:4326)
    #    if gdf.crs and gdf.crs.to_epsg() != 4326:
    #        logging.info(f"Reprojecting GeoDataFrame from {gdf.crs} to EPSG:4326")
    #        gdf = gdf.to_crs(epsg=4326)
    #    elif not gdf.crs:
    #        logging.warning("GeoDataFrame has no CRS set. Assuming EPSG:4326, but please verify.")
    #        # gdf.set_crs(epsg=4326, inplace=True) # Set if confident

    logging.info(f"Initial cleaning applied. GeoDataFrame shape: {gdf.shape}")
    return gdf


# --- Main Processing Logic ---

def main():
    logging.info("Starting building data processing script...")
    zip_files = find_geom_zip_files(DATA_DIR_BASE)

    if not zip_files:
        logging.warning("No zip files found to process. Exiting.")
        return

    all_building_gdfs = []
    temp_extract_path = os.path.join(SCRIPT_DIR, 'temp_geojson')

    for zip_file_path in tqdm(zip_files, desc="Processing Zip Files"):
        logging.info(f"Processing {zip_file_path}...")
        geojson_file_path = extract_geojson_from_zip(zip_file_path, temp_extract_path)

        if geojson_file_path:
            try:
                # Read the geojson file
                gdf = gpd.read_file(geojson_file_path)
                logging.info(f"Read {len(gdf)} features from {os.path.basename(geojson_file_path)}")

                if not gdf.empty:
                    # --- Data Inspection (Important First Step!) ---
                    if not all_building_gdfs: # Inspect only the first non-empty file
                         logging.info(f"Inspecting first GeoDataFrame from {geojson_file_path}:")
                         logging.info(f"Shape: {gdf.shape}")
                         logging.info(f"CRS: {gdf.crs}")
                         logging.info(f"Columns: {gdf.columns.tolist()}")
                         logging.info(f"Head:\n{gdf.head().to_string()}")
                         logging.info("Info:")
                         gdf.info(buf=logging.getLogger().handlers[0].stream) # Log gdf.info() output

                    # Apply cleaning steps (placeholder for now)
                    # gdf_cleaned = clean_geojson_data(gdf.copy()) # Pass copy to avoid modifying original
                    # all_building_gdfs.append(gdf_cleaned)
                    all_building_gdfs.append(gdf) # Append raw gdf for now until cleaning is defined

                # Clean up the extracted file
                os.remove(geojson_file_path)
            except Exception as e:
                logging.error(f"Failed to read or process {geojson_file_path}: {e}")
                # Optionally remove the file if it's corrupted
                # if os.path.exists(geojson_file_path):
                #     os.remove(geojson_file_path)
        else:
            logging.warning(f"Skipping {zip_file_path} as no GeoJSON was extracted.")

    # Clean up the temporary directory if it's empty
    try:
        if os.path.exists(temp_extract_path) and not os.listdir(temp_extract_path):
            os.rmdir(temp_extract_path)
        elif os.path.exists(temp_extract_path):
             logging.warning(f"Temp directory {temp_extract_path} not empty after processing.")
             # You might want to manually clean this or add more robust cleanup
    except OSError as e:
        logging.error(f"Error removing temp directory {temp_extract_path}: {e}")


    if not all_building_gdfs:
        logging.warning("No building data could be processed. Exiting.")
        return

    # Combine all GeoDataFrames into one
    logging.info(f"Concatenating {len(all_building_gdfs)} GeoDataFrames...")
    try:
        # Need pandas for concat, import here or ensure it's imported globally
        import pandas as pd
        final_gdf = gpd.GeoDataFrame(pd.concat(all_building_gdfs, ignore_index=True), crs=all_building_gdfs[0].crs) # Assumes all have same CRS initially
        logging.info(f"Combined GeoDataFrame shape: {final_gdf.shape}")

        # --- Perform Cleaning on Combined Data ---
        logging.info("Applying cleaning functions to combined data...")
        final_gdf_cleaned = clean_geojson_data(final_gdf)

        # --- Save or Load to DB ---
        # Example: Save to a single cleaned file (optional)
        output_filename = os.path.join(OUTPUT_DIR, f'senegal_buildings_{TARGET_YEAR}_cleaned.geojson')
        # Ensure saving uses appropriate driver and handles potential geometry issues
        try:
            # Use GeoJSON driver, may need adjustments based on data size and complexity
            # For very large data, consider GeoPackage (.gpkg) or other formats
             logging.info(f"Saving cleaned data to {output_filename}...")
             # Ensure the geometry column is named 'geometry' as expected by default
             if 'geometry' not in final_gdf_cleaned.columns and isinstance(final_gdf_cleaned.geometry, gpd.GeoSeries):
                 # Attempt to find the active geometry column name
                 geom_col_name = final_gdf_cleaned.geometry.name
                 final_gdf_cleaned = final_gdf_cleaned.rename(columns={geom_col_name: 'geometry'}).set_geometry('geometry')

             if 'geometry' in final_gdf_cleaned.columns:
                 final_gdf_cleaned.to_file(output_filename, driver='GeoJSON')
                 logging.info(f"Successfully saved cleaned data.")
             else:
                  logging.error("Could not find or set a geometry column named 'geometry'. Cannot save.")

        except Exception as e:
             logging.error(f"Error saving cleaned GeoDataFrame to {output_filename}: {e}")
             logging.error("Consider saving to GeoPackage (.gpkg) for better stability with complex data.")


        # TODO: Add database loading logic here using psycopg2 or SQLAlchemy/GeoAlchemy2
        # Example (conceptual using GeoAlchemy2):
        # from sqlalchemy import create_engine
        # from geoalchemy2 import Geometry, WKTElement
        # from geoalchemy2.shape import from_shape # Use from_shape for inserting GeoPandas geometries
        #
        # DB_USER = os.environ.get('DB_USER', 'your_user') # Use environment variables
        # DB_PASSWORD = os.environ.get('DB_PASSWORD', 'your_password')
        # DB_HOST = os.environ.get('DB_HOST', 'localhost')
        # DB_PORT = os.environ.get('DB_PORT', '5432')
        # DB_NAME = os.environ.get('DB_NAME', 'energy_db')
        # DATABASE_URL = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
        # engine = create_engine(DATABASE_URL)
        #
        # # Adapt final_gdf_cleaned columns to match 'buildings' table schema exactly
        # # Ensure required columns exist and have correct types before loading
        # df_to_load = final_gdf_cleaned.copy()
        # required_cols = ['footprint', 'year', 'energy_demand_kwh', 'has_access', 'building_type', 'data_source', 'grid_node_id'] # Example based on schema
        # # Add/rename/cast columns as needed...
        # # df_to_load.rename(columns={'geometry': 'footprint'}, inplace=True) # Rename geometry to match schema
        # # df_to_load['footprint'] = df_to_load['footprint'].apply(lambda g: from_shape(g, srid=4326)) # Convert geometry
        #
        # # Keep only columns relevant to the DB table
        # cols_to_keep = [col for col in required_cols if col in df_to_load.columns]
        # df_to_load = df_to_load[cols_to_keep]
        #
        # try:
        #    df_to_load.to_sql('buildings', engine, if_exists='append', index=False,
        #                      dtype={'footprint': Geometry(geometry_type='POLYGON', srid=4326)}) # Adjust SRID if needed
        #    logging.info(f"Successfully loaded {len(df_to_load)} records to 'buildings' table.")
        # except Exception as load_err:
        #     logging.error(f"Database load failed: {load_err}")

    except ImportError:
        logging.error("Pandas library not found. Please install it (`pip install pandas`)")
    except Exception as e:
        logging.error(f"Error during concatenation or final processing: {e}")


    logging.info("Building data processing script finished.")

if __name__ == "__main__":
    # Pandas is needed for concatenation
    try:
        import pandas as pd
        main()
    except ImportError:
        print("Error: Pandas library is required but not installed.")
        print("Please install it using: pip install pandas") 