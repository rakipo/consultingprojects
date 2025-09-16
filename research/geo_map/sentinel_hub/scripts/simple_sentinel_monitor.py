#!/usr/bin/env python3
"""
Simplified Sentinel Hub Land Monitoring System
Combines OAuth authentication with improved functionality
"""

import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple, Optional
import json
import base64
from PIL import Image
import io
import warnings
import yaml
import os
import argparse
import sys
warnings.filterwarnings('ignore')

class SimpleSentinelHubMonitor:
    def __init__(self, client_id: str, client_secret: str, config_path: str = "sentinel_hub_user_config.yaml"):
        """Initialize Sentinel Hub monitoring system with OAuth authentication"""
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.base_url = "https://services.sentinel-hub.com"
        
        # Load user configuration
        self.user_config = self._load_user_config(config_path)
        
        # Get coordinates from user config
        self.coordinates = self.user_config['coordinates']
        
        # Calculate center point
        lons = [coord[0] for coord in self.coordinates]
        lats = [coord[1] for coord in self.coordinates]
        self.center_lat = sum(lats) / len(lats)
        self.center_lon = sum(lons) / len(lons)
        
        # Authenticate
        self._authenticate()
    
    def _load_user_config(self, config_path: str) -> Dict:
        """Load user configuration from YAML file"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"User configuration file not found: {config_path}")
        
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        
        return config
    
    def _authenticate(self):
        """Authenticate with Sentinel Hub and get access token"""
        auth_url = f"{self.base_url}/oauth/token"
        
        payload = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            print(f"📡 Authenticating with Sentinel Hub...")
            response = requests.post(auth_url, data=payload)
            response.raise_for_status()
            auth_data = response.json()
            self.access_token = auth_data['access_token']
            print("✅ Successfully authenticated with Sentinel Hub")
        except Exception as e:
            print(f"❌ Authentication failed: {str(e)}")
            raise
    
    def _get_headers(self):
        """Get headers with authorization token"""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def _create_bbox(self, buffer_meters: int = 100) -> List[float]:
        """Create bounding box around the coordinates"""
        buffer_deg = buffer_meters / 111000  # rough conversion
        
        lons = [coord[0] for coord in self.coordinates]
        lats = [coord[1] for coord in self.coordinates]
        
        min_lon = min(lons) - buffer_deg
        max_lon = max(lons) + buffer_deg
        min_lat = min(lats) - buffer_deg
        max_lat = max(lats) + buffer_deg
        
        return [min_lon, min_lat, max_lon, max_lat]
    
    def get_sentinel2_data(self, start_date: str, end_date: str, 
                          max_cloud_coverage: float = 20) -> Optional[np.ndarray]:
        """Get Sentinel-2 data for the specified date range"""
        
        bbox = self._create_bbox()
        
        # Evalscript for getting bands and calculating indices
        evalscript = """
        //VERSION=3
        function setup() {
            return {
                input: ["B02", "B03", "B04", "B08", "B11", "B12", "SCL"],
                output: { bands: 7 }
            };
        }
        
        function evaluatePixel(sample) {
            // Skip clouds and cloud shadows
            if (sample.SCL == 3 || sample.SCL == 8 || sample.SCL == 9 || sample.SCL == 10) {
                return [0, 0, 0, 0, 0, 0, 0];
            }
            
            // Calculate NDVI
            let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
            
            // Calculate NDBI
            let ndbi = (sample.B11 - sample.B08) / (sample.B11 + sample.B08);
            
            // Calculate MNDWI
            let mndwi = (sample.B03 - sample.B11) / (sample.B03 + sample.B11);
            
            return [
                sample.B04/3000,  // Red (normalized)
                sample.B03/3000,  // Green (normalized)
                sample.B02/3000,  // Blue (normalized)
                sample.B08/3000,  // NIR (normalized)
                ndvi,
                ndbi,
                mndwi
            ];
        }
        """
        
        request_payload = {
            "input": {
                "bounds": {
                    "bbox": bbox
                },
                "data": [
                    {
                        "type": "sentinel-2-l2a",
                        "dataFilter": {
                            "timeRange": {
                                "from": f"{start_date}T00:00:00Z",
                                "to": f"{end_date}T23:59:59Z"
                            },
                            "maxCloudCoverage": max_cloud_coverage
                        }
                    }
                ]
            },
            "output": {
                "width": 256,
                "height": 256,
                "responses": [
                    {
                        "identifier": "default",
                        "format": {
                            "type": "image/tiff"
                        }
                    }
                ]
            },
            "evalscript": evalscript
        }
        
        try:
            print(f"📡 Requesting data for {start_date} to {end_date}...")
            response = requests.post(
                f"{self.base_url}/api/v1/process",
                headers=self._get_headers(),
                json=request_payload
            )
            
            response.raise_for_status()
            
            # Save the raw TIFF data to a temporary file
            temp_file = f"temp_image_{start_date}_{end_date}.tiff"
            with open(temp_file, 'wb') as f:
                f.write(response.content)
            
            # Use tifffile to read multi-band TIFF
            try:
                import tifffile
                image_array = tifffile.imread(temp_file)
                
                # Clean up temporary file
                os.remove(temp_file)
                
                # Handle different array shapes
                if len(image_array.shape) == 3:
                    # Multi-band image (height, width, bands)
                    return image_array
                elif len(image_array.shape) == 2:
                    # Single band image (height, width)
                    return image_array.reshape(image_array.shape[0], image_array.shape[1], 1)
                else:
                    print(f"❌ Unexpected image shape: {image_array.shape}")
                    return None
                    
            except ImportError:
                # Fallback to PIL if tifffile is not available
                print("⚠️  tifffile not available, trying PIL fallback...")
                image = Image.open(temp_file)
                image_array = np.array(image)
                os.remove(temp_file)
                
                if len(image_array.shape) == 3:
                    return image_array
                else:
                    return image_array.reshape(image_array.shape[0], image_array.shape[1], 1)
                
        except Exception as e:
            print(f"❌ Error retrieving data: {str(e)}")
            # Clean up temp file if it exists
            temp_file = f"temp_image_{start_date}_{end_date}.tiff"
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return None
    
    def calculate_statistics(self, image_data: np.ndarray) -> Dict:
        """Calculate statistics from image data"""
        if image_data is None:
            return {}
        
        # Calculate statistics for each band
        stats = {}
        
        # RGB bands (0-2)
        if image_data.shape[2] >= 3:
            stats['red_mean'] = np.mean(image_data[:, :, 0])
            stats['green_mean'] = np.mean(image_data[:, :, 1])
            stats['blue_mean'] = np.mean(image_data[:, :, 2])
        
        # NIR band (3)
        if image_data.shape[2] >= 4:
            stats['nir_mean'] = np.mean(image_data[:, :, 3])
        
        # NDVI band (4)
        if image_data.shape[2] >= 5:
            stats['ndvi_mean'] = np.mean(image_data[:, :, 4])
            stats['ndvi_std'] = np.std(image_data[:, :, 4])
        
        # NDBI band (5)
        if image_data.shape[2] >= 6:
            stats['ndbi_mean'] = np.mean(image_data[:, :, 5])
            stats['ndbi_std'] = np.std(image_data[:, :, 5])
        
        # MNDWI band (6)
        if image_data.shape[2] >= 7:
            stats['mndwi_mean'] = np.mean(image_data[:, :, 6])
            stats['mndwi_std'] = np.std(image_data[:, :, 6])
        
        return stats
    
    def detect_changes(self, before_date: str, after_date: str, 
                      change_threshold: float = 0.2) -> Dict:
        """Detect changes between two dates"""
        print(f"🔍 Analyzing changes from {before_date} to {after_date}...")
        
        # Get data for both periods
        before_start = (datetime.strptime(before_date, '%Y-%m-%d') - timedelta(days=15)).strftime('%Y-%m-%d')
        before_end = (datetime.strptime(before_date, '%Y-%m-%d') + timedelta(days=15)).strftime('%Y-%m-%d')
        
        after_start = (datetime.strptime(after_date, '%Y-%m-%d') - timedelta(days=15)).strftime('%Y-%m-%d')
        after_end = (datetime.strptime(after_date, '%Y-%m-%d') + timedelta(days=15)).strftime('%Y-%m-%d')
        
        before_data = self.get_sentinel2_data(before_start, before_end)
        after_data = self.get_sentinel2_data(after_start, after_end)
        
        if before_data is None or after_data is None:
            return {
                "error": "Failed to retrieve imagery for one or both time periods",
                "date_comparison": f"{before_date} to {after_date}"
            }
        
        # Calculate statistics
        before_stats = self.calculate_statistics(before_data)
        after_stats = self.calculate_statistics(after_data)
        
        if not before_stats or not after_stats:
            return {
                "error": "Failed to calculate statistics",
                "date_comparison": f"{before_date} to {after_date}"
            }
        
        # Calculate changes
        changes = {
            "date_comparison": f"{before_date} to {after_date}",
            "before_period": f"{before_start} to {before_end}",
            "after_period": f"{after_start} to {after_end}",
            "vegetation_change": {
                "before_ndvi": before_stats.get('ndvi_mean', 0),
                "after_ndvi": after_stats.get('ndvi_mean', 0),
                "ndvi_difference": after_stats.get('ndvi_mean', 0) - before_stats.get('ndvi_mean', 0),
                "interpretation": self._interpret_vegetation_change(
                    after_stats.get('ndvi_mean', 0) - before_stats.get('ndvi_mean', 0)
                )
            },
            "buildup_change": {
                "before_ndbi": before_stats.get('ndbi_mean', 0),
                "after_ndbi": after_stats.get('ndbi_mean', 0),
                "ndbi_difference": after_stats.get('ndbi_mean', 0) - before_stats.get('ndbi_mean', 0),
                "interpretation": self._interpret_buildup_change(
                    after_stats.get('ndbi_mean', 0) - before_stats.get('ndbi_mean', 0)
                )
            },
            "water_change": {
                "before_mndwi": before_stats.get('mndwi_mean', 0),
                "after_mndwi": after_stats.get('mndwi_mean', 0),
                "mndwi_difference": after_stats.get('mndwi_mean', 0) - before_stats.get('mndwi_mean', 0),
                "interpretation": self._interpret_water_change(
                    after_stats.get('mndwi_mean', 0) - before_stats.get('mndwi_mean', 0)
                )
            }
        }
        
        # Determine if changes are significant
        significant_change = (
            abs(changes['vegetation_change']['ndvi_difference']) > change_threshold or
            abs(changes['buildup_change']['ndbi_difference']) > change_threshold or
            abs(changes['water_change']['mndwi_difference']) > change_threshold
        )
        
        changes['significant_change'] = significant_change
        changes['change_summary'] = self._generate_change_summary(changes)
        
        return changes
    
    def _interpret_vegetation_change(self, change: float) -> str:
        """Interpret vegetation change values"""
        if change > 0.15:
            return "Major vegetation increase"
        elif change > 0.05:
            return "Moderate vegetation growth"
        elif change < -0.15:
            return "Major vegetation loss"
        elif change < -0.05:
            return "Moderate vegetation decline"
        else:
            return "No significant vegetation change"
    
    def _interpret_buildup_change(self, change: float) -> str:
        """Interpret built-up area change values"""
        if change > 0.1:
            return "Significant construction/development"
        elif change > 0.03:
            return "Minor built-up area increase"
        elif change < -0.03:
            return "Possible demolition or clearing"
        else:
            return "No significant built-up change"
    
    def _interpret_water_change(self, change: float) -> str:
        """Interpret water change values"""
        if change > 0.1:
            return "Water body appearance or expansion"
        elif change < -0.1:
            return "Water body reduction or drying"
        else:
            return "No significant water change"
    
    def _generate_change_summary(self, changes: Dict) -> str:
        """Generate human-readable change summary"""
        summary_parts = []
        
        veg_interp = changes['vegetation_change']['interpretation']
        if "No significant" not in veg_interp:
            summary_parts.append(f"Vegetation: {veg_interp}")
        
        build_interp = changes['buildup_change']['interpretation']
        if "No significant" not in build_interp:
            summary_parts.append(f"Built-up: {build_interp}")
        
        water_interp = changes['water_change']['interpretation']
        if "No significant" not in water_interp:
            summary_parts.append(f"Water: {water_interp}")
        
        if not summary_parts:
            return "No significant changes detected"
        
        return "; ".join(summary_parts)
    
    def generate_visual_comparison(self, before_date: str, after_date: str):
        """Generate visual comparison of before/after images"""
        print(f"🗺️  Generating visual comparison for {before_date} vs {after_date}")
        
        # Get imagery
        before_start = (datetime.strptime(before_date, '%Y-%m-%d') - timedelta(days=15)).strftime('%Y-%m-%d')
        before_end = (datetime.strptime(before_date, '%Y-%m-%d') + timedelta(days=15)).strftime('%Y-%m-%d')
        
        after_start = (datetime.strptime(after_date, '%Y-%m-%d') - timedelta(days=15)).strftime('%Y-%m-%d')
        after_end = (datetime.strptime(after_date, '%Y-%m-%d') + timedelta(days=15)).strftime('%Y-%m-%d')
        
        before_image = self.get_sentinel2_data(before_start, before_end)
        after_image = self.get_sentinel2_data(after_start, after_end)
        
        if before_image is None or after_image is None:
            print("❌ Failed to retrieve imagery for visualization")
            return
        
        # Create visualization
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle(f'Land Change Analysis: {before_date} vs {after_date}', fontsize=16)
        
        # RGB images
        if before_image.shape[2] >= 3:
            axes[0, 0].imshow(before_image[:, :, :3])
            axes[0, 0].set_title(f'RGB Before ({before_date})')
            axes[0, 0].axis('off')
            
            axes[1, 0].imshow(after_image[:, :, :3])
            axes[1, 0].set_title(f'RGB After ({after_date})')
            axes[1, 0].axis('off')
        
        # NDVI images
        if before_image.shape[2] >= 5:
            im1 = axes[0, 1].imshow(before_image[:, :, 4], cmap='RdYlGn', vmin=-1, vmax=1)
            axes[0, 1].set_title(f'NDVI Before ({before_date})')
            axes[0, 1].axis('off')
            plt.colorbar(im1, ax=axes[0, 1], fraction=0.046)
            
            im2 = axes[1, 1].imshow(after_image[:, :, 4], cmap='RdYlGn', vmin=-1, vmax=1)
            axes[1, 1].set_title(f'NDVI After ({after_date})')
            axes[1, 1].axis('off')
            plt.colorbar(im2, ax=axes[1, 1], fraction=0.046)
        
        # NDBI images
        if before_image.shape[2] >= 6:
            im3 = axes[0, 2].imshow(before_image[:, :, 5], cmap='RdBu_r', vmin=-1, vmax=1)
            axes[0, 2].set_title(f'NDBI Before ({before_date})')
            axes[0, 2].axis('off')
            plt.colorbar(im3, ax=axes[0, 2], fraction=0.046)
            
            im4 = axes[1, 2].imshow(after_image[:, :, 5], cmap='RdBu_r', vmin=-1, vmax=1)
            axes[1, 2].set_title(f'NDBI After ({after_date})')
            axes[1, 2].axis('off')
            plt.colorbar(im4, ax=axes[1, 2], fraction=0.046)
        
        plt.tight_layout()
        plt.savefig(f'land_change_comparison_{before_date}_to_{after_date}.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"✅ Visual comparison saved as 'land_change_comparison_{before_date}_to_{after_date}.png'")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Simple Sentinel Hub Land Monitoring System')
    
    parser.add_argument('--client-id', required=True, help='Sentinel Hub Client ID')
    parser.add_argument('--client-secret', required=True, help='Sentinel Hub Client Secret')
    parser.add_argument('--config', default='sentinel_hub_user_config.yaml', help='User config file path')
    parser.add_argument('--before-date', default='2023-01-01', help='Before date (YYYY-MM-DD)')
    parser.add_argument('--after-date', default='2024-01-01', help='After date (YYYY-MM-DD)')
    parser.add_argument('--mode', choices=['detect', 'visual', 'both'], default='detect', help='Operation mode')
    parser.add_argument('--threshold', type=float, default=0.2, help='Change detection threshold')
    
    return parser.parse_args()

def main():
    """Main function"""
    args = parse_arguments()
    
    try:
        # Initialize monitor
        print("🛰️  Initializing Simple Sentinel Hub Monitor...")
        monitor = SimpleSentinelHubMonitor(args.client_id, args.client_secret, args.config)
        
        if args.mode in ['detect', 'both']:
            print("\n📊 Change Detection Analysis")
            changes = monitor.detect_changes(args.before_date, args.after_date, args.threshold)
            
            if 'error' not in changes:
                print("🔍 CHANGE DETECTION RESULTS:")
                print(f"Summary: {changes['change_summary']}")
                print(f"Significant Change: {'YES' if changes['significant_change'] else 'NO'}")
                print(json.dumps(changes, indent=2))
            else:
                print(f"❌ Error: {changes['error']}")
        
        if args.mode in ['visual', 'both']:
            print("\n🗺️  Visual Comparison")
            monitor.generate_visual_comparison(args.before_date, args.after_date)
        
        print("\n✅ Operations completed!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
