"""
Custom exception classes for GraphRAG Retrieval Agent.

This module defines a hierarchy of custom exceptions with unique error codes
for different categories of errors that can occur in the system.

Error Code Categories:
- 1xxx: Configuration errors
- 2xxx: Neo4j connection/query errors  
- 3xxx: Embedding generation errors
- 4xxx: MCP server errors
- 5xxx: Retrieval logic errors
"""

from typing import Dict, Any, Optional


class GraphRAGException(Exception):
    """Base exception class for all GraphRAG-related errors."""
    
    def __init__(self, code: int, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize GraphRAG exception.
        
        Args:
            code: Unique error code (4-digit integer)
            message: Human-readable error message
            details: Optional dictionary with additional error context
        """
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(f"[{code}] {message}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON serialization."""
        return {
            "error_code": self.code,
            "error_message": self.message,
            "error_details": self.details,
            "error_type": self.__class__.__name__
        }


class ConfigurationError(GraphRAGException):
    """Configuration-related errors (1xxx codes)."""
    pass


class Neo4jError(GraphRAGException):
    """Neo4j connection and query errors (2xxx codes)."""
    pass


class EmbeddingError(GraphRAGException):
    """Embedding generation errors (3xxx codes)."""
    pass


class MCPServerError(GraphRAGException):
    """MCP server errors (4xxx codes)."""
    pass


class RetrievalError(GraphRAGException):
    """Retrieval logic errors (5xxx codes)."""
    pass


# Specific error codes and factory functions
class ErrorCodes:
    """Centralized error code definitions."""
    
    # Configuration errors (1xxx)
    CONFIG_FILE_NOT_FOUND = 1001
    CONFIG_INVALID_FORMAT = 1002
    CONFIG_MISSING_REQUIRED = 1003
    CONFIG_VALIDATION_FAILED = 1004
    
    # Neo4j errors (2xxx)
    NEO4J_CONNECTION_TIMEOUT = 2001
    NEO4J_AUTH_FAILED = 2002
    NEO4J_INDEX_NOT_FOUND = 2003
    NEO4J_QUERY_FAILED = 2004
    NEO4J_CONNECTION_LOST = 2005
    
    # Embedding errors (3xxx)
    EMBEDDING_MODEL_LOAD_FAILED = 3001
    EMBEDDING_TEXT_ENCODING_ERROR = 3002
    EMBEDDING_GENERATION_FAILED = 3003
    EMBEDDING_MODEL_NOT_FOUND = 3004
    
    # MCP server errors (4xxx)
    MCP_SERVER_STARTUP_FAILED = 4001
    MCP_INVALID_PARAMETERS = 4002
    MCP_TOOL_EXECUTION_FAILED = 4003
    MCP_PROTOCOL_ERROR = 4004
    
    # Retrieval errors (5xxx)
    RETRIEVAL_EMPTY_QUERY = 5001
    RETRIEVAL_GRAPH_EXPANSION_FAILED = 5002
    RETRIEVAL_RESULT_COMBINATION_FAILED = 5003
    RETRIEVAL_NO_RESULTS = 5004


def create_config_error(code: int, message: str, details: Optional[Dict[str, Any]] = None) -> ConfigurationError:
    """Create a configuration error with the specified code and message."""
    return ConfigurationError(code, message, details)


def create_neo4j_error(code: int, message: str, details: Optional[Dict[str, Any]] = None) -> Neo4jError:
    """Create a Neo4j error with the specified code and message."""
    return Neo4jError(code, message, details)


def create_embedding_error(code: int, message: str, details: Optional[Dict[str, Any]] = None) -> EmbeddingError:
    """Create an embedding error with the specified code and message."""
    return EmbeddingError(code, message, details)


def create_mcp_error(code: int, message: str, details: Optional[Dict[str, Any]] = None) -> MCPServerError:
    """Create an MCP server error with the specified code and message."""
    return MCPServerError(code, message, details)


def create_retrieval_error(code: int, message: str, details: Optional[Dict[str, Any]] = None) -> RetrievalError:
    """Create a retrieval error with the specified code and message."""
    return RetrievalError(code, message, details)