#!/bin/bash

# Wrapper script to reset the remote Neo4j database using configuration from config files
# This script automatically extracts connection details from your config files

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🔄 Remote Neo4j Database Reset (Auto-Config)"
echo "============================================="
echo ""

# Function to extract value from YAML config
extract_yaml_value() {
    local file="$1"
    local key="$2"
    
    if [ ! -f "$file" ]; then
        echo ""
        return 1
    fi
    
    # Extract the neo4j section and then the specific key
    python3 -c "
import yaml
import sys

try:
    with open('$file', 'r') as f:
        config = yaml.safe_load(f)
    
    neo4j_config = config.get('database', {}).get('neo4j', '')
    if not neo4j_config:
        sys.exit(1)
    
    # Parse the neo4j config string
    lines = neo4j_config.strip().split('\n')
    for line in lines:
        if ':' in line:
            k, v = line.split(':', 1)
            if k.strip() == '$key':
                print(v.strip())
                sys.exit(0)
    sys.exit(1)
except Exception as e:
    sys.exit(1)
"
}

# Try to find config file
CONFIG_FILE=""
for config in "config/config_boomer_load copy.yml" "config/config_boomer_load.yml" "config/config_boomer_model_userdefined.yml"; do
    if [ -f "$PROJECT_ROOT/$config" ]; then
        CONFIG_FILE="$PROJECT_ROOT/$config"
        echo "📁 Using config file: $config"
        break
    fi
done

if [ -z "$CONFIG_FILE" ]; then
    echo "❌ No config file found. Please run the script manually with parameters."
    echo ""
    echo "Usage:"
    echo "  $PROJECT_ROOT/scripts/cleanup/reset_neo4j_database_remote.sh -u bolt+s://your-server:7687 -U neo4j -p your_password"
    exit 1
fi

# Extract connection details
echo "🔍 Extracting connection details from config..."

NEO4J_HOST=$(extract_yaml_value "$CONFIG_FILE" "host")
NEO4J_PORT=$(extract_yaml_value "$CONFIG_FILE" "port")
NEO4J_USER=$(extract_yaml_value "$CONFIG_FILE" "user")
NEO4J_PASSWORD=$(extract_yaml_value "$CONFIG_FILE" "password")
NEO4J_DATABASE=$(extract_yaml_value "$CONFIG_FILE" "database")

# Default database if not specified
if [ -z "$NEO4J_DATABASE" ]; then
    NEO4J_DATABASE="neo4j"
fi

# Validate extracted values
if [ -z "$NEO4J_HOST" ] || [ -z "$NEO4J_PORT" ] || [ -z "$NEO4J_USER" ] || [ -z "$NEO4J_PASSWORD" ]; then
    echo "❌ Failed to extract connection details from config file"
    echo "Please check your config file or run the script manually"
    exit 1
fi

# Construct the URI (assuming bolt+s for remote connections)
NEO4J_URI="bolt+s://$NEO4J_HOST:$NEO4J_PORT"

echo "✅ Connection details extracted:"
echo "   URI: $NEO4J_URI"
echo "   Database: $NEO4J_DATABASE"
echo "   Username: $NEO4J_USER"
echo ""

# Run the reset script with extracted parameters
echo "🚀 Running remote database reset..."
echo ""

exec "$PROJECT_ROOT/scripts/cleanup/reset_neo4j_database_remote.sh" \
    -u "$NEO4J_URI" \
    -U "$NEO4J_USER" \
    -p "$NEO4J_PASSWORD" \
    -d "$NEO4J_DATABASE"