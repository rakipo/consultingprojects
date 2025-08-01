# 🚀 Complete Setup Sequence - PostgreSQL to Neo4j Graph Population

This guide provides the exact sequence of commands to run all programs and populate the final Neo4j graph with data from PostgreSQL.

## 📋 Prerequisites

- Docker and Docker Compose installed
- Ports 5432, 7474, 7687, 8000, 8080 available
- At least 4GB RAM available for containers

## 🔄 Step-by-Step Execution Sequence

### Step 1: Clean Environment (Optional)
```bash
# Stop any existing containers
docker-compose down
docker-compose -f docker-compose-mcp.yml down

# Remove existing volumes (WARNING: This deletes all data)
docker volume prune -f

# Verify clean state
docker ps
```

### Step 2: Start MCP Services
```bash
# Navigate to app directory
cd app

# Start all MCP services
docker-compose -f docker-compose-mcp.yml up -d

# Verify all containers are starting
docker-compose -f docker-compose-mcp.yml ps
```

### Step 3: Wait for Services to Initialize
```bash
# Wait for PostgreSQL to be ready (30-60 seconds)
echo "Waiting for PostgreSQL to initialize..."
until docker exec mcp_postgres pg_isready -U postgres; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done
echo "PostgreSQL is ready!"

# Wait for Neo4j to be ready (60-90 seconds)
echo "Waiting for Neo4j to initialize..."
until docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "RETURN 1" > /dev/null 2>&1; do
    echo "Neo4j is unavailable - sleeping"
    sleep 3
done
echo "Neo4j is ready!"

# Wait for MCP Manager to be ready
echo "Waiting for MCP Manager..."
until curl -s http://localhost:8000/health > /dev/null; do
    echo "MCP Manager is unavailable - sleeping"
    sleep 2
done
echo "MCP Manager is ready!"
```

### Step 4: Insert Sample Data into PostgreSQL
```bash
# Check if sample data was loaded automatically
echo "Checking PostgreSQL data..."
RECORD_COUNT=$(docker exec mcp_postgres psql -U postgres -d movies -t -c "SELECT COUNT(*) FROM structured_content;" 2>/dev/null | tr -d ' ' || echo "0")

if [ "$RECORD_COUNT" -eq "100" ]; then
    echo "✅ PostgreSQL already contains $RECORD_COUNT sample records"
else
    echo "📝 Inserting sample data into PostgreSQL..."
    
    # Method 1: Use Python script (recommended)
    python generate_full_dataset.py
    
    # Method 2: Alternative - Use SQL script
    # docker exec -i mcp_postgres psql -U postgres -d movies < insert_sample_data.sql
    
    # Verify insertion
    RECORD_COUNT=$(docker exec mcp_postgres psql -U postgres -d movies -t -c "SELECT COUNT(*) FROM structured_content;" | tr -d ' ')
    
    if [ "$RECORD_COUNT" -eq "100" ]; then
        echo "✅ Successfully inserted $RECORD_COUNT sample records"
    else
        echo "❌ Data insertion failed. Found $RECORD_COUNT records instead of 100"
        exit 1
    fi
fi

# Show sample data breakdown
echo "📊 Data breakdown:"
docker exec mcp_postgres psql -U postgres -d movies -c "
SELECT 
    COUNT(*) as total_articles,
    COUNT(DISTINCT author) as unique_authors,
    COUNT(DISTINCT domain) as unique_domains
FROM structured_content;
"

# Show top authors
echo "👥 Top authors:"
docker exec mcp_postgres psql -U postgres -d movies -c "
SELECT author, COUNT(*) as articles 
FROM structured_content 
GROUP BY author 
ORDER BY articles DESC 
LIMIT 5;
"
```

### Step 5: Verify Neo4j is Empty (Before Migration)
```bash
echo "Checking Neo4j initial state..."
NEO4J_COUNT=$(docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "MATCH (n) RETURN count(n) as count" --format plain | tail -n 1 | tr -d '"')

echo "Neo4j currently contains $NEO4J_COUNT nodes"
if [ "$NEO4J_COUNT" -gt "0" ]; then
    echo "⚠️  Neo4j already contains data. Migration will clear existing data."
fi
```

### Step 6: Execute Data Migration
```bash
echo "🔄 Starting data migration from PostgreSQL to Neo4j..."

# Method 1: Using MCP Manager API (Recommended)
MIGRATION_RESPONSE=$(curl -s -X POST http://localhost:8000/api/migrate \
  -H "Content-Type: application/json" \
  -d '{"clear_existing": true}')

echo "Migration response: $MIGRATION_RESPONSE"

# Wait for migration to complete
sleep 10

# Method 2: Alternative - Direct MCP Data Modeling Server (if Method 1 fails)
# curl -s -X POST http://localhost:8001/tools/migrate_to_neo4j \
#   -H "Content-Type: application/json" \
#   -d '{"clear_existing": true}'
```

### Step 7: Verify Neo4j Graph Population
```bash
echo "🔍 Verifying Neo4j graph population..."

# Check total nodes
NEO4J_NODES=$(docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "MATCH (n) RETURN count(n) as count" --format plain | tail -n 1 | tr -d '"')
echo "Total nodes in Neo4j: $NEO4J_NODES"

# Check total relationships
NEO4J_RELS=$(docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "MATCH ()-[r]->() RETURN count(r) as count" --format plain | tail -n 1 | tr -d '"')
echo "Total relationships in Neo4j: $NEO4J_RELS"

# Show node distribution by label
echo "📊 Node distribution:"
docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "
MATCH (n) 
RETURN labels(n) as node_type, count(n) as count 
ORDER BY count DESC
"

# Show relationship distribution
echo "🔗 Relationship distribution:"
docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "
MATCH ()-[r]->() 
RETURN type(r) as relationship_type, count(r) as count 
ORDER BY count DESC
"
```

