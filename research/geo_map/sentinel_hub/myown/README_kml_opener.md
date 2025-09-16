# KML to Google Earth Opener

This repository contains Python scripts to open KML files in Google Earth from the command line.

## Scripts

### 1. `open_kml_in_earth.py` (Basic Version)
A simple script that attempts to open KML files in Google Earth web interface.

### 2. `open_kml_in_earth_alternative.py` (Advanced Version)
A more comprehensive script that tries multiple methods to open KML files.

## Usage

### Basic Usage
```bash
python open_kml_in_earth.py <path_to_kml_file>
```

### Advanced Usage
```bash
# Try automatic method (desktop app first, then web)
python open_kml_in_earth_alternative.py <path_to_kml_file>

# Force desktop application only
python open_kml_in_earth_alternative.py --method desktop <path_to_kml_file>

# Force web interface only
python open_kml_in_earth_alternative.py --method web <path_to_kml_file>
```

## Examples

```bash
# Open the sample KML file
python open_kml_in_earth.py divide_and_analyze/office_025acre_square.kml

# Using the alternative script with web method
python open_kml_in_earth_alternative.py --method web divide_and_analyze/office_025acre_square.kml
```

## Features

### File Validation
- Checks if the file exists
- Validates that the file has a `.kml` extension
- Provides helpful error messages

### Multiple Opening Methods
1. **Desktop Application**: Attempts to open with Google Earth Pro desktop app
2. **Web Interface**: Opens Google Earth web interface with instructions
3. **Automatic Fallback**: Tries desktop first, then web interface

### Cross-Platform Support
- **macOS**: Uses `open -a "Google Earth Pro"`
- **Windows**: Uses `start "Google Earth Pro"`
- **Linux**: Uses `google-earth-pro` command

## Requirements

- Python 3.6 or higher
- Standard library modules (no external dependencies):
  - `sys`
  - `os`
  - `webbrowser`
  - `argparse`
  - `subprocess`
  - `platform`
  - `pathlib`

## Sample KML File

The repository includes a sample KML file: `divide_and_analyze/office_025acre_square.kml`

This file contains:
- A 0.25-acre square polygon
- A center point marker
- Custom styling with red color

## Troubleshooting

### Desktop App Not Found
If Google Earth Pro is not installed or not found:
1. Download from: https://www.google.com/earth/versions/
2. Use the web interface method instead

### Web Interface Issues
If the web interface doesn't work:
1. Manually open https://earth.google.com/web/
2. Click "Projects" → "Import KML file from device"
3. Select your KML file

### Alternative KML Viewers
If Google Earth doesn't work, try:
- **QGIS**: Free GIS software
- **Marble**: KDE's virtual globe
- **NASA World Wind**: Open-source virtual globe
- **Google My Maps**: Web-based mapping tool

## License

This script is provided as-is for educational and personal use.
