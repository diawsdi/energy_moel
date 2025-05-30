-- Create table for unelectrified buildings
CREATE TABLE IF NOT EXISTS unelectrified_buildings (
    id SERIAL PRIMARY KEY,
    origin TEXT,
    origin_id TEXT, 
    origin_origin_id TEXT,
    area_in_meters FLOAT,
    n_bldgs_1km_away INTEGER,
    lulc2023_built_area_N1 FLOAT,
    lulc2023_rangeland_N1 FLOAT,
    lulc2023_crops_N1 FLOAT,
    lulc2023_built_area_N11 FLOAT,
    lulc2023_rangeland_N11 FLOAT,
    lulc2023_crops_N11 FLOAT,
    ntl2023_N1 FLOAT,
    ntl2023_N11 FLOAT,
    ookla_fixed_20230101_avg_d_kbps FLOAT,
    ookla_fixed_20230101_devices INTEGER,
    ookla_mobile_20230101_avg_d_kbps FLOAT,
    ookla_mobile_20230101_devices INTEGER,
    predicted_prob FLOAT,
    predicted_electrified INTEGER,
    consumption_kwh_month FLOAT,
    std_consumption_kwh_month FLOAT,
    geom GEOMETRY(POLYGON, 4326)
);

-- Create spatial index for better performance
CREATE INDEX IF NOT EXISTS unelectrified_buildings_geom_idx ON unelectrified_buildings USING GIST(geom);

-- Create a comment to help with documentation
COMMENT ON TABLE unelectrified_buildings IS 'Individual unelectrified buildings with energy consumption predictions'; 