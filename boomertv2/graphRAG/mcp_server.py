#!/usr/bin/env python3
"""
MCP (Model Context Protocol) server for GraphRAG Retrieval Agent.

This module provides an MCP-compliant server interface that exposes GraphRAG
functionality to Claude Desktop and other MCP clients. It implements the
graph_retrieve tool for natural language queries against the knowledge graph.
"""

import asyncio
import json
import sys
from typing import Dict, Any, List, Optional
import traceback

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from modules.retrieval import get_graph_retriever
from modules.config import load_config
from modules.exceptions import MCPServerError, ErrorCodes, GraphRAGException
from modules.logging_config import setup_logging, get_logger, log_exception, get_execution_tracer


class GraphRAGMCPServer:
    """MCP server for GraphRAG functionality."""
    
    def __init__(self, config_path: str = "config/app.yaml"):
        """
        Initialize MCP server.
        
        Args:
            config_path: Path to application configuration file
        """
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.server = Server("graphrag-retrieval-agent")
        self.logger = get_logger("graphrag.mcp_server")
        self.tracer = get_execution_tracer("graphrag.mcp_server")
        self.retriever = None
        
        # Setup server handlers
        self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        """Set up MCP server handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="graph_retrieve",
                    description="Retrieve information from knowledge graph using natural language queries. "
                               "Combines vector similarity search with graph traversal to provide contextually rich results.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language query to search for in the knowledge graph"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results to return (default: 5)",
                                "minimum": 1,
                                "maximum": 20,
                                "default": 5
                            },
                            "expand_graph": {
                                "type": "boolean",
                                "description": "Whether to expand graph for additional context (default: true)",
                                "default": True
                            }
                        },
                        "required": ["query"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls."""
            if name == "graph_retrieve":
                return await self._handle_graph_retrieve(arguments)
            else:
                raise MCPServerError(
                    ErrorCodes.MCP_TOOL_EXECUTION_FAILED,
                    f"Unknown tool: {name}",
                    {"tool_name": name, "available_tools": ["graph_retrieve"]}
                )
    
    async def _handle_graph_retrieve(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Handle graph_retrieve tool calls.
        
        Args:
            arguments: Tool arguments containing query and options
            
        Returns:
            List of TextContent with retrieval results
        """
        request_id = self.tracer.start_trace("mcp_graph_retrieve", arguments)
        
        try:
            # Validate arguments
            query = arguments.get("query")
            if not query:
                raise MCPServerError(
                    ErrorCodes.MCP_INVALID_PARAMETERS,
                    "Missing required parameter: query",
                    {"provided_arguments": list(arguments.keys())}
                )
            
            limit = arguments.get("limit", 5)
            expand_graph = arguments.get("expand_graph", True)
            
            # Validate limit
            if not isinstance(limit, int) or limit < 1 or limit > 20:
                raise MCPServerError(
                    ErrorCodes.MCP_INVALID_PARAMETERS,
                    "Parameter 'limit' must be an integer between 1 and 20",
                    {"provided_limit": limit}
                )
            
            self.logger.info(f"Processing graph_retrieve request: {query[:100]}...")
            
            # Ensure retriever is initialized
            if self.retriever is None:
                await self._initialize_retriever()
            
            # Perform retrieval
            self.tracer.log_trace_event(request_id, "performing_retrieval")
            results = self.retriever.retrieve(query, limit, expand_graph)
            
            # Format results for MCP response
            response_data = {
                "query": query,
                "results_count": len(results),
                "results": results,
                "system_info": {
                    "limit": limit,
                    "expand_graph": expand_graph,
                    "timestamp": self.tracer.traces[request_id]["start_timestamp"]
                }
            }
            
            # Create formatted text response
            formatted_response = self._format_response(response_data)
            
            self.logger.info(f"Graph retrieval completed with {len(results)} results")
            self.tracer.end_trace(request_id, "completed", {
                "results_count": len(results),
                "query_length": len(query)
            })
            
            return [TextContent(type="text", text=formatted_response)]
            
        except GraphRAGException as e:
            # Handle known GraphRAG exceptions
            error_response = {
                "error": True,
                "error_code": e.code,
                "error_message": e.message,
                "error_details": e.details,
                "query": arguments.get("query", "")
            }
            
            log_exception(self.logger, e, {"mcp_arguments": arguments})
            self.tracer.end_trace(request_id, "failed", error=e)
            
            return [TextContent(
                type="text", 
                text=f"GraphRAG Error [{e.code}]: {e.message}\n\nDetails: {json.dumps(e.details, indent=2)}"
            )]
            
        except Exception as e:
            # Handle unexpected exceptions
            error = MCPServerError(
                ErrorCodes.MCP_TOOL_EXECUTION_FAILED,
                f"Tool execution failed: {str(e)}",
                {
                    "tool_name": "graph_retrieve",
                    "arguments": arguments,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            
            log_exception(self.logger, error, {"traceback": traceback.format_exc()})
            self.tracer.end_trace(request_id, "failed", error=error)
            
            return [TextContent(
                type="text",
                text=f"MCP Server Error [{error.code}]: {error.message}\n\nPlease check the server logs for more details."
            )]
    
    async def _initialize_retriever(self) -> None:
        """Initialize the graph retriever with configuration."""
        try:
            self.logger.info("Initializing GraphRAG retriever")
            
            # Load configuration
            self.config = load_config(self.config_path)
            neo4j_config = self.config.get("neo4j", {})
            
            # Initialize retriever
            self.retriever = get_graph_retriever(
                neo4j_uri=neo4j_config.get("uri", "bolt://localhost:7687"),
                neo4j_username=neo4j_config.get("username", "neo4j"),
                neo4j_password=neo4j_config.get("password", "password"),
                neo4j_database=neo4j_config.get("database", "neo4j")
            )
            
            # Test the system
            stats = self.retriever.get_retrieval_stats()
            if not stats.get("system_ready", False):
                self.logger.warning("GraphRAG system may not be fully ready", extra={"stats": stats})
            else:
                self.logger.info("GraphRAG system initialized and ready")
            
        except Exception as e:
            error = MCPServerError(
                ErrorCodes.MCP_SERVER_STARTUP_FAILED,
                f"Failed to initialize GraphRAG retriever: {str(e)}",
                {"config_path": self.config_path, "error": str(e)}
            )
            log_exception(self.logger, error)
            raise error
    
    def _format_response(self, response_data: Dict[str, Any]) -> str:
        """
        Format retrieval results for human-readable display.
        
        Args:
            response_data: Raw response data from retrieval
            
        Returns:
            Formatted string response
        """
        query = response_data["query"]
        results = response_data["results"]
        results_count = response_data["results_count"]
        
        if results_count == 0:
            return f"# GraphRAG Query Results\n\n**Query:** {query}\n\n**Results:** No relevant information found in the knowledge graph."
        
        # Build formatted response
        formatted = f"# GraphRAG Query Results\n\n"
        formatted += f"**Query:** {query}\n"
        formatted += f"**Results Found:** {results_count}\n\n"
        
        for i, result in enumerate(results, 1):
            formatted += f"## Result {i}\n\n"
            formatted += f"**Relevance Score:** {result['score']:.4f}\n\n"
            
            # Article and author info
            article = result.get("article", {})
            author = result.get("author", {})
            
            if author.get("name"):
                formatted += f"**Author:** {author['name']}\n"
            if article.get("title"):
                formatted += f"**Article:** {article['title']}\n"
            
            formatted += f"\n**Content:**\n{result['chunk_text']}\n\n"
            
            # Context information
            context = result.get("context", {})
            related_chunks = context.get("related_chunks", [])
            other_articles = context.get("other_articles", [])
            
            if related_chunks:
                formatted += f"**Related Content:** {len(related_chunks)} related chunks from the same article\n"
            
            if other_articles:
                formatted += f"**Other Works by Author:** {len(other_articles)} other articles\n"
            
            formatted += "\n---\n\n"
        
        return formatted
    
    async def run(self) -> None:
        """Run the MCP server."""
        try:
            self.logger.info("Starting GraphRAG MCP server")
            
            # Initialize logging
            setup_logging()
            
            # Run server
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options()
                )
                
        except Exception as e:
            error = MCPServerError(
                ErrorCodes.MCP_SERVER_STARTUP_FAILED,
                f"MCP server startup failed: {str(e)}",
                {"error": str(e), "error_type": type(e).__name__}
            )
            log_exception(self.logger, error)
            raise error


async def main():
    """Main entry point for MCP server."""
    try:
        server = GraphRAGMCPServer()
        await server.run()
    except KeyboardInterrupt:
        print("\nMCP server stopped by user")
    except Exception as e:
        print(f"MCP server failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())