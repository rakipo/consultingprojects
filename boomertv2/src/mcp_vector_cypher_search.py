#!/usr/bin/env python3
"""
mcp-vector-cypher-search
A custom MCP server that combines vector similarity search with Cypher query generation.

This server:
1. Analyzes questions to determine if they need vector search (contains "Article" or no label)
2. Generates embeddings for vector search queries
3. Searches Neo4j for similar chunks using vector similarity
4. Generates Cypher queries for detailed data retrieval
5. Returns both chunk results and Cypher query results separately

This server communicates over stdio per the Model Context Protocol (MCP).
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional, Tuple
import asyncio
import subprocess

from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase

try:
    # MCP Python SDK (FastMCP)
    from mcp.server.fastmcp import FastMCP
except Exception as e:  # pragma: no cover
    raise RuntimeError(
        "mcp package is required. Install with `pip install mcp`."
    ) from e


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s",
)
logger = logging.getLogger("mcp-vector-cypher-search")


SERVER_NAME = "mcp-vector-cypher-search"
_embedding_model: SentenceTransformer | None = None
_neo4j_driver = None


# Configuration - these should be loaded from environment or config
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password123"
VECTOR_INDEX_NAME = "chunk_embeddings"
SIMILARITY_THRESHOLD = 0.8
TOP_K_CHUNKS = 5


def _get_embedding_model() -> SentenceTransformer:
    """Get or initialize the embedding model."""
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading SentenceTransformer model: all-MiniLM-L6-v2")
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("SentenceTransformer model loaded")
    return _embedding_model


def _get_neo4j_driver():
    """Get or initialize Neo4j driver."""
    global _neo4j_driver
    if _neo4j_driver is None:
        logger.info(f"Connecting to Neo4j at {NEO4J_URI}")
        _neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        logger.info("Neo4j driver initialized")
    return _neo4j_driver


def _should_use_vector_search(question: str) -> bool:
    """
    Determine if the question should use vector search.
    
    Args:
        question: The input question
        
    Returns:
        True if should use vector search, False otherwise
    """
    question_lower = question.lower()
    
    # Check if question contains "article"
    if "article" in question_lower:
        return True
    
    # Check if question has no specific label names
    # This is a simple heuristic - you might want to make this more sophisticated
    common_labels = ["user", "person", "company", "product", "order", "transaction", "node", "relationship"]
    has_label = any(label in question_lower for label in common_labels)
    
    # If no common labels found, assume it's a content/article search
    if not has_label:
        return True
    
    return False


async def _create_embedding(text: str) -> List[float]:
    """Create embedding for the given text."""
    if not text or not text.strip():
        return []
    
    model = _get_embedding_model()
    embedding = model.encode([text], convert_to_tensor=False)[0]
    
    if hasattr(embedding, "tolist"):
        return embedding.tolist()
    else:
        return list(embedding)


async def _search_similar_chunks(query_embedding: List[float], top_k: int = TOP_K_CHUNKS) -> List[Dict[str, Any]]:
    """
    Search for similar chunks in Neo4j using vector similarity.
    
    Args:
        query_embedding: The query embedding vector
        top_k: Number of top similar chunks to return
        
    Returns:
        List of similar chunks with their content and metadata
    """
    if not query_embedding:
        return []
    
    driver = _get_neo4j_driver()
    
    # Vector similarity search query
    cypher_query = f"""
    CALL db.index.vector.queryNodes('{VECTOR_INDEX_NAME}', $top_k, $query_vector)
    YIELD node, score
    WHERE score >= $threshold
    RETURN node.content as content, 
           node.chunk_id as chunk_id,
           node.source_id as source_id,
           node.title as title,
           node.url as url,
           score
    ORDER BY score DESC
    """
    
    try:
        with driver.session() as session:
            result = session.run(
                cypher_query,
                query_vector=query_embedding,
                top_k=top_k,
                threshold=SIMILARITY_THRESHOLD
            )
            
            chunks = []
            for record in result:
                chunks.append({
                    "content": record["content"],
                    "chunk_id": record["chunk_id"],
                    "source_id": record["source_id"],
                    "title": record["title"],
                    "url": record["url"],
                    "similarity_score": record["score"]
                })
            
            logger.info(f"Found {len(chunks)} similar chunks")
            return chunks
            
    except Exception as e:
        logger.error(f"Error searching similar chunks: {e}")
        return []


async def _call_mcp_neo4j_cypher(question: str) -> str:
    """
    Call the external mcp-neo4j-cypher service to generate Cypher query.
    
    Args:
        question: The question to convert to Cypher
        
    Returns:
        Generated Cypher query
    """
    try:
        # This would call the actual mcp-neo4j-cypher service
        # For now, we'll simulate it with a basic implementation
        logger.info("Calling mcp-neo4j-cypher service")
        
        # In a real implementation, this would use MCP client to call the service
        # For now, we'll generate a basic query
        cypher_query = _generate_basic_cypher(question)
        
        logger.info("mcp-neo4j-cypher service completed")
        return cypher_query
        
    except Exception as e:
        logger.error(f"Error calling mcp-neo4j-cypher: {e}")
        return f"// Error generating Cypher query: {e}"


def _generate_basic_cypher(question: str) -> str:
    """
    Generate a basic Cypher query based on the question.
    This is a fallback implementation.
    """
    question_lower = question.lower()
    
    if "count" in question_lower:
        return "MATCH (n) RETURN count(n) as total_nodes"
    elif "article" in question_lower or "content" in question_lower:
        return "MATCH (n:Article) RETURN n.title, n.content, n.url LIMIT 10"
    elif "user" in question_lower:
        return "MATCH (n:User) RETURN n.name, n.email LIMIT 10"
    else:
        return "MATCH (n) RETURN labels(n) as node_types, count(n) as count ORDER BY count DESC LIMIT 10"


async def _execute_cypher_query(cypher_query: str) -> List[Dict[str, Any]]:
    """
    Execute the Cypher query against Neo4j.
    
    Args:
        cypher_query: The Cypher query to execute
        
    Returns:
        Query results as list of dictionaries
    """
    if not cypher_query or cypher_query.startswith("//"):
        return []
    
    driver = _get_neo4j_driver()
    
    try:
        with driver.session() as session:
            result = session.run(cypher_query)
            
            records = []
            for record in result:
                records.append(dict(record))
            
            logger.info(f"Cypher query returned {len(records)} records")
            return records
            
    except Exception as e:
        logger.error(f"Error executing Cypher query: {e}")
        return [{"error": f"Query execution failed: {e}"}]


mcp = FastMCP(SERVER_NAME)


@mcp.tool()
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
    use_vector_search = _should_use_vector_search(question)
    search_type = "vector" if use_vector_search else "direct_cypher"
    
    chunks = []
    cypher_results = []
    cypher_query = ""
    
    try:
        if use_vector_search:
            logger.info("Using vector search strategy")
            
            # Step 1: Create embedding for the question
            query_embedding = await _create_embedding(question)
            
            # Step 2: Search for similar chunks
            chunks = await _search_similar_chunks(query_embedding)
            
            # Step 3: Generate Cypher query for detailed retrieval
            # Modify question to be more specific based on found chunks
            if chunks:
                chunk_ids = [chunk["chunk_id"] for chunk in chunks[:3]]  # Use top 3 chunks
                enhanced_question = f"{question} (related to chunks: {', '.join(chunk_ids)})"
                cypher_query = await _call_mcp_neo4j_cypher(enhanced_question)
            else:
                cypher_query = await _call_mcp_neo4j_cypher(question)
        else:
            logger.info("Using direct Cypher strategy")
            
            # Direct Cypher query generation
            cypher_query = await _call_mcp_neo4j_cypher(question)
        
        # Step 4: Execute Cypher query
        if cypher_query:
            cypher_results = await _execute_cypher_query(cypher_query)
        
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
                "embedding_dimension": len(await _create_embedding(question)) if use_vector_search else 0
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


@mcp.tool()
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
    global SIMILARITY_THRESHOLD, TOP_K_CHUNKS, VECTOR_INDEX_NAME
    
    if similarity_threshold is not None:
        if 0.0 <= similarity_threshold <= 1.0:
            SIMILARITY_THRESHOLD = similarity_threshold
            logger.info(f"Updated similarity threshold to {similarity_threshold}")
        else:
            logger.warning(f"Invalid similarity threshold {similarity_threshold}, keeping current value")
    
    if top_k_chunks is not None:
        if top_k_chunks > 0:
            TOP_K_CHUNKS = top_k_chunks
            logger.info(f"Updated top_k_chunks to {top_k_chunks}")
        else:
            logger.warning(f"Invalid top_k_chunks {top_k_chunks}, keeping current value")
    
    if vector_index_name is not None:
        VECTOR_INDEX_NAME = vector_index_name
        logger.info(f"Updated vector index name to {vector_index_name}")
    
    return {
        "similarity_threshold": SIMILARITY_THRESHOLD,
        "top_k_chunks": TOP_K_CHUNKS,
        "vector_index_name": VECTOR_INDEX_NAME,
        "neo4j_uri": NEO4J_URI
    }


if __name__ == "__main__":
    logger.info("Starting MCP stdio server: %s", SERVER_NAME)
    mcp.run(transport="stdio")