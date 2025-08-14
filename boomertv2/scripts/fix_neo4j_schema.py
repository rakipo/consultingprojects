#!/usr/bin/env python3
"""
Fix Neo4j schema to match the model configuration.

This script:
1. Drops incorrect constraints and indexes
2. Creates the correct constraints and indexes as defined in the schema
3. Ensures alignment between the batch loader and Neo4j schema
"""

import logging
from neo4j import GraphDatabase
import json
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fix_neo4j_schema(neo4j_uri: str, username: str, password: str, model_path: str):
    """
    Fix Neo4j schema to match the model configuration.
    
    Args:
        neo4j_uri: Neo4j connection URI
        username: Neo4j username
        password: Neo4j password
        model_path: Path to the Neo4j model JSON file
    """
    
    # Load the model
    with open(model_path, 'r') as f:
        model = json.load(f)
    
    # Connect to Neo4j
    driver = GraphDatabase.driver(neo4j_uri, auth=(username, password))
    
    try:
        with driver.session() as session:
            logger.info("Starting Neo4j schema fix...")
            
            # Step 1: Drop incorrect constraints
            logger.info("Dropping incorrect constraints...")
            drop_queries = [
                "DROP CONSTRAINT article_url_unique IF EXISTS",
            ]
            
            for query in drop_queries:
                try:
                    session.run(query)
                    logger.info(f"Dropped: {query}")
                except Exception as e:
                    logger.warning(f"Failed to drop constraint: {e}")
            
            # Step 2: Create correct constraints from schema
            logger.info("Creating correct constraints from schema...")
            for constraint in model.get('constraints', []):
                cypher = constraint.get('cypher')
                if cypher:
                    try:
                        session.run(cypher)
                        logger.info(f"Created constraint: {constraint.get('node_label', '')}.{constraint.get('property', '')}")
                    except Exception as e:
                        logger.warning(f"Failed to create constraint: {e}")
            
            # Step 3: Create correct indexes from schema
            logger.info("Creating correct indexes from schema...")
            for index in model.get('indexes', []):
                cypher = index.get('cypher')
                if cypher:
                    try:
                        session.run(cypher)
                        logger.info(f"Created index: {index.get('node_label', '')}.{index.get('property', '')}")
                    except Exception as e:
                        logger.warning(f"Failed to create index: {e}")
            
            # Step 4: Verify the schema
            logger.info("Verifying schema...")
            
            # Check constraints
            result = session.run("SHOW CONSTRAINTS")
            constraints = list(result)
            logger.info(f"Current constraints: {len(constraints)}")
            for constraint in constraints:
                logger.info(f"  {constraint}")
            
            # Check indexes
            result = session.run("SHOW INDEXES")
            indexes = list(result)
            logger.info(f"Current indexes: {len(indexes)}")
            for index in indexes:
                logger.info(f"  {index}")
            
            logger.info("Schema fix completed successfully!")
            
    except Exception as e:
        logger.error(f"Error fixing schema: {e}")
        raise
    finally:
        driver.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix Neo4j schema to match model configuration")
    parser.add_argument("--uri", default="bolt://localhost:7687", help="Neo4j URI")
    parser.add_argument("--username", default="neo4j", help="Neo4j username")
    parser.add_argument("--password", default="password123", help="Neo4j password")
    parser.add_argument("--model", default="output/data/neo4j_model_load_schema.json", help="Path to model JSON file")
    
    args = parser.parse_args()
    
    fix_neo4j_schema(args.uri, args.username, args.password, args.model)
