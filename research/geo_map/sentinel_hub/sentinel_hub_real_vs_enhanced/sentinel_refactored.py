#!/usr/bin/env python3
"""
Refactored Sentinel Hub Image Types Comparison Tool
Separates configuration from functional logic and adds timestamped outputs
"""

import requests
from PIL import Image, ImageDraw, ImageFont
import io
import yaml
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List

class ConfigManager:
    """Manages configuration loading and validation"""
    
    def __init__(self, config_path: str = "sentinel_config.yaml"):
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
    
    def get_output_filename(self, template_key: str, **kwargs) -> str:
        """Generate timestamped filename based on template"""
        template = self.config['output']['file_naming'][template_key]
        filename = template.format(timestamp=self.timestamp, **kwargs)
        return os.path.join(self.output_dir, filename)

class SentinelHubAPI:
    """Sentinel Hub API client with configuration management"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.client_id = config.get('api_credentials.sentinel_hub.client_id')
        self.client_secret = config.get('api_credentials.sentinel_hub.client_secret')
        self.base_url = config.get('api_credentials.sentinel_hub.base_url')
        self.token = None
        self.evalscripts = config.get('evalscripts', {})
        self.default_settings = config.get('default_settings', {})
        
        if self.client_id and self.client_secret:
            self.authenticate()
    
    def authenticate(self):
        """Get OAuth2 token"""
        auth_url = f"{self.base_url}/oauth/token"
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            response = requests.post(auth_url, data=auth_data, 
                                   timeout=self.default_settings.get('timeout_seconds', 60))
            if response.status_code == 200:
                self.token = response.json()['access_token']
                print("✅ Sentinel Hub authentication successful")
            else:
                print(f"❌ Authentication failed: {response.text}")
                self.token = None
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            self.token = None
    
    def get_image_by_type(self, lat: float, lon: float, date: str, image_type: str = "true_color", 
                         **kwargs) -> Tuple[Optional[Image.Image], Dict[str, Any]]:
        """
        Get different types of satellite images
        
        Args:
            lat, lon: Coordinates
            date: Date in YYYY-MM-DD format
            image_type: 'true_color', 'false_color', 'ndvi', 'enhanced_true_color'
        """
        
        if not self.token:
            print("❌ No authentication token available")
            return None, {}
        
        # Get evalscript from configuration
        if image_type not in self.evalscripts:
            print(f"❌ Unknown image type: {image_type}")
            return None, {}
        
        evalscript_config = self.evalscripts[image_type]
        evalscript = evalscript_config['script']
        
        # Merge default settings with provided kwargs
        settings = {**self.default_settings, **kwargs}
        
        bbox_size = settings.get('bbox_size', 0.01)
        bbox = [
            lon - bbox_size/2, lat - bbox_size/2,
            lon + bbox_size/2, lat + bbox_size/2
        ]
        
        payload = {
            "input": {
                "bounds": {
                    "bbox": bbox,
                    "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}
                },
                "data": [{
                    "type": "sentinel-2-l2a",
                    "dataFilter": {
                        "timeRange": {
                            "from": f"{date}T00:00:00Z",
                            "to": f"{date}T23:59:59Z"
                        }
                    }
                }]
            },
            "output": {
                "width": settings.get('width', 1024),
                "height": settings.get('height', 1024),
                "responses": [{
                    "identifier": "default",
                    "format": {"type": "image/png"}
                }]
            },
            "evalscript": evalscript
        }
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/v1/process", 
                                   headers=headers, json=payload,
                                   timeout=settings.get('timeout_seconds', 60))
            
            if response.status_code == 200:
                image = Image.open(io.BytesIO(response.content))
                print(f"✅ SUCCESS: Got {image.size} {image_type} image from Sentinel Hub")
                
                # Extract metadata
                metadata = self._extract_metadata(lat, lon, date, image_type, settings, image, response, evalscript_config)
                return image, metadata
            else:
                print(f"❌ Error getting {image_type}: {response.text}")
                return None, {}
        except Exception as e:
            print(f"❌ Exception getting {image_type}: {e}")
            return None, {}
    
    def _extract_metadata(self, lat: float, lon: float, date: str, image_type: str, 
                         settings: dict, image: Image.Image, response, evalscript_config: dict) -> Dict[str, Any]:
        """Extract metadata from Sentinel Hub response"""
        metadata = {
            "api_source": "Sentinel Hub",
            "image_type": image_type,
            "image_type_info": {
                "name": evalscript_config.get('name', image_type),
                "description": evalscript_config.get('description', ''),
                "output_description": evalscript_config.get('output_description', '')
            },
            "coordinates": {
                "latitude": lat,
                "longitude": lon,
                "bbox_size": settings.get('bbox_size', 0.01)
            },
            "temporal_info": {
                "date": date,
                "time_range": f"{date}T00:00:00Z to {date}T23:59:59Z"
            },
            "image_properties": {
                "actual_size": image.size,
                "format": image.format,
                "mode": image.mode,
                "file_size_bytes": len(response.content)
            },
            "request_settings": settings,
            "request_details": {
                "url": f"{self.base_url}/api/v1/process",
                "response_status": response.status_code,
                "content_type": response.headers.get('content-type'),
                "server": response.headers.get('server')
            },
            "acquisition_info": {
                "satellite": "Sentinel-2 L2A",
                "sensor": "MultiSpectral Instrument (MSI)",
                "resolution": "10-20 meters",
                "coverage": "Global"
            },
            "processing_info": {
                "requested_at": datetime.now().isoformat(),
                "coordinate_system": "EPSG:4326 (WGS84)",
                "evalscript_version": "3"
            }
        }
        
        return metadata

class ImageComparisonManager:
    """Main manager class for image comparison and output management"""
    
    def __init__(self, config_path: str = "sentinel_config.yaml"):
        self.config = ConfigManager(config_path)
        self.sentinel_api = SentinelHubAPI(self.config)
    
    def save_image_and_metadata(self, image: Image.Image, metadata: Dict[str, Any], 
                               image_type: str, lat: float, lon: float) -> Tuple[str, str]:
        """Save image and metadata with timestamped filenames"""
        # Generate filenames
        image_path = self.config.get_output_filename('image_template', 
                                                    image_type=image_type, lat=lat, lon=lon)
        metadata_path = self.config.get_output_filename('metadata_template', 
                                                       image_type=image_type, lat=lat, lon=lon)
        
        # Save image
        image.save(image_path, format=self.config.get('processing.image_quality.save_format', 'PNG'))
        print(f"💾 Image saved: {image_path}")
        
        # Save metadata
        if self.config.get('output.save_metadata', True):
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=self.config.get('output.metadata_indent', 2))
            print(f"📄 Metadata saved: {metadata_path}")
        
        return image_path, metadata_path
    
    def create_comparison_image(self, images: Dict[str, Image.Image], lat: float, lon: float) -> str:
        """Create a comparison image showing all image types side by side"""
        if not images:
            return ""
        
        # Calculate grid layout
        num_images = len(images)
        cols = min(2, num_images)
        rows = (num_images + cols - 1) // cols
        
        # Get image size (assume all images are same size)
        first_image = next(iter(images.values()))
        img_width, img_height = first_image.size
        
        # Create comparison image
        comparison_width = img_width * cols
        comparison_height = img_height * rows
        comparison_img = Image.new('RGB', (comparison_width, comparison_height), 'white')
        
        # Add images to comparison
        for i, (image_type, image) in enumerate(images.items()):
            row = i // cols
            col = i % cols
            x = col * img_width
            y = row * img_height
            
            comparison_img.paste(image, (x, y))
            
            # Add label
            draw = ImageDraw.Draw(comparison_img)
            try:
                # Try to use a default font
                font = ImageFont.load_default()
            except:
                font = None
            
            label = self.config.get(f'evalscripts.{image_type}.name', image_type)
            text_bbox = draw.textbbox((0, 0), label, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Draw background for text
            draw.rectangle([x, y, x + text_width + 10, y + text_height + 10], 
                          fill='black', outline='white')
            
            # Draw text
            draw.text((x + 5, y + 5), label, fill='white', font=font)
        
        # Save comparison image
        comparison_path = self.config.get_output_filename('comparison_template', lat=lat, lon=lon)
        comparison_img.save(comparison_path, format=self.config.get('processing.image_quality.save_format', 'PNG'))
        print(f"🖼️  Comparison image saved: {comparison_path}")
        
        return comparison_path
    
    def compare_image_types(self, lat: float = None, lon: float = None, date: str = None) -> Dict[str, Any]:
        """Compare different image types for the same location"""
        
        # Use default coordinates if not provided
        if lat is None:
            lat = self.config.get('default_coordinates.latitude')
        if lon is None:
            lon = self.config.get('default_coordinates.longitude')
        if date is None:
            date = self.config.get('default_coordinates.date')
        
        print(f"🛰️ SENTINEL HUB IMAGE TYPES COMPARISON")
        print(f"📍 Location: {lat}, {lon}")
        print(f"📅 Date: {date}")
        print(f"📁 Output folder: {self.config.output_dir}")
        print("=" * 60)
        
        results = {}
        all_metadata = {}
        successful_images = {}
        
        # Get all available image types
        image_types = list(self.config.get('evalscripts', {}).keys())
        
        for image_type in image_types:
            print(f"\n🔄 Processing {image_type.upper()}...")
            
            try:
                image, metadata = self.sentinel_api.get_image_by_type(lat, lon, date, image_type)
                
                if image:
                    # Save image and metadata
                    image_path, metadata_path = self.save_image_and_metadata(image, metadata, image_type, lat, lon)
                    
                    results[image_type] = {
                        'image_path': image_path,
                        'metadata_path': metadata_path,
                        'image': image,
                        'metadata': metadata
                    }
                    all_metadata[image_type] = metadata
                    successful_images[image_type] = image
                    
                    # Print description
                    description = self.config.get(f'evalscripts.{image_type}.output_description', '')
                    if description:
                        print(f"   📝 {description}")
                else:
                    print(f"   ❌ Failed to retrieve {image_type} image")
                    
            except Exception as e:
                print(f"   ❌ Error processing {image_type}: {e}")
                if not self.config.get('processing.error_handling.continue_on_failure', True):
                    break
        
        # Create comparison image if we have multiple successful images
        if len(successful_images) > 1:
            print(f"\n🖼️  Creating comparison image...")
            comparison_path = self.create_comparison_image(successful_images, lat, lon)
            results['comparison'] = {'comparison_path': comparison_path}
        
        # Save combined metadata
        if all_metadata:
            combined_metadata = {
                "session_info": {
                    "timestamp": self.config.timestamp,
                    "output_directory": self.config.output_dir,
                    "total_image_types": len(image_types),
                    "successful_types": list(all_metadata.keys()),
                    "coordinates": {"latitude": lat, "longitude": lon},
                    "date": date,
                    "generated_at": datetime.now().isoformat(),
                    **self.config.get('metadata.custom_fields', {})
                },
                "image_metadata": all_metadata
            }
            
            combined_path = self.config.get_output_filename('combined_metadata_template', lat=lat, lon=lon)
            with open(combined_path, 'w') as f:
                json.dump(combined_metadata, f, indent=self.config.get('output.metadata_indent', 2))
            print(f"\n📊 Combined metadata saved: {combined_path}")
        
        # Print summary
        print(f"\n📋 SUMMARY:")
        print(f"   🕒 Session timestamp: {self.config.timestamp}")
        print(f"   📁 Output folder: {self.config.output_dir}")
        print(f"   ✅ Successful image types: {list(all_metadata.keys())}")
        print(f"   📊 Total images generated: {len(all_metadata)}")
        
        for image_type, meta in all_metadata.items():
            size = meta.get('image_properties', {}).get('actual_size', 'Unknown')
            name = meta.get('image_type_info', {}).get('name', image_type)
            print(f"      - {name}: {size}")
        
        return results
    
    def get_single_image(self, image_type: str = "true_color", lat: float = None, 
                        lon: float = None, date: str = None) -> Tuple[Optional[Image.Image], Dict[str, Any]]:
        """Get single image of specified type"""
        
        # Use default coordinates if not provided
        if lat is None:
            lat = self.config.get('default_coordinates.latitude')
        if lon is None:
            lon = self.config.get('default_coordinates.longitude')
        if date is None:
            date = self.config.get('default_coordinates.date')
        
        print(f"🛰️ Getting {image_type} image for {lat}, {lon} on {date}")
        
        image, metadata = self.sentinel_api.get_image_by_type(lat, lon, date, image_type)
        
        if image:
            image_path, metadata_path = self.save_image_and_metadata(image, metadata, image_type, lat, lon)
            
            # Print key info
            print(f"\n📊 IMAGE METADATA:")
            print(f"   Type: {metadata.get('image_type_info', {}).get('name', image_type)}")
            print(f"   Description: {metadata.get('image_type_info', {}).get('description', 'N/A')}")
            print(f"   Size: {metadata.get('image_properties', {}).get('actual_size', 'Unknown')}")
            print(f"   File Size: {metadata.get('image_properties', {}).get('file_size_bytes', 0):,} bytes")
            print(f"   Output folder: {self.config.output_dir}")
            
            return image, metadata
        
        print("❌ Failed to retrieve image")
        return None, {}

def main():
    """Main function with timestamped outputs"""
    
    print("🛰️ SENTINEL HUB IMAGE TYPES COMPARISON TOOL")
    print("=" * 65)
    
    # Initialize manager
    manager = ImageComparisonManager()
    
    # Check if credentials are available
    if not manager.sentinel_api.token:
        print("⚠️  No valid Sentinel Hub credentials found in config file")
        print("   Please update sentinel_config.yaml with your credentials")
        print("   The tool will show the structure but cannot fetch real images")
        
        # Show configuration structure
        print(f"\n📋 CONFIGURATION STRUCTURE:")
        print(f"   📁 Output directory: {manager.config.output_dir}")
        print(f"   🕒 Session timestamp: {manager.config.timestamp}")
        print(f"   📊 Available image types: {list(manager.config.get('evalscripts', {}).keys())}")
        
        # Create sample metadata files to show structure
        sample_metadata = {
            "session_info": {
                "timestamp": manager.config.timestamp,
                "output_directory": manager.config.output_dir,
                "status": "DEMO_MODE_NO_CREDENTIALS",
                "message": "This is a demo run without valid credentials"
            },
            "available_image_types": manager.config.get('evalscripts', {})
        }
        
        demo_path = manager.config.get_output_filename('combined_metadata_template', lat=14.382015, lon=79.523023)
        with open(demo_path, 'w') as f:
            json.dump(sample_metadata, f, indent=2)
        print(f"   📄 Demo metadata saved: {demo_path}")
        
        return
    
    # Get coordinates from config
    location = manager.config.get('example_locations.data_legos', {})
    lat = location.get('latitude', manager.config.get('default_coordinates.latitude'))
    lon = location.get('longitude', manager.config.get('default_coordinates.longitude'))
    date = manager.config.get('default_coordinates.date')
    
    # Compare all image types
    results = manager.compare_image_types(lat, lon, date)
    
    if results:
        print(f"\n🎉 SUCCESS! Generated {len(results)} image types with timestamped outputs!")
        print(f"📁 Check the output folder: {manager.config.output_dir}")
    else:
        print(f"\n❌ No images were successfully generated.")
        print(f"   Check your credentials and internet connection.")

if __name__ == "__main__":
    main()
