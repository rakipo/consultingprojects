#!/usr/bin/env python3
"""
Batch Property Analyzer
Reads multiple property coordinates from CSV and generates comprehensive analysis reports
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
import os
import yaml
import argparse
import calendar

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

class BatchPropertyAnalyzer:
    def __init__(self, config_path: str = "sentinel_hub_config.yml", 
                 user_config_path: str = "sentinel_hub_user_config.yaml"):
        """Initialize batch property analyzer"""
        
        # Load configurations
        self.config_data = self._load_config(config_path)
        self.user_config = self._load_user_config(user_config_path)
        
        # Setup Sentinel Hub
        self.config = SHConfig()
        self.config.sh_client_id = self.config_data['sentinel_hub']['client_id']
        self.config.sh_client_secret = self.config_data['sentinel_hub']['client_secret']
        self.config.use_oauth = True
        
        # Analysis parameters
        self.resolution = self.config_data['image_processing']['resolution']
        self.max_cloud_coverage = self.config_data['image_processing']['max_cloud_coverage']
        
        # Create output directory
        self.output_dir = self._create_output_directory()
        
        print(f"🏠 Batch Property Analyzer Initialized")
        print(f"📁 Output Directory: {self.output_dir}")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    
    def _load_user_config(self, user_config_path: str) -> Dict:
        """Load user configuration from YAML file"""
        with open(user_config_path, 'r') as file:
            return yaml.safe_load(file)
    
    def _create_output_directory(self) -> str:
        """Create output directory for batch analysis results"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = f"batch_analysis_results/{timestamp}_batch_analysis"
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
    
    def read_properties_from_csv(self, csv_file: str) -> pd.DataFrame:
        """Read property coordinates from CSV file"""
        print(f"📖 Reading properties from: {csv_file}")
        
        try:
            # Read CSV file
            df = pd.read_csv(csv_file)
            
            # Validate required columns
            required_columns = ['LATITUDE', 'LONGITUDE']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Add default values for missing optional columns
            if 'lp_no' not in df.columns:
                df['lp_no'] = range(1, len(df) + 1)
            
            if 'extent_ac' not in df.columns:
                df['extent_ac'] = 0.0
            
            if 'POINT_ID' not in df.columns:
                df['POINT_ID'] = range(1, len(df) + 1)
            
            if 'EASTING-X' not in df.columns:
                df['EASTING-X'] = 0.0
            
            if 'NORTHING-Y' not in df.columns:
                df['NORTHING-Y'] = 0.0
            
            print(f"✅ Loaded {len(df)} properties from CSV")
            return df
            
        except Exception as e:
            print(f"❌ Error reading CSV file: {str(e)}")
            raise
    
    def create_property_bbox(self, lat: float, lon: float, extent_ac: float = 0, buffer_meters: float = 10) -> BBox:
        """Create bounding box for a property with buffer, considering land area"""
        
        # Convert acres to square meters (1 acre = 4046.86 sq meters)
        extent_sq_meters = extent_ac * 4046.86 if extent_ac > 0 else 0
        
        # Calculate property radius based on area (assuming circular property)
        if extent_sq_meters > 0:
            property_radius_meters = (extent_sq_meters / 3.14159) ** 0.5
        else:
            property_radius_meters = 50  # Default 50m radius for point locations
        
        # Use the larger of property radius or buffer
        effective_radius_meters = max(property_radius_meters, buffer_meters)
        
        # Convert radius from meters to degrees (approximate)
        radius_degrees = effective_radius_meters / 111000  # 1 degree ≈ 111km
        
        bbox = BBox(
            bbox=[
                lon - radius_degrees,
                lat - radius_degrees,
                lon + radius_degrees,
                lat + radius_degrees
            ],
            crs=CRS.WGS84
        )
        
        return bbox
    
    def analyze_single_property(self, lat: float, lon: float, 
                               before_period: Tuple[str, str], 
                               after_period: Tuple[str, str],
                               extent_ac: float = 0) -> Dict:
        """Analyze a single property"""
        
        # Create bounding box considering land area
        bbox = self.create_property_bbox(lat, lon, extent_ac)
        size = bbox_to_dimensions(bbox, resolution=self.resolution)
        
        # Evalscript for analysis
        evalscript = """
        //VERSION=3
        function setup() {
            return {
                input: [{
                    bands: ["B02", "B03", "B04", "B08", "B11", "B12"],
                    units: "DN"
                }],
                output: { bands: 6 }
            };
        }
        
        function evaluatePixel(sample) {
            let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
            let ndbi = (sample.B11 - sample.B08) / (sample.B11 + sample.B08);
            let ndwi = (sample.B03 - sample.B08) / (sample.B03 + sample.B08);
            let ndre = (sample.B08 - sample.B11) / (sample.B08 + sample.B11);
            let brightness = (sample.B02 + sample.B03 + sample.B04) / 3;
            let moisture = (sample.B11 - sample.B12) / (sample.B11 + sample.B12);
            
            return [ndvi, ndbi, ndwi, ndre, brightness/3000, moisture];
        }
        """
        
        results = {}
        
        # Analyze before period
        try:
            before_request = SentinelHubRequest(
                evalscript=evalscript,
                input_data=[
                    SentinelHubRequest.input_data(
                        data_collection=DataCollection.SENTINEL2_L2A,
                        time_interval=before_period,
                        maxcc=self.max_cloud_coverage/100.0
                    )
                ],
                responses=[
                    SentinelHubRequest.output_response('default', MimeType.TIFF)
                ],
                bbox=bbox,
                size=size,
                config=self.config
            )
            
            before_response = before_request.get_data()
            if before_response and len(before_response) > 0:
                before_data = before_response[0]
                results['before'] = {
                    'ndvi': float(np.mean(before_data[:, :, 0])),
                    'ndbi': float(np.mean(before_data[:, :, 1])),
                    'ndwi': float(np.mean(before_data[:, :, 2]))
                }
            else:
                results['before'] = {'error': 'No data available'}
                
        except Exception as e:
            results['before'] = {'error': str(e)}
        
        # Analyze after period
        try:
            after_request = SentinelHubRequest(
                evalscript=evalscript,
                input_data=[
                    SentinelHubRequest.input_data(
                        data_collection=DataCollection.SENTINEL2_L2A,
                        time_interval=after_period,
                        maxcc=self.max_cloud_coverage/100.0
                    )
                ],
                responses=[
                    SentinelHubRequest.output_response('default', MimeType.TIFF)
                ],
                bbox=bbox,
                size=size,
                config=self.config
            )
            
            after_response = after_request.get_data()
            if after_response and len(after_response) > 0:
                after_data = after_response[0]
                results['after'] = {
                    'ndvi': float(np.mean(after_data[:, :, 0])),
                    'ndbi': float(np.mean(after_data[:, :, 1])),
                    'ndwi': float(np.mean(after_data[:, :, 2]))
                }
            else:
                results['after'] = {'error': 'No data available'}
                
        except Exception as e:
            results['after'] = {'error': str(e)}
        
        return results
    
    def interpret_changes(self, before_values: Dict, after_values: Dict) -> Dict:
        """Interpret changes between before and after periods"""
        
        if 'error' in before_values or 'error' in after_values:
            return {
                'vegetation': {'interpretation': 'Analysis failed', 'significance': 'Unknown'},
                'builtup': {'interpretation': 'Analysis failed', 'significance': 'Unknown'},
                'water': {'interpretation': 'Analysis failed', 'significance': 'Unknown'}
            }
        
        # Calculate differences
        ndvi_diff = after_values['ndvi'] - before_values['ndvi']
        ndbi_diff = after_values['ndbi'] - before_values['ndbi']
        ndwi_diff = after_values['ndwi'] - before_values['ndwi']
        
        # Threshold for significance
        threshold = 0.1
        
        # Interpret vegetation changes
        if abs(ndvi_diff) < threshold:
            vegetation_interpretation = "No significant vegetation change"
            vegetation_significance = "No"
        elif ndvi_diff > 0:
            vegetation_interpretation = "Vegetation growth or improvement"
            vegetation_significance = "Yes"
        else:
            vegetation_interpretation = "Vegetation loss or degradation"
            vegetation_significance = "Yes"
        
        # Interpret built-up area changes
        if abs(ndbi_diff) < threshold:
            builtup_interpretation = "No significant built-up area change"
            builtup_significance = "No"
        elif ndbi_diff > 0:
            builtup_interpretation = "Construction or development increase"
            builtup_significance = "Yes"
        else:
            builtup_interpretation = "Demolition or clearing"
            builtup_significance = "Yes"
        
        # Interpret water changes
        if abs(ndwi_diff) < threshold:
            water_interpretation = "No significant water change"
            water_significance = "No"
        elif ndwi_diff > 0:
            water_interpretation = "Water increase or flooding"
            water_significance = "Yes"
        else:
            water_interpretation = "Water decrease or drying"
            water_significance = "Yes"
        
        return {
            'vegetation': {
                'interpretation': vegetation_interpretation,
                'significance': vegetation_significance
            },
            'builtup': {
                'interpretation': builtup_interpretation,
                'significance': builtup_significance
            },
            'water': {
                'interpretation': water_interpretation,
                'significance': water_significance
            }
        }
    
    def analyze_batch_properties(self, csv_file: str, 
                                before_period: Tuple[str, str], 
                                after_period: Tuple[str, str]) -> pd.DataFrame:
        """Analyze multiple properties from CSV file"""
        
        print(f"🏠 Starting Batch Property Analysis")
        print(f"📅 Before Period: {before_period}")
        print(f"📅 After Period: {after_period}")
        
        # Read properties from CSV
        properties_df = self.read_properties_from_csv(csv_file)
        
        # Initialize results list
        results_list = []
        
        # Analyze each property
        for index, row in properties_df.iterrows():
            print(f"🔍 Analyzing property {index + 1}/{len(properties_df)}: {row['LATITUDE']:.6f}, {row['LONGITUDE']:.6f}")
            if row['extent_ac'] > 0:
                print(f"   📏 Land Area: {row['extent_ac']:.2f} acres ({row['extent_ac'] * 4046.86:.0f} sq meters)")
            
            # Analyze property
            analysis_results = self.analyze_single_property(
                row['LATITUDE'], 
                row['LONGITUDE'], 
                before_period, 
                after_period,
                row['extent_ac']
            )
            
            # Interpret changes
            interpretations = self.interpret_changes(analysis_results.get('before', {}), 
                                                   analysis_results.get('after', {}))
            
            # Create result row
            result_row = {
                # Basic identifiers & coordinates
                'lp_no': row['lp_no'],
                'extent_ac': row['extent_ac'],
                'POINT_ID': row['POINT_ID'],
                'EASTING-X': row['EASTING-X'],
                'NORTHING-Y': row['NORTHING-Y'],
                'LATITUDE': row['LATITUDE'],
                'LONGITUDE': row['LONGITUDE'],
                
                # Time periods (formatted as DD-MMM-YYYY)
                'Before Period Start': self._format_date_dd_mmm_yyyy(before_period[0]),
                'Before Period End': self._format_date_dd_mmm_yyyy(before_period[1]),
                'After Period Start': self._format_date_dd_mmm_yyyy(after_period[0]),
                'After Period End': self._format_date_dd_mmm_yyyy(after_period[1]),
            }
            
            # Add analysis results if available
            if 'before' in analysis_results and 'error' not in analysis_results['before']:
                before = analysis_results['before']
                after = analysis_results['after']
                
                # Vegetation Analysis (NDVI)
                result_row.update({
                    'Vegetation (NDVI)-Before Value': f"{before['ndvi']:.4f}",
                    'Vegetation (NDVI)-After Value': f"{after['ndvi']:.4f}",
                    'Vegetation (NDVI)-Difference': f"{after['ndvi'] - before['ndvi']:.4f}",
                    'Vegetation (NDVI)-Interpretation': interpretations['vegetation']['interpretation'],
                    'Vegetation (NDVI)-Significance': interpretations['vegetation']['significance']
                })
                
                # Built-up Area Analysis (NDBI)
                result_row.update({
                    'Built-up Area (NDBI)-Before Value': f"{before['ndbi']:.4f}",
                    'Built-up Area (NDBI)-After Value': f"{after['ndbi']:.4f}",
                    'Built-up Area (NDBI)-Difference': f"{after['ndbi'] - before['ndbi']:.4f}",
                    'Built-up Area (NDBI)-Interpretation': interpretations['builtup']['interpretation'],
                    'Built-up Area (NDBI)-Significance': interpretations['builtup']['significance']
                })
                
                # Water/Moisture Analysis (NDWI)
                result_row.update({
                    'Water/Moisture (NDWI)-Before Value': f"{before['ndwi']:.4f}",
                    'Water/Moisture (NDWI)-After Value': f"{after['ndwi']:.4f}",
                    'Water/Moisture (NDWI)-Difference': f"{after['ndwi'] - before['ndwi']:.4f}",
                    'Water/Moisture (NDWI)-Interpretation': interpretations['water']['interpretation'],
                    'Water/Moisture (NDWI)-Significance': interpretations['water']['significance']
                })
            else:
                # Add error placeholders
                error_placeholder = "Analysis failed"
                for metric in ['Vegetation (NDVI)', 'Built-up Area (NDBI)', 'Water/Moisture (NDWI)']:
                    result_row.update({
                        f'{metric}-Before Value': error_placeholder,
                        f'{metric}-After Value': error_placeholder,
                        f'{metric}-Difference': error_placeholder,
                        f'{metric}-Interpretation': error_placeholder,
                        f'{metric}-Significance': error_placeholder
                    })
            
            results_list.append(result_row)
        
        # Create results DataFrame
        results_df = pd.DataFrame(results_list)
        
        # Save results
        self._save_batch_results(results_df, before_period, after_period)
        
        return results_df
    
    def _format_date_dd_mmm_yyyy(self, date_str: str) -> str:
        """Convert date from YYYY-MM-DD to DD-MMM-YYYY format"""
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.strftime('%d-%b-%Y').upper()
        except ValueError:
            return date_str  # Return original if parsing fails
    
    def _save_batch_results(self, results_df: pd.DataFrame, 
                           before_period: Tuple[str, str], 
                           after_period: Tuple[str, str]):
        """Save batch analysis results"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Format dates for filename
        before_start_formatted = before_period[0].replace('-', '')
        before_end_formatted = before_period[1].replace('-', '')
        after_start_formatted = after_period[0].replace('-', '')
        after_end_formatted = after_period[1].replace('-', '')
        
        # Save CSV
        csv_filename = f"{timestamp}_batch_analysis_before{before_start_formatted}-{before_end_formatted}_after{after_start_formatted}-{after_end_formatted}.csv"
        csv_filepath = os.path.join(self.output_dir, csv_filename)
        results_df.to_csv(csv_filepath, index=False)
        
        # Save JSON
        json_filename = f"{timestamp}_batch_analysis_before{before_start_formatted}-{before_end_formatted}_after{after_start_formatted}-{after_end_formatted}.json"
        json_filepath = os.path.join(self.output_dir, json_filename)
        
        json_data = {
            'analysis_timestamp': datetime.now().isoformat(),
            'before_period': before_period,
            'after_period': after_period,
            'total_properties': len(results_df),
            'properties_analyzed': len(results_df),
            'results': results_df.to_dict('records')
        }
        
        with open(json_filepath, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        print(f"📁 Batch analysis results saved:")
        print(f"   CSV: {csv_filepath}")
        print(f"   JSON: {json_filepath}")

def main():
    """Main function for batch property analysis"""
    parser = argparse.ArgumentParser(description='Batch Property Analyzer')
    parser.add_argument('--input', '-i', required=True, help='Input CSV file with property coordinates')
    parser.add_argument('--before-start', '-bs', default='2022-11-01', help='Before period start date (YYYY-MM-DD)')
    parser.add_argument('--before-end', '-be', default='2023-01-31', help='Before period end date (YYYY-MM-DD)')
    parser.add_argument('--after-start', '-as', default='2025-01-01', help='After period start date (YYYY-MM-DD)')
    parser.add_argument('--after-end', '-ae', default='2025-03-31', help='After period end date (YYYY-MM-DD)')
    parser.add_argument('--main-config', '-m', default='sentinel_hub_config.yml', help='Main configuration file')
    parser.add_argument('--user-config', '-u', default='sentinel_hub_user_config.yaml', help='User configuration file')
    
    args = parser.parse_args()
    
    print("🏠 Batch Property Analysis")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = BatchPropertyAnalyzer(args.main_config, args.user_config)
    
    # Define periods
    before_period = (args.before_start, args.before_end)
    after_period = (args.after_start, args.after_end)
    
    # Run batch analysis
    results = analyzer.analyze_batch_properties(args.input, before_period, after_period)
    
    # Display summary
    print(f"\n📊 BATCH ANALYSIS SUMMARY:")
    print(f"Total Properties: {len(results)}")
    print(f"Analysis Period: {before_period} to {after_period}")
    
    # Count significant changes
    significant_changes = 0
    for _, row in results.iterrows():
        if any(row[f'{metric}-Significance'] == 'Yes' for metric in ['Vegetation (NDVI)', 'Built-up Area (NDBI)', 'Water/Moisture (NDWI)']):
            significant_changes += 1
    
    print(f"Properties with Significant Changes: {significant_changes}")
    print(f"✅ Batch analysis completed! Check the output directory for detailed results.")

if __name__ == "__main__":
    main()
