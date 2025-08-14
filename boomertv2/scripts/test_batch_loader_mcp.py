#!/usr/bin/env python3
"""
Test script to demonstrate MCP integration with Batch Loader.
"""

import sys
import os
import logging

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from batch_loader import BatchNeo4jLoader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_mcp_integration():
    """Test MCP integration with batch loader."""
    
    print("🧪 Testing MCP Integration with Batch Loader")
    print("=" * 50)
    
    # Initialize batch loader
    loader = BatchNeo4jLoader()
    
    # Test MCP Cypher generation
    print("\n1. Testing MCP Cypher Query Generation:")
    print("-" * 40)
    
    test_queries = [
        "create article node with title and content",
        "find articles about retirement planning",
        "count all articles in the database",
        "create relationship between article and author"
    ]
    
    for query in test_queries:
        print(f"\nRequest: {query}")
        cypher = loader.generate_cypher_with_mcp(query)
        print(f"Generated Cypher: {cypher}")
    
    # Test MCP Vector Search
    print("\n2. Testing MCP Vector Search:")
    print("-" * 40)
    
    test_questions = [
        "What are the best retirement strategies?",
        "How to plan for healthcare costs in retirement?",
        "Investment advice for seniors"
    ]
    
    for question in test_questions:
        print(f"\nQuestion: {question}")
        vector_query = loader.search_with_mcp_vector(question, top_k=3)
        print(f"Vector Search Query: {vector_query}")
    
    # Test MCP client status
    print("\n3. MCP Client Status:")
    print("-" * 40)
    
    if loader.mcp_cypher_client:
        print("✅ MCP Cypher client is available")
        print(f"   Server: {loader.mcp_cypher_client.server_name}")
    else:
        print("❌ MCP Cypher client is not available")
    
    if loader.mcp_vector_client:
        print("✅ MCP Vector Search client is available")
        print(f"   Server: {loader.mcp_vector_client.server_name}")
    else:
        print("❌ MCP Vector Search client is not available")
    
    print("\n" + "=" * 50)
    print("🎉 MCP Integration Test Completed!")

def test_mcp_config_loading():
    """Test MCP configuration loading."""
    
    print("\n🔧 Testing MCP Configuration Loading:")
    print("-" * 40)
    
    try:
        from mcp_client import load_mcp_config
        
        config_path = "config/claude_desktop_mcp_config.json"
        if os.path.exists(config_path):
            clients = load_mcp_config(config_path)
            print(f"✅ Loaded {len(clients)} MCP clients:")
            for name, client in clients.items():
                print(f"   - {name}: {client.server_name}")
        else:
            print(f"❌ MCP config file not found: {config_path}")
            
    except Exception as e:
        print(f"❌ Error loading MCP config: {str(e)}")

if __name__ == "__main__":
    test_mcp_config_loading()
    test_mcp_integration()
