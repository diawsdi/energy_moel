-- Create a specialized function for the default unelectrified buildings layer
-- This function ensures buildings are visible at all zoom levels

CREATE OR REPLACE FUNCTION unelectrified_buildings_zxy(z integer, x integer, y integer, query_params json DEFAULT '{}')
RETURNS bytea AS $$
DECLARE
  mvt bytea;
  zoom_feature_limit integer;
  min_area_threshold float;
BEGIN
  -- Adjust feature limit and area threshold based on zoom level
  -- At lower zoom levels, we want fewer buildings but the most significant ones
  IF z < 6 THEN 
    zoom_feature_limit := 10000;
    min_area_threshold := 20.0;  -- Only show larger buildings at very low zoom
  ELSIF z < 10 THEN
    zoom_feature_limit := 15000;
    min_area_threshold := 15.0;
  ELSIF z < 14 THEN
    zoom_feature_limit := 20000;
    min_area_threshold := 0.0;   -- Show all buildings at medium-high zoom
  ELSE
    zoom_feature_limit := 30000;
    min_area_threshold := 0.0;
  END IF;

  SELECT ST_AsMVT(q, 'unelectrified_buildings', 4096, 'geom')
  INTO mvt
  FROM (
    SELECT 
      id,
      ST_AsMVTGeom(
        geom,
        ST_TileEnvelope(z, x, y),
        4096,
        512,  -- Doubled buffer for better rendering across tiles
        true
      ) AS geom,
      origin,
      origin_id,
      area_in_meters,
      predicted_prob,
      predicted_electrified,
      consumption_kwh_month,
      std_consumption_kwh_month,
      CASE
        WHEN consumption_kwh_month > 15 THEN 'high'
        WHEN consumption_kwh_month > 10 THEN 'medium'
        ELSE 'low'
      END as consumption_category
    FROM 
      unelectrified_buildings
    WHERE 
      area_in_meters >= min_area_threshold AND
      ST_Intersects(geom, ST_TileEnvelope(z, x, y))
    ORDER BY
      -- Prioritize important buildings at lower zoom levels
      CASE 
        WHEN z < 10 THEN 
          -- At low zoom, prioritize by size and consumption
          area_in_meters * (consumption_kwh_month + 1.0) * (predicted_prob + 0.1)
        ELSE
          -- At higher zooms, prioritize by consumption
          consumption_kwh_month
      END DESC
    LIMIT zoom_feature_limit
  ) AS q;

  RETURN mvt;
END
$$ LANGUAGE plpgsql IMMUTABLE STRICT PARALLEL SAFE;
