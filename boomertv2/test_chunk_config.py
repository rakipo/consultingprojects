#!/usr/bin/env python3
"""
Test script to verify Chunk node configuration with vector embeddings
"""

import yaml
import json
from neo4j_model_generator import Neo4jModelGenerator

def test_chunk_configuration():
    """Test the Chunk node configuration with vector embeddings."""
    try:
        # Load config
        with open('config_boomer.yml', 'r') as file:
            config = yaml.safe_load(file)
        
        print("=== Chunk Node Configuration Test ===")
        
        # Get model config for trending query
        generator = Neo4jModelGenerator()
        model_config = generator.get_model_config(config, 'trending')
        
        if model_config:
            print("✅ Model configuration loaded successfully")
            
            # Find Chunk node
            chunk_node = None
            for node in model_config.get('nodes', []):
                if node['label'] == 'Chunk':
                    chunk_node = node
                    break
            
            if chunk_node:
                print("✅ Chunk node found in configuration")
                print(f"   - Label: {chunk_node['label']}")
                print(f"   - Node ID Property: {chunk_node['node_id_property']}")
                print(f"   - Multiple Labels: {chunk_node.get('multiple_labels', [])}")
                
                # Check properties
                print("   - Properties:")
                for prop in chunk_node.get('properties', []):
                    print(f"     * {prop['name']} ({prop['type']})", end="")
                    if prop.get('unique'):
                        print(" [UNIQUE]", end="")
                    if prop.get('indexed'):
                        print(" [INDEXED]", end="")
                    if prop.get('type') == 'vector':
                        print(f" [DIM: {prop.get('vector_dimension', 'N/A')}, SIM: {prop.get('vector_similarity', 'N/A')}]", end="")
                    print()
                
                # Check vector index in extra_indexes
                vector_index_found = False
                for index in model_config.get('extra_indexes', []):
                    if index['node_label'] == 'Chunk' and index['property'] == 'embedding' and index['type'] == 'VECTOR':
                        vector_index_found = True
                        print("✅ Vector index configuration found:")
                        print(f"   - Dimension: {index.get('vector_dimension', 'N/A')}")
                        print(f"   - Similarity: {index.get('vector_similarity', 'N/A')}")
                        break
                
                if not vector_index_found:
                    print("❌ Vector index configuration not found")
                
                # Test model generation with mock data
                print("\n=== Testing Model Generation ===")
                mock_data = {
                    'table_info': {
                        'columns': ['id', 'content', 'chunk_id', 'embedding', 'chunk_text', 'content_id'],
                        'row_count': 1
                    },
                    'metadata': {
                        'total_records': 1,
                        'column_count': 6
                    }
                }
                
                try:
                    generated_model = generator._generate_configured_neo4j_model(mock_data, model_config)
                    print("✅ Model generation successful")
                    
                    # Check if Chunk node is in generated model
                    chunk_in_model = False
                    for node in generated_model.get('nodes', []):
                        if node['label'] == 'Chunk':
                            chunk_in_model = True
                            print(f"✅ Chunk node generated with {len(node.get('properties', []))} properties")
                            break
                    
                    if not chunk_in_model:
                        print("❌ Chunk node not found in generated model")
                    
                    # Check vector index in generated model
                    vector_index_in_model = False
                    for index in generated_model.get('indexes', []):
                        if (index.get('node_label') == 'Chunk' and 
                            index.get('property') == 'embedding' and 
                            index.get('type') == 'VECTOR'):
                            vector_index_in_model = True
                            print("✅ Vector index generated in model")
                            print(f"   Cypher: {index.get('cypher', 'N/A')}")
                            break
                    
                    if not vector_index_in_model:
                        print("❌ Vector index not found in generated model")
                    
                    # Check constraints
                    chunk_constraint_found = False
                    for constraint in generated_model.get('constraints', []):
                        if (constraint.get('node_label') == 'Chunk' and 
                            constraint.get('property') == 'chunk_id'):
                            chunk_constraint_found = True
                            print("✅ Chunk ID unique constraint generated")
                            print(f"   Cypher: {constraint.get('cypher', 'N/A')}")
                            break
                    
                    if not chunk_constraint_found:
                        print("❌ Chunk ID unique constraint not found")
                    
                except Exception as e:
                    print(f"❌ Model generation failed: {str(e)}")
                
            else:
                print("❌ Chunk node not found in configuration")
        else:
            print("❌ No model configuration found")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    test_chunk_configuration()