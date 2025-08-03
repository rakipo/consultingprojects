# README.md

# PostgreSQL to Neo4j Pipeline

Automated ingestion pipeline that extracts articles from PostgreSQL, transforms them via Claude API into graph format, and loads into Neo4j.

## Quick Start

```bash
# 1. Clone and setup
git clone <repo>
cd postgres-neo4j-pipeline

# 2. Configure environment
cp config/.env.example config/.env
# Edit config/.env with your credentials

# 3. Start services
docker-compose up -d

# 4. Initialize Neo4j schema
docker exec neo4j cypher-shell -f /schema/init.cypher

# 5. Run pipeline
python pipeline/ingest.py
```

## Architecture

```
PostgreSQL → Claude API → Neo4j
     ↓           ↓         ↓
  Articles   Transform   Graph
```

## File Structure

```
project/
├── README.md
├── docker-compose.yml
├── requirements.txt
├── config/
│   ├── .env.example
│   ├── mcp_config.json
│   └── neo4j_setup.md
├── schema/
│   └── init.cypher
├── pipeline/
│   └── ingest.py
└── prompts/
    ├── entity_rules.md
    └── transform_article.md
```

## Configuration

### Environment Variables (.env)
```bash
# PostgreSQL
PG_HOST=localhost
PG_DATABASE=content_db
PG_USER=postgres
PG_PASSWORD=your_password

# Neo4j  
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Claude
CLAUDE_API_KEY=your_claude_key
```

### PostgreSQL Table Schema
```sql
CREATE TABLE structured_content (
    id VARCHAR PRIMARY KEY,
    title TEXT,
    content TEXT,
    tags TEXT[],
    author VARCHAR,
    publish_date TIMESTAMP,
    domain VARCHAR
);
```

## Usage

### Run Full Pipeline
```bash
python pipeline/ingest.py
```

### Run for Specific Days
```bash
# Last 30 days
python -c "
from pipeline.ingest import GraphIngestion
from dotenv import load_dotenv
load_dotenv()
pipeline = GraphIngestion()
pipeline.run_pipeline(days=30)
pipeline.close()
"
```

### Validate Schema
```bash
python -c "
from pipeline.ingest import GraphIngestion
pipeline = GraphIngestion()
print('Valid:', pipeline.validate_schema())
pipeline.close()
"
```

## Graph Schema

### Nodes
- **Article**: id, title, publish_date, domain
- **Author**: name  
- **Topic**: name (from tags)
- **Entity**: name, type (PERSON|ORGANIZATION|TECHNOLOGY|CONCEPT)

### Relationships
- **Article** -[WRITTEN_BY]-> **Author**
- **Article** -[TAGS]-> **Topic** 
- **Article** -[MENTIONS]-> **Entity**

## Monitoring

### Logs
```bash
# Pipeline logs
tail -f pipeline.log

# Neo4j logs
docker logs neo4j

# MCP server logs  
docker logs neo4j-mcp
```

### Neo4j Browser
Access at http://localhost:7474
```cypher
// Check article count
MATCH (a:Article) RETURN count(a)

// View recent articles
MATCH (a:Article) 
RETURN a.title, a.publish_date 
ORDER BY a.publish_date DESC 
LIMIT 10

// Check relationships
MATCH (a:Article)-[r]->(n) 
RETURN type(r), count(r)
```

## Troubleshooting

### Common Issues

**Claude API fails**
- Check API key in .env
- Pipeline uses fallback entity extraction

**Neo4j connection error**
- Verify docker-compose services running
- Check NEO4J_URI in .env

**PostgreSQL extraction fails**
- Verify table schema matches expected format
- Check PG credentials in .env

**Schema validation fails**
```bash
docker exec neo4j cypher-shell -f /schema/init.cypher
```

### Performance Tuning

**Large datasets (>10k articles)**
- Batch processing: modify `run_pipeline()` to process in chunks
- Increase Neo4j memory: add to docker-compose.yml:
```yaml
environment:
  NEO4J_dbms_memory_heap_max__size: 2G
```

**Rate limiting Claude API**
- Add delay between requests in `transform_to_graph()`
- Consider Claude batch API for high volume

## Development

### Adding New Entity Types
1. Update `extract_entities()` in pipeline/ingest.py
2. Add patterns to prompts/entity_rules.md
3. Update Claude prompt in prompts/transform_article.md

### Testing
```bash
# Test single article
python -c "
from pipeline.ingest import GraphIngestion
pipeline = GraphIngestion()
articles = pipeline.extract_articles(days=1)
if articles:
    result = pipeline.transform_to_graph(articles[0])
    print(result)
pipeline.close()
"
```

## Support

- Neo4j Browser: http://localhost:7474
- MCP Server: http://localhost:8080
- Logs: `docker logs <service_name>`