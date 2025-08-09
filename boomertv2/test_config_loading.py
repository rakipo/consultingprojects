#!/usr/bin/env python3
"""
Test script to verify configuration loading
"""

import yaml
from neo4j_model_generator import Neo4jModelGenerator

def test_config_loading():
    """Test loading the updated configuration."""
    try:
        # Load config
        with open('config_boomer.yml', 'r') as file:
            config = yaml.safe_load(file)
        
        print("Configuration loaded successfully!")
        print(f"Queries available: {list(config.get('queries', {}).keys())}")
        
        if 'neo4j_model_config' in config:
            print(f"Neo4j model configs available: {list(config['neo4j_model_config'].keys())}")
            
            # Test getting model config
            generator = Neo4jModelGenerator()
            model_config = generator.get_model_config(config, 'trending')
            
            if model_config:
                print("Model configuration found for 'trending' query:")
                print(f"- Include columns: {len(model_config.get('include_columns', []))}")
                print(f"- Nodes defined: {len(model_config.get('nodes', []))}")
                print(f"- Relationships defined: {len(model_config.get('relationships', []))}")
                print(f"- Extra indexes: {len(model_config.get('extra_indexes', []))}")
                
                # Print node details
                for i, node in enumerate(model_config.get('nodes', [])):
                    print(f"  Node {i+1}: {node['label']} with {len(node.get('properties', []))} properties")
                    if 'multiple_labels' in node:
                        print(f"    Multiple labels: {node['multiple_labels']}")
            else:
                print("No model configuration found for 'trending' query")
        else:
            print("No neo4j_model_config section found in configuration")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_config_loading()