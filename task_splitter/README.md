# Drone TM Task Splitter

- A hexagon grid is used to maximise captured imagery per flight,
  while ensuring visual line of sight of the drone.
- PostGIS has a ST_HexagonGrid function built in to aid this.
- The `generate_hexagon_grid.sql` file contains a first attempt at a splitting function.
  - This takes three params: the AOI, a hexagon size, and a buffer.
  - The hexagon size determines the length of each side:
    ![hexagon size](./hexagon_size.png)
  - The buffer determines how much of a buffer should be used to ensure full 
    coverage of the AOI (default 50m).
  - An offset of 75m in each direction is used to determine the shift with the
    minimum number of hexagons (as sometimes they get cut off at the edges).
  - The EPSG 4326 is projected to web mercator to use metres for all inputs.
    This could probably be improved.

## Usage

- Execute the `generate_hexagon_grid.sql` code in your database, to create function
  `generate_hexagon_grid`.
- Pass in the params to generate a grid.
- Either from an existing table:
  `SELECT generate_hexagon_grid((SELECT outline FROM projects LIMIT 1), 100, 50);`
- Or from a text based geojson:
    ```sql
    WITH aoi_geom AS (
        SELECT ST_SetSRID(ST_GeomFromGeoJSON('
            {
                "type": "Polygon",
                "coordinates": [
                    [
                        [85.29998911024427, 27.714008043780694],
                        [85.29998911024427, 27.710892349952076],
                        [85.30478315714117, 27.710892349952076],
                        [85.30478315714117, 27.714008043780694],
                        [85.29998911024427, 27.714008043780694]
                    ]
                ]
            }
        '), 4326) AS geom
    )

    SELECT generate_best_hexagon_grid(geom, 100, 50) AS hexgrid
    FROM aoi_geom;
    ```

> In the long run we will encapsulate the logic in a Python script.
>
> The function should be `CREATE OR REPLACE` on the database, then
> the function called from the Python db driver.

## Future Plans

- Drones often have no-fly zones that we must avoid in our task areas.
- One approach to do this would be to:
  1. Generate the hexgon grid.
  2. Cut out the provided no-fly zone polygons.
  3. For the hexagons that were affected / partially cut, then could be merged
     into surrounding hexagons.
    a. The result would not be perfectly sized hexagon areas, but as close as we can get.
    b. Some hexagon areas may be slightly larger than the provided size.
  
## Update: Hexagons, Flight Plans, & Hamiltonian Circuits

The most likely optimal setup for this is:

1. Get the project AOI from the user.
2. Overlay a hexagon grid on the AOI, using an optimal wayline spacing:
    - The spacing is optimised from the flight height, camera FOV, resolution.
    - Once the grid is generated, it should be clipped to the AOI edges.
    - Any small truncated hexagons (say only 30% remains) could be merged into neighbours,
      but be aware this may complicate generating the flight plan if shapes other than
      hexagons are used.
    - We also need to cut out any 'no-fly zones' from the grid, and do the same process
      as above (merge small hexagons into neighbours).
    - This code is almost finished in `generate_hexagons_v2.sql`.
3. Once we have a complete hexagon grid clipped to the AOI and with no-fly zones cut out,
  we can overlay the task areas.
4. Task areas should be simple squares with their size determined by the maximum flyable
  area for a drone on a single battery (or two batteries).
    - Each square will capture a certain number of hexagon centroids.
    - These centroids are used to generate a 
      [Hamiltonian Circuit](https://en.wikipedia.org/wiki/Hamiltonian_path), which is the
      most optimal flight path for the drone.

A simple visualisation below shows:
  - A hexagon grid.
  - An overlain rectangular task area (in practice this should be a square!).
  - The Hamiltonian Circuit showing the flight path.

![hexagon size](./hexagon_size.png)

### Hamiltonian Circuit Calculation

For future reference, this is an interesting summer research project on the topic:
https://github.com/zcczhang/UAV_Coverage

The author is trying to use ML to determine optimal flights paths in a rectangular 
field (common application), using either 1 or 2 drones. Not as applicable to our 
use case.

The key passage: `in comparison with the hexagon tessellation which is calculated and 
proved mathematically that generates the shorter coverage path than the square 
tessellation, we want to figure out if it is possible to implement the reinforcement
learning to find the shortest coverage path in a given field.`

There are two algorithms for calculating the Hamiltonian circuit for the hexagons:
https://github.com/zcczhang/UAV_Coverage/tree/master/Get_Path
