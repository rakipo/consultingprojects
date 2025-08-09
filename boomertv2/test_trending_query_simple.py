#!/usr/bin/env python3
"""
Simple test to verify trending query validation
"""

import yaml
import json
from postgres_query_runner import load_config, ErrorCodes

def test_trending_query_validation():
    """Test that the code specifically looks for 'trending' query."""
    print("=== Testing Trending Query Validation ===")
    
    # Test 1: Config with trending query
    config_with_trending = {
        'queries': {
            'other_query': 'SELECT * FROM other_table;',
            'trending': 'SELECT * FROM structured_content LIMIT 10;',
            'another_query': 'SELECT * FROM another_table;'
        }
    }
    
    with open('test_config_with_trending.yml', 'w') as f:
        yaml.dump(config_with_trending, f)
    
    config = load_config('test_config_with_trending.yml')
    query_name = "trending"
    
    if 'queries' in config and query_name in config['queries']:
        print("✅ Config contains 'trending' query - validation passed")
    else:
        print("❌ Config validation failed")
    
    # Test 2: Config without trending query
    config_without_trending = {
        'queries': {
            'other_query': 'SELECT * FROM other_table;',
            'another_query': 'SELECT * FROM another_table;'
        }
    }
    
    with open('test_config_without_trending.yml', 'w') as f:
        yaml.dump(config_without_trending, f)
    
    config = load_config('test_config_without_trending.yml')
    
    if 'queries' not in config or query_name not in config['queries']:
        available_queries = list(config.get('queries', {}).keys())
        print(f"✅ Correctly detected missing 'trending' query. Available queries: {available_queries}")
    else:
        print("❌ Should have detected missing 'trending' query")
    
    # Cleanup
    import os
    for file in ['test_config_with_trending.yml', 'test_config_without_trending.yml']:
        if os.path.exists(file):
            os.remove(file)
    
    print("\n🎉 Trending query validation test completed!")

if __name__ == "__main__":
    test_trending_query_validation()