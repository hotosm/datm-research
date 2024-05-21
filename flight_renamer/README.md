# Flight Renamer

Process the image files from a drone flight:
- Extract EXIF coordinates.
- Create metadata CSV file with file paths and coordinates.
- Move input files from a specified BBOX into an output directory
  for further processing.

Eventually this could also be part of a QGIS plugin, where the user draws a BBOX
and the files are filtered based on that.

## Usage

```
usage: main.py [-h] [--bbox BBOX BBOX BBOX BBOX] [--geojson GEOJSON] source_path output_path

Process images and filter based on EXIF data.

positional arguments:
  source_path           Path to the source directory containing image directories.
  output_path           Path to the output directory for filtered images.

options:
  -h, --help            show this help message and exit
  --bbox BBOX BBOX BBOX BBOX
                        Bounding box coordinates (min_lat, min_lon, max_lat, max_lon).
  --geojson GEOJSON     Path to the GeoJSON file containing bounding geometry.
```

Run via PDM (with PIL dependency):

```bash
# If PDM is not installed: pip install pdm
pdm install
pdm run main.py input output --geojson bbox.geojson
```
