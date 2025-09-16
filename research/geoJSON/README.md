# Geographic Data Conversion Tools

This repository contains Python programs for converting geographic data between different formats:
1. CSV to GeoJSON converter
2. GeoJSON to KML converter
3. Batch conversion pipeline (CSV → GeoJSON → KML)

## Features

- Groups boundary points by plot number (`lp_no`)
- Orders points by `POINT_ID` to create proper polygon boundaries
- Creates valid GeoJSON polygons with proper coordinate ordering
- Includes metadata like village ID, extent in acres, and point count
- Handles validation and error reporting

## CSV Format

The input CSV should have the following columns:
- `lp_no`: Plot number (used to group boundary points)
- `POINT_ID`: Point sequence number for ordering boundary points
- `LATITUDE`: Latitude coordinate
- `LONGITUDE`: Longitude coordinate
- `Village_id`: Village identifier (optional)
- `extent_ac`: Plot extent in acres (optional)
- `EASTING-X`, `NORTHING-Y`: UTM coordinates (optional)

## Usage

### 1. CSV to GeoJSON

```bash
python csv_to_geojson.py input.csv output.geojson
```

### 2. GeoJSON to KML

```bash
python geojson_to_kml.py input.geojson output.kml
```

### 3. Batch Conversion (CSV → GeoJSON → KML)

```bash
python batch_convert.py input.csv output.kml
```

### Examples

```bash
# Convert CSV to GeoJSON
python csv_to_geojson.py site1.csv output.geojson

# Convert GeoJSON to KML
python geojson_to_kml.py output.geojson output.kml

# One-step conversion from CSV to KML
python batch_convert.py site1.csv final_output.kml
```

## Output Formats

### GeoJSON Output
- FeatureCollection containing polygon features
- Each polygon represents one plot (grouped by `lp_no`)
- Properties include plot number, village ID, extent, and point count
- Proper coordinate ordering for valid polygon geometry

### KML Output
- Valid KML 2.2 format compatible with Google Earth and other GIS software
- Styled polygons with semi-transparent green fill and blue outlines
- Rich placemark descriptions with plot metadata in HTML tables
- Proper coordinate system and altitude handling

## Requirements

No external dependencies - uses only Python standard library modules.

## Error Handling

- Skips invalid rows with missing or malformed data
- Warns about plots with insufficient points (< 3)
- Validates polygon geometry before creating features
