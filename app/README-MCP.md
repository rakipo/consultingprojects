# MCP Neo4j Integration - Complete Setup Guide

This guide provides comprehensive instructions for setting up and running the MCP (Model Context Protocol) Neo4j integration with PostgreSQL data modeling and Cypher query capabilities.

## 📋 Setup Files Reference

- **`complete-setup.sh`**: Automated setup script (recommended)
- **`SETUP-SEQUENCE.md`**: Detailed step-by-step manual instructions
- **`docker-compose-mcp.yml`**: Multi-service Docker configuration
- **`README-MCP.md`**: This comprehensive guide

## 🏗️ Architecture Overview

The system consists of:
- **PostgreSQL Database**: Stores structured content with 100 sample publications
- **Neo4j Database**: Graph database for relationship modeling
- **MCP Data Modeling Server**: Handles data transformation and migration
- **MCP Cypher Server**: Executes Cypher queries and graph operations
- **MCP Manager**: Web interface for monitoring and management
- **pgAdmin**: PostgreSQL administration interface

## 🚀 Quick Start

### Option 1: Automated Complete Setup (Recommended)
```bash
# Run the complete automated setup sequence
./complete-setup.sh

# This script will:
# 1. Start all MCP services
# 2. Wait for services to be ready
# 3. Verify PostgreSQL data (100 records)
# 4. Migrate data to Neo4j
# 5. Verify graph population
# 6. Display access information
```

### Option 2: Manual Step-by-Step Setup
```bash
# Use the MCP-enabled Docker Compose file
docker-compose -f docker-compose-mcp.yml up -d

# Check all services are running
docker-compose -f docker-compose-mcp.yml ps

# Follow detailed steps in SETUP-SEQUENCE.md
```

### 2. Access Points
- **MCP Manager Dashboard**: http://localhost:8000
- **Neo4j Browser**: http://localhost:7474 (neo4j/password123)
- **pgAdmin**: http://localhost:8080 (admin@movies.com/admin123)
- **PostgreSQL**: localhost:5432 (postgres/password123)

### 3. pgAdmin Server Setup
After accessing pgAdmin, add the PostgreSQL server:

1. **Login to pgAdmin**: http://localhost:8080
   - Email: `admin@movies.com`
   - Password: `admin123`

2. **Add New Server**:
   - Right-click "Servers" → "Create" → "Server..."
   - **General Tab**: Name: `MCP PostgreSQL Database`
   - **Connection Tab**:
     - **Host name/address**: `postgres` (Docker service name)
     - **Port**: `5432`
     - **Maintenance database**: `movies`
     - **Username**: `postgres`
     - **Password**: `password123`
   - Click "Save"

**⚠️ Important**: Always use `postgres` as hostname (Docker service name), never use `localhost`, `127.0.0.1`, or container names like `mcp_postgres`.

### 4. Initialize Data Migration
```bash
# Access the MCP Manager dashboard
open http://localhost:8000

# Click "Migrate Data to Neo4j" or use the API:
curl -X POST http://localhost:8000/api/migrate \
  -H "Content-Type: application/json" \
  -d '{"clear_existing": true}'
```

### 5. Verify Setup
```bash
# Check all services are running
docker-compose -f docker-compose-mcp.yml ps

# Verify PostgreSQL data
docker exec mcp_postgres psql -U postgres -d movies -c "SELECT COUNT(*) FROM structured_content;"

# Verify Neo4j connection
docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "RETURN 1"

# Check MCP services
curl http://localhost:8000/api/status
```

## 📊 Services Details

### MCP Data Modeling Server (Port 8001)
**Purpose**: Handles data transformation between PostgreSQL and Neo4j

**Capabilities**:
- Analyze PostgreSQL schema and content structure
- Generate Neo4j data models based on relational data
- Migrate data from PostgreSQL to Neo4j with proper relationships
- Create graph nodes for Authors, Articles, Domains, Tags, and Websites

**Key Tools**:
- `analyze_postgres_schema`: Analyze source data structure
- `migrate_to_neo4j`: Perform data migration
- `generate_cypher_queries`: Create Cypher queries for common operations

