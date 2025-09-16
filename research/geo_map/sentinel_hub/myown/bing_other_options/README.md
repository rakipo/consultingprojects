# Refactored Satellite API Tool

This refactored version separates configuration from functional logic and adds timestamped output management for satellite image retrieval from multiple APIs.

## 🚀 Key Improvements

### 1. **Configuration-Driven Architecture**
- All settings moved to `satellite_api_config.yaml`
- No hardcoded values in the main code
- Easy to modify behavior without code changes
- Centralized API credentials management

### 2. **Timestamped Output Management**
- Automatic timestamped folder creation: `outputs/YYYYMMDD_HHMMSS/`
- Timestamped filenames for images and metadata
- Organized output structure with session tracking
- Configurable naming templates

### 3. **Enhanced Metadata Collection**
- Comprehensive metadata for each API
- Service information gathering (where available)
- Request details and processing information
- Combined metadata files for batch operations

### 4. **Modular Design**
- Separate classes for each API
- `ConfigManager` for configuration handling
- `SatelliteImageManager` for orchestration
- Clean separation of concerns

## 📁 File Structure

```
bing_other_options/
├── satellite_api_config.yaml          # Configuration file
├── satellite_apis_refactored.py       # Main refactored code
├── other_set_of_api.py                # Original version
├── README.md                          # This file
└── outputs/                           # Output directory
    └── 20240115_143022/               # Timestamped session folder
        ├── esri_satellite_14.443014_80.000370_20240115_143022.png
        ├── esri_metadata_14.443014_80.000370_20240115_143022.json
        ├── osm_satellite_14.443014_80.000370_20240115_143022.png
        ├── osm_metadata_14.443014_80.000370_20240115_143022.json
        └── combined_metadata_14.443014_80.000370_20240115_143022.json
```

## ⚙️ Configuration File

The `satellite_api_config.yaml` file contains:

### API Credentials
```yaml
api_credentials:
  google:
    api_key: "YOUR_GOOGLE_STATIC_MAPS_API_KEY"
  mapbox:
    access_token: "YOUR_MAPBOX_ACCESS_TOKEN"
  # ... other APIs
```

### Default Settings
```yaml
default_settings:
  esri:
    width: 1024
    height: 1024
    buffer: 0.005
  # ... other API settings
```

### Output Configuration
```yaml
output:
  base_directory: "outputs"
  create_timestamped_folders: true
  timestamp_format: "%Y%m%d_%H%M%S"
  file_naming:
    image_template: "{api_name}_satellite_{lat:.6f}_{lon:.6f}_{timestamp}.png"
```

## 🖥️ Usage

### Basic Usage
```python
# Initialize the manager
manager = SatelliteImageManager()

# Get single image
image, metadata = manager.get_single_image(lat=14.443014, lon=80.000370, api_name='esri')

# Test all APIs
results = manager.test_all_apis(lat=14.443014, lon=80.000370)
```

### Command Line
```bash
# Install dependencies
pip install requests pillow pyyaml

# Run the program
python satellite_apis_refactored.py
```

## 📊 Metadata Features

Each image comes with comprehensive metadata:

```json
{
  "api_source": "ESRI World Imagery",
  "coordinates": {
    "latitude": 14.443014,
    "longitude": 80.000370
  },
  "image_properties": {
    "actual_size": [1024, 1024],
    "format": "PNG",
    "file_size_bytes": 1234567
  },
  "acquisition_info": {
    "capture_date": "Unknown (ESRI composite imagery)",
    "satellite": "ESRI World Imagery Composite",
    "resolution": "Varies by location (typically 1-3 meters)"
  },
  "processing_info": {
    "requested_at": "2024-01-15T14:30:22.123456",
    "coordinate_system": "EPSG:4326 (WGS84)"
  }
}
```

## 🔧 Configuration Options

### Coordinates
Set default coordinates or use predefined locations:
```yaml
example_locations:
  data_legos:
    latitude: 14.443014
    longitude: 80.000370
```

### Output Settings
Customize output behavior:
```yaml
output:
  create_timestamped_folders: true  # Enable/disable timestamps
  save_metadata: true               # Save metadata files
  metadata_indent: 2                # JSON formatting
```

### Processing Settings
Configure request behavior:
```yaml
processing:
  timeout_seconds: 30
  retry_attempts: 3
  user_agent: "Python Satellite Downloader"
```

## 🆓 Free vs Premium APIs

### Free APIs (No API key required)
- **ESRI World Imagery**: High reliability, global coverage
- **OpenStreetMap Tiles**: Multiple tile servers, good fallback

### Premium APIs (API key required)
- **Google Static Maps**: Highest quality, $2/1000 requests
- **Mapbox**: Excellent quality, 50k free requests/month
- **Bing Maps**: Good quality, free tier available

## 🚦 Error Handling

The refactored version includes robust error handling:
- Graceful degradation when APIs fail
- Detailed error logging
- Automatic fallback to alternative servers
- Comprehensive exception handling

## 📈 Benefits of Refactoring

1. **Maintainability**: Easy to add new APIs or modify existing ones
2. **Configurability**: Change behavior without code modifications
3. **Traceability**: Timestamped outputs for session tracking
4. **Scalability**: Modular design supports easy extensions
5. **Documentation**: Comprehensive metadata for each operation
6. **Organization**: Clean output structure with timestamps

## 🔄 Migration from Original

To migrate from the original `other_set_of_api.py`:

1. Copy your existing API keys to `satellite_api_config.yaml`
2. Update coordinate settings in the config file
3. Use `SatelliteImageManager` instead of direct API calls
4. Check the timestamped output folders for results

## 🛠️ Customization

### Adding New APIs
1. Create new API class following the existing pattern
2. Add configuration section to YAML file
3. Register in `SatelliteImageManager._initialize_apis()`

### Modifying Output Format
1. Update filename templates in config
2. Modify metadata structure in API classes
3. Adjust output directory structure as needed

## 🔍 Dependencies

- `requests`: HTTP requests
- `Pillow`: Image processing
- `PyYAML`: Configuration file parsing
- `datetime`: Timestamp management
- `json`: Metadata serialization
