# Quick Commands Reference

## CSV to GeoJSON
```bash
python csv_to_geojson.py site1.csv output.geojson
```
**Purpose:** Convert CSV plot data to GeoJSON format

## GeoJSON to KML
```bash
python geojson_to_kml.py output.geojson output.kml
```
**Purpose:** Convert GeoJSON to KML for Google Earth/GIS software

## One-Step Conversion (CSV → KML)
```bash
python batch_convert.py site1.csv final_output.kml
```
**Purpose:** Direct conversion from CSV to KML in one command

## File Structure
- `site1.csv` - Input CSV with plot boundary points
- `output.geojson` - Intermediate GeoJSON file
- `output.kml` - Final KML file for GIS applications
