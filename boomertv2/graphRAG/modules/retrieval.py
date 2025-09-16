"""
Graph retrieval orchestration module for GraphRAG Retrieval Agent.

This module uses the neo4j-graphrag library directly to provide
comprehensive graph-based retrieval functionality.
"""

import logging
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

from neo4j import GraphDatabase
from neo4j_graphrag.retrievers import VectorRetriever
from neo4j_graphrag.embeddings import SentenceTransformerEmbeddings

from .exceptions import RetrievalError, ErrorCodes
from .logging_config import get_logger, log_exception, get_execution_tracer


class GraphRetriever:
    """Orchestrates graph-based retrieval using neo4j-graphrag library."""
    
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
        
        # GraphRAG components
        self.driver = None
        self.embeddings: Optional[SentenceTransformerEmbeddings] = None
        self.vector_retriever: Optional[VectorRetriever] = None
    
    def _initialize_graphrag(self) -> None:
        """Initialize GraphRAG components."""
        if self.vector_retriever is not None:
            return
            
        try:
            self.logger.info("Initializing GraphRAG components")
            
            # Create Neo4j driver
            self.driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_username, self.neo4j_password),
                connection_timeout=30,
                max_connection_lifetime=3600
            )
            
            # Test connection
            with self.driver.session(database=self.neo4j_database) as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                if test_value != 1:
                    raise RetrievalError(
                        ErrorCodes.RETRIEVAL_INITIALIZATION_FAILED,
                        "Neo4j connection test failed",
                        {"expected": 1, "got": test_value}
                    )
            
            # Initialize embeddings
            self.embeddings = SentenceTransformerEmbeddings(
                model="all-MiniLM-L6-v2"
            )
            
            # Initialize vector retriever
            self.vector_retriever = VectorRetriever(
                driver=self.driver,
                index_name="chunk_embeddings",
                embedder=self.embeddings,
                return_properties=["text", "chunk_id"],
                database=self.neo4j_database
            )
            
            self.logger.info("GraphRAG components initialized successfully")
            
        except Exception as e:
            error = RetrievalError(
                ErrorCodes.RETRIEVAL_INITIALIZATION_FAILED,
                f"Failed to initialize GraphRAG: {str(e)}",
                {"error": str(e), "error_type": type(e).__name__}
            )
            log_exception(self.logger, error)
            raise error
    
    def retrieve(self, query: str, limit: int = 5, expand_graph: bool = True) -> List[Dict[str, Any]]:
        """
        Perform comprehensive graph-based retrieval using neo4j-graphrag.
        
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
            
            # Initialize GraphRAG if not already done
            self._initialize_graphrag()
            
            # Step 1: Use VectorRetriever to retrieve documents
            self.tracer.log_trace_event(request_id, "graphrag_retrieval")
            documents = self.vector_retriever.get_relevant_documents(query, k=limit)
            
            if not documents:
                self.logger.info("No documents found for query")
                self.tracer.end_trace(request_id, "completed", {
                    "results_count": 0,
                    "reason": "no_documents_found"
                })
                return []
            
            self.logger.debug(f"Found {len(documents)} documents from GraphRAG")
            
            # Step 2: Expand graph if requested
            if expand_graph:
                self.tracer.log_trace_event(request_id, "graph_expansion")
                results = self._expand_and_format_results(documents, query)
            else:
                # Use documents as-is without expansion
                results = self._format_document_results(documents)
            
            self.logger.info(f"Retrieval completed with {len(results)} results")
            
            self.tracer.end_trace(request_id, "completed", {
                "results_count": len(results),
                "documents_found": len(documents),
                "graph_expanded": expand_graph
            })
            
            return results
            
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
    
    def _expand_and_format_results(self, documents: List[Any], query: str) -> List[Dict[str, Any]]:
        """
        Expand graph and format results with contextual information.
        
        Args:
            documents: Documents from GraphRAG retrieval
            query: Original query for context
            
        Returns:
            List of formatted results with expanded context
        """
        try:
            results = []
            
            for doc in documents:
                # Extract basic information from document
                chunk_text = doc.page_content
                metadata = doc.metadata
                
                # Get chunk ID from metadata
                chunk_id = metadata.get("chunk_id", "unknown")
                
                # Query for additional context using Cypher
                context_data = self._get_context_for_chunk(chunk_id)
                
                result = {
                    "chunk_id": chunk_id,
                    "chunk_text": chunk_text,
                    "score": getattr(doc, 'score', 0.0),  # GraphRAG may not always provide score
                    "article": context_data.get("article", {}),
                    "author": context_data.get("author", {}),
                    "context": {
                        "related_chunks": context_data.get("related_chunks", []),
                        "other_articles": context_data.get("other_articles", [])
                    }
                }
                
                results.append(result)
            
            # Sort by score if available
            results.sort(key=lambda x: x["score"], reverse=True)
            
            return results
            
        except Exception as e:
            raise RetrievalError(
                ErrorCodes.RETRIEVAL_RESULT_COMBINATION_FAILED,
                f"Failed to expand and format results: {str(e)}",
                {"documents_count": len(documents), "error": str(e)}
            )
    
    def _format_document_results(self, documents: List[Any]) -> List[Dict[str, Any]]:
        """
        Format document results without graph expansion.
        
        Args:
            documents: Documents from GraphRAG retrieval
            
        Returns:
            List of formatted results
        """
        formatted_results = []
        
        for doc in documents:
            chunk_text = doc.page_content
            metadata = doc.metadata
            
            result = {
                "chunk_id": metadata.get("chunk_id", "unknown"),
                "chunk_text": chunk_text,
                "score": getattr(doc, 'score', 0.0),
                "article": {},
                "author": {},
                "context": {
                    "related_chunks": [],
                    "other_articles": []
                }
            }
            formatted_results.append(result)
        
        # Sort by score if available
        formatted_results.sort(key=lambda x: x["score"], reverse=True)
        
        return formatted_results
    
    def _get_context_for_chunk(self, chunk_id: str) -> Dict[str, Any]:
        """
        Get contextual information for a chunk using Cypher queries.
        
        Args:
            chunk_id: Chunk ID to get context for
            
        Returns:
            Dictionary containing contextual information
        """
        try:
            with self.driver.session(database=self.neo4j_database) as session:
                # Query for article and author information
                query = """
                MATCH (chunk:Chunk)
                WHERE elementId(chunk) = $chunk_id
                
                // Get article and author relationships
                OPTIONAL MATCH (article:Article)-[:HAS_CHUNK]->(chunk)
                OPTIONAL MATCH (author:Author)-[:WROTE]->(article)
                
                // Get related chunks from same article
                OPTIONAL MATCH (article)-[:HAS_CHUNK]->(related_chunk:Chunk)
                WHERE elementId(related_chunk) <> $chunk_id
                
                // Get other articles by same author
                OPTIONAL MATCH (author)-[:WROTE]->(other_article:Article)
                WHERE elementId(other_article) <> elementId(article)
                
                RETURN 
                    elementId(article) as article_id,
                    article.title as article_title,
                    elementId(author) as author_id,
                    author.name as author_name,
                    collect(DISTINCT {
                        id: elementId(related_chunk),
                        text: related_chunk.text
                    }) as related_chunks,
                    collect(DISTINCT {
                        id: elementId(other_article),
                        title: other_article.title
                    }) as other_articles
                """
                
                result = session.run(query, {"chunk_id": chunk_id})
                record = result.single()
                
                if record:
                    # Filter out null entries
                    related_chunks = [
                        chunk for chunk in record["related_chunks"] 
                        if chunk["id"] is not None
                    ]
                    other_articles = [
                        article for article in record["other_articles"]
                        if article["id"] is not None
                    ]
                    
                    return {
                        "article": {
                            "id": record["article_id"],
                            "title": record["article_title"]
                        },
                        "author": {
                            "id": record["author_id"],
                            "name": record["author_name"]
                        },
                        "related_chunks": related_chunks,
                        "other_articles": other_articles
                    }
                
                return {
                    "article": {},
                    "author": {},
                    "related_chunks": [],
                    "other_articles": []
                }
                
        except Exception as e:
            self.logger.warning(f"Failed to get context for chunk {chunk_id}: {e}")
            return {
                "article": {},
                "author": {},
                "related_chunks": [],
                "other_articles": []
            }
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the retrieval system.
        
        Returns:
            Dictionary containing system statistics
        """
        try:
            # Initialize if not already done
            if self.vector_retriever is None:
                self._initialize_graphrag()
            
            # Get embedding model info
            model_info = {
                "name": "all-MiniLM-L6-v2",
                "dimension": 384,
                "device": "cpu"  # Default, could be enhanced to detect GPU
            }
            
            # Get Neo4j health info
            health_info = self._get_neo4j_health()
            
            stats = {
                "embedding_model": model_info,
                "neo4j": health_info,
                "system_ready": (
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
    
    def _get_neo4j_health(self) -> Dict[str, Any]:
        """
        Get Neo4j health information.
        
        Returns:
            Dictionary containing Neo4j health status
        """
        try:
            if self.driver is None:
                return {"connection": False, "error": "Driver not initialized"}
            
            with self.driver.session(database=self.neo4j_database) as session:
                # Test connection
                result = session.run("RETURN 1 as test")
                connection_ok = result.single()["test"] == 1
                
                health_info = {
                    "connection": connection_ok,
                    "database": self.neo4j_database,
                    "indexes": {},
                    "node_counts": {}
                }
                
                if connection_ok:
                    # Check vector index
                    try:
                        index_result = session.run(
                            "SHOW INDEXES YIELD name, type WHERE name = 'chunk_embeddings'"
                        )
                        index_record = index_result.single()
                        if index_record:
                            health_info["indexes"]["chunk_embeddings"] = {
                                "exists": True,
                                "type": index_record["type"]
                            }
                        else:
                            health_info["indexes"]["chunk_embeddings"] = {"exists": False}
                    except:
                        health_info["indexes"]["chunk_embeddings"] = {"exists": False, "error": "Could not check index"}
                    
                    # Get node counts
                    try:
                        counts_query = """
                        MATCH (c:Chunk) WITH count(c) as chunks
                        MATCH (a:Article) WITH chunks, count(a) as articles
                        MATCH (au:Author) WITH chunks, articles, count(au) as authors
                        RETURN chunks, articles, authors
                        """
                        counts_result = session.run(counts_query)
                        counts_record = counts_result.single()
                        if counts_record:
                            health_info["node_counts"] = {
                                "chunks": counts_record["chunks"],
                                "articles": counts_record["articles"],
                                "authors": counts_record["authors"]
                            }
                    except:
                        health_info["node_counts"] = {"error": "Could not get node counts"}
                
                return health_info
                
        except Exception as e:
            return {"connection": False, "error": str(e)}
    
    def close(self) -> None:
        """Close the Neo4j connection."""
        if self.driver:
            self.logger.info("Closing Neo4j connection")
            self.driver.close()
            self.driver = None


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