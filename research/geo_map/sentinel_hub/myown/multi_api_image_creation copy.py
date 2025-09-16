import requests
from PIL import Image
import io
from datetime import datetime, timedelta
import math
import json
import yaml
import os
import logging
from typing import Dict, List, Tuple, Optional, Any

class ConfigManager:
    """Manages configuration loading and validation"""
    
    def __init__(self, config_path: str = "multi_image_api_config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
            print(f"✅ Configuration loaded from {self.config_path}")
            return config
        except FileNotFoundError:
            print(f"❌ Configuration file not found: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            print(f"❌ Error parsing YAML file: {e}")
            raise
    
    def _setup_logging(self):
        """Setup logging based on configuration"""
        log_config = self.config.get('error_handling', {}).get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        if log_config.get('save_logs', False):
            log_file = log_config.get('log_file', 'satellite_image_retrieval.log')
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            logging.getLogger().addHandler(file_handler)
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def validate_coordinates(self, latitude: float, longitude: float) -> bool:
        """Validate coordinate values"""
        validation = self.get('validation.coordinates', {})
        return (validation.get('min_latitude', -90) <= latitude <= validation.get('max_latitude', 90) and
                validation.get('min_longitude', -180) <= longitude <= validation.get('max_longitude', 180))
    
    def validate_date(self, date_str: str) -> bool:
        """Validate date format and range"""
        try:
            date_format = self.get('validation.dates.date_format', '%Y-%m-%d')
            date_obj = datetime.strptime(date_str, date_format)
            
            min_date = datetime.strptime(self.get('validation.dates.min_date', '2015-01-01'), date_format)
            max_date = datetime.strptime(self.get('validation.dates.max_date', '2025-12-31'), date_format)
            
            return min_date <= date_obj <= max_date
        except ValueError:
            return False

class TimeSpecificSatelliteImagery:
    """Get satellite imagery for specific dates and times"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.nasa_base = config.get('api_credentials.nasa.base_url')
        self.landsat_base = config.get('api_credentials.nasa.landsat_base')
        self.logger = logging.getLogger(__name__)
    
    def deg2num(self, lat_deg: float, lon_deg: float, zoom: int) -> Tuple[int, int]:
        """Convert lat/lon to tile numbers"""
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        xtile = int((lon_deg + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return (xtile, ytile)
    
    def get_nasa_image_by_date(self, latitude: float, longitude: float, target_date: str, 
                              layer: str = None, zoom: int = None, tile_size: int = None) -> Tuple[Optional[Image.Image], str]:
        """
        Get NASA satellite image for specific date
        
        Args:
            latitude (float): Latitude coordinate
            longitude (float): Longitude coordinate
            target_date (str): Date in 'YYYY-MM-DD' format
            layer (str): NASA layer to use
            zoom (int): Zoom level (1-10)
            tile_size (int): Number of tiles to fetch
        """
        
        # Use configuration defaults if not provided
        layer = layer or self.config.get('nasa_gibs.default_layer')
        zoom = zoom or self.config.get('nasa_gibs.tile_settings.default_zoom')
        tile_size = tile_size or self.config.get('nasa_gibs.tile_settings.default_tile_size')
        timeout = self.config.get('nasa_gibs.tile_settings.timeout_seconds', 10)
        
        print(f"Fetching NASA imagery for {target_date} at {latitude}, {longitude}")
        
        # Validate inputs
        if not self.config.validate_coordinates(latitude, longitude):
            raise ValueError(f"Invalid coordinates: {latitude}, {longitude}")
        
        if not self.config.validate_date(target_date):
            raise ValueError(f"Invalid date: {target_date}")
        
        # Get center tile
        center_x, center_y = self.deg2num(latitude, longitude, zoom)
        
        # Calculate tile range
        half_size = tile_size // 2
        tiles = []
        
        for y in range(center_y - half_size, center_y + half_size + 1):
            row = []
            for x in range(center_x - half_size, center_x + half_size + 1):
                tile_url = (f"{self.nasa_base}/{layer}/default/{target_date}/"
                           f"GoogleMapsCompatible_Level6/{zoom}/{y}/{x}.jpg")
                
                try:
                    response = requests.get(tile_url, timeout=timeout)
                    if response.status_code == 200:
                        tile_img = Image.open(io.BytesIO(response.content))
                        row.append(tile_img)
                        print(f"✓ Got tile ({x}, {y})")
                    else:
                        placeholder_config = self.config.get('error_handling.fallback_images', {})
                        if placeholder_config.get('create_placeholder', True):
                            placeholder_size = placeholder_config.get('placeholder_size', [256, 256])
                            placeholder_color = placeholder_config.get('placeholder_color', 'gray')
                            tile_img = Image.new('RGB', tuple(placeholder_size), color=placeholder_color)
                            row.append(tile_img)
                        print(f"✗ No data for tile ({x}, {y}) on {target_date}")
                except Exception as e:
                    self.logger.error(f"Error fetching tile ({x}, {y}): {e}")
                    placeholder_config = self.config.get('error_handling.fallback_images', {})
                    if placeholder_config.get('create_placeholder', True):
                        placeholder_size = placeholder_config.get('placeholder_size', [256, 256])
                        placeholder_color = placeholder_config.get('placeholder_color', 'gray')
                        tile_img = Image.new('RGB', tuple(placeholder_size), color=placeholder_color)
                        row.append(tile_img)
                    print(f"✗ Error: {e}")
            tiles.append(row)
        
        # Stitch tiles
        if tiles and tiles[0]:
            tile_width, tile_height = tiles[0][0].size
            final_image = Image.new('RGB', 
                                  (len(tiles[0]) * tile_width, len(tiles) * tile_height))
            
            for row_idx, row in enumerate(tiles):
                for col_idx, tile in enumerate(row):
                    final_image.paste(tile, (col_idx * tile_width, row_idx * tile_height))
            
            return final_image, target_date
        
        return None, target_date

class SentinelHubTimeSpecific:
    """Fixed Sentinel Hub implementation for time-specific imagery"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.client_id = config.get('api_credentials.sentinel_hub.client_id')
        self.client_secret = config.get('api_credentials.sentinel_hub.client_secret')
        self.base_url = config.get('api_credentials.sentinel_hub.base_url')
        self.token = None
        self.logger = logging.getLogger(__name__)
        self.authenticate()
    
    def authenticate(self):
        """Get OAuth2 token"""
        auth_config = self.config.get('sentinel_hub.authentication', {})
        auth_url = f"{self.base_url}{auth_config.get('token_endpoint', '/oauth/token')}"
        auth_data = {
            'grant_type': auth_config.get('grant_type', 'client_credentials'),
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        response = requests.post(auth_url, data=auth_data)
        if response.status_code == 200:
            self.token = response.json()['access_token']
            print("✓ Sentinel Hub authenticated")
        else:
            raise Exception(f"Auth failed: {response.text}")
    
    def _create_evalscript(self) -> str:
        """Create evalscript based on configuration"""
        evalscript_config = self.config.get('sentinel_hub.evalscript', {})
        cloud_config = self.config.get('sentinel_hub.cloud_masking', {})
        
        cloud_classes = cloud_config.get('cloud_classes', [3, 8, 9])
        transparency_factor = cloud_config.get('transparency_factor', 0.7)
        color_enhancement = cloud_config.get('color_enhancement', 3.5)
        
        return f"""
        //VERSION={evalscript_config.get('version', '3')}
        function setup() {{
            return {{
                input: [{{
                    bands: {evalscript_config.get('input_bands', ['B02', 'B03', 'B04', 'B08', 'SCL'])},
                    units: "DN"
                }}],
                output: {{
                    bands: {evalscript_config.get('output_bands', 3)},
                    sampleType: "{evalscript_config.get('sample_type', 'AUTO')}"
                }}
            }};
        }}

        function evaluatePixel(sample) {{
            // Enhanced true color with cloud masking
            if ({' || '.join([f'sample.SCL == {cls}' for cls in cloud_classes])}) {{
                // Clouds, cloud shadows, cirrus - make slightly transparent
                return [sample.B04 * {color_enhancement} * {transparency_factor}, 
                        sample.B03 * {color_enhancement} * {transparency_factor}, 
                        sample.B02 * {color_enhancement} * {transparency_factor}];
            }}
            
            // Normal land/water - enhanced colors
            return [
                Math.min(1, sample.B04 * {color_enhancement}),
                Math.min(1, sample.B03 * {color_enhancement}), 
                Math.min(1, sample.B02 * {color_enhancement})
            ];
        }}
        """
    
    def get_image_exact_date(self, latitude: float, longitude: float, target_date: str, 
                           bbox_size: float = None, width: int = None, height: int = None) -> Tuple[Optional[Image.Image], str]:
        """
        Get Sentinel-2 image for exact date with proper evalscript
        
        Args:
            latitude (float): Latitude
            longitude (float): Longitude  
            target_date (str): Exact date 'YYYY-MM-DD'
            bbox_size (float): Bounding box size in degrees
            width/height (int): Image dimensions
        """
        
        # Use configuration defaults if not provided
        bbox_size = bbox_size or self.config.get('sentinel_hub.image_settings.default_bbox_size')
        width = width or self.config.get('sentinel_hub.image_settings.default_width')
        height = height or self.config.get('sentinel_hub.image_settings.default_height')
        max_cloud_coverage = self.config.get('sentinel_hub.image_settings.max_cloud_coverage')
        
        # Validate inputs
        if not self.config.validate_coordinates(latitude, longitude):
            raise ValueError(f"Invalid coordinates: {latitude}, {longitude}")
        
        if not self.config.validate_date(target_date):
            raise ValueError(f"Invalid date: {target_date}")
        
        bbox = [
            longitude - bbox_size/2, latitude - bbox_size/2,
            longitude + bbox_size/2, latitude + bbox_size/2
        ]
        
        # Create evalscript
        evalscript = self._create_evalscript()
        
        data_source_config = self.config.get('sentinel_hub.data_source', {})
        
        payload = {
            "input": {
                "bounds": {
                    "bbox": bbox,
                    "properties": {"crs": data_source_config.get('crs')}
                },
                "data": [{
                    "type": data_source_config.get('type', 'sentinel-2-l2a'),
                    "dataFilter": {
                        "timeRange": {
                            "from": f"{target_date}T00:00:00Z",
                            "to": f"{target_date}T23:59:59Z"
                        },
                        "maxCloudCoverage": max_cloud_coverage
                    }
                }]
            },
            "output": {
                "width": width,
                "height": height,
                "responses": [{
                    "identifier": "default",
                    "format": {"type": "image/png"}
                }]
            },
            "evalscript": evalscript
        }
        
        auth_config = self.config.get('sentinel_hub.authentication', {})
        process_endpoint = auth_config.get('process_endpoint', '/api/v1/process')
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(f"{self.base_url}{process_endpoint}", 
                               headers=headers, json=payload)
        
        if response.status_code == 200:
            image = Image.open(io.BytesIO(response.content))
            return image, target_date
        else:
            self.logger.error(f"Sentinel Hub error: {response.status_code} - {response.text}")
            print(f"Sentinel Hub error: {response.status_code} - {response.text}")
            return None, target_date

class PlanetLabsImagery:
    """Planet Labs API for daily imagery (requires API key)"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.api_key = config.get('api_credentials.planet_labs.api_key')
        self.base_url = config.get('api_credentials.planet_labs.base_url')
        self.logger = logging.getLogger(__name__)
    
    def search_images_by_date(self, latitude: float, longitude: float, target_date: str, 
                             date_range_days: int = None) -> List[Dict]:
        """
        Search for Planet images near specific date
        
        Args:
            latitude (float): Latitude
            longitude (float): Longitude
            target_date (str): Target date 'YYYY-MM-DD'
            date_range_days (int): Search within +/- days of target
        """
        
        # Use configuration defaults if not provided
        date_range_days = date_range_days or self.config.get('planet_labs.search.default_date_range_days')
        max_cloud_cover = self.config.get('planet_labs.search.max_cloud_cover')
        item_types = self.config.get('planet_labs.search.item_types', ['PSScene'])
        
        # Validate inputs
        if not self.config.validate_coordinates(latitude, longitude):
            raise ValueError(f"Invalid coordinates: {latitude}, {longitude}")
        
        if not self.config.validate_date(target_date):
            raise ValueError(f"Invalid date: {target_date}")
        
        # Create date range
        target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        start_date = (target_dt - timedelta(days=date_range_days)).strftime('%Y-%m-%dT00:00:00.000Z')
        end_date = (target_dt + timedelta(days=date_range_days)).strftime('%Y-%m-%dT23:59:59.999Z')
        
        # Define AOI (Area of Interest)
        geometry_config = self.config.get('planet_labs.geometry', {})
        aoi = {
            "type": geometry_config.get('type', 'Point'),
            "coordinates": [longitude, latitude]
        }
        
        # Search filter
        filters_config = self.config.get('planet_labs.filters', {})
        search_filter = {
            "type": "AndFilter",
            "config": [
                {
                    "type": "GeometryFilter",
                    "field_name": filters_config.get('geometry_filter', {}).get('field_name', 'geometry'),
                    "config": aoi
                },
                {
                    "type": "DateRangeFilter", 
                    "field_name": filters_config.get('date_range_filter', {}).get('field_name', 'acquired'),
                    "config": {
                        "gte": start_date,
                        "lte": end_date
                    }
                },
                {
                    "type": "RangeFilter",
                    "field_name": filters_config.get('cloud_cover_filter', {}).get('field_name', 'cloud_cover'),
                    "config": {"lte": max_cloud_cover}
                }
            ]
        }
        
        # Search request
        search_request = {
            "item_types": item_types,
            "filter": search_filter
        }
        
        headers = {'Authorization': f'api-key {self.api_key}'}
        
        response = requests.post(f"{self.base_url}/data/v1/quick-search",
                               json=search_request, headers=headers)
        
        if response.status_code == 200:
            results = response.json()
            return results.get('features', [])
        else:
            self.logger.error(f"Planet search error: {response.status_code}")
            print(f"Planet search error: {response.status_code}")
            return []

class ImageProcessor:
    """Handles image processing and output management"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def save_image(self, image: Image.Image, source: str, latitude: float, longitude: float, 
                  date_used: str, output_dir: str = None) -> str:
        """Save image with proper naming and organization"""
        
        output_config = self.config.get('output_settings', {})
        filename_template = output_config.get('filename_template', 'satellite_{source}_{lat}_{lon}_{date}.{ext}')
        
        # Determine output directory
        if output_dir is None:
            output_dir = output_config.get('directories.base_output_dir', 'satellite_images')
        
        # Create subdirectories if configured
        if output_config.get('directories.create_date_subdirs', True):
            date_dir = os.path.join(output_dir, date_used[:7])  # YYYY-MM
            os.makedirs(date_dir, exist_ok=True)
            output_dir = date_dir
        
        if output_config.get('directories.create_location_subdirs', True):
            location_dir = os.path.join(output_dir, f"lat{latitude:.4f}_lon{longitude:.4f}")
            os.makedirs(location_dir, exist_ok=True)
            output_dir = location_dir
        
        # Create filename
        ext = output_config.get('output_format', 'PNG').lower()
        filename = filename_template.format(
            source=source,
            lat=f"{latitude:.4f}",
            lon=f"{longitude:.4f}",
            date=date_used,
            ext=ext
        )
        
        filepath = os.path.join(output_dir, filename)
        
        # Save image
        image.save(filepath, format=ext.upper())
        
        # Save metadata if configured
        if output_config.get('save_metadata', True):
            self._save_metadata(filepath, source, latitude, longitude, date_used)
        
        print(f"💾 Image saved: {filepath}")
        return filepath
    
    def _save_metadata(self, image_path: str, source: str, latitude: float, longitude: float, date_used: str):
        """Save metadata for the image"""
        metadata = {
            "source": source,
            "coordinates": {
                "latitude": latitude,
                "longitude": longitude
            },
            "date_acquired": date_used,
            "created_at": datetime.now().isoformat(),
            "image_path": image_path,
            "config_used": self.config.config_path
        }
        
        metadata_path = image_path.replace('.png', '_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

def find_best_image_for_time(latitude: float, longitude: float, target_datetime: str, 
                            config: ConfigManager, apis_to_try: List[str] = None) -> List[Tuple[Image.Image, str, str]]:
    """
    Find the best available satellite image for a specific date/time
    
    Args:
        latitude (float): Latitude coordinate
        longitude (float): Longitude coordinate  
        target_datetime (str): Target date/time 'YYYY-MM-DD HH:MM:SS' or 'YYYY-MM-DD'
        config (ConfigManager): Configuration manager instance
        apis_to_try (list): APIs to try in order
    
    Returns:
        list: List of tuples (image, actual_date, source)
    """
    
    # Parse target date
    if len(target_datetime) > 10:
        target_date = target_datetime.split(' ')[0]
    else:
        target_date = target_datetime
    
    # Use default APIs if not specified
    if apis_to_try is None:
        apis_to_try = config.get('search_settings.default_apis', ['nasa', 'sentinel'])
    
    print(f"\n🛰️  Searching for imagery closest to: {target_datetime}")
    print(f"📍 Location: {latitude}, {longitude}")
    
    results = []
    
    # Try NASA GIBS (free, no auth needed)
    if 'nasa' in apis_to_try:
        print("\n--- Trying NASA GIBS ---")
        nasa_client = TimeSpecificSatelliteImagery(config)
        
        # Get date search configuration
        date_search_config = config.get('nasa_gibs.date_search', {})
        max_days_before = date_search_config.get('max_days_before', 7)
        max_days_after = date_search_config.get('max_days_after', 7)
        
        # Try exact date first, then nearby dates
        dates_to_try = [target_date]
        
        # Add nearby dates
        target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        for days in range(1, max_days_before + 1):
            dates_to_try.append((target_dt - timedelta(days=days)).strftime('%Y-%m-%d'))
        for days in range(1, max_days_after + 1):
            dates_to_try.append((target_dt + timedelta(days=days)).strftime('%Y-%m-%d'))
        
        for try_date in dates_to_try:
            try:
                image, date_used = nasa_client.get_nasa_image_by_date(
                    latitude, longitude, try_date
                )
                if image:
                    results.append((image, date_used, 'NASA_VIIRS'))
                    print(f"✅ Found NASA image for {date_used}")
                    break
            except Exception as e:
                print(f"NASA error for {try_date}: {e}")
                continue
    
    # Try Sentinel Hub if credentials provided
    if 'sentinel' in apis_to_try:
        print("\n--- Trying Sentinel Hub ---")
        sentinel_creds = config.get('api_credentials.sentinel_hub', {})
        if sentinel_creds.get('client_id') != "YOUR_SENTINEL_HUB_CLIENT_ID":
            try:
                sentinel_client = SentinelHubTimeSpecific(config)
                image, date_used = sentinel_client.get_image_exact_date(latitude, longitude, target_date)
                if image:
                    results.append((image, date_used, 'Sentinel-2'))
                    print(f"✅ Found Sentinel image for {date_used}")
            except Exception as e:
                print(f"Sentinel error: {e}")
        else:
            print("⚠️  Sentinel Hub credentials not configured")
    
    # Try Planet Labs if API key provided
    if 'planet' in apis_to_try:
        print("\n--- Trying Planet Labs ---")
        planet_creds = config.get('api_credentials.planet_labs', {})
        if planet_creds.get('api_key') != "YOUR_PLANET_LABS_API_KEY":
            try:
                planet_client = PlanetLabsImagery(config)
                images = planet_client.search_images_by_date(latitude, longitude, target_date)
                if images:
                    print(f"✅ Found {len(images)} Planet Labs images")
                    # Note: Planet Labs requires additional steps to download images
                    results.append((None, target_date, 'Planet_Labs'))
            except Exception as e:
                print(f"Planet Labs error: {e}")
        else:
            print("⚠️  Planet Labs API key not configured")
    
    return results

# Example usage
def main():
    # Load configuration
    config = ConfigManager("multi_image_api_config.yaml")
    
    # Get example coordinates from config
    example_coords = config.get('example_data.coordinates.times_square_nyc', {})
    latitude = example_coords.get('latitude', 40.7589)
    longitude = example_coords.get('longitude', -73.9851)
    target_datetime = "2024-07-15"  # or "2024-07-15 14:30:00" for specific time
    
    print("🛰️ Time-Specific Satellite Image Search")
    print("=" * 50)
    
    # Find best available images
    results = find_best_image_for_time(latitude, longitude, target_datetime, config)
    
    if results:
        print(f"\n🎉 Found {len(results)} image(s):")
        
        # Initialize image processor
        processor = ImageProcessor(config)
        
        for idx, (image, date_used, source) in enumerate(results):
            if image:  # Skip None images (like Planet Labs search results)
                filename = processor.save_image(image, source, latitude, longitude, date_used)
                print(f"  {idx+1}. {source} - {date_used} -> {filename}")
        
        print(f"\n📁 Images saved! Check the output directory.")
        
    else:
        print("\n❌ No images found. Try:")
        print("  1. Different date range")
        print("  2. Configure Sentinel Hub credentials in config file")
        print("  3. Configure Planet Labs API key in config file")

if __name__ == "__main__":
    main()