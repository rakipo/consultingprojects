#!/usr/bin/env python3

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.neo4j_data_loader import Neo4jDataLoader

def load_embeddings_to_neo4j():
    """Load embeddings data directly to Neo4j without PostgreSQL dependency."""
    
    print("🚀 Loading Embeddings to Neo4j")
    print("==============================")
    
    # Check if embeddings file exists
    if not os.path.exists('output/data/embeddings_output.json'):
        print("❌ embeddings_output.json not found!")
        print("Please run the debug_chunking.py script first to generate embeddings.")
        return
    
    # Load the embeddings data
    with open('output/data/embeddings_output.json', 'r') as f:
        embeddings_data = json.load(f)
    
    print(f"📊 Loaded {embeddings_data['total_chunks']} chunks from embeddings_output.json")
    print(f"📐 Embedding dimension: {embeddings_data['embedding_dimension']}")
    
    # Initialize Neo4j loader
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
        
        # Create schema first
        print("\n🏗️  Creating Neo4j schema...")
        
        # Create constraints
        constraints = [
            "CREATE CONSTRAINT article_id_unique IF NOT EXISTS FOR (n:Article) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT website_domain_unique IF NOT EXISTS FOR (n:Website) REQUIRE n.domain IS UNIQUE", 
            "CREATE CONSTRAINT author_name_unique IF NOT EXISTS FOR (n:Author) REQUIRE n.name IS UNIQUE",
            "CREATE CONSTRAINT chunk_chunk_id_unique IF NOT EXISTS FOR (n:Chunk) REQUIRE n.chunk_id IS UNIQUE"
        ]
        
        for constraint in constraints:
            try:
                loader.execute_cypher_query(constraint)
                print(f"✅ Created constraint")
            except Exception as e:
                print(f"⚠️  Constraint may already exist: {str(e)[:50]}...")
        
        # Create indexes
        indexes = [
            "CREATE INDEX article_title_text IF NOT EXISTS FOR (n:Article) ON (n.title)",
            "CREATE INDEX article_content_text IF NOT EXISTS FOR (n:Article) ON (n.content)",
            "CREATE INDEX article_publish_date_range IF NOT EXISTS FOR (n:Article) ON (n.publish_date)",
            "CREATE INDEX website_site_name_text IF NOT EXISTS FOR (n:Website) ON (n.site_name)",
            "CREATE INDEX website_domain_text IF NOT EXISTS FOR (n:Website) ON (n.domain)"
        ]
        
        for index in indexes:
            try:
                loader.execute_cypher_query(index)
                print(f"✅ Created index")
            except Exception as e:
                print(f"⚠️  Index may already exist: {str(e)[:50]}...")
        
        # Create vector index
        try:
            loader.execute_cypher_query("DROP INDEX chunk_embedding_vector IF EXISTS")
            vector_index = """
            CREATE VECTOR INDEX chunk_embedding_vector IF NOT EXISTS 
            FOR (n:Chunk) ON (n.embedding) 
            OPTIONS {
              indexConfig: {
                `vector.dimensions`: 384, 
                `vector.similarity_function`: 'cosine'
              }
            }
            """
            loader.execute_cypher_query(vector_index)
            print("✅ Created vector index")
        except Exception as e:
            print(f"⚠️  Vector index error: {str(e)[:100]}...")
        
        print("✅ Schema creation completed")
        
        # Load chunk data
        print(f"\n📥 Loading {len(embeddings_data['chunks'])} chunks...")
        
        chunks_loaded = 0
        chunks_failed = 0
        
        for i, chunk_data in enumerate(embeddings_data['chunks']):
            try:
                # Create chunk with all properties
                cypher = """
                MERGE (c:Chunk {chunk_id: $chunk_id})
                SET c.chunk_text = $chunk_text,
                    c.chunk_position = $chunk_position,
                    c.chunk_order = $chunk_order,
                    c.content_id = $content_id,
                    c.embedding = $embedding
                RETURN c.chunk_id
                """
                
                parameters = {
                    'chunk_id': chunk_data['chunk_id'],
                    'chunk_text': chunk_data['chunk_text'],
                    'chunk_position': chunk_data['chunk_position'],
                    'chunk_order': chunk_data['chunk_order'],
                    'content_id': chunk_data['content_id'],
                    'embedding': chunk_data['embedding']
                }
                
                result = loader.execute_cypher_query(cypher, parameters)
                chunks_loaded += 1
                
                # Progress indicator
                if (i + 1) % 10 == 0:
                    print(f"📊 Loaded {i + 1}/{len(embeddings_data['chunks'])} chunks...")
                
            except Exception as e:
                chunks_failed += 1
                print(f"❌ Failed to load chunk {chunk_data['chunk_id']}: {str(e)[:100]}...")
        
        print(f"\n✅ Chunk loading completed!")
        print(f"   📊 Chunks loaded: {chunks_loaded}")
        print(f"   ❌ Chunks failed: {chunks_failed}")
        
        # Verification
        print(f"\n🔍 Verification...")
        
        # Count nodes
        result = loader.execute_cypher_query("MATCH (c:Chunk) RETURN count(c) AS total")
        total_chunks = result['records'][0]['total'] if result['records'] else 0
        
        # Count chunks with embeddings
        result = loader.execute_cypher_query("MATCH (c:Chunk) WHERE c.embedding IS NOT NULL RETURN count(c) AS with_embeddings")
        chunks_with_embeddings = result['records'][0]['with_embeddings'] if result['records'] else 0
        
        print(f"   📊 Total chunks in Neo4j: {total_chunks}")
        print(f"   🧠 Chunks with embeddings: {chunks_with_embeddings}")
        
        # Test cosine similarity
        print(f"\n🧪 Testing cosine similarity...")
        
        similarity_test = """
        MATCH (c1:Chunk), (c2:Chunk)
        WHERE c1.embedding IS NOT NULL AND c2.embedding IS NOT NULL 
          AND c1.chunk_id <> c2.chunk_id
        WITH c1, c2 LIMIT 1
        WITH c1, c2,
             reduce(dot = 0.0, i IN range(0, size(c1.embedding)-1) | 
                    dot + c1.embedding[i] * c2.embedding[i]) AS dotProduct,
             sqrt(reduce(norm1 = 0.0, x IN c1.embedding | norm1 + x * x)) AS norm1,
             sqrt(reduce(norm2 = 0.0, x IN c2.embedding | norm2 + x * x)) AS norm2
        WITH c1, c2, dotProduct / (norm1 * norm2) AS similarity
        RETURN c1.chunk_id, c2.chunk_id, similarity
        """
        
        result = loader.execute_cypher_query(similarity_test)
        if result['records']:
            record = result['records'][0]
            print(f"   ✅ Cosine similarity test: {record['similarity']:.4f}")
            print(f"   📝 Between chunks: {record['c1.chunk_id'][:20]}... and {record['c2.chunk_id'][:20]}...")
        else:
            print(f"   ⚠️  No chunks available for similarity test")
        
        print(f"\n🎉 Neo4j loading completed successfully!")
        print(f"   🚀 Ready for semantic search and vector operations")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if hasattr(loader, 'neo4j_driver') and loader.neo4j_driver:
            loader.neo4j_driver.close()
            print("🔌 Neo4j connection closed")

if __name__ == "__main__":
    load_embeddings_to_neo4j()