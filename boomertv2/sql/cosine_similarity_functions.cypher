// Cosine Similarity Functions for Neo4j
// Since apoc.algo.cosineSimilarity is not available, here are custom implementations

// 1. Basic Cosine Similarity Function (as a Cypher query)
// Usage: CALL this as a subquery or use the WITH clause

// Example usage:
WITH [0.1, 0.2, 0.3, 0.4] AS vector1, [0.2, 0.3, 0.4, 0.5] AS vector2
WITH vector1, vector2,
     reduce(dot = 0.0, i IN range(0, size(vector1)-1) | dot + vector1[i] * vector2[i]) AS dotProduct,
     sqrt(reduce(norm1 = 0.0, x IN vector1 | norm1 + x * x)) AS norm1,
     sqrt(reduce(norm2 = 0.0, x IN vector2 | norm2 + x * x)) AS norm2
RETURN dotProduct / (norm1 * norm2) AS cosineSimilarity;

// 2. Find Similar Chunks using Cosine Similarity
// This query finds chunks similar to a given chunk based on embeddings

MATCH (target:Chunk {chunk_id: $targetChunkId})
MATCH (other:Chunk) 
WHERE other.chunk_id <> target.chunk_id
WITH target, other,
     reduce(dot = 0.0, i IN range(0, size(target.embedding)-1) | 
            dot + target.embedding[i] * other.embedding[i]) AS dotProduct,
     sqrt(reduce(norm1 = 0.0, x IN target.embedding | norm1 + x * x)) AS norm1,
     sqrt(reduce(norm2 = 0.0, x IN other.embedding | norm2 + x * x)) AS norm2
WITH target, other, dotProduct / (norm1 * norm2) AS similarity
WHERE similarity > $threshold
RETURN other.chunk_id, other.chunk_text, similarity
ORDER BY similarity DESC
LIMIT $limit;

// 3. Semantic Search using Cosine Similarity
// Find chunks most similar to a query embedding

WITH $queryEmbedding AS queryVector
MATCH (chunk:Chunk)
WITH chunk, queryVector,
     reduce(dot = 0.0, i IN range(0, size(chunk.embedding)-1) | 
            dot + chunk.embedding[i] * queryVector[i]) AS dotProduct,
     sqrt(reduce(norm1 = 0.0, x IN chunk.embedding | norm1 + x * x)) AS norm1,
     sqrt(reduce(norm2 = 0.0, x IN queryVector | norm2 + x * x)) AS norm2
WITH chunk, dotProduct / (norm1 * norm2) AS similarity
WHERE similarity > $threshold
RETURN chunk.chunk_id, chunk.chunk_text, chunk.content_id, similarity
ORDER BY similarity DESC
LIMIT $limit;

// 4. Batch Cosine Similarity Calculation
// Calculate similarities between all chunk pairs (expensive!)

MATCH (c1:Chunk), (c2:Chunk)
WHERE id(c1) < id(c2)  // Avoid duplicate pairs
WITH c1, c2,
     reduce(dot = 0.0, i IN range(0, size(c1.embedding)-1) | 
            dot + c1.embedding[i] * c2.embedding[i]) AS dotProduct,
     sqrt(reduce(norm1 = 0.0, x IN c1.embedding | norm1 + x * x)) AS norm1,
     sqrt(reduce(norm2 = 0.0, x IN c2.embedding | norm2 + x * x)) AS norm2
WITH c1, c2, dotProduct / (norm1 * norm2) AS similarity
WHERE similarity > $threshold
RETURN c1.chunk_id, c2.chunk_id, similarity
ORDER BY similarity DESC;

// 5. Create a stored procedure-like function using APOC (if available)
// This creates a custom function you can reuse

CALL apoc.custom.asFunction(
  'cosineSimilarity',
  'WITH $vector1 AS v1, $vector2 AS v2
   WITH v1, v2,
        reduce(dot = 0.0, i IN range(0, size(v1)-1) | dot + v1[i] * v2[i]) AS dotProduct,
        sqrt(reduce(norm1 = 0.0, x IN v1 | norm1 + x * x)) AS norm1,
        sqrt(reduce(norm2 = 0.0, x IN v2 | norm2 + x * x)) AS norm2
   RETURN dotProduct / (norm1 * norm2)',
  'DOUBLE',
  [['vector1', 'LIST OF DOUBLE'], ['vector2', 'LIST OF DOUBLE']],
  false,
  'Calculate cosine similarity between two vectors'
);

// After creating the custom function, you can use it like:
// RETURN custom.cosineSimilarity([0.1, 0.2, 0.3], [0.2, 0.3, 0.4]) AS similarity;