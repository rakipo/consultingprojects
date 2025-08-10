#!/usr/bin/env python3
"""
Neo4j Data Loader
A program that inherits from PostgreSQL Query Runner to load data into Neo4j based on generated models.

Usage:
    python src/neo4j_data_loader.py config/config_boomer_load.yml output/data/neo4j_model_20250807.json output/metrics/neo4j_load_metrics_20250807.txt
"""

import sys
import logging
import json
import subprocess
import tempfile
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import argparse
from pathlib import Path
from neo4j import GraphDatabase
import openai
from sentence_transformers import SentenceTransformer

# Import the parent class
try:
    from .postgres_query_runner import (
        PostgresQueryRunner, 
        ErrorCodes as BaseErrorCodes,
        load_config,
        parse_postgres_config,
        get_query_from_config
    )
except ImportError:
    # Fallback for direct execution
    from postgres_query_runner import (
        PostgresQueryRunner, 
        ErrorCodes as BaseErrorCodes,
        load_config,
        parse_postgres_config,
        get_query_from_config
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

# Extended error codes for Neo4j data loading
class Neo4jLoaderErrorCodes:
    NEO4J_CONNECTION_ERROR = "ERR_L001"
    NEO4J_EXECUTION_ERROR = "ERR_L002"
    MODEL_LOADING_ERROR = "ERR_L003"
    CHUNKING_ERROR = "ERR_L004"
    EMBEDDING_ERROR = "ERR_L005"
    MCP_CONNECTION_ERROR = "ERR_L006"
    MCP_EXECUTION_ERROR = "ERR_L007"
    METRICS_WRITE_ERROR = "ERR_L008"
    DATA_VALIDATION_ERROR = "ERR_L009"


class Neo4jDataLoader(PostgresQueryRunner):
    """
    Neo4j Data Loader that extends PostgreSQL Query Runner.
    
    This class inherits from PostgresQueryRunner to fetch data from PostgreSQL
    and loads it into Neo4j based on the provided model configuration.
    """
    
    def __init__(self):
        """Initialize the Neo4j Data Loader."""
        super().__init__()
        self.neo4j_driver = None
        self.embedding_model = None
        self.load_metrics = {
            "nodes_created": {},
            "relationships_created": {},
            "nodes_failed": {},
            "relationships_failed": {},
            "chunks_created": 0,
            "embeddings_generated": 0,
            "total_records_processed": 0,
            "errors": []
        }
        # Track cypher templates executed and how many times
        # Key: (category, name, cypher_text) -> count
        self.cypher_usage: Dict[Tuple[str, str, str], int] = {}
        # Store Postgres records without the 'content' field for metrics
        self.postgres_records_wo_content: List[Dict[str, Any]] = []
        logger.info("Neo4j Data Loader initialized")
    
    def load_neo4j_model(self, model_path: str) -> Dict[str, Any]:
        """
        Load Neo4j model from JSON file.
        
        Args:
            model_path: Path to the Neo4j model JSON file
            
        Returns:
            Dictionary containing the Neo4j model
        """
        logger.info(f"Loading Neo4j model from: {model_path}")
        
        try:
            with open(model_path, 'r', encoding='utf-8') as file:
                model = json.load(file)
            
            logger.info(f"Neo4j model loaded successfully with {len(model.get('nodes', []))} nodes and {len(model.get('relationships', []))} relationships")
            return model
            
        except FileNotFoundError as e:
            error_msg = f"{Neo4jLoaderErrorCodes.MODEL_LOADING_ERROR}: Model file not found: {model_path}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
        except json.JSONDecodeError as e:
            error_msg = f"{Neo4jLoaderErrorCodes.MODEL_LOADING_ERROR}: Invalid JSON in model file: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"{Neo4jLoaderErrorCodes.MODEL_LOADING_ERROR}: Error loading model: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    def connect_to_neo4j(self, neo4j_config: Dict[str, str]) -> None:
        """
        Connect to Neo4j database.
        
        Args:
            neo4j_config: Neo4j connection configuration
        """
        logger.info(f"Connecting to Neo4j at {neo4j_config.get('host')}:{neo4j_config.get('port')}")
        
        try:
            uri = f"bolt://{neo4j_config['host']}:{neo4j_config['port']}"
            self.neo4j_driver = GraphDatabase.driver(
                uri,
                auth=(neo4j_config['user'], neo4j_config['password'])
            )
            
            # Test connection
            with self.neo4j_driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            
            logger.info("Neo4j connection established successfully")
            
        except Exception as e:
            error_msg = f"{Neo4jLoaderErrorCodes.NEO4J_CONNECTION_ERROR}: Failed to connect to Neo4j: {str(e)}"
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
        Use OpenAI LLM to intelligently chunk text based on semantic boundaries.
        
        Args:
            text: Text to chunk
            target_chunk_size: Target size for each chunk
            
        Returns:
            List of intelligently chunked text segments
        """
        logger.info("Using LLM-based intelligent text chunking")
        
        try:
            # Initialize OpenAI client if not already done
            if not hasattr(self, 'openai_client'):
                api_key = os.getenv('OPENAI_API_KEY')
                if not api_key:
                    logger.warning("OPENAI_API_KEY environment variable not set, falling back to simple chunking")
                    return self._chunk_simple(text, target_chunk_size, 50)
                self.openai_client = openai.OpenAI(api_key=api_key)
            
            # Create prompt for intelligent chunking
            prompt = f"""
            Please intelligently chunk the following text into segments of approximately {target_chunk_size} characters each.
            Focus on semantic boundaries like paragraphs, sentences, and logical breaks.
            Return the chunks as a JSON array where each element has 'text' and 'summary' fields.
            
            Text to chunk:
            {text[:4000]}  # Limit text to avoid token limits
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at intelligently chunking text for vector embeddings. Focus on semantic boundaries and logical breaks."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            # Parse LLM response
            llm_response = response.choices[0].message.content
            
            try:
                # Try to parse as JSON
                import re
                json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
                if json_match:
                    chunks_data = json.loads(json_match.group())
                else:
                    # Fallback to simple parsing
                    raise ValueError("No JSON array found in LLM response")
                
                chunks = []
                for i, chunk_data in enumerate(chunks_data):
                    if isinstance(chunk_data, dict) and 'text' in chunk_data:
                        chunk_text = chunk_data['text'].strip()
                    elif isinstance(chunk_data, str):
                        chunk_text = chunk_data.strip()
                    else:
                        continue
                    
                    if chunk_text:
                        chunk_id = str(uuid.uuid4())
                        chunks.append({
                            'chunk_id': chunk_id,
                            'chunk_text': chunk_text,
                            'chunk_position': i,
                            'chunk_order': i,
                            'summary': chunk_data.get('summary', '') if isinstance(chunk_data, dict) else '',
                            'chunking_method': 'llm'
                        })
                
                if chunks:
                    logger.info(f"LLM-based chunking created {len(chunks)} semantic chunks")
                    return chunks
                else:
                    logger.warning("LLM chunking failed, falling back to simple chunking")
                    return self._chunk_simple(text, target_chunk_size, 50)
                    
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"Failed to parse LLM response, falling back to simple chunking: {str(e)}")
                return self._chunk_simple(text, target_chunk_size, 50)
                
        except Exception as e:
            logger.warning(f"LLM chunking failed: {str(e)}, falling back to simple chunking")
            return self._chunk_simple(text, target_chunk_size, 50)
    
    def _chunk_simple(self, text: str, chunk_size: int, overlap: int) -> List[Dict[str, Any]]:
        """
        Simple character-based text chunking with word boundary awareness.
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        chunk_position = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            
            # Try to break at word boundary
            if end < len(text):
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunk_id = str(uuid.uuid4())
                chunks.append({
                    'chunk_id': chunk_id,
                    'chunk_text': chunk_text,
                    'chunk_position': chunk_position,
                    'chunk_order': len(chunks),
                    'chunking_method': 'simple'
                })
                chunk_position += 1
            
            start = end - overlap if end < len(text) else end
        
        return chunks
    
    def _record_cypher(self, category: str, name: str, cypher: str) -> None:
        """Record a cypher template and increment execution count for metrics."""
        key = (category, name, cypher.strip())
        self.cypher_usage[key] = self.cypher_usage.get(key, 0) + 1

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for text chunks.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        logger.info(f"Generating embeddings for {len(texts)} texts")
        
        try:
            if not self.embedding_model:
                self.initialize_embedding_model()
            
            embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
            # Handle both numpy arrays and lists
            embeddings_list = []
            for embedding in embeddings:
                if hasattr(embedding, 'tolist'):
                    embeddings_list.append(embedding.tolist())
                else:
                    embeddings_list.append(embedding)
            
            self.load_metrics["embeddings_generated"] += len(embeddings_list)
            logger.info(f"Generated {len(embeddings_list)} embeddings")
            
            return embeddings_list
            
        except Exception as e:
            error_msg = f"{Neo4jLoaderErrorCodes.EMBEDDING_ERROR}: Error generating embeddings: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    def call_mcp_neo4j_cypher(self, query_request: str) -> str:
        """
        Call MCP Neo4j Cypher service to get Cypher queries.
        
        Args:
            query_request: Request for Cypher query generation
            
        Returns:
            Generated Cypher query
        """
        logger.info("Calling MCP Neo4j Cypher service")
        
        try:
            # Create temporary file with request
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump({"request": query_request}, temp_file, indent=2)
                temp_file_path = temp_file.name
            
            try:
                # Call MCP service (simulated - in real implementation this would call actual MCP)
                # For now, we'll return a basic query structure
                cypher_query = self._generate_basic_cypher(query_request)
                
                logger.info("MCP Neo4j Cypher service completed successfully")
                return cypher_query
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except subprocess.CalledProcessError as e:
            error_msg = f"{Neo4jLoaderErrorCodes.MCP_EXECUTION_ERROR}: MCP service execution failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"{Neo4jLoaderErrorCodes.MCP_CONNECTION_ERROR}: Error calling MCP Neo4j Cypher: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    def _generate_basic_cypher(self, query_request: str) -> str:
        """
        Generate basic Cypher query (fallback when MCP is not available).
        
        Args:
            query_request: Request description
            
        Returns:
            Basic Cypher query
        """
        # This is a simplified fallback - in production, MCP would handle this
        if "create node" in query_request.lower():
            return "MERGE (n:Node {id: $id}) SET n += $properties"
        elif "create relationship" in query_request.lower():
            return "MATCH (a), (b) WHERE a.id = $start_id AND b.id = $end_id MERGE (a)-[r:RELATES_TO]->(b) SET r += $properties"
        else:
            return "RETURN 'Query generated by fallback method'"
    
    def execute_cypher_query(self, cypher: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute Cypher query in Neo4j.
        
        Args:
            cypher: Cypher query to execute
            parameters: Query parameters
            
        Returns:
            Query execution results
        """
        logger.info(f"Executing Cypher query: {cypher[:100]}...")
        
        try:
            with self.neo4j_driver.session() as session:
                result = session.run(cypher, parameters or {})
                
                # Process results - collect records BEFORE consuming
                records = []
                for record in result:
                    records.append(dict(record))
                
                # Now consume to get summary
                summary = result.consume()
                
                execution_result = {
                    "records": records,
                    "summary": {
                        "nodes_created": summary.counters.nodes_created,
                        "relationships_created": summary.counters.relationships_created,
                        "properties_set": summary.counters.properties_set,
                        "labels_added": summary.counters.labels_added
                    }
                }
                
                logger.info(f"Query executed successfully. Nodes created: {summary.counters.nodes_created}, Relationships created: {summary.counters.relationships_created}")
                return execution_result
                
        except Exception as e:
            error_msg = f"{Neo4jLoaderErrorCodes.NEO4J_EXECUTION_ERROR}: Error executing Cypher query: {str(e)}"
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
            
            # Find vector properties in the model
            vector_properties = []
            content_property = None
            
            for node in model.get('nodes', []):
                for prop in node.get('properties', []):
                    if prop.get('type') == 'vector':
                        vector_properties.append(prop)
                    elif prop.get('name') in ['content', 'text', 'description']:
                        content_property = prop.get('name')
            
            if not vector_properties or not content_property:
                logger.info("No vector properties or content property found, skipping embedding processing")
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
                        load_config_section = config.get('neo4j_load_config', {})
                        embedding_config = load_config_section.get('embedding', {})
                        chunk_size = embedding_config.get('chunk_size', 512)
                        chunk_overlap = embedding_config.get('chunk_overlap', 50)
                        use_llm_chunking = embedding_config.get('use_llm_chunking', True)
                    
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
 
    def _compute_required_node_properties_from_relationships(self, model: Dict[str, Any]) -> Dict[str, set]:
        """Determine which node properties are referenced by relationships so we can set them on nodes."""
        label_to_required_props: Dict[str, set] = {}
        for rel in model.get('relationships', []):
            start_label = rel.get('start_node')
            end_label = rel.get('end_node')
            start_prop = rel.get('start_property')
            end_prop = rel.get('end_property')
            if start_label and start_prop:
                label_to_required_props.setdefault(start_label, set()).add(start_prop)
            if end_label and end_prop:
                label_to_required_props.setdefault(end_label, set()).add(end_prop)
        return label_to_required_props

    def apply_schema_from_model(self, model: Dict[str, Any], vector_dimension_override: Optional[int] = None) -> None:
        """Create constraints and indexes defined in the model before loading data."""
        logger.info("Applying constraints from model")
        for constraint in model.get('constraints', []):
            cypher = constraint.get('cypher')
            if not cypher:
                continue
            try:
                self.execute_cypher_query(cypher)
            except Exception as e:
                logger.warning(f"Failed to create constraint '{constraint.get('node_label', '')}.{constraint.get('property', '')}': {str(e)}")

        logger.info("Applying indexes from model")
        for index in model.get('indexes', []):
            cypher = index.get('cypher')
            index_type = index.get('type', '')
            node_label = index.get('node_label', '')
            property_name = index.get('property', '')

            # Adjust vector index to match actual embedding dimension if provided
            if index_type == 'VECTOR' and node_label == 'Chunk' and property_name == 'embedding':
                dim = vector_dimension_override or index.get('vector_dimension') or 384
                similarity = index.get('vector_similarity', 'cosine')
                cypher = (
                    f"CREATE VECTOR INDEX chunk_embedding_vector IF NOT EXISTS "
                    f"FOR (n:Chunk) ON (n.embedding) OPTIONS {{indexConfig: {{`vector.dimensions`: {dim}, "
                    f"`vector.similarity_function`: '{similarity}'}}}}"
                )

            if not cypher:
                continue
            try:
                self._record_cypher('schema', f"INDEX {node_label}.{property_name}", cypher)
                self.execute_cypher_query(cypher)
            except Exception as e:
                logger.warning(f"Failed to create index '{node_label}.{property_name}' ({index_type}): {str(e)}")

    def load_nodes_to_neo4j(self, data_records: List[Dict[str, Any]], model: Dict[str, Any]) -> None:
        """
        Load nodes to Neo4j based on the model configuration.
        
        Args:
            data_records: List of data records from PostgreSQL
            model: Neo4j model configuration
        """
        logger.info("Loading nodes to Neo4j")
        
        try:
            # Ensure that properties used in relationships are present on nodes
            required_props_by_label = self._compute_required_node_properties_from_relationships(model)
            for node_config in model.get('nodes', []):
                node_label = node_config['label']
                logger.info(f"Processing {node_label} nodes")
                
                nodes_created = 0
                nodes_failed = 0
                
                for record in data_records:
                    try:
                        # Special handling for Author nodes: use 'name' field sourced from record['author']
                        if node_label == 'Author':
                            author_value = record.get('author')
                            if not author_value:
                                # Skip if no author provided
                                continue
                            cypher = """
                            MERGE (n:Author {name: $name})
                            """
                            params = {"name": author_value}
                            self._record_cypher('nodes', 'Author', cypher)
                            result = self.execute_cypher_query(cypher, params)
                            nodes_created += result['summary']['nodes_created']
                            continue

                        # Build node properties
                        node_properties = {}
                        node_id_property = node_config.get('node_id_property')
                        
                        for prop_config in node_config.get('properties', []):
                            prop_name = prop_config['name']
                            if prop_name in record and record[prop_name] is not None:
                                alias = prop_config.get('alias', prop_name)
                                node_properties[alias] = record[prop_name]

                        # Also include any relationship-referenced properties for this label
                        for rel_prop in required_props_by_label.get(node_label, set()):
                            if rel_prop not in node_properties and rel_prop in record and record[rel_prop] is not None:
                                node_properties[rel_prop] = record[rel_prop]
 
                        if node_id_property and node_id_property in record:
                            # Use MERGE for better data integrity
                            cypher = f"""
                            MERGE (n:{node_label} {{{node_id_property}: $id}})
                            SET n += $properties
                            """
                            
                            # Add multiple labels if specified
                            if 'multiple_labels' in node_config:
                                additional_labels = ':'.join(node_config['multiple_labels'])
                                cypher += f"\nSET n:{additional_labels}"
                            
                            parameters = {
                                'id': record[node_id_property],
                                'properties': node_properties
                            }
                            
                            self._record_cypher('nodes', node_label, cypher)
                            result = self.execute_cypher_query(cypher, parameters)
                            nodes_created += result['summary']['nodes_created']
                        
                    except Exception as e:
                        nodes_failed += 1
                        error_msg = f"Failed to create {node_label} node: {str(e)}"
                        logger.error(error_msg)
                        self.load_metrics["errors"].append(error_msg)
                
                self.load_metrics["nodes_created"][node_label] = nodes_created
                self.load_metrics["nodes_failed"][node_label] = nodes_failed
                
                logger.info(f"Completed {node_label} nodes: {nodes_created} created, {nodes_failed} failed")
                
        except Exception as e:
            error_msg = f"{Neo4jLoaderErrorCodes.NEO4J_EXECUTION_ERROR}: Error loading nodes: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
 
    def load_relationships_to_neo4j(self, data_records: List[Dict[str, Any]], model: Dict[str, Any]) -> None:
        """
        Load relationships to Neo4j based on the model configuration.
        
        Args:
            data_records: List of data records from PostgreSQL
            model: Neo4j model configuration
        """
        logger.info("Loading relationships to Neo4j")
        
        try:
            for rel_config in model.get('relationships', []):
                rel_type = rel_config['type']
                
                # Skip HAS_CHUNK relationships - they are handled separately in load_chunk_relationships
                if rel_type == 'HAS_CHUNK':
                    logger.info(f"Skipping {rel_type} relationships - handled separately during chunk loading")
                    continue
                    
                logger.info(f"Processing {rel_type} relationships")
                
                relationships_created = 0
                relationships_failed = 0
                
                for record in data_records:
                    try:
                        start_node = rel_config['start_node']
                        end_node = rel_config['end_node']
                        start_property = rel_config['start_property']
                        end_property = rel_config['end_property']
                        
                        if start_property in record and end_property in record:
                            # Build relationship properties
                            rel_properties = {}
                            for prop in rel_config.get('properties', []):
                                prop_name = prop['name']
                                if prop_name in record and record[prop_name] is not None:
                                    rel_properties[prop_name] = record[prop_name]
                            
                            # Use MERGE for relationships
                            cypher = f"""
                            MATCH (start:{start_node} {{{start_property}: $start_value}})
                            MATCH (end:{end_node} {{{end_property}: $end_value}})
                            MERGE (start)-[r:{rel_type}]->(end)
                            SET r += $properties
                            """
                            
                            parameters = {
                                'start_value': record[start_property],
                                'end_value': record[end_property],
                                'properties': rel_properties
                            }
                            
                            self._record_cypher('relationships', rel_type, cypher)
                            result = self.execute_cypher_query(cypher, parameters)
                            relationships_created += result['summary']['relationships_created']
                    
                    except Exception as e:
                        relationships_failed += 1
                        error_msg = f"Failed to create {rel_type} relationship: {str(e)}"
                        logger.error(error_msg)
                        self.load_metrics["errors"].append(error_msg)
                
                self.load_metrics["relationships_created"][rel_type] = relationships_created
                self.load_metrics["relationships_failed"][rel_type] = relationships_failed
                
                logger.info(f"Completed {rel_type} relationships: {relationships_created} created, {relationships_failed} failed")
                
        except Exception as e:
            error_msg = f"{Neo4jLoaderErrorCodes.NEO4J_EXECUTION_ERROR}: Error loading relationships: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
 
    def load_chunk_relationships(self, chunk_records: List[Dict[str, Any]]) -> None:
        """Create HAS_CHUNK relationships between Article and Chunk nodes using chunk metadata."""
        if not chunk_records:
            return
        logger.info("Creating HAS_CHUNK relationships from chunk records")
        try:
            rel_type = 'HAS_CHUNK'
            relationships_created = 0
            relationships_failed = 0
            for rec in chunk_records:
                try:
                    cypher = """
                    MATCH (start:Article {id: $article_id})
                    MATCH (end:Chunk {chunk_id: $chunk_id})
                    MERGE (start)-[r:HAS_CHUNK]->(end)
                    SET r.chunk_order = $chunk_order, r.chunk_position = $chunk_position
                    """
                    params = {
                        'article_id': rec.get('content_id'),
                        'chunk_id': rec.get('chunk_id'),
                        'chunk_order': rec.get('chunk_order'),
                        'chunk_position': rec.get('chunk_position'),
                    }
                    self._record_cypher('relationships', 'HAS_CHUNK', cypher)
                    result = self.execute_cypher_query(cypher, params)
                    relationships_created += result['summary']['relationships_created']
                except Exception as e:
                    relationships_failed += 1
                    err = f"Failed to create HAS_CHUNK relationship: {str(e)}"
                    logger.error(err)
                    self.load_metrics["errors"].append(err)
            self.load_metrics["relationships_created"].setdefault('HAS_CHUNK', 0)
            self.load_metrics["relationships_failed"].setdefault('HAS_CHUNK', 0)
            self.load_metrics["relationships_created"][rel_type] += relationships_created
            self.load_metrics["relationships_failed"][rel_type] += relationships_failed
            logger.info(f"Completed HAS_CHUNK relationships: {relationships_created} created, {relationships_failed} failed")
        except Exception as e:
            error_msg = f"{Neo4jLoaderErrorCodes.NEO4J_EXECUTION_ERROR}: Error loading HAS_CHUNK relationships: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e

    def load_tag_nodes_and_relationships(self, data_records: List[Dict[str, Any]]) -> None:
        """Create Tag nodes from 'tags' array and TAGGED_WITH relationships to Article."""
        logger.info("Creating Tag nodes and TAGGED_WITH relationships")
        try:
            nodes_created = 0
            rels_created = 0
            nodes_failed = 0
            rels_failed = 0
            for rec in data_records:
                article_id = rec.get('id')
                tags_value = rec.get('tags')
                if not article_id or tags_value is None:
                    continue
                # Normalize tags to list[str]
                if isinstance(tags_value, str):
                    # Attempt comma-separated
                    tag_list = [t.strip() for t in tags_value.split(',') if t.strip()]
                elif isinstance(tags_value, list):
                    tag_list = [str(t).strip() for t in tags_value if str(t).strip()]
                else:
                    continue
                for tag_name in tag_list:
                    try:
                        cy_node = """
                        MERGE (t:Tag {tag_name: $tag_name})
                        """
                        self._record_cypher('nodes', 'Tag', cy_node)
                        res_node = self.execute_cypher_query(cy_node, {"tag_name": tag_name})
                        nodes_created += res_node['summary']['nodes_created']

                        cy_rel = """
                        MATCH (a:Article {id: $article_id})
                        MATCH (t:Tag {tag_name: $tag_name})
                        MERGE (a)-[r:TAGGED_WITH]->(t)
                        """
                        self._record_cypher('relationships', 'TAGGED_WITH', cy_rel)
                        res_rel = self.execute_cypher_query(cy_rel, {"article_id": article_id, "tag_name": tag_name})
                        rels_created += res_rel['summary']['relationships_created']
                    except Exception as e:
                        # track failure
                        nodes_failed += 0  # node failure captured via exception; continue
                        rels_failed += 1
                        err = f"Failed TAGGED_WITH for article {article_id} tag '{tag_name}': {str(e)}"
                        logger.error(err)
                        self.load_metrics["errors"].append(err)

            # Aggregate counts into metrics
            self.load_metrics["nodes_created"].setdefault('Tag', 0)
            self.load_metrics["nodes_created"]["Tag"] += nodes_created
            self.load_metrics["nodes_failed"].setdefault('Tag', 0)
            self.load_metrics["nodes_failed"]["Tag"] += nodes_failed
            self.load_metrics["relationships_created"].setdefault('TAGGED_WITH', 0)
            self.load_metrics["relationships_created"]["TAGGED_WITH"] += rels_created
            self.load_metrics["relationships_failed"].setdefault('TAGGED_WITH', 0)
            self.load_metrics["relationships_failed"]["TAGGED_WITH"] += rels_failed
            logger.info(f"Completed Tag nodes and TAGGED_WITH: {nodes_created} tags, {rels_created} relationships created")
        except Exception as e:
            error_msg = f"{Neo4jLoaderErrorCodes.NEO4J_EXECUTION_ERROR}: Error loading tags: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e

    def load_written_by_relationships(self, data_records: List[Dict[str, Any]]) -> None:
        """Create WRITTEN_BY relationships using record['author'] to Author{name} and Article{id}."""
        logger.info("Creating WRITTEN_BY relationships")
        try:
            created = 0
            failed = 0
            for rec in data_records:
                author = rec.get('author')
                article_id = rec.get('id')
                publish_date = rec.get('publish_date')
                if not author or not article_id:
                    continue
                try:
                    cy = """
                    MATCH (a:Article {id: $article_id})
                    MERGE (auth:Author {name: $author})
                    MERGE (a)-[r:WRITTEN_BY]->(auth)
                    SET r.publish_date = $publish_date
                    """
                    params = {"article_id": article_id, "author": author, "publish_date": publish_date}
                    self._record_cypher('relationships', 'WRITTEN_BY', cy)
                    res = self.execute_cypher_query(cy, params)
                    created += res['summary']['relationships_created']
                except Exception as e:
                    failed += 1
                    err = f"Failed WRITTEN_BY for article {article_id} author '{author}': {str(e)}"
                    logger.error(err)
                    self.load_metrics["errors"].append(err)
            self.load_metrics["relationships_created"].setdefault('WRITTEN_BY', 0)
            self.load_metrics["relationships_created"]["WRITTEN_BY"] += created
            self.load_metrics["relationships_failed"].setdefault('WRITTEN_BY', 0)
            self.load_metrics["relationships_failed"]["WRITTEN_BY"] += failed
            logger.info(f"Completed WRITTEN_BY relationships: {created} created, {failed} failed")
        except Exception as e:
            error_msg = f"{Neo4jLoaderErrorCodes.NEO4J_EXECUTION_ERROR}: Error loading WRITTEN_BY relationships: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
 
    def write_load_metrics(self, metrics_file: str) -> None:
        """
        Write load metrics to file.
        
        Args:
            metrics_file: Path to metrics output file
        """
        logger.info(f"Writing load metrics to: {metrics_file}")
        
        try:
            with open(metrics_file, 'w', encoding='utf-8') as file:
                file.write("Neo4j Data Load Metrics\n")
                file.write("=" * 50 + "\n\n")
                file.write(f"Load completed at: {datetime.now().isoformat()}\n\n")
                
                # Nodes created
                file.write("NODES CREATED:\n")
                file.write("-" * 20 + "\n")
                total_nodes = 0
                for node_type, count in self.load_metrics["nodes_created"].items():
                    file.write(f"{node_type}: {count}\n")
                    total_nodes += count
                file.write(f"Total Nodes: {total_nodes}\n\n")
                
                # Relationships created
                file.write("RELATIONSHIPS CREATED:\n")
                file.write("-" * 25 + "\n")
                total_relationships = 0
                for rel_type, count in self.load_metrics["relationships_created"].items():
                    file.write(f"{rel_type}: {count}\n")
                    total_relationships += count
                file.write(f"Total Relationships: {total_relationships}\n\n")
                
                # Failed operations
                file.write("FAILED OPERATIONS:\n")
                file.write("-" * 20 + "\n")
                for node_type, count in self.load_metrics["nodes_failed"].items():
                    if count > 0:
                        file.write(f"Failed {node_type} nodes: {count}\n")
                for rel_type, count in self.load_metrics["relationships_failed"].items():
                    if count > 0:
                        file.write(f"Failed {rel_type} relationships: {count}\n")
                
                # Vector embeddings
                file.write(f"\nVECTOR EMBEDDINGS:\n")
                file.write("-" * 20 + "\n")
                file.write(f"Chunks created: {self.load_metrics['chunks_created']}\n")
                file.write(f"Embeddings generated: {self.load_metrics['embeddings_generated']}\n")
                
                # Summary
                file.write(f"\nSUMMARY:\n")
                file.write("-" * 10 + "\n")
                file.write(f"Total records processed: {self.load_metrics['total_records_processed']}\n")
                file.write(f"Total errors: {len(self.load_metrics['errors'])}\n")
                
                # Errors
                if self.load_metrics["errors"]:
                    file.write(f"\nERRORS:\n")
                    file.write("-" * 10 + "\n")
                    for i, error in enumerate(self.load_metrics["errors"], 1):
                        file.write(f"{i}. {error}\n")

                # Cypher queries used
                if self.cypher_usage:
                    file.write(f"\nCYPHER QUERIES USED:\n")
                    file.write("-" * 22 + "\n")
                    # Group and list
                    for (category, name, cypher_text), count in sorted(self.cypher_usage.items(), key=lambda x: (x[0][0], x[0][1])):
                        file.write(f"[{category}] {name} (executed {count}x)\n")
                        file.write(cypher_text.strip() + "\n\n")

                # Postgres records (excluding 'content')
                if self.postgres_records_wo_content:
                    file.write(f"\nPOSTGRES RECORDS (excluding 'content'):\n")
                    file.write("-" * 40 + "\n")
                    max_to_write = len(self.postgres_records_wo_content)
                    for i in range(max_to_write):
                        rec = self.postgres_records_wo_content[i]
                        try:
                            rec_json = json.dumps(rec, default=str)
                        except Exception:
                            rec_json = str(rec)
                        if len(rec_json) > 5000:
                            rec_json = rec_json[:5000] + '...'
                        file.write(f"Record {i+1}: {rec_json}\n")
 
            logger.info(f"Load metrics written successfully to {metrics_file}")
            
        except Exception as e:
            error_msg = f"{Neo4jLoaderErrorCodes.METRICS_WRITE_ERROR}: Error writing metrics: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
 
    def load_data_to_neo4j(self, config_path: str, model_path: str, metrics_file: str) -> None:
        """
        Main function to load data from PostgreSQL to Neo4j.
        
        Args:
            config_path: Path to configuration file
            model_path: Path to Neo4j model JSON file
            metrics_file: Path to metrics output file
        """
        logger.info(f"Starting Neo4j data loading process")
        
        try:
            # Load configuration and model
            config = load_config(config_path)
            model = self.load_neo4j_model(model_path)
            
            # Parse database configurations
            if 'database' not in config:
                raise Exception(f"{BaseErrorCodes.MISSING_DB_CONFIG}: Database configuration not found")
            
            postgres_config_str = config['database']['postgres']
            postgres_config = parse_postgres_config(postgres_config_str)
            
            neo4j_config_str = config['database']['neo4j']
            neo4j_config = parse_postgres_config(neo4j_config_str)  # Same parsing logic
            
            # Connect to databases
            self.connect_to_neo4j(neo4j_config)

            # Apply schema (constraints and indexes) before loading
            # Determine embedding dimension to use for vector indexes
            vector_dim = None
            try:
                # Lazy compute embedding dimension by encoding a small sample
                self.initialize_embedding_model()
                test_vec = self.embedding_model.encode(["test"], convert_to_tensor=False)[0]
                vector_dim = len(test_vec.tolist() if hasattr(test_vec, 'tolist') else list(test_vec))
            except Exception:
                vector_dim = 384
            self.apply_schema_from_model(model, vector_dimension_override=vector_dim)

            # Use the specific "trending" query as mentioned in requirements
            query_name = "trending"
            
            if 'queries' not in config or query_name not in config['queries']:
                available_queries = list(config.get('queries', {}).keys())
                raise Exception(f"{BaseErrorCodes.INVALID_QUERY_NAME}: Query '{query_name}' not found in configuration. Available queries: {available_queries}")
            
            query = get_query_from_config(config, query_name)
            logger.info(f"Using query '{query_name}' for data loading")
            
            # Execute PostgreSQL query
            with self.get_db_connection(postgres_config) as connection:
                results, column_names = self.execute_query(connection, query)
            
            # Convert results to dictionaries
            data_records = []
            for row in results:
                record = {}
                for i, value in enumerate(row):
                    if i < len(column_names):
                        record[column_names[i]] = value
                data_records.append(record)
 
            # Print/log retrieval values excluding the 'content' column
            try:
                self.postgres_records_wo_content = [
                    {k: v for k, v in rec.items() if k != 'content'} for rec in data_records
                ]
                for idx, rec_wo_content in enumerate(self.postgres_records_wo_content, start=1):
                    # Limit log size to avoid extremely large outputs
                    rec_json = json.dumps(rec_wo_content, default=str)
                    if len(rec_json) > 2000:
                        rec_json = rec_json[:2000] + '...'
                    logger.info(f"Postgres record #{idx} (excluding 'content'): {rec_json}")
            except Exception as e:
                logger.warning(f"Failed to log Postgres records without 'content': {str(e)}")
 
            self.load_metrics["total_records_processed"] = len(data_records)
            
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
                logger.info(f"Loading {len(chunk_records)} chunk nodes to Neo4j")
                self.load_nodes_to_neo4j(chunk_records, chunk_model)

                # Create HAS_CHUNK relationships between Article and Chunk
                self.load_chunk_relationships(chunk_records)
 
            # Load relationships to Neo4j
            self.load_relationships_to_neo4j(data_records, model)

            # Create derived entities/relationships not covered properly by the model
            self.load_tag_nodes_and_relationships(data_records)
            self.load_written_by_relationships(data_records)
 
            # Write metrics
            self.write_load_metrics(metrics_file)
            
            logger.info("Neo4j data loading completed successfully")
            
        except Exception as e:
            logger.error(f"Neo4j data loading failed: {str(e)}")
            # Still try to write metrics even if loading failed
            try:
                self.write_load_metrics(metrics_file)
            except:
                pass
            raise
        finally:
            if self.neo4j_driver:
                self.neo4j_driver.close()
                logger.info("Neo4j connection closed")


def main():
    """Main entry point for command line usage."""
    parser = argparse.ArgumentParser(description='Neo4j Data Loader')
    parser.add_argument('config_file', help='Path to configuration YAML file')
    parser.add_argument('model_file', help='Path to Neo4j model JSON file')
    parser.add_argument('metrics_file', help='Path to metrics output file')
    
    args = parser.parse_args()
    
    try:
        loader = Neo4jDataLoader()
        loader.load_data_to_neo4j(args.config_file, args.model_file, args.metrics_file)
        print(f"Data loading completed successfully. Metrics saved to {args.metrics_file}")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()