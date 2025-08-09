import ee
import geemap
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class LandChangeMonitor:
    def __init__(self):
        """Initialize Google Earth Engine and define the area of interest"""
        try:
            ee.Initialize(project='n8n-arxiv')
        except:
            ee.Authenticate()
            ee.Initialize()
        
        # Define your land coordinates
        self.coordinates = [
            [80.033289, 14.446383],  # West-North
            [80.033892, 14.446587],  # East-North  
            [80.033909, 14.446203],  # East-South
            [80.033298, 14.446032],  # West-South
            [80.033289, 14.446383]   # Close polygon
        ]
        
        # Create area of interest (AOI)
        self.aoi = ee.Geometry.Polygon([self.coordinates])
        
        # Center point for reference
        self.center_lat = 14.446308
        self.center_lon = 80.033594
        
    def get_sentinel2_imagery(self, start_date: str, end_date: str) -> ee.ImageCollection:
        """Get Sentinel-2 imagery for the specified date range"""
        return ee.ImageCollection('COPERNICUS/S2_SR') \
            .filterDate(start_date, end_date) \
            .filterBounds(self.aoi) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
            .select(['B2', 'B3', 'B4', 'B8', 'B11', 'B12'])  # Blue, Green, Red, NIR, SWIR1, SWIR2
    
    def get_landsat_imagery(self, start_date: str, end_date: str) -> ee.ImageCollection:
        """Get Landsat 8/9 imagery for the specified date range"""
        return ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
            .filterDate(start_date, end_date) \
            .filterBounds(self.aoi) \
            .filter(ee.Filter.lt('CLOUD_COVER', 20)) \
            .select(['SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6', 'SR_B7'])
    
    def calculate_indices(self, image: ee.Image, sensor: str = 'sentinel2') -> ee.Image:
        """Calculate vegetation and built-up indices"""
        if sensor == 'sentinel2':
            # NDVI (Normalized Difference Vegetation Index)
            ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
            
            # NDBI (Normalized Difference Built-up Index)
            ndbi = image.normalizedDifference(['B11', 'B8']).rename('NDBI')
            
            # MNDWI (Modified Normalized Difference Water Index)
            mndwi = image.normalizedDifference(['B3', 'B11']).rename('MNDWI')
            
        else:  # Landsat
            ndvi = image.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
            ndbi = image.normalizedDifference(['SR_B6', 'SR_B5']).rename('NDBI')
            mndwi = image.normalizedDifference(['SR_B3', 'SR_B6']).rename('MNDWI')
        
        return image.addBands([ndvi, ndbi, mndwi])
    
    def detect_changes(self, before_date: str, after_date: str, 
                      change_threshold: float = 0.2) -> Dict:
        """Detect changes between two time periods"""
        
        # Get imagery for both periods
        before_collection = self.get_sentinel2_imagery(
            (datetime.strptime(before_date, '%Y-%m-%d') - timedelta(days=15)).strftime('%Y-%m-%d'),
            (datetime.strptime(before_date, '%Y-%m-%d') + timedelta(days=15)).strftime('%Y-%m-%d')
        )
        
        after_collection = self.get_sentinel2_imagery(
            (datetime.strptime(after_date, '%Y-%m-%d') - timedelta(days=15)).strftime('%Y-%m-%d'),
            (datetime.strptime(after_date, '%Y-%m-%d') + timedelta(days=15)).strftime('%Y-%m-%d')
        )
        
        # Get median composite images
        before_image = before_collection.median()
        after_image = after_collection.median()
        
        # Calculate indices
        before_with_indices = self.calculate_indices(before_image)
        after_with_indices = self.calculate_indices(after_image)
        
        # Calculate differences
        ndvi_diff = after_with_indices.select('NDVI').subtract(before_with_indices.select('NDVI'))
        ndbi_diff = after_with_indices.select('NDBI').subtract(before_with_indices.select('NDBI'))
        
        # Get statistics for the AOI
        ndvi_stats = ndvi_diff.reduceRegion(
            reducer=ee.Reducer.mean().combine(ee.Reducer.stdDev(), sharedInputs=True),
            geometry=self.aoi,
            scale=10,
            maxPixels=1e9
        ).getInfo()
        
        ndbi_stats = ndbi_diff.reduceRegion(
            reducer=ee.Reducer.mean().combine(ee.Reducer.stdDev(), sharedInputs=True),
            geometry=self.aoi,
            scale=10,
            maxPixels=1e9
        ).getInfo()
        
        # Analyze changes
        changes_detected = {
            'date_comparison': f"{before_date} to {after_date}",
            'vegetation_change': {
                'mean_ndvi_change': ndvi_stats.get('NDVI_mean', 0),
                'stddev_ndvi_change': ndvi_stats.get('NDVI_stdDev', 0),
                'interpretation': self._interpret_vegetation_change(ndvi_stats.get('NDVI_mean', 0))
            },
            'buildup_change': {
                'mean_ndbi_change': ndbi_stats.get('NDBI_mean', 0),
                'stddev_ndbi_change': ndbi_stats.get('NDBI_stdDev', 0),
                'interpretation': self._interpret_buildup_change(ndbi_stats.get('NDBI_mean', 0))
            },
            'significant_change': abs(ndvi_stats.get('NDVI_mean', 0)) > change_threshold or 
                                abs(ndbi_stats.get('NDBI_mean', 0)) > change_threshold
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
        
        while current_date < end:
            next_date = current_date + timedelta(days=interval_days)
            if next_date > end:
                next_date = end
            
            try:
                changes = self.detect_changes(
                    current_date.strftime('%Y-%m-%d'),
                    next_date.strftime('%Y-%m-%d')
                )
                results.append(changes)
                
                if changes['significant_change']:
                    print(f"⚠️  SIGNIFICANT CHANGE DETECTED: {changes['date_comparison']}")
                    # self._send_alert(changes)  # Commented out to avoid email authentication errors
                
            except Exception as e:
                print(f"Error processing {current_date} to {next_date}: {str(e)}")
            
            current_date = next_date
        
        return results
    
    def _send_alert(self, change_data: Dict):
        """Send email alert for significant changes"""
        # Configure your email settings here
        EMAIL_CONFIG = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'sender_email': 'ravikiran.ponduri@gmail.com',
            'sender_password': 'your_app_password',
            'recipient_email': 'recipient@gmail.com'
        }
        
        try:
            msg = MIMEMultipart()
            msg['From'] = EMAIL_CONFIG['sender_email']
            msg['To'] = EMAIL_CONFIG['recipient_email']
            msg['Subject'] = f"Land Change Alert - {change_data['date_comparison']}"
            
            body = f"""
            Significant change detected on your monitored land:
            
            Period: {change_data['date_comparison']}
            
            Vegetation Changes:
            - Mean NDVI Change: {change_data['vegetation_change']['mean_ndvi_change']:.4f}
            - Interpretation: {change_data['vegetation_change']['interpretation']}
            
            Built-up Changes:
            - Mean NDBI Change: {change_data['buildup_change']['mean_ndbi_change']:.4f}
            - Interpretation: {change_data['buildup_change']['interpretation']}
            
            Coordinates: {self.center_lat}, {self.center_lon}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
            server.starttls()
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.send_message(msg)
            server.quit()
            
            print("✅ Alert email sent successfully!")
            
        except Exception as e:
            print(f"❌ Failed to send email alert: {str(e)}")
    
    def generate_visual_report(self, before_date: str, after_date: str):
        """Generate visual comparison using geemap"""
        # Create map centered on your land
        Map = geemap.Map(center=[self.center_lat, self.center_lon], zoom=18)
        
        # Add your land boundary
        Map.addLayer(self.aoi, {'color': 'red'}, 'Land Boundary')
        
        # Get imagery
        before_collection = self.get_sentinel2_imagery(
            (datetime.strptime(before_date, '%Y-%m-%d') - timedelta(days=15)).strftime('%Y-%m-%d'),
            (datetime.strptime(before_date, '%Y-%m-%d') + timedelta(days=15)).strftime('%Y-%m-%d')
        )
        
        after_collection = self.get_sentinel2_imagery(
            (datetime.strptime(after_date, '%Y-%m-%d') - timedelta(days=15)).strftime('%Y-%m-%d'),
            (datetime.strptime(after_date, '%Y-%m-%d') + timedelta(days=15)).strftime('%Y-%m-%d')
        )
        
        # Add imagery layers
        vis_params = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000}
        
        Map.addLayer(before_collection.median(), vis_params, f'Before ({before_date})')
        Map.addLayer(after_collection.median(), vis_params, f'After ({after_date})')
        
        return Map

# Example usage
def main():
    # Initialize the monitor
    monitor = LandChangeMonitor()
    
    # Example 1: Compare two specific dates
    print("🔍 Detecting changes between two dates...")
    changes = monitor.detect_changes('2023-01-01', '2024-01-01')
    print(json.dumps(changes, indent=2))
    
    # Example 2: Continuous monitoring for the past year
    print("\n📊 Starting continuous monitoring...")
    results = monitor.continuous_monitoring('2023-01-01', '2024-01-01', interval_days=60)
    
    # Example 3: Generate visual report
    print("\n🗺️  Generating visual report...")
    visual_map = monitor.generate_visual_report('2023-06-01', '2024-01-01')
    # visual_map.to_html('land_change_report.html')

if __name__ == "__main__":
    main()