### MCP Cypher Server (Port 8002)
**Purpose**: Executes Cypher queries and manages Neo4j operations

**Capabilities**:
- Execute custom Cypher queries with parameters
- Provide pre-built query templates
- Analyze relationships and patterns in graph data
- Search articles by various criteria (author, domain, tags, keywords)

**Key Tools**:
- `execute_cypher`: Run custom Cypher queries
- `search_articles`: Search content by different criteria
- `analyze_relationships`: Perform graph analysis
- `get_query_template`: Access pre-built query templates

### MCP Manager (Port 8000)
**Purpose**: Web interface for monitoring and managing MCP servers

**Features**:
- Real-time server and database status monitoring
- Interactive query interface with templates
- Data migration controls
- API documentation and testing

## 🔄 Data Migration Process

### Automatic Schema Creation
The system automatically creates the following Neo4j schema:

```cypher
// Node Labels
(:Author)     - Content creators
(:Article)    - Individual publications  
(:Domain)     - Content categories
(:Tag)        - Content tags
(:Website)    - Source websites

// Relationships
(Author)-[:WROTE]->(Article)
(Article)-[:BELONGS_TO]->(Domain)
(Article)-[:TAGGED_WITH]->(Tag)
(Article)-[:PUBLISHED_ON]->(Website)
(Author)-[:SPECIALIZES_IN]->(Domain)
```

### Migration Statistics
After migration, you'll have:
- **~10 Author nodes** (Dr. Sarah Chen, Michael Rodriguez, etc.)
- **100 Article nodes** (sample publications)
- **10 Domain nodes** (Healthcare, Technology, AI, etc.)
- **~15 Tag nodes** (Healthcare, Fintech, AI, etc.)
- **~10 Website nodes** (based on site_name)
- **~200+ relationships** connecting all entities

## 📝 Sample Queries

### Basic Exploration
```cypher
// Count all nodes by type
MATCH (n) 
RETURN labels(n) as node_type, count(n) as count 
ORDER BY count DESC

// Find most productive authors
MATCH (a:Author)-[:WROTE]->(article:Article)
RETURN a.name, count(article) as articles
ORDER BY articles DESC

// Domain distribution
MATCH (d:Domain)<-[:BELONGS_TO]-(article:Article)
RETURN d.name, count(article) as article_count
ORDER BY article_count DESC
```

### Advanced Analysis
```cypher
// Find authors working in similar domains
MATCH (a1:Author)-[:WROTE]->(article1:Article)-[:BELONGS_TO]->(d:Domain)<-[:BELONGS_TO]-(article2:Article)<-[:WROTE]-(a2:Author)
WHERE a1 <> a2
RETURN a1.name, a2.name, d.name, count(*) as shared_articles
ORDER BY shared_articles DESC

// Tag co-occurrence analysis
MATCH (article:Article)-[:TAGGED_WITH]->(t1:Tag), 
      (article)-[:TAGGED_WITH]->(t2:Tag)
WHERE t1 <> t2
RETURN t1.name, t2.name, count(article) as co_occurrence
ORDER BY co_occurrence DESC LIMIT 10

// Find related articles through tags
MATCH (article1:Article {title: "AI-Powered Medical Diagnosis Revolution"})-[:TAGGED_WITH]->(tag:Tag)<-[:TAGGED_WITH]-(article2:Article)
WHERE article1 <> article2
RETURN article2.title, article2.author, collect(tag.name) as shared_tags
ORDER BY size(shared_tags) DESC
```

## 🛠️ API Usage Examples

### Using MCP Data Modeling Server
```bash
# Analyze PostgreSQL schema
curl -X POST http://localhost:8001/tools/analyze_postgres_schema \
  -H "Content-Type: application/json" \
  -d '{}'

# Migrate data to Neo4j
curl -X POST http://localhost:8001/tools/migrate_to_neo4j \
  -H "Content-Type: application/json" \
  -d '{"clear_existing": true}'
```

