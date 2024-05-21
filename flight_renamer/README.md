# Flight Renamer

Process the image files from a drone flight:
- Extract EXIF coordinates.
- Create metadata CSV file with file paths and coordinates.
- Move input files from a specified BBOX into an output directory
  for further processing.

Eventually this could also be part of a QGIS plugin, where the user draws a BBOX
and the files are filtered based on that.
