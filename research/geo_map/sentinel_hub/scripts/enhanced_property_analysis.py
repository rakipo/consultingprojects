#!/usr/bin/env python3
"""
Enhanced Property Analysis using Multiple Sentinel Hub APIs
This script demonstrates various APIs for comprehensive property monitoring
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
import os
import yaml

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

class EnhancedPropertyAnalyzer:
    def __init__(self, config_path: str = "sentinel_hub_config.yml", 
                 user_config_path: str = "sentinel_hub_user_config.yaml"):
        """Initialize enhanced property analyzer with multiple data sources"""
        
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
        
        self.bbox = BBox(
            bbox=[min(lons), min(lats), max(lons), max(lats)], 
            crs=CRS.WGS84
        )
        
        # Analysis parameters
        self.resolution = self.config_data['image_processing']['resolution']
        self.max_cloud_coverage = self.config_data['image_processing']['max_cloud_coverage']
        self.size = bbox_to_dimensions(self.bbox, resolution=self.resolution)
        
        # Create output directory
        self.output_dir = self._create_output_directory()
        
        print(f"🏠 Enhanced Property Analyzer Initialized")
        print(f"📍 Property Location: {self.bbox}")
        print(f"📐 Analysis Area: {self.size[0]}x{self.size[1]} pixels")
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
        """Create output directory for analysis results"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        coord_str = f"lon{self.bbox.min_x:.4f}_lat{self.bbox.min_y:.4f}".replace('.', 'p')
        output_dir = f"enhanced_analysis_results/{timestamp}_{coord_str}"
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
    
    def analyze_optical_property(self, date_range: Tuple[str, str]) -> Dict:
        """Analyze property using Sentinel-2 optical imagery"""
        print(f"🔍 Optical Analysis: {date_range}")
        
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
            // Enhanced property analysis indices
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
        
        try:
            response = request.get_data()
            if response and len(response) > 0:
                data = response[0]
                
                # Calculate statistics
                results = {
                    'ndvi_mean': float(np.mean(data[:, :, 0])),
                    'ndbi_mean': float(np.mean(data[:, :, 1])),
                    'ndwi_mean': float(np.mean(data[:, :, 2])),
                    'ndre_mean': float(np.mean(data[:, :, 3])),
                    'brightness_mean': float(np.mean(data[:, :, 4])),
                    'moisture_mean': float(np.mean(data[:, :, 5])),
                    'vegetation_health': self._interpret_vegetation_health(float(np.mean(data[:, :, 0]))),
                    'construction_activity': self._interpret_construction(float(np.mean(data[:, :, 1]))),
                    'water_presence': self._interpret_water(float(np.mean(data[:, :, 2])))
                }
                
                return results
            else:
                return {'error': 'No optical data available'}
        except Exception as e:
            return {'error': f'Optical analysis failed: {str(e)}'}
    
    def analyze_radar_property(self, date_range: Tuple[str, str]) -> Dict:
        """Analyze property using Sentinel-1 radar imagery"""
        print(f"📡 Radar Analysis: {date_range}")
        
        evalscript = """
        //VERSION=3
        function setup() {
            return {
                input: [{
                    bands: ["VV", "VH"],
                    units: "NATURAL"
                }],
                output: { bands: 3 }
            };
        }
        
        function evaluatePixel(sample) {
            // Radar-based property analysis
            let vv = sample.VV;
            let vh = sample.VH;
            
            // Radar vegetation index
            let rvi = 4 * vh / (vv + vh);
            
            // Radar built-up index
            let rbi = (vv - vh) / (vv + vh);
            
            // Surface roughness (simplified)
            let roughness = Math.log(vv / vh);
            
            return [rvi, rbi, roughness];
        }
        """
        
        request = SentinelHubRequest(
            evalscript=evalscript,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL1_IW,
                    time_interval=date_range
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
                data = response[0]
                
                results = {
                    'radar_vegetation_index': float(np.mean(data[:, :, 0])),
                    'radar_builtup_index': float(np.mean(data[:, :, 1])),
                    'surface_roughness': float(np.mean(data[:, :, 2])),
                    'construction_detection': self._interpret_radar_construction(float(np.mean(data[:, :, 1]))),
                    'surface_changes': self._interpret_surface_changes(float(np.mean(data[:, :, 2])))
                }
                
                return results
            else:
                return {'error': 'No radar data available'}
        except Exception as e:
            return {'error': f'Radar analysis failed: {str(e)}'}
    
    def get_elevation_data(self) -> Dict:
        """Get elevation data for the property"""
        print(f"🏔️ Elevation Analysis")
        
        evalscript = """
        //VERSION=3
        function setup() {
            return {
                input: [{
                    bands: ["DEM"],
                    units: "METERS"
                }],
                output: { bands: 1 }
            };
        }
        
        function evaluatePixel(sample) {
            return [sample.DEM];
        }
        """
        
        request = SentinelHubRequest(
            evalscript=evalscript,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.DEM_COPERNICUS_30
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
                data = response[0]
                
                elevation = float(np.mean(data))
                slope = self._calculate_slope(data)
                
                results = {
                    'elevation_meters': elevation,
                    'slope_degrees': slope,
                    'terrain_type': self._interpret_terrain(elevation, slope),
                    'flood_risk': self._assess_flood_risk(elevation, slope)
                }
                
                return results
            else:
                return {'error': 'No elevation data available'}
        except Exception as e:
            return {'error': f'Elevation analysis failed: {str(e)}'}
    
    def _calculate_slope(self, elevation_data: np.ndarray) -> float:
        """Calculate average slope from elevation data"""
        try:
            # Simplified slope calculation
            return float(np.std(elevation_data)) * 0.1  # Approximate slope
        except:
            return 0.0
    
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
    
    def _interpret_radar_construction(self, rbi: float) -> str:
        """Interpret construction from radar data"""
        if rbi > 0.3:
            return "High radar reflection (possible construction)"
        elif rbi > 0.1:
            return "Moderate radar reflection"
        else:
            return "Low radar reflection"
    
    def _interpret_surface_changes(self, roughness: float) -> str:
        """Interpret surface changes from radar"""
        if abs(roughness) > 2.0:
            return "Significant surface changes detected"
        elif abs(roughness) > 1.0:
            return "Moderate surface changes"
        else:
            return "Minimal surface changes"
    
    def _interpret_terrain(self, elevation: float, slope: float) -> str:
        """Interpret terrain type"""
        if slope > 15:
            return "Steep terrain"
        elif slope > 5:
            return "Moderate slope"
        else:
            return "Flat terrain"
    
    def _assess_flood_risk(self, elevation: float, slope: float) -> str:
        """Assess flood risk"""
        if elevation < 10 and slope < 2:
            return "High flood risk"
        elif elevation < 50 and slope < 5:
            return "Moderate flood risk"
        else:
            return "Low flood risk"
    
    def comprehensive_property_analysis(self, date_range: Tuple[str, str]) -> Dict:
        """Perform comprehensive property analysis using multiple data sources"""
        print(f"🏠 Starting Comprehensive Property Analysis")
        print(f"📅 Analysis Period: {date_range}")
        
        results = {
            'analysis_timestamp': datetime.now().isoformat(),
            'property_coordinates': self.coordinates,
            'bounding_box': {
                'min_lon': self.bbox.min_x,
                'min_lat': self.bbox.min_y,
                'max_lon': self.bbox.max_x,
                'max_lat': self.bbox.max_y
            },
            'analysis_period': date_range,
            'data_sources': []
        }
        
        # 1. Optical Analysis (Sentinel-2)
        optical_results = self.analyze_optical_property(date_range)
        if 'error' not in optical_results:
            results['optical_analysis'] = optical_results
            results['data_sources'].append('Sentinel-2 L2A')
        
        # 2. Radar Analysis (Sentinel-1)
        radar_results = self.analyze_radar_property(date_range)
        if 'error' not in radar_results:
            results['radar_analysis'] = radar_results
            results['data_sources'].append('Sentinel-1 IW')
        
        # 3. Elevation Analysis (DEM)
        elevation_results = self.get_elevation_data()
        if 'error' not in elevation_results:
            results['elevation_analysis'] = elevation_results
            results['data_sources'].append('DEM Copernicus 30')
        
        # 4. Property Summary
        results['property_summary'] = self._generate_property_summary(results)
        
        # Save results
        self._save_comprehensive_results(results)
        
        return results
    
    def _generate_property_summary(self, results: Dict) -> Dict:
        """Generate comprehensive property summary"""
        summary = {
            'property_characteristics': [],
            'recommendations': [],
            'risk_assessment': {}
        }
        
        # Analyze optical data
        if 'optical_analysis' in results:
            optical = results['optical_analysis']
            
            if 'vegetation_health' in optical:
                summary['property_characteristics'].append(optical['vegetation_health'])
            
            if 'construction_activity' in optical:
                summary['property_characteristics'].append(optical['construction_activity'])
            
            if 'water_presence' in optical:
                summary['property_characteristics'].append(optical['water_presence'])
        
        # Analyze radar data
        if 'radar_analysis' in results:
            radar = results['radar_analysis']
            
            if 'construction_detection' in radar:
                summary['property_characteristics'].append(radar['construction_detection'])
            
            if 'surface_changes' in radar:
                summary['property_characteristics'].append(radar['surface_changes'])
        
        # Analyze elevation data
        if 'elevation_analysis' in results:
            elevation = results['elevation_analysis']
            
            if 'terrain_type' in elevation:
                summary['property_characteristics'].append(elevation['terrain_type'])
            
            if 'flood_risk' in elevation:
                summary['risk_assessment']['flood_risk'] = elevation['flood_risk']
        
        # Generate recommendations
        if 'optical_analysis' in results:
            ndvi = results['optical_analysis'].get('ndvi_mean', 0)
            if ndvi < 0.2:
                summary['recommendations'].append("Consider vegetation improvement measures")
        
        if 'elevation_analysis' in results:
            flood_risk = results['elevation_analysis'].get('flood_risk', 'Unknown')
            if 'High' in flood_risk:
                summary['recommendations'].append("Implement flood protection measures")
        
        return summary
    
    def _save_comprehensive_results(self, results: Dict):
        """Save comprehensive analysis results"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save JSON
        json_file = os.path.join(self.output_dir, f"{timestamp}_comprehensive_property_analysis.json")
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Save CSV
        csv_file = os.path.join(self.output_dir, f"{timestamp}_comprehensive_property_analysis.csv")
        self._save_comprehensive_csv(results, csv_file)
        
        print(f"📁 Comprehensive analysis saved:")
        print(f"   JSON: {json_file}")
        print(f"   CSV: {csv_file}")
    
    def _save_comprehensive_csv(self, results: Dict, filepath: str):
        """Save comprehensive results as CSV"""
        import csv
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Metadata
            writer.writerow(["COMPREHENSIVE PROPERTY ANALYSIS", ""])
            writer.writerow(["Timestamp", results.get('analysis_timestamp', 'N/A')])
            writer.writerow(["Coordinates", str(results.get('property_coordinates', 'N/A'))])
            writer.writerow(["Analysis Period", str(results.get('analysis_period', 'N/A'))])
            writer.writerow(["Data Sources", ", ".join(results.get('data_sources', []))])
            writer.writerow(["", ""])
            
            # Optical Analysis
            if 'optical_analysis' in results:
                writer.writerow(["OPTICAL ANALYSIS (Sentinel-2)", ""])
                optical = results['optical_analysis']
                writer.writerow(["NDVI", f"{optical.get('ndvi_mean', 0):.4f}"])
                writer.writerow(["NDBI", f"{optical.get('ndbi_mean', 0):.4f}"])
                writer.writerow(["NDWI", f"{optical.get('ndwi_mean', 0):.4f}"])
                writer.writerow(["Vegetation Health", optical.get('vegetation_health', 'N/A')])
                writer.writerow(["Construction Activity", optical.get('construction_activity', 'N/A')])
                writer.writerow(["Water Presence", optical.get('water_presence', 'N/A')])
                writer.writerow(["", ""])
            
            # Radar Analysis
            if 'radar_analysis' in results:
                writer.writerow(["RADAR ANALYSIS (Sentinel-1)", ""])
                radar = results['radar_analysis']
                writer.writerow(["Radar Vegetation Index", f"{radar.get('radar_vegetation_index', 0):.4f}"])
                writer.writerow(["Radar Built-up Index", f"{radar.get('radar_builtup_index', 0):.4f}"])
                writer.writerow(["Surface Roughness", f"{radar.get('surface_roughness', 0):.4f}"])
                writer.writerow(["Construction Detection", radar.get('construction_detection', 'N/A')])
                writer.writerow(["Surface Changes", radar.get('surface_changes', 'N/A')])
                writer.writerow(["", ""])
            
            # Elevation Analysis
            if 'elevation_analysis' in results:
                writer.writerow(["ELEVATION ANALYSIS (DEM)", ""])
                elevation = results['elevation_analysis']
                writer.writerow(["Elevation (meters)", f"{elevation.get('elevation_meters', 0):.2f}"])
                writer.writerow(["Slope (degrees)", f"{elevation.get('slope_degrees', 0):.2f}"])
                writer.writerow(["Terrain Type", elevation.get('terrain_type', 'N/A')])
                writer.writerow(["Flood Risk", elevation.get('flood_risk', 'N/A')])
                writer.writerow(["", ""])
            
            # Property Summary
            if 'property_summary' in results:
                writer.writerow(["PROPERTY SUMMARY", ""])
                summary = results['property_summary']
                
                writer.writerow(["Property Characteristics", ""])
                for char in summary.get('property_characteristics', []):
                    writer.writerow(["", char])
                
                writer.writerow(["Risk Assessment", ""])
                for risk_type, risk_level in summary.get('risk_assessment', {}).items():
                    writer.writerow(["", f"{risk_type}: {risk_level}"])
                
                writer.writerow(["Recommendations", ""])
                for rec in summary.get('recommendations', []):
                    writer.writerow(["", rec])

def main():
    """Main function to demonstrate enhanced property analysis"""
    print("🏠 Enhanced Property Analysis Demo")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = EnhancedPropertyAnalyzer()
    
    # Define analysis period
    date_range = ("2024-01-01", "2024-01-31")
    
    # Perform comprehensive analysis
    results = analyzer.comprehensive_property_analysis(date_range)
    
    # Display summary
    print("\n📊 ANALYSIS SUMMARY:")
    print(f"Data Sources Used: {', '.join(results.get('data_sources', []))}")
    
    if 'property_summary' in results:
        summary = results['property_summary']
        print(f"\n🏠 Property Characteristics:")
        for char in summary.get('property_characteristics', []):
            print(f"   • {char}")
        
        print(f"\n⚠️ Risk Assessment:")
        for risk_type, risk_level in summary.get('risk_assessment', {}).items():
            print(f"   • {risk_type}: {risk_level}")
        
        print(f"\n💡 Recommendations:")
        for rec in summary.get('recommendations', []):
            print(f"   • {rec}")
    
    print(f"\n✅ Analysis completed! Check the output directory for detailed results.")

if __name__ == "__main__":
    main()
