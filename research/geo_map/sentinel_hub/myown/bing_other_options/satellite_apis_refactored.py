#!/usr/bin/env python3
"""
Refactored Satellite API Tool with Configuration Management
Separates configuration from functional logic and adds timestamped outputs
"""

import requests
from PIL import Image
import io
from datetime import datetime, timedelta
import json
import os
import yaml
import math
from typing import Dict, Any, Optional, Tuple, List

class ConfigManager:
    """Manages configuration loading and validation"""
    
    def __init__(self, config_path: str = "satellite_api_config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.timestamp = datetime.now().strftime(self.config['output']['timestamp_format'])
        self.output_dir = self._create_output_directory()
    
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
    
    def _create_output_directory(self) -> str:
        """Create timestamped output directory"""
        base_dir = self.config['output']['base_directory']
        
        if self.config['output']['create_timestamped_folders']:
            output_dir = os.path.join(base_dir, self.timestamp)
        else:
            output_dir = base_dir
        
        os.makedirs(output_dir, exist_ok=True)
        print(f"📁 Output directory created: {output_dir}")
        return output_dir
    
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
    
    def get_output_filename(self, template_key: str, api_name: str, lat: float, lon: float) -> str:
        """Generate timestamped filename based on template"""
        template = self.config['output']['file_naming'][template_key]
        filename = template.format(
            api_name=api_name,
            lat=lat,
            lon=lon,
            timestamp=self.timestamp
        )
        return os.path.join(self.output_dir, filename)

class GoogleSatelliteAPI:
    """Google Static Maps API for satellite imagery"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.api_key = config.get('api_credentials.google.api_key')
        self.base_url = config.get('api_credentials.google.base_url')
        self.default_settings = config.get('default_settings.google', {})
    
    def get_satellite_image(self, lat: float, lon: float, **kwargs) -> Tuple[Optional[Image.Image], Dict[str, Any]]:
        """Get satellite image from Google Static Maps API"""
        # Merge default settings with provided kwargs
        settings = {**self.default_settings, **kwargs}
        
        params = {
            'center': f"{lat},{lon}",
            'zoom': settings.get('zoom', 18),
            'size': settings.get('size', '640x640'),
            'maptype': settings.get('maptype', 'satellite'),
            'key': self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params, 
                                  timeout=self.config.get('processing.timeout_seconds', 30))
            print(f"Google API Status: {response.status_code}")
            
            if response.status_code == 200:
                image = Image.open(io.BytesIO(response.content))
                print(f"✅ SUCCESS: Got {image.size} satellite image from Google")
                
                metadata = self._extract_metadata(lat, lon, settings, image, response)
                return image, metadata
            else:
                print(f"❌ Google Error: {response.text}")
                return None, {}
        except Exception as e:
            print(f"❌ Google Exception: {e}")
            return None, {}
    
    def _extract_metadata(self, lat: float, lon: float, settings: dict, image: Image.Image, response) -> Dict[str, Any]:
        """Extract metadata from Google API response"""
        metadata = {
            "api_source": "Google Static Maps",
            "coordinates": {"latitude": lat, "longitude": lon},
            "image_properties": {
                "actual_size": image.size,
                "format": image.format,
                "mode": image.mode,
                "file_size_bytes": len(response.content)
            },
            "request_settings": settings,
            "request_details": {
                "url": self.base_url,
                "response_status": response.status_code,
                "content_type": response.headers.get('content-type'),
                "server": response.headers.get('server')
            },
            "acquisition_info": {
                "capture_date": "Recent (Google imagery)",
                "satellite": "Various (Google composite)",
                "resolution": "High resolution (sub-meter to 1 meter)",
                "coverage": "Global"
            },
            "processing_info": {
                "requested_at": datetime.now().isoformat(),
                "coordinate_system": "WGS84",
                "api_version": "Static Maps API v1"
            }
        }
        return metadata

class MapboxSatelliteAPI:
    """Mapbox Satellite API for satellite imagery"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.access_token = config.get('api_credentials.mapbox.access_token')
        self.base_url = config.get('api_credentials.mapbox.base_url')
        self.default_settings = config.get('default_settings.mapbox', {})
    
    def get_satellite_image(self, lat: float, lon: float, **kwargs) -> Tuple[Optional[Image.Image], Dict[str, Any]]:
        """Get satellite image from Mapbox API"""
        settings = {**self.default_settings, **kwargs}
        
        zoom = settings.get('zoom', 15)
        width = settings.get('width', 512)
        height = settings.get('height', 512)
        retina = "@2x" if settings.get('high_res', True) else ""
        
        url = f"{self.base_url}/{lon},{lat},{zoom}/{width}x{height}{retina}"
        params = {'access_token': self.access_token}
        
        try:
            response = requests.get(url, params=params,
                                  timeout=self.config.get('processing.timeout_seconds', 30))
            print(f"Mapbox API Status: {response.status_code}")
            
            if response.status_code == 200:
                image = Image.open(io.BytesIO(response.content))
                print(f"✅ SUCCESS: Got {image.size} satellite image from Mapbox")
                
                metadata = self._extract_metadata(lat, lon, settings, image, response)
                return image, metadata
            else:
                print(f"❌ Mapbox Error: {response.text}")
                return None, {}
        except Exception as e:
            print(f"❌ Mapbox Exception: {e}")
            return None, {}
    
    def _extract_metadata(self, lat: float, lon: float, settings: dict, image: Image.Image, response) -> Dict[str, Any]:
        """Extract metadata from Mapbox API response"""
        metadata = {
            "api_source": "Mapbox Satellite",
            "coordinates": {"latitude": lat, "longitude": lon},
            "image_properties": {
                "actual_size": image.size,
                "format": image.format,
                "mode": image.mode,
                "file_size_bytes": len(response.content)
            },
            "request_settings": settings,
            "request_details": {
                "url": response.url,
                "response_status": response.status_code,
                "content_type": response.headers.get('content-type'),
                "server": response.headers.get('server')
            },
            "acquisition_info": {
                "capture_date": "Recent (Mapbox imagery)",
                "satellite": "Various (Mapbox composite)",
                "resolution": "High resolution (sub-meter to 1 meter)",
                "coverage": "Global"
            },
            "processing_info": {
                "requested_at": datetime.now().isoformat(),
                "coordinate_system": "WGS84",
                "api_version": "Mapbox Static API v1"
            }
        }
        return metadata

class BingSatelliteAPI:
    """Bing Maps API for satellite imagery"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.api_key = config.get('api_credentials.bing.api_key')
        self.base_url = config.get('api_credentials.bing.base_url')
        self.default_settings = config.get('default_settings.bing', {})
    
    def get_satellite_image(self, lat: float, lon: float, **kwargs) -> Tuple[Optional[Image.Image], Dict[str, Any]]:
        """Get satellite image from Bing Maps API"""
        settings = {**self.default_settings, **kwargs}
        
        url = f"{self.base_url}/{lat},{lon}/{settings.get('zoom', 18)}"
        params = {
            'mapSize': f"{settings.get('width', 512)},{settings.get('height', 512)}",
            'key': self.api_key,
            'format': settings.get('format', 'png')
        }
        
        try:
            response = requests.get(url, params=params,
                                  timeout=self.config.get('processing.timeout_seconds', 30))
            print(f"Bing API Status: {response.status_code}")
            
            if response.status_code == 200:
                image = Image.open(io.BytesIO(response.content))
                print(f"✅ SUCCESS: Got {image.size} satellite image from Bing")
                
                metadata = self._extract_metadata(lat, lon, settings, image, response)
                return image, metadata
            else:
                print(f"❌ Bing Error: {response.text}")
                return None, {}
        except Exception as e:
            print(f"❌ Bing Exception: {e}")
            return None, {}
    
    def _extract_metadata(self, lat: float, lon: float, settings: dict, image: Image.Image, response) -> Dict[str, Any]:
        """Extract metadata from Bing API response"""
        metadata = {
            "api_source": "Bing Maps",
            "coordinates": {"latitude": lat, "longitude": lon},
            "image_properties": {
                "actual_size": image.size,
                "format": image.format,
                "mode": image.mode,
                "file_size_bytes": len(response.content)
            },
            "request_settings": settings,
            "request_details": {
                "url": response.url,
                "response_status": response.status_code,
                "content_type": response.headers.get('content-type'),
                "server": response.headers.get('server')
            },
            "acquisition_info": {
                "capture_date": "Recent (Bing imagery)",
                "satellite": "Various (Bing composite)",
                "resolution": "High resolution (sub-meter to 1 meter)",
                "coverage": "Global"
            },
            "processing_info": {
                "requested_at": datetime.now().isoformat(),
                "coordinate_system": "WGS84",
                "api_version": "Bing Maps REST API"
            }
        }
        return metadata

class ESRIWorldImagery:
    """ESRI World Imagery API (Free)"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.base_url = config.get('api_credentials.esri.base_url')
        self.info_url = config.get('api_credentials.esri.info_url')
        self.default_settings = config.get('default_settings.esri', {})
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get service information and metadata"""
        try:
            response = requests.get(f"{self.info_url}?f=json")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error getting service info: {e}")
        return {}
    
    def get_satellite_image(self, lat: float, lon: float, **kwargs) -> Tuple[Optional[Image.Image], Dict[str, Any]]:
        """Get satellite image from ESRI World Imagery"""
        settings = {**self.default_settings, **kwargs}
        
        width = settings.get('width', 1024)
        height = settings.get('height', 1024)
        buffer = settings.get('buffer', 0.005)
        
        bbox = f"{lon-buffer},{lat-buffer},{lon+buffer},{lat+buffer}"
        
        params = {
            'bbox': bbox,
            'bboxSR': settings.get('coordinate_system', '4326'),
            'size': f"{width},{height}",
            'imageSR': settings.get('coordinate_system', '4326'),
            'format': settings.get('format', 'png'),
            'pixelType': 'U8',
            'noDataInterpretation': 'esriNoDataMatchAny',
            'interpolation': settings.get('interpolation', '+RSP_BilinearInterpolation'),
            'f': 'image'
        }
        
        try:
            response = requests.get(self.base_url, params=params,
                                  timeout=self.config.get('processing.timeout_seconds', 30))
            print(f"ESRI API Status: {response.status_code}")
            
            if response.status_code == 200 and 'image' in response.headers.get('content-type', ''):
                image = Image.open(io.BytesIO(response.content))
                print(f"✅ SUCCESS: Got {image.size} satellite image from ESRI")
                
                metadata = self._extract_metadata(lat, lon, settings, buffer, image, response)
                return image, metadata
            else:
                print(f"❌ ESRI Error: {response.headers.get('content-type', 'Unknown error')}")
                return None, {}
        except Exception as e:
            print(f"❌ ESRI Exception: {e}")
            return None, {}
    
    def _extract_metadata(self, lat: float, lon: float, settings: dict, buffer: float, image: Image.Image, response) -> Dict[str, Any]:
        """Extract metadata from ESRI response"""
        metadata = {
            "api_source": "ESRI World Imagery",
            "coordinates": {
                "latitude": lat,
                "longitude": lon,
                "bbox": f"{lon-buffer},{lat-buffer},{lon+buffer},{lat+buffer}"
            },
            "image_properties": {
                "actual_size": image.size,
                "format": image.format,
                "mode": image.mode,
                "file_size_bytes": len(response.content)
            },
            "request_settings": settings,
            "request_details": {
                "url": self.base_url,
                "response_status": response.status_code,
                "content_type": response.headers.get('content-type'),
                "server": response.headers.get('server'),
                "cache_control": response.headers.get('cache-control')
            },
            "acquisition_info": {
                "capture_date": "Unknown (ESRI composite imagery)",
                "satellite": "ESRI World Imagery Composite",
                "resolution": "Varies by location (typically 1-3 meters)",
                "coverage": "Global"
            },
            "processing_info": {
                "requested_at": datetime.now().isoformat(),
                "buffer_distance_degrees": buffer,
                "coordinate_system": f"EPSG:{settings.get('coordinate_system', '4326')}",
                "interpolation": settings.get('interpolation', 'Bilinear')
            }
        }
        
        # Try to get service information
        if self.config.get('metadata.include_service_info', True):
            service_info = self.get_service_info()
            if service_info:
                metadata["service_info"] = {
                    "name": service_info.get("name", "Unknown"),
                    "description": service_info.get("description", "Unknown"),
                    "copyright": service_info.get("copyrightText", "Unknown"),
                    "spatial_reference": service_info.get("spatialReference", {}),
                    "initial_extent": service_info.get("initialExtent", {}),
                    "full_extent": service_info.get("fullExtent", {})
                }
        
        return metadata

class OpenStreetMapSatellite:
    """OpenStreetMap Tile Server API (Free)"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.servers = config.get('api_credentials.osm.tile_servers', [])
        self.default_settings = config.get('default_settings.osm', {})
    
    def deg2num(self, lat_deg: float, lon_deg: float, zoom: int) -> Tuple[int, int]:
        """Convert lat/lon to tile coordinates"""
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        xtile = int((lon_deg + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return (xtile, ytile)
    
    def get_satellite_image(self, lat: float, lon: float, **kwargs) -> Tuple[Optional[Image.Image], Dict[str, Any]]:
        """Get satellite image from tile servers"""
        settings = {**self.default_settings, **kwargs}
        zoom = settings.get('zoom', 16)
        
        x, y = self.deg2num(lat, lon, zoom)
        
        for i, server in enumerate(self.servers):
            try:
                url = server.format(z=zoom, y=y, x=x)
                headers = {'User-Agent': self.config.get('processing.user_agent', 'Python Satellite Downloader')}
                response = requests.get(url, timeout=settings.get('timeout', 10), headers=headers)
                
                if response.status_code == 200:
                    image = Image.open(io.BytesIO(response.content))
                    print(f"✅ SUCCESS: Got {image.size} image from tile server {i+1}")
                    
                    metadata = self._extract_metadata(lat, lon, settings, zoom, x, y, image, response, server, i+1)
                    return image, metadata
            except Exception as e:
                print(f"Tile server {i+1} failed: {e}")
                continue
        
        return None, {}
    
    def _extract_metadata(self, lat: float, lon: float, settings: dict, zoom: int, tile_x: int, tile_y: int, 
                         image: Image.Image, response, server_url: str, server_num: int) -> Dict[str, Any]:
        """Extract metadata from tile server response"""
        metadata = {
            "api_source": f"OpenStreetMap Tile Server {server_num}",
            "coordinates": {
                "latitude": lat,
                "longitude": lon,
                "zoom_level": zoom,
                "tile_coordinates": {"x": tile_x, "y": tile_y}
            },
            "image_properties": {
                "actual_size": image.size,
                "format": image.format,
                "mode": image.mode,
                "file_size_bytes": len(response.content)
            },
            "request_settings": settings,
            "request_details": {
                "server_url": server_url,
                "response_status": response.status_code,
                "content_type": response.headers.get('content-type'),
                "server": response.headers.get('server'),
                "cache_control": response.headers.get('cache-control')
            },
            "acquisition_info": {
                "capture_date": "Unknown (tile-based imagery)",
                "satellite": "Various (tile server composite)",
                "resolution": f"~{156000 / (2**zoom):.1f} meters per pixel at equator",
                "coverage": "Global"
            },
            "processing_info": {
                "requested_at": datetime.now().isoformat(),
                "zoom_level": zoom,
                "tile_size": "256x256 pixels (standard)",
                "coordinate_system": "Web Mercator (EPSG:3857)"
            }
        }
        
        return metadata

class SatelliteImageManager:
    """Main manager class for satellite image retrieval"""
    
    def __init__(self, config_path: str = "satellite_api_config.yaml"):
        self.config = ConfigManager(config_path)
        self.apis = self._initialize_apis()
    
    def _initialize_apis(self) -> Dict[str, Any]:
        """Initialize all API clients"""
        apis = {
            'google': GoogleSatelliteAPI(self.config),
            'mapbox': MapboxSatelliteAPI(self.config),
            'bing': BingSatelliteAPI(self.config),
            'esri': ESRIWorldImagery(self.config),
            'osm': OpenStreetMapSatellite(self.config)
        }
        return apis
    
    def get_image_from_api(self, api_name: str, lat: float, lon: float, **kwargs) -> Tuple[Optional[Image.Image], Dict[str, Any]]:
        """Get image from specific API"""
        if api_name not in self.apis:
            print(f"❌ Unknown API: {api_name}")
            return None, {}
        
        return self.apis[api_name].get_satellite_image(lat, lon, **kwargs)
    
    def save_image_and_metadata(self, api_name: str, image: Image.Image, metadata: Dict[str, Any], 
                               lat: float, lon: float) -> Tuple[str, str]:
        """Save image and metadata with timestamped filenames"""
        # Generate filenames
        image_path = self.config.get_output_filename('image_template', api_name, lat, lon)
        metadata_path = self.config.get_output_filename('metadata_template', api_name, lat, lon)
        
        # Save image
        image.save(image_path, format=self.config.get('processing.image_quality.save_format', 'PNG'))
        print(f"💾 Image saved: {image_path}")
        
        # Save metadata
        if self.config.get('output.save_metadata', True):
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=self.config.get('output.metadata_indent', 2))
            print(f"📄 Metadata saved: {metadata_path}")
        
        return image_path, metadata_path
    
    def test_all_apis(self, lat: float, lon: float) -> Dict[str, Any]:
        """Test all available APIs"""
        print("🧪 TESTING ALL SATELLITE APIs WITH TIMESTAMPED OUTPUTS")
        print("=" * 60)
        
        results = {}
        all_metadata = {}
        
        # Get API priority lists
        free_apis = self.config.get('api_priority.free_apis', ['esri', 'osm'])
        premium_apis = self.config.get('api_priority.premium_apis', ['google', 'mapbox', 'bing'])
        
        # Test free APIs first
        for api_name in free_apis:
            print(f"\n🆓 Testing {api_name.upper()} (FREE)...")
            try:
                image, metadata = self.get_image_from_api(api_name, lat, lon)
                if image:
                    image_path, metadata_path = self.save_image_and_metadata(api_name, image, metadata, lat, lon)
                    results[api_name] = {'image': image_path, 'metadata': metadata_path}
                    all_metadata[api_name] = metadata
            except Exception as e:
                print(f"   ❌ {api_name.upper()} failed: {e}")
        
        # Instructions for premium APIs
        print(f"\n💰 PREMIUM APIs (require API keys):")
        for api_name in premium_apis:
            print(f"   🔑 {api_name.upper()}: API key required")
        
        # Save combined metadata
        if all_metadata:
            combined_metadata = {
                "session_info": {
                    "timestamp": self.config.timestamp,
                    "output_directory": self.config.output_dir,
                    "total_apis_tested": len(all_metadata),
                    "successful_apis": list(all_metadata.keys()),
                    "coordinates": {"latitude": lat, "longitude": lon},
                    "generated_at": datetime.now().isoformat(),
                    **self.config.get('metadata.custom_fields', {})
                },
                "api_metadata": all_metadata
            }
            
            combined_path = self.config.get_output_filename('combined_metadata_template', 'all', lat, lon)
            with open(combined_path, 'w') as f:
                json.dump(combined_metadata, f, indent=self.config.get('output.metadata_indent', 2))
            print(f"\n📊 Combined metadata saved: {combined_path}")
            
            # Print summary
            print(f"\n📋 SUMMARY:")
            print(f"   🕒 Session timestamp: {self.config.timestamp}")
            print(f"   📁 Output folder: {self.config.output_dir}")
            print(f"   ✅ Successful APIs: {list(all_metadata.keys())}")
            for api, meta in all_metadata.items():
                size = meta.get('image_properties', {}).get('actual_size', 'Unknown')
                print(f"      - {api.upper()}: {size}")
        
        return results
    
    def get_single_image(self, lat: float = None, lon: float = None, api_name: str = 'esri') -> Tuple[Optional[Image.Image], Dict[str, Any]]:
        """Get single image using specified API or default coordinates"""
        # Use default coordinates if not provided
        if lat is None:
            lat = self.config.get('default_coordinates.latitude')
        if lon is None:
            lon = self.config.get('default_coordinates.longitude')
        
        print(f"🛰️ Getting satellite image for {lat}, {lon} using {api_name.upper()}")
        
        image, metadata = self.get_image_from_api(api_name, lat, lon)
        
        if image:
            image_path, metadata_path = self.save_image_and_metadata(api_name, image, metadata, lat, lon)
            
            # Print key info
            print(f"\n📊 IMAGE METADATA:")
            print(f"   API Source: {metadata.get('api_source', 'Unknown')}")
            print(f"   Resolution: {metadata.get('acquisition_info', {}).get('resolution', 'Unknown')}")
            print(f"   File Size: {metadata.get('image_properties', {}).get('file_size_bytes', 0):,} bytes")
            print(f"   Output folder: {self.config.output_dir}")
            
            return image, metadata
        
        print("❌ Failed to retrieve image")
        return None, {}

def main():
    """Main function with timestamped outputs"""
    
    print("🛰️ SATELLITE IMAGE DOWNLOADER WITH CONFIGURATION & TIMESTAMPS")
    print("=" * 65)
    
    # Initialize manager
    manager = SatelliteImageManager()
    
    # Get coordinates from config
    location = manager.config.get('example_locations.data_legos', {})
    lat = location.get('latitude', manager.config.get('default_coordinates.latitude'))
    lon = location.get('longitude', manager.config.get('default_coordinates.longitude'))
    
    print(f"📍 Using coordinates: {lat}, {lon}")
    print(f"📁 Output folder: {manager.config.output_dir}")
    
    # Test single image first
    print(f"\n🎯 Getting single image using most reliable API...")
    image, metadata = manager.get_single_image(lat, lon, 'esri')
    
    if image:
        print(f"✅ Single image retrieved successfully!")
        
        # Test all APIs
        print(f"\n🔍 Testing all available APIs...")
        results = manager.test_all_apis(lat, lon)
        
        if results:
            print(f"\n🎉 SUCCESS! Retrieved {len(results)} images with timestamped outputs!")
        else:
            print(f"\n⚠️  Only single image was successful.")
    else:
        print(f"\n❌ Failed to retrieve any images.")
        print(f"   Check API credentials and internet connection.")

if __name__ == "__main__":
    main()
