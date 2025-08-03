#!/bin/bash

# MCP Neo4j Integration Startup Script
# This script starts all MCP services and performs initial setup

set -e

echo "🚀 Starting MCP Neo4j Integration Services..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
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

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed. Please install docker-compose and try again."
    exit 1
fi

print_status "Starting all MCP services..."

# Start services using the MCP Docker Compose file
docker-compose -f docker-compose-mcp.yml up -d

print_status "Waiting for services to be ready..."

# Function to wait for service to be ready
wait_for_service() {
    local service_name=$1
    local health_url=$2
    local max_attempts=30
    local attempt=1

    print_status "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$health_url" > /dev/null 2>&1; then
            print_success "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start within expected time"
    return 1
}

# Wait for PostgreSQL
print_status "Waiting for PostgreSQL..."
sleep 10
if docker exec mcp_postgres pg_isready -U postgres > /dev/null 2>&1; then
    print_success "PostgreSQL is ready!"
else
    print_error "PostgreSQL is not ready"
    exit 1
fi

# Wait for Neo4j
print_status "Waiting for Neo4j..."
sleep 15
if docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "RETURN 1" > /dev/null 2>&1; then
    print_success "Neo4j is ready!"
else
    print_error "Neo4j is not ready"
    exit 1
fi

# Wait for MCP Manager
wait_for_service "MCP Manager" "http://localhost:8000/health"

print_success "All services are ready!"

# Display service information
echo ""
echo "🎉 MCP Neo4j Integration is now running!"
echo ""
echo "📊 Access Points:"
echo "  • MCP Manager Dashboard: http://localhost:8000"
echo "  • Neo4j Browser:         http://localhost:7474 (neo4j/password123)"
echo "  • pgAdmin:               http://localhost:8080 (admin@movies.com/admin123)"
echo ""
echo "🔧 Service Status:"
docker-compose -f docker-compose-mcp.yml ps

echo ""
echo "📝 Quick Commands:"
echo "  • View logs:           docker-compose -f docker-compose-mcp.yml logs [service]"
echo "  • Stop services:       docker-compose -f docker-compose-mcp.yml down"
echo "  • Restart service:     docker-compose -f docker-compose-mcp.yml restart [service]"
echo ""

# Check if data migration is needed
print_status "Checking if data migration is needed..."
neo4j_node_count=$(docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "MATCH (n) RETURN count(n) as count" --format plain 2>/dev/null | tail -n 1 | tr -d '"' || echo "0")

if [ "$neo4j_node_count" -eq "0" ]; then
    print_warning "Neo4j database is empty. You may want to migrate data from PostgreSQL."
    echo ""
    echo "🔄 To migrate data:"
    echo "  • Visit: http://localhost:8000"
    echo "  • Click 'Migrate Data to Neo4j'"
    echo "  • Or run: curl -X POST http://localhost:8000/api/migrate -H 'Content-Type: application/json' -d '{\"clear_existing\": true}'"
else
    print_success "Neo4j database contains $neo4j_node_count nodes"
fi

echo ""
echo "📚 For detailed documentation, see README-MCP.md"
echo ""
print_success "Setup complete! Happy graphing! 🎯"