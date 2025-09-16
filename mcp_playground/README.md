# MCP Vector Cypher Search

A Model Context Protocol (MCP) server that combines vector similarity search with Cypher query generation for Neo4j databases. This server intelligently routes queries between vector search for content-based queries and direct Cypher execution for analytical queries.

Note: while searching in claude to get to this mcp give the clue to the claude chat mention like "In my DB".

## Features

- 🔍 **Intelligent Query Routing**: Automatically determines whether to use vector search or direct Cypher based on query intent
- 🚀 **Vector Similarity Search**: Uses SentenceTransformers for semantic search on content chunks
- 📊 **Direct Cypher Queries**: Optimized for analytical queries (counts, statistics, schema queries)
- 📝 **Comprehensive Logging**: Detailed execution paths, performance metrics, and results logging
- 🛡️ **Database-Only Responses**: Prevents fallback to general knowledge when no data is found
- ⚡ **Performance Optimized**: Direct Cypher queries are 4-5x faster than vector search

## Architecture

```
Query Input
    ↓
Query Classification
    ↓
┌─────────────────┬─────────────────┐
│  Vector Search  │  Direct Cypher  │
│  (Content)      │  (Analytics)    │
├─────────────────┼─────────────────┤
│ • "GPT 4o"      │ • "Top tags"    │
│ • "AI models"   │ • "How many"    │
│ • "Explain..."  │ • "Count..."    │
│ • Content queries│ • Statistics   │
└─────────────────┴─────────────────┘
    ↓
Neo4j Database Query
    ↓
Structured Response + Logging
```

## Prerequisites

- Python 3.8+
- Neo4j database with vector index
- Docker (for containerized deployment)
- Claude Desktop (for MCP integration)

## Installation

### Option 1: Local Python Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd mcp-vector-cypher-search
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env with your Neo4j connection details
```

### Option 2: Docker Installation

1. **Use the provided Docker Compose setup**:
```bash
docker-compose -f docker-compose-neo4j-mcp.yml up -d mcp-vector-cypher-search
```

## Configuration

### Environment Variables

Create a `.env` file with your Neo4j connection details:

```env
# Neo4j Configuration
NEO4J_URI=neo4j://your-neo4j-host:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j

# Vector Search Configuration
VECTOR_INDEX_NAME=chunk_embedding_vector
SIMILARITY_THRESHOLD=0.8
TOP_K_CHUNKS=10

# MCP Server Configuration
MCP_LOG_LEVEL=INFO
```

### Docker Compose Configuration

The `docker-compose-neo4j-mcp.yml` includes a complete setup:

```yaml
services:
  mcp-vector-cypher-search:
    image: python:3.11-slim
    container_name: mcp_vector_cypher_search
    working_dir: /app
    volumes:
      - /path/to/your/project:/app
    environment:
      - NEO4J_URI=neo4j://your-neo4j-host:7687
      - NEO4J_USERNAME=neo4j
      - NEO4J_PASSWORD=your-password
      - NEO4J_DATABASE=neo4j
      - VECTOR_INDEX_NAME=chunk_embedding_vector
      - SIMILARITY_THRESHOLD=0.8
      - TOP_K_CHUNKS=10
      - PYTHONPATH=/app
    command: >
      sh -c "
        pip install --no-cache-dir neo4j==5.15.0 sentence-transformers==2.2.2 mcp>=0.1.0 python-dotenv>=1.0.0 &&
        echo 'MCP Vector Cypher Search Server ready for connections' &&
        tail -f /dev/null
      "
    restart: unless-stopped
    stdin_open: true
    tty: true
```

## Running the MCP Server

### Method 1: Direct Python Execution

```bash
# Run the MCP server directly
python mcp_vector_cypher_search.py
```

### Method 2: Docker Container

```bash
# Start the container
docker-compose -f docker-compose-neo4j-mcp.yml up -d mcp-vector-cypher-search

