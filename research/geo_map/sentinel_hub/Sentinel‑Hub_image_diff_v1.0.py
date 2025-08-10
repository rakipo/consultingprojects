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
warnings.filterwarnings('ignore')

class SentinelHubLandChangeMonitor:
    def __init__(self, client_id: str, client_secret: str):
        """Initialize Sentinel Hub API client"""
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.base_url = "https://services.sentinel-hub.com"
        
        # Define your land coordinates (updated coordinates)
        self.coordinates = [
            [79.9957724429183, 14.446024455437907],   # West-North
            [79.99587101412848, 14.44600887103552],   # East-North  
            [79.99586363806654, 14.44594718263318],   # East-South
            [79.9957664079881, 14.445960169624453],   # West-South
            [79.9957724429183, 14.446024455437907]    # Close polygon
        ]
        
        # Center point for reference (calculated from new coordinates)
        self.center_lat = 14.445986312535515  # Average of lat coordinates
        self.center_lon = 79.99581901604329   # Average of lon coordinates
        
        # Get access token
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Sentinel Hub and get access token"""
        auth_url = f"{self.base_url}/oauth/token"
        
        payload = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            print(f"📡 Authenticating with: {auth_url}")
            print(f"📡 Auth payload: {{'grant_type': 'client_credentials', 'client_id': '{self.client_id[:8]}...'}}")
            
            response = requests.post(auth_url, data=payload)
            
            print(f"📡 Auth response status: {response.status_code}")
            print(f"📡 Auth response: {response.text}")
            
            response.raise_for_status()
            auth_data = response.json()
            self.access_token = auth_data['access_token']
            print("✅ Successfully authenticated with Sentinel Hub")
            print(f"📡 Token length: {len(self.access_token)} characters")
        except Exception as e:
            print(f"❌ Authentication failed: {str(e)}")
            if 'response' in locals():
                print(f"📡 Auth error response: {response.text}")
            raise
    
    def _get_headers(self):
        """Get headers with authorization token"""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def _create_bbox(self, buffer_meters: int = 100) -> List[float]:
        """Create bounding box around the coordinates"""
        # Convert buffer from meters to degrees (approximate)
        buffer_deg = buffer_meters / 111000  # rough conversion
        
        lons = [coord[0] for coord in self.coordinates[:-1]]  # exclude duplicate last point
        lats = [coord[1] for coord in self.coordinates[:-1]]
        
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
            print(f"📡 Sending request to: {self.base_url}/api/v1/process")
            print(f"📡 Request payload: {json.dumps(request_payload, indent=2)}")
            
            response = requests.post(
                f"{self.base_url}/api/v1/process",
                headers=self._get_headers(),
                json=request_payload
            )
            
            print(f"📡 Response status: {response.status_code}")
            print(f"📡 Response headers: {dict(response.headers)}")
            print(f"📡 Response content length: {len(response.content)} bytes")
            
            # Try to print response as text if it's an error
            if response.status_code != 200:
                try:
                    error_text = response.text
                    print(f"📡 Error response body: {error_text}")
                except:
                    print(f"📡 Could not decode error response")
            
            response.raise_for_status()
            
            # Convert response to numpy array
            try:
                print(f"📡 Attempting to decode image data...")
                image_data = Image.open(io.BytesIO(response.content))
                result = np.array(image_data, dtype=np.float32)
                print(f"📡 Successfully decoded image: shape={result.shape}, dtype={result.dtype}")
                return result
            except Exception as img_error:
                print(f"❌ Image decoding error: {str(img_error)}")
                print(f"📡 Raw response content (first 200 bytes): {response.content[:200]}")
                
                # Try alternative approach - save and reload
                with open('temp_image.tiff', 'wb') as f:
                    f.write(response.content)
                try:
                    image_data = Image.open('temp_image.tiff')
                    result = np.array(image_data, dtype=np.float32)
                    import os
                    os.remove('temp_image.tiff')
                    print(f"📡 Alternative loading successful: shape={result.shape}")
                    return result
                except Exception as e2:
                    print(f"❌ Alternative image loading failed: {str(e2)}")
                    return None
            
        except Exception as e:
            print(f"❌ Error fetching Sentinel-2 data: {str(e)}")
            if 'response' in locals():
                try:
                    print(f"📡 Full error response: {response.text}")
                except:
                    print(f"📡 Could not get error response text")
            return None
    
    def calculate_statistics(self, image_data: np.ndarray) -> Dict:
        """Calculate statistics from image data"""
        if image_data is None:
            print("❌ Image data is None")
            return {}
        
        print(f"📊 Image shape: {image_data.shape}, dtype: {image_data.dtype}")
        
        # Handle different image formats
        if len(image_data.shape) == 2:
            print("❌ Got 2D image, expected 3D with multiple bands")
            return {}
        elif len(image_data.shape) == 3:
            if image_data.shape[2] < 7:
                print(f"❌ Expected 7 bands, got {image_data.shape[2]}")
                return {}
            
            ndvi_band = image_data[:, :, 4]
            ndbi_band = image_data[:, :, 5]
            mndwi_band = image_data[:, :, 6]
            
            print(f"📊 NDVI range: {np.min(ndvi_band):.3f} to {np.max(ndvi_band):.3f}")
            print(f"📊 NDBI range: {np.min(ndbi_band):.3f} to {np.max(ndbi_band):.3f}")
            
            # Filter out invalid values (0 values from cloud masking and extreme values)
            valid_mask = (ndvi_band != 0) & (ndbi_band != 0) & \
                        (ndvi_band >= -1) & (ndvi_band <= 1) & \
                        (ndbi_band >= -1) & (ndbi_band <= 1)
            
            valid_count = np.sum(valid_mask)
            print(f"📊 Valid pixels: {valid_count} / {ndvi_band.size}")
            
            if valid_count > 0:
                ndvi_valid = ndvi_band[valid_mask]
                ndbi_valid = ndbi_band[valid_mask]
                
                return {
                    'ndvi_mean': float(np.mean(ndvi_valid)),
                    'ndvi_std': float(np.std(ndvi_valid)),
                    'ndbi_mean': float(np.mean(ndbi_valid)),
                    'ndbi_std': float(np.std(ndbi_valid)),
                    'valid_pixels': int(valid_count),
                    'total_pixels': int(ndvi_band.size)
                }
        
        print("❌ No valid statistics could be calculated")
        return {}
    
    def detect_changes(self, before_date: str, after_date: str, 
                      change_threshold: float = 0.2) -> Dict:
        """Detect changes between two time periods"""
        
        print(f"🔍 Analyzing changes from {before_date} to {after_date}...")
        
        # Get imagery for both periods (with 15-day buffer)
        before_start = (datetime.strptime(before_date, '%Y-%m-%d') - timedelta(days=15)).strftime('%Y-%m-%d')
        before_end = (datetime.strptime(before_date, '%Y-%m-%d') + timedelta(days=15)).strftime('%Y-%m-%d')
        
        after_start = (datetime.strptime(after_date, '%Y-%m-%d') - timedelta(days=15)).strftime('%Y-%m-%d')
        after_end = (datetime.strptime(after_date, '%Y-%m-%d') + timedelta(days=15)).strftime('%Y-%m-%d')
        
        before_image = self.get_sentinel2_data(before_start, before_end)
        after_image = self.get_sentinel2_data(after_start, after_end)
        
        if before_image is None or after_image is None:
            return {
                'error': 'Failed to retrieve imagery for one or both time periods',
                'date_comparison': f"{before_date} to {after_date}"
            }
        
        # Calculate statistics
        before_stats = self.calculate_statistics(before_image)
        after_stats = self.calculate_statistics(after_image)
        
        if not before_stats or not after_stats:
            return {
                'error': 'Failed to calculate statistics from imagery',
                'date_comparison': f"{before_date} to {after_date}"
            }
        
        # Calculate changes
        ndvi_change = after_stats['ndvi_mean'] - before_stats['ndvi_mean']
        ndbi_change = after_stats['ndbi_mean'] - before_stats['ndbi_mean']
        
        changes_detected = {
            'date_comparison': f"{before_date} to {after_date}",
            'vegetation_change': {
                'mean_ndvi_change': ndvi_change,
                'before_ndvi': before_stats['ndvi_mean'],
                'after_ndvi': after_stats['ndvi_mean'],
                'interpretation': self._interpret_vegetation_change(ndvi_change)
            },
            'buildup_change': {
                'mean_ndbi_change': ndbi_change,
                'before_ndbi': before_stats['ndbi_mean'],
                'after_ndbi': after_stats['ndbi_mean'],
                'interpretation': self._interpret_buildup_change(ndbi_change)
            },
            'data_quality': {
                'before_valid_pixels': before_stats['valid_pixels'],
                'after_valid_pixels': after_stats['valid_pixels'],
                'before_coverage': before_stats['valid_pixels'] / before_stats['total_pixels'] * 100,
                'after_coverage': after_stats['valid_pixels'] / after_stats['total_pixels'] * 100
            },
            'significant_change': abs(ndvi_change) > change_threshold or abs(ndbi_change) > change_threshold
        }
        
        return changes_detected
    
    def _interpret_vegetation_change(self, ndvi_change: float) -> str:
        """Interpret NDVI change values"""
        if ndvi_change > 0.1:
            return "Significant vegetation increase (new planting/growth)"
        elif ndvi_change > 0.05:
            return "Moderate vegetation increase"
        elif ndvi_change < -0.1:
            return "Significant vegetation loss (clearing/construction)"
        elif ndvi_change < -0.05:
            return "Moderate vegetation decrease"
        else:
            return "No significant vegetation change"
    
    def _interpret_buildup_change(self, ndbi_change: float) -> str:
        """Interpret NDBI change values"""
        if ndbi_change > 0.1:
            return "Significant construction/development activity"
        elif ndbi_change > 0.05:
            return "Moderate built-up area increase"
        elif ndbi_change < -0.05:
            return "Possible demolition or area clearing"
        else:
            return "No significant built-up change"
    
    def continuous_monitoring(self, start_date: str, end_date: str, 
                            interval_days: int = 90) -> List[Dict]:
        """Perform continuous monitoring with specified intervals"""
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        results = []
        current_date = start
        
        print(f"📊 Starting continuous monitoring from {start_date} to {end_date}")
        
        while current_date < end:
            next_date = current_date + timedelta(days=interval_days)
            if next_date > end:
                next_date = end
            
            try:
                changes = self.detect_changes(
                    current_date.strftime('%Y-%m-%d'),
                    next_date.strftime('%Y-%m-%d')
                )
                
                if 'error' not in changes:
                    results.append(changes)
                    
                    if changes['significant_change']:
                        print(f"⚠️  SIGNIFICANT CHANGE DETECTED: {changes['date_comparison']}")
                        print(f"   Vegetation: {changes['vegetation_change']['interpretation']}")
                        print(f"   Built-up: {changes['buildup_change']['interpretation']}")
                else:
                    print(f"⚠️  Error processing {current_date} to {next_date}: {changes['error']}")
                
            except Exception as e:
                print(f"❌ Error processing {current_date} to {next_date}: {str(e)}")
            
            current_date = next_date
        
        return results
    
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

# Example usage
def main():
    # You need to get these from Sentinel Hub Dashboard
    # Visit: https://apps.sentinel-hub.com/dashboard/
    CLIENT_ID = "1ecf7748-4066-4ba1-a3df-3ea2517cf7f6"
    CLIENT_SECRET = "lCK9t1qjeD1mKjcmW9sZ1wqMCFwD1RsQ"
    
    if CLIENT_ID == "your_client_id_here" or CLIENT_SECRET == "your_client_secret_here":
        print("❌ Please set your Sentinel Hub credentials!")
        print("1. Visit https://apps.sentinel-hub.com/dashboard/")
        print("2. Create an account and get your Client ID and Secret")
        print("3. Replace the CLIENT_ID and CLIENT_SECRET variables above")
        return
    
    try:
        # Initialize the monitor
        monitor = SentinelHubLandChangeMonitor(CLIENT_ID, CLIENT_SECRET)
        
        # Example 1: Compare two specific dates
        print("🔍 Detecting changes between two dates...")
        changes = monitor.detect_changes('2023-01-01', '2024-01-01')
        print(json.dumps(changes, indent=2))
        
        # Example 2: Continuous monitoring
        print("\n📊 Starting continuous monitoring...")
        results = monitor.continuous_monitoring('2023-11-01', '2025-02-01', interval_days=120)
        
        # Example 3: Generate visual comparison
        print("\n🗺️  Generating visual report...")
        monitor.generate_visual_comparison('2023-06-01', '2024-01-01')
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()