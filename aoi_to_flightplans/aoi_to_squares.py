import geojson
from math import sqrt
from zipfile import ZipFile
from shapely.geometry import shape
from fmtm_splitter.splitter import split_by_square

from wpml_generator import (
    calculate_gsd,
    calculate_image_interval,
    calculate_wayline_spacing,
    generate_waypoints_within_polygon,
    create_xml,
)

def load_geojson(file_path: str):
    """Load GeoJSON file into memory."""
    with open(file_path, 'r') as f:
        return geojson.load(f)

def save_geojson(geojson_obj: geojson.GeoJSON, file_path: str):
    """Write memory GeoJSON to disk."""
    with open(file_path, 'w') as f:
        geojson.dump(geojson_obj, f)

def multipoly_to_poly_in_featcol(featcol: geojson.FeatureCollection) -> geojson.FeatureCollection:
    """Extract individual polygons from a MultiPolygon."""
    filtered_polygons = []

    for feature in featcol["features"]:
        polygon = feature["geometry"]

        if isinstance(polygon, geojson.Polygon):
            filtered_polygons.append(geojson.Feature(geometry=polygon))

        elif isinstance(polygon, geojson.MultiPolygon):
            for coords in polygon["coordinates"]:
                filtered_polygons.append(geojson.Feature(geometry=geojson.Polygon(coordinates=coords)))

    return geojson.FeatureCollection(features=filtered_polygons)

def filter_or_merge_small_polygons_in_featcol(
    featcol: geojson.FeatureCollection,
    expected_square_size: int,
) -> geojson.FeatureCollection:
    """Filter or merge polygons smaller than specified threshholds.
    
    Less than 10% desired size are filtered.
    Less than 30% desired size are merged.
    """
    filtered_polygons = []

    # Approx conversion
    meter_in_degrees = 0.0000114
    # Values in in degrees squared
    min_area = (expected_square_size * meter_in_degrees) ** 2 * 0.1
    merge_area_threshold = (expected_square_size * meter_in_degrees) ** 2 * 0.3

    for feature in featcol["features"]:
        polygon = shape(feature["geometry"])
        # Calculate area in square meters
        area = polygon.area
        if area >= min_area:
            filtered_polygons.append(feature)

    # # Handle merging
    # small_polygons = [f for f in filtered_polygons if f[0].area < merge_area_threshold]
    # large_polygons = [f for f in filtered_polygons if f[0].area >= merge_area_threshold]

    # merged_polygons = []

    # while small_polygons:
    #     small_polygon, small_feature = small_polygons.pop(0)
    #     merged = False
    #     for i, (large_polygon, large_feature) in enumerate(large_polygons):
    #         if small_polygon.touches(large_polygon):
    #             merged_polygon = small_polygon.union(large_polygon)
    #             large_polygons[i] = (merged_polygon, large_feature)
    #             merged = True
    #             break
    #     if not merged:
    #         merged_polygons.append((small_polygon, small_feature))

    # merged_polygons.extend(large_polygons)

    # final_features = [
    #     geojson.Feature(geometry=geojson.mapping(polygon), properties=feature['properties'])
    #     for polygon, feature in merged_polygons
    # ]
    # return geojson.FeatureCollection(features=final_features)

    return geojson.FeatureCollection(features=filtered_polygons)

def get_wpml_files(
    task_areas: list[geojson.Feature], 
    wayline_spacing: float,
    flight_speed: int,
    gimble_angle: int,
    finish_action: str = "goHome",
):
    """Generate wpml for each task area."""
    zip_file_paths = []

    for index, geom in enumerate(task_areas):
        print(f"Processing task {index + 1} flight plan")
        print(geom)
        waypoints = generate_waypoints_within_polygon(geom, wayline_spacing)

        placemark_data = []

        for x in waypoints:
            placemark_data.append(
                (
                    f"{x['coordinates'][0]},{x['coordinates'][1]}",
                    altitude,
                    flight_speed,
                    int(x["angle"]),
                    gimble_angle,
                )
            )
        output_file = create_xml(
            placemark_data,
            finish_action,
            generate_each_points=False,
            filename=f"task-{index + 1}",
        )

        zip_file_paths.append(output_file)

    all_flightplans = "./flightplans.zip"
    with ZipFile(all_flightplans, 'w') as large_zip:
        for zip_file_path in zip_file_paths:
            large_zip.write(zip_file_path, arcname=zip_file_path.split('/')[-1])

    print(f"All task flightplans zipped into: {all_flightplans}")

# def get_wpml_from_api(task_areas, image_interval, altitude, overlap):
#     """Call waypoint file generation API for task area"""

#     url = "https://waypoint.naxa.com.np/api/waypoint/"
#     headers = {"accept": "application/json"}

#     for index, geom in enumerate(task_areas):
#         files = {
#             "project_geojson": (
#                 "task_polygon.geojson",
#                 geojson.dumps(geom.get("geometry")),
#             )
#         }

#         data = {
#             "altitude": altitude,
#             "image_interval": image_interval,
#             "download": True,
#             "overlap": overlap,
#             "finish_action": "goHome",
#         }

#         response = requests.post(url, headers=headers, data=data, files=files)

#         if response.status_code == 200:
#             print(f"Success: flight plan created")
#         else:
#             print(f"URL: {url}")
#             print(f"Headers: {headers}")
#             print(f"Request Body: {data}")
#             print(f"Failed with status {response.status_code}: {response.text}")

#         # The response is a zip that contains a folder called wmpl
#         # rename the file

if __name__ == "__main__":
    geojson_file_path = "./bobo.geojson"

    geojson_data = load_geojson(geojson_file_path)
    aoi_geom = geojson_data["features"][0]["geometry"]

    # Divide AOI approx 2km length squares grid
    grid_side_meters = 2000
    grid_featcol = split_by_square(aoi_geom, grid_side_meters)
    grid_featcol_no_multipoly = multipoly_to_poly_in_featcol(grid_featcol)
    grid_featcol_final = filter_or_merge_small_polygons_in_featcol(grid_featcol_no_multipoly, grid_side_meters)
    save_geojson(grid_featcol_final, "./output.geojson")

    # Get image interval in seconds for 80m altitude, 20% overlap
    altitude = 80  # meters
    overlap = 20  # percent
    sensor_width = 9.6  # DJI Mini 4 Pro 9.6mm (1/1.3-inch CMOS)
    focal_length = 24  # DJI Mini 4 Pro 24mm
    image_width = 8064  # DJI Mini 4 Pro 8064×6048 pixels
    image_height = 6048  # DJI Mini 4 Pro 8064×6048 pixels
    flight_speed: int = 10  # DJI Mini 4 Pro 12m/s (reduced slightly)
    gimble_angle: int = -90

    gsd = calculate_gsd(altitude, sensor_width, focal_length, image_width)
    wayline_spacing = calculate_wayline_spacing(gsd, overlap, image_width)
    image_interval = calculate_image_interval(gsd, flight_speed, overlap, image_height)

    print(f"GSD: {gsd}")
    print(f"Wayline spacing: {wayline_spacing}")
    print(f"Image interval: {image_interval}")

    waypoints = get_wpml_files(
        grid_featcol_final["features"], wayline_spacing, flight_speed, gimble_angle,
    )
