"""
Neo4j client module for GraphRAG Retrieval Agent.

This module provides functionality to connect to Neo4j database, perform vector
similarity searches using the chunk_embeddings index, and expand graph traversal
to retrieve connected entities (authors, articles) using the official neo4j-graphrag library.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
import time

from neo4j import GraphDatabase, Driver, Session, Transaction
from neo4j.exceptions import ServiceUnavailable, AuthError, ClientError, TransientError
from neo4j_graphrag import GraphRAG
from neo4j_graphrag.retrievers import VectorRetriever, VectorCypherRetriever
from neo4j_graphrag.embeddings import SentenceTransformerEmbeddings
from neo4j_graphrag.generation import RagTemplate

from .exceptions import Neo4jError, ErrorCodes
from .logging_config import get_logger, log_exception, get_execution_tracer


class Neo4jClient:
    """Handles all Neo4j database operations for GraphRAG retrieval using neo4j-graphrag library."""
    
    def __init__(self, uri: str, username: str, password: str, database: str = "neo4j"):
        """
        Initialize Neo4j client with GraphRAG capabilities.
        
        Args:
            uri: Neo4j connection URI (e.g., "bolt://localhost:7687")
            username: Neo4j username
            password: Neo4j password
            database: Database name (default: "neo4j")
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.driver: Optional[Driver] = None
        self.logger = get_logger("graphrag.neo4j")
        self.tracer = get_execution_tracer("graphrag.neo4j")
        
        # GraphRAG components
        self.graphrag: Optional[GraphRAG] = None
        self.embeddings: Optional[SentenceTransformerEmbeddings] = None
        self.vector_retriever: Optional[VectorRetriever] = None
    
    def connect(self) -> None:
        """
        Establish connection to Neo4j database and initialize GraphRAG components.
        
        Raises:
            Neo4jError: If connection fails
        """
        if self.driver is not None:
            return
        
        request_id = self.tracer.start_trace("neo4j_connect", {
            "uri": self.uri,
            "username": self.username,
            "database": self.database
        })
        
        try:
            self.logger.info(f"Connecting to Neo4j at {self.uri}")
            
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
                connection_timeout=30,
                max_connection_lifetime=3600
            )
            
            # Test the connection
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                if test_value != 1:
                    raise Neo4jError(
                        ErrorCodes.NEO4J_CONNECTION_LOST,
                        "Connection test failed",
                        {"expected": 1, "got": test_value}
                    )
            
            # Initialize GraphRAG components
            self._initialize_graphrag()
            
            self.logger.info("Successfully connected to Neo4j and initialized GraphRAG")
            self.tracer.end_trace(request_id, "completed", {"connection_status": "success"})
            
        except ServiceUnavailable as e:
            error = Neo4jError(
                ErrorCodes.NEO4J_CONNECTION_TIMEOUT,
                f"Neo4j service unavailable: {str(e)}",
                {"uri": self.uri, "error": str(e)}
            )
            log_exception(self.logger, error)
            self.tracer.end_trace(request_id, "failed", error=error)
            raise error
            
        except AuthError as e:
            error = Neo4jError(
                ErrorCodes.NEO4J_AUTH_FAILED,
                f"Neo4j authentication failed: {str(e)}",
                {"username": self.username, "error": str(e)}
            )
            log_exception(self.logger, error)
            self.tracer.end_trace(request_id, "failed", error=error)
            raise error
            
        except Exception as e:
            error = Neo4jError(
                ErrorCodes.NEO4J_CONNECTION_TIMEOUT,
                f"Failed to connect to Neo4j: {str(e)}",
                {"uri": self.uri, "error": str(e), "error_type": type(e).__name__}
            )
            log_exception(self.logger, error)
            self.tracer.end_trace(request_id, "failed", error=error)
            raise error
    
    def _initialize_graphrag(self) -> None:
        """Initialize GraphRAG components."""
        try:
            # Initialize embeddings with sentence-transformers
            self.embeddings = SentenceTransformerEmbeddings(
                model="all-MiniLM-L6-v2"
            )
            
            # Initialize vector retriever
            self.vector_retriever = VectorRetriever(
                driver=self.driver,
                index_name="chunk_embeddings",
                embedder=self.embeddings,
                return_properties=["text", "chunk_id"],
                database=self.database
            )
            
            # Initialize GraphRAG
            self.graphrag = GraphRAG(
                retriever=self.vector_retriever,
                llm=None  # We don't need LLM for retrieval-only
            )
            
            self.logger.info("GraphRAG components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize GraphRAG components: {e}")
            raise Neo4jError(
                ErrorCodes.NEO4J_CONNECTION_TIMEOUT,
                f"Failed to initialize GraphRAG: {str(e)}",
                {"error": str(e)}
            )
    
    def close(self) -> None:
        """Close the Neo4j connection."""
        if self.driver:
            self.logger.info("Closing Neo4j connection")
            self.driver.close()
            self.driver = None
    
    @contextmanager
    def get_session(self):
        """Context manager for Neo4j sessions."""
        self.connect()
        session = self.driver.session(database=self.database)
        try:
            yield session
        finally:
            session.close()
    
    def vector_search(self, embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search using the chunk_embeddings index.
        
        Args:
            embedding: Query embedding vector
            limit: Maximum number of results to return
            
        Returns:
            List of dictionaries containing chunk information and similarity scores
            
        Raises:
            Neo4jError: If vector search fails
        """
        request_id = self.tracer.start_trace("vector_search", {
            "embedding_dimension": len(embedding),
            "limit": limit
        })
        
        try:
            self.logger.debug(f"Performing vector search with limit {limit}")
            
            # Cypher query for vector similarity search
            query = """
            CALL db.index.vector.queryNodes('chunk_embedding_vector', $limit, $embedding)
            YIELD node, score
            MATCH (node:Chunk)
            OPTIONAL MATCH (article:Article)-[:HAS_CHUNK]->(node)
            OPTIONAL MATCH (author:Author)-[:WROTE]->(article)
            RETURN 
                node.text as chunk_text,
                elementId(node) as chunk_id,
                score,
                article.title as article_title,
                elementId(article) as article_id,
                author.name as author_name,
                elementId(author) as author_id
            ORDER BY score DESC
            """
            
            with self.get_session() as session:
                result = session.run(query, {
                    "embedding": embedding,
                    "limit": limit
                })
                
                chunks = []
                for record in result:
                    chunk_data = {
                        "chunk_id": record["chunk_id"],
                        "chunk_text": record["chunk_text"],
                        "score": record["score"],
                        "article_id": record["article_id"],
                        "article_title": record["article_title"],
                        "author_id": record["author_id"],
                        "author_name": record["author_name"]
                    }
                    chunks.append(chunk_data)
                
                self.logger.debug(f"Vector search returned {len(chunks)} results")
                self.tracer.end_trace(request_id, "completed", {
                    "results_count": len(chunks),
                    "top_score": chunks[0]["score"] if chunks else None
                })
                
                return chunks
                
        except ClientError as e:
            if "index" in str(e).lower() and "chunk_embeddings" in str(e).lower():
                error = Neo4jError(
                    ErrorCodes.NEO4J_INDEX_NOT_FOUND,
                    f"Vector index 'chunk_embeddings' not found: {str(e)}",
                    {"index_name": "chunk_embeddings", "error": str(e)}
                )
            else:
                error = Neo4jError(
                    ErrorCodes.NEO4J_QUERY_FAILED,
                    f"Vector search query failed: {str(e)}",
                    {"query": "vector_search", "error": str(e)}
                )
            log_exception(self.logger, error)
            self.tracer.end_trace(request_id, "failed", error=error)
            raise error
            
        except Exception as e:
            error = Neo4jError(
                ErrorCodes.NEO4J_QUERY_FAILED,
                f"Vector search failed: {str(e)}",
                {"embedding_dimension": len(embedding), "limit": limit, "error": str(e)}
            )
            log_exception(self.logger, error)
            self.tracer.end_trace(request_id, "failed", error=error)
            raise error
    
    def expand_graph(self, chunk_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Expand graph to retrieve connected entities for given chunk IDs.
        
        Args:
            chunk_ids: List of chunk element IDs to expand from
            
        Returns:
            List of dictionaries containing expanded graph information
            
        Raises:
            Neo4jError: If graph expansion fails
        """
        if not chunk_ids:
            return []
        
        request_id = self.tracer.start_trace("expand_graph", {
            "chunk_ids_count": len(chunk_ids)
        })
        
        try:
            self.logger.debug(f"Expanding graph for {len(chunk_ids)} chunks")
            
            # Cypher query to expand graph relationships
            query = """
            UNWIND $chunk_ids as chunk_id
            MATCH (chunk:Chunk)
            WHERE elementId(chunk) = chunk_id
            
            // Get article and author relationships
            OPTIONAL MATCH (article:Article)-[:HAS_CHUNK]->(chunk)
            OPTIONAL MATCH (author:Author)-[:WROTE]->(article)
            
            // Get related chunks from same article
            OPTIONAL MATCH (article)-[:HAS_CHUNK]->(related_chunk:Chunk)
            WHERE elementId(related_chunk) <> chunk_id
            
            // Get other articles by same author
            OPTIONAL MATCH (author)-[:WROTE]->(other_article:Article)
            WHERE elementId(other_article) <> elementId(article)
            
            RETURN DISTINCT
                elementId(chunk) as chunk_id,
                chunk.text as chunk_text,
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
            
            with self.get_session() as session:
                result = session.run(query, {"chunk_ids": chunk_ids})
                
                expanded_data = []
                for record in result:
                    # Filter out null entries from collections
                    related_chunks = [
                        chunk for chunk in record["related_chunks"] 
                        if chunk["id"] is not None
                    ]
                    other_articles = [
                        article for article in record["other_articles"]
                        if article["id"] is not None
                    ]
                    
                    expansion_data = {
                        "chunk_id": record["chunk_id"],
                        "chunk_text": record["chunk_text"],
                        "article_id": record["article_id"],
                        "article_title": record["article_title"],
                        "author_id": record["author_id"],
                        "author_name": record["author_name"],
                        "related_chunks": related_chunks,
                        "other_articles": other_articles
                    }
                    expanded_data.append(expansion_data)
                
                self.logger.debug(f"Graph expansion returned {len(expanded_data)} expanded entries")
                self.tracer.end_trace(request_id, "completed", {
                    "expanded_entries": len(expanded_data),
                    "total_related_chunks": sum(len(entry["related_chunks"]) for entry in expanded_data),
                    "total_other_articles": sum(len(entry["other_articles"]) for entry in expanded_data)
                })
                
                return expanded_data
                
        except Exception as e:
            error = Neo4jError(
                ErrorCodes.NEO4J_QUERY_FAILED,
                f"Graph expansion failed: {str(e)}",
                {"chunk_ids_count": len(chunk_ids), "error": str(e)}
            )
            log_exception(self.logger, error)
            self.tracer.end_trace(request_id, "failed", error=error)
            raise error
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Neo4j connection and indexes.
        
        Returns:
            Dictionary containing health status information
        """
        request_id = self.tracer.start_trace("health_check")
        
        try:
            health_info = {
                "connection": False,
                "database": self.database,
                "indexes": {},
                "node_counts": {},
                "timestamp": time.time()
            }
            
            with self.get_session() as session:
                # Test basic connection
                result = session.run("RETURN 1 as test")
                if result.single()["test"] == 1:
                    health_info["connection"] = True
                
                # Check vector index
                try:
                    index_result = session.run("SHOW INDEXES YIELD name, type WHERE name = 'chunk_embedding_vector'")
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
            
            self.tracer.end_trace(request_id, "completed", health_info)
            return health_info
            
        except Exception as e:
            error_info = {"error": str(e), "connection": False}
            self.tracer.end_trace(request_id, "failed", error=error_info)
            return error_info


# Global Neo4j client instance
_global_client: Optional[Neo4jClient] = None


def get_neo4j_client(uri: str = None, username: str = None, password: str = None, 
                     database: str = "neo4j") -> Neo4jClient:
    """
    Get the global Neo4j client instance.
    
    Args:
        uri: Neo4j URI (only used on first call)
        username: Neo4j username (only used on first call)
        password: Neo4j password (only used on first call)
        database: Database name (only used on first call)
        
    Returns:
        Neo4jClient instance
    """
    global _global_client
    if _global_client is None:
        if not all([uri, username, password]):
            raise Neo4jError(
                ErrorCodes.NEO4J_CONNECTION_TIMEOUT,
                "Neo4j connection parameters required for first initialization",
                {"provided": {"uri": bool(uri), "username": bool(username), "password": bool(password)}}
            )
        _global_client = Neo4jClient(uri, username, password, database)
    return _global_client


def vector_search(embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
    """
    Perform vector search using the global client.
    
    Args:
        embedding: Query embedding vector
        limit: Maximum number of results
        
    Returns:
        List of search results
    """
    client = get_neo4j_client()
    return client.vector_search(embedding, limit)


def expand_graph(chunk_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Expand graph using the global client.
    
    Args:
        chunk_ids: List of chunk IDs to expand
        
    Returns:
        List of expanded graph data
    """
    client = get_neo4j_client()
    return client.expand_graph(chunk_ids)