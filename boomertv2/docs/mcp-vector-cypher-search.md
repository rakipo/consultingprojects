# MCP Vector Cypher Search Server

## Overview

The `mcp-vector-cypher-search` server is a custom MCP (Model Context Protocol) server that intelligently combines vector similarity search with Cypher query generation for Neo4j databases. It provides a unified interface for both content-based searches and structured data queries.

## Features

### 🔍 Intelligent Query Routing
- **Vector Search**: Automatically triggered for questions containing "Article" or questions without specific entity labels
- **Direct Cypher**: Used for structured queries about specific entities (users, companies, products, etc.)

### 🧠 Vector Similarity Search
- Uses SentenceTransformer (`all-MiniLM-L6-v2`) for embedding generation
- Searches Neo4j vector indexes for similar content chunks
- Configurable similarity thresholds and result limits

### ⚡ Cypher Query Generation
- Integrates with `mcp-neo4j-cypher` service for intelligent query generation
- Enhances queries with context from vector search results
- Fallback query generation for basic scenarios

### 📊 Dual Result Sets
- Returns both vector search chunks and Cypher query results separately
- Provides comprehensive metadata about the search process
- Maintains search context and scoring information

## Architecture

```
Question Input
     ↓
Question Analysis
     ↓
┌─────────────────┬─────────────────┐
│  Vector Search  │  Direct Cypher  │
│  (Article/      │  (Specific      │
│   Generic)      │   Entities)     │
└─────────────────┴─────────────────┘
     ↓                     ↓
Embedding Generation    MCP Cypher Call
     ↓                     ↓
Vector Similarity       Query Enhancement
     ↓                     ↓
Chunk Retrieval         Cypher Execution
     ↓                     ↓
┌─────────────────────────────────────┐
│        Combined Results             │
│  - Chunks + Similarity Scores       │
│  - Cypher Results                   │
│  - Metadata                         │
└─────────────────────────────────────┘
```

## Installation

### Prerequisites
```bash
pip install sentence-transformers neo4j mcp
```

### Configuration
1. **Neo4j Setup**: Ensure Neo4j is running with vector indexes
2. **Environment Variables**: Configure connection parameters
3. **MCP Registration**: Add to your MCP client configuration

### MCP Client Configuration
```json
{
  "mcpServers": {
    "mcp-vector-cypher-search": {
      "command": "python",
      "args": ["src/mcp_vector_cypher_search.py"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "password123",
        "VECTOR_INDEX_NAME": "chunk_embeddings",
        "SIMILARITY_THRESHOLD": "0.8",
        "TOP_K_CHUNKS": "5"
      }
    }
  }
}
```

## Usage

### Available Tools

#### 1. `vector_cypher_search(question: str)`
Main search function that intelligently routes queries and returns comprehensive results.

**Parameters:**
- `question`: The search question or query string

**Returns:**
```json
{
  "search_type": "vector|direct_cypher|error",
  "chunks": [
    {
      "content": "chunk content...",
      "chunk_id": "chunk_123",
      "source_id": "article_456",
      "title": "Article Title",
      "url": "https://example.com/article",
      "similarity_score": 0.85
    }
  ],
  "cypher_query": "MATCH (n:Article) RETURN n.title, n.content LIMIT 10",
  "cypher_results": [
    {"title": "Article 1", "content": "Content..."},
    {"title": "Article 2", "content": "Content..."}
  ],
  "metadata": {
    "question": "original question",
    "chunks_found": 3,
    "cypher_records": 10,
    "vector_search_used": true,
    "embedding_dimension": 384
  }
}
```

#### 2. `configure_search_parameters(...)`
Configure search behavior and parameters.

**Parameters:**
- `similarity_threshold`: Minimum similarity score (0.0-1.0)
- `top_k_chunks`: Maximum chunks to return
- `vector_index_name`: Neo4j vector index name

## Query Examples

### Vector Search Triggers
These questions will use vector similarity search:

```
"Find articles about machine learning"
"What content discusses artificial intelligence?"
"Show me information about data science"
"Tell me about recent developments"
"What are the latest trends?"
```

