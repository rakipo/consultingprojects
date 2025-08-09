#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.neo4j_data_loader import Neo4jDataLoader
from src.postgres_query_runner import load_config, get_query_from_config, parse_postgres_config
import json

def debug_chunking():
    """Debug the chunking process to see what's happening."""
    
    # Load configuration
    config = load_config('config/config_boomer_load.yml')
    
    # Load model
    loader = Neo4jDataLoader()
    model = loader.load_neo4j_model('neo4j_model_best_practices_20250807_200801.json')
    
    # Get the trending query
    query = get_query_from_config(config, 'trending')
    print(f"Query: {query}")
    
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
    
    print(f"\nRetrieved {len(data_records)} records")
    print(f"Column names: {column_names}")
    
    # Show first record structure
    if data_records:
        print(f"\nFirst record keys: {list(data_records[0].keys())}")
        
        # Check for content fields
        content_fields = ['content', 'text', 'description', 'summary']
        for field in content_fields:
            if field in data_records[0]:
                content = data_records[0][field]
                if content:
                    print(f"\n{field} field found with length: {len(str(content))}")
                    print(f"First 200 chars: {str(content)[:200]}...")
                else:
                    print(f"\n{field} field is empty/null")
    
    # Test chunking process
    print("\n" + "="*50)
    print("TESTING CHUNKING PROCESS")
    print("="*50)
    
    chunk_records = loader.process_vector_embeddings(data_records, model, config)
    print(f"Generated {len(chunk_records)} chunk records")
    
    if chunk_records:
        print(f"\nFirst chunk record keys: {list(chunk_records[0].keys())}")
        print(f"Embedding dimension: {len(chunk_records[0].get('embedding', []))}")
        
        # Write all embeddings to a file
        embeddings_output = {
            "total_chunks": len(chunk_records),
            "embedding_dimension": len(chunk_records[0].get('embedding', [])),
            "chunks": []
        }
        
        for i, chunk in enumerate(chunk_records):
            chunk_data = {
                "chunk_index": i,
                "chunk_id": chunk.get('chunk_id', 'N/A'),
                "chunk_order": chunk.get('chunk_order', 'N/A'),
                "chunk_position": chunk.get('chunk_position', 'N/A'),
                "content_id": chunk.get('content_id', 'N/A'),
                "chunk_text": chunk.get('chunk_text', ''),
                "chunk_text_length": len(chunk.get('chunk_text', '')),
                "embedding": chunk.get('embedding', []),
                "embedding_length": len(chunk.get('embedding', []))
            }
            embeddings_output["chunks"].append(chunk_data)
        
        # Write to JSON file
        with open('output/data/embeddings_output.json', 'w') as f:
            json.dump(embeddings_output, f, indent=2)
        
        print(f"\n✅ All {len(chunk_records)} embeddings written to 'embeddings_output.json'")
        
        # Print details for first 3 chunks
        print(f"\n" + "="*80)
        print("CHUNK DETAILS (First 3 chunks)")
        print("="*80)
        
        for i, chunk in enumerate(chunk_records[:3]):
            print(f"\n--- CHUNK {i+1} ---")
            print(f"Chunk ID: {chunk.get('chunk_id', 'N/A')}")
            print(f"Chunk Order: {chunk.get('chunk_order', 'N/A')}")
            print(f"Chunk Position: {chunk.get('chunk_position', 'N/A')}")
            print(f"Content ID: {chunk.get('content_id', 'N/A')}")
            
            # Print chunk text
            chunk_text = chunk.get('chunk_text', '')
            print(f"Chunk Text ({len(chunk_text)} chars):")
            print(f"'{chunk_text[:200]}...'")  # Show first 200 chars only
            
            # Print embedding info
            embedding = chunk.get('embedding', [])
            if embedding:
                print(f"Embedding dimension: {len(embedding)}")
                print(f"Embedding type: {type(embedding)}")
                print(f"First 5 values: {embedding[:5]}")
                print(f"Last 5 values: {embedding[-5:]}")
                print(f"Min value: {min(embedding):.6f}")
                print(f"Max value: {max(embedding):.6f}")
                print(f"Mean value: {sum(embedding)/len(embedding):.6f}")
            else:
                print("❌ Embedding: None")
            print("-" * 60)
        
        # Verify embeddings are different
        print(f"\n" + "="*80)
        print("EMBEDDING VERIFICATION")
        print("="*80)
        
        if len(chunk_records) >= 2:
            emb1 = chunk_records[0].get('embedding', [])
            emb2 = chunk_records[1].get('embedding', [])
            
            if emb1 and emb2:
                # Calculate cosine similarity
                import math
                dot_product = sum(a * b for a, b in zip(emb1, emb2))
                magnitude1 = math.sqrt(sum(a * a for a in emb1))
                magnitude2 = math.sqrt(sum(a * a for a in emb2))
                cosine_similarity = dot_product / (magnitude1 * magnitude2)
                
                print(f"✅ Embeddings are different vectors")
                print(f"Cosine similarity between chunk 1 and 2: {cosine_similarity:.4f}")
                print(f"Embedding 1 first 3 values: {emb1[:3]}")
                print(f"Embedding 2 first 3 values: {emb2[:3]}")
            else:
                print("❌ Missing embeddings for comparison")
        else:
            print("❌ Not enough chunks for comparison")

if __name__ == "__main__":
    debug_chunking()