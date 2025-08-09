#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from neo4j import GraphDatabase
import json

def verify_chunks_in_neo4j():
    """Verify that chunks with embeddings are actually loaded in Neo4j."""
    
    # Connect to Neo4j
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password123"))
    
    try:
        with driver.session() as session:
            # Count total chunks
            result = session.run("MATCH (c:Chunk) RETURN count(c) as total_chunks")
            total_chunks = result.single()["total_chunks"]
            print(f"✅ Total Chunk nodes in Neo4j: {total_chunks}")
            
            # Get sample chunks with their properties
            result = session.run("""
                MATCH (c:Chunk) 
                RETURN c.chunk_id, c.chunk_text, c.chunk_position, c.chunk_order, c.content_id, c.embedding
                LIMIT 3
            """)
            
            print(f"\n" + "="*80)
            print("SAMPLE CHUNKS FROM NEO4J")
            print("="*80)
            
            for i, record in enumerate(result):
                print(f"\n--- CHUNK {i+1} FROM NEO4J ---")
                print(f"Chunk ID: {record['c.chunk_id']}")
                print(f"Chunk Order: {record['c.chunk_order']}")
                print(f"Chunk Position: {record['c.chunk_position']}")
                print(f"Content ID: {record['c.content_id']}")
                
                chunk_text = record['c.chunk_text']
                print(f"Chunk Text ({len(chunk_text) if chunk_text else 0} chars):")
                if chunk_text:
                    print(f"'{chunk_text[:200]}...'")
                else:
                    print("❌ No chunk text found")
                
                embedding = record['c.embedding']
                if embedding:
                    print(f"✅ Embedding found: {len(embedding)} dimensions")
                    print(f"First 5 values: {embedding[:5]}")
                    print(f"Last 5 values: {embedding[-5:]}")
                else:
                    print("❌ No embedding found")
                print("-" * 60)
            
            # Check for chunks with embeddings
            result = session.run("""
                MATCH (c:Chunk) 
                WHERE c.embedding IS NOT NULL 
                RETURN count(c) as chunks_with_embeddings
            """)
            chunks_with_embeddings = result.single()["chunks_with_embeddings"]
            print(f"\n✅ Chunks with embeddings: {chunks_with_embeddings}")
            
            # Check embedding dimensions
            result = session.run("""
                MATCH (c:Chunk) 
                WHERE c.embedding IS NOT NULL 
                RETURN size(c.embedding) as embedding_dimension
                LIMIT 1
            """)
            record = result.single()
            if record:
                embedding_dimension = record["embedding_dimension"]
                print(f"✅ Embedding dimension: {embedding_dimension}")
            
            # Check for chunks with text
            result = session.run("""
                MATCH (c:Chunk) 
                WHERE c.chunk_text IS NOT NULL AND c.chunk_text <> ''
                RETURN count(c) as chunks_with_text
            """)
            chunks_with_text = result.single()["chunks_with_text"]
            print(f"✅ Chunks with text: {chunks_with_text}")
            
    finally:
        driver.close()

if __name__ == "__main__":
    verify_chunks_in_neo4j()