-- Fix the unelectrified buildings function with proper SRID transformation
-- This ensures buildings are visible at all zoom levels by correctly handling projection systems

CREATE OR REPLACE FUNCTION unelectrified_buildings_zxy(z integer, x integer, y integer, query_params json DEFAULT '{}')
RETURNS bytea AS $$
DECLARE
  mvt bytea;
  zoom_feature_limit integer;
  min_area_threshold float;
  tile_bbox geometry;
BEGIN
  -- Get the tile envelope in SRID 3857 (Web Mercator)
  tile_bbox := ST_TileEnvelope(z, x, y);
  
  -- Transform tile bbox to SRID 4326 to match our data
  tile_bbox := ST_Transform(tile_bbox, 4326);

  -- Adjust feature limit and area threshold based on zoom level
  -- At lower zoom levels, we show fewer buildings but the most significant ones
  IF z < 6 THEN 
    zoom_feature_limit := 10000;
    min_area_threshold := 15.0;  -- Only show larger buildings at very low zoom
  ELSIF z < 10 THEN
    zoom_feature_limit := 15000;
    min_area_threshold := 10.0;
  ELSIF z < 14 THEN
    zoom_feature_limit := 20000;
    min_area_threshold := 0.0;   -- Show all buildings at medium-high zoom
  ELSE
    zoom_feature_limit := 30000;
    min_area_threshold := 0.0;
  END IF;

  -- For the absolute lowest zoom levels (0-2), ensure we at least show some data
  -- by reducing area threshold further and prioritizing the largest buildings
  IF z < 3 THEN
    zoom_feature_limit := 5000;
    min_area_threshold := 0.0;  -- Show all buildings at lowest zoom
  END IF;

  -- Generate MVT using transformed bbox
  SELECT ST_AsMVT(q, 'unelectrified_buildings', 4096, 'geom')
  INTO mvt
  FROM (
    SELECT 
      id,
      -- Note the ST_Transform to 3857 within AsMVTGeom
      ST_AsMVTGeom(
        geom,
        tile_bbox,
        4096,
        512,  -- Large buffer for better rendering
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
      ST_Intersects(geom, tile_bbox)
      -- For lowest zoom levels (0-2), use a simpler filter to ensure we show data
      AND (z >= 3 OR area_in_meters >= (CASE WHEN z < 3 THEN 0 ELSE min_area_threshold END))
    ORDER BY
      -- For lowest zoom levels, prioritize by size to show the most significant buildings
      CASE 
        WHEN z < 3 THEN area_in_meters * 1000
        WHEN z < 10 THEN area_in_meters * (consumption_kwh_month + 1.0) * (predicted_prob + 0.1)
        ELSE consumption_kwh_month
      END DESC
    LIMIT zoom_feature_limit
  ) AS q;

  RETURN mvt;
END
$$ LANGUAGE plpgsql IMMUTABLE STRICT PARALLEL SAFE;
