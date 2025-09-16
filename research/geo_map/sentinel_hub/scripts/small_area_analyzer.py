#!/usr/bin/env python3
"""
Small Area Property Analyzer
Specialized for analyzing very small properties (1200 sq ft and similar)
Addresses Sentinel Hub limitations for small areas
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
import os
import yaml
import math
import logging
import requests
from urllib.parse import urlparse

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

class SmallAreaAnalyzer:
    def __init__(self, config_path: str = "sentinel_hub_config.yml", 
                 user_config_path: str = "sentinel_hub_user_config.yaml"):
        """Initialize small area analyzer with specialized settings"""
        
        # Load configurations
        self.config_data = self._load_config(config_path)
        self.user_config = self._load_user_config(user_config_path)
        
        # Setup Sentinel Hub
        self.config = SHConfig()
        self.config.sh_client_id = self.config_data['sentinel_hub']['client_id']
        self.config.sh_client_secret = self.config_data['sentinel_hub']['client_secret']
        self.config.use_oauth = True
        
        # Load coordinates
        self.coordinates = self.user_config['coordinates']
        lons = [coord[0] for coord in self.coordinates]
        lats = [coord[1] for coord in self.coordinates]
        
        # Calculate area
        self.area_sq_meters = self._calculate_area(lons, lats)
        self.area_sq_feet = self.area_sq_meters * 10.764
        
        print(f"📏 Property Area: {self.area_sq_feet:.1f} sq ft ({self.area_sq_meters:.1f} sq m)")
        
        # Determine if area is too small
        self.is_small_area = self.area_sq_meters < 1000  # Less than 1000 sq m
        
        if self.is_small_area:
            print(f"⚠️  Small area detected! Using specialized analysis methods.")
            self._setup_small_area_analysis()
        else:
            print(f"✅ Area size is adequate for standard analysis.")
            self._setup_standard_analysis()
        
        # Create output directory
        self.output_dir = self._create_output_directory()
        
        # Setup logging for Sentinel Hub requests/responses
        self._setup_logging()
        
        print(f"🏠 Small Area Analyzer Initialized")
        print(f"📍 Property Location: {min(lons):.6f}, {min(lats):.6f} to {max(lons):.6f}, {max(lats):.6f}")
        print(f"📁 Output Directory: {self.output_dir}")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    
    def _load_user_config(self, user_config_path: str) -> Dict:
        """Load user configuration from YAML file"""
        with open(user_config_path, 'r') as file:
            return yaml.safe_load(file)
    
    def _calculate_area(self, lons: List[float], lats: List[float]) -> float:
        """Calculate area in square meters using Haversine formula"""
        if len(lons) < 3:
            return 0.0
        
        # Convert to radians
        lons_rad = [math.radians(lon) for lon in lons]
        lats_rad = [math.radians(lat) for lat in lats]
        
        # Calculate area using shoelace formula
        area = 0.0
        for i in range(len(lons)):
            j = (i + 1) % len(lons)
            area += lons_rad[i] * lats_rad[j]
            area -= lats_rad[i] * lons_rad[j]
        
        area = abs(area) / 2.0
        
        # Convert to square meters (approximate)
        # This is a simplified calculation - for precise area, use proper geodesic calculations
        earth_radius = 6371000  # meters
        area_sq_meters = area * earth_radius * earth_radius
        
        return area_sq_meters
    
    def _setup_small_area_analysis(self):
        """Setup specialized analysis for small areas"""
        # Use higher resolution when possible
        self.resolution = 5  # 5m resolution instead of 10m
        self.max_cloud_coverage = 10  # Lower cloud coverage for better quality
        
        # Expand bounding box slightly for better analysis
        lons = [coord[0] for coord in self.coordinates]
        lats = [coord[1] for coord in self.coordinates]
        
        # Add buffer around the property
        buffer_degrees = 0.0001  # Approximately 10m buffer
        self.bbox = BBox(
            bbox=[
                min(lons) - buffer_degrees, 
                min(lats) - buffer_degrees, 
                max(lons) + buffer_degrees, 
                max(lats) + buffer_degrees
            ], 
            crs=CRS.WGS84
        )
        
        self.size = bbox_to_dimensions(self.bbox, resolution=self.resolution)
        
        print(f"🔧 Small area settings:")
        print(f"   Resolution: {self.resolution}m (higher than standard 10m)")
        print(f"   Buffer added: ~10m around property")
        print(f"   Analysis area: {self.size[0]}x{self.size[1]} pixels")
    
    def _setup_standard_analysis(self):
        """Setup standard analysis for larger areas"""
        self.resolution = self.config_data['image_processing']['resolution']
        self.max_cloud_coverage = self.config_data['image_processing']['max_cloud_coverage']
        
        lons = [coord[0] for coord in self.coordinates]
        lats = [coord[1] for coord in self.coordinates]
        
        self.bbox = BBox(
            bbox=[min(lons), min(lats), max(lons), max(lats)], 
            crs=CRS.WGS84
        )
        
        self.size = bbox_to_dimensions(self.bbox, resolution=self.resolution)
    
    def _create_output_directory(self) -> str:
        """Create output directory for analysis results"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        area_str = f"{self.area_sq_feet:.0f}sqft"
        coord_str = f"lon{self.bbox.min_x:.4f}_lat{self.bbox.min_y:.4f}".replace('.', 'p')
        output_dir = f"small_area_analysis/{timestamp}_{area_str}_{coord_str}"
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
    
    def _setup_logging(self):
        """Setup logging for Sentinel Hub requests and responses"""
        # Create logger
        self.logger = logging.getLogger('sentinel_hub_requests')
        self.logger.setLevel(logging.INFO)
        
        # Create file handler for detailed logs
        log_file = os.path.join(self.output_dir, 'sentinel_hub_requests.log')
        file_handler = logging.FileHandler(log_file, mode='w')
        file_handler.setLevel(logging.INFO)
        
        # Create console handler for important messages
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Store log file path for reference
        self.log_file_path = log_file
        
        print(f"📝 Logging setup complete. Log file: {log_file}")
    
    def _log_request_details(self, request: SentinelHubRequest, request_type: str = "optical"):
        """Log detailed information about Sentinel Hub request"""
        try:
            # Extract request information
            request_info = {
                'timestamp': datetime.now().isoformat(),
                'request_type': request_type,
                'evalscript': request.evalscript,
                'bbox': {
                    'min_x': request.bbox.min_x,
                    'min_y': request.bbox.min_y,
                    'max_x': request.bbox.max_x,
                    'max_y': request.bbox.max_y,
                    'crs': str(request.bbox.crs)
                },
                'size': request.size,
                'data_collection': str(request.input_data[0].data_collection) if request.input_data else None,
                'time_interval': {
                    'start': str(request.input_data[0].time_interval.start) if request.input_data and request.input_data[0].time_interval else None,
                    'end': str(request.input_data[0].time_interval.end) if request.input_data and request.input_data[0].time_interval else None
                },
                'max_cloud_coverage': request.input_data[0].maxcc if request.input_data else None,
                'responses': [{
                    'identifier': resp.identifier,
                    'mime_type': str(resp.mime_type)
                } for resp in request.responses]
            }
            
            # Log request details
            self.logger.info(f"SENTINEL HUB REQUEST - {request_type.upper()}")
            self.logger.info(f"Request Details: {json.dumps(request_info, indent=2)}")
            
            # Log evalscript separately for readability
            self.logger.info(f"Evalscript:\n{request.evalscript}")
            
        except Exception as e:
            self.logger.error(f"Error logging request details: {str(e)}")
    
    def _log_response_details(self, response, request_type: str = "optical"):
        """Log detailed information about Sentinel Hub response"""
        try:
            response_info = {
                'timestamp': datetime.now().isoformat(),
                'request_type': request_type,
                'response_type': type(response).__name__,
                'response_length': len(response) if hasattr(response, '__len__') else 'unknown',
                'success': True if response else False
            }
            
            if hasattr(response, '__len__') and len(response) > 0:
                if hasattr(response[0], 'shape'):
                    response_info['data_shape'] = response[0].shape
                if hasattr(response[0], 'dtype'):
                    response_info['data_type'] = str(response[0].dtype)
                
                # Log data statistics if it's a numpy array
                if isinstance(response[0], np.ndarray):
                    data = response[0]
                    response_info['data_statistics'] = {
                        'min': float(np.min(data)) if data.size > 0 else None,
                        'max': float(np.max(data)) if data.size > 0 else None,
                        'mean': float(np.mean(data)) if data.size > 0 else None,
                        'std': float(np.std(data)) if data.size > 0 else None,
                        'shape': data.shape
                    }
            
            # Log response details
            self.logger.info(f"SENTINEL HUB RESPONSE - {request_type.upper()}")
            self.logger.info(f"Response Details: {json.dumps(response_info, indent=2)}")
            
            # Log any errors or warnings
            if not response:
                self.logger.warning(f"No data received for {request_type} request")
            elif hasattr(response, '__len__') and len(response) == 0:
                self.logger.warning(f"Empty response received for {request_type} request")
            
        except Exception as e:
            self.logger.error(f"Error logging response details: {str(e)}")
    
    def _log_api_usage(self, request, response, request_type: str = "optical"):
        """Log API usage statistics and costs"""
        try:
            # Calculate approximate data size
            data_size_mb = 0
            if response and hasattr(response, '__len__') and len(response) > 0:
                if isinstance(response[0], np.ndarray):
                    data_size_mb = response[0].nbytes / (1024 * 1024)
            
            # Estimate processing units (rough calculation)
            bbox_area = (self.bbox.max_x - self.bbox.min_x) * (self.bbox.max_y - self.bbox.min_y)
            processing_units = bbox_area * 1000  # Rough estimate
            
            usage_info = {
                'timestamp': datetime.now().isoformat(),
                'request_type': request_type,
                'data_size_mb': round(data_size_mb, 2),
                'bbox_area_degrees': round(bbox_area, 8),
                'estimated_processing_units': round(processing_units, 2),
                'resolution': self.resolution,
                'pixel_count': self.size[0] * self.size[1] if hasattr(self, 'size') else 0
            }
            
            self.logger.info(f"API USAGE - {request_type.upper()}")
            self.logger.info(f"Usage Statistics: {json.dumps(usage_info, indent=2)}")
            
        except Exception as e:
            self.logger.error(f"Error logging API usage: {str(e)}")
    
    def analyze_small_area_optical(self, date_range: Tuple[str, str]) -> Dict:
        """Specialized optical analysis for small areas"""
        print(f"🔍 Small Area Optical Analysis: {date_range}")
        
        # Use higher resolution evalscript for small areas
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
            // Enhanced analysis for small areas
            let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
            let ndbi = (sample.B11 - sample.B08) / (sample.B11 + sample.B08);
            let ndwi = (sample.B03 - sample.B08) / (sample.B03 + sample.B08);
            let ndre = (sample.B08 - sample.B11) / (sample.B08 + sample.B11);
            let brightness = (sample.B02 + sample.B03 + sample.B04) / 3;
            let moisture = (sample.B11 - sample.B12) / (sample.B11 + sample.B12);
            
            return [ndvi, ndbi, ndwi, ndre, brightness/3000, moisture];
        }
        """
        
        request = SentinelHubRequest(
            evalscript=evalscript,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L2A,
                    time_interval=date_range,
                    maxcc=self.max_cloud_coverage/100.0
                )
            ],
            responses=[
                SentinelHubRequest.output_response('default', MimeType.TIFF)
            ],
            bbox=self.bbox,
            size=self.size,
            config=self.config
        )
        
        # Log request details
        self._log_request_details(request, "optical")
        
        try:
            # Log the actual API call
            self.logger.info(f"Making Sentinel Hub API call for optical analysis...")
            start_time = datetime.now()
            
            response = request.get_data()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Log response details
            self._log_response_details(response, "optical")
            
            # Log API usage
            self._log_api_usage(request, response, "optical")
            
            # Log timing information
            self.logger.info(f"API call completed in {duration:.2f} seconds")
            
            if response and len(response) > 0:
                data = response[0]
                
                # For small areas, analyze each pixel individually
                if self.is_small_area:
                    results = self._analyze_small_area_pixels(data)
                else:
                    results = self._analyze_standard_area(data)
                
                # Log analysis results summary
                self.logger.info(f"Analysis completed successfully. Results: {json.dumps(results, indent=2)}")
                
                return results
            else:
                error_msg = 'No optical data available'
                self.logger.warning(error_msg)
                return {'error': error_msg}
        except Exception as e:
            error_msg = f'Optical analysis failed: {str(e)}'
            self.logger.error(error_msg)
            return {'error': error_msg}
    
    def _analyze_small_area_pixels(self, data: np.ndarray) -> Dict:
        """Analyze individual pixels for small areas"""
        print(f"🔬 Analyzing individual pixels for small area...")
        
        # Get the center pixel (most representative of the property)
        center_x, center_y = data.shape[0] // 2, data.shape[1] // 2
        
        # Analyze center pixel
        center_pixel = data[center_x, center_y, :]
        
        # Also analyze surrounding pixels for context
        surrounding_pixels = []
        for i in range(max(0, center_x-1), min(data.shape[0], center_x+2)):
            for j in range(max(0, center_y-1), min(data.shape[1], center_y+2)):
                if i != center_x or j != center_y:
                    surrounding_pixels.append(data[i, j, :])
        
        if surrounding_pixels:
            surrounding_data = np.array(surrounding_pixels)
            surrounding_mean = np.mean(surrounding_data, axis=0)
        else:
            surrounding_mean = center_pixel
        
        results = {
            'property_pixel': {
                'ndvi': float(center_pixel[0]),
                'ndbi': float(center_pixel[1]),
                'ndwi': float(center_pixel[2]),
                'ndre': float(center_pixel[3]),
                'brightness': float(center_pixel[4]),
                'moisture': float(center_pixel[5])
            },
            'surrounding_area': {
                'ndvi': float(surrounding_mean[0]),
                'ndbi': float(surrounding_mean[1]),
                'ndwi': float(surrounding_mean[2]),
                'ndre': float(surrounding_mean[3]),
                'brightness': float(surrounding_mean[4]),
                'moisture': float(surrounding_mean[5])
            },
            'analysis_method': 'pixel-level (small area)',
            'pixel_count': len(surrounding_pixels) + 1,
            'interpretation': self._interpret_small_area_results(center_pixel, surrounding_mean)
        }
        
        return results
    
    def _analyze_standard_area(self, data: np.ndarray) -> Dict:
        """Standard analysis for larger areas"""
        results = {
            'ndvi_mean': float(np.mean(data[:, :, 0])),
            'ndbi_mean': float(np.mean(data[:, :, 1])),
            'ndwi_mean': float(np.mean(data[:, :, 2])),
            'ndre_mean': float(np.mean(data[:, :, 3])),
            'brightness_mean': float(np.mean(data[:, :, 4])),
            'moisture_mean': float(np.mean(data[:, :, 5])),
            'analysis_method': 'area-average (standard)',
            'pixel_count': data.shape[0] * data.shape[1],
            'interpretation': self._interpret_standard_results(data)
        }
        
        return results
    
    def _interpret_small_area_results(self, property_pixel: np.ndarray, surrounding_mean: np.ndarray) -> Dict:
        """Interpret results for small area analysis"""
        interpretation = {
            'property_characteristics': [],
            'comparison_with_surroundings': [],
            'recommendations': []
        }
        
        # Property characteristics
        ndvi = property_pixel[0]
        ndbi = property_pixel[1]
        ndwi = property_pixel[2]
        
        if ndvi > 0.6:
            interpretation['property_characteristics'].append("Excellent vegetation health")
        elif ndvi > 0.4:
            interpretation['property_characteristics'].append("Good vegetation health")
        elif ndvi > 0.2:
            interpretation['property_characteristics'].append("Moderate vegetation health")
        else:
            interpretation['property_characteristics'].append("Poor vegetation health")
        
        if ndbi > 0.2:
            interpretation['property_characteristics'].append("High built-up area")
        elif ndbi > 0.1:
            interpretation['property_characteristics'].append("Moderate built-up area")
        else:
            interpretation['property_characteristics'].append("Low built-up area")
        
        if ndwi > 0.3:
            interpretation['property_characteristics'].append("High water presence")
        elif ndwi > 0.1:
            interpretation['property_characteristics'].append("Moderate water presence")
        else:
            interpretation['property_characteristics'].append("Low water presence")
        
        # Compare with surroundings
        ndvi_diff = ndvi - surrounding_mean[0]
        ndbi_diff = ndbi - surrounding_mean[1]
        ndwi_diff = ndwi - surrounding_mean[2]
        
        if abs(ndvi_diff) > 0.1:
            if ndvi_diff > 0:
                interpretation['comparison_with_surroundings'].append("Better vegetation than surroundings")
            else:
                interpretation['comparison_with_surroundings'].append("Poorer vegetation than surroundings")
        
        if abs(ndbi_diff) > 0.1:
            if ndbi_diff > 0:
                interpretation['comparison_with_surroundings'].append("More built-up than surroundings")
            else:
                interpretation['comparison_with_surroundings'].append("Less built-up than surroundings")
        
        # Recommendations
        if ndvi < 0.2:
            interpretation['recommendations'].append("Consider vegetation improvement")
        
        if ndbi > 0.3:
            interpretation['recommendations'].append("High development - monitor for changes")
        
        return interpretation
    
    def _interpret_standard_results(self, data: np.ndarray) -> Dict:
        """Interpret results for standard area analysis"""
        ndvi_mean = np.mean(data[:, :, 0])
        ndbi_mean = np.mean(data[:, :, 1])
        ndwi_mean = np.mean(data[:, :, 2])
        
        interpretation = {
            'vegetation_health': self._interpret_vegetation_health(ndvi_mean),
            'construction_activity': self._interpret_construction(ndbi_mean),
            'water_presence': self._interpret_water(ndwi_mean)
        }
        
        return interpretation
    
    def _interpret_vegetation_health(self, ndvi: float) -> str:
        """Interpret vegetation health from NDVI"""
        if ndvi > 0.6:
            return "Excellent vegetation health"
        elif ndvi > 0.4:
            return "Good vegetation health"
        elif ndvi > 0.2:
            return "Moderate vegetation health"
        else:
            return "Poor vegetation health"
    
    def _interpret_construction(self, ndbi: float) -> str:
        """Interpret construction activity from NDBI"""
        if ndbi > 0.2:
            return "High construction activity"
        elif ndbi > 0.1:
            return "Moderate construction activity"
        elif ndbi > 0.05:
            return "Low construction activity"
        else:
            return "No construction activity"
    
    def _interpret_water(self, ndwi: float) -> str:
        """Interpret water presence from NDWI"""
        if ndwi > 0.3:
            return "High water presence"
        elif ndwi > 0.1:
            return "Moderate water presence"
        elif ndwi > 0.0:
            return "Low water presence"
        else:
            return "No water detected"
    
    def get_alternative_data_sources(self) -> Dict:
        """Get recommendations for alternative data sources for small areas"""
        recommendations = {
            'high_resolution_satellites': [
                {
                    'name': 'Planet Labs',
                    'resolution': '3-5m',
                    'coverage': 'Daily',
                    'best_for': 'Small area monitoring, construction tracking'
                },
                {
                    'name': 'Maxar',
                    'resolution': '0.3-1.5m',
                    'coverage': 'On-demand',
                    'best_for': 'Very detailed analysis, infrastructure monitoring'
                },
                {
                    'name': 'Airbus Pleiades',
                    'resolution': '0.5-2m',
                    'coverage': 'On-demand',
                    'best_for': 'High-resolution property analysis'
                }
            ],
            'drone_imagery': {
                'resolution': '1-10cm',
                'coverage': 'On-demand',
                'best_for': 'Very detailed property analysis, construction monitoring',
                'limitations': 'Requires drone access, weather dependent'
            },
            'aerial_photography': {
                'resolution': '10-50cm',
                'coverage': 'Periodic',
                'best_for': 'Property assessment, historical comparison',
                'limitations': 'Limited temporal coverage'
            }
        }
        
        return recommendations
    
    def analyze_small_area(self, date_range: Tuple[str, str]) -> Dict:
        """Perform comprehensive small area analysis"""
        print(f"🏠 Starting Small Area Analysis")
        print(f"📅 Analysis Period: {date_range}")
        print(f"📏 Property Size: {self.area_sq_feet:.1f} sq ft")
        
        results = {
            'analysis_timestamp': datetime.now().isoformat(),
            'property_coordinates': self.coordinates,
            'property_area': {
                'square_feet': self.area_sq_feet,
                'square_meters': self.area_sq_meters
            },
            'bounding_box': {
                'min_lon': self.bbox.min_x,
                'min_lat': self.bbox.min_y,
                'max_lon': self.bbox.max_x,
                'max_lat': self.bbox.max_y
            },
            'analysis_period': date_range,
            'analysis_method': 'small_area_specialized' if self.is_small_area else 'standard',
            'limitations': self._get_limitations()
        }
        
        # Perform optical analysis
        optical_results = self.analyze_small_area_optical(date_range)
        if 'error' not in optical_results:
            results['optical_analysis'] = optical_results
        else:
            results['optical_analysis'] = {'error': optical_results['error']}
        
        # Add alternative data source recommendations
        results['alternative_data_sources'] = self.get_alternative_data_sources()
        
        # Save results
        self._save_small_area_results(results)
        
        return results
    
    def _get_limitations(self) -> List[str]:
        """Get limitations for small area analysis"""
        limitations = []
        
        if self.area_sq_meters < 100:
            limitations.append("Property smaller than 1 Sentinel-2 pixel (100 sq m)")
        elif self.area_sq_meters < 1000:
            limitations.append("Property smaller than 10 Sentinel-2 pixels")
        
        limitations.append("Limited statistical significance due to small sample size")
        limitations.append("Weather and cloud coverage can significantly impact results")
        limitations.append("Temporal analysis may be limited by data availability")
        
        return limitations
    
    def _save_small_area_results(self, results: Dict):
        """Save small area analysis results"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save JSON
        json_file = os.path.join(self.output_dir, f"{timestamp}_small_area_analysis.json")
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Save CSV
        csv_file = os.path.join(self.output_dir, f"{timestamp}_small_area_analysis.csv")
        self._save_small_area_csv(results, csv_file)
        
        print(f"📁 Small area analysis saved:")
        print(f"   JSON: {json_file}")
        print(f"   CSV: {csv_file}")
        print(f"   LOG: {self.log_file_path}")
    
    def _save_small_area_csv(self, results: Dict, filepath: str):
        """Save small area results as CSV"""
        import csv
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Metadata
            writer.writerow(["SMALL AREA PROPERTY ANALYSIS", ""])
            writer.writerow(["Timestamp", results.get('analysis_timestamp', 'N/A')])
            writer.writerow(["Property Area (sq ft)", f"{results.get('property_area', {}).get('square_feet', 0):.1f}"])
            writer.writerow(["Property Area (sq m)", f"{results.get('property_area', {}).get('square_meters', 0):.1f}"])
            writer.writerow(["Analysis Method", results.get('analysis_method', 'N/A')])
            writer.writerow(["Analysis Period", str(results.get('analysis_period', 'N/A'))])
            writer.writerow(["", ""])
            
            # Limitations
            writer.writerow(["LIMITATIONS", ""])
            for limitation in results.get('limitations', []):
                writer.writerow(["", limitation])
            writer.writerow(["", ""])
            
            # Optical Analysis
            if 'optical_analysis' in results and 'error' not in results['optical_analysis']:
                optical = results['optical_analysis']
                writer.writerow(["OPTICAL ANALYSIS", ""])
                
                if 'property_pixel' in optical:
                    # Small area analysis
                    prop_pixel = optical['property_pixel']
                    writer.writerow(["Property Pixel Values", ""])
                    writer.writerow(["NDVI", f"{prop_pixel.get('ndvi', 0):.4f}"])
                    writer.writerow(["NDBI", f"{prop_pixel.get('ndbi', 0):.4f}"])
                    writer.writerow(["NDWI", f"{prop_pixel.get('ndwi', 0):.4f}"])
                    writer.writerow(["NDRE", f"{prop_pixel.get('ndre', 0):.4f}"])
                    writer.writerow(["Brightness", f"{prop_pixel.get('brightness', 0):.4f}"])
                    writer.writerow(["Moisture", f"{prop_pixel.get('moisture', 0):.4f}"])
                    writer.writerow(["", ""])
                    
                    # Surrounding area
                    surr_area = optical['surrounding_area']
                    writer.writerow(["Surrounding Area Values", ""])
                    writer.writerow(["NDVI", f"{surr_area.get('ndvi', 0):.4f}"])
                    writer.writerow(["NDBI", f"{surr_area.get('ndbi', 0):.4f}"])
                    writer.writerow(["NDWI", f"{surr_area.get('ndwi', 0):.4f}"])
                    writer.writerow(["", ""])
                    
                    # Interpretation
                    if 'interpretation' in optical:
                        interp = optical['interpretation']
                        writer.writerow(["Property Characteristics", ""])
                        for char in interp.get('property_characteristics', []):
                            writer.writerow(["", char])
                        
                        writer.writerow(["Comparison with Surroundings", ""])
                        for comp in interp.get('comparison_with_surroundings', []):
                            writer.writerow(["", comp])
                        
                        writer.writerow(["Recommendations", ""])
                        for rec in interp.get('recommendations', []):
                            writer.writerow(["", rec])
                else:
                    # Standard analysis
                    writer.writerow(["NDVI Mean", f"{optical.get('ndvi_mean', 0):.4f}"])
                    writer.writerow(["NDBI Mean", f"{optical.get('ndbi_mean', 0):.4f}"])
                    writer.writerow(["NDWI Mean", f"{optical.get('ndwi_mean', 0):.4f}"])
                    writer.writerow(["Analysis Method", optical.get('analysis_method', 'N/A')])
                    writer.writerow(["Pixel Count", optical.get('pixel_count', 0)])
            
            # Alternative Data Sources
            if 'alternative_data_sources' in results:
                writer.writerow(["", ""])
                writer.writerow(["ALTERNATIVE DATA SOURCES", ""])
                writer.writerow(["For better small area analysis, consider:", ""])
                
                for satellite in results['alternative_data_sources']['high_resolution_satellites']:
                    writer.writerow(["", f"{satellite['name']} ({satellite['resolution']} resolution)"])
                    writer.writerow(["", f"  Coverage: {satellite['coverage']}"])
                    writer.writerow(["", f"  Best for: {satellite['best_for']}"])
                    writer.writerow(["", ""])

