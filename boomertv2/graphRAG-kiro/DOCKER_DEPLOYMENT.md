# Docker Deployment Guide

This guide explains how to deploy the GraphRAG Retrieval Agent using Docker.

## Quick Start

### 1. Using Docker Compose (Recommended)

The easiest way to deploy the complete system with Neo4j:

```bash
# Start the complete system
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f graphrag-agent

# Stop the system
docker-compose down
```

### 2. Using Docker Build

Build and run the container manually:

```bash
# Build the image
docker build -t graphrag-agent .

# Run with environment variables
docker run -d \
  --name graphrag-agent \
  -e NEO4J_URI=bolt://your-neo4j-host:7687 \
  -e NEO4J_USERNAME=neo4j \
  -e NEO4J_PASSWORD=your-password \
  -v $(pwd)/logs:/app/logs \
  graphrag-agent
```

## Configuration

### Environment Variables

The container supports the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `NEO4J_URI` | Neo4j connection URI | `bolt://localhost:7687` |
| `NEO4J_USERNAME` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | `password` |
| `NEO4J_DATABASE` | Neo4j database name | `neo4j` |
| `EMBEDDING_MODEL` | Sentence transformer model | `all-MiniLM-L6-v2` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Volume Mounts

- `/app/logs` - Log files (recommended to mount externally)
- `/app/config` - Configuration files (optional, read-only)

## Usage Modes

### 1. MCP Server Mode (Default)

The container runs the MCP server by default:

```bash
docker-compose up -d graphrag-agent
```

### 2. CLI Mode

Run one-off CLI commands:

```bash
# Check system status
docker-compose run --rm graphrag-cli python main.py status

# Perform a query
docker-compose run --rm graphrag-cli python main.py query "What is machine learning?"

# Run tests
docker-compose run --rm graphrag-cli python tests/test_runner.py
```

### 3. Interactive Mode

Run an interactive session:

```bash
docker-compose run --rm graphrag-cli bash
```

## Neo4j Setup

### Using Docker Compose Neo4j

The included `docker-compose.yml` sets up Neo4j automatically:

- **Web Interface**: http://localhost:7474
- **Bolt Port**: 7687
- **Username**: neo4j
- **Password**: graphrag_password

### Using External Neo4j

To use an external Neo4j instance:

1. Update environment variables in `docker-compose.yml`
2. Or set them when running the container directly

```yaml
environment:
  - NEO4J_URI=bolt://your-external-neo4j:7687
  - NEO4J_USERNAME=your-username
  - NEO4J_PASSWORD=your-password
```

## Data Loading

Before using the system, you need to load data into Neo4j:

1. **Connect to Neo4j**: Use the web interface at http://localhost:7474
2. **Create Vector Index**: 
   ```cypher
   CREATE VECTOR INDEX chunk_embeddings FOR (c:Chunk) ON c.embedding
   OPTIONS {indexConfig: {
     `vector.dimensions`: 384,
     `vector.similarity_function`: 'cosine'
   }}
   ```
3. **Load Your Data**: Import your chunks, articles, and authors with embeddings

## Health Checks

The container includes health checks:

```bash
# Check container health
docker-compose ps

# View health check logs
docker inspect graphrag-agent --format='{{.State.Health.Status}}'
```

## Troubleshooting

### Common Issues

1. **Neo4j Connection Failed**
   - Check Neo4j is running: `docker-compose ps neo4j`
   - Verify connection settings in environment variables
   - Check network connectivity: `docker-compose exec graphrag-agent ping neo4j`

2. **Permission Denied on Logs**
   ```bash
   sudo chown -R 1000:1000 logs/
   ```

3. **Model Download Issues**
   - The first run downloads the embedding model
   - Ensure internet connectivity
   - Check disk space

### Debugging

Enable debug logging:

```bash
docker-compose run -e LOG_LEVEL=DEBUG graphrag-agent
```

View detailed logs:

```bash
docker-compose logs -f --tail=100 graphrag-agent
```

## Production Deployment

### Security Considerations

1. **Change Default Passwords**
   ```yaml
   environment:
     - NEO4J_PASSWORD=your-secure-password
   ```

2. **Use Secrets Management**
   ```yaml
   secrets:
     neo4j_password:
       file: ./secrets/neo4j_password.txt
   ```

3. **Network Security**
   - Use internal networks
   - Expose only necessary ports
   - Consider using reverse proxy

### Resource Limits

Add resource limits to `docker-compose.yml`:

```yaml
services:
  graphrag-agent:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
```

### Monitoring

Set up monitoring with health checks and log aggregation:

```yaml
services:
  graphrag-agent:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Scaling

For high availability:

1. **Multiple Agent Instances**
   ```bash
   docker-compose up -d --scale graphrag-agent=3
   ```

2. **Load Balancer**
   - Use nginx or HAProxy
   - Balance MCP connections

3. **Neo4j Clustering**
   - Use Neo4j Enterprise
   - Configure cluster in docker-compose

## Backup and Recovery

### Neo4j Backup

```bash
# Backup Neo4j data
docker-compose exec neo4j neo4j-admin database dump neo4j

# Restore from backup
docker-compose exec neo4j neo4j-admin database load neo4j
```

### Configuration Backup

```bash
# Backup configuration
tar -czf graphrag-backup.tar.gz config/ docker-compose.yml
```