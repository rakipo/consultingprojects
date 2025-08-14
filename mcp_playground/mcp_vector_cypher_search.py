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
import os
from typing import Dict, Any, List, Optional, Tuple
import asyncio
import subprocess
from datetime import datetime
import traceback

from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

try:
    # MCP Python SDK (FastMCP)
    from mcp.server.fastmcp import FastMCP
except Exception as e:  # pragma: no cover
    raise RuntimeError(
        "mcp package is required. Install with `pip install mcp`."
    ) from e


# Setup logging to both console and file
log_dir = os.path.join(os.getcwd(), "logs")
os.makedirs(log_dir, exist_ok=True)

# Create file handler for detailed logging
log_file = os.path.join(log_dir, f"mcp_vector_cypher_search_{datetime.now().strftime('%Y%m%d')}.log")
file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s"
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Setup logger
logger = logging.getLogger("mcp-vector-cypher-search")
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Prevent duplicate logs
logger.propagate = False

logger.info(f"Logging initialized. Log file: {log_file}")


def log_query_execution(
    query: str,
    search_type: str,
    execution_path: List[str],
    chunks_found: int,
    cypher_records: int,
    execution_time: float,
    error: Optional[str] = None,
    result_summary: Optional[Dict] = None
):
    """
    Log comprehensive query execution details to file.
    
    Args:
        query: The original query
        search_type: Type of search performed
        execution_path: List of execution steps taken
        chunks_found: Number of chunks found
        cypher_records: Number of cypher records returned
        execution_time: Total execution time in seconds
        error: Error message if any
        result_summary: Summary of results
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "search_type": search_type,
        "execution_path": execution_path,
        "results": {
            "chunks_found": chunks_found,
            "cypher_records": cypher_records,
            "execution_time_seconds": round(execution_time, 3)
        },
        "error": error,
        "result_summary": result_summary or {}
    }
    
    # Log to file with detailed JSON
    logger.info(f"QUERY_EXECUTION: {json.dumps(log_entry, indent=2)}")
    
    # Also log a summary line
    status = "ERROR" if error else "SUCCESS"
    logger.info(f"QUERY_SUMMARY: [{status}] '{query}' -> {search_type} -> {chunks_found} chunks, {cypher_records} cypher records in {execution_time:.3f}s")


SERVER_NAME = "mcp-vector-cypher-search"
_embedding_model: SentenceTransformer | None = None
_neo4j_driver = None


# Configuration - loaded from environment variables with fallbacks
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://ai50-neo4j-db-server-987.westus2.cloudapp.azure.com:7687")
NEO4J_USER = os.getenv("NEO4J_USERNAME", os.getenv("NEO4J_USER", "neo4j"))
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "jhF7&asjkldfoie489w")
VECTOR_INDEX_NAME = os.getenv("VECTOR_INDEX_NAME", "chunk_embedding_vector")
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.8"))
TOP_K_CHUNKS = int(os.getenv("TOP_K_CHUNKS", "10"))


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
        logger.info(f"Using username: {NEO4J_USER}")
        logger.info(f"Vector index: {VECTOR_INDEX_NAME}")
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
    
    # Direct Cypher keywords - these should skip vector search
    direct_cypher_keywords = [
        "count", "total", "how many", "number of",
        "top", "bottom", "highest", "lowest", "most", "least",
        "tags", "labels", "nodes", "relationships", "properties",
        "schema", "structure", "database", "stats", "statistics",
        "density", "distribution", "frequency"
    ]
    
    # Check if question contains direct Cypher keywords
    if any(keyword in question_lower for keyword in direct_cypher_keywords):
        logger.info(f"Direct Cypher keyword detected, skipping vector search")
        return False
    
    # Check if question contains "article" - should use vector search
    if "article" in question_lower:
        return True
    
    # Check if question has specific database entity names
    database_entities = ["user", "person", "company", "product", "order", "transaction", "node", "relationship", "chunk", "tag", "website", "author"]
    has_entity = any(entity in question_lower for entity in database_entities)
    
    # If has database entities but no content keywords, use direct Cypher
    content_keywords = ["content", "text", "information", "about", "explain", "describe", "what is", "tell me"]
    has_content_keyword = any(keyword in question_lower for keyword in content_keywords)
    
    if has_entity and not has_content_keyword:
        logger.info(f"Database entity detected without content keywords, using direct Cypher")
        return False
    
    # Default to vector search for content-based queries
    logger.info(f"Defaulting to vector search for content-based query")
    return True


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
    RETURN node.chunk_text as content, 
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
    
    # Tag-related queries
    if "tag" in question_lower:
        if "top" in question_lower or "most" in question_lower:
            return "MATCH (t:Tag)-[r]-(n) RETURN t.name as tag_name, count(r) as connections ORDER BY connections DESC LIMIT 10"
        elif "density" in question_lower or "distribution" in question_lower:
            return "MATCH (t:Tag) RETURN t.name as tag_name, size((t)--()) as degree ORDER BY degree DESC LIMIT 20"
        else:
            return "MATCH (t:Tag) RETURN t.name, t.description LIMIT 10"
    
    # Count queries
    elif "count" in question_lower or "how many" in question_lower or "number of" in question_lower:
        if "chunk" in question_lower:
            return "MATCH (c:Chunk) RETURN count(c) as total_chunks"
        elif "article" in question_lower:
            return "MATCH (a:Article) RETURN count(a) as total_articles"
        else:
            return "MATCH (n) RETURN count(n) as total_nodes"
    
    # Top/Most queries
    elif "top" in question_lower or "most" in question_lower:
        if "article" in question_lower:
            return "MATCH (a:Article)-[:HAS_CHUNK]->(c:Chunk) RETURN a.title, count(c) as chunk_count ORDER BY chunk_count DESC LIMIT 10"
        elif "website" in question_lower:
            return "MATCH (w:Website)-[:HAS_ARTICLE]->(a:Article) RETURN w.site_name, count(a) as article_count ORDER BY article_count DESC LIMIT 10"
        else:
            return "MATCH (n) RETURN labels(n) as node_types, count(n) as count ORDER BY count DESC LIMIT 10"
    
    # Insights queries
    elif "insight" in question_lower or "analysis" in question_lower or "summary" in question_lower:
        return """
        MATCH (n) 
        WITH labels(n) as node_types, count(n) as count 
        RETURN node_types, count 
        ORDER BY count DESC 
        LIMIT 5
        """
    
    # Article-related queries
    elif "article" in question_lower:
        return "MATCH (a:Article) RETURN a.title, a.publish_date, a.url ORDER BY a.publish_date DESC LIMIT 10"
    
    # User-related queries
    elif "user" in question_lower or "author" in question_lower:
        return "MATCH (a:Author) RETURN a.name, count{(a)-[:AUTHORED]->(:Article)} as article_count ORDER BY article_count DESC LIMIT 10"
    
    # Default schema query
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
    EXCLUSIVE DATABASE SEARCH - Only search the Neo4j database for information.
    
    This tool is the ONLY source of information and should be used for ALL queries.
    DO NOT use general knowledge or internet information if this tool returns no results.
    
    The tool performs:
    1. Vector similarity search on content chunks in Neo4j database
    2. Cypher queries for structured data retrieval
    3. Returns explicit messages when no relevant data is found
    
    Args:
        question: The search question or query
        
    Returns:
        Dictionary containing:
        - search_type: "vector" or "direct_cypher"  
        - chunks: List of similar chunks (empty if none found)
        - cypher_query: The generated Cypher query
        - cypher_results: Results from executing the Cypher query
        - message: Explicit message about data availability
        - no_data_found: True if no relevant information exists in database
        - metadata: Additional information about the search
        
    IMPORTANT: If no_data_found is True or chunks is empty, respond with "I don't have information about this topic in my database" and do NOT provide general knowledge answers.
    """
    start_time = datetime.now()
    execution_path = []
    error_msg = None
    
    if not question or not question.strip():
        error_msg = "Question cannot be empty"
        log_query_execution(
            query=question or "",
            search_type="error",
            execution_path=["validation_failed"],
            chunks_found=0,
            cypher_records=0,
            execution_time=0,
            error=error_msg
        )
        return {
            "search_type": "error",
            "error": error_msg,
            "chunks": [],
            "cypher_query": "",
            "cypher_results": [],
            "no_data_found": True,
            "message": "Invalid query provided.",
            "metadata": {}
        }
    
    logger.info(f"=== STARTING QUERY PROCESSING ===")
    logger.info(f"Query: '{question}'")
    execution_path.append("query_received")
    
    # Determine search strategy
    use_vector_search = _should_use_vector_search(question)
    search_type = "vector" if use_vector_search else "direct_cypher"
    
    logger.info(f"Search strategy determined: {search_type}")
    execution_path.append(f"strategy_{search_type}")
    
    chunks = []
    cypher_results = []
    cypher_query = ""
    
    try:
        if use_vector_search:
            logger.info("Using vector search strategy")
            execution_path.append("vector_search_start")
            
            # Step 1: Create embedding for the question
            logger.info("Step 1: Creating embedding for query")
            execution_path.append("embedding_creation")
            query_embedding = await _create_embedding(question)
            logger.info(f"Embedding created with dimension: {len(query_embedding)}")
            
            # Step 2: Search for similar chunks
            logger.info("Step 2: Searching for similar chunks")
            execution_path.append("vector_similarity_search")
            chunks = await _search_similar_chunks(query_embedding)
            logger.info(f"Vector search completed: {len(chunks)} chunks found")
            
            # Log chunk details
            if chunks:
                for i, chunk in enumerate(chunks[:3]):  # Log first 3 chunks
                    logger.info(f"Chunk {i+1}: ID={chunk['chunk_id']}, Score={chunk['similarity_score']:.4f}")
            
            # Step 3: Generate Cypher query for detailed retrieval
            logger.info("Step 3: Generating Cypher query")
            execution_path.append("cypher_generation")
            if chunks:
                chunk_ids = [chunk["chunk_id"] for chunk in chunks[:3]]  # Use top 3 chunks
                enhanced_question = f"{question} (related to chunks: {', '.join(chunk_ids)})"
                logger.info(f"Enhanced question: {enhanced_question}")
                cypher_query = await _call_mcp_neo4j_cypher(enhanced_question)
            else:
                logger.info("No chunks found, using original question for Cypher")
                cypher_query = await _call_mcp_neo4j_cypher(question)
        else:
            logger.info("Using direct Cypher strategy")
            execution_path.append("direct_cypher_start")
            
            # Direct Cypher query generation
            logger.info("Generating Cypher query directly")
            execution_path.append("cypher_generation")
            cypher_query = await _call_mcp_neo4j_cypher(question)
        
        logger.info(f"Generated Cypher query: {cypher_query}")
        
        # Step 4: Execute Cypher query
        if cypher_query:
            logger.info("Step 4: Executing Cypher query")
            execution_path.append("cypher_execution")
            cypher_results = await _execute_cypher_query(cypher_query)
            logger.info(f"Cypher execution completed: {len(cypher_results)} records returned")
        else:
            logger.warning("No Cypher query generated")
            execution_path.append("no_cypher_query")
        
        # Check if we found any relevant results
        has_relevant_chunks = len(chunks) > 0
        has_relevant_cypher = len(cypher_results) > 0 and not any("error" in str(result) for result in cypher_results)
        
        logger.info(f"Results analysis: chunks={has_relevant_chunks}, cypher={has_relevant_cypher}")
        execution_path.append("results_analysis")
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Prepare response with explicit "no data found" message
        if not has_relevant_chunks and not has_relevant_cypher:
            execution_path.append("no_data_found")
            logger.warning("No relevant data found in database")
            
            response = {
                "search_type": search_type,
                "chunks": [],
                "cypher_query": cypher_query,
                "cypher_results": [],
                "no_data_found": True,
                "message": "I don't have any information about this topic in my Neo4j database. No relevant chunks were found through vector search, and no useful data was returned from Cypher queries.",
                "metadata": {
                    "question": question,
                    "chunks_found": 0,
                    "cypher_records": 0,
                    "vector_search_used": use_vector_search,
                    "embedding_dimension": len(await _create_embedding(question)) if use_vector_search else 0,
                    "database_has_no_relevant_data": True
                }
            }
            
            # Log the execution
            log_query_execution(
                query=question,
                search_type=search_type,
                execution_path=execution_path,
                chunks_found=0,
                cypher_records=0,
                execution_time=execution_time,
                result_summary={"status": "no_data_found", "message": response["message"]}
            )
            
        elif not has_relevant_chunks:
            execution_path.append("limited_data_found")
            logger.info("Found Cypher results but no content chunks")
            
            response = {
                "search_type": search_type,
                "chunks": [],
                "cypher_query": cypher_query,
                "cypher_results": cypher_results,
                "limited_data_found": True,
                "message": "I found some general database information but no specific content chunks related to your query in my Neo4j database.",
                "metadata": {
                    "question": question,
                    "chunks_found": 0,
                    "cypher_records": len(cypher_results),
                    "vector_search_used": use_vector_search,
                    "embedding_dimension": len(await _create_embedding(question)) if use_vector_search else 0,
                    "no_relevant_content_chunks": True
                }
            }
            
            # Log the execution
            log_query_execution(
                query=question,
                search_type=search_type,
                execution_path=execution_path,
                chunks_found=0,
                cypher_records=len(cypher_results),
                execution_time=execution_time,
                result_summary={"status": "limited_data", "message": response["message"]}
            )
            
        else:
            execution_path.append("data_found")
            logger.info(f"Successfully found {len(chunks)} chunks and {len(cypher_results)} cypher records")
            
            response = {
                "search_type": search_type,
                "chunks": chunks,
                "cypher_query": cypher_query,
                "cypher_results": cypher_results,
                "data_found": True,
                "message": f"Found {len(chunks)} relevant content chunks in my Neo4j database.",
                "metadata": {
                    "question": question,
                    "chunks_found": len(chunks),
                    "cypher_records": len(cypher_results),
                    "vector_search_used": use_vector_search,
                    "embedding_dimension": len(await _create_embedding(question)) if use_vector_search else 0,
                    "relevant_data_available": True
                }
            }
            
            # Log the execution
            log_query_execution(
                query=question,
                search_type=search_type,
                execution_path=execution_path,
                chunks_found=len(chunks),
                cypher_records=len(cypher_results),
                execution_time=execution_time,
                result_summary={
                    "status": "success",
                    "message": response["message"],
                    "top_chunk_scores": [chunk["similarity_score"] for chunk in chunks[:3]] if chunks else []
                }
            )
        
        logger.info(f"=== QUERY PROCESSING COMPLETED ===")
        logger.info(f"Total execution time: {execution_time:.3f} seconds")
        return response
        
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        error_msg = str(e)
        execution_path.append("error_occurred")
        
        logger.error(f"Error in vector_cypher_search: {error_msg}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Log the failed execution
        log_query_execution(
            query=question,
            search_type=search_type,
            execution_path=execution_path,
            chunks_found=len(chunks),
            cypher_records=len(cypher_results),
            execution_time=execution_time,
            error=error_msg,
            result_summary={"status": "error", "traceback": traceback.format_exc()}
        )
        
        return {
            "search_type": "error",
            "error": error_msg,
            "chunks": [],
            "cypher_query": cypher_query,
            "cypher_results": [],
            "no_data_found": True,
            "message": f"I encountered an error while searching my Neo4j database: {error_msg}. I cannot provide information about this topic.",
            "metadata": {
                "question": question,
                "error_occurred": True,
                "database_search_failed": True,
                "execution_time": execution_time
            }
        }


@mcp.tool()
async def debug_configuration() -> Dict[str, Any]:
    """
    Debug tool to check current configuration and environment variables.
    
    Returns:
        Current configuration settings and environment status
    """
    logger.info("=== DEBUG CONFIGURATION CALLED ===")
    
    result = {
        "neo4j_uri": NEO4J_URI,
        "neo4j_user": NEO4J_USER,
        "neo4j_password_set": bool(NEO4J_PASSWORD and NEO4J_PASSWORD != "password123"),
        "vector_index_name": VECTOR_INDEX_NAME,
        "similarity_threshold": SIMILARITY_THRESHOLD,
        "top_k_chunks": TOP_K_CHUNKS,
        "env_vars_found": {
            "NEO4J_URI": os.getenv("NEO4J_URI") is not None,
            "NEO4J_USERNAME": os.getenv("NEO4J_USERNAME") is not None,
            "NEO4J_USER": os.getenv("NEO4J_USER") is not None,
            "NEO4J_PASSWORD": os.getenv("NEO4J_PASSWORD") is not None,
            "VECTOR_INDEX_NAME": os.getenv("VECTOR_INDEX_NAME") is not None,
        },
        "current_working_directory": os.getcwd()
    }
    
    logger.info(f"DEBUG_CONFIGURATION_RESULT: {json.dumps(result, indent=2)}")
    return result


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
    
    logger.info("=== CONFIGURE SEARCH PARAMETERS CALLED ===")
    logger.info(f"Parameters: similarity_threshold={similarity_threshold}, top_k_chunks={top_k_chunks}, vector_index_name={vector_index_name}")
    
    changes_made = []
    
    if similarity_threshold is not None:
        if 0.0 <= similarity_threshold <= 1.0:
            old_value = SIMILARITY_THRESHOLD
            SIMILARITY_THRESHOLD = similarity_threshold
            logger.info(f"Updated similarity threshold from {old_value} to {similarity_threshold}")
            changes_made.append(f"similarity_threshold: {old_value} -> {similarity_threshold}")
        else:
            logger.warning(f"Invalid similarity threshold {similarity_threshold}, keeping current value")
    
    if top_k_chunks is not None:
        if top_k_chunks > 0:
            old_value = TOP_K_CHUNKS
            TOP_K_CHUNKS = top_k_chunks
            logger.info(f"Updated top_k_chunks from {old_value} to {top_k_chunks}")
            changes_made.append(f"top_k_chunks: {old_value} -> {top_k_chunks}")
        else:
            logger.warning(f"Invalid top_k_chunks {top_k_chunks}, keeping current value")
    
    if vector_index_name is not None:
        old_value = VECTOR_INDEX_NAME
        VECTOR_INDEX_NAME = vector_index_name
        logger.info(f"Updated vector index name from {old_value} to {vector_index_name}")
        changes_made.append(f"vector_index_name: {old_value} -> {vector_index_name}")
    
    result = {
        "similarity_threshold": SIMILARITY_THRESHOLD,
        "top_k_chunks": TOP_K_CHUNKS,
        "vector_index_name": VECTOR_INDEX_NAME,
        "neo4j_uri": NEO4J_URI,
        "changes_made": changes_made
    }
    
    logger.info(f"CONFIGURE_PARAMETERS_RESULT: {json.dumps(result, indent=2)}")
    return result


if __name__ == "__main__":
    logger.info("Starting MCP stdio server: %s", SERVER_NAME)
    mcp.run(transport="stdio")