### Direct Cypher Triggers
These questions will use direct Cypher generation:

```
"How many users are in the database?"
"Show me all user names and emails"
"What companies have more than 100 employees?"
"List all products ordered by price"
"Find relationships between users and companies"
```

## Neo4j Requirements

### Vector Index Setup
Your Neo4j database should have a vector index for embeddings:

```cypher
CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
FOR (n:Chunk) ON (n.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 384,
    `vector.similarity_function`: 'cosine'
  }
}
```

### Expected Node Structure
```cypher
// Chunk nodes for vector search
(:Chunk {
  content: "text content...",
  chunk_id: "unique_id",
  source_id: "parent_document_id",
  title: "document title",
  url: "source url",
  embedding: [0.1, 0.2, 0.3, ...] // 384-dimensional vector
})

// Other entity nodes for structured queries
(:Article {title: "...", content: "...", url: "..."})
(:User {name: "...", email: "..."})
(:Company {name: "...", employees: 100})
```

## Configuration Options

### Environment Variables
- `NEO4J_URI`: Neo4j connection URI (default: "bolt://localhost:7687")
- `NEO4J_USER`: Neo4j username (default: "neo4j")
- `NEO4J_PASSWORD`: Neo4j password (default: "password123")
- `VECTOR_INDEX_NAME`: Vector index name (default: "chunk_embeddings")
- `SIMILARITY_THRESHOLD`: Minimum similarity score (default: 0.8)
- `TOP_K_CHUNKS`: Maximum chunks to return (default: 5)

### Runtime Configuration
Use the `configure_search_parameters` tool to adjust settings during runtime:

```python
# Example MCP call
configure_search_parameters(
    similarity_threshold=0.7,
    top_k_chunks=10,
    vector_index_name="custom_embeddings"
)
```

## Integration with Existing Services

### MCP Neo4j Cypher Integration
The server integrates with the existing `mcp-neo4j-cypher` service:
- Calls the service for Cypher query generation
- Enhances queries with vector search context
- Falls back to basic query generation if service unavailable

### Boomer Vector Embedding Creator
Shares the same embedding model (`all-MiniLM-L6-v2`) for consistency:
- Same 384-dimensional embeddings
- Compatible with existing vector indexes
- Consistent similarity calculations

## Error Handling

The server provides comprehensive error handling:

- **Empty Questions**: Returns error response for empty/null questions
- **Neo4j Connection**: Graceful handling of database connection issues
- **Vector Index**: Handles missing or misconfigured vector indexes
- **MCP Service**: Falls back to basic queries if external MCP services fail
- **Embedding Generation**: Handles model loading and encoding errors

## Performance Considerations

### Optimization Tips
1. **Vector Index Tuning**: Optimize vector index configuration for your data
2. **Similarity Threshold**: Adjust threshold based on your content similarity requirements
3. **Chunk Size**: Balance between context and performance when creating chunks
4. **Connection Pooling**: Neo4j driver handles connection pooling automatically

### Monitoring
The server provides detailed logging for:
- Query routing decisions
- Vector search performance
- Cypher query execution
- Error conditions and recovery

## Testing

Run the test suite to verify functionality:

```bash
python scripts/test_mcp_vector_cypher_search.py
```

The test suite covers:
- Vector search question routing
- Direct Cypher question routing
- Configuration management
- Error handling scenarios

## Troubleshooting

### Common Issues

1. **No Vector Results**: Check vector index exists and has data
2. **Connection Errors**: Verify Neo4j credentials and URI
3. **Embedding Errors**: Ensure SentenceTransformer model can load
4. **MCP Integration**: Verify mcp-neo4j-cypher service is available

### Debug Logging
Enable debug logging for detailed troubleshooting:

```python
import logging
logging.getLogger("mcp-vector-cypher-search").setLevel(logging.DEBUG)
```

## Future Enhancements

Potential improvements for future versions:
- Support for multiple embedding models
- Advanced query routing with ML classification
- Caching for frequently accessed embeddings
- Integration with additional MCP services
- Real-time vector index updates