-- =============================================================================
-- BATCH LOAD CYPHER QUERIES
-- =============================================================================
-- This file contains all Cypher queries used in the batch loading process
-- Organized by category: Schema, Node Creation, Relationships, Data Integrity
-- =============================================================================

-- =============================================================================
-- SCHEMA DEFINITION QUERIES
-- =============================================================================

-- CONSTRAINTS
-- ===========

-- Article ID unique constraint
CREATE CONSTRAINT article_id_unique IF NOT EXISTS FOR (n:Article) REQUIRE n.id IS UNIQUE;

-- Website domain unique constraint  
CREATE CONSTRAINT website_domain_unique IF NOT EXISTS FOR (n:Website) REQUIRE n.domain IS UNIQUE;

-- Author name unique constraint
CREATE CONSTRAINT author_name_unique IF NOT EXISTS FOR (n:Author) REQUIRE n.name IS UNIQUE;

-- Chunk chunk_id unique constraint
CREATE CONSTRAINT chunk_chunk_id_unique IF NOT EXISTS FOR (n:Chunk) REQUIRE n.chunk_id IS UNIQUE;

-- INDEXES
-- =======

-- Article URL index
CREATE INDEX article_id_text IF NOT EXISTS FOR (n:Article) ON (n.url);

-- Article title index
CREATE INDEX article_title_text IF NOT EXISTS FOR (n:Article) ON (n.title);

-- Article publish date range index
CREATE INDEX article_publish_date_range IF NOT EXISTS FOR (n:Article) ON (n.publish_date);

-- Website domain text index
CREATE INDEX website_domain_text IF NOT EXISTS FOR (n:Website) ON (n.domain);

-- Chunk embedding vector index
CREATE VECTOR INDEX chunk_embedding_vector IF NOT EXISTS FOR (n:Chunk) ON (n.embedding) 
OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: 'cosine'}};

-- =============================================================================
-- NODE CREATION QUERIES
-- =============================================================================

-- GENERIC NODE CREATION (from batch_loader.py)
-- ============================================
-- MERGE (n:{node_label} {{{node_id_property}: $id}})
-- SET n += $properties

-- ARTICLE NODE CREATION
-- =====================
MERGE (n:Article {id: $id})
SET n += $properties;

-- WEBSITE NODE CREATION  
-- =====================
MERGE (n:Website {domain: $id})
SET n += $properties;

-- AUTHOR NODE CREATION
-- ====================
MERGE (a:Author {name: $name});

-- CHUNK NODE CREATION
-- ===================
MERGE (n:Chunk {chunk_id: $id})
SET n += $properties;

-- TAG NODE CREATION
-- =================
MERGE (t:Tag {tag_name: $tag_name});

-- =============================================================================
-- RELATIONSHIP CREATION QUERIES
-- =============================================================================

-- GENERIC RELATIONSHIP CREATION (from batch_loader.py)
-- ===================================================
-- MATCH (start:{start_node} {{{start_property}: $start_value}})
-- MATCH (end:{end_node} {{{end_property}: $end_value}})
-- MERGE (start)-[r:{rel_type}]->(end)

-- PUBLISHED_ON RELATIONSHIP (Article -> Website)
-- =============================================
MATCH (start:Article {id: $start_value})
MATCH (end:Website {domain: $end_value})
MERGE (start)-[r:PUBLISHED_ON]->(end);

-- HAS_CHUNK RELATIONSHIP (Article -> Chunk)
-- =========================================
MATCH (start:Article {id: $article_id})
MATCH (end:Chunk {source_id: $article_id})
MERGE (start)-[r:HAS_CHUNK]->(end)
SET r.chunk_order = $chunk_order;

-- WRITTEN_BY RELATIONSHIP (Article -> Author)
-- ==========================================
MATCH (article:Article {id: $article_id})
MATCH (author:Author {name: $author_name})
MERGE (article)-[r:WRITTEN_BY]->(author);

