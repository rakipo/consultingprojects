import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import json
import requests
import base64
from PIL import Image
import io
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.image import MimeImage
import warnings
warnings.filterwarnings('ignore')

# Install required packages:
# pip install sentinelhub pandas matplotlib pillow numpy requests

from sentinelhub import (
    SHConfig, 
    BBox, 
    CRS, 
    SentinelHubRequest, 
    DataCollection, 
    MimeType,
    bbox_to_dimensions,
    SentinelHubStatistical,
    Geometry
)

class SentinelHubLandMonitor:
    def __init__(self, instance_id: str, client_id: str, client_secret: str):
        """
        Initialize Sentinel Hub monitoring system
        
        Args:
            instance_id: Your Sentinel Hub instance ID
            client_id: OAuth client ID
            client_secret: OAuth client secret
        """
        # Configure Sentinel Hub
        self.config = SHConfig()
        self.config.instance_id = instance_id
        self.config.sh_client_id = client_id
        self.config.sh_client_secret = client_secret
        
        # Define your land coordinates (adjusted for proper bbox format)
        self.coordinates = [
            [80.033289, 14.446383],  # West-North
            [80.033892, 14.446587],  # East-North  
            [80.033909, 14.446203],  # East-South
            [80.033298, 14.446032],  # West-South
        ]
        
        # Create bounding box (min_x, min_y, max_x, max_y)
        lons = [coord[0] for coord in self.coordinates]
        lats = [coord[1] for coord in self.coordinates]
        
        self.bbox = BBox(
            bbox=[min(lons), min(lats), max(lons), max(lats)], 
            crs=CRS.WGS84
        )
        
        # Calculate image dimensions (higher resolution = more detail)
        self.resolution = 10  # 10m per pixel for Sentinel-2
        self.size = bbox_to_dimensions(self.bbox, resolution=self.resolution)
        
        print(f"Monitoring area: {self.bbox}")
        print(f"Image dimensions: {self.size}")
        
        # Define evaluation scripts for different indices
        self.evalscripts = {
            'true_color': self._get_true_color_evalscript(),
            'ndvi': self._get_ndvi_evalscript(),
            'ndbi': self._get_ndbi_evalscript(),
            'ndwi': self._get_ndwi_evalscript(),
            'change_detection': self._get_change_detection_evalscript()
        }
    
    def _get_true_color_evalscript(self) -> str:
        """Evaluation script for true color RGB imagery"""
        return """
        //VERSION=3
        function setup() {
            return {
                input: ["B02", "B03", "B04", "dataMask"],
                output: { bands: 4 }
            };
        }
        
        function evaluatePixel(sample) {
            return [2.5 * sample.B04, 2.5 * sample.B03, 2.5 * sample.B02, sample.dataMask];
        }
        """
    
    def _get_ndvi_evalscript(self) -> str:
        """Evaluation script for NDVI calculation"""
        return """
        //VERSION=3
        function setup() {
            return {
                input: ["B04", "B08", "dataMask"],
                output: { bands: 2 }
            };
        }
        
        function evaluatePixel(sample) {
            let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
            return [ndvi, sample.dataMask];
        }
        """
    
    def _get_ndbi_evalscript(self) -> str:
        """Evaluation script for NDBI (Built-up areas)"""
        return """
        //VERSION=3
        function setup() {
            return {
                input: ["B08", "B11", "dataMask"],
                output: { bands: 2 }
            };
        }
        
        function evaluatePixel(sample) {
            let ndbi = (sample.B11 - sample.B08) / (sample.B11 + sample.B08);
            return [ndbi, sample.dataMask];
        }
        """
    
    def _get_ndwi_evalscript(self) -> str:
        """Evaluation script for NDWI (Water detection)"""
        return """
        //VERSION=3
        function setup() {
            return {
                input: ["B03", "B08", "dataMask"],
                output: { bands: 2 }
            };
        }
        
        function evaluatePixel(sample) {
            let ndwi = (sample.B03 - sample.B08) / (sample.B03 + sample.B08);
            return [ndwi, sample.dataMask];
        }
        """
    
    def _get_change_detection_evalscript(self) -> str:
        """Multi-temporal evaluation script for change detection"""
        return """
        //VERSION=3
        function setup() {
            return {
                input: [
                    {
                        bands: ["B02", "B03", "B04", "B08", "B11"],
                        units: "DN"
                    }
                ],
                output: { bands: 5 },
                mosaicking: "ORBIT"
            };
        }
        
        function evaluatePixel(samples) {
            // Return the most recent valid sample
            let sample = samples[0];
            
            // Calculate indices
            let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
            let ndbi = (sample.B11 - sample.B08) / (sample.B11 + sample.B08);
            let ndwi = (sample.B03 - sample.B08) / (sample.B03 + sample.B08);
            
            // Brightness index
            let brightness = (sample.B02 + sample.B03 + sample.B04) / 3;
            
            return [ndvi, ndbi, ndwi, brightness/3000, 1];
        }
        """
    
    def get_satellite_image(self, date_range: Tuple[str, str], 
                           evalscript_type: str = 'true_color',
                           max_cloud_coverage: float = 20.0) -> np.ndarray:
        """
        Retrieve satellite imagery for specified date range
        
        Args:
            date_range: Tuple of (start_date, end_date) in 'YYYY-MM-DD' format
            evalscript_type: Type of evaluation script to use
            max_cloud_coverage: Maximum allowed cloud coverage percentage
        
        Returns:
            numpy array of image data
        """
        request = SentinelHubRequest(
            evalscript=self.evalscripts[evalscript_type],
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L2A,
                    time_interval=date_range,
                    maxcc=max_cloud_coverage/100.0,
                    other_args={"dataFilter": {"mosaickingOrder": "mostRecent"}}
                )
            ],
            responses=[
                SentinelHubRequest.output_response('default', MimeType.TIFF)
            ],
            bbox=self.bbox,
            size=self.size,
            config=self.config
        )
        
        try:
            response = request.get_data()
            if response and len(response) > 0:
                return response[0]
            else:
                raise Exception("No data returned from Sentinel Hub")
        except Exception as e:
            print(f"Error retrieving imagery: {str(e)}")
            return None
    
    def calculate_statistics(self, date_range: Tuple[str, str],
                           max_cloud_coverage: float = 20.0) -> Dict:
        """
        Calculate statistical metrics for the area
        """
        # Create geometry for statistical analysis
        geometry = Geometry(
            geometry={
                "type": "Polygon",
                "coordinates": [[
                    [coord[0], coord[1]] for coord in self.coordinates + [self.coordinates[0]]
                ]]
            },
            crs=CRS.WGS84
        )
        
        # Statistical request
        request = SentinelHubStatistical(
            aggregation=SentinelHubStatistical.aggregation(
                evalscript=self.evalscripts['change_detection'],
                time_interval=date_range,
                aggregation_interval='P1D',  # Daily aggregation
                size=self.size
            ),
            input_data=[
                SentinelHubStatistical.input_data(
                    DataCollection.SENTINEL2_L2A,
                    maxcc=max_cloud_coverage/100.0
                )
            ],
            geometry=geometry,
            config=self.config
        )
        
        try:
            response = request.get_data()
            return self._process_statistical_response(response)
        except Exception as e:
            print(f"Error calculating statistics: {str(e)}")
            return {}
    
    def _process_statistical_response(self, response: List) -> Dict:
        """Process statistical response from Sentinel Hub"""
        if not response:
            return {}
        
        # Extract statistics from the response
        stats = {}
        for item in response:
            if 'outputs' in item:
                for output in item['outputs']:
                    if 'bands' in output:
                        bands = output['bands']
                        stats[item['interval']['from']] = {
                            'ndvi_mean': bands.get('B0', {}).get('stats', {}).get('mean', 0),
                            'ndbi_mean': bands.get('B1', {}).get('stats', {}).get('mean', 0),
                            'ndwi_mean': bands.get('B2', {}).get('stats', {}).get('mean', 0),
                            'brightness_mean': bands.get('B3', {}).get('stats', {}).get('mean', 0)
                        }
        
        return stats
    
    def detect_changes(self, before_date_range: Tuple[str, str],
                      after_date_range: Tuple[str, str],
                      change_threshold: float = 0.1) -> Dict:
        """
        Detect changes between two time periods
        
        Args:
            before_date_range: (start, end) dates for before period
            after_date_range: (start, end) dates for after period
            change_threshold: Threshold for significant change detection
        """
        print(f"🔍 Analyzing changes between {before_date_range} and {after_date_range}")
        
        # Get statistics for both periods
        before_stats = self.calculate_statistics(before_date_range)
        after_stats = self.calculate_statistics(after_date_range)
        
        if not before_stats or not after_stats:
            return {"error": "Could not retrieve statistics for comparison"}
        
        # Get the most recent statistics from each period
        before_values = list(before_stats.values())[-1] if before_stats else {}
        after_values = list(after_stats.values())[-1] if after_stats else {}
        
        # Calculate changes
        changes = {
            'before_period': before_date_range,
            'after_period': after_date_range,
            'vegetation_change': {
                'before_ndvi': before_values.get('ndvi_mean', 0),
                'after_ndvi': after_values.get('ndvi_mean', 0),
                'ndvi_difference': after_values.get('ndvi_mean', 0) - before_values.get('ndvi_mean', 0),
                'interpretation': self._interpret_ndvi_change(
                    after_values.get('ndvi_mean', 0) - before_values.get('ndvi_mean', 0)
                )
            },
            'buildup_change': {
                'before_ndbi': before_values.get('ndbi_mean', 0),
                'after_ndbi': after_values.get('ndbi_mean', 0),
                'ndbi_difference': after_values.get('ndbi_mean', 0) - before_values.get('ndbi_mean', 0),
                'interpretation': self._interpret_ndbi_change(
                    after_values.get('ndbi_mean', 0) - before_values.get('ndbi_mean', 0)
                )
            },
            'water_change': {
                'before_ndwi': before_values.get('ndwi_mean', 0),
                'after_ndwi': after_values.get('ndwi_mean', 0),
                'ndwi_difference': after_values.get('ndwi_mean', 0) - before_values.get('ndwi_mean', 0),
                'interpretation': self._interpret_ndwi_change(
                    after_values.get('ndwi_mean', 0) - before_values.get('ndwi_mean', 0)
                )
            }
        }
        
        # Determine if changes are significant
        significant_change = (
            abs(changes['vegetation_change']['ndvi_difference']) > change_threshold or
            abs(changes['buildup_change']['ndbi_difference']) > change_threshold or
            abs(changes['water_change']['ndwi_difference']) > change_threshold
        )
        
        changes['significant_change'] = significant_change
        changes['change_summary'] = self._generate_change_summary(changes)
        
        return changes
    
    def _interpret_ndvi_change(self, change: float) -> str:
        """Interpret NDVI change values"""
        if change > 0.15:
            return "Major vegetation increase (new crops/plantations)"
        elif change > 0.05:
            return "Moderate vegetation growth"
        elif change < -0.15:
            return "Major vegetation loss (clearing/harvesting)"
        elif change < -0.05:
            return "Moderate vegetation decline"
        else:
            return "No significant vegetation change"
    
    def _interpret_ndbi_change(self, change: float) -> str:
        """Interpret NDBI change values"""
        if change > 0.1:
            return "Significant construction/development"
        elif change > 0.03:
            return "Minor built-up area increase"
        elif change < -0.03:
            return "Possible demolition or clearing"
        else:
            return "No significant built-up change"
    
    def _interpret_ndwi_change(self, change: float) -> str:
        """Interpret NDWI change values"""
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
    
    def continuous_monitoring(self, start_date: str, end_date: str,
                             interval_days: int = 30,
                             change_threshold: float = 0.1) -> List[Dict]:
        """
        Perform continuous monitoring with regular intervals
        """
        print(f"🚀 Starting continuous monitoring from {start_date} to {end_date}")
        
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        results = []
        current_date = start
        
        while current_date < end - timedelta(days=interval_days):
            period1_start = current_date
            period1_end = current_date + timedelta(days=15)
            period2_start = current_date + timedelta(days=interval_days)
            period2_end = current_date + timedelta(days=interval_days + 15)
            
            if period2_end > end:
                break
            
            try:
                changes = self.detect_changes(
                    (period1_start.strftime('%Y-%m-%d'), period1_end.strftime('%Y-%m-%d')),
                    (period2_start.strftime('%Y-%m-%d'), period2_end.strftime('%Y-%m-%d')),
                    change_threshold
                )
                
                results.append(changes)
                
                if changes.get('significant_change', False):
                    print(f"⚠️  ALERT: {changes['change_summary']}")
                    self._send_alert(changes)
                else:
                    print(f"✅ No significant changes: {period1_start.strftime('%Y-%m-%d')} to {period2_start.strftime('%Y-%m-%d')}")
                
            except Exception as e:
                print(f"❌ Error processing {current_date}: {str(e)}")
            
            current_date += timedelta(days=interval_days)
        
        return results
    
    def generate_visual_comparison(self, before_date_range: Tuple[str, str],
                                 after_date_range: Tuple[str, str],
                                 save_path: Optional[str] = None) -> None:
        """Generate side-by-side visual comparison"""
        print("🖼️  Generating visual comparison...")
        
        # Get images for both periods
        before_img = self.get_satellite_image(before_date_range, 'true_color')
        after_img = self.get_satellite_image(after_date_range, 'true_color')
        
        if before_img is None or after_img is None:
            print("❌ Could not retrieve images for comparison")
            return
        
        # Create comparison plot
        fig, axes = plt.subplots(1, 2, figsize=(15, 7))
        
        # Before image
        axes[0].imshow(before_img)
        axes[0].set_title(f'Before: {before_date_range[0]} to {before_date_range[1]}', fontsize=12)
        axes[0].axis('off')
        
        # After image
        axes[1].imshow(after_img)
        axes[1].set_title(f'After: {after_date_range[0]} to {after_date_range[1]}', fontsize=12)
        axes[1].axis('off')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📁 Comparison saved to {save_path}")
        
        plt.show()
    
    def _send_alert(self, change_data: Dict):
        """Send email alert for significant changes"""
        # Email configuration - update with your settings
        EMAIL_CONFIG = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'sender_email': 'your_email@gmail.com',
            'sender_password': 'your_app_password',  # Use App Password for Gmail
            'recipient_email': 'recipient@gmail.com'
        }
        
        try:
            msg = MimeMultipart()
            msg['From'] = EMAIL_CONFIG['sender_email']
            msg['To'] = EMAIL_CONFIG['recipient_email']
            msg['Subject'] = f"🚨 Land Change Alert - Significant Changes Detected"
            
            # Create detailed email body
            body = f"""
            Significant changes detected on your monitored land parcel:
            
            📍 Location: {self.bbox}
            📅 Analysis Period: {change_data['before_period']} → {change_data['after_period']}
            
            📊 DETECTED CHANGES:
            {change_data['change_summary']}
            
            📈 DETAILED ANALYSIS:
            
            🌿 Vegetation Changes (NDVI):
            - Before: {change_data['vegetation_change']['before_ndvi']:.4f}
            - After: {change_data['vegetation_change']['after_ndvi']:.4f}
            - Change: {change_data['vegetation_change']['ndvi_difference']:+.4f}
            - Impact: {change_data['vegetation_change']['interpretation']}
            
            🏗️ Built-up Area Changes (NDBI):
            - Before: {change_data['buildup_change']['before_ndbi']:.4f}
            - After: {change_data['buildup_change']['after_ndbi']:.4f}
            - Change: {change_data['buildup_change']['ndbi_difference']:+.4f}
            - Impact: {change_data['buildup_change']['interpretation']}
            
            💧 Water/Moisture Changes (NDWI):
            - Before: {change_data['water_change']['before_ndwi']:.4f}
            - After: {change_data['water_change']['after_ndwi']:.4f}
            - Change: {change_data['water_change']['ndwi_difference']:+.4f}
            - Impact: {change_data['water_change']['interpretation']}
            
            🔗 View your land on Google Maps:
            https://www.google.com/maps/@{(self.bbox[1] + self.bbox[3])/2},{(self.bbox[0] + self.bbox[2])/2},18z
            
            This is an automated alert from your Land Monitoring System.
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
            server.starttls()
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.send_message(msg)
            server.quit()
            
            print("📧 Alert email sent successfully!")
            
        except Exception as e:
            print(f"❌ Failed to send email: {str(e)}")

# Example usage and configuration
def main():
    """
    Main function demonstrating how to use the monitoring system
    """
    # SETUP: Replace with your Sentinel Hub credentials
    INSTANCE_ID = "your-instance-id"  # From Sentinel Hub Dashboard
    CLIENT_ID = "your-client-id"      # OAuth credentials
    CLIENT_SECRET = "your-client-secret"
    
    # Initialize the monitoring system
    print("🛰️  Initializing Sentinel Hub Land Monitor...")
    monitor = SentinelHubLandMonitor(INSTANCE_ID, CLIENT_ID, CLIENT_SECRET)
    
    # Example 1: Simple change detection between two periods
    print("\n📊 Example 1: Change Detection Analysis")
    changes = monitor.detect_changes(
        before_date_range=('2023-01-01', '2023-01-31'),
        after_date_range=('2024-01-01', '2024-01-31'),
        change_threshold=0.05
    )
    
    if 'error' not in changes:
        print("🔍 CHANGE DETECTION RESULTS:")
        print(f"Summary: {changes['change_summary']}")
        print(f"Significant Change: {'YES' if changes['significant_change'] else 'NO'}")
        print(json.dumps(changes, indent=2))
    
    # Example 2: Generate visual comparison
    print("\n🖼️  Example 2: Visual Comparison")
    monitor.generate_visual_comparison(
        before_date_range=('2023-06-01', '2023-06-30'),
        after_date_range=('2024-06-01', '2024-06-30'),
        save_path='land_comparison.png'
    )
    
    # Example 3: Continuous monitoring (run this for ongoing monitoring)
    print("\n🚀 Example 3: Continuous Monitoring Setup")
    # Uncomment the next lines to start continuous monitoring
    # results = monitor.continuous_monitoring(
    #     start_date='2023-01-01',
    #     end_date='2024-12-31',
    #     interval_days=60,  # Check every 60 days
    #     change_threshold=0.05
    # )
    
    print("\n✅ Setup complete! Your land monitoring system is ready.")
    print("\n📋 Next Steps:")
    print("1. Sign up at https://www.sentinel-hub.com/")
    print("2. Get your Instance ID, Client ID, and Client Secret")
    print("3. Update the credentials in this script")
    print("4. Configure email settings for alerts")
    print("5. Set up automated scheduling (cron job, etc.)")

if __name__ == "__main__":
    main()