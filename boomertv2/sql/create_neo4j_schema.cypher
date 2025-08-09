// Create Neo4j Schema: Constraints and Indexes
// This script creates the missing constraints and indexes from the model

// ============================================================================
// CONSTRAINTS
// ============================================================================

// Article constraints
CREATE CONSTRAINT article_id_unique IF NOT EXISTS FOR (n:Article) REQUIRE n.id IS UNIQUE;

// Website constraints  
CREATE CONSTRAINT website_domain_unique IF NOT EXISTS FOR (n:Website) REQUIRE n.domain IS UNIQUE;

// Author constraints
CREATE CONSTRAINT author_name_unique IF NOT EXISTS FOR (n:Author) REQUIRE n.name IS UNIQUE;

// Chunk constraints
CREATE CONSTRAINT chunk_chunk_id_unique IF NOT EXISTS FOR (n:Chunk) REQUIRE n.chunk_id IS UNIQUE;

// ============================================================================
// INDEXES
// ============================================================================

// Article indexes
CREATE INDEX article_title_text IF NOT EXISTS FOR (n:Article) ON (n.title);
CREATE INDEX article_content_text IF NOT EXISTS FOR (n:Article) ON (n.content);
CREATE INDEX article_publish_date_range IF NOT EXISTS FOR (n:Article) ON (n.publish_date);

// Website indexes
CREATE INDEX website_site_name_text IF NOT EXISTS FOR (n:Website) ON (n.site_name);
CREATE INDEX website_domain_text IF NOT EXISTS FOR (n:Website) ON (n.domain);

// ============================================================================
// VECTOR INDEX (Fixed dimension: 384 instead of 1536)
// ============================================================================

// Drop existing vector index if it exists with wrong dimensions
DROP INDEX chunk_embedding_vector IF EXISTS;

// Create vector index with correct dimensions (384 for all-MiniLM-L6-v2)
CREATE VECTOR INDEX chunk_embedding_vector IF NOT EXISTS 
FOR (n:Chunk) ON (n.embedding) 
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 384, 
    `vector.similarity_function`: 'cosine'
  }
};

// ============================================================================
// VERIFICATION QUERIES
// ============================================================================

// Show all constraints
SHOW CONSTRAINTS;

// Show all indexes
SHOW INDEXES;

// Check if vector index is ready
SHOW INDEXES YIELD name, state, populationPercent 
WHERE name = 'chunk_embedding_vector' 
RETURN name, state, populationPercent;