-- TAGGED_WITH RELATIONSHIP (Article -> Tag)
-- =========================================
MATCH (a:Article {id: $article_id})
MATCH (t:Tag {tag_name: $tag_name})
MERGE (a)-[r:TAGGED_WITH]->(t);

-- =============================================================================
-- DATA INTEGRITY CHECK QUERIES
-- =============================================================================

-- ORPHAN NODE CHECKS
-- ==================

-- Check for orphan Article nodes
MATCH (n:Article)
WHERE NOT EXISTS((n)-[]-())
RETURN count(n) as orphan_count;

-- Check for orphan Website nodes
MATCH (n:Website)
WHERE NOT EXISTS((n)-[]-())
RETURN count(n) as orphan_count;

-- Check for orphan Author nodes
MATCH (n:Author)
WHERE NOT EXISTS((n)-[]-())
RETURN count(n) as orphan_count;

-- Check for orphan Chunk nodes
MATCH (n:Chunk)
WHERE NOT EXISTS((n)-[]-())
RETURN count(n) as orphan_count;

-- Check for orphan Tag nodes
MATCH (n:Tag)
WHERE NOT EXISTS((n)-[]-())
RETURN count(n) as orphan_count;

-- Get details of orphan nodes (first 5 for logging)
MATCH (n:Article)
WHERE NOT EXISTS((n)-[]-())
RETURN n LIMIT 5;

-- ORPHAN RELATIONSHIP CHECKS
-- ==========================

-- Check for orphan HAS_CHUNK relationships
MATCH ()-[r:HAS_CHUNK]->()
WHERE NOT EXISTS((r)-[:HAS_CHUNK]-())
RETURN count(r) as orphan_rel_count;

-- Check for orphan PUBLISHED_ON relationships
MATCH ()-[r:PUBLISHED_ON]->()
WHERE NOT EXISTS((r)-[:PUBLISHED_ON]-())
RETURN count(r) as orphan_rel_count;

-- Check for orphan WRITTEN_BY relationships
MATCH ()-[r:WRITTEN_BY]->()
WHERE NOT EXISTS((r)-[:WRITTEN_BY]-())
RETURN count(r) as orphan_rel_count;

-- Check for orphan TAGGED_WITH relationships
MATCH ()-[r:TAGGED_WITH]->()
WHERE NOT EXISTS((r)-[:TAGGED_WITH]-())
RETURN count(r) as orphan_rel_count;

-- DATA CONSISTENCY CHECKS
-- =======================

-- Check for articles without content
MATCH (a:Article)
WHERE a.content IS NULL OR a.content = ""
RETURN count(a) as empty_content_count;

-- Check for chunks without embeddings
MATCH (c:Chunk)
WHERE c.embedding IS NULL
RETURN count(c) as no_embedding_count;

-- Check for articles without chunks
MATCH (a:Article)
WHERE NOT EXISTS((a)-[:HAS_CHUNK]->())
RETURN count(a) as no_chunks_count;

-- DUPLICATE NODE CHECKS
-- =====================

-- Check for duplicate articles by URL
MATCH (a:Article)
WITH a.url as url, count(a) as count
WHERE count > 1
RETURN url, count;

-- Check for duplicate websites by domain
MATCH (w:Website)
WITH w.domain as domain, count(w) as count
WHERE count > 1
RETURN domain, count;

-- =============================================================================
-- METRICS AND COUNTING QUERIES
-- =============================================================================

-- NODE COUNTS
-- ===========

-- Count Article nodes
MATCH (a:Article) RETURN count(a) as count;

-- Count Website nodes
MATCH (w:Website) RETURN count(w) as count;

-- Count Author nodes
MATCH (a:Author) RETURN count(a) as count;

-- Count Chunk nodes
MATCH (c:Chunk) RETURN count(c) as count;

-- Count Tag nodes
MATCH (t:Tag) RETURN count(t) as count;

-- RELATIONSHIP COUNTS
-- ===================

-- Count HAS_CHUNK relationships
MATCH ()-[r:HAS_CHUNK]->() RETURN count(r) as count;

