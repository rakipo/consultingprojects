#!/usr/bin/env python3
"""
Test script to verify all three APIs are working correctly
"""

from multi_api_image_creation import ConfigManager, find_best_image_for_time

def test_all_apis():
    """Test all three APIs with a simple search"""
    
    print("🧪 Testing All APIs")
    print("=" * 50)
    
    # Load configuration
    config = ConfigManager("multi_image_api_config.yaml")
    
    # Test coordinates (Times Square, NYC)
    latitude = 40.7589
    longitude = -73.9851
    target_datetime = "2024-07-15"
    
    # Test with just 1 image per API for faster testing
    print(f"📍 Testing location: {latitude}, {longitude}")
    print(f"📅 Target date: {target_datetime}")
    print(f"🎯 Images per API: 1")
    
    # Test all APIs
    results = find_best_image_for_time(
        latitude=latitude,
        longitude=longitude,
        target_datetime=target_datetime,
        config=config,
        apis_to_try=['nasa', 'sentinel', 'planet'],
        images_per_api=1
    )
    
    print(f"\n📊 Test Results:")
    print(f"   Total images found: {len(results)}")
    
    # Group by source
    source_counts = {}
    for image, date, source in results:
        base_source = source.split('_')[0]  # Get base source name
        source_counts[base_source] = source_counts.get(base_source, 0) + 1
    
    for source, count in source_counts.items():
        print(f"   {source}: {count} image(s)")
    
    print(f"\n✅ Test completed!")
    
    return results

if __name__ == "__main__":
    test_all_apis()
