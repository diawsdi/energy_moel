-- Update functions to better handle zoom levels and visibility

-- Function to get unelectrified buildings by consumption - with zoom level optimization
CREATE OR REPLACE FUNCTION buildings_by_consumption_zxy(z integer, x integer, y integer, query_params json DEFAULT '{"min_consumption": 10.0}')
RETURNS bytea AS $$
DECLARE
  mvt bytea;
  min_consumption float;
  zoom_feature_limit integer;
BEGIN
  min_consumption := COALESCE((query_params->>'min_consumption')::float, 10.0);
  
  -- Adjust feature limit based on zoom level
  IF z < 10 THEN 
    zoom_feature_limit := 5000;
  ELSIF z < 14 THEN
    zoom_feature_limit := 10000;
  ELSE
    zoom_feature_limit := 25000;
  END IF;

  -- Dynamically adjust selection criteria based on zoom level
  SELECT ST_AsMVT(q, 'buildings_by_consumption', 4096, 'geom')
  INTO mvt
  FROM (
    SELECT 
      id,
      ST_AsMVTGeom(
        geom,
        ST_TileEnvelope(z, x, y),
        4096,
        256,  -- Increased buffer for better rendering
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
      consumption_kwh_month >= min_consumption
      AND ST_Intersects(geom, ST_TileEnvelope(z, x, y))
    ORDER BY
      -- Prioritize buildings with higher consumption at lower zoom levels
      CASE WHEN z < 12 THEN consumption_kwh_month ELSE area_in_meters END DESC
    LIMIT zoom_feature_limit
  ) AS q;

  RETURN mvt;
END
$$ LANGUAGE plpgsql IMMUTABLE STRICT PARALLEL SAFE;

-- Function to get unelectrified buildings by probability - with zoom level optimization
CREATE OR REPLACE FUNCTION buildings_by_probability_zxy(z integer, x integer, y integer, query_params json DEFAULT '{"min_probability": 0.3}')
RETURNS bytea AS $$
DECLARE
  mvt bytea;
  min_probability float;
  zoom_feature_limit integer;
BEGIN
  min_probability := COALESCE((query_params->>'min_probability')::float, 0.3);
  
  -- Adjust feature limit based on zoom level
  IF z < 10 THEN 
    zoom_feature_limit := 5000;
  ELSIF z < 14 THEN
    zoom_feature_limit := 10000;
  ELSE
    zoom_feature_limit := 25000;
  END IF;

  SELECT ST_AsMVT(q, 'buildings_by_probability', 4096, 'geom')
  INTO mvt
  FROM (
    SELECT 
      id,
      ST_AsMVTGeom(
        geom,
        ST_TileEnvelope(z, x, y),
        4096,
        256,  -- Increased buffer for better rendering
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
      predicted_prob >= min_probability
      AND ST_Intersects(geom, ST_TileEnvelope(z, x, y))
    ORDER BY
      -- Prioritize buildings with higher probability at lower zoom levels
      CASE WHEN z < 12 THEN predicted_prob ELSE area_in_meters END DESC
    LIMIT zoom_feature_limit
  ) AS q;

  RETURN mvt;
END
$$ LANGUAGE plpgsql IMMUTABLE STRICT PARALLEL SAFE;

-- Function to filter unelectrified buildings with combined criteria - with zoom level optimization
CREATE OR REPLACE FUNCTION buildings_combined_filter_zxy(z integer, x integer, y integer, query_params json DEFAULT '{"min_consumption": 10.0, "min_probability": 0.3, "filter_type": "and"}')
RETURNS bytea AS $$
DECLARE
  mvt bytea;
  min_consumption float;
  min_probability float;
  filter_type text;
  zoom_feature_limit integer;
BEGIN
  min_consumption := COALESCE((query_params->>'min_consumption')::float, 10.0);
  min_probability := COALESCE((query_params->>'min_probability')::float, 0.3);
  filter_type := COALESCE(query_params->>'filter_type', 'and');
  
  -- Adjust feature limit based on zoom level
  IF z < 10 THEN 
    zoom_feature_limit := 5000;
  ELSIF z < 14 THEN
    zoom_feature_limit := 10000;
  ELSE
    zoom_feature_limit := 25000;
  END IF;

  SELECT ST_AsMVT(q, 'buildings_combined_filter', 4096, 'geom')
  INTO mvt
  FROM (
    SELECT 
      id,
      ST_AsMVTGeom(
        geom,
        ST_TileEnvelope(z, x, y),
        4096,
        256,  -- Increased buffer for better rendering
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
      (
        CASE 
          WHEN filter_type = 'or' THEN 
            (consumption_kwh_month >= min_consumption OR predicted_prob >= min_probability)
          ELSE 
            (consumption_kwh_month >= min_consumption AND predicted_prob >= min_probability)
        END
      )
      AND ST_Intersects(geom, ST_TileEnvelope(z, x, y))
    ORDER BY
      -- Prioritize buildings with higher values at lower zoom levels
      CASE 
        WHEN z < 12 THEN 
          CASE 
            WHEN filter_type = 'or' THEN 
              -- For OR filter, prioritize higher consumption or probability
              GREATEST(consumption_kwh_month / 20.0, predicted_prob)
            ELSE 
              -- For AND filter, prioritize larger buildings with both high values
              area_in_meters * (consumption_kwh_month / 20.0) * predicted_prob
          END
        ELSE
          -- For higher zoom levels, prioritize by size
          area_in_meters
      END DESC
    LIMIT zoom_feature_limit
  ) AS q;

  RETURN mvt;
END
$$ LANGUAGE plpgsql IMMUTABLE STRICT PARALLEL SAFE;
