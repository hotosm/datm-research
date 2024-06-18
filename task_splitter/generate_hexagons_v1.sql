-- Attempts to find the best offset with the minimum number of geometries
-- Uses a buffer to the AOI to shift the grid around by an offset

CREATE OR REPLACE FUNCTION generate_hexagon_grid(
    aoi_geom geometry,
    size_meters integer,
    buffer_distance_meters integer DEFAULT 50
)
RETURNS jsonb AS $$
DECLARE
    expanded_aoi_geom geometry;
BEGIN
    IF ST_SRID(aoi_geom) != 4326 THEN
        RAISE EXCEPTION 'Input geometry must be in EPSG:4326';
    END IF;

    -- Transform to web mercator (for metres) and buffer the AOI geometry
    expanded_aoi_geom := ST_Buffer(ST_Transform(aoi_geom, 3857), buffer_distance_meters);

    RETURN (
        WITH offsets AS (
            -- Define the offsets (hardcoded to 75 meters in each direction)
            SELECT * FROM (VALUES (0, 0), (75, 0), (-75, 0), (0, 75), (0, -75)) AS o(x_offset, y_offset)
        ),
        generate_hexagons AS (
            -- Generate hexagon grid with optional offsets
            SELECT (ST_HexagonGrid(size_meters, ST_Translate(expanded_aoi_geom, o.x_offset, o.y_offset))).*,
                   o.x_offset, o.y_offset
            FROM offsets o
        ),
        clipped_hexagons AS (
            -- Clip hexagons to the expanded AOI and calculate their areas
            SELECT 
                ST_Intersection(h.geom, expanded_aoi_geom) AS geom,
                ST_Area(ST_Intersection(h.geom, expanded_aoi_geom)) AS area,
                h.x_offset, h.y_offset
            FROM generate_hexagons h
            WHERE ST_Intersects(h.geom, expanded_aoi_geom)
        ),
        filtered_hexagons AS (
            -- Filter out small hexagons (less than half size)
            SELECT geom, x_offset, y_offset
            FROM clipped_hexagons
            WHERE area > (size_meters * size_meters * 0.5)
        ),
        best_shift AS (
            -- Find the shift with the most hexagons remaining
            SELECT x_offset, y_offset
            FROM (
                SELECT x_offset, y_offset, COUNT(*) AS hex_count
                FROM filtered_hexagons
                GROUP BY x_offset, y_offset
                ORDER BY hex_count ASC
                LIMIT 1
            ) AS best
        )
        -- Convert the result to GeoJSON and transform back to EPSG 4326
        SELECT ST_AsGeoJSON(ST_Transform(ST_Collect(geom), 4326)) AS geom_collection_geojson
        FROM filtered_hexagons
        WHERE x_offset = (SELECT x_offset FROM best_shift)
          AND y_offset = (SELECT y_offset FROM best_shift)
    );
EXCEPTION
    WHEN others THEN
        RAISE EXCEPTION 'Error in generate_hexagon_grid function: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;
