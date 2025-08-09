#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.neo4j_data_loader import Neo4jDataLoader
from src.postgres_query_runner import load_config, get_query_from_config, parse_postgres_config
import json

def debug_chunk_loading():
    """Debug why chunk embeddings aren't being stored in Neo4j."""
    
    # Load configuration
    config = load_config('config/config_boomer_load.yml')
    
    # Load model
    loader = Neo4jDataLoader()
    model = loader.load_neo4j_model('neo4j_model_best_practices_20250807_200801.json')
    
    # Get the trending query
    query = get_query_from_config(config, 'trending')
    
    # Connect to PostgreSQL and get data
    postgres_config_str = config['database']['postgres']
    postgres_config = parse_postgres_config(postgres_config_str)
    
    with loader.get_db_connection(postgres_config) as connection:
        results, column_names = loader.execute_query(connection, query)
    
    # Convert to records
    data_records = []
    for row in results:
        record = {}
        for i, value in enumerate(row):
            if i < len(column_names):
                record[column_names[i]] = value
        data_records.append(record)
    
    print(f"Retrieved {len(data_records)} records")
    
    # Process vector embeddings
    chunk_records = loader.process_vector_embeddings(data_records, model, config)
    print(f"Generated {len(chunk_records)} chunk records")
    
    if chunk_records:
        # Show first chunk record structure
        first_chunk = chunk_records[0]
        print(f"\nFirst chunk record structure:")
        for key, value in first_chunk.items():
            if key == 'embedding':
                print(f"  {key}: <list of {len(value)} floats>")
            elif key == 'source_record':
                print(f"  {key}: <source record dict>")
            else:
                print(f"  {key}: {value}")
        
        # Create the chunk model that would be used
        chunk_model = {
            "nodes": [{
                "label": "Chunk", 
                "node_id_property": "chunk_id", 
                "properties": [
                    {"name": "chunk_id", "type": "string", "unique": True},
                    {"name": "chunk_text", "type": "text"},
                    {"name": "chunk_position", "type": "integer"},
                    {"name": "chunk_order", "type": "integer"},
                    {"name": "content_id", "type": "string"},
                    {"name": "embedding", "type": "vector", "vector_dimension": 384, "vector_similarity": "cosine"}
                ]
            }]
        }
        
        print(f"\nChunk model properties:")
        for prop in chunk_model["nodes"][0]["properties"]:
            print(f"  {prop['name']}: {prop['type']}")
        
        # Test what properties would be extracted
        print(f"\nProperty extraction test:")
        node_config = chunk_model["nodes"][0]
        record = first_chunk
        
        node_properties = {}
        node_id_property = node_config.get('node_id_property')
        
        for prop_config in node_config.get('properties', []):
            prop_name = prop_config['name']
            if prop_name in record and record[prop_name] is not None:
                alias = prop_config.get('alias', prop_name)
                node_properties[alias] = record[prop_name]
                print(f"  ✅ {prop_name}: Found in record")
            else:
                print(f"  ❌ {prop_name}: Missing from record or None")
        
        print(f"\nExtracted properties: {list(node_properties.keys())}")
        print(f"Node ID property ({node_id_property}): {record.get(node_id_property)}")

if __name__ == "__main__":
    debug_chunk_loading()