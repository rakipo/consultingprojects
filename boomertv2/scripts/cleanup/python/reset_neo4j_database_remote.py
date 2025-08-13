#!/usr/bin/env python3
"""
Remote Neo4j Database Reset Script

This script connects to a remote Neo4j server and removes all data,
indexes, and constraints. It replicates the functionality of the
reset_neo4j_database_remote.sh shell script.

Usage:
    python reset_neo4j_database_remote.py [--config CONFIG_FILE] [--queries QUERIES_FILE]

Configuration:
    - Credentials are stored in config.yaml
    - Queries are stored in queries.yaml
"""

import argparse
import sys
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError, ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class Neo4jResetManager:
    """Manages Neo4j database reset operations."""
    
    def __init__(self, config: Dict[str, Any], queries: Dict[str, Any]):
        """Initialize the reset manager with configuration and queries."""
        self.config = config
        self.queries = queries
        self.driver = None
        self.uri = config.get('neo4j', {}).get('uri')
        self.username = config.get('neo4j', {}).get('username')
        self.password = config.get('neo4j', {}).get('password')
        self.database = config.get('neo4j', {}).get('database', 'neo4j')
        
        if not all([self.uri, self.username, self.password]):
            raise ValueError("Missing required Neo4j credentials in config")
    
    def connect(self) -> bool:
        """Establish connection to Neo4j database."""
        try:
            logger.info("🔗 Connecting to remote Neo4j server...")
            
            # Handle SSL certificate verification for remote connections
            if self.uri.startswith("bolt+s://"):
                # For remote SSL connections, we might need to disable certificate verification
                # This is a common issue with self-signed certificates or Azure Neo4j instances
                try:
                    # First try with default SSL settings
                    logger.info("Attempting SSL connection with default settings...")
                    self.driver = GraphDatabase.driver(
                        self.uri,
                        auth=(self.username, self.password)
                    )
                except Exception as ssl_error:
                    error_msg = str(ssl_error).lower()
                    logger.info(f"SSL connection error: {ssl_error}")
                    if any(keyword in error_msg for keyword in ["ssl", "certificate", "cert", "trust", "sslcertverificationerror"]):
                        logger.warning("SSL certificate verification failed, trying with relaxed SSL settings...")
                        # Try with relaxed SSL settings
                        self.driver = GraphDatabase.driver(
                            self.uri,
                            auth=(self.username, self.password),
                            encrypted=True,
                            trust="TRUST_ALL_CERTIFICATES"
                        )
                    else:
                        raise ssl_error
            else:
                # For non-SSL connections (bolt://)
                self.driver = GraphDatabase.driver(
                    self.uri,
                    auth=(self.username, self.password)
                )
            
            # Test connection
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 1 AS test")
                result.single()
            
            logger.info("✅ Successfully connected to Neo4j server")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j server: {e}")
            return False
    
    def disconnect(self):
        """Close the database connection."""
        if self.driver:
            self.driver.close()
            logger.info("🔌 Disconnected from Neo4j server")
    
    def execute_query(self, query: str, description: str) -> bool:
        """Execute a Cypher query and log the result."""
        try:
            logger.info(f"Executing: {description}")
            with self.driver.session(database=self.database) as session:
                result = session.run(query)
                # Consume the result to ensure it's executed
                list(result)
            logger.info(f"✅ {description} completed")
            return True
        except Exception as e:
            logger.error(f"❌ {description} failed: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test the database connection."""
        return self.execute_query("RETURN 1 AS test;", "Connection test")
    
    def clear_all_data(self) -> bool:
        """Clear all nodes and relationships from the database."""
        logger.info("1️⃣ Clearing all nodes and relationships...")
        
        # Delete all relationships first
        rel_query = self.queries.get('delete_relationships', """
        MATCH ()-[r]-()
        CALL {
          WITH r
          DELETE r
        } IN TRANSACTIONS OF 1000 ROWS;
        """)
        
        if not self.execute_query(rel_query, "Delete all relationships"):
            return False
        
        # Delete all nodes
        node_query = self.queries.get('delete_nodes', """
        MATCH (n)
        CALL {
          WITH n
          DELETE n
        } IN TRANSACTIONS OF 1000 ROWS;
        """)
        
        return self.execute_query(node_query, "Delete all nodes")
    
    def drop_indexes(self) -> bool:
        """Drop all custom indexes."""
        logger.info("2️⃣ Dropping all custom indexes...")
        
        # Try to drop indexes using APOC if available
        index_query = self.queries.get('drop_indexes', """
        SHOW INDEXES YIELD name, type
        WHERE type <> 'LOOKUP' AND NOT name STARTS WITH '__'
        WITH collect(name) AS indexNames
        UNWIND indexNames AS indexName
        CALL {
          WITH indexName
          EXECUTE 'DROP INDEX ' + indexName + ' IF EXISTS'
        }
        RETURN count(*) AS droppedIndexes;
        """)
        
        if not self.execute_query(index_query, "Drop custom indexes"):
            logger.info("Trying fallback method for dropping indexes...")
            return self._drop_indexes_fallback()
        
        return True
    
    def _drop_indexes_fallback(self) -> bool:
        """Fallback method to drop known common indexes."""
        fallback_indexes = self.queries.get('fallback_indexes', [
            "article_title_text",
            "article_content_text", 
            "article_publish_date_range",
            "article_id_text",
            "website_site_name_text",
            "website_domain_text",
            "chunk_embedding_vector",
            "chunk_embeddings"
        ])
        
        success = True
        for index_name in fallback_indexes:
            query = f"DROP INDEX {index_name} IF EXISTS;"
            if not self.execute_query(query, f"Drop {index_name} index"):
                success = False
        
        return success
    
    def drop_constraints(self) -> bool:
        """Drop all constraints."""
        logger.info("3️⃣ Dropping all constraints...")
        
        constraint_query = self.queries.get('drop_constraints', """
        SHOW CONSTRAINTS YIELD name
        WHERE NOT name STARTS WITH '__'
        WITH collect(name) AS constraintNames
        UNWIND constraintNames AS constraintName
        CALL {
          WITH constraintName
          EXECUTE 'DROP CONSTRAINT ' + constraintName + ' IF EXISTS'
        }
        RETURN count(*) AS droppedConstraints;
        """)
        
        if not self.execute_query(constraint_query, "Drop all constraints"):
            logger.info("Trying fallback method for dropping constraints...")
            return self._drop_constraints_fallback()
        
        return True
    
    def _drop_constraints_fallback(self) -> bool:
        """Fallback method to drop known common constraints."""
        fallback_constraints = self.queries.get('fallback_constraints', [
            "article_id_unique",
            "article_url_unique",
            "website_domain_unique",
            "author_name_unique",
            "chunk_chunk_id_unique"
        ])
        
        success = True
        for constraint_name in fallback_constraints:
            query = f"DROP CONSTRAINT {constraint_name} IF EXISTS;"
            if not self.execute_query(query, f"Drop {constraint_name} constraint"):
                success = False
        
        return success
    
    def verify_reset(self) -> Dict[str, int]:
        """Verify the reset by counting remaining data."""
        logger.info("4️⃣ Verification...")
        
        verification_queries = self.queries.get('verification', {})
        
        # Count remaining nodes
        node_count_query = verification_queries.get('count_nodes', "MATCH (n) RETURN count(n) AS count;")
        node_count = 0
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(node_count_query)
                node_count = result.single()['count']
        except Exception as e:
            logger.error(f"Failed to count nodes: {e}")
        
        # Count remaining relationships
        rel_count_query = verification_queries.get('count_relationships', "MATCH ()-[r]-() RETURN count(r) AS count;")
        rel_count = 0
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(rel_count_query)
                rel_count = result.single()['count']
        except Exception as e:
            logger.error(f"Failed to count relationships: {e}")
        
        logger.info(f"Remaining nodes: {node_count}")
        logger.info(f"Remaining relationships: {rel_count}")
        
        # Show remaining indexes
        logger.info("Remaining indexes:")
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run("SHOW INDEXES YIELD name, type RETURN name, type;")
                for record in result:
                    logger.info(f"  {record['name']} ({record['type']})")
        except Exception as e:
            logger.error(f"Could not retrieve indexes: {e}")
        
        # Show remaining constraints
        logger.info("Remaining constraints:")
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run("SHOW CONSTRAINTS YIELD name RETURN name;")
                for record in result:
                    logger.info(f"  {record['name']}")
        except Exception as e:
            logger.error(f"Could not retrieve constraints: {e}")
        
        return {'nodes': node_count, 'relationships': rel_count}
    
    def reset_database(self) -> bool:
        """Perform the complete database reset."""
        try:
            if not self.connect():
                return False
            
            if not self.test_connection():
                return False
            
            if not self.clear_all_data():
                return False
            
            if not self.drop_indexes():
                logger.warning("Failed to drop some indexes")
            
            if not self.drop_constraints():
                logger.warning("Failed to drop some constraints")
            
            counts = self.verify_reset()
            
            if counts['nodes'] == 0 and counts['relationships'] == 0:
                logger.info("🎉 Remote Neo4j database successfully reset!")
                logger.info("✅ Database is now empty and ready for fresh data")
            else:
                logger.warning("⚠️ Database reset completed, but some data may remain")
                logger.warning(f"   Nodes: {counts['nodes']}, Relationships: {counts['relationships']}")
            
            return True
            
        finally:
            self.disconnect()


def load_yaml_config(file_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {file_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing configuration file {file_path}: {e}")
        sys.exit(1)


def confirm_reset() -> bool:
    """Ask for user confirmation before resetting the database."""
    print("")
    print("⚠️  WARNING: This will permanently delete ALL data in the Neo4j database!")
    print("⚠️  This action cannot be undone!")
    print("")
    
    confirmation = input("Are you sure you want to clear the remote Neo4j database? (type 'RESET' to confirm): ")
    return confirmation == "RESET"


def show_usage():
    """Display usage information."""
    print("Remote Neo4j Database Reset Script")
    print("===================================")
    print("")
    print("Usage: python reset_neo4j_database_remote.py [OPTIONS]")
    print("")
    print("Options:")
    print("  --config CONFIG_FILE    Configuration file path (default: config.yaml)")
    print("  --queries QUERIES_FILE  Queries file path (default: queries.yaml)")
    print("  --help                  Show this help message")
    print("")
    print("Configuration files:")
    print("  - config.yaml: Contains Neo4j connection credentials")
    print("  - queries.yaml: Contains Cypher queries for reset operations")
    print("")
    print("Example:")
    print("  python reset_neo4j_database_remote.py --config my_config.yaml --queries my_queries.yaml")
    print("")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Reset a remote Neo4j database",
        add_help=False
    )
    parser.add_argument('--config', default='config.yaml', help='Configuration file path')
    parser.add_argument('--queries', default='queries.yaml', help='Queries file path')
    parser.add_argument('--help', action='store_true', help='Show help message')
    
    args = parser.parse_args()
    
    if args.help:
        show_usage()
        return
    
    # Get the directory of the script
    script_dir = Path(__file__).parent
    config_path = script_dir / args.config
    queries_path = script_dir / args.queries
    
    print("🔄 Remote Neo4j Database Reset Script")
    print("=====================================")
    print("")
    
    # Load configurations
    try:
        config = load_yaml_config(config_path)
        queries = load_yaml_config(queries_path)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Display connection info
    neo4j_config = config.get('neo4j', {})
    print("This will clear all data from the remote Neo4j database:")
    print(f"  URI: {neo4j_config.get('uri', 'Not set')}")
    print(f"  Database: {neo4j_config.get('database', 'neo4j')}")
    print(f"  Username: {neo4j_config.get('username', 'Not set')}")
    print("")
    
    # Ask for confirmation
    if not confirm_reset():
        print("❌ Reset cancelled.")
        return
    
    print("")
    print("🗑️ Starting remote Neo4j database reset...")
    print("")
    
    # Perform the reset
    try:
        reset_manager = Neo4jResetManager(config, queries)
        success = reset_manager.reset_database()
        
        if success:
            print("")
            print("Remote Neo4j server is ready to use.")
            print("You can now load fresh data using your data loader.")
            print("")
            print("To verify the reset:")
            print(f"  cypher-shell -a \"{neo4j_config.get('uri')}\" -u \"{neo4j_config.get('username')}\" -p \"{neo4j_config.get('password')}\" -d \"{neo4j_config.get('database', 'neo4j')}\" 'MATCH (n) RETURN count(n);'")
        else:
            print("❌ Database reset failed.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Unexpected error during reset: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
