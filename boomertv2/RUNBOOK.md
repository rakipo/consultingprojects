# PostgreSQL to Neo4j Pipeline - Runbook

## Quick Start Commands

### 1. Environment Setup
```bash
# Start all services
docker-compose -f config/docker-compose-neo4j-mcp.yml up -d

# Check service status
docker ps

# Stop all services
docker-compose -f config/docker-compose-neo4j-mcp.yml down
```

### 2. Database Operations

#### Neo4j Management
```bash
# Reset Neo4j database (clears all data)
./scripts/reset_neo4j_database.sh

# Access Neo4j browser
open http://localhost:7474
# Login: neo4j/password123

# Direct cypher shell access
docker exec -it neo4j_db cypher-shell -u neo4j -p password123
```

#### PostgreSQL Connection
```bash
# Test PostgreSQL connection
python src/postgres_query_runner.py config/config_boomer_load.yml
```

### 3. Data Pipeline

#### Generate Neo4j Model
```bash
# Create Neo4j model from PostgreSQL data
python src/neo4j_model_generator.py config/config_boomer_load.yml output/data/neo4j_model_$(date +%Y%m%d_%H%M%S).json
```

#### Load Data to Neo4j
```bash
# Load data using generated model
python src/neo4j_data_loader.py config/config_boomer_load.yml output/data/neo4j_model_YYYYMMDD_HHMMSS.json output/metrics/load_metrics_$(date +%Y%m%d_%H%M%S).json
```

#### Full Pipeline (Model + Load)
```bash
# Generate model and load data in one go
python src/neo4j_model_generator.py config/config_boomer_load.yml output/data/neo4j_model_$(date +%Y%m%d_%H%M%S).json --load-data
```

### 4. Vector Embeddings

#### Create Embeddings
```bash
# Generate vector embeddings for content
python src/boomer_vector_embedding_creator.py config/config_boomer_load.yml output/data/embeddings_$(date +%Y%m%d_%H%M%S).json
```

#### Test Vector Search
```bash
# Test MCP vector search functionality
python scripts/test_mcp_vector_cypher_search.py
```

### 5. Monitoring & Debugging

#### Check Logs
```bash
# Neo4j logs
docker logs neo4j_db --tail 50

# MCP services logs
docker logs mcp_neo4j_cypher --tail 20
docker logs mcp_vector_cypher_search --tail 20
```

#### Database Stats
```bash
# Quick Neo4j stats
docker exec neo4j_db cypher-shell -u neo4j -p password123 "MATCH (n) RETURN labels(n) as label, count(n) as count"

# Relationship counts
docker exec neo4j_db cypher-shell -u neo4j -p password123 "MATCH ()-[r]->() RETURN type(r) as relationship, count(r) as count"
```

### 6. Configuration Files

#### Key Config Files
- `config/config_boomer_load.yml` - Main pipeline configuration
- `config/docker-compose-neo4j-mcp.yml` - Docker services
- `config/mcp_vector_cypher_search_config.json` - MCP client config

#### Environment Variables
```bash
# Required for OpenAI (optional for LLM chunking)
export OPENAI_API_KEY="your-key-here"

# Neo4j connection (auto-configured in Docker)
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="password123"
```

### 7. Common Workflows

#### Fresh Start
```bash
# 1. Reset everything
docker-compose -f config/docker-compose-neo4j-mcp.yml down
./scripts/reset_neo4j_database.sh

# 2. Start services
docker-compose -f config/docker-compose-neo4j-mcp.yml up -d

# 3. Generate and load data
python src/neo4j_model_generator.py config/config_boomer_load.yml output/data/neo4j_model_$(date +%Y%m%d_%H%M%S).json --load-data
```

#### Data Refresh
```bash
# 1. Clear Neo4j data only
./scripts/reset_neo4j_database.sh

# 2. Reload with existing model
python src/neo4j_data_loader.py config/config_boomer_load.yml output/data/neo4j_model_LATEST.json output/metrics/load_metrics_$(date +%Y%m%d_%H%M%S).json
```

#### Model Update
```bash
# 1. Generate new model
python src/neo4j_model_generator.py config/config_boomer_load.yml output/data/neo4j_model_$(date +%Y%m%d_%H%M%S).json

# 2. Reset and load with new model
./scripts/reset_neo4j_database.sh
python src/neo4j_data_loader.py config/config_boomer_load.yml output/data/neo4j_model_LATEST.json output/metrics/load_metrics_$(date +%Y%m%d_%H%M%S).json
```

### 8. Troubleshooting

#### Common Issues
```bash
# Neo4j not responding
docker restart neo4j_db

# Check Neo4j health
docker exec neo4j_db cypher-shell -u neo4j -p password123 'RETURN 1'

# PostgreSQL connection issues
# Check config/config_boomer_load.yml database settings

# MCP services not working
docker restart mcp_neo4j_cypher mcp_vector_cypher_search

# Clear Docker volumes (nuclear option)
docker-compose -f config/docker-compose-neo4j-mcp.yml down -v
```

#### File Locations
- **Models**: `output/data/neo4j_model_*.json`
- **Metrics**: `output/metrics/load_metrics_*.json`
- **Logs**: `output/logs/`
- **Scripts**: `scripts/`
- **Source**: `src/`

### 9. Useful Cypher Queries

```cypher
-- Count all nodes by type
MATCH (n) RETURN labels(n) as label, count(n) as count

-- Count all relationships by type
MATCH ()-[r]->() RETURN type(r) as relationship, count(r) as count

-- Find articles with most tags
MATCH (a:Article)-[:TAGGED_WITH]->(t:Tag)
RETURN a.title, count(t) as tag_count
ORDER BY tag_count DESC LIMIT 10

-- Vector similarity search (if embeddings loaded)
CALL db.index.vector.queryNodes('chunk_embeddings', 5, [0.1, 0.2, ...])
YIELD node, score
RETURN node.chunk_text, score
```

---

**Note**: Replace `YYYYMMDD_HHMMSS` with actual timestamps from generated files, or use `$(date +%Y%m%d_%H%M%S)` for current timestamp.