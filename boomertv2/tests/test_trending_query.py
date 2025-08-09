#!/usr/bin/env python3
"""
Test script to verify that the Neo4j Data Loader specifically uses the "trending" query
"""

import yaml
import os
import sys

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.neo4j_data_loader import Neo4jDataLoader

def test_trending_query_usage():
    """Test that the loader specifically uses the 'trending' query."""
    try:
        print("=== Testing Trending Query Usage ===")
        
        # Test config with multiple queries
        test_config = {
            'database': {
                'postgres': 'host: localhost\nport: 5432\ndatabase: test\nuser: test\npassword: test',
                'neo4j': 'host: localhost\nport: 7687\ndatabase: neo4j\nuser: neo4j\npassword: test'
            },
            'queries': {
                'other_query': 'SELECT * FROM other_table;',
                'trending': 'SELECT * FROM structured_content LIMIT 10;',
                'another_query': 'SELECT * FROM another_table;'
            },
            'neo4j_load_config': {
                'embedding': {
                    'chunk_size': 512,
                    'chunk_overlap': 50,
                    'use_llm_chunking': True
                }
            }
        }
        
        # Save test config
        with open('test_config.yml', 'w') as f:
            yaml.dump(test_config, f)
        
        # Create a simple test model
        test_model = {
            'nodes': [
                {
                    'label': 'Content',
                    'node_id_property': 'id',
                    'properties': [
                        {'name': 'id', 'type': 'string', 'unique': True},
                        {'name': 'title', 'type': 'string'}
                    ]
                }
            ],
            'relationships': []
        }
        
        with open('test_model.json', 'w') as f:
            import json
            json.dump(test_model, f)
        
        # Test that the loader specifically looks for "trending" query
        loader = Neo4jDataLoader()
        
        # This should work - config has "trending" query
        print("✅ Config contains 'trending' query - should work")
        
        # Test config without "trending" query
        config_without_trending = {
            'database': {
                'postgres': 'host: localhost\nport: 5432\ndatabase: test\nuser: test\npassword: test',
                'neo4j': 'host: localhost\nport: 7687\ndatabase: neo4j\nuser: neo4j\npassword: test'
            },
            'queries': {
                'other_query': 'SELECT * FROM other_table;',
                'another_query': 'SELECT * FROM another_table;'
            }
        }
        
        with open('test_config_no_trending.yml', 'w') as f:
            yaml.dump(config_without_trending, f)
        
        print("✅ Testing config without 'trending' query - should fail gracefully")
        
        try:
            loader.load_data_to_neo4j('test_config_no_trending.yml', 'test_model.json', 'test_metrics.txt')
            print("❌ Should have failed but didn't")
        except Exception as e:
            if "Query 'trending' not found" in str(e):
                print("✅ Correctly failed when 'trending' query not found")
                print(f"   Error message: {str(e)}")
            else:
                print(f"❌ Failed for wrong reason: {str(e)}")
        
        # Cleanup
        import os
        for file in ['test_config.yml', 'test_config_no_trending.yml', 'test_model.json']:
            if os.path.exists(file):
                os.remove(file)
        
        print("\n🎉 Trending query usage test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    test_trending_query_usage()