### Using MCP Cypher Server
```bash
# Execute custom query
curl -X POST http://localhost:8002/tools/execute_cypher \
  -H "Content-Type: application/json" \
  -d '{
    "query": "MATCH (a:Author) RETURN a.name LIMIT 5",
    "parameters": {}
  }'

# Search articles by author
curl -X POST http://localhost:8002/tools/search_articles \
  -H "Content-Type: application/json" \
  -d '{
    "search_type": "author",
    "search_value": "Dr. Sarah Chen",
    "limit": 10
  }'
```

### Using MCP Manager API
```bash
# Get system status
curl http://localhost:8000/api/status

# Execute Cypher query through manager
curl -X POST http://localhost:8000/api/query/cypher \
  -H "Content-Type: application/json" \
  -d '{
    "query": "MATCH (n) RETURN count(n) as total_nodes"
  }'

# Get query templates
curl http://localhost:8000/api/query/templates
```

## 🔧 Configuration

### Environment Variables
All services can be configured through environment variables:

```bash
# Database connections
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=movies
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password123

NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123

# MCP server URLs
MCP_DATA_MODELING_URL=http://mcp-data-modeling:8001
MCP_CYPHER_URL=http://mcp-cypher:8002
```

### Custom Configuration
To modify server behavior, edit the respective `__main__.py` files in:
- `mcp-servers/data-modeling/`
- `mcp-servers/cypher/`
- `mcp-servers/manager/`

## 🐛 Troubleshooting

### Service Health Checks
```bash
# Check all container status
docker-compose -f docker-compose-mcp.yml ps

# View logs for specific services
docker-compose -f docker-compose-mcp.yml logs postgres
docker-compose -f docker-compose-mcp.yml logs neo4j
docker-compose -f docker-compose-mcp.yml logs mcp-data-modeling
docker-compose -f docker-compose-mcp.yml logs mcp-cypher
```

### Common Issues

**PostgreSQL Connection Issues**:
```bash
# Check if PostgreSQL is ready
docker exec mcp_postgres pg_isready -U postgres

# Verify data exists
docker exec mcp_postgres psql -U postgres -d movies -c "SELECT COUNT(*) FROM structured_content;"
```

**Neo4j Connection Issues**:
```bash
# Test Neo4j connection
docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "RETURN 1"

# Check Neo4j logs
docker-compose -f docker-compose-mcp.yml logs neo4j
```

**pgAdmin Connection Issues**:
```bash
# Common pgAdmin setup mistakes:
# ❌ Wrong: Using 'localhost' or '127.0.0.1' as hostname
# ❌ Wrong: Using container name 'mcp_postgres' as hostname  
# ✅ Correct: Using service name 'postgres' as hostname

# Verify pgAdmin can reach PostgreSQL
docker exec mcp_pgadmin ping postgres

# Check if PostgreSQL is accepting connections
docker exec mcp_postgres pg_isready -U postgres
```

**MCP Server Issues**:
```bash
# Check server health
curl http://localhost:8001/health  # Data modeling server
curl http://localhost:8002/health  # Cypher server
curl http://localhost:8000/health  # Manager

# View detailed logs
docker-compose -f docker-compose-mcp.yml logs mcp-data-modeling
```

### Data Verification
```bash
# Verify PostgreSQL data
docker exec mcp_postgres psql -U postgres -d movies -c "
  SELECT 
    COUNT(*) as total_articles,
    COUNT(DISTINCT author) as unique_authors,
    COUNT(DISTINCT domain) as unique_domains
  FROM structured_content;
"

# Expected output: 100 articles, 10 authors, 10 domains

# Verify Neo4j data (after migration)
docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "
  MATCH (n) 
  RETURN labels(n) as node_type, count(n) as count 
  ORDER BY count DESC;
"

# Expected output after migration:
# - Article: 100 nodes
# - Author: 10 nodes  
# - Domain: 10 nodes
# - Tag: ~15 nodes
# - Website: ~10 nodes
```

### Container Network Verification
```bash
# Check if services can communicate
docker exec mcp_pgadmin ping postgres
docker exec mcp_data_modeling ping postgres
docker exec mcp_data_modeling ping neo4j
docker exec mcp_cypher ping neo4j

# Verify network configuration
docker network ls | grep mcp
docker network inspect mcp_mcp-network
```

