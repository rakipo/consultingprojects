#!/usr/bin/env python3
"""
Main entry point and CLI interface for GraphRAG Retrieval Agent.

This module provides a command-line interface for direct usage of the GraphRAG
system, allowing users to perform queries and get formatted results without
requiring the MCP server interface.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

from modules.retrieval import get_graph_retriever
from modules.config import load_config, create_default_config_file
from modules.exceptions import GraphRAGException
from modules.logging_config import setup_logging, get_logger, log_exception


class GraphRAGCLI:
    """Command-line interface for GraphRAG retrieval system."""
    
    def __init__(self, config_path: str = "config/app.yaml"):
        """
        Initialize CLI interface.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.logger = get_logger("graphrag.cli")
        self.retriever = None
    
    def initialize(self) -> None:
        """Initialize the CLI system."""
        try:
            # Setup logging
            setup_logging()
            self.logger.info("Initializing GraphRAG CLI")
            
            # Load configuration
            if not Path(self.config_path).exists():
                self.logger.warning(f"Configuration file not found: {self.config_path}")
                print(f"Configuration file not found: {self.config_path}")
                print("Creating default configuration file...")
                create_default_config_file(self.config_path)
                print(f"Default configuration created at: {self.config_path}")
                print("Please edit the configuration file with your Neo4j credentials and run again.")
                sys.exit(1)
            
            self.config = load_config(self.config_path)
            
            # Initialize retriever
            neo4j_config = self.config.get("neo4j", {})
            self.retriever = get_graph_retriever(
                neo4j_uri=neo4j_config.get("uri"),
                neo4j_username=neo4j_config.get("username"),
                neo4j_password=neo4j_config.get("password"),
                neo4j_database=neo4j_config.get("database", "neo4j")
            )
            
            self.logger.info("GraphRAG CLI initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize GraphRAG CLI: {e}")
            print(f"Error: Failed to initialize GraphRAG CLI: {e}")
            sys.exit(1)
    
    def query(self, query_text: str, limit: int = 5, expand_graph: bool = True, 
              output_format: str = "text") -> None:
        """
        Perform a query and display results.
        
        Args:
            query_text: Natural language query
            limit: Maximum number of results
            expand_graph: Whether to expand graph for context
            output_format: Output format ('text', 'json')
        """
        try:
            self.logger.info(f"Processing query: {query_text[:100]}...")
            
            # Perform retrieval
            results = self.retriever.retrieve(query_text, limit, expand_graph)
            
            # Display results
            if output_format == "json":
                self._display_json_results(query_text, results)
            else:
                self._display_text_results(query_text, results)
            
            self.logger.info(f"Query completed with {len(results)} results")
            
        except GraphRAGException as e:
            self.logger.error(f"GraphRAG error during query: {e}")
            print(f"Error [{e.code}]: {e.message}")
            if e.details:
                print(f"Details: {json.dumps(e.details, indent=2)}")
            sys.exit(1)
            
        except Exception as e:
            log_exception(self.logger, e, {"query": query_text})
            print(f"Unexpected error: {e}")
            sys.exit(1)
    
    def _display_text_results(self, query: str, results: List[Dict[str, Any]]) -> None:
        """Display results in human-readable text format."""
        print(f"\n{'='*60}")
        print(f"GraphRAG Query Results")
        print(f"{'='*60}")
        print(f"Query: {query}")
        print(f"Results Found: {len(results)}")
        print(f"{'='*60}")
        
        if not results:
            print("\nNo relevant information found in the knowledge graph.")
            return
        
        for i, result in enumerate(results, 1):
            print(f"\n--- Result {i} ---")
            print(f"Relevance Score: {result['score']:.4f}")
            
            # Article and author info
            article = result.get("article", {})
            author = result.get("author", {})
            
            if author.get("name"):
                print(f"Author: {author['name']}")
            if article.get("title"):
                print(f"Article: {article['title']}")
            
            print(f"\nContent:")
            print(f"{result['chunk_text']}")
            
            # Context information
            context = result.get("context", {})
            related_chunks = context.get("related_chunks", [])
            other_articles = context.get("other_articles", [])
            
            if related_chunks:
                print(f"\nRelated Content: {len(related_chunks)} related chunks from the same article")
            
            if other_articles:
                print(f"Other Works by Author: {len(other_articles)} other articles")
                for article_info in other_articles[:3]:  # Show first 3
                    print(f"  - {article_info.get('title', 'Untitled')}")
                if len(other_articles) > 3:
                    print(f"  ... and {len(other_articles) - 3} more")
        
        print(f"\n{'='*60}")
    
    def _display_json_results(self, query: str, results: List[Dict[str, Any]]) -> None:
        """Display results in JSON format."""
        output = {
            "query": query,
            "results_count": len(results),
            "results": results
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    
    def status(self) -> None:
        """Display system status information."""
        try:
            self.logger.info("Checking system status")
            
            # Get system statistics
            stats = self.retriever.get_retrieval_stats()
            
            print(f"\n{'='*50}")
            print(f"GraphRAG System Status")
            print(f"{'='*50}")
            
            # Embedding model info
            embedding_info = stats.get("embedding_model", {})
            print(f"Embedding Model: {embedding_info.get('name', 'Unknown')}")
            print(f"Embedding Dimension: {embedding_info.get('dimension', 'Unknown')}")
            print(f"Device: {embedding_info.get('device', 'Unknown')}")
            
            # Neo4j info
            neo4j_info = stats.get("neo4j", {})
            print(f"\nNeo4j Connection: {'✓ Connected' if neo4j_info.get('connection') else '✗ Disconnected'}")
            print(f"Database: {neo4j_info.get('database', 'Unknown')}")
            
            # Index info
            indexes = neo4j_info.get("indexes", {})
            chunk_index = indexes.get("chunk_embeddings", {})
            print(f"Vector Index: {'✓ Available' if chunk_index.get('exists') else '✗ Missing'}")
            
            # Node counts
            node_counts = neo4j_info.get("node_counts", {})
            if isinstance(node_counts, dict) and "error" not in node_counts:
                print(f"\nData Statistics:")
                print(f"  Chunks: {node_counts.get('chunks', 0)}")
                print(f"  Articles: {node_counts.get('articles', 0)}")
                print(f"  Authors: {node_counts.get('authors', 0)}")
            
            # Overall status
            system_ready = stats.get("system_ready", False)
            print(f"\nSystem Status: {'✓ Ready' if system_ready else '✗ Not Ready'}")
            
            if not system_ready:
                print("\nSystem is not ready. Please check:")
                print("- Neo4j connection and credentials")
                print("- Vector index 'chunk_embeddings' exists")
                print("- Data has been loaded into the graph")
            
            print(f"{'='*50}")
            
        except Exception as e:
            log_exception(self.logger, e)
            print(f"Error checking system status: {e}")
            sys.exit(1)


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="GraphRAG Retrieval Agent - Query knowledge graphs with natural language",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s query "What is machine learning?"
  %(prog)s query "Who wrote about GPT-4?" --limit 10 --no-expand
  %(prog)s query "AI ethics" --format json
  %(prog)s status
  %(prog)s --config custom_config.yaml query "test query"
        """
    )
    
    parser.add_argument(
        "--config", "-c",
        default="config/app.yaml",
        help="Path to configuration file (default: config/app.yaml)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Perform a natural language query")
    query_parser.add_argument("text", help="Query text")
    query_parser.add_argument(
        "--limit", "-l",
        type=int,
        default=5,
        help="Maximum number of results (default: 5)"
    )
    query_parser.add_argument(
        "--no-expand",
        action="store_true",
        help="Disable graph expansion for additional context"
    )
    query_parser.add_argument(
        "--format", "-f",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    
    # Status command
    subparsers.add_parser("status", help="Show system status")
    
    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize CLI
    cli = GraphRAGCLI(args.config)
    cli.initialize()
    
    # Execute command
    if args.command == "query":
        cli.query(
            query_text=args.text,
            limit=args.limit,
            expand_graph=not args.no_expand,
            output_format=args.format
        )
    elif args.command == "status":
        cli.status()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()