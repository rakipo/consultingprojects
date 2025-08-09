// Test inserting a chunk with embedding manually

// First, let's see what chunk records exist
MATCH (c:Chunk) 
RETURN c.chunk_id, keys(c) AS properties 
LIMIT 3;

// Test creating a chunk with embedding manually
MERGE (c:Chunk {chunk_id: 'test-chunk-001'})
SET c.chunk_text = 'This is a test chunk for embedding',
    c.chunk_position = 0,
    c.chunk_order = 0,
    c.content_id = 'test-content',
    c.embedding = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0];

// Verify the test chunk was created with embedding
MATCH (c:Chunk {chunk_id: 'test-chunk-001'}) 
RETURN c.chunk_id, c.chunk_text, size(c.embedding) AS embedding_size, c.embedding[0..5] AS first_5_values;