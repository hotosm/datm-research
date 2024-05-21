"""Process images from drone flights.

Example usage:
    pdm run main.py input output --bbox 40 10 45 20
    pdm run main.py input output --geojson bbox.geojson
"""

from typing import Optional
from argparse import ArgumentParser
from csv import reader as csvreader, writer as csvwriter
from json import load
from pathlib import Path
from PIL import Image, UnidentifiedImageError
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime
from shutil import copy as os_copy


def get_exif_data(image_path: Path) -> Optional[tuple[float, float]]:
    """
    Extracts GPS latitude and longitude from the EXIF data of an image.

    Args:
        image_path (Path): Path to the image file.

    Returns:
        Optional[tuple[float, float]]: Latitude and longitude if found, else None.
    """
    try:
        image = Image.open(image_path)
        print(f"Processing image: {image_path}")
    except UnidentifiedImageError as e:
        print(f"Skipping invalid image file: {image_path}")
        return None

    exif_data = image._getexif()
    if not exif_data:
        print(f"Image has no EXIF info: {image_path}")
        return None

    exif = {TAGS.get(tag, tag): value for tag, value in exif_data.items()}
    gps_info = exif.get("GPSInfo")
    if not gps_info:
        print(f"Image has no GPS info: {image_path}")
        return None

    gps_data = {}
    for key, value in gps_info.items():
        decode = GPSTAGS.get(key, key)
        gps_data[decode] = value

    if "GPSLatitude" in gps_data and "GPSLongitude" in gps_data:
        lat = convert_to_degrees(gps_data["GPSLatitude"], gps_data["GPSLatitudeRef"])
        lon = convert_to_degrees(gps_data["GPSLongitude"], gps_data["GPSLongitudeRef"])
        return lat, lon
    return None


def get_bounding_box_from_geojson(
    geojson_path: Path,
) -> Optional[tuple[float, float, float, float]]:
    """
    Extracts the bounding box coordinates from a GeoJSON file.

    Args:
        geojson_path (Path): Path to the GeoJSON file.

    Returns:
        Optional[tuple[float, float, float, float]]: Bounding box coordinates (min_lat, min_lon, max_lat, max_lon),
        or None if no valid bounding box found.
    """
    with open(geojson_path, "r") as geojson_file:
        data = load(geojson_file)

        if data.get("type") == "FeatureCollection":
            return _extract_bounding_box_from_features(data.get("features"))
        elif data.get("type") == "Feature":
            return _extract_bounding_box_from_geometry(data.get("geometry"))
        elif data.get("type") == "Polygon":
            return _extract_bounding_box_from_geometry(data)

    return None


def _extract_bounding_box_from_features(
    features: list[dict],
) -> Optional[tuple[float, float, float, float]]:
    """
    Extracts the bounding box coordinates from a list of GeoJSON features.

    Args:
        features (List[dict]): List of GeoJSON features.

    Returns:
        Optional[tuple[float, float, float, float]]: Bounding box coordinates (min_lat, min_lon, max_lat, max_lon),
        or None if no valid bounding box found.
    """
    bbox = [float("inf"), float("inf"), float("-inf"), float("-inf")]

    for feature in features:
        geometry = feature.get("geometry")
        if geometry and geometry["type"] == "Polygon":
            feature_bbox = _extract_bounding_box_from_geometry(geometry)
            if feature_bbox:
                bbox = [min(bbox[i], feature_bbox[i]) for i in range(4)]
                bbox = [max(bbox[i], feature_bbox[i]) for i in range(4)]

    if any(b == float("inf") or b == float("-inf") for b in bbox):
        return None

    return tuple(bbox)


def _extract_bounding_box_from_geometry(
    geometry: dict,
) -> Optional[tuple[float, float, float, float]]:
    """
    Extracts the bounding box coordinates from a GeoJSON geometry.

    Args:
        geometry (dict): GeoJSON geometry.

    Returns:
        Optional[tuple[float, float, float, float]]: Bounding box coordinates (min_lat, min_lon, max_lat, max_lon),
        or None if no valid bounding box found.
    """
    if geometry["type"] == "Polygon":
        coordinates = geometry["coordinates"][0]  # Assuming only exterior ring is used
        bbox = [float("inf"), float("inf"), float("-inf"), float("-inf")]

        for lon, lat in coordinates:
            bbox[0] = min(bbox[0], lat)
            bbox[1] = min(bbox[1], lon)
            bbox[2] = max(bbox[2], lat)
            bbox[3] = max(bbox[3], lon)

        return tuple(bbox)

    return None


