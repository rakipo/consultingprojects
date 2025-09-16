"""
Graph retrieval orchestration module for GraphRAG Retrieval Agent.

This module coordinates embedding generation and Neo4j operations to provide
comprehensive graph-based retrieval functionality. It combines vector similarity
search with graph expansion to return contextually rich results.
"""

import logging
from typing import List, Dict, Any, Optional, Set
from collections import defaultdict

from .embedding import generate_embedding, get_model_info
from .neo4j_client import get_neo4j_client
from .exceptions import RetrievalError, ErrorCodes
from .logging_config import get_logger, log_exception, get_execution_tracer


class GraphRetriever:
    """Orchestrates graph-based retrieval combining vector search and graph expansion."""
    
    def __init__(self, neo4j_uri: str = None, neo4j_username: str = None, 
                 neo4j_password: str = None, neo4j_database: str = "neo4j"):
        """
        Initialize graph retriever.
        
        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_username: Neo4j username
            neo4j_password: Neo4j password
            neo4j_database: Neo4j database name
        """
        self.neo4j_uri = neo4j_uri
        self.neo4j_username = neo4j_username
        self.neo4j_password = neo4j_password
        self.neo4j_database = neo4j_database
        self.logger = get_logger("graphrag.retrieval")
        self.tracer = get_execution_tracer("graphrag.retrieval")
        self._neo4j_client = None
    
    @property
    def neo4j_client(self):
        """Get Neo4j client instance."""
        if self._neo4j_client is None:
            self._neo4j_client = get_neo4j_client(
                self.neo4j_uri, 
                self.neo4j_username, 
                self.neo4j_password, 
                self.neo4j_database
            )
        return self._neo4j_client
    
    def retrieve(self, query: str, limit: int = 5, expand_graph: bool = True) -> List[Dict[str, Any]]:
        """
        Perform comprehensive graph-based retrieval.
        
        Args:
            query: Natural language query
            limit: Maximum number of initial chunks to retrieve
            expand_graph: Whether to expand graph for additional context
            
        Returns:
            List of dictionaries containing chunks with contextual information
            
        Raises:
            RetrievalError: If retrieval process fails
        """
        if not query or not query.strip():
            raise RetrievalError(
                ErrorCodes.RETRIEVAL_EMPTY_QUERY,
                "Cannot perform retrieval with empty query",
                {"query_length": len(query) if query else 0}
            )
        
        request_id = self.tracer.start_trace("graph_retrieval", {
            "query_length": len(query),
            "limit": limit,
            "expand_graph": expand_graph
        })
        
        try:
            self.logger.info(f"Starting graph retrieval for query: {query[:100]}...")
            
            # Step 1: Generate embedding for query
            self.tracer.log_trace_event(request_id, "generating_embedding")
            embedding = generate_embedding(query)
            
            self.logger.debug(f"Generated embedding with dimension {len(embedding)}")
            
            # Step 2: Perform vector similarity search
            self.tracer.log_trace_event(request_id, "vector_search")
            chunks = self.neo4j_client.vector_search(embedding, limit)
            
            if not chunks:
                self.logger.info("No chunks found for query")
                self.tracer.end_trace(request_id, "completed", {
                    "results_count": 0,
                    "reason": "no_chunks_found"
                })
                return []
            
            self.logger.debug(f"Found {len(chunks)} chunks from vector search")
            
            # Step 3: Expand graph if requested
            if expand_graph:
                self.tracer.log_trace_event(request_id, "graph_expansion")
                chunk_ids = [chunk["chunk_id"] for chunk in chunks]
                expanded_data = self.neo4j_client.expand_graph(chunk_ids)
                
                self.logger.debug(f"Expanded graph for {len(chunk_ids)} chunks")
                
                # Step 4: Combine results
                self.tracer.log_trace_event(request_id, "combining_results")
                combined_results = self._combine_results(chunks, expanded_data)
            else:
                # Use chunks as-is without expansion
                combined_results = self._format_chunk_results(chunks)
            
            self.logger.info(f"Retrieval completed with {len(combined_results)} results")
            
            self.tracer.end_trace(request_id, "completed", {
                "results_count": len(combined_results),
                "chunks_found": len(chunks),
                "graph_expanded": expand_graph
            })
            
            return combined_results
            
        except RetrievalError:
            # Re-raise retrieval errors as-is
            self.tracer.end_trace(request_id, "failed", error=RetrievalError)
            raise
            
        except Exception as e:
            error = RetrievalError(
                ErrorCodes.RETRIEVAL_RESULT_COMBINATION_FAILED,
                f"Graph retrieval failed: {str(e)}",
                {
                    "query_length": len(query),
                    "limit": limit,
                    "expand_graph": expand_graph,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            log_exception(self.logger, error)
            self.tracer.end_trace(request_id, "failed", error=error)
            raise error
    
    def _combine_results(self, chunks: List[Dict[str, Any]], 
                        expanded_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Combine vector search results with expanded graph data.
        
        Args:
            chunks: Results from vector similarity search
            expanded_data: Results from graph expansion
            
        Returns:
            Combined and enriched results
            
        Raises:
            RetrievalError: If result combination fails
        """
        try:
            # Create lookup for expanded data by chunk_id
            expanded_lookup = {item["chunk_id"]: item for item in expanded_data}
            
            combined_results = []
            
            for chunk in chunks:
                chunk_id = chunk["chunk_id"]
                expanded_info = expanded_lookup.get(chunk_id, {})
                
                # Build combined result
                result = {
                    "chunk_id": chunk_id,
                    "chunk_text": chunk["chunk_text"],
                    "score": chunk["score"],
                    "article": {
                        "id": chunk.get("article_id"),
                        "title": chunk.get("article_title")
                    },
                    "author": {
                        "id": chunk.get("author_id"),
                        "name": chunk.get("author_name")
                    }
                }
                
                # Add expanded context if available
                if expanded_info:
                    result["context"] = {
                        "related_chunks": expanded_info.get("related_chunks", []),
                        "other_articles": expanded_info.get("other_articles", [])
                    }
                else:
                    result["context"] = {
                        "related_chunks": [],
                        "other_articles": []
                    }
                
                combined_results.append(result)
            
            # Sort by score (highest first)
            combined_results.sort(key=lambda x: x["score"], reverse=True)
            
            return combined_results
            
        except Exception as e:
            raise RetrievalError(
                ErrorCodes.RETRIEVAL_RESULT_COMBINATION_FAILED,
                f"Failed to combine retrieval results: {str(e)}",
                {
                    "chunks_count": len(chunks),
                    "expanded_data_count": len(expanded_data),
                    "error": str(e)
                }
            )
    
    def _format_chunk_results(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format chunk results without graph expansion.
        
        Args:
            chunks: Raw chunk results from vector search
            
        Returns:
            Formatted results
        """
        formatted_results = []
        
        for chunk in chunks:
            result = {
                "chunk_id": chunk["chunk_id"],
                "chunk_text": chunk["chunk_text"],
                "score": chunk["score"],
                "article": {
                    "id": chunk.get("article_id"),
                    "title": chunk.get("article_title")
                },
                "author": {
                    "id": chunk.get("author_id"),
                    "name": chunk.get("author_name")
                },
                "context": {
                    "related_chunks": [],
                    "other_articles": []
                }
            }
            formatted_results.append(result)
        
        # Sort by score (highest first)
        formatted_results.sort(key=lambda x: x["score"], reverse=True)
        
        return formatted_results
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the retrieval system.
        
        Returns:
            Dictionary containing system statistics
        """
        try:
            # Get embedding model info
            model_info = get_model_info()
            
            # Get Neo4j health info
            health_info = self.neo4j_client.health_check()
            
            stats = {
                "embedding_model": {
                    "name": model_info.get("model_name"),
                    "dimension": model_info.get("embedding_dimension"),
                    "device": model_info.get("device")
                },
                "neo4j": {
                    "connection": health_info.get("connection", False),
                    "database": health_info.get("database"),
                    "indexes": health_info.get("indexes", {}),
                    "node_counts": health_info.get("node_counts", {})
                },
                "system_ready": (
                    model_info.get("embedding_dimension") == 384 and
                    health_info.get("connection", False) and
                    health_info.get("indexes", {}).get("chunk_embeddings", {}).get("exists", False)
                )
            }
            
            return stats
            
        except Exception as e:
            self.logger.warning(f"Failed to get retrieval stats: {e}")
            return {
                "error": str(e),
                "system_ready": False
            }


# Global retriever instance
_global_retriever: Optional[GraphRetriever] = None


def get_graph_retriever(neo4j_uri: str = None, neo4j_username: str = None,
                       neo4j_password: str = None, neo4j_database: str = "neo4j") -> GraphRetriever:
    """
    Get the global graph retriever instance.
    
    Args:
        neo4j_uri: Neo4j URI (only used on first call)
        neo4j_username: Neo4j username (only used on first call)
        neo4j_password: Neo4j password (only used on first call)
        neo4j_database: Neo4j database (only used on first call)
        
    Returns:
        GraphRetriever instance
    """
    global _global_retriever
    if _global_retriever is None:
        _global_retriever = GraphRetriever(neo4j_uri, neo4j_username, neo4j_password, neo4j_database)
    return _global_retriever


def retrieve(query: str, limit: int = 5, expand_graph: bool = True) -> List[Dict[str, Any]]:
    """
    Perform graph-based retrieval using the global retriever.
    
    Args:
        query: Natural language query
        limit: Maximum number of results
        expand_graph: Whether to expand graph for context
        
    Returns:
        List of retrieval results
        
    Raises:
        RetrievalError: If retrieval fails
    """
    retriever = get_graph_retriever()
    return retriever.retrieve(query, limit, expand_graph)


def get_system_stats() -> Dict[str, Any]:
    """
    Get system statistics using the global retriever.
    
    Returns:
        Dictionary containing system statistics
    """
    retriever = get_graph_retriever()
    return retriever.get_retrieval_stats()