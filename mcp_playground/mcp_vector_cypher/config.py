"""
Configuration management for MCP Vector Cypher Search.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration class for MCP Vector Cypher Search."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # Neo4j Configuration
        self.neo4j_uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        self.neo4j_user = os.getenv("NEO4J_USERNAME", os.getenv("NEO4J_USER", "neo4j"))
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "neo4j")
        self.neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
        
        # Vector Search Configuration
        self.vector_index_name = os.getenv("VECTOR_INDEX_NAME", "chunk_embeddings")
        self.similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.8"))
        self.top_k_chunks = int(os.getenv("TOP_K_CHUNKS", "5"))
        
        # Embedding Model Configuration
        self.embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
        
        # MCP Server Configuration
        self.server_name = "mcp-vector-cypher-search"
        self.log_level = os.getenv("MCP_LOG_LEVEL", "INFO")
    
    def update_search_parameters(
        self,
        similarity_threshold: Optional[float] = None,
        top_k_chunks: Optional[int] = None,
        vector_index_name: Optional[str] = None
    ) -> dict:
        """
        Update search parameters.
        
        Args:
            similarity_threshold: Minimum similarity score for chunk matching (0.0-1.0)
            top_k_chunks: Maximum number of chunks to return
            vector_index_name: Name of the vector index to use
            
        Returns:
            Current configuration settings
        """
        if similarity_threshold is not None:
            if 0.0 <= similarity_threshold <= 1.0:
                self.similarity_threshold = similarity_threshold
            else:
                raise ValueError(f"Invalid similarity threshold {similarity_threshold}, must be between 0.0 and 1.0")
        
        if top_k_chunks is not None:
            if top_k_chunks > 0:
                self.top_k_chunks = top_k_chunks
            else:
                raise ValueError(f"Invalid top_k_chunks {top_k_chunks}, must be greater than 0")
        
        if vector_index_name is not None:
            self.vector_index_name = vector_index_name
        
        return self.to_dict()
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "neo4j_uri": self.neo4j_uri,
            "neo4j_user": self.neo4j_user,
            "neo4j_password_set": bool(self.neo4j_password and self.neo4j_password != "neo4j"),
            "neo4j_database": self.neo4j_database,
            "vector_index_name": self.vector_index_name,
            "similarity_threshold": self.similarity_threshold,
            "top_k_chunks": self.top_k_chunks,
            "embedding_model_name": self.embedding_model_name,
            "server_name": self.server_name,
            "log_level": self.log_level,
            "current_working_directory": os.getcwd()
        }
    
    def get_env_vars_status(self) -> dict:
        """Get status of environment variables."""
        return {
            "NEO4J_URI": os.getenv("NEO4J_URI") is not None,
            "NEO4J_USERNAME": os.getenv("NEO4J_USERNAME") is not None,
            "NEO4J_USER": os.getenv("NEO4J_USER") is not None,
            "NEO4J_PASSWORD": os.getenv("NEO4J_PASSWORD") is not None,
            "VECTOR_INDEX_NAME": os.getenv("VECTOR_INDEX_NAME") is not None,
            "SIMILARITY_THRESHOLD": os.getenv("SIMILARITY_THRESHOLD") is not None,
            "TOP_K_CHUNKS": os.getenv("TOP_K_CHUNKS") is not None,
        }