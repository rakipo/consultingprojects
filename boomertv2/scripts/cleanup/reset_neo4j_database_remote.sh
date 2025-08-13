#!/bin/bash

# Script to reset/clear a remote Neo4j database using bolt+s connection
# This connects to a remote Neo4j server and removes all data

echo "🔄 Remote Neo4j Database Reset Script"
echo "====================================="
echo ""

# Configuration - Update these values for your remote server
NEO4J_URI=""
NEO4J_USERNAME=""
NEO4J_PASSWORD=""
NEO4J_DATABASE="neo4j"

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -u, --uri URI          Neo4j URI (e.g., bolt+s://your-server.com:7687)"
    echo "  -U, --username USER    Neo4j username"
    echo "  -p, --password PASS    Neo4j password"
    echo "  -d, --database DB      Neo4j database name (default: neo4j)"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 -u bolt+s://ai50-neo4j-db-server-987.westus2.cloudapp.azure.com:7687 -U neo4j -p your_password"
    echo ""
    echo "Environment variables (alternative to command line options):"
    echo "  NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--uri)
            NEO4J_URI="$2"
            shift 2
            ;;
        -U|--username)
            NEO4J_USERNAME="$2"
            shift 2
            ;;
        -p|--password)
            NEO4J_PASSWORD="$2"
            shift 2
            ;;
        -d|--database)
            NEO4J_DATABASE="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Check if cypher-shell is available
if ! command -v cypher-shell &> /dev/null; then
    echo "❌ cypher-shell is not installed or not in PATH"
    echo ""
    echo "To install cypher-shell:"
    echo "1. Download from: https://neo4j.com/download-center/#command-line"
    echo "2. Or install via package manager:"
    echo "   - macOS: brew install cypher-shell"
    echo "   - Ubuntu/Debian: apt install cypher-shell"
    echo "   - Or use Docker: docker run --rm -it neo4j/cypher-shell"
    echo ""
    exit 1
fi

# Validate required parameters
if [ -z "$NEO4J_URI" ] || [ -z "$NEO4J_USERNAME" ] || [ -z "$NEO4J_PASSWORD" ]; then
    echo "❌ Missing required parameters"
    echo ""
    show_usage
    exit 1
fi

echo "This will clear all data from the remote Neo4j database:"
echo "  URI: $NEO4J_URI"
echo "  Database: $NEO4J_DATABASE"
echo "  Username: $NEO4J_USERNAME"
echo ""
echo "⚠️  WARNING: This will permanently delete ALL data in the Neo4j database!"
echo "⚠️  This action cannot be undone!"
echo ""

# Function to ask for confirmation
confirm_reset() {
    read -p "Are you sure you want to clear the remote Neo4j database? (type 'RESET' to confirm): " confirmation
    if [ "$confirmation" != "RESET" ]; then
        echo "❌ Reset cancelled."
        exit 0
    fi
}

# Ask for confirmation
confirm_reset

echo ""
echo "🗑️  Starting remote Neo4j database reset..."
echo ""

# Function to execute cypher query on remote server
execute_cypher() {
    local query="$1"
    local description="$2"
    
    echo "Executing: $description"
    cypher-shell -a "$NEO4J_URI" -u "$NEO4J_USERNAME" -p "$NEO4J_PASSWORD" -d "$NEO4J_DATABASE" "$query"
    
    if [ $? -eq 0 ]; then
        echo "✅ $description completed"
    else
        echo "❌ $description failed"
        return 1
    fi
}

# Test connection first
echo "🔗 Testing connection to remote Neo4j server..."
if ! execute_cypher "RETURN 1 AS test;" "Connection test"; then
    echo "❌ Failed to connect to remote Neo4j server"
    echo "Please check your connection parameters and try again"
    exit 1
fi

echo ""

# Step 1: Clear all data using Cypher
echo "1️⃣  Clearing all nodes and relationships..."

# Delete all relationships first
execute_cypher "
MATCH ()-[r]-()
CALL {
  WITH r
  DELETE r
} IN TRANSACTIONS OF 1000 ROWS;
" "Delete all relationships"

# Delete all nodes
execute_cypher "
MATCH (n)
CALL {
  WITH n
  DELETE n
} IN TRANSACTIONS OF 1000 ROWS;
" "Delete all nodes"

echo ""

# Step 2: Drop all indexes (except system indexes)
echo "2️⃣  Dropping all custom indexes..."

