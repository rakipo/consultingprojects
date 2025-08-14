#!/usr/bin/env python3
"""
MCP Client for Batch Loader
Provides integration with MCP (Model Context Protocol) servers for Cypher query generation.
"""

import logging
import json
import subprocess
import tempfile
import os
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class MCPClient:
    """
    MCP Client for connecting to MCP servers.
    """
    
    def __init__(self, server_config: Dict[str, Any]):
        """
        Initialize MCP client with server configuration.
        
        Args:
            server_config: MCP server configuration
        """
        self.server_config = server_config
        self.server_name = server_config.get('name', 'unknown')
        self.command = server_config.get('command', '')
        self.args = server_config.get('args', [])
        self.env = server_config.get('env', {})
        
    def call_mcp_cypher_server(self, query_request: str) -> str:
        """
        Call MCP Cypher server to generate Cypher queries.
        
        Args:
            query_request: Natural language request for Cypher query
            
        Returns:
            Generated Cypher query
        """
        try:
            logger.info(f"Calling MCP Cypher server: {self.server_name}")
            
            # Create temporary file for request
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                request_data = {
                    "method": "tools/call",
                    "params": {
                        "name": "write_cypher",
                        "arguments": {
                            "query": query_request
                        }
                    }
                }
                json.dump(request_data, temp_file, indent=2)
                temp_file_path = temp_file.name
            
            try:
                # Execute MCP server command
                result = subprocess.run(
                    [self.command] + self.args,
                    input=json.dumps(request_data),
                    text=True,
                    capture_output=True,
                    env=self.env,
                    timeout=30
                )
                
                if result.returncode == 0:
                    response = json.loads(result.stdout)
                    cypher_query = response.get('result', {}).get('content', [{}])[0].get('text', '')
                    logger.info("MCP Cypher server call successful")
                    return cypher_query
                else:
                    logger.error(f"MCP server error: {result.stderr}")
                    return self._generate_fallback_cypher(query_request)
                    
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except subprocess.TimeoutExpired:
            logger.error("MCP server call timed out")
            return self._generate_fallback_cypher(query_request)
        except Exception as e:
            logger.error(f"Error calling MCP server: {str(e)}")
            return self._generate_fallback_cypher(query_request)
    
    def call_mcp_vector_search(self, question: str, top_k: int = 5) -> str:
        """
        Call MCP Vector Cypher Search server for semantic search.
        
        Args:
            question: Natural language question
            top_k: Number of top results to return
            
        Returns:
            Cypher query for vector search
        """
        try:
            logger.info(f"Calling MCP Vector Search server: {self.server_name}")
            
            request_data = {
                "method": "tools/call",
                "params": {
                    "name": "vector_search",
                    "arguments": {
                        "question": question,
                        "top_k": top_k
                    }
                }
            }
            
            result = subprocess.run(
                [self.command] + self.args,
                input=json.dumps(request_data),
                text=True,
                capture_output=True,
                env=self.env,
                timeout=30
            )
            
            if result.returncode == 0:
                response = json.loads(result.stdout)
                cypher_query = response.get('result', {}).get('content', [{}])[0].get('text', '')
                logger.info("MCP Vector Search call successful")
                return cypher_query
            else:
                logger.error(f"MCP Vector Search error: {result.stderr}")
                return self._generate_fallback_vector_search(question, top_k)
                
        except Exception as e:
            logger.error(f"Error calling MCP Vector Search: {str(e)}")
            return self._generate_fallback_vector_search(question, top_k)
    
    def _generate_fallback_cypher(self, query_request: str) -> str:
        """
        Generate fallback Cypher query when MCP server is unavailable.
        
        Args:
            query_request: Request description
            
        Returns:
            Basic Cypher query
        """
        logger.warning("Using fallback Cypher generation")
        
        query_lower = query_request.lower()
        
        if "create article" in query_lower or "create node" in query_lower:
            return "MERGE (n:Article {id: $id}) SET n += $properties"
        elif "create relationship" in query_lower or "connect" in query_lower:
            return "MATCH (a), (b) WHERE a.id = $start_id AND b.id = $end_id MERGE (a)-[r:RELATES_TO]->(b)"
        elif "find" in query_lower or "search" in query_lower:
            return "MATCH (n) WHERE n.title CONTAINS $search_term RETURN n LIMIT 10"
        elif "count" in query_lower:
            return "MATCH (n) RETURN count(n) as total_count"
        else:
            return "MATCH (n) RETURN n LIMIT 10"
    
    def _generate_fallback_vector_search(self, question: str, top_k: int) -> str:
        """
        Generate fallback vector search query.
        
        Args:
            question: Search question
            top_k: Number of results
            
        Returns:
            Vector search Cypher query
        """
        logger.warning("Using fallback vector search generation")
        
        return f"""
        MATCH (c:Chunk)
        WHERE c.embedding IS NOT NULL
        RETURN c.chunk_text, c.chunk_id
        LIMIT {top_k}
        """

def load_mcp_config(config_path: str) -> Dict[str, MCPClient]:
    """
    Load MCP configuration and create clients.
    
    Args:
        config_path: Path to MCP configuration file
        
    Returns:
        Dictionary of MCP clients
    """
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        clients = {}
        mcp_servers = config.get('mcpServers', {})
        
        for server_name, server_config in mcp_servers.items():
            server_config['name'] = server_name
            clients[server_name] = MCPClient(server_config)
            logger.info(f"Loaded MCP client: {server_name}")
        
        return clients
        
    except Exception as e:
        logger.error(f"Error loading MCP config: {str(e)}")
        return {}

def get_mcp_cypher_client(config_path: str = "config/claude_desktop_mcp_config.json") -> Optional[MCPClient]:
    """
    Get MCP Cypher client from configuration.
    
    Args:
        config_path: Path to MCP configuration file
        
    Returns:
        MCP Cypher client or None if not available
    """
    clients = load_mcp_config(config_path)
    return clients.get('mcp-cypher')

def get_mcp_vector_search_client(config_path: str = "config/claude_desktop_mcp_config.json") -> Optional[MCPClient]:
    """
    Get MCP Vector Search client from configuration.
    
    Args:
        config_path: Path to MCP configuration file
        
    Returns:
        MCP Vector Search client or None if not available
    """
    clients = load_mcp_config(config_path)
    return clients.get('mcp-vector-cypher-search')
