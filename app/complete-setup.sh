#!/bin/bash

# Complete MCP Neo4j Setup Script
# This script runs the entire sequence to populate the Neo4j graph from PostgreSQL

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}[STEP $1]${NC} $2"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${PURPLE}[INFO]${NC} $1"
}

echo "🚀 Starting Complete MCP Neo4j Setup Sequence"
echo "=============================================="

# Step 1: Clean Environment
print_step "1" "Cleaning environment..."
docker-compose down 2>/dev/null || true
docker-compose -f docker-compose-mcp.yml down 2>/dev/null || true
print_success "Environment cleaned"

# Step 2: Start MCP Services
print_step "2" "Starting MCP services..."
docker-compose -f docker-compose-mcp.yml up -d

print_info "Waiting for containers to start..."
sleep 5

# Check if containers are running
RUNNING_CONTAINERS=$(docker-compose -f docker-compose-mcp.yml ps --services --filter "status=running" | wc -l)
TOTAL_CONTAINERS=$(docker-compose -f docker-compose-mcp.yml ps --services | wc -l)

echo "Containers running: $RUNNING_CONTAINERS/$TOTAL_CONTAINERS"
docker-compose -f docker-compose-mcp.yml ps

# Step 3: Wait for PostgreSQL
print_step "3" "Waiting for PostgreSQL to be ready..."
POSTGRES_READY=false
for i in {1..30}; do
    if docker exec mcp_postgres pg_isready -U postgres > /dev/null 2>&1; then
        POSTGRES_READY=true
        break
    fi
    echo -n "."
    sleep 2
done

if [ "$POSTGRES_READY" = true ]; then
    print_success "PostgreSQL is ready!"
else
    print_error "PostgreSQL failed to start"
    exit 1
fi

# Step 4: Wait for Neo4j
print_step "4" "Waiting for Neo4j to be ready..."
NEO4J_READY=false
for i in {1..45}; do
    if docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "RETURN 1" > /dev/null 2>&1; then
        NEO4J_READY=true
        break
    fi
    echo -n "."
    sleep 2
done

if [ "$NEO4J_READY" = true ]; then
    print_success "Neo4j is ready!"
else
    print_error "Neo4j failed to start"
    exit 1
fi

# Step 5: Wait for MCP Manager
print_step "5" "Waiting for MCP Manager..."
MCP_READY=false
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        MCP_READY=true
        break
    fi
    echo -n "."
    sleep 2
done

if [ "$MCP_READY" = true ]; then
    print_success "MCP Manager is ready!"
else
    print_warning "MCP Manager may not be ready, continuing..."
fi

# Step 6: Verify PostgreSQL Data
print_step "6" "Verifying PostgreSQL data population..."
sleep 5  # Give initialization scripts time to complete

RECORD_COUNT=$(docker exec mcp_postgres psql -U postgres -d movies -t -c "SELECT COUNT(*) FROM structured_content;" 2>/dev/null | tr -d ' ' || echo "0")

if [ "$RECORD_COUNT" -eq "100" ]; then
    print_success "PostgreSQL contains $RECORD_COUNT sample records"
else
    print_warning "Expected 100 records, found $RECORD_COUNT. Checking if initialization is still running..."
    sleep 10
    RECORD_COUNT=$(docker exec mcp_postgres psql -U postgres -d movies -t -c "SELECT COUNT(*) FROM structured_content;" 2>/dev/null | tr -d ' ' || echo "0")
    
    if [ "$RECORD_COUNT" -eq "100" ]; then
        print_success "PostgreSQL now contains $RECORD_COUNT sample records"
    else
        print_info "Inserting sample data using Python script..."
        if python generate_full_dataset.py; then
            RECORD_COUNT=$(docker exec mcp_postgres psql -U postgres -d movies -t -c "SELECT COUNT(*) FROM structured_content;" 2>/dev/null | tr -d ' ' || echo "0")
            if [ "$RECORD_COUNT" -eq "100" ]; then
                print_success "Successfully inserted $RECORD_COUNT sample records"
            else
                print_error "Data insertion failed. Found $RECORD_COUNT records"
                exit 1
            fi
        else
            print_error "Python script failed. Check if psycopg2-binary is installed:"
            print_info "Run: pip install psycopg2-binary"
            exit 1
        fi
    fi
fi

# Show data breakdown
print_info "Data breakdown:"
docker exec mcp_postgres psql -U postgres -d movies -c "
SELECT 
    COUNT(*) as total_articles,
    COUNT(DISTINCT author) as unique_authors,
    COUNT(DISTINCT domain) as unique_domains
FROM structured_content;
" 2>/dev/null

# Step 7: Check Neo4j Initial State
print_step "7" "Checking Neo4j initial state..."
NEO4J_COUNT=$(docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "MATCH (n) RETURN count(n) as count" --format plain 2>/dev/null | tail -n 1 | tr -d '"' || echo "0")
print_info "Neo4j currently contains $NEO4J_COUNT nodes"

