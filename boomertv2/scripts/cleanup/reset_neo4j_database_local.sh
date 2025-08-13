#!/bin/bash

# Script to reset/clear the Neo4j database content only
# This keeps the Neo4j server running but removes all data

echo "🔄 Neo4j Database Reset Script"
echo "=============================="
echo ""
echo "This will clear all data from the Neo4j database while keeping the server running."
echo "⚠️  WARNING: This will permanently delete ALL data in the Neo4j database!"
echo "⚠️  This action cannot be undone!"
echo ""

# Function to ask for confirmation
confirm_reset() {
    read -p "Are you sure you want to clear the Neo4j database? (type 'RESET' to confirm): " confirmation
    if [ "$confirmation" != "RESET" ]; then
        echo "❌ Reset cancelled."
        exit 0
    fi
}

# Ask for confirmation
confirm_reset

echo ""
echo "🗑️  Starting Neo4j database reset..."
echo ""

# Check if Neo4j container is running
if ! docker ps --format "{{.Names}}" | grep -q "neo4j_db"; then
    echo "❌ Neo4j container 'neo4j_db' is not running."
    echo "Please start Neo4j first with:"
    echo "  docker-compose -f config/docker-compose-neo4j-mcp.yml up -d"
    exit 1
fi

echo "✅ Neo4j container is running"

# Step 1: Clear all data using Cypher
echo ""
echo "1️⃣  Clearing all nodes and relationships..."

# Delete all data in batches to avoid memory issues
docker exec neo4j_db cypher-shell -u neo4j -p password123 "
// Delete all relationships first
MATCH ()-[r]-()
CALL {
  WITH r
  DELETE r
} IN TRANSACTIONS OF 1000 ROWS;
"

docker exec neo4j_db cypher-shell -u neo4j -p password123 "
// Delete all nodes
MATCH (n)
CALL {
  WITH n
  DELETE n
} IN TRANSACTIONS OF 1000 ROWS;
"

echo "✅ All nodes and relationships deleted"

# Step 2: Drop all indexes (except system indexes)
echo ""
echo "2️⃣  Dropping all custom indexes..."

# Get list of custom indexes and drop them
docker exec neo4j_db cypher-shell -u neo4j -p password123 "
SHOW INDEXES YIELD name, type
WHERE type <> 'LOOKUP'
WITH collect(name) AS indexNames
UNWIND indexNames AS indexName
CALL {
  WITH indexName
  CALL apoc.cypher.doIt('DROP INDEX ' + indexName + ' IF EXISTS', {}) YIELD value
  RETURN value
}
RETURN count(*) AS droppedIndexes;
" 2>/dev/null || {
    # Fallback method if APOC is not available
    echo "Using fallback method to drop indexes..."
    
    # Drop known indexes one by one
    docker exec neo4j_db cypher-shell -u neo4j -p password123 "DROP INDEX article_title_text IF EXISTS;" 2>/dev/null || true
    docker exec neo4j_db cypher-shell -u neo4j -p password123 "DROP INDEX article_content_text IF EXISTS;" 2>/dev/null || true
    docker exec neo4j_db cypher-shell -u neo4j -p password123 "DROP INDEX article_publish_date_range IF EXISTS;" 2>/dev/null || true
    docker exec neo4j_db cypher-shell -u neo4j -p password123 "DROP INDEX website_site_name_text IF EXISTS;" 2>/dev/null || true
    docker exec neo4j_db cypher-shell -u neo4j -p password123 "DROP INDEX website_domain_text IF EXISTS;" 2>/dev/null || true
    docker exec neo4j_db cypher-shell -u neo4j -p password123 "DROP INDEX chunk_embedding_vector IF EXISTS;" 2>/dev/null || true
}

echo "✅ Custom indexes dropped"

# Step 3: Drop all constraints
echo ""
echo "3️⃣  Dropping all constraints..."

docker exec neo4j_db cypher-shell -u neo4j -p password123 "
SHOW CONSTRAINTS YIELD name
WITH collect(name) AS constraintNames
UNWIND constraintNames AS constraintName
CALL {
  WITH constraintName
  CALL apoc.cypher.doIt('DROP CONSTRAINT ' + constraintName + ' IF EXISTS', {}) YIELD value
  RETURN value
}
RETURN count(*) AS droppedConstraints;
" 2>/dev/null || {
    # Fallback method if APOC is not available
    echo "Using fallback method to drop constraints..."
    
    # Drop known constraints one by one
    docker exec neo4j_db cypher-shell -u neo4j -p password123 "DROP CONSTRAINT article_id_unique IF EXISTS;" 2>/dev/null || true
    docker exec neo4j_db cypher-shell -u neo4j -p password123 "DROP CONSTRAINT website_domain_unique IF EXISTS;" 2>/dev/null || true
    docker exec neo4j_db cypher-shell -u neo4j -p password123 "DROP CONSTRAINT author_name_unique IF EXISTS;" 2>/dev/null || true
    docker exec neo4j_db cypher-shell -u neo4j -p password123 "DROP CONSTRAINT chunk_chunk_id_unique IF EXISTS;" 2>/dev/null || true
}

echo "✅ Constraints dropped"

# Step 4: Clear any remaining schema
echo ""
echo "4️⃣  Clearing remaining schema elements..."

# Clear any procedures or functions (if any custom ones exist)
docker exec neo4j_db cypher-shell -u neo4j -p password123 "
CALL apoc.custom.list() YIELD type, name
WHERE type IN ['function', 'procedure']
WITH collect({type: type, name: name}) AS customItems
UNWIND customItems AS item
CALL apoc.custom.remove(item.name)
RETURN count(*) AS removedCustomItems;
" 2>/dev/null || echo "No custom procedures/functions to remove"

echo "✅ Schema cleared"

# Step 5: Verification
echo ""
echo "5️⃣  Verification..."

# Count remaining nodes
NODE_COUNT=$(docker exec neo4j_db cypher-shell -u neo4j -p password123 "MATCH (n) RETURN count(n) AS count;" | tail -n 1 | tr -d '"' | xargs)
echo "Remaining nodes: $NODE_COUNT"

# Count remaining relationships
REL_COUNT=$(docker exec neo4j_db cypher-shell -u neo4j -p password123 "MATCH ()-[r]-() RETURN count(r) AS count;" | tail -n 1 | tr -d '"' | xargs)
echo "Remaining relationships: $REL_COUNT"

# Show remaining indexes
echo ""
echo "Remaining indexes:"
docker exec neo4j_db cypher-shell -u neo4j -p password123 "SHOW INDEXES YIELD name, type RETURN name, type;"

# Show remaining constraints
echo ""
echo "Remaining constraints:"
docker exec neo4j_db cypher-shell -u neo4j -p password123 "SHOW CONSTRAINTS YIELD name RETURN name;" 2>/dev/null || echo "No constraints"

echo ""
if [ "$NODE_COUNT" = "0" ] && [ "$REL_COUNT" = "0" ]; then
    echo "🎉 Neo4j database successfully reset!"
    echo "✅ Database is now empty and ready for fresh data"
else
    echo "⚠️  Database reset completed, but some data may remain"
    echo "   Nodes: $NODE_COUNT, Relationships: $REL_COUNT"
fi

echo ""
echo "Neo4j server is still running and ready to use."
echo "You can now load fresh data using your data loader."
echo ""
echo "To verify the reset:"
echo "  docker exec neo4j_db cypher-shell -u neo4j -p password123 'MATCH (n) RETURN count(n);'"
echo ""