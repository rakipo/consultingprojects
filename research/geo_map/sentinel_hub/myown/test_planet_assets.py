#!/usr/bin/env python3
"""
Test script to inspect Planet Labs assets in detail
"""

from multi_api_image_creation import ConfigManager, PlanetLabsImagery
import requests

def test_planet_assets():
    """Test Planet Labs asset inspection"""
    
    print("🧪 Testing Planet Labs Asset Details")
    print("=" * 50)
    
    # Load configuration
    config = ConfigManager("multi_image_api_config.yaml")
    
    # Test coordinates (Times Square, NYC)
    latitude = 40.7589
    longitude = -73.9851
    target_date = "2024-07-15"
    
    print(f"📍 Location: {latitude}, {longitude}")
    print(f"📅 Target date: {target_date}")
    
    # Initialize Planet Labs client
    planet_client = PlanetLabsImagery(config)
    
    # Search for images
    print(f"\n🔍 Searching for Planet Labs images...")
    images = planet_client.search_images_by_date(latitude, longitude, target_date)
    
    if images:
        print(f"✅ Found {len(images)} Planet Labs images")
        
        # Inspect first few images in detail
        for i, item in enumerate(images[:3]):  # Check first 3 items
            print(f"\n📋 Item {i+1} Details:")
            item_id = item.get('id', 'unknown')
            item_type = item.get('properties', {}).get('item_type', 'PSScene')
            acquired_date = item.get('properties', {}).get('acquired', 'unknown')
            cloud_cover = item.get('properties', {}).get('cloud_cover', 'unknown')
            
            print(f"   ID: {item_id}")
            print(f"   Type: {item_type}")
            print(f"   Acquired: {acquired_date}")
            print(f"   Cloud Cover: {cloud_cover}")
            
            # Get assets for this item
            headers = {'Authorization': f'api-key {planet_client.api_key}'}
            assets_url = f"{planet_client.base_url}/data/v1/item-types/{item_type}/items/{item_id}/assets"
            
            print(f"   🔗 Assets URL: {assets_url}")
            
            try:
                assets_response = requests.get(assets_url, headers=headers)
                print(f"   📡 Assets Response: {assets_response.status_code}")
                
                if assets_response.status_code == 200:
                    assets = assets_response.json()
                    print(f"   📦 Available Assets: {list(assets.keys())}")
                    
                    # Show details for each asset
                    for asset_name, asset_info in assets.items():
                        status = asset_info.get('status', 'unknown')
                        print(f"      - {asset_name}: {status}")
                        
                        if 'location' in asset_info:
                            print(f"        Location: Available")
                        else:
                            print(f"        Location: Not available")
                else:
                    error_text = assets_response.text[:200]
                    print(f"   ❌ Assets request failed: {error_text}")
                    
            except Exception as e:
                print(f"   ❌ Error getting assets: {e}")
    
    else:
        print("❌ No Planet Labs images found")

if __name__ == "__main__":
    test_planet_assets()

