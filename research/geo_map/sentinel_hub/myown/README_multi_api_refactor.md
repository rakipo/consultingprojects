# Multi-API Satellite Image Creation System

This system has been refactored to use a centralized configuration file (`multi_image_api_config.yaml`) for all parameters, making it more maintainable and flexible.

## Overview

The refactored system supports multiple satellite imagery APIs:
- **NASA GIBS** (free, no authentication required)
- **Sentinel Hub** (requires OAuth credentials)
- **Planet Labs** (requires API key)

## Key Improvements

### 1. Configuration-Driven Architecture
- All parameters moved to `multi_image_api_config.yaml`
- No hardcoded values in the Python code
- Easy to modify settings without code changes

### 2. Enhanced Error Handling
- Comprehensive logging system
- Configurable retry mechanisms
- Fallback image creation for failed requests

### 3. Input Validation
- Coordinate validation (latitude/longitude bounds)
- Date format and range validation
- Image dimension validation

### 4. Flexible Output Management
- Configurable file naming templates
- Automatic directory organization
- Metadata generation and storage

## Configuration File Structure

### API Credentials
```yaml
api_credentials:
  sentinel_hub:
    client_id: "YOUR_SENTINEL_HUB_CLIENT_ID"
    client_secret: "YOUR_SENTINEL_HUB_CLIENT_SECRET"
  planet_labs:
    api_key: "YOUR_PLANET_LABS_API_KEY"
```

### NASA GIBS Settings
```yaml
nasa_gibs:
  default_layer: "VIIRS_SNPP_CorrectedReflectance_TrueColor"
  tile_settings:
    default_zoom: 8
    default_tile_size: 3
    timeout_seconds: 10
```

### Sentinel Hub Settings
```yaml
sentinel_hub:
  image_settings:
    default_width: 1024
    default_height: 1024
    max_cloud_coverage: 80
  cloud_masking:
    cloud_classes: [3, 8, 9]
    transparency_factor: 0.7
```

### Output Configuration
```yaml
output_settings:
  filename_template: "satellite_{source}_{lat}_{lon}_{date}.{ext}"
  directories:
    base_output_dir: "satellite_images"
    create_date_subdirs: true
    create_location_subdirs: true
```

## Usage Examples

### Basic Usage
```python
from multi_api_image_creation import ConfigManager, find_best_image_for_time

# Load configuration
config = ConfigManager("multi_image_api_config.yaml")

# Search for images
results = find_best_image_for_time(
    latitude=40.7589,
    longitude=-73.9851,
    target_datetime="2024-07-15",
    config=config
)
```

### Custom API Selection
```python
# Try only NASA and Sentinel Hub
results = find_best_image_for_time(
    latitude=40.7589,
    longitude=-73.9851,
    target_datetime="2024-07-15",
    config=config,
    apis_to_try=['nasa', 'sentinel']
)
```

### Using Example Data from Config
```python
# Get coordinates from config file
example_coords = config.get('example_data.coordinates.times_square_nyc', {})
latitude = example_coords.get('latitude')
longitude = example_coords.get('longitude')

results = find_best_image_for_time(
    latitude=latitude,
    longitude=longitude,
    target_datetime="2024-07-15",
    config=config
)
```

## Configuration Parameters

### API Credentials Section
- **sentinel_hub**: OAuth credentials for Sentinel Hub
- **planet_labs**: API key for Planet Labs
- **nasa**: Base URLs for NASA services

### NASA GIBS Section
- **default_layer**: Default satellite layer to use
- **available_layers**: List of available NASA layers
- **tile_settings**: Tile fetching parameters
- **date_search**: Date range expansion settings

### Sentinel Hub Section
- **authentication**: OAuth settings
- **image_settings**: Image dimensions and quality
- **evalscript**: JavaScript processing parameters
- **data_source**: Sentinel-2 data source settings
- **cloud_masking**: Cloud detection and handling

### Planet Labs Section
- **search**: Image search parameters
- **geometry**: Area of interest settings
- **filters**: Search filter configurations

### Image Processing Section
- **output_format**: Image format (PNG, JPEG, TIFF)
- **enhancement**: Color and contrast settings
- **normalization**: Value normalization parameters

### Search Configuration
- **default_apis**: APIs to try by default
- **api_priority_order**: Priority order for API selection
- **fallback_strategy**: Date expansion and API fallback settings
- **quality_preferences**: Image quality preferences

### Output Settings
- **filename_template**: Template for output filenames
- **directories**: Directory organization settings
- **file_organization**: File grouping options

### Error Handling
- **max_retries**: Maximum retry attempts
- **logging**: Logging configuration
- **fallback_images**: Placeholder image settings

### Performance Settings
- **concurrent_requests**: Number of concurrent API requests
- **cache_results**: Caching configuration
- **memory_management**: Memory usage settings

## File Organization

The refactored system creates organized output directories:

```
satellite_images/
├── 2024-07/
│   └── lat40.7589_lon-73.9851/
│       ├── satellite_NASA_VIIRS_40.7589_-73.9851_2024-07-15.png
│       ├── satellite_NASA_VIIRS_40.7589_-73.9851_2024-07-15_metadata.json
│       ├── satellite_Sentinel-2_40.7589_-73.9851_2024-07-15.png
│       └── satellite_Sentinel-2_40.7589_-73.9851_2024-07-15_metadata.json
```

## Error Handling

The system includes comprehensive error handling:

1. **Input Validation**: Validates coordinates and dates before processing
2. **API Failures**: Graceful handling of API errors with fallback options
3. **Network Issues**: Retry mechanisms for network failures
4. **Missing Data**: Placeholder image creation for missing tiles
5. **Logging**: Detailed logging for debugging and monitoring

## Performance Optimizations

- **Concurrent Requests**: Configurable concurrent API requests
- **Caching**: Optional result caching to reduce API calls
- **Memory Management**: Configurable image size limits and compression
- **Request Delays**: Configurable delays between requests to avoid rate limiting

## Validation Rules

The system validates:
- **Coordinates**: Latitude (-90 to 90), Longitude (-180 to 180)
- **Dates**: Format and range validation (2015-2025)
- **Image Dimensions**: Minimum and maximum size limits
- **API Credentials**: Format and presence validation

## Migration from Old Code

### Before (Hardcoded Parameters)
```python
# Old way with hardcoded values
nasa_client = TimeSpecificSatelliteImagery()
image, date = nasa_client.get_nasa_image_by_date(
    latitude, longitude, target_date,
    layer='VIIRS_SNPP_CorrectedReflectance_TrueColor',
    zoom=8, tile_size=3
)
```

### After (Configuration-Driven)
```python
# New way using configuration
config = ConfigManager("multi_image_api_config.yaml")
nasa_client = TimeSpecificSatelliteImagery(config)
image, date = nasa_client.get_nasa_image_by_date(
    latitude, longitude, target_date
)
```

## Benefits of Refactoring

1. **Maintainability**: Easy to modify settings without code changes
2. **Flexibility**: Support for multiple configurations and environments
3. **Scalability**: Easy to add new APIs and parameters
4. **Reliability**: Better error handling and validation
5. **Usability**: Clear separation of configuration and logic
6. **Documentation**: Self-documenting configuration structure

## Next Steps

1. **Add Your Credentials**: Update the configuration file with your API credentials
2. **Customize Settings**: Modify parameters based on your requirements
3. **Test Different APIs**: Try different combinations of APIs
4. **Extend Functionality**: Add new APIs or processing options

## Support

For issues or questions:
1. Check the configuration file for correct settings
2. Review the log files for error details
3. Validate your API credentials
4. Ensure your coordinates and dates are within valid ranges
