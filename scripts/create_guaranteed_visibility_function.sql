-- Create a specialized function that always returns building data at ANY zoom level
-- This function ensures buildings are visible at all zoom levels by using simpler geometries at low zooms

CREATE OR REPLACE FUNCTION unelectrified_buildings_all_zooms_zxy(z integer, x integer, y integer, query_params json DEFAULT '{}')
RETURNS bytea AS $$
DECLARE
  mvt bytea;
  bbox geometry;
  zoom_feature_limit integer;
  simplified_geom_text text;
BEGIN
  -- Transform tile envelope to match our data's SRID
  bbox := ST_Transform(ST_TileEnvelope(z, x, y), 4326);
  
  -- Adjust feature limits based on zoom
  IF z < 3 THEN
    zoom_feature_limit := 5000;
    -- At very low zoom levels, use centroids instead of full polygons
    simplified_geom_text := 'ST_Centroid(geom)';
  ELSIF z < 6 THEN
    zoom_feature_limit := 8000;
    -- At low zoom levels, use simplified geometries
    simplified_geom_text := 'ST_SimplifyPreserveTopology(geom, 0.001)';
  ELSIF z < 10 THEN
    zoom_feature_limit := 12000;
    -- At medium zoom levels, use slightly simplified geometries
    simplified_geom_text := 'ST_SimplifyPreserveTopology(geom, 0.0001)';
  ELSE
    zoom_feature_limit := 25000;
    -- At high zoom levels, use original geometries
    simplified_geom_text := 'geom';
  END IF;

  -- Execute dynamic SQL to use the appropriate geometry simplification
  EXECUTE format('
    SELECT ST_AsMVT(q, ''unelectrified_buildings'', 4096, ''geom'')
    FROM (
      SELECT 
        id,
        ST_AsMVTGeom(
          %s,
          ST_Transform(ST_TileEnvelope(%L, %L, %L), 4326),
          4096,
          512,
          true
        ) AS geom,
        origin,
        origin_id,
        area_in_meters,
        predicted_prob,
        predicted_electrified,
        consumption_kwh_month,
        std_consumption_kwh_month
      FROM 
        unelectrified_buildings
      WHERE 
        ST_Intersects(geom, ST_Transform(ST_TileEnvelope(%L, %L, %L), 4326))
      ORDER BY
        CASE 
          WHEN %L < 5 THEN area_in_meters * 100
          WHEN %L < 10 THEN consumption_kwh_month * area_in_meters
          ELSE consumption_kwh_month
        END DESC
      LIMIT %L
    ) AS q
  ', simplified_geom_text, z, x, y, z, x, y, z, z, zoom_feature_limit) INTO mvt;

  RETURN mvt;
END
$$ LANGUAGE plpgsql IMMUTABLE STRICT PARALLEL SAFE;
