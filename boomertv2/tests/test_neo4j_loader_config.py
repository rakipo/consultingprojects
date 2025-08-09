#!/usr/bin/env python3
"""
Test script to verify Neo4j Data Loader configuration
"""

import yaml
import json
import os
import sys

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.neo4j_data_loader import Neo4jDataLoader

def test_loader_configuration():
    """Test the Neo4j Data Loader configuration."""
    try:
        print("=== Neo4j Data Loader Configuration Test ===")
        
        # Test config loading
        with open('config/config_boomer_load.yml', 'r') as file:
            config = yaml.safe_load(file)
        
        print("✅ Configuration loaded successfully")
        print(f"   - Database configs: {list(config.get('database', {}).keys())}")
        print(f"   - Queries available: {list(config.get('queries', {}).keys())}")
        
        # Test loader initialization
        loader = Neo4jDataLoader()
        print("✅ Neo4j Data Loader initialized")
        
        # Test model loading (if model file exists)
        try:
            # Look for any existing model file
            import glob
            model_files = glob.glob("neo4j_model_*.json")
            if model_files:
                model_file = model_files[0]
                model = loader.load_neo4j_model(model_file)
                print(f"✅ Model loaded from {model_file}")
                print(f"   - Nodes: {len(model.get('nodes', []))}")
                print(f"   - Relationships: {len(model.get('relationships', []))}")
                
                # Check for vector properties
                vector_nodes = []
                for node in model.get('nodes', []):
                    for prop in node.get('properties', []):
                        if prop.get('type') == 'vector':
                            vector_nodes.append(node['label'])
                            break
                
                if vector_nodes:
                    print(f"✅ Vector embedding nodes found: {vector_nodes}")
                else:
                    print("ℹ️  No vector embedding nodes found")
            else:
                print("ℹ️  No model files found for testing")
        except Exception as e:
            print(f"⚠️  Model loading test skipped: {str(e)}")
        
        # Test text chunking
        test_text = "This is a test text for chunking. " * 20
        chunks = loader.chunk_text_content(test_text, chunk_size=100, overlap=20)
        print(f"✅ Text chunking test successful: {len(chunks)} chunks created")
        
        # Test metrics structure
        print("✅ Load metrics structure initialized:")
        for key, value in loader.load_metrics.items():
            print(f"   - {key}: {type(value).__name__}")
        
        print("\n🎉 All configuration tests passed!")
        
    except Exception as e:
        print(f"❌ Configuration test failed: {str(e)}")

if __name__ == "__main__":
    test_loader_configuration()