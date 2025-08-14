#!/usr/bin/env python3
"""
Command-line interface for MCP Vector Cypher Search.
"""

import argparse
import asyncio
import sys
from .server import MCPVectorCypherServer
from .config import Config


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MCP Vector Cypher Search Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Start MCP server with stdio transport
  %(prog)s --transport stdio  # Same as above
  %(prog)s --test            # Run a test search
        """
    )
    
    parser.add_argument(
        "--transport",
        choices=["stdio"],
        default="stdio",
        help="Transport method for MCP server (default: stdio)"
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run a test search instead of starting the server"
    )
    
    parser.add_argument(
        "--query",
        default="GPT 4o",
        help="Test query to use (default: 'GPT 4o')"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Create configuration
    config = Config()
    config.log_level = args.log_level
    
    if args.test:
        # Run test mode
        asyncio.run(run_test(config, args.query))
    else:
        # Start MCP server
        server = MCPVectorCypherServer(config)
        server.run(transport=args.transport)


async def run_test(config: Config, query: str):
    """
    Run a test search.
    
    Args:
        config: Configuration object
        query: Test query string
    """
    print(f"Running test search for: '{query}'")
    print("=" * 50)
    
    server = MCPVectorCypherServer(config)
    
    try:
        # Test debug configuration
        print("1. Testing debug configuration...")
        debug_result = await server._debug_configuration()
        print(f"   Neo4j URI: {debug_result['neo4j_uri']}")
        print(f"   Vector Index: {debug_result['vector_index_name']}")
        print(f"   Password Set: {debug_result['neo4j_password_set']}")
        print()
        
        # Test vector search
        print(f"2. Testing vector search for '{query}'...")
        search_result = await server._vector_cypher_search(query)
        
        print(f"   Search Type: {search_result['search_type']}")
        print(f"   Chunks Found: {search_result['metadata']['chunks_found']}")
        print(f"   Cypher Records: {search_result['metadata']['cypher_records']}")
        
        if search_result['chunks']:
            chunk = search_result['chunks'][0]
            print(f"   First Chunk ID: {chunk['chunk_id']}")
            print(f"   Similarity Score: {chunk['similarity_score']:.4f}")
            content = chunk.get('content', 'No content')
            if content and len(content) > 100:
                print(f"   Content Preview: {content[:100]}...")
            else:
                print(f"   Content: {content}")
        
        print()
        print("Test completed successfully!")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        server.close()


if __name__ == "__main__":
    main()