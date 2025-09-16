import yaml
import os
from typing import Dict, Any, List, Optional
from datetime import datetime


class ConfigManager:
    """
    Configuration manager for satellite analysis parameters
    """
    
    def __init__(self, config_file: str = "config.yaml"):
        """
        Initialize configuration manager
        
        Args:
            config_file: Path to the configuration YAML file
        """
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file
        
        Returns:
            Dictionary containing configuration parameters
        """
        try:
            with open(self.config_file, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
            print(f"✅ Configuration loaded from {self.config_file}")
            return config
        except FileNotFoundError:
            print(f"❌ Configuration file {self.config_file} not found")
            raise
        except yaml.YAMLError as e:
            print(f"❌ Error parsing configuration file: {e}")
            raise
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Args:
            key_path: Dot-separated path to configuration key (e.g., 'api_credentials.sentinel_hub.client_id')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            if default is not None:
                return default
            raise KeyError(f"Configuration key '{key_path}' not found")
    
    def get_api_credentials(self) -> Dict[str, str]:
        """
        Get Sentinel Hub API credentials
        
        Returns:
            Dictionary with client_id, client_secret, and base_url
        """
        return {
            'client_id': self.get('api_credentials.sentinel_hub.client_id'),
            'client_secret': self.get('api_credentials.sentinel_hub.client_secret'),
            'base_url': self.get('api_credentials.sentinel_hub.base_url')
        }
    
    def get_analysis_params(self) -> Dict[str, Any]:
        """
        Get analysis parameters
        
        Returns:
            Dictionary with analysis parameters
        """
        return {
            'square_size_acres': self.get('analysis.square_size_acres'),
            'region_type': self.get('analysis.region_type'),
            'min_quality_score': self.get('analysis.quality.min_quality_score'),
            'min_temporal_consistency': self.get('analysis.quality.min_temporal_consistency')
        }
    
    def get_sentinel_hub_config(self) -> Dict[str, Any]:
        """
        Get Sentinel Hub configuration
        
        Returns:
            Dictionary with Sentinel Hub settings
        """
        return {
            'data_source_type': self.get('sentinel_hub.data_source.type'),
            'crs': self.get('sentinel_hub.data_source.crs'),
            'width': self.get('sentinel_hub.image_settings.width'),
            'height': self.get('sentinel_hub.image_settings.height'),
            'timeout': self.get('sentinel_hub.image_settings.timeout_seconds'),
            'max_cloud_coverage': self.get('sentinel_hub.data_filter.max_cloud_coverage'),
            'mosaicking_order': self.get('sentinel_hub.data_filter.mosaicking_order')
        }
    
    def get_custom_periods(self) -> Optional[List[Dict[str, str]]]:
        """
        Get custom date periods if enabled
        
        Returns:
            List of period dictionaries or None if disabled
        """
        if self.get('custom_periods.enabled', False):
            return self.get('custom_periods.periods')
        return None
    
    def get_default_periods_config(self) -> Dict[str, int]:
        """
        Get default periods configuration
        
        Returns:
            Dictionary with default period settings
        """
        return {
            'time_range_days': self.get('default_periods.time_range_days'),
            'number_of_periods': self.get('default_periods.number_of_periods'),
            'period_overlap_days': self.get('default_periods.period_overlap_days')
        }
    
    def get_thresholds(self, region_type: str = None) -> Dict[str, float]:
        """
        Get thresholds for significance determination
        
        Args:
            region_type: Region type ('urban', 'rural', 'mixed')
            
        Returns:
            Dictionary with thresholds
        """
        if region_type is None:
            region_type = self.get('analysis.region_type')
        
        thresholds = self.get(f'thresholds.{region_type}')
        max_std_dev = self.get('thresholds.max_std_dev')
        
        return {
            'ndvi': thresholds['ndvi'],
            'ndbi': thresholds['ndbi'],
            'ndwi': thresholds['ndwi'],
            'max_std_dev_ndvi': max_std_dev['ndvi'],
            'max_std_dev_ndbi': max_std_dev['ndbi'],
            'max_std_dev_ndwi': max_std_dev['ndwi']
        }
    
    def get_inference_thresholds(self) -> Dict[str, Dict[str, float]]:
        """
        Get inference thresholds for all indices
        
        Returns:
            Dictionary with inference thresholds
        """
        return {
            'ndvi': self.get('ndvi_inference'),
            'ndbi': self.get('ndbi_inference'),
            'ndwi': self.get('ndwi_inference')
        }
    
    def get_output_config(self) -> Dict[str, Any]:
        """
        Get output configuration
        
        Returns:
            Dictionary with output settings
        """
        return {
            'base_directory': self.get('output.base_directory'),
            'timestamp_format': self.get('output.timestamp_format'),
            'files': self.get('output.files'),
            'kml_styles': self.get('output.kml_styles')
        }
    
    def get_sample_data(self) -> Dict[str, Any]:
        """
        Get sample input data
        
        Returns:
            Dictionary with sample data
        """
        return self.get('sample_data')
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get logging configuration
        
        Returns:
            Dictionary with logging settings
        """
        return self.get('logging')
    
    def validate_config(self) -> bool:
        """
        Validate configuration file
        
        Returns:
            True if valid, False otherwise
        """
        required_keys = [
            'api_credentials.sentinel_hub.client_id',
            'api_credentials.sentinel_hub.client_secret',
            'analysis.square_size_acres',
            'sentinel_hub.data_source.type'
        ]
        
        for key in required_keys:
            try:
                self.get(key)
            except KeyError:
                print(f"❌ Missing required configuration key: {key}")
                return False
        
        # Validate square size
        square_size = self.get('analysis.square_size_acres')
        if square_size <= 0:
            print("❌ Square size must be greater than 0")
            return False
        
        # Validate region type
        region_type = self.get('analysis.region_type')
        if region_type not in ['urban', 'rural', 'mixed']:
            print("❌ Region type must be 'urban', 'rural', or 'mixed'")
            return False
        
        print("✅ Configuration validation passed")
        return True
    
    def print_config_summary(self):
        """
        Print a summary of the current configuration
        """
        print("\n" + "="*60)
        print("📋 CONFIGURATION SUMMARY")
        print("="*60)
        
        # Analysis parameters
        analysis_params = self.get_analysis_params()
        print(f"🔍 Analysis Parameters:")
        print(f"  - Square Size: {analysis_params['square_size_acres']} acres")
        print(f"  - Region Type: {analysis_params['region_type']}")
        print(f"  - Min Quality Score: {analysis_params['min_quality_score']}")
        
        # Sentinel Hub settings
        sh_config = self.get_sentinel_hub_config()
        print(f"\n🛰️  Sentinel Hub Settings:")
        print(f"  - Data Source: {sh_config['data_source_type']}")
        print(f"  - Image Size: {sh_config['width']}x{sh_config['height']}")
        print(f"  - Max Cloud Coverage: {sh_config['max_cloud_coverage']}%")
        
        # Date periods
        custom_periods = self.get_custom_periods()
        if custom_periods:
            print(f"\n📅 Custom Date Periods:")
            for i, period in enumerate(custom_periods, 1):
                print(f"  - Period {i}: {period['start_date']} to {period['end_date']}")
        else:
            default_config = self.get_default_periods_config()
            print(f"\n📅 Default Date Periods:")
            print(f"  - Time Range: {default_config['time_range_days']} days")
            print(f"  - Number of Periods: {default_config['number_of_periods']}")
        
        # Output settings
        output_config = self.get_output_config()
        print(f"\n📁 Output Settings:")
        print(f"  - Base Directory: {output_config['base_directory']}")
        print(f"  - Timestamp Format: {output_config['timestamp_format']}")
        
        print("="*60 + "\n")