### Step 8: Validate Graph Structure
```bash
echo "✅ Validating graph structure..."

# Check if we have the expected node types
echo "Checking for Author nodes:"
docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "MATCH (a:Author) RETURN count(a) as author_count"

echo "Checking for Article nodes:"
docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "MATCH (a:Article) RETURN count(a) as article_count"

echo "Checking for Domain nodes:"
docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "MATCH (d:Domain) RETURN count(d) as domain_count"

echo "Checking for Tag nodes:"
docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "MATCH (t:Tag) RETURN count(t) as tag_count"

# Verify relationships exist
echo "Checking WROTE relationships:"
docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "MATCH ()-[r:WROTE]->() RETURN count(r) as wrote_count"

echo "Checking BELONGS_TO relationships:"
docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "MATCH ()-[r:BELONGS_TO]->() RETURN count(r) as belongs_to_count"
```

### Step 9: Test Graph Queries
```bash
echo "🧪 Testing sample graph queries..."

# Find most productive authors
echo "Most productive authors:"
docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "
MATCH (a:Author)-[:WROTE]->(article:Article)
RETURN a.name, count(article) as articles
ORDER BY articles DESC
LIMIT 5
"

# Find domain distribution
echo "Domain distribution:"
docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "
MATCH (d:Domain)<-[:BELONGS_TO]-(article:Article)
RETURN d.name, count(article) as articles
ORDER BY articles DESC
"

# Find articles with AI tag
echo "Articles tagged with 'AI':"
docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "
MATCH (article:Article)-[:TAGGED_WITH]->(t:Tag {name: 'AI'})
RETURN article.title, article.author
LIMIT 5
"
```

### Step 10: Setup pgAdmin Connection
```bash
echo "🔧 Setting up pgAdmin connection..."
echo "1. Open pgAdmin: http://localhost:8080"
echo "2. Login: admin@movies.com / admin123"
echo "3. Add server with these settings:"
echo "   - Name: MCP PostgreSQL Database"
echo "   - Host: postgres"
echo "   - Port: 5432"
echo "   - Database: movies"
echo "   - Username: postgres"
echo "   - Password: password123"
```

### Step 11: Final Verification & Access Points
```bash
echo "🎉 Setup Complete! Access points:"
echo ""
echo "📊 MCP Manager Dashboard: http://localhost:8000"
echo "🌐 Neo4j Browser:         http://localhost:7474 (neo4j/password123)"
echo "🗄️  pgAdmin:               http://localhost:8080 (admin@movies.com/admin123)"
echo ""
echo "📈 Final Statistics:"
echo "PostgreSQL Records: $(docker exec mcp_postgres psql -U postgres -d movies -t -c 'SELECT COUNT(*) FROM structured_content;' | tr -d ' ')"
echo "Neo4j Nodes: $(docker exec mcp_neo4j cypher-shell -u neo4j -p password123 'MATCH (n) RETURN count(n) as count' --format plain | tail -n 1 | tr -d '"')"
echo "Neo4j Relationships: $(docker exec mcp_neo4j cypher-shell -u neo4j -p password123 'MATCH ()-[r]->() RETURN count(r) as count' --format plain | tail -n 1 | tr -d '"')"
echo ""
echo "✅ Graph population complete!"
```

## 🔧 Automated Setup Script

For convenience, you can run the entire sequence with:

```bash
# Make the script executable
chmod +x complete-setup.sh

# Run the complete setup
./complete-setup.sh
```

## 📊 Expected Final Results

After successful completion, you should have:

### PostgreSQL Database
- **100 articles** in `structured_content` table
- **10 unique authors** across multiple domains
- **10 domain categories** (Healthcare, Technology, AI, etc.)
- **Multiple tags** per article in JSONB format

### Neo4j Graph Database
- **~135 total nodes**:
  - 100 Article nodes
  - 10 Author nodes
  - 10 Domain nodes
  - ~15 Tag nodes
  - ~10 Website nodes
- **~250+ relationships**:
  - 100 WROTE relationships (Author → Article)
  - 100 BELONGS_TO relationships (Article → Domain)
  - ~50+ TAGGED_WITH relationships (Article → Tag)
  - 100 PUBLISHED_ON relationships (Article → Website)
  - 10 SPECIALIZES_IN relationships (Author → Domain)

## 🐛 Troubleshooting

If any step fails:

1. **Check container status**: `docker-compose -f docker-compose-mcp.yml ps`
2. **View logs**: `docker-compose -f docker-compose-mcp.yml logs [service-name]`
3. **Restart specific service**: `docker-compose -f docker-compose-mcp.yml restart [service-name]`
4. **Full restart**: `docker-compose -f docker-compose-mcp.yml down && docker-compose -f docker-compose-mcp.yml up -d`

## 🔄 Reset and Retry

To start over completely:

```bash
# Stop all services
docker-compose -f docker-compose-mcp.yml down

# Remove all volumes (deletes all data)
docker-compose -f docker-compose-mcp.yml down -v

# Remove any orphaned containers
docker container prune -f

# Start fresh
docker-compose -f docker-compose-mcp.yml up -d
```

This sequence ensures a complete, verified setup from PostgreSQL data to a fully populated Neo4j graph database! 🎯