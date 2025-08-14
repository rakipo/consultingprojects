#!/usr/bin/env python3
"""
Batch Neo4j Data Loader
A program that loads data into Neo4j in configurable batches to handle large datasets efficiently.

Usage:
    python src/batch_loader.py config/config_boomer_model_userdefined.yml
"""

import sys
import logging
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import argparse
from pathlib import Path
from neo4j import GraphDatabase
import openai
from sentence_transformers import SentenceTransformer
import psycopg2
import yaml

# Import the parent classes
try:
    from .postgres_query_runner import (
        PostgresQueryRunner, 
        ErrorCodes as BaseErrorCodes,
        load_config,
        parse_postgres_config,
        get_query_from_config
    )
    from .neo4j_data_loader import Neo4jDataLoader
except ImportError:
    # Fallback for direct execution
    from postgres_query_runner import (
        PostgresQueryRunner, 
        ErrorCodes as BaseErrorCodes,
        load_config,
        parse_postgres_config,
        get_query_from_config
    )
    from neo4j_data_loader import Neo4jDataLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

# Extended error codes for batch loading
class BatchLoaderErrorCodes:
    BATCH_CONFIG_ERROR = "ERR_B001"
    BATCH_PROCESSING_ERROR = "ERR_B002"
    STATUS_UPDATE_ERROR = "ERR_B003"
    BATCH_SIZE_ERROR = "ERR_B004"


