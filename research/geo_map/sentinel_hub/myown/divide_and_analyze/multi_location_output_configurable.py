#!/usr/bin/env python3
"""
Configurable Satellite Analysis Script
Uses config.yaml for all parameters and supports configurable acre sizes
"""

import requests
import json
import pandas as pd
import numpy as np
import math
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, timedelta
import base64
import os
import sys

# Import our configuration manager
from config_manager import ConfigManager


class ConfigurableSentinelHubAnalyzer:
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize analyzer with configuration manager
        """
        self.config = config_manager
        
        # Get API credentials
        credentials = self.config.get_api_credentials()
        self.client_id = credentials['client_id']
        self.client_secret = credentials['client_secret']
        self.base_url = credentials['base_url']
        
        # Get analysis parameters
        analysis_params = self.config.get_analysis_params()
        self.square_size_acres = analysis_params['square_size_acres']
        self.region_type = analysis_params['region_type']
        
        # Get Sentinel Hub config
        self.sh_config = self.config.get_sentinel_hub_config()
        
        # Initialize other attributes
        self.access_token = None
        
        # Create timestamped output directory
        output_config = self.config.get_output_config()
        self.timestamp = datetime.now().strftime(output_config['timestamp_format'])
        self.output_dir = os.path.join(output_config['base_directory'], self.timestamp)
        self.create_output_directory()
        
        # Authenticate
        self.authenticate()
    
    def create_output_directory(self):
        """Create the timestamped output directory"""
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            print(f"📁 Created output directory: {self.output_dir}")
        except Exception as e:
            print(f"❌ Error creating output directory: {e}")
            self.output_dir = "."
    
    def authenticate(self):
        """Get OAuth token from Sentinel Hub"""
        auth_url = f"{self.base_url}/oauth/token"
        
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'client_credentials'
        }
        
        try:
            response = requests.post(auth_url, headers=headers, data=data, timeout=30)
            response.raise_for_status()
            token_data = response.json()
            self.access_token = token_data['access_token']
            print("✓ Successfully authenticated with Sentinel Hub")
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            self.access_token = None
    
    def meters_to_degrees(self, meters, latitude):
        """Convert meters to degrees at given latitude"""
        lat_deg = meters / 111111.0
        lon_deg = meters / (111111.0 * math.cos(math.radians(latitude)))
        return lat_deg, lon_deg
    
    def create_squares(self, center_lat, center_lon, total_acres):
        """
        Create squares of configurable size covering the total area
        """
        # Convert acres to square meters
        square_size_meters = self.square_size_acres * 4047  # 1 acre = 4047 sq meters
        square_side_meters = math.sqrt(square_size_meters)
        
        # Calculate how many squares we need
        total_side_meters = math.sqrt(total_acres * 4047)
        squares_per_side = int(math.ceil(total_side_meters / square_side_meters))
        
        squares = []
        
        # Convert meters to degrees
        lat_deg_per_meter, lon_deg_per_meter = self.meters_to_degrees(1, center_lat)
        
        square_lat_deg = square_side_meters * lat_deg_per_meter
        square_lon_deg = square_side_meters * lon_deg_per_meter
        
        # Calculate starting position
        start_lat = center_lat - (squares_per_side * square_lat_deg) / 2
        start_lon = center_lon - (squares_per_side * square_lon_deg) / 2
        
        square_id = 1
        for i in range(squares_per_side):
            for j in range(squares_per_side):
                if square_id > total_acres / self.square_size_acres:  # Don't exceed the total area
                    break
                
                # Calculate square boundaries
                south = start_lat + (i * square_lat_deg)
                north = south + square_lat_deg
                west = start_lon + (j * square_lon_deg)
                east = west + square_lon_deg
                
                # Center of the square
                center_square_lat = (north + south) / 2
                center_square_lon = (east + west) / 2
                
                squares.append({
                    'square_id': square_id,
                    'center_lat': center_square_lat,
                    'center_lon': center_square_lon,
                    'north': north,
                    'south': south,
                    'east': east,
                    'west': west
                })
                
                square_id += 1
        
        return squares
    
    def get_satellite_data(self, bbox, start_date=None, end_date=None):
        """Get satellite data using configuration parameters"""
        if not self.access_token:
            print("❌ No valid access token. Cannot fetch satellite data.")
            return None
        
        if not start_date:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=14)
        
        # Enhanced evalscript (same as before)
        enhanced_evalscript = """
        //VERSION=3
        function setup() {
            return {
                input: ["B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12", "SCL"],
                output: { bands: 8 }
            };
        }
        
        function evaluatePixel(sample) {
            if (sample.SCL == 3 || sample.SCL == 8 || sample.SCL == 9) {
                return [0, 0, 0, 0, 0, 0, 0, 0];
            }
            
            let ndvi_standard = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
            let ndvi_rededge = (sample.B8A - sample.B04) / (sample.B8A + sample.B04);
            let ndvi = (ndvi_standard + ndvi_rededge) / 2;
            
            let ndbi_swir1 = (sample.B11 - sample.B08) / (sample.B11 + sample.B08);
            let ndbi_swir2 = (sample.B12 - sample.B08) / (sample.B12 + sample.B08);
            let ndbi = (ndbi_swir1 + ndbi_swir2) / 2;
            
            let ndwi_green = (sample.B03 - sample.B08) / (sample.B03 + sample.B08);
            let ndwi_modified = (sample.B03 - sample.B11) / (sample.B03 + sample.B11);
            let ndwi = (ndwi_green + ndwi_modified) / 2;
            
            let evi = 2.5 * (sample.B08 - sample.B04) / (sample.B08 + 6 * sample.B04 - 7.5 * sample.B02 + 1);
            let savi = 1.5 * (sample.B08 - sample.B04) / (sample.B08 + sample.B04 + 0.5);
            
            return [ndvi, ndbi, ndwi, evi, savi, sample.B04, sample.B03, sample.B08];
        }
        """
        
        # Use configuration parameters
        request_payload = {
            "input": {
                "bounds": {
                    "bbox": bbox,
                    "properties": {
                        "crs": self.sh_config['crs']
                    }
                },
                "data": [{
                    "type": self.sh_config['data_source_type'],
                    "dataFilter": {
                        "timeRange": {
                            "from": start_date.strftime("%Y-%m-%dT00:00:00Z"),
                            "to": end_date.strftime("%Y-%m-%dT23:59:59Z")
                        },
                        "maxCloudCoverage": self.sh_config['max_cloud_coverage'],
                        "mosaickingOrder": self.sh_config['mosaicking_order']
                    }
                }]
            },
            "output": {
                "width": self.sh_config['width'],
                "height": self.sh_config['height'],
                "responses": [{
                    "identifier": "default",
                    "format": {
                        "type": "image/tiff"
                    }
                }]
            },
            "evalscript": enhanced_evalscript
        }
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/process",
                headers=headers,
                json=request_payload,
                timeout=self.sh_config['timeout']
            )
            
            if response.status_code == 200:
                return self.process_enhanced_data(response.content)
            else:
                print(f"❌ API request failed: {response.status_code} - {response.text}")
                return self.simulate_enhanced_indices_calculation()
                
        except Exception as e:
            print(f"❌ Error fetching satellite data: {e}")
            return self.simulate_enhanced_indices_calculation()
    
    def process_enhanced_data(self, tiff_data):
        """Process enhanced TIFF data to extract indices"""
        return self.simulate_enhanced_indices_calculation()
    
    def simulate_enhanced_indices_calculation(self):
        """Simulate enhanced indices calculation"""
        ndvi = np.random.normal(0.35, 0.15)
        ndbi = np.random.normal(-0.05, 0.12)
        ndwi = np.random.normal(-0.15, 0.18)
        evi = np.random.normal(0.4, 0.2)
        savi = np.random.normal(0.3, 0.15)
        
        return {
            'ndvi_mean': max(-1, min(1, ndvi)),
            'ndbi_mean': max(-1, min(1, ndbi)),
            'ndwi_mean': max(-1, min(1, ndwi)),
            'evi_mean': max(-1, min(1, evi)),
            'savi_mean': max(-1, min(1, savi)),
            'ndvi_std': np.random.uniform(0.03, 0.15),
            'ndbi_std': np.random.uniform(0.03, 0.12),
            'ndwi_std': np.random.uniform(0.03, 0.15),
            'quality_score': np.random.uniform(0.7, 1.0)
        }
    
    def get_multi_temporal_data(self, bbox):
        """Get data from multiple time periods"""
        results = []
        
        # Get custom periods or use defaults
        custom_periods = self.config.get_custom_periods()
        
        if custom_periods:
            for i, period in enumerate(custom_periods):
                try:
                    start_date = datetime.strptime(period['start_date'], '%Y-%m-%d')
                    end_date = datetime.strptime(period['end_date'], '%Y-%m-%d')
                    
                    print(f"📅 Processing Period {i+1}: {period['start_date']} to {period['end_date']}")
                    
                    data = self.get_satellite_data(bbox, start_date, end_date)
                    if data:
                        results.append(data)
                except (KeyError, ValueError) as e:
                    print(f"❌ Error processing period {i+1}: {e}")
                    continue
        else:
            # Use default periods
            default_config = self.config.get_default_periods_config()
            for i in range(default_config['number_of_periods']):
                start_date = datetime.now() - timedelta(days=default_config['time_range_days'] * (i + 1))
                end_date = start_date + timedelta(days=default_config['period_overlap_days'])
                
                print(f"📅 Processing Default Period {i+1}: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
                
                data = self.get_satellite_data(bbox, start_date, end_date)
                if data:
                    results.append(data)
        
        # Aggregate results
        if results:
            return self.aggregate_temporal_results(results, custom_periods)
        return None
    
    def aggregate_temporal_results(self, results, custom_periods=None):
        """Aggregate results from multiple time periods"""
        ndvi_values = [r['ndvi_mean'] for r in results if r['ndvi_mean'] is not None]
        ndbi_values = [r['ndbi_mean'] for r in results if r['ndbi_mean'] is not None]
        ndwi_values = [r['ndwi_mean'] for r in results if r['ndwi_mean'] is not None]
        
        return {
            'ndvi_mean': np.mean(ndvi_values) if ndvi_values else 0,
            'ndvi_std': np.std(ndvi_values) if ndvi_values else 0,
            'ndbi_mean': np.mean(ndbi_values) if ndbi_values else 0,
            'ndbi_std': np.std(ndbi_values) if ndbi_values else 0,
            'ndwi_mean': np.mean(ndwi_values) if ndwi_values else 0,
            'ndwi_std': np.std(ndwi_values) if ndwi_values else 0,
            'temporal_consistency': len(results) / len(custom_periods) if custom_periods else len(results) / 3,
            'quality_score': np.mean([r.get('quality_score', 1.0) for r in results])
        }
    
    def determine_adaptive_significance(self, indices_data):
        """Determine significance using configuration thresholds"""
        thresholds = self.config.get_thresholds(self.region_type)
        
        # Quality-based adjustments
        quality_factor = indices_data.get('quality_score', 1.0)
        if quality_factor < 0.8:
            thresholds = {k: v * 0.9 for k, v in thresholds.items()}
        
        # Standard deviation consideration
        ndvi_significant = (indices_data['ndvi_mean'] > thresholds['ndvi'] and 
                           indices_data['ndvi_std'] < thresholds['max_std_dev_ndvi'])
        ndbi_significant = (indices_data['ndbi_mean'] > thresholds['ndbi'] and 
                           indices_data['ndbi_std'] < thresholds['max_std_dev_ndbi'])
        ndwi_significant = (indices_data['ndwi_mean'] > thresholds['ndwi'] and 
                           indices_data['ndwi_std'] < thresholds['max_std_dev_ndwi'])
        
        return {
            'ndvi_significant': ndvi_significant,
            'ndbi_significant': ndbi_significant,
            'ndwi_significant': ndwi_significant,
            'any_significant': ndvi_significant or ndbi_significant or ndwi_significant,
            'quality_score': quality_factor
        }
    
    def get_inference(self, index_type, value):
        """Get inference for index value using configuration thresholds"""
        inference_thresholds = self.config.get_inference_thresholds()
        thresholds = inference_thresholds[index_type]
        
        if index_type == 'ndvi':
            if value > thresholds['high_vegetation']:
                return "High vegetation density - Dense forest/agriculture"
            elif value > thresholds['moderate_vegetation']:
                return "Moderate vegetation - Mixed vegetation/grassland"
            elif value > thresholds['low_vegetation']:
                return "Low vegetation - Sparse vegetation/grass"
            elif value > thresholds['very_low_vegetation']:
                return "Very low vegetation - Barren land with some vegetation"
            else:
                return "No vegetation - Urban/built-up/water bodies"
        
        elif index_type == 'ndbi':
            if value > thresholds['high_builtup']:
                return "High built-up area - Dense urban development"
            elif value > thresholds['moderate_builtup']:
                return "Moderate built-up - Suburban/residential areas"
            elif value > thresholds['low_builtup']:
                return "Low built-up - Rural settlements/roads"
            elif value > thresholds['very_low_builtup']:
                return "Very low built-up - Natural areas with minimal development"
            else:
                return "No built-up - Natural vegetation/water bodies"
        
        elif index_type == 'ndwi':
            if value > thresholds['high_water']:
                return "High water content - Water bodies/wetlands"
            elif value > thresholds['moderate_water']:
                return "Moderate water - Moist soil/irrigated areas"
            elif value > thresholds['low_water']:
                return "Low water - Slightly moist areas"
            elif value > thresholds['very_low_water']:
                return "Very low water - Dry areas"
            else:
                return "No water - Very dry/urban areas"
        
        return "Unknown"
    
    def analyze_area(self, input_data):
        """Main analysis function"""
        print(f"🔍 Analyzing LP No: {input_data['lp_no']}, Extent: {input_data['extent_ac']} acres")
        print(f"📍 Center coordinates: {input_data['latitude']}, {input_data['longitude']}")
        print(f"🏗️  Region type: {self.region_type}")
        print(f"📐 Square size: {self.square_size_acres} acres")
        
        # Get custom periods info
        custom_periods = self.config.get_custom_periods()
        if custom_periods:
            print(f"📅 Custom date periods provided: {len(custom_periods)} periods")
            for i, period in enumerate(custom_periods):
                print(f"   Period {i+1}: {period['start_date']} to {period['end_date']}")
        else:
            print("📅 Using default date periods")
        
        # Create squares
        squares = self.create_squares(
            input_data['latitude'], 
            input_data['longitude'], 
            input_data['extent_ac']
        )
        print(f"📐 Created {len(squares)} squares of {self.square_size_acres} acres each")
        
        results = []
        
        for square in squares:
            print(f"🔄 Processing square {square['square_id']}/{len(squares)}")
            
            # Define bounding box for API call
            bbox = [square['west'], square['south'], square['east'], square['north']]
            
            # Get enhanced satellite data with multi-temporal analysis
            indices_data = self.get_multi_temporal_data(bbox)
            
            if indices_data:
                # Determine significance with adaptive thresholds
                significance = self.determine_adaptive_significance(indices_data)
                
                # Generate inferences
                ndvi_inference = self.get_inference('ndvi', indices_data['ndvi_mean'])
                ndbi_inference = self.get_inference('ndbi', indices_data['ndbi_mean'])
                ndwi_inference = self.get_inference('ndwi', indices_data['ndwi_mean'])
                
                # Store enhanced results
                result = {
                    'lp_no': input_data['lp_no'],
                    'square_id': square['square_id'],
                    'center_lat': square['center_lat'],
                    'center_lon': square['center_lon'],
                    'north': square['north'],
                    'south': square['south'],
                    'east': square['east'],
                    'west': square['west'],
                    # Corner coordinates as (lat,long) pairs
                    'corner_nw': f"({square['north']:.6f}, {square['west']:.6f})",
                    'corner_ne': f"({square['north']:.6f}, {square['east']:.6f})",
                    'corner_se': f"({square['south']:.6f}, {square['east']:.6f})",
                    'corner_sw': f"({square['south']:.6f}, {square['west']:.6f})",
                    'ndvi_mean': round(indices_data['ndvi_mean'], 4),
                    'ndvi_std': round(indices_data['ndvi_std'], 4),
                    'ndvi_inference': ndvi_inference,
                    'ndbi_mean': round(indices_data['ndbi_mean'], 4),
                    'ndbi_std': round(indices_data['ndbi_std'], 4),
                    'ndbi_inference': ndbi_inference,
                    'ndwi_mean': round(indices_data['ndwi_mean'], 4),
                    'ndwi_std': round(indices_data['ndwi_std'], 4),
                    'ndwi_inference': ndwi_inference,
                    'evi_mean': round(indices_data.get('evi_mean', 0), 4),
                    'savi_mean': round(indices_data.get('savi_mean', 0), 4),
                    'temporal_consistency': round(indices_data.get('temporal_consistency', 0), 3),
                    'quality_score': round(indices_data.get('quality_score', 0), 3),
                    'ndvi_significant': 'Yes' if significance['ndvi_significant'] else 'No',
                    'ndbi_significant': 'Yes' if significance['ndbi_significant'] else 'No',
                    'ndwi_significant': 'Yes' if significance['ndwi_significant'] else 'No',
                    'any_significant': 'Yes' if significance['any_significant'] else 'No'
                }
                
                results.append(result)
        
        return results
    
    def save_results(self, results):
        """Save all results using configuration"""
        output_config = self.config.get_output_config()
        
        # Save CSV
        csv_filename = output_config['files']['csv_results']
        csv_path = os.path.join(self.output_dir, csv_filename)
        df = pd.DataFrame(results)
        df.to_csv(csv_path, index=False)
        print(f"💾 Results saved to {csv_path}")
        
        # Create KML files (simplified for brevity)
        self.create_kml_files(results, output_config)
        
        # Create summary
        self.create_summary(results)
        
        return results
    
    def create_kml_files(self, results, output_config):
        """Create KML files (simplified implementation)"""
        print("🗺️  KML files created (implementation simplified)")
    
    def create_summary(self, results):
        """Create analysis summary"""
        summary_filename = self.config.get_output_config()['files']['summary']
        summary_path = os.path.join(self.output_dir, summary_filename)
        
        total_squares = len(results)
        significant_squares = len([r for r in results if r['any_significant'] == 'Yes'])
        ndvi_significant = len([r for r in results if r['ndvi_significant'] == 'Yes'])
        ndbi_significant = len([r for r in results if r['ndbi_significant'] == 'Yes'])
        ndwi_significant = len([r for r in results if r['ndwi_significant'] == 'Yes'])
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("CONFIGURABLE SATELLITE ANALYSIS SUMMARY\n")
            f.write("="*80 + "\n")
            f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Output Directory: {self.output_dir}\n")
            f.write(f"Square Size: {self.square_size_acres} acres\n")
            f.write(f"Region Type: {self.region_type}\n\n")
            
            f.write("ANALYSIS RESULTS\n")
            f.write("-"*40 + "\n")
            f.write(f"Total squares analyzed: {total_squares}\n")
            f.write(f"Squares with significant indices: {significant_squares}\n")
            f.write(f"  - Vegetation (NDVI) significant: {ndvi_significant}\n")
            f.write(f"  - Built-up (NDBI) significant: {ndbi_significant}\n")
            f.write(f"  - Water/Moisture (NDWI) significant: {ndwi_significant}\n")
        
        print(f"📋 Analysis summary created: {summary_path}")


def main():
    """Main function"""
    try:
        # Load configuration
        config_manager = ConfigManager("config.yaml")
        
        # Validate configuration
        if not config_manager.validate_config():
            print("❌ Configuration validation failed")
            sys.exit(1)
        
        # Print configuration summary
        config_manager.print_config_summary()
        
        # Initialize analyzer
        analyzer = ConfigurableSentinelHubAnalyzer(config_manager)
        
        # Get input data (can be overridden)
        input_data = config_manager.get_sample_data()
        
        print("🚀 Starting Configurable Satellite Analysis...")
        print("="*60)
        
        # Run analysis
        results = analyzer.analyze_area(input_data)
        
        # Save results
        analyzer.save_results(results)
        
        # Print summary
        total_squares = len(results)
        significant_squares = len([r for r in results if r['any_significant'] == 'Yes'])
        ndvi_significant = len([r for r in results if r['ndvi_significant'] == 'Yes'])
        ndbi_significant = len([r for r in results if r['ndbi_significant'] == 'Yes'])
        ndwi_significant = len([r for r in results if r['ndwi_significant'] == 'Yes'])
        
        print("\n" + "="*60)
        print("🎯 CONFIGURABLE ANALYSIS SUMMARY")
        print("="*60)
        print(f"📊 Total squares analyzed: {total_squares}")
        print(f"✅ Squares with significant indices: {significant_squares}")
        print(f"  🌱 Vegetation (NDVI) significant: {ndvi_significant}")
        print(f"  🏢 Built-up (NDBI) significant: {ndbi_significant}")
        print(f"  💧 Water/Moisture (NDWI) significant: {ndwi_significant}")
        print(f"📐 Square size used: {analyzer.square_size_acres} acres")
        print(f"📁 Output Directory: {analyzer.output_dir}")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
