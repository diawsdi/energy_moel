-- This is similar to the query Martin would use to generate a vector tile
-- For zoom level 8, tile 117/117
WITH
mvtgeom AS (
    SELECT ST_AsMVTGeom(
        ST_Transform(geom, 3857),
        ST_TileEnvelope(8, 117, 117),
        4096,
        256,
        true
    ) AS geom,
    id,
    area_in_meters,
    energy_demand_kwh,
    has_access,
    building_type,
    year
    FROM buildings_energy
    WHERE geom && ST_Transform(ST_TileEnvelope(8, 117, 117, margin => 0.5), 4326)
    LIMIT 10000
)
SELECT count(*) FROM mvtgeom;