def convert_to_degrees(value: tuple[int, int, int], ref: str) -> float:
    """
    Converts GPS coordinates from degrees, minutes, seconds format to decimal degrees.

    Args:
        value (tuple[int, int, int]): tuple of degrees, minutes, seconds.
        ref (str): Reference direction ('N', 'S', 'E', 'W').

    Returns:
        float: Decimal degrees.
    """
    d = float(value[0])
    m = float(value[1]) / 60.0
    s = float(value[2]) / 3600.0
    result = d + m + s
    if ref in ["S", "W"]:
        result = -result
    return result


def create_csv(
    image_dirs: list[Path],
    output_csv: Path,
    bbox: tuple[float, float, float, float],
    target_dir: Path,
) -> None:
    """
    Creates a CSV file containing image metadata and bounding box information.

    Args:
        image_dirs (list[Path]): list of directories containing images.
        output_csv (Path): Path to the output CSV file.
        bbox (tuple[float, float, float, float]): Bounding box coordinates (min_lat, min_lon, max_lat, max_lon).
        target_dir (Path): Path to the directory where images will be copied.
    """
    with open(output_csv, "w", newline="") as csvfile:
        csv_writer = csvwriter(csvfile)
        csv_writer.writerow(["source_path", "dest_path", "latitude", "longitude"])
        csv_writer.writerow(
            [
                "Bounding box",
                f"min_lat={bbox[0]}",
                f"min_lon={bbox[1]}",
                f"max_lat={bbox[2]}",
                f"max_lon={bbox[3]}",
            ]
        )

        for flight_number, image_dir_path in enumerate(image_dirs, start=1):
            for image_path in image_dir_path.glob("*.*"):
                coords = get_exif_data(image_path)
                if coords:
                    lat, lon = coords
                    if is_within_bbox(lat, lon, bbox):
                        file_extension = image_path.suffix
                        new_file_name = (
                            f"flight_{flight_number}_{image_path.stem}{file_extension}"
                        )
                        new_file_path = target_dir / new_file_name
                        csv_writer.writerow(
                            [image_path.absolute(), new_file_path.absolute(), lat, lon]
                        )


def is_within_bbox(
    lat: float, lon: float, bbox: tuple[float, float, float, float]
) -> bool:
    """
    Checks if a given latitude and longitude fall within a bounding box.

    Args:
        lat (float): Latitude.
        lon (float): Longitude.
        bbox (tuple[float, float, float, float]): Bounding box coordinates (min_lat, min_lon, max_lat, max_lon).

    Returns:
        bool: True if the coordinates are within the bounding box, else False.
    """
    min_lat, min_lon, max_lat, max_lon = bbox
    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon


def filter_and_copy_images(csv_file: Path) -> None:
    """
    Filters images based on the information in the CSV file and copies them to the destination directory.

    Args:
        csv_file (Path): Path to the CSV file containing image metadata.
    """
    with open(csv_file, "r") as csvfile:
        csv_data = csvreader(csvfile)
        header = next(csv_data)  # Skip header
        bbox_info = next(csv_data)  # Skip bounding box info

        for row in csv_data:
            source_path, dest_path, lat, lon = row
            os_copy(source_path, dest_path)


def main() -> None:
    """
    Main function to process images based on provided arguments.
    """
    parser = ArgumentParser(description="Process images and filter based on EXIF data.")
    parser.add_argument(
        "source_path",
        type=str,
        help="Path to the source directory containing image directories.",
    )
    parser.add_argument(
        "output_path",
        type=str,
        help="Path to the output directory for filtered images.",
    )
    parser.add_argument(
        "--bbox",
        type=float,
        nargs=4,
        help="Bounding box coordinates (min_lat, min_lon, max_lat, max_lon).",
    )
    parser.add_argument(
        "--geojson",
        type=str,
        help="Path to the GeoJSON file containing bounding geometry.",
    )
    args = parser.parse_args()

    if args.bbox and args.geojson:
        parser.error("Both --bbox and --geojson cannot be provided simultaneously.")

    if args.bbox:
        bbox = tuple(args.bbox)
    elif args.geojson:
        bbox = get_bounding_box_from_geojson(Path(args.geojson))
    else:
        parser.error("Either --bbox or --geojson must be provided.")

    source_path = Path(args.source_path)
    output_path = Path(args.output_path)

    source_image_dirs = [d for d in source_path.iterdir() if d.is_dir()]

    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = output_path / f"metadata_{current_datetime}.csv"
    if not csv_path.parent.exists():
        csv_path.parent.mkdir(exist_ok=True, parents=True)
    create_csv(source_image_dirs, csv_path, bbox, output_path)
    filter_and_copy_images(csv_path)


if __name__ == "__main__":
    main()
