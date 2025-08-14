#!/usr/bin/env python3
"""
Test script to verify the MCP Vector Cypher Search server is working
"""

import subprocess
import json
import sys

def test_mcp_server():
    """Test the MCP server by sending a simple request"""
    print("🧪 Testing MCP Vector Cypher Search Server")
    print("=" * 50)
    
    try:
        # Test if the container is running
        result = subprocess.run([
            "docker", "exec", "mcp_vector_cypher_search", 
            "python", "-c", "print('Container is accessible')"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Container is running and accessible")
        else:
            print(f"❌ Container access failed: {result.stderr}")
            return False
        
        # Test if the MCP server can start
        result = subprocess.run([
            "docker", "exec", "mcp_vector_cypher_search",
            "python", "-c", 
            "import src.mcp_vector_cypher_search; print('MCP server module can be imported')"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ MCP server module can be imported")
        else:
            print(f"❌ MCP server import failed: {result.stderr}")
            return False
        
        # Test Neo4j connection
        result = subprocess.run([
            "docker", "exec", "mcp_vector_cypher_search",
            "python", "-c", 
            """
from neo4j import GraphDatabase
try:
    driver = GraphDatabase.driver('bolt://neo4j:7687', auth=('neo4j', 'password123'))
    with driver.session() as session:
        result = session.run('RETURN 1 as test')
        record = result.single()
        print('Neo4j connection successful')
        driver.close()
except Exception as e:
    print(f'Neo4j connection failed: {e}')
    """
        ], capture_output=True, text=True, timeout=15)
        
        if "Neo4j connection successful" in result.stdout:
            print("✅ Neo4j connection is working")
        else:
            print(f"❌ Neo4j connection failed: {result.stdout} {result.stderr}")
        
        print("\n📊 Container Status:")
        status_result = subprocess.run([
            "docker", "ps", "--filter", "name=mcp_vector_cypher_search", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        ], capture_output=True, text=True)
        
        print(status_result.stdout)
        
        print("\n💡 To use this MCP server with Claude Desktop:")
        print("Add this to your Claude Desktop config:")
        print("""
{
  "mcpServers": {
    "mcp-vector-cypher-search": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "mcp_vector_cypher_search",
        "python",
        "-u",
        "src/mcp_vector_cypher_search.py"
      ]
    }
  }
}
        """)
        
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Test timed out")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = test_mcp_server()
    sys.exit(0 if success else 1)