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

    def download_image(self, item_id: str, item_type: str = "PSScene", 
                      asset_type: str = "visual") -> Optional[Image.Image]:
        """
        Download actual image data for a Planet Labs item using the correct API approach
        
        Args:
            item_id (str): Planet Labs item ID
            item_type (str): Item type (default: PSScene)
            asset_type (str): Asset type to download (default: visual)
        
        Returns:
            PIL Image or None if download fails
        """
        
        try:
            headers = {'Authorization': f'api-key {self.api_key}'}
            
            # Step 1: Get assets for the item
            assets_url = f"{self.base_url}/data/v1/item-types/{item_type}/items/{item_id}/assets"
            
            print(f"🔍 Getting assets for item {item_id}...")
            assets_response = requests.get(assets_url, headers=headers)
            
            if assets_response.status_code != 200:
                print(f"❌ Failed to get assets: {assets_response.status_code}")
                return None
            
            assets = assets_response.json()
            
            # Check if any assets are available
            if not assets:
                print(f"❌ No assets available for item {item_id}")
                print(f"   This may be due to subscription limitations or access restrictions")
                
                # Create a placeholder image with Planet Labs metadata
                placeholder_config = self.config.get('error_handling.fallback_images', {})
                placeholder_size = placeholder_config.get('placeholder_size', [512, 512])
                placeholder_color = 'lightblue'  # Use light blue for Planet Labs
                
                placeholder_img = Image.new('RGB', tuple(placeholder_size), color=placeholder_color)
                
                # Add text to indicate this is a Planet Labs placeholder
                try:
                    from PIL import ImageDraw, ImageFont
                    draw = ImageDraw.Draw(placeholder_img)
                    
                    try:
                        font = ImageFont.load_default()
                    except:
                        font = None
                    
                    text = f"Planet Labs\nItem: {item_id}\nNo assets available\n(subscription required)"
                    
                    if font:
                        bbox = draw.textbbox((0, 0), text, font=font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                        
                        x = (placeholder_size[0] - text_width) // 2
                        y = (placeholder_size[1] - text_height) // 2
                        
                        draw.text((x, y), text, fill='darkblue', font=font)
                    else:
                        draw.text((50, 250), text, fill='darkblue')
                        
                except Exception as e:
                    print(f"Could not add text to placeholder: {e}")
                
                print(f"✅ Created Planet Labs placeholder image for {item_id}")
                return placeholder_img
            
            # Check if the desired asset type exists
            if asset_type not in assets:
                print(f"❌ Asset type '{asset_type}' not available for item {item_id}")
                available_assets = list(assets.keys())
                print(f"   Available assets: {available_assets}")
                
                # Try alternative asset types
                alternatives = ['visual', 'basic_analytic', 'analytic', 'ortho_visual']
                for alt_asset in alternatives:
                    if alt_asset in assets:
                        asset_type = alt_asset
                        print(f"✅ Using alternative asset type: {asset_type}")
                        break
                else:
                    print(f"❌ No suitable asset types found among: {available_assets}")
                    return None
            
            asset = assets[asset_type]
            
            # Step 2: Check if asset needs activation
            if asset['status'] == 'inactive':
                print(f"🔄 Activating asset {asset_type}...")
                
                # Get activation URL
                activation_url = asset['_links']['activate']
                activation_response = requests.post(activation_url, headers=headers)
                
                if activation_response.status_code not in [200, 202, 204]:
                    print(f"❌ Failed to activate asset: {activation_response.status_code}")
                    return None
                
                # Wait for activation (simplified - just check a few times)
                import time
                max_retries = 10
                retry_delay = 2
                
                for retry in range(max_retries):
                    time.sleep(retry_delay)
                    
                    # Check asset status
                    assets_response = requests.get(assets_url, headers=headers)
                    if assets_response.status_code == 200:
                        updated_assets = assets_response.json()
                        if asset_type in updated_assets:
                            asset = updated_assets[asset_type]
                            if asset['status'] == 'active':
                                print(f"✅ Asset activated successfully")
                                break
                    
                    print(f"⏳ Waiting for activation... (attempt {retry + 1}/{max_retries})")
                else:
                    print(f"⚠️  Asset activation timeout, proceeding anyway...")
            
            # Step 3: Download the asset
            if 'location' in asset:
                download_url = asset['location']
                print(f"📥 Downloading image from {download_url[:50]}...")
                
                download_response = requests.get(download_url, headers=headers)
                
                if download_response.status_code == 200:
                    # Try to open as image
                    try:
                        image = Image.open(io.BytesIO(download_response.content))
                        print(f"✅ Successfully downloaded Planet Labs image")
                        return image
                    except Exception as e:
                        print(f"❌ Failed to parse downloaded image: {e}")
                        return None
                else:
                    print(f"❌ Failed to download image: {download_response.status_code}")
                    return None
            else:
                print(f"❌ No download location available for asset")
                return None
            
        except Exception as e:
            self.logger.error(f"Planet image download error: {e}")
            print(f"❌ Planet image download error: {e}")
            return None

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
                            config: ConfigManager, apis_to_try: List[str] = None, 
                            images_per_api: int = 3) -> List[Tuple[Image.Image, str, str]]:
    """
    Find multiple satellite images for a specific date/time (3 per API by default)
    
    Args:
        latitude (float): Latitude coordinate
        longitude (float): Longitude coordinate  
        target_datetime (str): Target date/time 'YYYY-MM-DD HH:MM:SS' or 'YYYY-MM-DD'
        config (ConfigManager): Configuration manager instance
        apis_to_try (list): APIs to try in order
        images_per_api (int): Number of images to retrieve per API (default: 3)
    
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
    
    print(f"\n🛰️  Searching for {images_per_api} images per API closest to: {target_datetime}")
    print(f"📍 Location: {latitude}, {longitude}")
    
    results = []
    
    # Try NASA GIBS (free, no auth needed)
    if 'nasa' in apis_to_try:
        print(f"\n--- Trying NASA GIBS (target: {images_per_api} images) ---")
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
        
        nasa_images_found = 0
        used_dates = set()  # Track used dates to avoid duplicates
        
        for try_date in dates_to_try:
            if nasa_images_found >= images_per_api:
                break
                
            try:
                image, date_used = nasa_client.get_nasa_image_by_date(
                    latitude, longitude, try_date
                )
                if image and date_used not in used_dates:
                    results.append((image, date_used, 'NASA_VIIRS'))
                    used_dates.add(date_used)
                    nasa_images_found += 1
                    print(f"✅ Found NASA image {nasa_images_found}/{images_per_api} for {date_used}")
            except Exception as e:
                print(f"NASA error for {try_date}: {e}")
                continue
        
        if nasa_images_found == 0:
            print(f"❌ No NASA images found after trying {len(dates_to_try)} dates")
        else:
            print(f"🎉 Found {nasa_images_found} NASA images")
    
    # Try Sentinel Hub if credentials provided
    if 'sentinel' in apis_to_try:
        print(f"\n--- Trying Sentinel Hub (target: {images_per_api} images) ---")
        sentinel_creds = config.get('api_credentials.sentinel_hub', {})
        if sentinel_creds.get('client_id') != "YOUR_SENTINEL_HUB_CLIENT_ID":
            sentinel_client = SentinelHubTimeSpecific(config)
            sentinel_images_found = 0
            used_dates = set()
            
            # Try multiple dates for Sentinel Hub
            target_dt = datetime.strptime(target_date, '%Y-%m-%d')
            dates_to_try = [target_date]
            
            # Add nearby dates for Sentinel Hub
            for days in range(1, 8):  # Try up to 7 days before and after
                dates_to_try.append((target_dt - timedelta(days=days)).strftime('%Y-%m-%d'))
                dates_to_try.append((target_dt + timedelta(days=days)).strftime('%Y-%m-%d'))
            
            for try_date in dates_to_try:
                if sentinel_images_found >= images_per_api:
                    break
                    
                try:
                    image, date_used = sentinel_client.get_image_exact_date(latitude, longitude, try_date)
                    if image and date_used not in used_dates:
                        results.append((image, date_used, 'Sentinel-2'))
                        used_dates.add(date_used)
                        sentinel_images_found += 1
                        print(f"✅ Found Sentinel image {sentinel_images_found}/{images_per_api} for {date_used}")
                except Exception as e:
                    print(f"Sentinel error for {try_date}: {e}")
                    continue
            
            if sentinel_images_found == 0:
                print(f"❌ No Sentinel images found after trying {len(dates_to_try)} dates")
            else:
                print(f"🎉 Found {sentinel_images_found} Sentinel images")
        else:
            print("⚠️  Sentinel Hub credentials not configured")
    
    # Try Planet Labs if API key provided
    if 'planet' in apis_to_try:
        print(f"\n--- Trying Planet Labs (target: {images_per_api} images) ---")
        planet_creds = config.get('api_credentials.planet_labs', {})
        if planet_creds.get('api_key') != "YOUR_PLANET_LABS_API_KEY":
            try:
                planet_client = PlanetLabsImagery(config)
                images = planet_client.search_images_by_date(latitude, longitude, target_date)
                if images:
                    planet_images_found = min(len(images), images_per_api)
                    print(f"✅ Found {len(images)} Planet Labs images, downloading {planet_images_found}")
                    
                    for i in range(planet_images_found):
                        if i < len(images):
                            item = images[i]
                            item_id = item.get('id', f'unknown_{i}')
                            acquired_date = item.get('properties', {}).get('acquired', target_date)
                            
                            # Download the actual image
                            image = planet_client.download_image(item_id)
                            if image:
                                results.append((image, acquired_date, f'Planet_Labs_{i+1}'))
                                print(f"✅ Downloaded Planet Labs image {i+1}/{planet_images_found}")
                            else:
                                print(f"❌ Failed to download Planet Labs image {i+1}")
                else:
                    print("❌ No Planet Labs images found")
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
    
    # Find multiple images per API (configurable number)
    images_per_api = config.get('search_settings.images_per_api', 3)
    results = find_best_image_for_time(latitude, longitude, target_datetime, config, images_per_api=images_per_api)
    
    if results:
        print(f"\n🎉 Found {len(results)} total image(s):")
        
        # Initialize image processor
        processor = ImageProcessor(config)
        
        # Group results by source for better organization
        source_counts = {}
        saved_images = []
        
        for idx, (image, date_used, source) in enumerate(results):
            if image:  # Skip None images (like Planet Labs search results)
                # Create unique filename to avoid overwrites
                unique_source = source
                if source in source_counts:
                    source_counts[source] += 1
                    unique_source = f"{source}_{source_counts[source]}"
                else:
                    source_counts[source] = 1
                
                filename = processor.save_image(image, unique_source, latitude, longitude, date_used)
                saved_images.append((unique_source, date_used, filename))
                print(f"  {idx+1}. {unique_source} - {date_used} -> {filename}")
        
        # Print summary by source
        print(f"\n📊 Summary by API:")
        for source, count in source_counts.items():
            print(f"  {source}: {count} images")
        
        print(f"\n📁 {len(saved_images)} images saved! Check the output directory.")
        
    else:
        print("\n❌ No images found. Try:")
        print("  1. Different date range")
        print("  2. Configure Sentinel Hub credentials in config file")
        print("  3. Configure Planet Labs API key in config file")

if __name__ == "__main__":
    main()