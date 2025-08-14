# Batch Loader MCP Integration

## Overview

The Batch Loader now supports integration with MCP (Model Context Protocol) servers for intelligent Cypher query generation and vector search capabilities.

## Current Status

### ✅ **MCP Integration Available**

The batch loader can now connect to MCP servers:

1. **MCP Cypher Server**: For natural language to Cypher query generation
2. **MCP Vector Search Server**: For semantic search capabilities
3. **Fallback Support**: Graceful degradation when MCP servers are unavailable

## Architecture

```
Batch Loader
    ├── MCP Cypher Client
    │   ├── Natural Language → Cypher Query
    │   └── Fallback Generation
    ├── MCP Vector Search Client
    │   ├── Question → Vector Search Query
    │   └── Fallback Vector Search
    └── Neo4j Data Loader
        └── Direct Cypher Execution
```

## Features

### 1. **MCP Cypher Query Generation**

```python
# Generate Cypher from natural language
cypher = loader.generate_cypher_with_mcp("create article node with title and content")
# Returns: MERGE (n:Article {id: $id}) SET n += $properties
```

### 2. **MCP Vector Search**

```python
# Generate vector search query
vector_query = loader.search_with_mcp_vector("retirement planning strategies", top_k=5)
# Returns: Vector similarity search Cypher query
```

### 3. **Automatic Fallback**

When MCP servers are unavailable, the system automatically falls back to basic query generation.

## Configuration

### MCP Server Configuration

The batch loader reads MCP configuration from `config/claude_desktop_mcp_config.json`:

```json
{
  "mcpServers": {
    "mcp-cypher": {
      "command": "/Users/ravikiranponduri/.local/bin/uvx",
      "args": ["mcp-neo4j-cypher@0.2.3"],
      "env": {
        "NEO4J_URL": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "password123",
        "NEO4J_DATABASE": "neo4j"
      }
    }
  }
}
```

### Docker MCP Services

Available MCP services in `docker-compose-neo4j-mcp.yml`:

- `mcp-neo4j-cypher`: Official Neo4j MCP Cypher server
- `mcp-vector-cypher-search`: Custom vector search server
- `mcp-neo4j-data-modeling`: Data modeling server

## Usage Examples

### 1. **Basic MCP Integration**

```python
from src.batch_loader import BatchNeo4jLoader

# Initialize batch loader (automatically loads MCP clients)
loader = BatchNeo4jLoader()

# Use MCP for query generation
cypher = loader.generate_cypher_with_mcp("find all articles about retirement")
print(cypher)
```

### 2. **Vector Search with MCP**

```python
# Generate vector search query
vector_query = loader.search_with_mcp_vector(
    "What are the best investment strategies for seniors?",
    top_k=10
)

# Execute the query
result = loader.execute_cypher_query(vector_query)
```

### 3. **Check MCP Availability**

```python
if loader.mcp_cypher_client:
    print("MCP Cypher server is available")
else:
    print("Using fallback query generation")

if loader.mcp_vector_client:
    print("MCP Vector Search server is available")
else:
    print("Using fallback vector search")
```

## Testing

### Run MCP Integration Test

```bash
cd boomertv2
python scripts/test_batch_loader_mcp.py
```

This will test:
- MCP configuration loading
- Cypher query generation
- Vector search generation
- Client availability status

### Expected Output

```
🔧 Testing MCP Configuration Loading:
✅ Loaded 2 MCP clients:
   - mcp-cypher: mcp-cypher
   - mcp-vector-cypher-search: mcp-vector-cypher-search

🧪 Testing MCP Integration with Batch Loader
1. Testing MCP Cypher Query Generation:
Request: create article node with title and content
Generated Cypher: MERGE (n:Article {id: $id}) SET n += $properties

2. Testing MCP Vector Search:
Question: What are the best retirement strategies?
Vector Search Query: MATCH (c:Chunk) WHERE c.embedding IS NOT NULL RETURN c.chunk_text, c.chunk_id LIMIT 3

3. MCP Client Status:
✅ MCP Cypher client is available
✅ MCP Vector Search client is available
```

## Setup Instructions

### 1. **Install MCP Dependencies**

```bash
# Install uvx (MCP client tool)
pip install uv
uvx install mcp-neo4j-cypher@latest

# Or use Docker
docker-compose -f config/docker-compose-neo4j-mcp.yml up -d
```

### 2. **Configure MCP Servers**

Update `config/claude_desktop_mcp_config.json` with your Neo4j credentials:

```json
{
  "mcpServers": {
    "mcp-cypher": {
      "command": "/path/to/uvx",
      "args": ["mcp-neo4j-cypher@0.2.3"],
      "env": {
        "NEO4J_URL": "bolt://your-neo4j-host:7687",
        "NEO4J_USERNAME": "your-username",
        "NEO4J_PASSWORD": "your-password",
        "NEO4J_DATABASE": "neo4j"
      }
    }
  }
}
```

### 3. **Start MCP Services**

```bash
# Start Docker MCP services
docker-compose -f config/docker-compose-neo4j-mcp.yml up -d

# Or start individual services
docker exec -i mcp_neo4j_cypher uvx mcp-neo4j-cypher@latest
docker exec -i mcp_vector_cypher_search python src/mcp_vector_cypher_search.py
```

## Benefits

### 1. **Intelligent Query Generation**
- Natural language to Cypher translation
- Context-aware query optimization
- Schema-aware query generation

### 2. **Semantic Search**
- Vector similarity search
- Natural language question answering
- Content-aware retrieval

### 3. **Graceful Degradation**
- Automatic fallback when MCP unavailable
- No interruption to batch loading process
- Maintains existing functionality

### 4. **Extensibility**
- Easy to add new MCP servers
- Configurable client management
- Modular architecture

## Troubleshooting

### Common Issues

1. **MCP Client Not Available**
   - Check MCP server is running
   - Verify configuration file path
   - Check network connectivity

2. **Query Generation Fails**
   - MCP server returns error
   - Fallback to basic generation
   - Check server logs

3. **Configuration Loading Error**
   - Verify JSON syntax
   - Check file permissions
   - Validate server configuration

### Debug Commands

```bash
# Check MCP server status
docker ps | grep mcp

# View MCP server logs
docker logs mcp_neo4j_cypher
docker logs mcp_vector_cypher_search

# Test MCP configuration
python scripts/test_batch_loader_mcp.py

# Check MCP client connectivity
python -c "from src.mcp_client import get_mcp_cypher_client; print(get_mcp_cypher_client())"
```

## Future Enhancements

1. **Advanced MCP Features**
   - Schema-aware query optimization
   - Query performance analysis
   - Automatic query tuning

2. **Additional MCP Servers**
   - Data validation server
   - Query optimization server
   - Analytics server

3. **Enhanced Integration**
   - Real-time MCP monitoring
   - Automatic failover
   - Performance metrics

## Conclusion

The batch loader now provides seamless MCP integration for intelligent Cypher query generation and vector search capabilities, while maintaining backward compatibility and graceful fallback mechanisms.