def main():
    """Main function to demonstrate small area analysis"""
    print("🏠 Small Area Property Analysis Demo")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = SmallAreaAnalyzer()
    
    # Define analysis period
    date_range = ("2024-01-01", "2024-01-31")
    
    # Perform small area analysis
    results = analyzer.analyze_small_area(date_range)
    
    # Display summary
    print("\n📊 SMALL AREA ANALYSIS SUMMARY:")
    print(f"Property Size: {results['property_area']['square_feet']:.1f} sq ft")
    print(f"Analysis Method: {results['analysis_method']}")
    
    if 'optical_analysis' in results and 'error' not in results['optical_analysis']:
        optical = results['optical_analysis']
        
        if 'interpretation' in optical:
            interp = optical['interpretation']
            print(f"\n🏠 Property Characteristics:")
            for char in interp.get('property_characteristics', []):
                print(f"   • {char}")
            
            print(f"\n🔄 Comparison with Surroundings:")
            for comp in interp.get('comparison_with_surroundings', []):
                print(f"   • {comp}")
            
            print(f"\n💡 Recommendations:")
            for rec in interp.get('recommendations', []):
                print(f"   • {rec}")
    
    print(f"\n⚠️ Limitations:")
    for limitation in results.get('limitations', []):
        print(f"   • {limitation}")
    
    print(f"\n✅ Analysis completed! Check the output directory for detailed results.")
    print(f"📝 Sentinel Hub request/response logs saved to: {analyzer.log_file_path}")

if __name__ == "__main__":
    main()
