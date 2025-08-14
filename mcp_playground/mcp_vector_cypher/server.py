"""
MCP Server implementation for Vector Cypher Search.
"""

import logging
from typing import Dict, Any, Optional

from .config import Config
from .search import VectorSearch
from .cypher import CypherGenerator

try:
    from mcp.server.fastmcp import FastMCP
except Exception as e:
    raise RuntimeError(
        "mcp package is required. Install with `pip install mcp`."
    ) from e

logger = logging.getLogger(__name__)


class MCPVectorCypherServer:
    """MCP Server for Vector Cypher Search functionality."""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the MCP server.
        
        Args:
            config: Configuration object (creates default if None)
        """
        self.config = config or Config()
        self.vector_search = VectorSearch(self.config)
        self.cypher_generator = CypherGenerator(self.config)
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s",
        )
        
        # Initialize FastMCP server
        self.mcp = FastMCP(self.config.server_name)
        self._register_tools()
    
    def _register_tools(self):
        """Register MCP tools."""
        
        @self.mcp.tool()
        async def vector_cypher_search(question: str) -> Dict[str, Any]:
            """
            Perform intelligent search combining vector similarity and Cypher queries.
            
            This tool analyzes the question and:
            1. If it contains "Article" or no specific labels, performs vector search for similar chunks
            2. Generates appropriate Cypher queries for detailed data retrieval
            3. Returns both chunk results and Cypher query results separately
            
            Args:
                question: The search question or query
                
            Returns:
                Dictionary containing:
                - search_type: "vector" or "direct_cypher"
                - chunks: List of similar chunks (if vector search was used)
                - cypher_query: The generated Cypher query
                - cypher_results: Results from executing the Cypher query
                - metadata: Additional information about the search
            """
            return await self._vector_cypher_search(question)
        
        @self.mcp.tool()
        async def debug_configuration() -> Dict[str, Any]:
            """
            Debug tool to check current configuration and environment variables.
            
            Returns:
                Current configuration settings and environment status
            """
            return await self._debug_configuration()
        
        @self.mcp.tool()
        async def configure_search_parameters(
            similarity_threshold: Optional[float] = None,
            top_k_chunks: Optional[int] = None,
            vector_index_name: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Configure search parameters for the vector Cypher search.
            
            Args:
                similarity_threshold: Minimum similarity score for chunk matching (0.0-1.0)
                top_k_chunks: Maximum number of chunks to return
                vector_index_name: Name of the vector index to use
                
            Returns:
                Current configuration settings
            """
            return await self._configure_search_parameters(
                similarity_threshold, top_k_chunks, vector_index_name
            )
    
    async def _vector_cypher_search(self, question: str) -> Dict[str, Any]:
        """Implementation of vector_cypher_search tool."""
        if not question or not question.strip():
            return {
                "search_type": "error",
                "error": "Question cannot be empty",
                "chunks": [],
                "cypher_query": "",
                "cypher_results": [],
                "metadata": {}
            }
        
        logger.info(f"Processing question: {question}")
        
        # Determine search strategy
        use_vector_search = self.vector_search.should_use_vector_search(question)
        search_type = "vector" if use_vector_search else "direct_cypher"
        
        chunks = []
        cypher_results = []
        cypher_query = ""
        
        try:
            if use_vector_search:
                logger.info("Using vector search strategy")
                
                # Step 1: Create embedding for the question
                query_embedding = await self.vector_search.create_embedding(question)
                
                # Step 2: Search for similar chunks
                chunks = await self.vector_search.search_similar_chunks(query_embedding)
                
                # Step 3: Generate Cypher query for detailed retrieval
                # Modify question to be more specific based on found chunks
                if chunks:
                    chunk_ids = [chunk["chunk_id"] for chunk in chunks[:3]]  # Use top 3 chunks
                    enhanced_question = f"{question} (related to chunks: {', '.join(chunk_ids)})"
                    cypher_query = await self.cypher_generator.call_mcp_neo4j_cypher(enhanced_question)
                else:
                    cypher_query = await self.cypher_generator.call_mcp_neo4j_cypher(question)
            else:
                logger.info("Using direct Cypher strategy")
                
                # Direct Cypher query generation
                cypher_query = await self.cypher_generator.call_mcp_neo4j_cypher(question)
            
            # Step 4: Execute Cypher query
            if cypher_query:
                cypher_results = await self.cypher_generator.execute_cypher_query(cypher_query)
            
            # Prepare response
            response = {
                "search_type": search_type,
                "chunks": chunks,
                "cypher_query": cypher_query,
                "cypher_results": cypher_results,
                "metadata": {
                    "question": question,
                    "chunks_found": len(chunks),
                    "cypher_records": len(cypher_results),
                    "vector_search_used": use_vector_search,
                    "embedding_dimension": len(await self.vector_search.create_embedding(question)) if use_vector_search else 0
                }
            }
            
            logger.info(f"Search completed: {search_type}, {len(chunks)} chunks, {len(cypher_results)} cypher results")
            return response
            
        except Exception as e:
            logger.error(f"Error in vector_cypher_search: {e}")
            return {
                "search_type": "error",
                "error": str(e),
                "chunks": chunks,
                "cypher_query": cypher_query,
                "cypher_results": cypher_results,
                "metadata": {
                    "question": question,
                    "error_occurred": True
                }
            }
    
    async def _debug_configuration(self) -> Dict[str, Any]:
        """Implementation of debug_configuration tool."""
        config_dict = self.config.to_dict()
        config_dict["env_vars_found"] = self.config.get_env_vars_status()
        return config_dict
    
    async def _configure_search_parameters(
        self,
        similarity_threshold: Optional[float] = None,
        top_k_chunks: Optional[int] = None,
        vector_index_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Implementation of configure_search_parameters tool."""
        try:
            result = self.config.update_search_parameters(
                similarity_threshold, top_k_chunks, vector_index_name
            )
            
            # Log the updates
            if similarity_threshold is not None:
                logger.info(f"Updated similarity threshold to {similarity_threshold}")
            if top_k_chunks is not None:
                logger.info(f"Updated top_k_chunks to {top_k_chunks}")
            if vector_index_name is not None:
                logger.info(f"Updated vector index name to {vector_index_name}")
            
            return result
            
        except ValueError as e:
            logger.warning(str(e))
            return {"error": str(e), **self.config.to_dict()}
    
    def run(self, transport: str = "stdio"):
        """
        Run the MCP server.
        
        Args:
            transport: Transport method (default: "stdio")
        """
        logger.info(f"Starting MCP stdio server: {self.config.server_name}")
        try:
            self.mcp.run(transport=transport)
        finally:
            self.close()
    
    def close(self):
        """Close connections and cleanup resources."""
        self.vector_search.close()
        self.cypher_generator.close()