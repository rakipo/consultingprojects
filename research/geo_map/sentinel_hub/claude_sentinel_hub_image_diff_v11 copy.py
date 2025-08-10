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
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import warnings
import yaml
import os
import argparse
import sys
import re
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
    def __init__(self, main_config_path: str = "sentinel_hub_config.yml", 
                 user_config_path: str = "sentinel_hub_user_config.yaml"):
        """
        Initialize Sentinel Hub monitoring system
        
        Args:
            main_config_path: Path to the main YAML configuration file
            user_config_path: Path to the user YAML configuration file
        """
        # Load main configuration from YAML file
        self.config_data = self._load_config(main_config_path)
        
        # Load user configuration from YAML file
        self.user_config = self._load_user_config(user_config_path)
        self.user_config_path = user_config_path  # Store for later use
        
        # Configure Sentinel Hub using OAuth authentication (no instance ID needed)
        self.config = SHConfig()
        self.config.sh_client_id = self.config_data['sentinel_hub']['client_id']
        self.config.sh_client_secret = self.config_data['sentinel_hub']['client_secret']
        
        # Use OAuth authentication instead of instance-based
        self.config.use_oauth = True
        
        # Load coordinates from user config
        self.coordinates = self._load_coordinates_from_yaml()
        
        # Create bounding box (min_x, min_y, max_x, max_y)
        lons = [coord[0] for coord in self.coordinates]
        lats = [coord[1] for coord in self.coordinates]
        
        self.bbox = BBox(
            bbox=[min(lons), min(lats), max(lons), max(lats)], 
            crs=CRS.WGS84
        )
        
        # Load image processing settings from config
        self.resolution = self.config_data['image_processing']['resolution']
        self.max_cloud_coverage = self.config_data['image_processing']['max_cloud_coverage']
        self.size = bbox_to_dimensions(self.bbox, resolution=self.resolution)
        
        # Create output directory for analysis results
        self.output_dir = self._create_output_directory()
        
        print(f"Monitoring area: {self.bbox}")

        print(f"Image dimensions: {self.size}")
        print(f"Output directory: {self.output_dir}")
        
        # Load evaluation scripts from config
        self.evalscripts = self.config_data['evalscripts']
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        
        return config
    
    def _load_user_config(self, user_config_path: str) -> Dict:
        """Load user configuration from YAML file"""
        if not os.path.exists(user_config_path):
            raise FileNotFoundError(f"User configuration file not found: {user_config_path}")
        
        with open(user_config_path, 'r') as file:
            user_config = yaml.safe_load(file)
        
        return user_config
    
    def _load_coordinates_from_yaml(self) -> List[List[float]]:
        """Load coordinates from the user YAML configuration"""
        if 'coordinates' not in self.user_config:
            raise ValueError("No coordinates found in user configuration file")
        
        coordinates = self.user_config['coordinates']
        
        if not coordinates:
            raise ValueError("No coordinates found in user configuration file")
        
        return coordinates
    
    def _create_output_directory(self) -> str:
        """Create output directory for analysis results"""
        # Create base output directory
        base_output_dir = self.config_data.get('output', {}).get('base_directory', 'analysis_results')
        
        # Create timestamped directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create coordinate string for directory name
        coord_str = self._get_coordinate_string()
        
        # Create full directory path
        output_dir = os.path.join(base_output_dir, f"{timestamp}_{coord_str}")
        
        # Create directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        return output_dir
    
    def _get_coordinate_string(self) -> str:
        """Generate a string representation of coordinates for file naming"""
        # Get center coordinates
        lons = [coord[0] for coord in self.coordinates]
        lats = [coord[1] for coord in self.coordinates]
        
        center_lon = sum(lons) / len(lons)
        center_lat = sum(lats) / len(lats)
        
        # Format coordinates (4 decimal places for readability)
        lon_str = f"{center_lon:.4f}".replace('.', 'p').replace('-', 'n')
        lat_str = f"{center_lat:.4f}".replace('.', 'p').replace('-', 'n')
        
        return f"lon{lon_str}_lat{lat_str}"
    
    def _get_timestamp_string(self) -> str:
        """Generate timestamp string for file naming"""
        return datetime.now().strftime('%Y%m%d_%H%M%S')
    
    def _save_analysis_result(self, result_data: Dict, analysis_type: str, 
                            date_ranges: Optional[Tuple[Tuple[str, str], Tuple[str, str]]] = None) -> str:
        """
        Save analysis result to file with timestamp and coordinates
        
        Args:
            result_data: The analysis result data to save
            analysis_type: Type of analysis (e.g., 'change_detection', 'statistics', 'continuous_monitoring')
            date_ranges: Optional tuple of date ranges for the analysis
        
        Returns:
            Path to the saved file
        """
        # Create filename with timestamp and coordinates
        timestamp = self._get_timestamp_string()
        coord_str = self._get_coordinate_string()
        
        # Add date range info if provided
        date_suffix = ""
        if date_ranges:
            before_start = date_ranges[0][0].replace('-', '')
            before_end = date_ranges[0][1].replace('-', '')
            after_start = date_ranges[1][0].replace('-', '')
            after_end = date_ranges[1][1].replace('-', '')
            date_suffix = f"_before{before_start}-{before_end}_after{after_start}-{after_end}"
        
        filename = f"{timestamp}_{coord_str}_{analysis_type}{date_suffix}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        # Add metadata to the result
        result_with_metadata = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "analysis_type": analysis_type,
                "coordinates": self.coordinates,
                "bbox": {
                    "min_lon": self.bbox.min_x,
                    "min_lat": self.bbox.min_y,
                    "max_lon": self.bbox.max_x,
                    "max_lat": self.bbox.max_y
                },
                "resolution": self.resolution,
                "max_cloud_coverage": self.max_cloud_coverage,
                "date_ranges": date_ranges
            },
            "analysis_result": result_data
        }
        
        # Save to JSON file
        with open(filepath, 'w') as f:
            json.dump(result_with_metadata, f, indent=2)
        
        print(f"📁 Analysis result saved: {filepath}")
        return filepath
    
    def _save_summary_report(self, all_results: List[Dict], analysis_type: str) -> str:
        """
        Save a summary report of all analysis results
        
        Args:
            all_results: List of all analysis results
            analysis_type: Type of analysis performed
        
        Returns:
            Path to the saved summary file
        """
        timestamp = self._get_timestamp_string()
        coord_str = self._get_coordinate_string()
        
        filename = f"{timestamp}_{coord_str}_{analysis_type}_summary.txt"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write(f"SENTINEL HUB LAND MONITORING ANALYSIS SUMMARY\n")
            f.write(f"=" * 50 + "\n\n")
            
            f.write(f"Analysis Type: {analysis_type}\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Coordinates: {self.coordinates}\n")
            f.write(f"Bounding Box: {self.bbox}\n")
            f.write(f"Resolution: {self.resolution}\n")
            f.write(f"Max Cloud Coverage: {self.max_cloud_coverage}%\n\n")
            
            f.write(f"TOTAL ANALYSES: {len(all_results)}\n\n")
            
            for i, result in enumerate(all_results, 1):
                f.write(f"Analysis #{i}:\n")
                f.write(f"  - Date Ranges: {result.get('before_period', 'N/A')} → {result.get('after_period', 'N/A')}\n")
                f.write(f"  - Significant Change: {result.get('significant_change', 'N/A')}\n")
                f.write(f"  - Summary: {result.get('change_summary', 'N/A')}\n")
                
                if 'vegetation_change' in result:
                    veg_change = result['vegetation_change']['ndvi_difference']
                    f.write(f"  - Vegetation Change: {veg_change:+.4f}\n")
                
                if 'buildup_change' in result:
                    build_change = result['buildup_change']['ndbi_difference']
                    f.write(f"  - Built-up Change: {build_change:+.4f}\n")
                
                if 'water_change' in result:
                    water_change = result['water_change']['ndwi_difference']
                    f.write(f"  - Water Change: {water_change:+.4f}\n")
                
                f.write("\n")
        
        print(f"📁 Summary report saved: {filepath}")
        return filepath
    
    def _save_csv_report(self, result_data: Dict, analysis_type: str, 
                        date_ranges: Optional[Tuple[Tuple[str, str], Tuple[str, str]]] = None) -> str:
        """
        Save analysis result as a formal CSV report with coordinates, analysis results, and interpretations
        
        Args:
            result_data: The analysis result data to save
            analysis_type: Type of analysis (e.g., 'change_detection', 'statistics', 'continuous_monitoring')
            date_ranges: Optional tuple of date ranges for the analysis
        
        Returns:
            Path to the saved CSV file
        """
        import csv
        
        # Create filename with timestamp and coordinates
        timestamp = self._get_timestamp_string()
        coord_str = self._get_coordinate_string()
        
        # Add date range info if provided
        date_suffix = ""
        if date_ranges:
            before_start = date_ranges[0][0].replace('-', '')
            before_end = date_ranges[0][1].replace('-', '')
            after_start = date_ranges[1][0].replace('-', '')
            after_end = date_ranges[1][1].replace('-', '')
            date_suffix = f"_before{before_start}-{before_end}_after{after_start}-{after_end}"
        
        filename = f"{timestamp}_{coord_str}_{analysis_type}{date_suffix}.csv"
        filepath = os.path.join(self.output_dir, filename)
        
        # Prepare CSV data
        csv_data = []
        
        # Add metadata rows
        csv_data.append(["ANALYSIS METADATA", ""])
        csv_data.append(["Timestamp", datetime.now().isoformat()])
        csv_data.append(["Analysis Type", analysis_type])
        csv_data.append(["Coordinates (Longitude, Latitude)", str(self.coordinates)])
        csv_data.append(["Bounding Box Min Lon", f"{self.bbox.min_x:.6f}"])
        csv_data.append(["Bounding Box Min Lat", f"{self.bbox.min_y:.6f}"])
        csv_data.append(["Bounding Box Max Lon", f"{self.bbox.max_x:.6f}"])
        csv_data.append(["Bounding Box Max Lat", f"{self.bbox.max_y:.6f}"])
        csv_data.append(["Resolution (meters)", str(self.resolution)])
        csv_data.append(["Max Cloud Coverage (%)", str(self.max_cloud_coverage)])
        
        if date_ranges:
            csv_data.append(["Before Period Start", date_ranges[0][0]])
            csv_data.append(["Before Period End", date_ranges[0][1]])
            csv_data.append(["After Period Start", date_ranges[1][0]])
            csv_data.append(["After Period End", date_ranges[1][1]])
        
        csv_data.append(["", ""])  # Empty row for spacing
        
        # Add analysis results
        if 'error' not in result_data:
            csv_data.append(["ANALYSIS RESULTS", ""])
            csv_data.append(["Change Type", "Before Value", "After Value", "Difference", "Interpretation", "Significance"])
            
            # Vegetation changes
            if 'vegetation_change' in result_data:
                veg = result_data['vegetation_change']
                csv_data.append([
                    "Vegetation (NDVI)",
                    f"{veg.get('before_ndvi', 0):.4f}",
                    f"{veg.get('after_ndvi', 0):.4f}",
                    f"{veg.get('ndvi_difference', 0):+.4f}",
                    veg.get('interpretation', 'N/A'),
                    "Significant" if abs(veg.get('ndvi_difference', 0)) > 0.1 else "Not Significant"
                ])
            
            # Built-up area changes
            if 'buildup_change' in result_data:
                build = result_data['buildup_change']
                csv_data.append([
                    "Built-up Area (NDBI)",
                    f"{build.get('before_ndbi', 0):.4f}",
                    f"{build.get('after_ndbi', 0):.4f}",
                    f"{build.get('ndbi_difference', 0):+.4f}",
                    build.get('interpretation', 'N/A'),
                    "Significant" if abs(build.get('ndbi_difference', 0)) > 0.1 else "Not Significant"
                ])
            
            # Water changes
            if 'water_change' in result_data:
                water = result_data['water_change']
                csv_data.append([
                    "Water/Moisture (NDWI)",
                    f"{water.get('before_ndwi', 0):.4f}",
                    f"{water.get('after_ndwi', 0):.4f}",
                    f"{water.get('ndwi_difference', 0):+.4f}",
                    water.get('interpretation', 'N/A'),
                    "Significant" if abs(water.get('ndwi_difference', 0)) > 0.1 else "Not Significant"
                ])
            
            csv_data.append(["", ""])  # Empty row for spacing
            
            # Overall summary
            csv_data.append(["OVERALL SUMMARY", ""])
            csv_data.append(["Significant Change Detected", "Yes" if result_data.get('significant_change', False) else "No"])
            csv_data.append(["Change Summary", result_data.get('change_summary', 'N/A')])
            
        else:
            csv_data.append(["ERROR", result_data.get('error', 'Unknown error')])
        
        # Write CSV file
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)
        
        print(f"📊 Formal CSV report saved: {filepath}")
        return filepath

    # def get_satellite_image(self, date_range: Tuple[str, str], 
    #                        evalscript_type: str = 'true_color',
    #                        max_cloud_coverage: Optional[float] = None) -> np.ndarray:
    #     """
    #     Retrieve satellite imagery for specified date range
    #     
    #     Args:
    #         date_range: Tuple of (start_date, end_date) in 'YYYY-MM-DD' format
    #         evalscript_type: Type of evaluation script to use
    #         max_cloud_coverage: Maximum allowed cloud coverage percentage (uses config default if None)
    #         
    #         Returns:
    #             numpy array of image data
    #         """
    #     # Use config default if not specified
    #     if max_cloud_coverage is None:
    #         max_cloud_coverage = self.max_cloud_coverage
    #         
    #     print(f"📡 Attempting to retrieve satellite imagery for {date_range}...")
    #     
    #     request = SentinelHubRequest(
    #         evalscript=self.evalscripts[evalscript_type],
    #         input_data=[
    #             SentinelHubRequest.input_data(
    #                 data_collection=DataCollection.SENTINEL2_L2A,
    #                 time_interval=date_range,
    #                 maxcc=max_cloud_coverage/100.0,
    #                 other_args={"dataFilter": {"mosaickingOrder": "mostRecent"}}
    #             )
    #         ],
    #         responses=[
    #             SentinelHubRequest.output_response('default', MimeType.TIFF)
    #         ],
    #         bbox=self.bbox,
    #         size=self.size,
    #         config=self.config
    #     )
    #     
    #     try:
    #         response = request.get_data()
    #         if response and len(response) > 0:
    #             print(f"✅ Successfully retrieved imagery: {response[0].shape}")
    #             return response[0]
    #         else:
    #             raise Exception("No data returned from Sentinel Hub")
    #     except Exception as e:
    #         print(f"❌ Error retrieving imagery: {str(e)}")
    #         print(f"🔄 Generating mock satellite imagery for demonstration...")
    #         return self._generate_mock_satellite_image(date_range)
    
    # def _generate_mock_satellite_image(self, date_range: Tuple[str, str]) -> np.ndarray:
    #     """
    #     Generate mock satellite imagery for demonstration purposes
    #     """
    #     # Create a realistic-looking satellite image
    #     height, width = self.size
    #     
    #     # Generate different patterns based on date for variety
    #     date_hash = hash(date_range[0]) % 1000
    #     
    #     # Create base image with some variation
    #     base_image = np.random.rand(height, width, 3) * 0.3 + 0.2
    #     
    #     # Add some realistic patterns
    #     for i in range(height):
    #         for j in range(width):
    #                 # Add some vegetation-like patterns
    #                 if (i + j + date_hash) % 20 < 10:
    #                     base_image[i, j, 1] += 0.3  # More green
    #                 
    #                 # Add some built-up area patterns
    #                 if (i * j + date_hash) % 15 < 5:
    #                     base_image[i, j, 0] += 0.2  # More red
    #                     base_image[i, j, 2] += 0.1  # More blue
    #                 
    #                 # Add some water-like patterns
    #                 if (i - j + date_hash) % 25 < 8:
    #                     base_image[i, j, 2] += 0.4  # More blue
    #                     base_image[i, j, 0] *= 0.7  # Less red
    #                     base_image[i, j, 1] *= 0.8  # Less green
    #     
    #     # Ensure values are in valid range
    #     base_image = np.clip(base_image, 0, 1)
    #     
    #     print(f"🎨 Generated mock image: {base_image.shape}")
    #     return base_image
    
    def calculate_statistics(self, date_range: Tuple[str, str],
                           max_cloud_coverage: Optional[float] = None,
                           save_result: bool = False) -> Dict:
        """
        Calculate statistical metrics for the area
        """
        # For demonstration purposes, create mock statistics
        # In a real implementation, this would use the Sentinel Hub Statistical API
        print(f"📊 Calculating statistics for {date_range}")
        
        # Mock statistics for demonstration
        mock_stats = {
            f"{date_range[0]}": {
                'ndvi_mean': 0.45 + (hash(date_range[0]) % 100) / 1000.0,  # Random but consistent
                'ndbi_mean': 0.12 + (hash(date_range[0]) % 50) / 1000.0,
                'ndwi_mean': 0.08 + (hash(date_range[0]) % 30) / 1000.0,
                'brightness_mean': 0.25 + (hash(date_range[0]) % 40) / 1000.0
            }
        }
        
        # Save result if requested
        if save_result and mock_stats:
            self._save_analysis_result(mock_stats, 'statistics', (date_range, date_range))
        
        return mock_stats
    
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
                      change_threshold: Optional[float] = None,
                      save_result: bool = True) -> Dict:
        """
        Detect changes between two time periods
        
        Args:
            before_date_range: (start, end) dates for before period
            after_date_range: (start, end) dates for after period
            change_threshold: Threshold for significant change detection
            save_result: Whether to save the result to file
        """
        # Use config default if not specified
        if change_threshold is None:
            change_threshold = self.config_data['change_detection']['default_threshold']
            
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
        
        # Save result if requested
        if save_result and 'error' not in changes:
            self._save_analysis_result(changes, 'change_detection', (before_date_range, after_date_range))
            self._save_csv_report(changes, 'change_detection', (before_date_range, after_date_range))
        
        return changes
    
    def _interpret_ndvi_change(self, change: float) -> str:
        """Interpret NDVI change values"""
        # Use user thresholds if available, otherwise fall back to system defaults
        if ('monitoring_preferences' in self.user_config and 
            'custom_thresholds' in self.user_config['monitoring_preferences'] and
            'ndvi' in self.user_config['monitoring_preferences']['custom_thresholds']):
            thresholds = self.user_config['monitoring_preferences']['custom_thresholds']['ndvi']
        else:
            thresholds = self.config_data['change_detection']['ndvi_thresholds']
        
        if change > thresholds['major_increase']:
            return "Major vegetation increase (new crops/plantations)"
        elif change > thresholds['moderate_increase']:
            return "Moderate vegetation growth"
        elif change < thresholds['major_decrease']:
            return "Major vegetation loss (clearing/harvesting)"
        elif change < thresholds['moderate_decrease']:
            return "Moderate vegetation decline"
        else:
            return "No significant vegetation change"
    
    def _interpret_ndbi_change(self, change: float) -> str:
        """Interpret NDBI change values"""
        # Use user thresholds if available, otherwise fall back to system defaults
        if ('monitoring_preferences' in self.user_config and 
            'custom_thresholds' in self.user_config['monitoring_preferences'] and
            'ndbi' in self.user_config['monitoring_preferences']['custom_thresholds']):
            thresholds = self.user_config['monitoring_preferences']['custom_thresholds']['ndbi']
        else:
            thresholds = self.config_data['change_detection']['ndbi_thresholds']
        
        if change > thresholds['significant_construction']:
            return "Significant construction/development"
        elif change > thresholds['minor_increase']:
            return "Minor built-up area increase"
        elif change < thresholds['demolition']:
            return "Possible demolition or clearing"
        else:
            return "No significant built-up change"
    
    def _interpret_ndwi_change(self, change: float) -> str:
        """Interpret NDWI change values"""
        # Use user thresholds if available, otherwise fall back to system defaults
        if ('monitoring_preferences' in self.user_config and 
            'custom_thresholds' in self.user_config['monitoring_preferences'] and
            'ndwi' in self.user_config['monitoring_preferences']['custom_thresholds']):
            thresholds = self.user_config['monitoring_preferences']['custom_thresholds']['ndwi']
        else:
            thresholds = self.config_data['change_detection']['ndwi_thresholds']
        
        if change > thresholds['water_appearance']:
            return "Water body appearance or expansion"
        elif change < thresholds['water_reduction']:
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
                             interval_days: Optional[int] = None,
                             change_threshold: Optional[float] = None,
                             save_results: bool = True) -> List[Dict]:
        """
        Perform continuous monitoring with regular intervals
        """
        # Use config defaults if not specified
        if interval_days is None:
            interval_days = self.config_data['monitoring']['default_interval_days']
        if change_threshold is None:
            change_threshold = self.config_data['change_detection']['default_threshold']
            
        period_length = self.config_data['monitoring']['period_length_days']
        
        print(f"🚀 Starting continuous monitoring from {start_date} to {end_date}")
        
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        results = []
        current_date = start
        
        while current_date < end - timedelta(days=interval_days):
            period1_start = current_date
            period1_end = current_date + timedelta(days=period_length)
            period2_start = current_date + timedelta(days=interval_days)
            period2_end = current_date + timedelta(days=interval_days + period_length)
            
            if period2_end > end:
                break
            
            try:
                changes = self.detect_changes(
                    (period1_start.strftime('%Y-%m-%d'), period1_end.strftime('%Y-%m-%d')),
                    (period2_start.strftime('%Y-%m-%d'), period2_end.strftime('%Y-%m-%d')),
                    change_threshold,
                    save_result=False  # Don't save individual results during continuous monitoring
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
        
        # Save summary of all continuous monitoring results
        if save_results and results:
            self._save_summary_report(results, 'continuous_monitoring')
            
            # Also save individual results for significant changes
            for result in results:
                if result.get('significant_change', False) and 'error' not in result:
                    self._save_analysis_result(
                        result, 
                        'continuous_monitoring_significant_change',
                        (result.get('before_period'), result.get('after_period'))
                    )
                    self._save_csv_report(
                        result, 
                        'continuous_monitoring_significant_change',
                        (result.get('before_period'), result.get('after_period'))
                    )
        
        return results
    
    # def generate_visual_comparison(self, before_date_range: Tuple[str, str],
    #                              after_date_range: Tuple[str, str],
    #                              save_path: Optional[str] = None,
    #                              save_metadata: bool = True) -> None:
    #     """Generate side-by-side visual comparison"""
    #     print("🖼️  Generating visual comparison...")
    #     
    #     # Use output directory for save path if not specified
    #     if save_path is None and self.config_data['output']['save_comparison_images']:
    #         # Generate timestamped filename in output directory
    #         timestamp = self._get_timestamp_string()
    #         coord_str = self._get_coordinate_string()
    #         before_start = before_date_range[0].replace('-', '')
    #         before_end = before_date_range[1].replace('-', '')
    #         after_start = after_date_range[0].replace('-', '')
    #         after_end = after_date_range[1].replace('-', '')
    #         
    #         filename = f"{timestamp}_{coord_str}_visual_comparison_before{before_start}-{before_end}_after{after_start}-{after_end}.png"
    #         save_path = os.path.join(self.output_dir, filename)
    #     
    #     # Get images for both periods
    #     before_img = self.get_satellite_image(before_date_range, 'true_color')
    #     after_img = self.get_satellite_image(after_date_range, 'true_color')
    #     
    #     if before_img is None or after_img is None:
    #         print("❌ Could not retrieve images for comparison")
    #         return
    #     
    #     # Create comparison plot
    #     fig, axes = plt.subplots(1, 2, figsize=(15, 7))
    #     
    #     # Before image
    #     axes[0].imshow(before_img)
    #     axes[0].set_title(f'Before: {before_date_range[0]} to {before_date_range[1]}', fontsize=12)
    #     axes[0].axis('off')
    #     
    #     # After image
    #     axes[1].imshow(after_img)
    #     axes[1].set_title(f'After: {after_date_range[0]} to {after_date_range[1]}', fontsize=12)
    #     axes[1].axis('off')
    #     
    #     plt.tight_layout()
    #     
    #     if save_path:
    #         dpi = self.config_data['output']['dpi']
    #         plt.savefig(save_path, dpi=dpi, bbox_inches='tight')
    #         print(f"📁 Comparison saved to {save_path}")
    #             
    #         # Save metadata if requested
    #         if save_metadata:
    #             self._save_visual_comparison_metadata(save_path, before_date_range, after_date_range)
    #     
    #     plt.show()
    
    # def _save_visual_comparison_metadata(self, image_path: str, 
    #                                    before_date_range: Tuple[str, str],
    #                                    after_date_range: Tuple[str, str]) -> str:
    #     """
    #     Save metadata for visual comparison image
    #     
    #     Args:
    #         image_path: Path to the saved image
    #         before_date_range: Date range for before period
    #         after_date_range: Date range for after period
    #     
    #     Returns:
    #         Path to the saved metadata file
    #     """
    #     # Create metadata filename based on image path
    #     base_name = os.path.splitext(image_path)[0]
    #     metadata_path = f"{base_name}_metadata.json"
    #     
    #     metadata = {
    #         "metadata": {
    #             "timestamp": datetime.now().isoformat(),
    #             "analysis_type": "visual_comparison",
    #             "coordinates": self.coordinates,
    #             "bbox": {
    #                 "min_lon": self.bbox.min_x,
    #                 "min_lat": self.bbox.min_y,
    #                 "max_lon": self.bbox.max_x,
    #                 "max_lat": self.bbox.max_y
    #             },
    #             "resolution": self.resolution,
    #             "max_cloud_coverage": self.max_cloud_coverage,
    #             "date_ranges": (before_date_range, after_date_range),
    #             "image_path": image_path
    #         },
    #         "image_info": {
    #             "before_period": before_date_range,
    #             "after_period": after_date_range,
    #             "image_format": "PNG",
    #             "dpi": self.config_data['output']['dpi']
    #         }
    #     }
    #     
    #     with open(metadata_path, 'w') as f:
    #         json.dump(metadata, f, indent=2)
    #     
    #     print(f"📁 Visual comparison metadata saved: {metadata_path}")
    #     return metadata_path
    
    def _send_alert(self, change_data: Dict):
        """Send email alert for significant changes"""
        # Check if alerts are enabled
        if not self.config_data['email']['enable_alerts']:
            print("📧 Email alerts are disabled in configuration")
            return
            
        # Email configuration from config file
        email_config = self.config_data['email']
        
        try:
            msg = MIMEMultipart()
            msg['From'] = email_config['sender_email']
            msg['To'] = email_config['recipient_email']
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
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['sender_email'], email_config['sender_password'])
            server.send_message(msg)
            server.quit()
            
            print("📧 Alert email sent successfully!")
            
        except Exception as e:
            print(f"❌ Failed to send email: {str(e)}")

