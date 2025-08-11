#!/usr/bin/env python3
"""
Test script for the MCP Vector Cypher Search server.

This script demonstrates how to use the new mcp_vector_cypher_search server
with different types of questions.
"""

import sys
import os
import asyncio
import json

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_vector_cypher_search import vector_cypher_search, configure_search_parameters


async def test_vector_search_questions():
    """Test questions that should trigger vector search."""
    print("=" * 60)
    print("TESTING VECTOR SEARCH QUESTIONS")
    print("=" * 60)
    
    vector_questions = [
        "Find articles about machine learning",
        "What content discusses artificial intelligence?",
        "Show me information about data science",
        "Tell me about recent developments",  # No specific label
        "What are the latest trends?"  # No specific label
    ]
    
    for question in vector_questions:
        print(f"\nQuestion: {question}")
        print("-" * 40)
        
        try:
            result = await vector_cypher_search(question)
            print(f"Search Type: {result['search_type']}")
            print(f"Chunks Found: {result['metadata']['chunks_found']}")
            print(f"Cypher Records: {result['metadata']['cypher_records']}")
            
            if result['chunks']:
                print("Sample Chunks:")
                for i, chunk in enumerate(result['chunks'][:2]):  # Show first 2 chunks
                    print(f"  {i+1}. Score: {chunk['similarity_score']:.3f}")
                    print(f"     Content: {chunk['content'][:100]}...")
            
            if result['cypher_query']:
                print(f"Generated Cypher: {result['cypher_query']}")
                
        except Exception as e:
            print(f"Error: {e}")


async def test_direct_cypher_questions():
    """Test questions that should trigger direct Cypher generation."""
    print("\n" + "=" * 60)
    print("TESTING DIRECT CYPHER QUESTIONS")
    print("=" * 60)
    
    cypher_questions = [
        "How many users are in the database?",
        "Show me all user names and emails",
        "What are the different node types?",
        "Find all companies with more than 100 employees",
        "List all products ordered by price"
    ]
    
    for question in cypher_questions:
        print(f"\nQuestion: {question}")
        print("-" * 40)
        
        try:
            result = await vector_cypher_search(question)
            print(f"Search Type: {result['search_type']}")
            print(f"Cypher Records: {result['metadata']['cypher_records']}")
            
            if result['cypher_query']:
                print(f"Generated Cypher: {result['cypher_query']}")
            
            if result['cypher_results']:
                print("Sample Results:")
                for i, record in enumerate(result['cypher_results'][:3]):  # Show first 3 records
                    print(f"  {i+1}. {record}")
                    
        except Exception as e:
            print(f"Error: {e}")


async def test_configuration():
    """Test configuration changes."""
    print("\n" + "=" * 60)
    print("TESTING CONFIGURATION")
    print("=" * 60)
    
    # Get current configuration
    config = await configure_search_parameters()
    print("Current Configuration:")
    print(json.dumps(config, indent=2))
    
    # Update configuration
    print("\nUpdating configuration...")
    new_config = await configure_search_parameters(
        similarity_threshold=0.7,
        top_k_chunks=3,
        vector_index_name="custom_embeddings"
    )
    print("Updated Configuration:")
    print(json.dumps(new_config, indent=2))


async def test_error_handling():
    """Test error handling with invalid inputs."""
    print("\n" + "=" * 60)
    print("TESTING ERROR HANDLING")
    print("=" * 60)
    
    error_cases = [
        "",  # Empty question
        None,  # None question
        "   ",  # Whitespace only
    ]
    
    for question in error_cases:
        print(f"\nTesting with question: {repr(question)}")
        print("-" * 40)
        
        try:
            result = await vector_cypher_search(question)
            print(f"Search Type: {result['search_type']}")
            if 'error' in result:
                print(f"Error: {result['error']}")
                
        except Exception as e:
            print(f"Exception: {e}")


async def main():
    """Run all tests."""
    print("MCP Vector Cypher Search - Test Suite")
    print("=" * 60)
    
    try:
        await test_vector_search_questions()
        await test_direct_cypher_questions()
        await test_configuration()
        await test_error_handling()
        
        print("\n" + "=" * 60)
        print("TEST SUITE COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        print(f"Test suite failed: {e}")


if __name__ == "__main__":
    # Note: This test script simulates the MCP server functionality
    # In a real MCP environment, you would interact with the server via MCP protocol
    print("Note: This is a simulation test. In production, the MCP server")
    print("would be called via MCP protocol from Claude or other MCP clients.")
    print()
    
    asyncio.run(main())