# Step 8: Execute Data Migration
print_step "8" "Executing data migration from PostgreSQL to Neo4j..."

# Try migration via MCP Manager API
print_info "Attempting migration via MCP Manager API..."
MIGRATION_RESPONSE=$(curl -s -X POST http://localhost:8000/api/migrate \
  -H "Content-Type: application/json" \
  -d '{"clear_existing": true}' 2>/dev/null || echo "failed")

if [[ "$MIGRATION_RESPONSE" == *"success"* ]]; then
    print_success "Migration initiated successfully"
else
    print_warning "MCP Manager migration failed, trying direct approach..."
    
    # Alternative: Try to trigger migration by calling the data modeling server directly
    # This would require the server to be properly exposed and configured
    print_info "Migration may need to be done manually via the web interface"
fi

# Wait for migration to complete
print_info "Waiting for migration to complete..."
sleep 15

# Step 9: Verify Neo4j Population
print_step "9" "Verifying Neo4j graph population..."

# Check nodes
NEO4J_NODES=$(docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "MATCH (n) RETURN count(n) as count" --format plain 2>/dev/null | tail -n 1 | tr -d '"' || echo "0")
print_info "Total nodes in Neo4j: $NEO4J_NODES"

# Check relationships
NEO4J_RELS=$(docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "MATCH ()-[r]->() RETURN count(r) as count" --format plain 2>/dev/null | tail -n 1 | tr -d '"' || echo "0")
print_info "Total relationships in Neo4j: $NEO4J_RELS"

if [ "$NEO4J_NODES" -gt "100" ]; then
    print_success "Neo4j graph populated successfully!"
    
    # Show node distribution
    print_info "Node distribution:"
    docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "
    MATCH (n) 
    RETURN labels(n) as node_type, count(n) as count 
    ORDER BY count DESC
    " 2>/dev/null
    
else
    print_warning "Neo4j graph may not be fully populated. Manual migration may be required."
    print_info "You can migrate data manually by:"
    print_info "1. Visit http://localhost:8000"
    print_info "2. Click 'Migrate Data to Neo4j'"
fi

# Step 10: Final Verification
print_step "10" "Running final verification tests..."

# Test some basic queries
print_info "Testing basic graph queries..."

# Check for Author nodes
AUTHOR_COUNT=$(docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "MATCH (a:Author) RETURN count(a) as count" --format plain 2>/dev/null | tail -n 1 | tr -d '"' || echo "0")
print_info "Author nodes: $AUTHOR_COUNT"

# Check for Article nodes
ARTICLE_COUNT=$(docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "MATCH (a:Article) RETURN count(a) as count" --format plain 2>/dev/null | tail -n 1 | tr -d '"' || echo "0")
print_info "Article nodes: $ARTICLE_COUNT"

# Check for relationships
WROTE_COUNT=$(docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "MATCH ()-[r:WROTE]->() RETURN count(r) as count" --format plain 2>/dev/null | tail -n 1 | tr -d '"' || echo "0")
print_info "WROTE relationships: $WROTE_COUNT"

# Step 11: Display Access Information
print_step "11" "Setup complete! Access information:"

echo ""
echo "🎉 MCP Neo4j Integration Setup Complete!"
echo "========================================"
echo ""
echo "📊 Access Points:"
echo "  • MCP Manager Dashboard: http://localhost:8000"
echo "  • Neo4j Browser:         http://localhost:7474 (neo4j/password123)"
echo "  • pgAdmin:               http://localhost:8080 (admin@movies.com/admin123)"
echo ""
echo "🔧 pgAdmin Server Setup:"
echo "  • Name: MCP PostgreSQL Database"
echo "  • Host: postgres"
echo "  • Port: 5432"
echo "  • Database: movies"
echo "  • Username: postgres"
echo "  • Password: password123"
echo ""
echo "📈 Final Statistics:"
echo "  • PostgreSQL Records: $RECORD_COUNT"
echo "  • Neo4j Nodes: $NEO4J_NODES"
echo "  • Neo4j Relationships: $NEO4J_RELS"
echo ""

if [ "$NEO4J_NODES" -gt "100" ] && [ "$RECORD_COUNT" -eq "100" ]; then
    print_success "✅ Complete setup successful! Graph is populated and ready to use."
else
    print_warning "⚠️  Setup completed with warnings. Manual migration may be needed."
    echo ""
    echo "🔄 To manually migrate data:"
    echo "  1. Visit: http://localhost:8000"
    echo "  2. Click 'Migrate Data to Neo4j'"
    echo "  3. Or run: curl -X POST http://localhost:8000/api/migrate -H 'Content-Type: application/json' -d '{\"clear_existing\": true}'"
fi

echo ""
echo "📚 For detailed documentation, see:"
echo "  • README-MCP.md - Complete MCP integration guide"
echo "  • SETUP-SEQUENCE.md - Detailed step-by-step instructions"
echo ""
print_success "Happy graphing! 🎯"