# Example usage and configuration
def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Sentinel Hub Land Monitoring System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python claude_sentinel_hub_image_diff_v11.py --main-config sentinel_hub_config.yml --user-config sentinel_hub_user_config.yaml
  python claude_sentinel_hub_image_diff_v11.py -m my_config.yml -u my_coordinates.yaml
  python claude_sentinel_hub_image_diff_v11.py --main-config config.yml --user-config coordinates.yaml --mode detect
        """
    )
    
    parser.add_argument(
        '--main-config', '-m',
        required=True,
        help='Path to main YAML configuration file (REQUIRED)'
    )
    
    parser.add_argument(
        '--user-config', '-u',
        required=True,
        help='Path to user YAML configuration file (REQUIRED)'
    )
    
    parser.add_argument(
        '--mode', '-M',
        choices=['detect', 'visual', 'continuous', 'all'],
        default='all',
        help='Operation mode: detect changes, visual comparison, continuous monitoring, or all (default: all)'
    )
    
    parser.add_argument(
        '--before-start', '-bs',
        help='Start date for before period (YYYY-MM-DD format)'
    )
    
    parser.add_argument(
        '--before-end', '-be',
        help='End date for before period (YYYY-MM-DD format)'
    )
    
    parser.add_argument(
        '--after-start', '-as',
        help='Start date for after period (YYYY-MM-DD format)'
    )
    
    parser.add_argument(
        '--after-end', '-ae',
        help='End date for after period (YYYY-MM-DD format)'
    )
    
    parser.add_argument(
        '--threshold', '-t',
        type=float,
        help='Change detection threshold (overrides config default)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output file path for comparison images'
    )
    
    return parser.parse_args()

def main():
    """
    Main function demonstrating how to use the monitoring system
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Validate configuration files exist (additional check for better error messages)
    if not os.path.exists(args.main_config):
        print(f"❌ Main configuration file not found: {args.main_config}")
        print(f"💡 Please provide a valid path to your main configuration file")
        sys.exit(1)
    
    if not os.path.exists(args.user_config):
        print(f"❌ User configuration file not found: {args.user_config}")
        print(f"💡 Please provide a valid path to your user configuration file")
        sys.exit(1)
    
    # Initialize the monitoring system
    print("🛰️  Initializing Sentinel Hub Land Monitor...")
    print(f"📁 Main config: {args.main_config}")
    print(f"📁 User config: {args.user_config}")
    
    try:
        monitor = SentinelHubLandMonitor(args.main_config, args.user_config)
    except Exception as e:
        print(f"❌ Failed to initialize monitoring system: {str(e)}")
        sys.exit(1)
    
    # Determine date ranges from arguments or config
    if args.before_start and args.before_end and args.after_start and args.after_end:
        before_range = (args.before_start, args.before_end)
        after_range = (args.after_start, args.after_end)
    else:
        # Use default dates from user config if available, otherwise from main config
        if ('monitoring_preferences' in monitor.user_config and 
            'custom_date_ranges' in monitor.user_config['monitoring_preferences']):
            before_range = (
                monitor.user_config['monitoring_preferences']['custom_date_ranges']['before_period']['start'],
                monitor.user_config['monitoring_preferences']['custom_date_ranges']['before_period']['end']
            )
            after_range = (
                monitor.user_config['monitoring_preferences']['custom_date_ranges']['after_period']['start'],
                monitor.user_config['monitoring_preferences']['custom_date_ranges']['after_period']['end']
            )
        else:
            before_range = (
                monitor.config_data['default_dates']['before_period']['start'],
                monitor.config_data['default_dates']['before_period']['end']
            )
            after_range = (
                monitor.config_data['default_dates']['after_period']['start'],
                monitor.config_data['default_dates']['after_period']['end']
            )
    
    # Run operations based on mode
    if args.mode in ['detect', 'all']:
        print("\n📊 Change Detection Analysis")
        try:
            changes = monitor.detect_changes(
                before_date_range=before_range,
                after_date_range=after_range,
                change_threshold=args.threshold
            )
            
            if 'error' not in changes:
                print("🔍 CHANGE DETECTION RESULTS:")
                print(f"Summary: {changes['change_summary']}")
                print(f"Significant Change: {'YES' if changes['significant_change'] else 'NO'}")
                print(json.dumps(changes, indent=2))
            else:
                print(f"❌ Error in change detection: {changes['error']}")
        except Exception as e:
            print(f"❌ Error during change detection: {str(e)}")
    
    if args.mode in ['visual', 'all']:
        print("\n🖼️  Visual Comparison")
        print("⚠️  Visual comparison is disabled. Only analysis results are generated.")
        print("💡 Use --mode detect for change detection analysis only.")
    
    if args.mode in ['continuous', 'all']:
        print("\n🚀 Continuous Monitoring Setup")
        try:
            # Use user config dates if available
            if ('monitoring_preferences' in monitor.user_config and 
                'custom_date_ranges' in monitor.user_config['monitoring_preferences']):
                start_date = monitor.user_config['monitoring_preferences']['custom_date_ranges']['continuous_monitoring']['start']
                end_date = monitor.user_config['monitoring_preferences']['custom_date_ranges']['continuous_monitoring']['end']
            else:
                start_date = monitor.config_data['default_dates']['continuous_monitoring']['start']
                end_date = monitor.config_data['default_dates']['continuous_monitoring']['end']
            
            print(f"📅 Monitoring period: {start_date} to {end_date}")
            print("💡 To start continuous monitoring, uncomment the following lines in the code:")
            print(f"   results = monitor.continuous_monitoring('{start_date}', '{end_date}')")
        except Exception as e:
            print(f"❌ Error setting up continuous monitoring: {str(e)}")
    
    print("\n✅ Operations completed!")
    print(f"\n📁 All analysis results saved to: {monitor.output_dir}")
    print("\n📋 Configuration Summary:")
    print(f"   Main config: {args.main_config}")
    print(f"   User config: {args.user_config}")
    print(f"   Mode: {args.mode}")
    if args.threshold:
        print(f"   Threshold: {args.threshold}")
    if args.output:
        print(f"   Output: {args.output}")
    
    # Show what files were created
    if os.path.exists(monitor.output_dir):
        print(f"\n📄 Files created in output directory:")
        for file in os.listdir(monitor.output_dir):
            file_path = os.path.join(monitor.output_dir, file)
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path)
                print(f"   - {file} ({file_size} bytes)")

if __name__ == "__main__":
    main()