class BatchNeo4jLoader(Neo4jDataLoader):
    """
    Batch Neo4j Data Loader that extends Neo4jDataLoader for batch processing.
    
    This class processes data in configurable batches and updates the status_neo4j
    field after each successful batch to track progress.
    """
    
    def __init__(self):
        """Initialize the Batch Neo4j Data Loader."""
        super().__init__()
        self.batch_size = 10  # Default batch size
        self.batch_metrics = {
            "total_batches": 0,
            "completed_batches": 0,
            "failed_batches": 0,
            "total_records_processed": 0,
            "batch_errors": []
        }
        logger.info("Batch Neo4j Data Loader initialized")
    
    def get_batch_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get batch configuration from config file.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Dictionary containing batch configuration
        """
        batch_config = config.get('batch_config', {})
        self.batch_size = batch_config.get('batch_size', 10)
        logger.info(f"Batch size configured: {self.batch_size}")
        return batch_config
    
    def initialize_neo4j_connection(self, config: Dict[str, Any]) -> None:
        """
        Initialize Neo4j connection from configuration.
        
        Args:
            config: Configuration dictionary
        """
        try:
            if 'database' not in config or 'neo4j' not in config['database']:
                raise Exception(f"{BaseErrorCodes.MISSING_DB_CONFIG}: Neo4j configuration not found in config file")
            
            # Parse Neo4j configuration
            neo4j_config_str = config['database']['neo4j']
            neo4j_config = {}
            
            for line in neo4j_config_str.strip().split('\n'):
                line = line.strip()
                if line and ':' in line:
                    key, value = line.split(':', 1)
                    neo4j_config[key.strip()] = value.strip()
            
            # Create Neo4j driver
            uri = f"neo4j://{neo4j_config['host']}:{neo4j_config['port']}"
            self.neo4j_driver = GraphDatabase.driver(
                uri, 
                auth=(neo4j_config['user'], neo4j_config['password'])
            )
            
            # Test connection
            with self.neo4j_driver.session() as session:
                session.run("RETURN 1")
            
            logger.info(f"Neo4j connection established: {neo4j_config['host']}:{neo4j_config['port']}")
            
        except Exception as e:
            error_msg = f"{Neo4jLoaderErrorCodes.NEO4J_CONNECTION_ERROR}: Failed to initialize Neo4j connection: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    def initialize_embedding_model(self) -> None:
        """Initialize the sentence transformer model for embeddings."""
        logger.info("Initializing embedding model")
        
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Embedding model initialized successfully")
        except Exception as e:
            error_msg = f"{Neo4jLoaderErrorCodes.EMBEDDING_ERROR}: Failed to initialize embedding model: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    def chunk_text_content(self, text: str, chunk_size: int = 512, overlap: int = 50, use_llm: bool = True) -> List[Dict[str, Any]]:
        """
        Chunk text content for vector embeddings using LLM-based intelligent chunking.
        
        Args:
            text: Text content to chunk
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks
            use_llm: Whether to use LLM for intelligent chunking
            
        Returns:
            List of chunk dictionaries with chunk_id, chunk_text, and position
        """
        try:
            if text is None:
                raise ValueError("Text cannot be None")
            
            logger.info(f"Chunking text content of length {len(text)} using {'LLM-based' if use_llm else 'simple'} chunking")
            if not text or len(text.strip()) == 0:
                return []
            
            if use_llm and len(text) > 1000:  # Use LLM for longer texts
                chunks = self._chunk_with_llm(text, chunk_size)
            else:
                chunks = self._chunk_simple(text, chunk_size, overlap)
            
            logger.info(f"Created {len(chunks)} chunks from text")
            return chunks
            
        except Exception as e:
            error_msg = f"{Neo4jLoaderErrorCodes.CHUNKING_ERROR}: Error chunking text: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    def _chunk_with_llm(self, text: str, target_chunk_size: int) -> List[Dict[str, Any]]:
        """
        Use LLM for intelligent text chunking.
        
        Args:
            text: Text to chunk
            target_chunk_size: Target size for each chunk
            
        Returns:
            List of chunk dictionaries
        """
        logger.info("Using LLM-based intelligent text chunking")
        
        try:
            # Check if OpenAI API key is available
            if not os.getenv('OPENAI_API_KEY'):
                logger.warning("OPENAI_API_KEY environment variable not set, falling back to simple chunking")
                return self._chunk_simple(text, target_chunk_size, target_chunk_size // 10)
            
            # Use OpenAI for intelligent chunking
            import openai
            
            prompt = f"""
            Please split the following text into chunks of approximately {target_chunk_size} characters each. 
            Each chunk should be semantically meaningful and complete. Return only the chunks, one per line.
            
            Text to chunk:
            {text}
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=0.1
            )
            
            chunks_text = response.choices[0].message.content.strip()
            chunk_lines = [line.strip() for line in chunks_text.split('\n') if line.strip()]
            
            chunks = []
            for i, chunk_text in enumerate(chunk_lines):
                chunk = {
                    'chunk_id': f"chunk_{uuid.uuid4().hex[:8]}",
                    'chunk_text': chunk_text,
                    'chunk_position': i,
                    'chunk_order': i
                }
                chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            logger.warning(f"LLM chunking failed: {str(e)}, falling back to simple chunking")
            return self._chunk_simple(text, target_chunk_size, target_chunk_size // 10)
    
    def _chunk_simple(self, text: str, chunk_size: int, overlap: int) -> List[Dict[str, Any]]:
        """
        Simple text chunking by character count.
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk
            overlap: Overlap between chunks
            
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            
            chunk = {
                'chunk_id': f"chunk_{uuid.uuid4().hex[:8]}",
                'chunk_text': chunk_text,
                'chunk_position': len(chunks),
                'chunk_order': len(chunks)
            }
            chunks.append(chunk)
            
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def _record_cypher(self, category: str, name: str, cypher: str) -> None:
        """Record cypher usage for metrics."""
        key = (category, name, cypher)
        self.cypher_usage[key] = self.cypher_usage.get(key, 0) + 1
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings
            
        Returns:
            List of embedding vectors
        """
        logger.info(f"Generating embeddings for {len(texts)} texts")
        
        try:
            if not self.embedding_model:
                self.initialize_embedding_model()
            
            # Generate embeddings in batches
            embeddings = []
            batch_size = 32
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_embeddings = self.embedding_model.encode(batch_texts, show_progress_bar=True)
                embeddings.extend(batch_embeddings.tolist())
            
            self.load_metrics["embeddings_generated"] += len(embeddings)
            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            error_msg = f"{Neo4jLoaderErrorCodes.EMBEDDING_ERROR}: Error generating embeddings: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    def execute_cypher_query(self, cypher: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a Cypher query on Neo4j.
        
        Args:
            cypher: Cypher query string
            parameters: Query parameters
            
        Returns:
            Query result
        """
        if not self.neo4j_driver:
            raise Exception("Neo4j connection not established")
        
        try:
            with self.neo4j_driver.session() as session:
                result = session.run(cypher, parameters or {})
                records = [dict(record) for record in result]
                return {"records": records, "summary": result.consume()}
        except Exception as e:
            error_msg = f"{Neo4jLoaderErrorCodes.NEO4J_EXECUTION_ERROR}: Cypher execution failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    def process_vector_embeddings(self, data_records: List[Dict[str, Any]], model: Dict[str, Any], config: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Process vector embeddings for data records.
        
        Args:
            data_records: List of data records from PostgreSQL
            model: Neo4j model configuration
            
        Returns:
            List of chunk records with embeddings
        """
        logger.info("Processing vector embeddings")
        
        try:
            chunk_records = []
            
            # Find vector properties and chunking configuration in the model
            vector_properties = []
            content_property = None
            chunking_node = None
            
            for node in model.get('nodes', []):
                # Check if this node has chunking enabled
                if node.get('chunking_enabled', False):
                    chunking_node = node
                    content_property = node.get('source_content_field')
                    logger.info(f"Found chunking node: {node.get('label')} with source field: {content_property}")
                
                # Find vector properties
                for prop in node.get('properties', []):
                    if prop.get('type') == 'vector':
                        vector_properties.append(prop)
            
            # If no chunking node found, look for content fields in data
            if not content_property and data_records:
                sample_record = data_records[0]
                for field_name in ['content', 'text', 'description', 'summary', 'meta_description']:
                    if field_name in sample_record and sample_record[field_name]:
                        content_property = field_name
                        logger.info(f"Using field '{field_name}' as content source")
                        break
            
            if not vector_properties or not content_property:
                logger.info(f"No vector properties ({len(vector_properties)}) or content property ({content_property}) found, skipping embedding processing")
                return []
            
            # Process each record
            for record in data_records:
                content_text = record.get(content_property, '')
                if content_text and len(content_text.strip()) > 0:
                    # Get chunking configuration
                    chunk_size = 512
                    chunk_overlap = 50
                    use_llm_chunking = True
                    
                    if config:
                        chunking_config = config.get('chunking_config', {})
                        chunk_size = chunking_config.get('default_chunk_size', 512)
                        chunk_overlap = chunking_config.get('default_chunk_overlap', 50)
                        use_llm_chunking = chunking_config.get('use_llm_chunking', True)
                    
                    # Chunk the content
                    chunks = self.chunk_text_content(content_text, chunk_size, chunk_overlap, use_llm_chunking)
                    
                    if chunks:
                        # Generate embeddings for chunks
                        chunk_texts = [chunk['chunk_text'] for chunk in chunks]
                        embeddings = self.generate_embeddings(chunk_texts)
                        
                        # Create chunk records
                        for i, chunk in enumerate(chunks):
                            chunk_record = {
                                'chunk_id': chunk['chunk_id'],
                                'chunk_text': chunk['chunk_text'],
                                'chunk_position': chunk['chunk_position'],
                                'chunk_order': chunk['chunk_order'],
                                'embedding': embeddings[i],
                                'content_id': record.get('id'),  # Link back to original content
                                'source_record': record
                            }
                            chunk_records.append(chunk_record)
                            
                        self.load_metrics["chunks_created"] += len(chunks)
            
            logger.info(f"Processed {len(chunk_records)} chunk records with embeddings")
            return chunk_records
            
        except Exception as e:
            error_msg = f"{Neo4jLoaderErrorCodes.EMBEDDING_ERROR}: Error processing vector embeddings: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    def load_nodes_to_neo4j(self, data_records: List[Dict[str, Any]], model: Dict[str, Any]) -> None:
        """
        Load nodes to Neo4j based on model configuration.
        
        Args:
            data_records: List of data records
            model: Neo4j model configuration
        """
        logger.info(f"Loading {len(data_records)} records to Neo4j nodes")
        
        try:
            for node_config in model.get('nodes', []):
                node_label = node_config.get('label')
                node_id_property = node_config.get('node_id_property')
                
                if not node_label or not node_id_property:
                    continue
                
                # Create nodes for this label
                created_count = 0
                failed_count = 0
                
                for record in data_records:
                    try:
                        # Get node ID value
                        node_id_value = record.get(node_id_property)
                        if not node_id_value:
                            continue
                        
                        # Build properties
                        properties = {}
                        for prop_config in node_config.get('properties', []):
                            prop_name = prop_config.get('name')
                            if prop_name in record:
                                properties[prop_name] = record[prop_name]
                        
                        # Create node
                        cypher = f"""
                        MERGE (n:{node_label} {{{node_id_property}: $id}})
                        SET n += $properties
                        """
                        
                        self.execute_cypher_query(cypher, {
                            'id': node_id_value,
                            'properties': properties
                        })
                        
                        created_count += 1
                        
                    except Exception as e:
                        failed_count += 1
                        logger.warning(f"Failed to create {node_label} node: {str(e)}")
                
                # Update metrics (accumulate instead of overwrite)
                if node_label not in self.load_metrics["nodes_created"]:
                    self.load_metrics["nodes_created"][node_label] = 0
                self.load_metrics["nodes_created"][node_label] += created_count
                if failed_count > 0:
                    if node_label not in self.load_metrics["nodes_failed"]:
                        self.load_metrics["nodes_failed"][node_label] = 0
                    self.load_metrics["nodes_failed"][node_label] += failed_count
                
                logger.info(f"Created {created_count} {node_label} nodes")
                
        except Exception as e:
            error_msg = f"{Neo4jLoaderErrorCodes.NEO4J_EXECUTION_ERROR}: Error loading nodes: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    def load_relationships_to_neo4j(self, data_records: List[Dict[str, Any]], model: Dict[str, Any]) -> None:
        """
        Load relationships to Neo4j based on model configuration.
        
        Args:
            data_records: List of data records
            model: Neo4j model configuration
        """
        logger.info(f"Loading relationships for {len(data_records)} records")
        
        try:
            for rel_config in model.get('relationships', []):
                rel_type = rel_config.get('type')
                start_node = rel_config.get('start_node')
                end_node = rel_config.get('end_node')
                start_property = rel_config.get('start_property')
                end_property = rel_config.get('end_property')
                
                if not all([rel_type, start_node, end_node, start_property, end_property]):
                    continue
                
                # Skip chunk relationships as they're handled separately
                if 'Chunk' in [start_node, end_node]:
                    continue
                
                created_count = 0
                failed_count = 0
                
                for record in data_records:
                    try:
                        start_value = record.get(start_property)
                        end_value = record.get(end_property)
                        
                        if not start_value or not end_value:
                            continue
                        
                        # Create relationship
                        cypher = f"""
                        MATCH (start:{start_node} {{{start_property}: $start_value}})
                        MATCH (end:{end_node} {{{end_property}: $end_value}})
                        MERGE (start)-[r:{rel_type}]->(end)
                        """
                        
                        self.execute_cypher_query(cypher, {
                            'start_value': start_value,
                            'end_value': end_value
                        })
                        
                        created_count += 1
                        
                    except Exception as e:
                        failed_count += 1
                        logger.warning(f"Failed to create {rel_type} relationship: {str(e)}")
                
                # Update metrics (accumulate instead of overwrite)
                if rel_type not in self.load_metrics["relationships_created"]:
                    self.load_metrics["relationships_created"][rel_type] = 0
                self.load_metrics["relationships_created"][rel_type] += created_count
                if failed_count > 0:
                    if rel_type not in self.load_metrics["relationships_failed"]:
                        self.load_metrics["relationships_failed"][rel_type] = 0
                    self.load_metrics["relationships_failed"][rel_type] += failed_count
                
                logger.info(f"Created {created_count} {rel_type} relationships")
                
        except Exception as e:
            error_msg = f"{Neo4jLoaderErrorCodes.NEO4J_EXECUTION_ERROR}: Error loading relationships: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    def load_chunk_relationships(self, chunk_records: List[Dict[str, Any]]) -> None:
        """
        Load relationships between articles and chunks.
        
        Args:
            chunk_records: List of chunk records
        """
        logger.info(f"Loading chunk relationships for {len(chunk_records)} chunks")
        
        try:
            created_count = 0
            failed_count = 0
            
            for chunk_record in chunk_records:
                try:
                    article_id = chunk_record.get('content_id')
                    chunk_id = chunk_record.get('chunk_id')
                    chunk_order = chunk_record.get('chunk_order', 0)
                    
                    if not article_id or not chunk_id:
                        continue
                    
                    cypher = """
                    MATCH (start:Article {id: $article_id})
                    MATCH (end:Chunk {chunk_id: $chunk_id})
                    MERGE (start)-[r:HAS_CHUNK]->(end)
                    SET r.chunk_order = $chunk_order
                    """
                    
                    self.execute_cypher_query(cypher, {
                        'article_id': article_id,
                        'chunk_id': chunk_id,
                        'chunk_order': chunk_order
                    })
                    
                    created_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    logger.warning(f"Failed to create chunk relationship: {str(e)}")
            
            # Update metrics (accumulate instead of overwrite)
            if "HAS_CHUNK" not in self.load_metrics["relationships_created"]:
                self.load_metrics["relationships_created"]["HAS_CHUNK"] = 0
            self.load_metrics["relationships_created"]["HAS_CHUNK"] += created_count
            if failed_count > 0:
                if "HAS_CHUNK" not in self.load_metrics["relationships_failed"]:
                    self.load_metrics["relationships_failed"]["HAS_CHUNK"] = 0
                self.load_metrics["relationships_failed"]["HAS_CHUNK"] += failed_count
            
            logger.info(f"Created {created_count} chunk relationships")
            
        except Exception as e:
            error_msg = f"{Neo4jLoaderErrorCodes.NEO4J_EXECUTION_ERROR}: Error loading chunk relationships: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    def load_tag_nodes_and_relationships(self, data_records: List[Dict[str, Any]]) -> None:
        """
        Load tag nodes and relationships from tags field.
        
        Args:
            data_records: List of data records
        """
        logger.info("Loading tag nodes and relationships")
        
        try:
            created_tags = 0
            created_relationships = 0
            
            for record in data_records:
                tags = record.get('tags', [])
                if not tags:
                    continue
                
                # Handle both string and list formats
                if isinstance(tags, str):
                    tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
                
                for tag in tags:
                    try:
                        # Create tag node
                        cypher = """
                        MERGE (t:Tag {tag_name: $tag_name})
                        """
                        self.execute_cypher_query(cypher, {'tag_name': tag})
                        created_tags += 1
                        
                        # Create relationship
                        article_id = record.get('id')
                        if article_id:
                            cypher = """
                            MATCH (a:Article {id: $article_id})
                            MATCH (t:Tag {tag_name: $tag_name})
                            MERGE (a)-[r:TAGGED_WITH]->(t)
                            """
                            self.execute_cypher_query(cypher, {
                                'article_id': article_id,
                                'tag_name': tag
                            })
                            created_relationships += 1
                            
                    except Exception as e:
                        logger.warning(f"Failed to process tag '{tag}': {str(e)}")
            
            # Update metrics (accumulate instead of overwrite)
            if "Tag" not in self.load_metrics["nodes_created"]:
                self.load_metrics["nodes_created"]["Tag"] = 0
            self.load_metrics["nodes_created"]["Tag"] += created_tags
            if "TAGGED_WITH" not in self.load_metrics["relationships_created"]:
                self.load_metrics["relationships_created"]["TAGGED_WITH"] = 0
            self.load_metrics["relationships_created"]["TAGGED_WITH"] += created_relationships
            
            logger.info(f"Created {created_tags} tag nodes and {created_relationships} tag relationships")
            
        except Exception as e:
            error_msg = f"{Neo4jLoaderErrorCodes.NEO4J_EXECUTION_ERROR}: Error loading tags: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    def load_written_by_relationships(self, data_records: List[Dict[str, Any]]) -> None:
        """
        Load WRITTEN_BY relationships between articles and authors.
        
        Args:
            data_records: List of data records
        """
        logger.info("Loading WRITTEN_BY relationships")
        
        try:
            created_count = 0
            failed_count = 0
            
            for record in data_records:
                try:
                    author = record.get('author')
                    article_id = record.get('id')
                    
                    if not author or not article_id:
                        continue
                    
                    # Create author node if it doesn't exist
                    cypher = """
                    MERGE (a:Author {name: $author_name})
                    """
                    self.execute_cypher_query(cypher, {'author_name': author})
                    
                    # Create relationship
                    cypher = """
                    MATCH (article:Article {id: $article_id})
                    MATCH (author:Author {name: $author_name})
                    MERGE (article)-[r:WRITTEN_BY]->(author)
                    """
                    self.execute_cypher_query(cypher, {
                        'article_id': article_id,
                        'author_name': author
                    })
                    
                    created_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    logger.warning(f"Failed to create WRITTEN_BY relationship: {str(e)}")
            
            # Update metrics (accumulate instead of overwrite)
            if "WRITTEN_BY" not in self.load_metrics["relationships_created"]:
                self.load_metrics["relationships_created"]["WRITTEN_BY"] = 0
            self.load_metrics["relationships_created"]["WRITTEN_BY"] += created_count
            if failed_count > 0:
                if "WRITTEN_BY" not in self.load_metrics["relationships_failed"]:
                    self.load_metrics["relationships_failed"]["WRITTEN_BY"] = 0
                self.load_metrics["relationships_failed"]["WRITTEN_BY"] += failed_count
            
            logger.info(f"Created {created_count} WRITTEN_BY relationships")
            
        except Exception as e:
            error_msg = f"{Neo4jLoaderErrorCodes.NEO4J_EXECUTION_ERROR}: Error loading WRITTEN_BY relationships: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    def get_batch_query(self, base_query: str, offset: int, limit: int) -> str:
        """
        Modify the base query to include LIMIT and OFFSET for batch processing.
        
        Args:
            base_query: Original SQL query
            offset: Number of records to skip
            limit: Number of records to fetch
            
        Returns:
            Modified SQL query with LIMIT and OFFSET
        """
        # Remove any existing LIMIT or OFFSET clauses
        query = base_query.strip()
        if query.lower().endswith(';'):
            query = query[:-1]
        
        # Add LIMIT and OFFSET
        batch_query = f"{query} LIMIT {limit} OFFSET {offset}"
        logger.info(f"Batch query: {batch_query}")
        return batch_query
    
    def update_status_neo4j(self, db_config: Dict[str, str], record_ids: List[int], status: bool = True) -> bool:
        """
        Update the status_neo4j field for processed records.
        
        Args:
            db_config: PostgreSQL database configuration
            record_ids: List of record IDs to update
            status: Status value to set (True/False)
            
        Returns:
            True if update was successful, False otherwise
        """
        if not record_ids:
            logger.warning("No record IDs provided for status update")
            return True
        
        try:
            with psycopg2.connect(**db_config) as connection:
                with connection.cursor() as cursor:
                    # Create placeholders for the IN clause
                    placeholders = ','.join(['%s'] * len(record_ids))
                    update_query = f"""
                        UPDATE structured_content 
                        SET status_neo4j = %s 
                        WHERE id IN ({placeholders})
                    """
                    
                    # Execute the update
                    cursor.execute(update_query, [status] + record_ids)
                    connection.commit()
                    
                    logger.info(f"Updated status_neo4j to {status} for {len(record_ids)} records")
                    return True
                    
        except Exception as e:
            error_msg = f"{BatchLoaderErrorCodes.STATUS_UPDATE_ERROR}: Failed to update status_neo4j: {str(e)}"
            logger.error(error_msg)
            return False
    
    def get_total_record_count(self, db_config: Dict[str, str], base_query: str) -> int:
        """
        Get the total number of records to process.
        
        Args:
            db_config: PostgreSQL database configuration
            base_query: Base SQL query
            
        Returns:
            Total number of records
        """
        try:
            with psycopg2.connect(**db_config) as connection:
                with connection.cursor() as cursor:
                    # Create a count query from the base query
                    # Remove semicolon if present
                    clean_query = base_query.strip()
                    if clean_query.endswith(';'):
                        clean_query = clean_query[:-1]
                    
                    count_query = f"SELECT COUNT(*) FROM ({clean_query}) AS count_subquery"
                    logger.info(f"Count query: {count_query}")
                    cursor.execute(count_query)
                    count = cursor.fetchone()[0]
                    logger.info(f"Total records to process: {count}")
                    return count
                    
        except Exception as e:
            logger.error(f"Failed to get total record count: {str(e)}")
            return 0
    
    def process_batch(self, config: Dict[str, Any], model: Dict[str, Any], 
                     db_config: Dict[str, str], base_query: str, 
                     offset: int, batch_num: int) -> Tuple[bool, List[int]]:
        """
        Process a single batch of records.
        
        Args:
            config: Configuration dictionary
            model: Neo4j model configuration
            db_config: PostgreSQL database configuration
            base_query: Base SQL query
            offset: Offset for this batch
            batch_num: Batch number for logging
            
        Returns:
            Tuple of (success, record_ids)
        """
        logger.info(f"Processing batch {batch_num} (offset: {offset}, limit: {self.batch_size})")
        
        try:
            # Get batch query
            batch_query = self.get_batch_query(base_query, offset, self.batch_size)
            
            # Execute batch query
            with psycopg2.connect(**db_config) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(batch_query)
                    results = cursor.fetchall()
                    column_names = [desc[0] for desc in cursor.description]
            
            if not results:
                logger.info(f"Batch {batch_num}: No records found")
                return True, []
            
            # Convert results to dictionaries
            data_records = []
            record_ids = []
            for row in results:
                record = {}
                for i, value in enumerate(row):
                    if i < len(column_names):
                        record[column_names[i]] = value
                data_records.append(record)
                if 'id' in record:
                    record_ids.append(record['id'])
            
            logger.info(f"Batch {batch_num}: Processing {len(data_records)} records")
            
            # Process vector embeddings if needed
            chunk_records = self.process_vector_embeddings(data_records, model, config)
            
            # Load nodes to Neo4j
            self.load_nodes_to_neo4j(data_records, model)
            
            # Load chunk nodes if we have embeddings
            if chunk_records:
                chunk_model = {
                    "nodes": [{
                        "label": "Chunk", 
                        "node_id_property": "chunk_id", 
                        "properties": [
                            {"name": "chunk_id", "type": "string", "unique": True},
                            {"name": "chunk_text", "type": "text"},
                            {"name": "chunk_position", "type": "integer"},
                            {"name": "chunk_order", "type": "integer"},
                            {"name": "content_id", "type": "string"},
                            {"name": "embedding", "type": "vector", "vector_dimension": 384, "vector_similarity": "cosine"}
                        ]
                    }]
                }
                logger.info(f"Batch {batch_num}: Loading {len(chunk_records)} chunk nodes to Neo4j")
                self.load_nodes_to_neo4j(chunk_records, chunk_model)
                self.load_chunk_relationships(chunk_records)
            
            # Load relationships to Neo4j
            self.load_relationships_to_neo4j(data_records, model)
            
            # Create derived entities/relationships
            self.load_tag_nodes_and_relationships(data_records)
            self.load_written_by_relationships(data_records)
            
            # Update status_neo4j for this batch
            if record_ids:
                success = self.update_status_neo4j(db_config, record_ids, True)
                if not success:
                    logger.error(f"Batch {batch_num}: Failed to update status_neo4j")
                    return False, record_ids
            
            logger.info(f"Batch {batch_num}: Completed successfully")
            return True, record_ids
            
        except Exception as e:
            error_msg = f"{BatchLoaderErrorCodes.BATCH_PROCESSING_ERROR}: Batch {batch_num} failed: {str(e)}"
            logger.error(error_msg)
            self.batch_metrics["batch_errors"].append({
                "batch_num": batch_num,
                "offset": offset,
                "error": str(e)
            })
            return False, []
    
    def load_data_in_batches(self, config_path: str, model_path: str, metrics_file: str) -> None:
        """
        Main function to load data into Neo4j in batches.
        
        Args:
            config_path: Path to configuration file
            model_path: Path to Neo4j model JSON file
            metrics_file: Path to metrics output file
        """
        logger.info(f"Starting batch Neo4j data loader with config: {config_path}, model: {model_path}")
        
        try:
            # Load configuration
            config = load_config(config_path)
            
            # Get batch configuration
            self.get_batch_config(config)
            
            # Check if postgres config exists
            if 'database' not in config or 'postgres' not in config['database']:
                raise Exception(f"{BaseErrorCodes.MISSING_DB_CONFIG}: PostgreSQL configuration not found in config file")
            
            # Parse database configuration
            postgres_config_str = config['database']['postgres']
            db_config = parse_postgres_config(postgres_config_str)
            
            # Get base query
            base_query = get_query_from_config(config, 'trending')
            
            # Get total record count
            total_records = self.get_total_record_count(db_config, base_query)
            if total_records == 0:
                logger.info("No records to process")
                return
            
            # Calculate total batches
            total_batches = (total_records + self.batch_size - 1) // self.batch_size
            self.batch_metrics["total_batches"] = total_batches
            
            logger.info(f"Processing {total_records} records in {total_batches} batches of size {self.batch_size}")
            
            # Load Neo4j model
            model = self.load_neo4j_model(model_path)
            
            # Initialize Neo4j connection
            self.initialize_neo4j_connection(config)
            
            # Process batches
            for batch_num in range(1, total_batches + 1):
                offset = (batch_num - 1) * self.batch_size
                
                success, record_ids = self.process_batch(
                    config, model, db_config, base_query, offset, batch_num
                )
                
                if success:
                    self.batch_metrics["completed_batches"] += 1
                    self.load_metrics["total_records_processed"] += len(record_ids)
                else:
                    self.batch_metrics["failed_batches"] += 1
                    logger.error(f"Batch {batch_num} failed, but continuing with next batch")
                
                # Log progress
                progress = (batch_num / total_batches) * 100
                logger.info(f"Progress: {progress:.1f}% ({batch_num}/{total_batches} batches completed)")
            
            # Write final metrics
            self.write_batch_metrics(metrics_file)
            
            logger.info("Batch Neo4j data loading completed successfully")
            
        except Exception as e:
            logger.error(f"Batch Neo4j data loading failed: {str(e)}")
            # Still try to write metrics even if loading failed
            try:
                self.write_batch_metrics(metrics_file)
            except:
                pass
            raise
        finally:
            if self.neo4j_driver:
                self.neo4j_driver.close()
                logger.info("Neo4j connection closed")
    
    def write_batch_metrics(self, metrics_file: str) -> None:
        """
        Write batch processing metrics to file.
        
        Args:
            metrics_file: Path to metrics output file
        """
        try:
            metrics = {
                "batch_metrics": self.batch_metrics,
                "load_metrics": self.load_metrics,
                "cypher_usage": dict(self.cypher_usage),
                "timestamp": datetime.now().isoformat()
            }
            
            with open(metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2, default=str)
            
            logger.info(f"Batch metrics written to {metrics_file}")
            
        except Exception as e:
            error_msg = f"{BatchLoaderErrorCodes.BATCH_CONFIG_ERROR}: Failed to write batch metrics: {str(e)}"
            logger.error(error_msg)


def main():
    """Main entry point for command line usage."""
    parser = argparse.ArgumentParser(description='Batch Neo4j Data Loader')
    parser.add_argument('config_file', help='Path to configuration YAML file')
    parser.add_argument('--model-file', help='Path to Neo4j model JSON file (optional)')
    parser.add_argument('--metrics-file', help='Path to metrics output file (optional)')
    
    args = parser.parse_args()
    
    # Generate default model and metrics file names if not provided
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_file = args.model_file or f"output/data/neo4j_model_clean_{timestamp}.json"
    metrics_file = args.metrics_file or f"output/metrics/batch_load_metrics_{timestamp}.txt"
    
    try:
        loader = BatchNeo4jLoader()
        loader.load_data_in_batches(args.config_file, model_file, metrics_file)
        print(f"Batch data loading completed successfully. Metrics saved to {metrics_file}")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