-- Count PUBLISHED_ON relationships
MATCH ()-[r:PUBLISHED_ON]->() RETURN count(r) as count;

-- Count WRITTEN_BY relationships
MATCH ()-[r:WRITTEN_BY]->() RETURN count(r) as count;

-- Count TAGGED_WITH relationships
MATCH ()-[r:TAGGED_WITH]->() RETURN count(r) as count;

-- =============================================================================
-- IMPORT QUERIES (from schema)
-- =============================================================================

-- IMPORT ARTICLE NODES
-- ====================
-- Create Article nodes using MERGE with ID only (Best Practice)
LOAD CSV WITH HEADERS FROM 'file:///data.csv' AS row
WITH row WHERE row.id IS NOT NULL
MERGE (n:Article {id: row.id})
SET n.url = CASE WHEN row.url IS NOT NULL THEN row.url ELSE n.url END, 
    n.title = CASE WHEN row.title IS NOT NULL THEN row.title ELSE n.title END, 
    n.summary = CASE WHEN row.summary IS NOT NULL THEN row.summary ELSE n.summary END, 
    n.publish_date = CASE WHEN row.publish_date IS NOT NULL THEN row.publish_date ELSE n.publish_date END, 
    n.language = CASE WHEN row.language IS NOT NULL THEN row.language ELSE n.language END, 
    n.meta_description = CASE WHEN row.meta_description IS NOT NULL THEN row.meta_description ELSE n.meta_description END;

-- IMPORT WEBSITE NODES
-- ====================
-- Create Website nodes using MERGE with ID only (Best Practice)
LOAD CSV WITH HEADERS FROM 'file:///data.csv' AS row
WITH row WHERE row.domain IS NOT NULL
MERGE (n:Website {site_domain: row.domain})
SET n.name = CASE WHEN row.site_name IS NOT NULL THEN row.site_name ELSE n.name END;

-- IMPORT AUTHOR NODES
-- ===================
-- Create Author nodes using MERGE
LOAD CSV WITH HEADERS FROM 'file:///data.csv' AS row
MERGE (n:Author {});

-- IMPORT CHUNK NODES
-- ==================
-- Create Chunk nodes using MERGE
LOAD CSV WITH HEADERS FROM 'file:///data.csv' AS row
MERGE (n:Chunk {embedding: row.embedding});

-- IMPORT RELATIONSHIPS
-- ====================

-- Create PUBLISHED_ON relationships using MERGE (Best Practice)
LOAD CSV WITH HEADERS FROM 'file:///data.csv' AS row
MATCH (start:Article {url: row.url})
MATCH (end:Website {domain: row.domain})
MERGE (start)-[r:PUBLISHED_ON]->(end);

-- Create HAS_CHUNK relationships using MERGE (Best Practice)
LOAD CSV WITH HEADERS FROM 'file:///data.csv' AS row
MATCH (start:Article {url: row.url})
MATCH (end:Chunk {source_id: row.source_id})
MERGE (start)-[r:HAS_CHUNK]->(end);

-- Create WRITTEN_BY relationships using MERGE (Best Practice)
LOAD CSV WITH HEADERS FROM 'file:///data.csv' AS row
MATCH (start:Article {author: row.author})
MATCH (end:Author {name: row.name})
MERGE (start)-[r:WRITTEN_BY]->(end);

-- Create TAGGED_WITH relationships using MERGE (Best Practice)
LOAD CSV WITH HEADERS FROM 'file:///data.csv' AS row
MATCH (start:Article {url: row.url})
MATCH (end:Tag {tag_name: row.tag_name})
MERGE (start)-[r:TAGGED_WITH]->(end);

-- =============================================================================
-- UTILITY QUERIES
-- =============================================================================

-- SHOW ALL CONSTRAINTS
SHOW CONSTRAINTS;

-- SHOW ALL INDEXES
SHOW INDEXES;

-- CLEAR ALL DATA (for testing)
MATCH (n) DETACH DELETE n;

-- =============================================================================
-- END OF BATCH LOAD CYPHER QUERIES
-- =============================================================================