## 🔄 Stopping Services

```bash
# Stop all services
docker-compose -f docker-compose-mcp.yml down

# Stop and remove all data (WARNING: This deletes all data)
docker-compose -f docker-compose-mcp.yml down -v
```

## 📚 Next Steps

1. **Explore the Data**: Use the MCP Manager dashboard to explore your migrated data
2. **Custom Queries**: Create custom Cypher queries for your specific use cases
3. **Integration**: Integrate the MCP servers with your applications
4. **Scaling**: Consider scaling individual services based on your needs
5. **Monitoring**: Set up monitoring and alerting for production deployments

The MCP Neo4j integration provides a powerful foundation for graph-based content analysis and relationship discovery. The sample data includes realistic publications across multiple domains, making it perfect for testing and development of graph-based applications.##
 🚀 Quick Reference Card

### Essential Commands
```bash
# Start MCP services
./start-mcp.sh                                    # Automated startup
docker-compose -f docker-compose-mcp.yml up -d    # Manual startup

# Check all services
docker-compose -f docker-compose-mcp.yml ps

# Individual service logs
docker-compose -f docker-compose-mcp.yml logs postgres
docker-compose -f docker-compose-mcp.yml logs neo4j
docker-compose -f docker-compose-mcp.yml logs mcp-data-modeling
docker-compose -f docker-compose-mcp.yml logs mcp-cypher
docker-compose -f docker-compose-mcp.yml logs mcp-manager

# Stop services
docker-compose -f docker-compose-mcp.yml down
```

### Access URLs & Credentials
| Service | URL | Credentials |
|---------|-----|-------------|
| MCP Manager | http://localhost:8000 | No auth required |
| Neo4j Browser | http://localhost:7474 | neo4j / password123 |
| pgAdmin | http://localhost:8080 | admin@movies.com / admin123 |
| PostgreSQL | localhost:5432 | postgres / password123 |

### pgAdmin Server Setup (Copy-Paste Ready)
```
General Tab:
  Name: MCP PostgreSQL Database

Connection Tab:
  Host name/address: postgres
  Port: 5432
  Maintenance database: movies
  Username: postgres  
  Password: password123
```

### Health Check Commands
```bash
# PostgreSQL
docker exec mcp_postgres pg_isready -U postgres

# Neo4j  
docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "RETURN 1"

# MCP Services
curl http://localhost:8000/health    # Manager
curl http://localhost:8001/health    # Data Modeling (if exposed)
curl http://localhost:8002/health    # Cypher (if exposed)
```

### Data Migration Quick Commands
```bash
# Check PostgreSQL data
docker exec mcp_postgres psql -U postgres -d movies -c "SELECT COUNT(*) FROM structured_content;"

# Migrate to Neo4j via API
curl -X POST http://localhost:8000/api/migrate -H "Content-Type: application/json" -d '{"clear_existing": true}'

# Verify Neo4j data
docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "MATCH (n) RETURN count(n)"
```

### Common Cypher Queries
```cypher
-- Count all nodes
MATCH (n) RETURN labels(n) as type, count(n) as count ORDER BY count DESC

-- Find all authors
MATCH (a:Author) RETURN a.name ORDER BY a.name

-- Articles by domain
MATCH (d:Domain)<-[:BELONGS_TO]-(a:Article) 
RETURN d.name, count(a) as articles ORDER BY articles DESC

-- Most productive authors
MATCH (author:Author)-[:WROTE]->(article:Article)
RETURN author.name, count(article) as articles ORDER BY articles DESC
```

### Troubleshooting Checklist
- [ ] All containers running: `docker-compose -f docker-compose-mcp.yml ps`
- [ ] PostgreSQL healthy: `docker exec mcp_postgres pg_isready -U postgres`
- [ ] Neo4j accessible: `docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "RETURN 1"`
- [ ] pgAdmin uses `postgres` hostname (not `localhost` or container name)
- [ ] Data exists: 100 records in PostgreSQL, nodes in Neo4j after migration
- [ ] Services can communicate: `docker exec mcp_pgadmin ping postgres`