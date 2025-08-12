#!/usr/bin/env python3
"""
Neo4j Model Generator
A program that inherits from PostgreSQL Query Runner to get data and generate Neo4j models using MCP.

Usage:
    python src/neo4j_model_generator.py config/config_boomer_model.yml trending output/data/neo4j_model_<timestamp>.json
"""

import sys
import logging
import json
import subprocess
import tempfile
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import argparse
from pathlib import Path

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

# Extended error codes for Neo4j functionality
class Neo4jErrorCodes:
    MCP_CONNECTION_ERROR = "ERR_N001"
    MCP_EXECUTION_ERROR = "ERR_N002"
    DATA_PROCESSING_ERROR = "ERR_N003"
    MODEL_GENERATION_ERROR = "ERR_N004"
    JSON_SERIALIZATION_ERROR = "ERR_N005"
    TIMESTAMP_GENERATION_ERROR = "ERR_N006"
    MCP_TOOL_NOT_AVAILABLE = "ERR_N007"


class Neo4jModelGenerator(PostgresQueryRunner):
    """
    Neo4j Model Generator that extends PostgreSQL Query Runner.
    
    This class inherits from PostgresQueryRunner to fetch data from PostgreSQL
    and then uses MCP Neo4j data modeling to generate Neo4j graph models.
    """
    
    def __init__(self):
        """Initialize the Neo4j Model Generator with enhanced logging."""
        super().__init__()
        self._setup_enhanced_logging()
        logger.info("Neo4j Model Generator initialized with enhanced logging")
    
    def _setup_enhanced_logging(self):
        """Setup enhanced logging with file output to output/logs folder."""
        try:
            # Create output/logs directory if it doesn't exist
            logs_dir = Path("output/logs")
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate timestamp for log file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = f"neo4j_model_generator_{timestamp}.log"
            log_filepath = logs_dir / log_filename
            
            # Create file handler for detailed logging
            file_handler = logging.FileHandler(log_filepath, mode='w', encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            
            # Create detailed formatter for file logs
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            
            # Add file handler to logger
            logger.addHandler(file_handler)
            
            # Store log file path for reference
            self.log_file_path = str(log_filepath)
            
            logger.info(f"Enhanced logging initialized - log file: {self.log_file_path}")
            logger.info("=" * 80)
            logger.info("NEO4J MODEL GENERATOR - ENHANCED LOGGING SESSION STARTED")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.warning(f"Failed to setup enhanced logging: {str(e)}, continuing with console logging only")
    
    def generate_timestamp(self) -> str:
        """
        Generate timestamp for file naming.
        
        Returns:
            Timestamp string in format YYYYMMDD_HHMMSS
        """
        logger.info("Generating timestamp for file naming")
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            logger.info(f"Generated timestamp: {timestamp}")
            return timestamp
        except Exception as e:
            error_msg = f"{Neo4jErrorCodes.TIMESTAMP_GENERATION_ERROR}: Error generating timestamp: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    def prepare_data_for_modeling(self, results: List[tuple], column_names: List[str]) -> Dict[str, Any]:
        """
        Prepare PostgreSQL query results for Neo4j modeling.
        
        Args:
            results: Query results as list of tuples
            column_names: List of column names
            
        Returns:
            Dictionary containing structured data for modeling
        """
        try:
            if results is None or column_names is None:
                raise ValueError("Results and column_names cannot be None")
            
            logger.info(f"Preparing {len(results)} rows of data for Neo4j modeling")
            
            # Check if results is iterable
            if not hasattr(results, '__iter__'):
                raise ValueError("Results must be iterable")
                
            # Convert results to list of dictionaries
            data_records = []
            for row in results:
                record = {}
                for i, value in enumerate(row):
                    if i < len(column_names):
                        # Handle None values and convert to JSON-serializable types
                        if value is None:
                            record[column_names[i]] = None
                        elif isinstance(value, (str, int, float, bool)):
                            record[column_names[i]] = value
                        else:
                            # Convert other types to string
                            record[column_names[i]] = str(value)
                data_records.append(record)
            
            # Create structured data for modeling
            modeling_data = {
                "source": "postgresql",
                "table_info": {
                    "columns": column_names,
                    "row_count": len(results),
                    "sample_data": data_records[:5] if len(data_records) > 5 else data_records
                },
                "full_data": data_records,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "total_records": len(results),
                    "column_count": len(column_names)
                }
            }
            
            logger.info(f"Data prepared successfully with {len(data_records)} records")
            return modeling_data
            
        except Exception as e:
            error_msg = f"{Neo4jErrorCodes.DATA_PROCESSING_ERROR}: Error preparing data for modeling: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    def call_mcp_neo4j_modeling(self, data: Dict[str, Any], model_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Call MCP Neo4j data modeling service to generate graph model.
        
        Args:
            data: Structured data for modeling
            model_config: User-defined model configuration
            
        Returns:
            Neo4j model as dictionary (single clean model without duplication)
        """
        logger.info("Calling MCP Neo4j data modeling service")
        
        try:
            # Create temporary file with data
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(data, temp_file, indent=2)
                temp_file_path = temp_file.name
            
            try:
                # Determine which model generation approach to use
                if model_config:
                    logger.info("User configuration provided - generating configured model")
                    neo4j_model = self._generate_configured_neo4j_model(data, model_config)
                else:
                    logger.info("No user configuration - generating default model")
                    neo4j_model = self._generate_basic_neo4j_model(data)
                
                logger.info("MCP Neo4j modeling completed successfully")
                return neo4j_model
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except subprocess.CalledProcessError as e:
            error_msg = f"{Neo4jErrorCodes.MCP_EXECUTION_ERROR}: MCP service execution failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"{Neo4jErrorCodes.MCP_CONNECTION_ERROR}: Error calling MCP Neo4j modeling: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    def _generate_configured_neo4j_model(self, data: Dict[str, Any], model_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Neo4j model based on user configuration.
        
        Args:
            data: Structured data for modeling
            model_config: User-defined model configuration
            
        Returns:
            Configured Neo4j model structure
        """
        logger.info("🏗️  GENERATING CONFIGURED NEO4J MODEL")
        logger.info(f"Source data: {data['metadata']['total_records']} records from PostgreSQL")
        logger.info(f"Configuration sections: {list(model_config.keys())}")
        
        try:
            # Create model structure in chronological order
            from collections import OrderedDict
            model = OrderedDict([
                ("model_info", {
                    "generated_by": "Neo4j Model Generator (Configured)",
                    "generated_at": datetime.now().isoformat(),
                    "source_table_columns": data['table_info']['columns'],
                    "total_records": data['metadata']['total_records'],
                    "configuration_applied": True
                }),
                ("nodes", []),
                ("relationships", []),
                ("constraints", []),
                ("indexes", []),
                ("import_queries", [])
            ])
            
            # Filter columns if specified
            include_columns = model_config.get('include_columns', data['table_info']['columns'])
            filtered_columns = [col for col in data['table_info']['columns'] if col in include_columns]
            
            # Process node definitions
            logger.info("📊 Processing node definitions")
            if 'nodes' in model_config:
                for i, node_config in enumerate(model_config['nodes'], 1):
                    logger.info(f"   Creating node {i}/{len(model_config['nodes'])}: {node_config['label']}")
                    node = self._create_node_from_config(node_config, filtered_columns)
                    model['nodes'].append(node)
                    
                    # Log node properties
                    properties_count = len(node_config.get('properties', []))
                    logger.info(f"      Properties: {properties_count}")
                    
                    # Log chunking configuration if present
                    if node_config.get('chunking_enabled', False):
                        logger.info(f"      🧠 CHUNKING ENABLED: source field '{node_config.get('source_content_field')}'")
                        chunking_config = node_config.get('chunking_config', {})
                        logger.info(f"         Chunk size: {chunking_config.get('chunk_size', 'default')}")
                        logger.info(f"         Chunk overlap: {chunking_config.get('chunk_overlap', 'default')}")
                        logger.info(f"         Use LLM chunking: {chunking_config.get('use_llm_chunking', 'default')}")
                    
                    # Log vector properties
                    vector_props = [p for p in node_config.get('properties', []) if p.get('type') == 'vector']
                    if vector_props:
                        for prop in vector_props:
                            logger.info(f"      🔢 VECTOR PROPERTY: {prop['name']} (dim: {prop.get('vector_dimension', 'default')})")
                
                logger.info(f"✅ Created {len(model['nodes'])} node definitions")
            
            # Process constraints and indexes
            logger.info("🔒 Processing constraints and indexes")
            if 'nodes' in model_config:
                for node_config in model_config['nodes']:
                    # Create constraints for unique properties
                    for prop in node_config.get('properties', []):
                        if prop.get('unique', False):
                            constraint = self._create_constraint(node_config['label'], prop['name'])
                            model['constraints'].append(constraint)
                            logger.info(f"      Created constraint: {node_config['label']}.{prop['name']}")
                    
                    # Create indexes for indexed properties
                    for prop in node_config.get('properties', []):
                        if prop.get('indexed', False):
                            index = self._create_index(node_config['label'], prop['name'], prop.get('type', 'TEXT'))
                            model['indexes'].append(index)
                            logger.info(f"      Created index: {node_config['label']}.{prop['name']} ({prop.get('type', 'TEXT')})")
            
            # Process relationships
            logger.info("🔗 Processing relationships")
            if 'relationships' in model_config:
                for i, rel_config in enumerate(model_config['relationships'], 1):
                    logger.info(f"   Creating relationship {i}/{len(model_config['relationships'])}: {rel_config['type']}")
                    logger.info(f"      {rel_config['start_node']} → {rel_config['end_node']}")
                    relationship = self._create_relationship_from_config(rel_config)
                    model['relationships'].append(relationship)
                logger.info(f"✅ Created {len(model['relationships'])} relationship definitions")
            
            # Process extra indexes
            if 'extra_indexes' in model_config:
                for index_config in model_config['extra_indexes']:
                    # Pass vector-specific parameters if present
                    kwargs = {}
                    if 'vector_dimension' in index_config:
                        kwargs['vector_dimension'] = index_config['vector_dimension']
                    if 'vector_similarity' in index_config:
                        kwargs['vector_similarity'] = index_config['vector_similarity']
                    
                    index = self._create_index(
                        index_config['node_label'], 
                        index_config['property'], 
                        index_config.get('type', 'TEXT'),
                        **kwargs
                    )
                    model['indexes'].append(index)
            
            # Generate import queries
            model['import_queries'] = self._generate_import_queries(model_config, filtered_columns)
            
            logger.info(f"Generated configured Neo4j model with {len(model['nodes'])} nodes and {len(model['relationships'])} relationships")
            return model
            
        except Exception as e:
            error_msg = f"{Neo4jErrorCodes.MODEL_GENERATION_ERROR}: Error generating configured Neo4j model: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    def _create_node_from_config(self, node_config: Dict[str, Any], available_columns: List[str]) -> Dict[str, Any]:
        """Create node definition from configuration with enhanced chunking support."""
        node = {
            "label": node_config['label'],
            "node_id_property": node_config.get('node_id_property'),
            "properties": [],
            "description": f"Node representing {node_config['label']} entities"
        }
        
        # Add multiple labels if specified
        if 'multiple_labels' in node_config:
            node['multiple_labels'] = node_config['multiple_labels']
        
        # Add chunking configuration if this is a Chunk node
        if node_config.get('chunking_enabled', False):
            node['chunking_enabled'] = True
            node['source_content_field'] = node_config.get('source_content_field')
            if 'chunking_config' in node_config:
                node['chunking_config'] = node_config['chunking_config']
            logger.info(f"Enhanced {node_config['label']} node with chunking configuration")
        
        # Process properties
        for prop_config in node_config.get('properties', []):
            # Include all properties for chunk nodes, or properties that exist in available columns
            if (prop_config['name'] in available_columns or 
                prop_config.get('type') == 'vector' or 
                node_config.get('chunking_enabled', False)):
                
                prop = {
                    "name": prop_config['name'],
                    "type": prop_config.get('type', 'string')
                }
                
                if prop_config.get('unique', False):
                    prop['unique'] = True
                if prop_config.get('indexed', False):
                    prop['indexed'] = True
                if 'alias' in prop_config:
                    prop['alias'] = prop_config['alias']
                if 'default_value' in prop_config:
                    prop['default_value'] = prop_config['default_value']
                
                # Add vector-specific properties
                if prop_config.get('type') == 'vector':
                    if 'vector_dimension' in prop_config:
                        prop['vector_dimension'] = prop_config['vector_dimension']
                    if 'vector_similarity' in prop_config:
                        prop['vector_similarity'] = prop_config['vector_similarity']
                
                node['properties'].append(prop)
        
        return node
    
    def _create_relationship_from_config(self, rel_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create relationship definition from configuration with enhanced properties."""
        relationship = {
            "type": rel_config['type'],
            "start_node": rel_config['start_node'],
            "end_node": rel_config['end_node'],
            "start_property": rel_config['start_property'],
            "end_property": rel_config['end_property'],
            "properties": rel_config.get('properties', []),
            "description": rel_config.get('description', f"Relationship {rel_config['type']} from {rel_config['start_node']} to {rel_config['end_node']}")
        }
        
        # Add enhanced relationship properties
        if 'auto_generated' in rel_config:
            relationship['auto_generated'] = rel_config['auto_generated']
        
        return relationship
    
    def _create_constraint(self, node_label: str, property_name: str) -> Dict[str, Any]:
        """Create constraint definition."""
        return {
            "type": "UNIQUE",
            "node_label": node_label,
            "property": property_name,
            "cypher": f"CREATE CONSTRAINT {node_label.lower()}_{property_name}_unique IF NOT EXISTS FOR (n:{node_label}) REQUIRE n.{property_name} IS UNIQUE"
        }
    
    def _create_index(self, node_label: str, property_name: str, index_type: str = "TEXT", **kwargs) -> Dict[str, Any]:
        """Create index definition."""
        index_type_upper = index_type.upper()
        
        if index_type_upper == "VECTOR":
            # Vector index for embeddings
            vector_dimension = kwargs.get('vector_dimension', 1536)
            vector_similarity = kwargs.get('vector_similarity', 'cosine')
            cypher = f"CREATE VECTOR INDEX {node_label.lower()}_{property_name}_vector IF NOT EXISTS FOR (n:{node_label}) ON (n.{property_name}) OPTIONS {{indexConfig: {{`vector.dimensions`: {vector_dimension}, `vector.similarity_function`: '{vector_similarity}'}}}}"
            
            return {
                "type": index_type_upper,
                "node_label": node_label,
                "property": property_name,
                "vector_dimension": vector_dimension,
                "vector_similarity": vector_similarity,
                "cypher": cypher
            }
        elif index_type_upper in ["RANGE", "POINT"]:
            cypher = f"CREATE INDEX {node_label.lower()}_{property_name}_{index_type.lower()} IF NOT EXISTS FOR (n:{node_label}) ON (n.{property_name})"
        else:
            cypher = f"CREATE INDEX {node_label.lower()}_{property_name}_text IF NOT EXISTS FOR (n:{node_label}) ON (n.{property_name})"
        
        return {
            "type": index_type_upper,
            "node_label": node_label,
            "property": property_name,
            "cypher": cypher
        }
    
    def _generate_import_queries(self, model_config: Dict[str, Any], columns: List[str]) -> List[Dict[str, Any]]:
        """Generate Cypher import queries based on configuration and best practices."""
        queries = []
        best_practices = model_config.get('best_practices', {})
        
        # Check if we should use MERGE instead of CREATE
        use_merge_nodes = best_practices.get('use_merge_for_nodes', False)
        use_merge_relationships = best_practices.get('use_merge_for_relationships', False)
        merge_on_id_only = best_practices.get('node_creation', {}).get('merge_on_id_only', False)
        separate_set_properties = best_practices.get('node_creation', {}).get('separate_set_properties', False)
        use_unwind = best_practices.get('performance', {}).get('use_unwind_for_batch', False)
        batch_size = best_practices.get('performance', {}).get('batch_size', 1000)
        skip_null_properties = best_practices.get('data_integrity', {}).get('skip_null_properties', True)
        
        # Generate node creation queries
        if 'nodes' in model_config:
            for node_config in model_config['nodes']:
                node_id_property = node_config.get('node_id_property')
                
                # Get properties that exist in the data
                id_properties = []
                other_properties = []
                aliases = {}
                
                for prop_config in node_config.get('properties', []):
                    if prop_config['name'] in columns or prop_config.get('type') == 'vector':
                        prop_name = prop_config['name']
                        alias = prop_config.get('alias', prop_name)
                        property_clause = f"{alias}: row.{prop_name}"
                        
                        if alias != prop_name:
                            aliases[prop_name] = alias
                        
                        # Separate ID properties from other properties
                        if prop_name == node_id_property:
                            id_properties.append(property_clause)
                        else:
                            other_properties.append(property_clause)
                
                # Create labels
                labels = [node_config['label']]
                if 'multiple_labels' in node_config:
                    labels.extend(node_config['multiple_labels'])
                labels_str = ':'.join(labels)
                
                # Generate query based on best practices
                if use_merge_nodes and merge_on_id_only and separate_set_properties and id_properties:
                    # Best practice: MERGE on ID only, then SET other properties
                    id_props_str = ', '.join(id_properties)
                    other_props_str = ', '.join(other_properties)
                    
                    if use_unwind:
                        query = f"""
                        // Create {node_config['label']} nodes using MERGE with ID only (Best Practice)
                        LOAD CSV WITH HEADERS FROM 'file:///data.csv' AS row
                        WITH row WHERE row.{node_id_property} IS NOT NULL
                        MERGE (n:{node_config['label']} {{{id_props_str}}})"""
                        
                        if other_properties:
                            if skip_null_properties:
                                # Add conditional SET for each property to skip nulls
                                set_clauses = []
                                for prop_config in node_config.get('properties', []):
                                    if prop_config['name'] in columns and prop_config['name'] != node_id_property:
                                        prop_name = prop_config['name']
                                        alias = prop_config.get('alias', prop_name)
                                        set_clauses.append(f"n.{alias} = CASE WHEN row.{prop_name} IS NOT NULL THEN row.{prop_name} ELSE n.{alias} END")
                                
                                if set_clauses:
                                    query += f"\nSET {', '.join(set_clauses)}"
                            else:
                                query += f"\nSET {other_props_str}"
                        
                        # Add multiple labels if specified
                        if 'multiple_labels' in node_config:
                            additional_labels = ':'.join(node_config['multiple_labels'])
                            query += f"\nSET n:{additional_labels}"
                    else:
                        query = f"""
                        // Create {node_config['label']} nodes using MERGE with ID only (Best Practice)
                        LOAD CSV WITH HEADERS FROM 'file:///data.csv' AS row
                        WITH row WHERE row.{node_id_property} IS NOT NULL
                        MERGE (n:{node_config['label']} {{{id_props_str}}})"""
                        
                        if other_properties:
                            query += f"\nSET {other_props_str}"
                        
                        # Add multiple labels
                        if 'multiple_labels' in node_config:
                            additional_labels = ':'.join(node_config['multiple_labels'])
                            query += f"\nSET n:{additional_labels}"
                
                elif use_merge_nodes:
                    # Standard MERGE with all properties
                    all_properties = id_properties + other_properties
                    properties_str = ', '.join(all_properties)
                    
                    query = f"""
                    // Create {node_config['label']} nodes using MERGE
                    LOAD CSV WITH HEADERS FROM 'file:///data.csv' AS row
                    MERGE (n:{labels_str} {{{properties_str}}})
                    """
                else:
                    # Standard CREATE (original behavior)
                    all_properties = id_properties + other_properties
                    properties_str = ', '.join(all_properties)
                    
                    query = f"""
                    // Create {node_config['label']} nodes
                    LOAD CSV WITH HEADERS FROM 'file:///data.csv' AS row
                    CREATE (n:{labels_str} {{{properties_str}}})
                    """
                
                queries.append({
                    "description": f"Import {node_config['label']} nodes" + (" (Best Practice: MERGE)" if use_merge_nodes else ""),
                    "cypher": query.strip(),
                    "node_type": node_config['label'],
                    "uses_best_practices": use_merge_nodes
                })
        
        # Generate relationship creation queries
        if 'relationships' in model_config:
            for rel_config in model_config['relationships']:
                rel_properties = []
                for prop in rel_config.get('properties', []):
                    if prop['name'] in columns:
                        rel_properties.append(f"{prop['name']}: row.{prop['name']}")
                
                rel_props_str = ', '.join(rel_properties)
                
                if use_merge_relationships:
                    # Best practice: Use MERGE for relationships
                    if rel_properties:
                        query = f"""
                        // Create {rel_config['type']} relationships using MERGE (Best Practice)
                        LOAD CSV WITH HEADERS FROM 'file:///data.csv' AS row
                        MATCH (start:{rel_config['start_node']} {{{rel_config['start_property']}: row.{rel_config['start_property']}}})
                        MATCH (end:{rel_config['end_node']} {{{rel_config['end_property']}: row.{rel_config['end_property']}}})
                        MERGE (start)-[r:{rel_config['type']}]->(end)
                        SET {rel_props_str}
                        """
                    else:
                        query = f"""
                        // Create {rel_config['type']} relationships using MERGE (Best Practice)
                        LOAD CSV WITH HEADERS FROM 'file:///data.csv' AS row
                        MATCH (start:{rel_config['start_node']} {{{rel_config['start_property']}: row.{rel_config['start_property']}}})
                        MATCH (end:{rel_config['end_node']} {{{rel_config['end_property']}: row.{rel_config['end_property']}}})
                        MERGE (start)-[r:{rel_config['type']}]->(end)
                        """
                else:
                    # Standard CREATE for relationships
                    rel_props_clause = f" {{{rel_props_str}}}" if rel_props_str else ""
                    
                    query = f"""
                    // Create {rel_config['type']} relationships
                    LOAD CSV WITH HEADERS FROM 'file:///data.csv' AS row
                    MATCH (start:{rel_config['start_node']} {{{rel_config['start_property']}: row.{rel_config['start_property']}}})
                    MATCH (end:{rel_config['end_node']} {{{rel_config['end_property']}: row.{rel_config['end_property']}}})
                    CREATE (start)-[r:{rel_config['type']}{rel_props_clause}]->(end)
                    """
                
                queries.append({
                    "description": f"Create {rel_config['type']} relationships" + (" (Best Practice: MERGE)" if use_merge_relationships else ""),
                    "cypher": query.strip(),
                    "relationship_type": rel_config['type'],
                    "uses_best_practices": use_merge_relationships
                })
        
        return queries

    def _generate_basic_neo4j_model(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Neo4j model using MCP Neo4j data modeling server.
        
        Args:
            data: Structured data for modeling
            
        Returns:
            Neo4j model structure generated by MCP server
        """
        logger.info("🤖 Calling MCP Neo4j Data Modeling Server")
        
        try:
            # Create temporary file with data for MCP server
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(data, temp_file, indent=2)
                temp_file_path = temp_file.name
                logger.info(f"Created temporary data file: {temp_file_path}")
            
            try:
                # Call MCP Neo4j data modeling server via Docker
                logger.info("Executing MCP Neo4j data modeling via Docker container")
                
                # Start MCP server in stdio mode and communicate with it
                logger.info("Starting MCP Neo4j data modeling server in stdio mode")
                
                # Copy data file to container first
                copy_cmd = ["docker", "cp", temp_file_path, "mcp_neo4j_data_modeling:/tmp/data.json"]
                logger.info(f"Copying data to container: {' '.join(copy_cmd)}")
                
                copy_result = subprocess.run(copy_cmd, capture_output=True, text=True, timeout=30)
                if copy_result.returncode != 0:
                    logger.error(f"Failed to copy data to container: {copy_result.stderr}")
                    raise subprocess.CalledProcessError(copy_result.returncode, copy_cmd, copy_result.stderr)
                
                # Create MCP initialization request
                init_request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "neo4j-model-generator", "version": "1.0.0"}
                    }
                }
                
                # Try different possible tool names based on Neo4j data modeling
                possible_tools = [
                    "analyze_data_structure",
                    "generate_data_model", 
                    "create_neo4j_model",
                    "model_data",
                    "analyze_schema",
                    "generate_graph_model"
                ]
                
                # We'll try each tool name to see which one works
                modeling_requests = []
                for i, tool_name in enumerate(possible_tools, 2):
                    modeling_requests.append({
                        "jsonrpc": "2.0",
                        "id": i,
                        "method": "tools/call",
                        "params": {
                            "name": tool_name,
                            "arguments": {
                                "data": data,
                                "schema_analysis": True,
                                "neo4j_connection": {
                                    "uri": "bolt://neo4j:7687",
                                    "username": "neo4j",
                                    "password": "password123"
                                }
                            }
                        }
                    })
                
                # Start MCP server and send request
                docker_cmd = [
                    "docker", "exec", "-i", "mcp_neo4j_data_modeling",
                    "sh", "-c", "uvx mcp-neo4j-data-modeling --transport stdio"
                ]
                
                logger.info(f"Starting MCP server: {' '.join(docker_cmd)}")
                
                # Send JSON-RPC request to MCP server
                process = subprocess.Popen(
                    docker_cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Send initialization first, then try different tool calls
                all_requests = [init_request] + modeling_requests
                request_json = "\n".join([json.dumps(req) for req in all_requests]) + "\n"
                logger.info(f"Sending MCP requests: initialization and {len(modeling_requests)} tool attempts")
                logger.info(f"Trying tools: {possible_tools}")
                
                stdout, stderr = process.communicate(input=request_json, timeout=120)
                result_returncode = process.returncode
                
                if result_returncode != 0:
                    logger.error(f"MCP server execution failed: {stderr}")
                    logger.info("Falling back to basic model generation")
                    return self._generate_fallback_model(data)
                
                # Parse MCP server response
                logger.info("Parsing MCP server response")
                logger.info(f"Raw MCP stdout: {stdout}")
                logger.info(f"Raw MCP stderr: {stderr}")
                
                try:
                    # Parse all responses to find a successful one
                    lines = stdout.strip().split('\n')
                    successful_response = None
                    
                    for line in lines:
                        if line.strip().startswith('{'):
                            try:
                                response = json.loads(line.strip())
                                # Check if this is a successful tool call response
                                if 'result' in response and response.get('id', 0) > 1:  # Skip init response (id=1)
                                    successful_response = response
                                    tool_id = response.get('id', 0) - 2  # Adjust for init request
                                    if tool_id < len(possible_tools):
                                        logger.info(f"✅ Successfully called tool: {possible_tools[tool_id]}")
                                    break
                            except json.JSONDecodeError:
                                continue
                    
                    if successful_response and 'result' in successful_response:
                        model_data = successful_response['result']
                        # Enhance MCP response with metadata
                        enhanced_model = self._enhance_mcp_model(model_data, data)
                        logger.info(f"Generated MCP-powered Neo4j model with {len(enhanced_model.get('nodes', []))} nodes")
                        return enhanced_model
                    else:
                        logger.warning("No successful MCP tool calls found")
                        logger.info("All attempted tools failed, checking responses:")
                        for line in lines:
                            if line.strip().startswith('{'):
                                try:
                                    response = json.loads(line.strip())
                                    if 'error' in response:
                                        logger.info(f"Tool call error (id={response.get('id')}): {response['error']['message']}")
                                except json.JSONDecodeError:
                                    continue
                        logger.info("Falling back to basic model generation")
                        return self._generate_fallback_model(data)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse MCP response as JSON: {str(e)}")
                    logger.info(f"Raw MCP output: {stdout}")
                    logger.info("Falling back to basic model generation")
                    return self._generate_fallback_model(data)
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    logger.info("Cleaned up temporary data file")
                    
        except subprocess.TimeoutExpired:
            error_msg = f"{Neo4jErrorCodes.MCP_EXECUTION_ERROR}: MCP server execution timed out"
            logger.error(error_msg)
            logger.info("Falling back to basic model generation")
            return self._generate_fallback_model(data)
        except Exception as e:
            error_msg = f"{Neo4jErrorCodes.MCP_CONNECTION_ERROR}: Error calling MCP Neo4j modeling server: {str(e)}"
            logger.error(error_msg)
            logger.info("Falling back to basic model generation")
            return self._generate_fallback_model(data)
    
    def _enhance_mcp_model(self, mcp_response: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance MCP server response with additional metadata and structure.
        
        Args:
            mcp_response: Response from MCP server
            data: Original data for context
            
        Returns:
            Enhanced Neo4j model
        """
        logger.info("Enhancing MCP model with metadata")
        
        from collections import OrderedDict
        enhanced_model = OrderedDict([
            ("model_info", {
                "generated_by": "Neo4j Model Generator (MCP-Powered)",
                "generated_at": datetime.now().isoformat(),
                "source_table_columns": data['table_info']['columns'],
                "total_records": data['metadata']['total_records'],
                "configuration_applied": False,
                "mcp_server_used": True
            }),
            ("nodes", mcp_response.get('nodes', [])),
            ("relationships", mcp_response.get('relationships', [])),
            ("constraints", mcp_response.get('constraints', [])),
            ("indexes", mcp_response.get('indexes', [])),
            ("import_queries", mcp_response.get('import_queries', []))
        ])
        
        logger.info("MCP model enhanced successfully")
        return enhanced_model
    
    def _generate_fallback_model(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate fallback model when MCP server is unavailable.
        
        Args:
            data: Structured data for modeling
            
        Returns:
            Basic fallback Neo4j model structure
        """
        logger.info("Generating fallback Neo4j model structure")
        
        try:
            columns = data['table_info']['columns']
            
            # Analyze columns to suggest node structure
            id_columns = [col for col in columns if 'id' in col.lower()]
            text_columns = [col for col in columns if any(keyword in col.lower() 
                          for keyword in ['title', 'name', 'content', 'description', 'text'])]
            date_columns = [col for col in columns if any(keyword in col.lower() 
                          for keyword in ['date', 'time', 'created', 'updated'])]
            url_columns = [col for col in columns if 'url' in col.lower()]
            
            # Generate basic model with chronological ordering
            from collections import OrderedDict
            model = OrderedDict([
                ("model_info", {
                    "generated_by": "Neo4j Model Generator (Fallback)",
                    "generated_at": datetime.now().isoformat(),
                    "source_table_columns": columns,
                    "total_records": data['metadata']['total_records'],
                    "configuration_applied": False,
                    "mcp_server_used": False,
                    "fallback_reason": "MCP server unavailable"
                }),
                ("nodes", []),
                ("relationships", []),
                ("constraints", []),
                ("indexes", []),
                ("import_queries", [])
            ])
            
            # Suggest primary node based on data structure
            primary_node = "Content" if text_columns else "Record"
            
            node_properties = []
            for col in columns:
                if col in id_columns:
                    node_properties.append({"name": col, "type": "string", "unique": True})
                elif col in text_columns:
                    node_properties.append({"name": col, "type": "string", "indexed": True})
                elif col in date_columns:
                    node_properties.append({"name": col, "type": "datetime"})
                elif col in url_columns:
                    node_properties.append({"name": col, "type": "string"})
                else:
                    node_properties.append({"name": col, "type": "string"})
            
            model["nodes"].append({
                "label": primary_node,
                "properties": node_properties,
                "description": f"Primary node representing records from PostgreSQL table"
            })
            
            # Add constraints for ID fields
            for id_col in id_columns:
                model["constraints"].append({
                    "type": "UNIQUE",
                    "node_label": primary_node,
                    "property": id_col,
                    "cypher": f"CREATE CONSTRAINT {primary_node.lower()}_{id_col}_unique IF NOT EXISTS FOR (n:{primary_node}) REQUIRE n.{id_col} IS UNIQUE"
                })
            
            # Add indexes for text fields
            for text_col in text_columns:
                model["indexes"].append({
                    "type": "TEXT",
                    "node_label": primary_node,
                    "property": text_col,
                    "cypher": f"CREATE INDEX {primary_node.lower()}_{text_col}_text IF NOT EXISTS FOR (n:{primary_node}) ON (n.{text_col})"
                })
            
            # Generate import query
            properties_str = ", ".join([f"{col}: row.{col}" for col in columns])
            import_query = f"""
            // Import data from CSV
            LOAD CSV WITH HEADERS FROM 'file:///data.csv' AS row
            CREATE (n:{primary_node} {{{properties_str}}})
            """
            
            model["import_queries"].append({
                "description": "Basic import from CSV",
                "cypher": import_query.strip()
            })
            
            logger.info(f"Generated fallback Neo4j model with {len(model['nodes'])} nodes")
            return model
            
        except Exception as e:
            error_msg = f"{Neo4jErrorCodes.MODEL_GENERATION_ERROR}: Error generating fallback Neo4j model: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    def save_neo4j_model(self, model: Dict[str, Any], output_file: str) -> None:
        """
        Save Neo4j model to JSON file.
        
        Args:
            model: Neo4j model dictionary
            output_file: Path to output file
        """
        logger.info(f"Saving Neo4j model to file: {output_file}")
        
        try:
            # Create output directory if it doesn't exist
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as file:
                json.dump(model, file, indent=2, ensure_ascii=False)
            
            logger.info(f"Neo4j model successfully saved to {output_file}")
            
        except (TypeError, ValueError) as e:
            error_msg = f"{Neo4jErrorCodes.JSON_SERIALIZATION_ERROR}: Error serializing model to JSON: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
        except IOError as e:
            error_msg = f"{BaseErrorCodes.FILE_WRITE_ERROR}: Error writing model file {output_file}: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"{Neo4jErrorCodes.JSON_SERIALIZATION_ERROR}: Unexpected error saving model: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    def get_model_config(self, config: Dict[str, Any], query_name: str) -> Optional[Dict[str, Any]]:
        """
        Get Neo4j model configuration for the specified query.
        
        Args:
            config: Full configuration dictionary
            query_name: Name of the query
            
        Returns:
            Model configuration if found and valid, None otherwise
        """
        logger.info(f"Looking for Neo4j model configuration for query: {query_name}")
        
        try:
            if 'neo4j_model_config' in config and query_name in config['neo4j_model_config']:
                model_config = config['neo4j_model_config'][query_name]
                
                # Validate that the model configuration has required structure
                if self._validate_model_config(model_config):
                    logger.info(f"Found valid model configuration for query: {query_name}")
                    return model_config
                else:
                    logger.warning(f"Model configuration for query '{query_name}' is invalid, using default model")
                    return None
            else:
                logger.info(f"No specific model configuration found for query: {query_name}, using default model")
                return None
        except Exception as e:
            logger.warning(f"Error retrieving model configuration: {str(e)}, using default model")
            return None
    
    def _validate_model_config(self, model_config: Dict[str, Any]) -> bool:
        """
        Validate that the model configuration has the required structure.
        
        Args:
            model_config: Model configuration to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check if it has nodes definition
            if 'nodes' not in model_config:
                logger.warning("Model configuration missing 'nodes' section")
                return False
            
            # Check if nodes is a list and not empty
            if not isinstance(model_config['nodes'], list) or len(model_config['nodes']) == 0:
                logger.warning("Model configuration 'nodes' must be a non-empty list")
                return False
            
            # Validate each node has required fields
            for i, node in enumerate(model_config['nodes']):
                if not isinstance(node, dict):
                    logger.warning(f"Node {i} must be a dictionary")
                    return False
                
                if 'label' not in node:
                    logger.warning(f"Node {i} missing required 'label' field")
                    return False
                
                if 'node_id_property' not in node:
                    logger.warning(f"Node {i} missing required 'node_id_property' field")
                    return False
            
            logger.info("Model configuration validation passed")
            return True
            
        except Exception as e:
            logger.warning(f"Error validating model configuration: {str(e)}")
            return False
    
    def _clean_model_output(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean the model output to ensure no duplicate sections and proper chronological ordering.
        
        Args:
            model: Raw model dictionary
            
        Returns:
            Cleaned model dictionary with sections in logical chronological order
        """
        logger.info("Cleaning model output to remove duplicates and ensure chronological ordering")
        
        try:
            # Define the sections in proper chronological order
            ordered_sections = [
                'model_info',      # 1. Metadata about the model
                'nodes',           # 2. Node definitions (core structure)
                'relationships',   # 3. Relationship definitions (core structure)
                'constraints',     # 4. Database constraints (schema)
                'indexes',         # 5. Database indexes (schema)
                'import_queries'   # 6. Import queries (implementation)
            ]
            
            # Create clean model with sections in chronological order
            cleaned_model = {}
            for section in ordered_sections:
                if section in model and model[section]:  # Only include non-empty sections
                    cleaned_model[section] = model[section]
            
            # Log what was cleaned and reordered
            removed_sections = set(model.keys()) - set(ordered_sections)
            if removed_sections:
                logger.info(f"Removed duplicate/unnecessary sections: {', '.join(removed_sections)}")
            
            # Log the final section order
            included_sections = list(cleaned_model.keys())
            logger.info(f"Model sections in chronological order: {' → '.join(included_sections)}")
            
            # Validate the cleaned model has essential sections
            essential_sections = ['model_info', 'nodes']
            missing_sections = [section for section in essential_sections if section not in cleaned_model]
            if missing_sections:
                logger.warning(f"Cleaned model missing essential sections: {', '.join(missing_sections)}")
            
            logger.info(f"Model cleaned and ordered successfully - contains {len(cleaned_model.get('nodes', []))} nodes, {len(cleaned_model.get('relationships', []))} relationships")
            return cleaned_model
            
        except Exception as e:
            logger.warning(f"Error cleaning model output: {str(e)}, returning original model")
            return model

    def generate_neo4j_model_from_query(self, config_path: str, query_name: str, output_file: str) -> None:
        """
        Main function to generate Neo4j model from PostgreSQL query results.
        
        Args:
            config_path: Path to configuration file
            query_name: Name of query to execute
            output_file: Path to output JSON file
        """
        logger.info("=" * 80)
        logger.info(f"STARTING NEO4J MODEL GENERATION")
        logger.info(f"Query: {query_name}")
        logger.info(f"Config: {config_path}")
        logger.info(f"Output: {output_file}")
        logger.info("=" * 80)
        
        try:
            # Load configuration
            logger.info("STEP 1: Loading configuration")
            config = load_config(config_path)
            logger.info(f"Configuration sections found: {list(config.keys())}")
            
            # Check if postgres config exists
            if 'database' not in config or 'postgres' not in config['database']:
                raise Exception(f"{BaseErrorCodes.MISSING_DB_CONFIG}: PostgreSQL configuration not found in config file")
            
            # Parse database configuration
            logger.info("STEP 2: Parsing database configuration")
            postgres_config_str = config['database']['postgres']
            db_config = parse_postgres_config(postgres_config_str)
            logger.info(f"PostgreSQL connection: {db_config['host']}:{db_config['port']}/{db_config['database']}")
            
            # Get query
            logger.info("STEP 3: Retrieving query")
            query = get_query_from_config(config, query_name)
            logger.info(f"Query retrieved: {query[:100]}{'...' if len(query) > 100 else ''}")
            
            # Get model configuration
            logger.info("STEP 4: Analyzing model configuration")
            model_config = self.get_model_config(config, query_name)
            
            # Log which model type will be generated
            if model_config:
                logger.info(f"✅ CONFIGURED MODEL will be used for query '{query_name}'")
                logger.info(f"Configuration includes {len(model_config.get('nodes', []))} node types")
                logger.info(f"Configuration includes {len(model_config.get('relationships', []))} relationship types")
                
                # Log chunking configuration if present
                chunking_nodes = [node for node in model_config.get('nodes', []) if node.get('chunking_enabled', False)]
                if chunking_nodes:
                    logger.info(f"🧠 CHUNKING ENABLED for {len(chunking_nodes)} node type(s)")
                    for node in chunking_nodes:
                        logger.info(f"   - {node['label']} will chunk field '{node.get('source_content_field')}'")
            else:
                logger.info(f"⚠️  DEFAULT MODEL will be generated for query '{query_name}' (no configuration found)")
            
            # Execute query using parent class functionality
            logger.info("STEP 5: Executing PostgreSQL query")
            with self.get_db_connection(db_config) as connection:
                results, column_names = self.execute_query(connection, query)
            logger.info(f"Query executed successfully: {len(results)} rows, {len(column_names)} columns")
            logger.info(f"Columns: {', '.join(column_names)}")
            
            # Prepare data for modeling
            logger.info("STEP 6: Preparing data for modeling")
            modeling_data = self.prepare_data_for_modeling(results, column_names)
            logger.info(f"Data prepared: {modeling_data['metadata']['total_records']} records")
            
            # Generate Neo4j model - either configured or default, but never both
            logger.info("STEP 7: Generating Neo4j model")
            neo4j_model = self.call_mcp_neo4j_modeling(modeling_data, model_config)
            logger.info(f"Model generated with {len(neo4j_model.get('nodes', []))} nodes, {len(neo4j_model.get('relationships', []))} relationships")
            
            # Validate and clean the model before saving
            logger.info("STEP 8: Cleaning and validating model")
            cleaned_model = self._clean_model_output(neo4j_model)
            
            # Save model to file
            logger.info("STEP 9: Saving model to file")
            self.save_neo4j_model(cleaned_model, output_file)
            
            logger.info("=" * 80)
            logger.info("✅ NEO4J MODEL GENERATION COMPLETED SUCCESSFULLY")
            logger.info(f"📁 Model saved to: {output_file}")
            logger.info(f"📋 Log file: {getattr(self, 'log_file_path', 'console only')}")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error("=" * 80)
            logger.error("❌ NEO4J MODEL GENERATION FAILED")
            logger.error(f"Error: {str(e)}")
            logger.error("=" * 80)
            raise


def main():
    """Main entry point for command line usage."""
    parser = argparse.ArgumentParser(description='Neo4j Model Generator')
    parser.add_argument('config_file', help='Path to configuration YAML file')
    parser.add_argument('query_name', help='Name of query to execute')
    parser.add_argument('output_file', help='Path to output JSON file')
    
    args = parser.parse_args()
    
    try:
        generator = Neo4jModelGenerator()
        generator.generate_neo4j_model_from_query(args.config_file, args.query_name, args.output_file)
        print(f"Neo4j model generated successfully. Results saved to {args.output_file}")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()