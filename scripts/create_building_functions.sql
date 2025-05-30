-- Function to get unelectrified buildings by consumption
CREATE OR REPLACE FUNCTION buildings_by_consumption_zxy(z integer, x integer, y integer, query_params json DEFAULT '{"min_consumption": 10.0}')
RETURNS bytea AS $$
DECLARE
  mvt bytea;
  min_consumption float;
BEGIN
  min_consumption := COALESCE((query_params->>'min_consumption')::float, 10.0);

  SELECT ST_AsMVT(q, 'buildings_by_consumption', 4096, 'geom')
  INTO mvt
  FROM (
    SELECT 
      id,
      ST_AsMVTGeom(
        geom,
        ST_TileEnvelope(z, x, y),
        4096,
        256,
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
      consumption_kwh_month DESC
    LIMIT 10000
  ) AS q;

  RETURN mvt;
END
$$ LANGUAGE plpgsql IMMUTABLE STRICT PARALLEL SAFE;

-- Function to get unelectrified buildings by probability
CREATE OR REPLACE FUNCTION buildings_by_probability_zxy(z integer, x integer, y integer, query_params json DEFAULT '{"min_probability": 0.3}')
RETURNS bytea AS $$
DECLARE
  mvt bytea;
  min_probability float;
BEGIN
  min_probability := COALESCE((query_params->>'min_probability')::float, 0.3);

  SELECT ST_AsMVT(q, 'buildings_by_probability', 4096, 'geom')
  INTO mvt
  FROM (
    SELECT 
      id,
      ST_AsMVTGeom(
        geom,
        ST_TileEnvelope(z, x, y),
        4096,
        256,
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
      predicted_prob DESC
    LIMIT 10000
  ) AS q;

  RETURN mvt;
END
$$ LANGUAGE plpgsql IMMUTABLE STRICT PARALLEL SAFE;

-- Function to filter unelectrified buildings with combined criteria
CREATE OR REPLACE FUNCTION buildings_combined_filter_zxy(z integer, x integer, y integer, query_params json DEFAULT '{"min_consumption": 10.0, "min_probability": 0.3, "filter_type": "and"}')
RETURNS bytea AS $$
DECLARE
  mvt bytea;
  min_consumption float;
  min_probability float;
  filter_type text;
BEGIN
  min_consumption := COALESCE((query_params->>'min_consumption')::float, 10.0);
  min_probability := COALESCE((query_params->>'min_probability')::float, 0.3);
  filter_type := COALESCE(query_params->>'filter_type', 'and');

  SELECT ST_AsMVT(q, 'buildings_combined_filter', 4096, 'geom')
  INTO mvt
  FROM (
    SELECT 
      id,
      ST_AsMVTGeom(
        geom,
        ST_TileEnvelope(z, x, y),
        4096,
        256,
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
      CASE 
        WHEN filter_type = 'or' THEN consumption_kwh_month 
        ELSE predicted_prob 
      END DESC
    LIMIT 10000
  ) AS q;

  RETURN mvt;
END
$$ LANGUAGE plpgsql IMMUTABLE STRICT PARALLEL SAFE;