# Run the MCP server inside the container
docker exec -i mcp_vector_cypher_search python -u /app/mcp_vector_cypher_search.py
```

### Method 3: Background Docker Process

```bash
# Start the MCP server as a background process in Docker
docker exec -d mcp_vector_cypher_search python -u /app/mcp_vector_cypher_search.py
```

## Claude Desktop Configuration

### Option 1: Workspace-Level Configuration

Create `.kiro/settings/mcp.json` in your project directory:

```json
{
  "mcpServers": {
    "mcp-vector-cypher-search": {
      "command": "docker",
      "args": ["exec", "-i", "mcp_vector_cypher_search", "python", "-u", "/app/mcp_vector_cypher_search.py"],
      "disabled": false,
      "autoApprove": ["vector_cypher_search", "debug_configuration", "configure_search_parameters"]
    }
  }
}
```

### Option 2: User-Level Configuration

Edit `~/.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "mcp-vector-cypher-search": {
      "command": "python",
      "args": ["-u", "/path/to/your/project/mcp_vector_cypher_search.py"],
      "cwd": "/path/to/your/project",
      "env": {
        "NEO4J_URI": "neo4j://your-neo4j-host:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "your-password",
        "NEO4J_DATABASE": "neo4j",
        "VECTOR_INDEX_NAME": "chunk_embedding_vector",
        "SIMILARITY_THRESHOLD": "0.8",
        "TOP_K_CHUNKS": "10"
      },
      "disabled": false,
      "autoApprove": ["vector_cypher_search", "debug_configuration", "configure_search_parameters"]
    }
  }
}
```

### Option 3: Claude Desktop Config

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "mcp-vector-cypher-search": {
      "command": "docker",
      "args": ["exec", "-i", "mcp_vector_cypher_search", "python", "-u", "/app/mcp_vector_cypher_search.py"]
    }
  }
}
```

## Usage Examples

### Content-Based Queries (Vector Search)
These queries will use vector similarity search to find relevant content chunks:

```
"GPT 4o capabilities"
"artificial intelligence models"
"machine learning algorithms"
"explain neural networks"
"what is deep learning"
```

**Execution Path**: `Vector Search → Cypher Query → Results`

### Analytical Queries (Direct Cypher)
These queries will skip vector search and go directly to Cypher:

```
"How many articles"
"Top tags by density"
"Count of nodes"
"Database insights"
"Most frequent authors"
"Website statistics"
```

**Execution Path**: `Direct Cypher → Results`

## Available MCP Tools

### 1. `vector_cypher_search`
Main search function that intelligently routes queries.

```python
# Example usage in Claude Desktop
result = await vector_cypher_search("GPT 4o performance")
```

### 2. `debug_configuration`
Check current configuration and environment variables.

```python
config = await debug_configuration()
```

### 3. `configure_search_parameters`
Dynamically adjust search parameters.

```python
result = await configure_search_parameters(
    similarity_threshold=0.7,
    top_k_chunks=15,
    vector_index_name="my_custom_index"
)
```

## Logging

The server provides comprehensive logging to help debug and monitor query execution:

### Log File Location
- **Docker**: `/app/logs/mcp_vector_cypher_search_YYYYMMDD.log`
- **Local**: `./logs/mcp_vector_cypher_search_YYYYMMDD.log`

### Log Contents
- Query execution paths
- Performance metrics
- Similarity scores
- Cypher queries generated
- Results summaries
- Error details

### Example Log Entry
```json
{
  "timestamp": "2025-08-14T13:35:29.507904",
  "query": "GPT 4o",
  "search_type": "vector",
  "execution_path": [
    "query_received",
    "strategy_vector",
    "vector_search_start",
    "embedding_creation",
    "vector_similarity_search",
    "cypher_generation",
    "cypher_execution",
    "results_analysis",
    "data_found"
  ],
  "results": {
    "chunks_found": 3,
    "cypher_records": 5,
    "execution_time_seconds": 2.37
  },
  "result_summary": {
    "status": "success",
    "message": "Found 3 relevant content chunks in my Neo4j database.",
    "top_chunk_scores": [0.8234, 0.8231, 0.8226]
  }
}
```

## Troubleshooting

### Common Issues

1. **Connection Refused Error**
   ```
   Failed to establish connection to Neo4j
   ```
   - Check Neo4j is running
   - Verify connection details in `.env`
   - Ensure Neo4j is accessible from Docker container

2. **Vector Index Not Found**
   ```
   Vector index 'chunk_embedding_vector' not found
   ```
   - Create vector index in Neo4j
   - Update `VECTOR_INDEX_NAME` in configuration

3. **MCP Server Not Starting**
   - Check Docker container is running: `docker ps`
   - Verify Python dependencies are installed
   - Check logs: `docker logs mcp_vector_cypher_search`

### Testing the Setup

Run the test scenarios to verify everything is working:

```bash
# Test inside Docker container
docker exec mcp_vector_cypher_search python -c "
import asyncio
from mcp_vector_cypher_search import vector_cypher_search

async def test():
    result = await vector_cypher_search('GPT 4o')
    print('Test successful:', result['search_type'])

asyncio.run(test())
"
```

## Performance

- **Vector Search Queries**: ~2-3 seconds (includes embedding generation)
- **Direct Cypher Queries**: ~0.4-0.6 seconds
- **Memory Usage**: ~200-500MB (depending on embedding model)
- **Concurrent Requests**: Supports multiple simultaneous queries

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the log files
3. Open an issue on GitHub
4. Provide log excerpts and configuration details