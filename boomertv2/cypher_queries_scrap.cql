WITH $queryEmbedding AS queryVector
MATCH (chunk:Chunk)
WHERE chunk.embedding IS NOT NULL
WITH chunk, queryVector,
     reduce(dot = 0.0, i IN range(0, size(chunk.embedding)-1) | 
            dot + chunk.embedding[i] * queryVector[i]) AS dotProduct,
     sqrt(reduce(norm1 = 0.0, x IN chunk.embedding | norm1 + x * x)) AS norm1,
     sqrt(reduce(norm2 = 0.0, x IN queryVector | norm2 + x * x)) AS norm2
WITH chunk, dotProduct / (norm1 * norm2) AS similarity
WHERE similarity > 0.5
RETURN chunk.chunk_id, chunk.chunk_text, similarity
ORDER BY similarity DESC
LIMIT 10;



Find similar chunks:

MATCH (target:Chunk {chunk_id: 'your-chunk-id'})
MATCH (other:Chunk) 
WHERE other.chunk_id <> target.chunk_id AND other.embedding IS NOT NULL
WITH target, other,
     reduce(dot = 0.0, i IN range(0, size(target.embedding)-1) | 
            dot + target.embedding[i] * other.embedding[i]) AS dotProduct,
     sqrt(reduce(norm1 = 0.0, x IN target.embedding | norm1 + x * x)) AS norm1,
     sqrt(reduce(norm2 = 0.0, x IN other.embedding | norm2 + x * x)) AS norm2
WITH target, other, dotProduct / (norm1 * norm2) AS similarity
WHERE similarity > 0.7
RETURN other.chunk_id, other.chunk_text, similarity
ORDER BY similarity DESC
LIMIT 10