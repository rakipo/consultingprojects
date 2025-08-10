#!/usr/bin/env python3
"""
Test script to demonstrate the new output functionality with timestamps and coordinates
"""

import os
import sys
from datetime import datetime, timedelta
import json

# Add the current directory to the path so we can import the main module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from claude_sentinel_hub_image_diff_v11 import SentinelHubLandMonitor

def test_output_functionality():
    """Test the new output functionality"""
    
    print("🧪 Testing Output Functionality with Timestamps and Coordinates")
    print("=" * 60)
    
    try:
        # Initialize the monitoring system
        print("📁 Initializing monitoring system...")
        monitor = SentinelHubLandMonitor(
            main_config_path="sentinel_hub_config.yml",
            user_config_path="sentinel_hub_user_config.yaml"
        )
        
        print(f"📍 Coordinates: {monitor.coordinates}")
        print(f"📦 Bounding Box: {monitor.bbox}")
        print(f"📁 Output Directory: {monitor.output_dir}")
        
        # Test coordinate string generation
        coord_str = monitor._get_coordinate_string()
        print(f"🔢 Coordinate String: {coord_str}")
        
        # Test timestamp generation
        timestamp = monitor._get_timestamp_string()
        print(f"⏰ Timestamp: {timestamp}")
        
        # Create a sample analysis result
        sample_result = {
            "before_period": ("2023-01-01", "2023-01-31"),
            "after_period": ("2024-01-01", "2024-01-31"),
            "vegetation_change": {
                "before_ndvi": 0.45,
                "after_ndvi": 0.52,
                "ndvi_difference": 0.07,
                "interpretation": "Moderate vegetation growth"
            },
            "buildup_change": {
                "before_ndbi": 0.12,
                "after_ndbi": 0.15,
                "ndbi_difference": 0.03,
                "interpretation": "Minor built-up area increase"
            },
            "water_change": {
                "before_ndwi": 0.08,
                "after_ndwi": 0.06,
                "ndwi_difference": -0.02,
                "interpretation": "No significant water change"
            },
            "significant_change": True,
            "change_summary": "Vegetation: Moderate vegetation growth; Built-up: Minor built-up area increase"
        }
        
        # Test saving analysis result
        print("\n💾 Testing analysis result saving...")
        saved_file = monitor._save_analysis_result(
            sample_result, 
            'test_change_detection', 
            (("2023-01-01", "2023-01-31"), ("2024-01-01", "2024-01-31"))
        )
        print(f"✅ Saved to: {saved_file}")
        
        # Test saving summary report
        print("\n📊 Testing summary report generation...")
        summary_file = monitor._save_summary_report([sample_result], 'test_analysis')
        print(f"✅ Summary saved to: {summary_file}")
        
        # Test visual comparison metadata
        print("\n🖼️ Testing visual comparison metadata...")
        metadata_file = monitor._save_visual_comparison_metadata(
            "test_image.png",
            ("2023-01-01", "2023-01-31"),
            ("2024-01-01", "2024-01-31")
        )
        print(f"✅ Metadata saved to: {metadata_file}")
        
        # Show all created files
        print(f"\n📄 All files created in {monitor.output_dir}:")
        if os.path.exists(monitor.output_dir):
            for file in sorted(os.listdir(monitor.output_dir)):
                file_path = os.path.join(monitor.output_dir, file)
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    print(f"   📁 {file}")
                    print(f"      Size: {file_size} bytes")
                    print(f"      Modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test reading a saved result
        print(f"\n📖 Testing result reading...")
        with open(saved_file, 'r') as f:
            loaded_data = json.load(f)
        
        print(f"✅ Successfully loaded saved result")
        print(f"   Timestamp: {loaded_data['metadata']['timestamp']}")
        print(f"   Analysis Type: {loaded_data['metadata']['analysis_type']}")
        print(f"   Coordinates: {loaded_data['metadata']['coordinates']}")
        print(f"   Change Summary: {loaded_data['analysis_result']['change_summary']}")
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_output_functionality()
