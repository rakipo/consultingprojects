"""
Cypher query generation and execution for MCP Vector Cypher Search.
"""

import logging
from typing import List, Dict, Any
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


class CypherGenerator:
    """Handles Cypher query generation and execution."""
    
    def __init__(self, config):
        """
        Initialize CypherGenerator.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self._neo4j_driver = None
    
    def get_neo4j_driver(self):
        """Get or initialize Neo4j driver."""
        if self._neo4j_driver is None:
            logger.info(f"Connecting to Neo4j at {self.config.neo4j_uri}")
            self._neo4j_driver = GraphDatabase.driver(
                self.config.neo4j_uri, 
                auth=(self.config.neo4j_user, self.config.neo4j_password)
            )
            logger.info("Neo4j driver initialized for Cypher operations")
        return self._neo4j_driver
    
    async def call_mcp_neo4j_cypher(self, question: str) -> str:
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
            cypher_query = self.generate_basic_cypher(question)
            
            logger.info("mcp-neo4j-cypher service completed")
            return cypher_query
            
        except Exception as e:
            logger.error(f"Error calling mcp-neo4j-cypher: {e}")
            return f"// Error generating Cypher query: {e}"
    
    def generate_basic_cypher(self, question: str) -> str:
        """
        Generate a basic Cypher query based on the question.
        This is a fallback implementation.
        
        Args:
            question: The input question
            
        Returns:
            Generated Cypher query string
        """
        question_lower = question.lower()
        
        if "count" in question_lower:
            return "MATCH (n) RETURN count(n) as total_nodes"
        elif "article" in question_lower or "content" in question_lower:
            return "MATCH (n:Article) RETURN n.title, n.content, n.url LIMIT 10"
        elif "user" in question_lower:
            return "MATCH (n:User) RETURN n.name, n.email LIMIT 10"
        elif "chunk" in question_lower:
            return "MATCH (n:Chunk) RETURN n.chunk_id, n.chunk_text, n.source_id LIMIT 10"
        else:
            return "MATCH (n) RETURN labels(n) as node_types, count(n) as count ORDER BY count DESC LIMIT 10"
    
    async def execute_cypher_query(self, cypher_query: str) -> List[Dict[str, Any]]:
        """
        Execute the Cypher query against Neo4j.
        
        Args:
            cypher_query: The Cypher query to execute
            
        Returns:
            Query results as list of dictionaries
        """
        if not cypher_query or cypher_query.startswith("//"):
            return []
        
        driver = self.get_neo4j_driver()
        
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
    
    def close(self):
        """Close connections and cleanup resources."""
        if self._neo4j_driver:
            self._neo4j_driver.close()
            self._neo4j_driver = None