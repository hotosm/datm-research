-- Clips to the exact AOI area instead of buffering
-- Attempts to merge small truncated hexagons into larger adjacent hexagons
-- TODO requires code to remove from large_hexagons the hexagons that were paired
-- TODO then we need to merge the subset of large_hexagons with merged_hexagons

CREATE OR REPLACE FUNCTION generate_hexagon_grid(
    aoi_geom geometry,
    size_meters integer
)
RETURNS jsonb AS $$
DECLARE
    mercator_aoi_geom geometry;
    hexagon_geom geometry;
    hexagon_area double precision;
BEGIN
    IF ST_SRID(aoi_geom) != 4326 THEN
        RAISE EXCEPTION 'Input geometry must be in EPSG:4326';
    END IF;

    -- Transform to web mercator (for specifying hexagon size in metres)
    mercator_aoi_geom := ST_Transform(aoi_geom, 3857);
    -- Generate a single hexagon geometry with the specified size
    hexagon_geom := ST_SetSRID(ST_Hexagon(size_meters, 0, 0), 3857);
    -- Calculate the area of the hexagon
    hexagon_area := ST_Area(hexagon_geom);

    RETURN (
        WITH generate_hexagons AS (
            -- Generate hexagon grid from AOI
            SELECT (ST_HexagonGrid(size_meters, mercator_aoi_geom)).geom AS geom
        ),
        clipped_hexagons AS (
            -- Clip hexagons to the AOI and calculate their areas
            SELECT 
                ST_Intersection(h.geom, mercator_aoi_geom) AS geom,
                ST_Area(ST_Intersection(h.geom, mercator_aoi_geom)) AS area
            FROM generate_hexagons h
            WHERE ST_Intersects(h.geom, mercator_aoi_geom)
        ),
        large_hexagons AS (
            -- Select large hexagons within the AOI
            SELECT geom
            FROM clipped_hexagons
            WHERE ST_Area(geom) > (hexagon_area * 0.3)
        ),
        small_hexagons AS (
            -- Select small hexagons within the AOI
            SELECT geom
            FROM clipped_hexagons
            WHERE ST_Area(geom) < (hexagon_area * 0.3)
        ),
        paired_hexagons AS (
            -- Pair each small hexagon with its adjacent large hexagon based on longest border
            SELECT DISTINCT ON (s.geom)
                s.geom AS small_geom,
                l.geom AS large_geom,
                ST_Length(ST_CollectionExtract(ST_Intersection(s.geom, l.geom), 2)) AS shared_border_length
            FROM small_hexagons s
            JOIN large_hexagons l ON ST_Touches(s.geom, l.geom)
            ORDER BY s.geom, shared_border_length DESC
        ),
        merged_hexagons AS (
            -- Merge small hexagon into adjacent large hexagon based on longest shared border
            SELECT
                CASE
                    WHEN ST_Length(ST_CollectionExtract(ST_Intersection(p.small_geom, p.large_geom), 2)) > 0
                        THEN ST_Union(p.large_geom, p.small_geom)
                    ELSE p.large_geom
                END AS geom
            FROM paired_hexagons p
        )

        -- Union all large hexagons (untouched) and merged hexagons
        SELECT ST_AsGeoJSON(ST_Transform(ST_Collect(geom), 4326)) AS geom_collection_geojson
        FROM merged_hexagons
        -- TODO remove the paired hexagons from large_hexagons first
        -- We need unique hexagons only, no overlaps
        -- FROM (
        --     SELECT geom FROM large_hexagons
        --     UNION ALL
        --     SELECT geom FROM merged_hexagons
        -- ) AS combined_hexagons
    );
EXCEPTION
    WHEN others THEN
        RAISE EXCEPTION 'Error in generate_hexagon_grid function: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;
