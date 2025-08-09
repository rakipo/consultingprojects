#!/usr/bin/env python3

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.neo4j_data_loader import Neo4jDataLoader

def debug_chunk_loading_offline():
    """Debug chunk loading using existing embeddings data."""
    
    # Load the embeddings data we generated earlier
    with open('output/data/embeddings_output.json', 'r') as f:
        embeddings_data = json.load(f)
    
    print(f"Loaded {embeddings_data['total_chunks']} chunks from embeddings_output.json")
    print(f"Embedding dimension: {embeddings_data['embedding_dimension']}")
    
    # Convert to chunk records format
    chunk_records = []
    for chunk_data in embeddings_data['chunks'][:3]:  # Just test first 3
        chunk_record = {
            'chunk_id': chunk_data['chunk_id'],
            'chunk_text': chunk_data['chunk_text'],
            'chunk_position': chunk_data['chunk_position'],
            'chunk_order': chunk_data['chunk_order'],
            'content_id': chunk_data['content_id'],
            'embedding': chunk_data['embedding']
        }
        chunk_records.append(chunk_record)
    
    print(f"\nConverted {len(chunk_records)} chunk records")
    
    # Show first chunk record structure
    first_chunk = chunk_records[0]
    print(f"\nFirst chunk record structure:")
    for key, value in first_chunk.items():
        if key == 'embedding':
            print(f"  {key}: <list of {len(value)} floats> - first 3: {value[:3]}")
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
    
    # Test what properties would be extracted (simulate the data loader logic)
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
    
    # Test the actual Cypher query that would be generated
    print(f"\n" + "="*60)
    print("CYPHER QUERY SIMULATION")
    print("="*60)
    
    cypher = f"""
    MERGE (n:Chunk {{chunk_id: $id}})
    SET n += $properties
    """
    
    parameters = {
        'id': record[node_id_property],
        'properties': node_properties
    }
    
    print(f"Cypher query:")
    print(cypher)
    print(f"\nParameters:")
    print(f"  id: {parameters['id']}")
    print(f"  properties keys: {list(parameters['properties'].keys())}")
    print(f"  embedding length: {len(parameters['properties'].get('embedding', []))}")
    
    # Test manual insertion
    print(f"\n" + "="*60)
    print("MANUAL INSERTION TEST")
    print("="*60)
    
    loader = Neo4jDataLoader()
    
    # Connect to Neo4j
    neo4j_config = {
        'host': 'localhost',
        'port': 7687,
        'database': 'neo4j',
        'user': 'neo4j',
        'password': 'password123'
    }
    
    try:
        loader.connect_to_neo4j(neo4j_config)
        print("✅ Connected to Neo4j")
        
        # Try to insert one chunk manually
        test_chunk = chunk_records[0]
        cypher = """
        MERGE (n:Chunk {chunk_id: $id})
        SET n.chunk_text = $chunk_text,
            n.chunk_position = $chunk_position,
            n.chunk_order = $chunk_order,
            n.content_id = $content_id,
            n.embedding = $embedding
        RETURN n.chunk_id, size(n.embedding) AS embedding_size
        """
        
        parameters = {
            'id': test_chunk['chunk_id'],
            'chunk_text': test_chunk['chunk_text'],
            'chunk_position': test_chunk['chunk_position'],
            'chunk_order': test_chunk['chunk_order'],
            'content_id': test_chunk['content_id'],
            'embedding': test_chunk['embedding']
        }
        
        result = loader.execute_cypher_query(cypher, parameters)
        print(f"✅ Manual insertion successful!")
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if hasattr(loader, 'neo4j_driver') and loader.neo4j_driver:
            loader.neo4j_driver.close()

if __name__ == "__main__":
    debug_chunk_loading_offline()