# Try to drop indexes using APOC if available
execute_cypher "
SHOW INDEXES YIELD name, type
WHERE type <> 'LOOKUP' AND NOT name STARTS WITH '__'
WITH collect(name) AS indexNames
UNWIND indexNames AS indexName
CALL {
  WITH indexName
  EXECUTE 'DROP INDEX ' + indexName + ' IF EXISTS'
}
RETURN count(*) AS droppedIndexes;
" "Drop custom indexes" || {
    echo "Trying fallback method for dropping indexes..."
    
    # Fallback: Drop known common indexes
    execute_cypher "DROP INDEX article_title_text IF EXISTS;" "Drop article_title_text index" || true
    execute_cypher "DROP INDEX article_content_text IF EXISTS;" "Drop article_content_text index" || true
    execute_cypher "DROP INDEX article_publish_date_range IF EXISTS;" "Drop article_publish_date_range index" || true
    execute_cypher "DROP INDEX article_id_text IF EXISTS;" "Drop article_id_text index" || true
    execute_cypher "DROP INDEX website_site_name_text IF EXISTS;" "Drop website_site_name_text index" || true
    execute_cypher "DROP INDEX website_domain_text IF EXISTS;" "Drop website_domain_text index" || true
    execute_cypher "DROP INDEX chunk_embedding_vector IF EXISTS;" "Drop chunk_embedding_vector index" || true
    execute_cypher "DROP INDEX chunk_embeddings IF EXISTS;" "Drop chunk_embeddings index" || true
}

echo ""

# Step 3: Drop all constraints
echo "3️⃣  Dropping all constraints..."

execute_cypher "
SHOW CONSTRAINTS YIELD name
WHERE NOT name STARTS WITH '__'
WITH collect(name) AS constraintNames
UNWIND constraintNames AS constraintName
CALL {
  WITH constraintName
  EXECUTE 'DROP CONSTRAINT ' + constraintName + ' IF EXISTS'
}
RETURN count(*) AS droppedConstraints;
" "Drop all constraints" || {
    echo "Trying fallback method for dropping constraints..."
    
    # Fallback: Drop known common constraints
    execute_cypher "DROP CONSTRAINT article_id_unique IF EXISTS;" "Drop article_id_unique constraint" || true
    execute_cypher "DROP CONSTRAINT article_url_unique IF EXISTS;" "Drop article_url_unique constraint" || true
    execute_cypher "DROP CONSTRAINT website_domain_unique IF EXISTS;" "Drop website_domain_unique constraint" || true
    execute_cypher "DROP CONSTRAINT author_name_unique IF EXISTS;" "Drop author_name_unique constraint" || true
    execute_cypher "DROP CONSTRAINT chunk_chunk_id_unique IF EXISTS;" "Drop chunk_chunk_id_unique constraint" || true
}

echo ""

# Step 4: Verification
echo "4️⃣  Verification..."

# Count remaining nodes
echo "Checking remaining nodes..."
NODE_COUNT=$(cypher-shell -a "$NEO4J_URI" -u "$NEO4J_USERNAME" -p "$NEO4J_PASSWORD" -d "$NEO4J_DATABASE" "MATCH (n) RETURN count(n) AS count;" --format plain | tail -n 1 | tr -d '"' | xargs)
echo "Remaining nodes: $NODE_COUNT"

# Count remaining relationships
echo "Checking remaining relationships..."
REL_COUNT=$(cypher-shell -a "$NEO4J_URI" -u "$NEO4J_USERNAME" -p "$NEO4J_PASSWORD" -d "$NEO4J_DATABASE" "MATCH ()-[r]-() RETURN count(r) AS count;" --format plain | tail -n 1 | tr -d '"' | xargs)
echo "Remaining relationships: $REL_COUNT"

# Show remaining indexes
echo ""
echo "Remaining indexes:"
cypher-shell -a "$NEO4J_URI" -u "$NEO4J_USERNAME" -p "$NEO4J_PASSWORD" -d "$NEO4J_DATABASE" "SHOW INDEXES YIELD name, type RETURN name, type;" --format table || echo "Could not retrieve indexes"

# Show remaining constraints
echo ""
echo "Remaining constraints:"
cypher-shell -a "$NEO4J_URI" -u "$NEO4J_USERNAME" -p "$NEO4J_PASSWORD" -d "$NEO4J_DATABASE" "SHOW CONSTRAINTS YIELD name RETURN name;" --format table || echo "Could not retrieve constraints"

echo ""
if [ "$NODE_COUNT" = "0" ] && [ "$REL_COUNT" = "0" ]; then
    echo "🎉 Remote Neo4j database successfully reset!"
    echo "✅ Database is now empty and ready for fresh data"
else
    echo "⚠️  Database reset completed, but some data may remain"
    echo "   Nodes: $NODE_COUNT, Relationships: $REL_COUNT"
fi

echo ""
echo "Remote Neo4j server is ready to use."
echo "You can now load fresh data using your data loader."
echo ""
echo "To verify the reset:"
echo "  cypher-shell -a \"$NEO4J_URI\" -u \"$NEO4J_USERNAME\" -p \"$NEO4J_PASSWORD\" -d \"$NEO4J_DATABASE\" 'MATCH (n) RETURN count(n);'"
echo ""