#!/usr/bin/env python3
"""
MCP Neo4j Cypher Server
Handles Cypher query execution and Neo4j database operations
"""

import asyncio
import os
import logging
from typing import Any, Dict, List, Optional, Union
from neo4j import GraphDatabase
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CypherServer:
    def __init__(self):
        self.neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
        self.neo4j_password = os.getenv('NEO4J_PASSWORD', 'password123')
        
        self.neo4j_driver = None
        self.server = Server("mcp-neo4j-cypher")
        
    async def initialize(self):
        """Initialize Neo4j connection"""
        try:
            self.neo4j_driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            
            # Test connection
            await self.test_connection()
            logger.info("Cypher server initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize server: {e}")
            raise

    async def test_connection(self):
        """Test Neo4j connection"""
        try:
            with self.neo4j_driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            logger.info("Neo4j connection successful")
        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}")
            raise

    async def execute_cypher(self, query: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a Cypher query"""
        try:
            with self.neo4j_driver.session() as session:
                result = session.run(query, parameters or {})
                
                # Convert result to serializable format
                records = []
                for record in result:
                    record_dict = {}
                    for key in record.keys():
                        value = record[key]
                        # Handle Neo4j types
                        if hasattr(value, '__dict__'):
                            if hasattr(value, 'labels'):  # Node
                                record_dict[key] = {
                                    'type': 'node',
                                    'labels': list(value.labels),
                                    'properties': dict(value)
                                }
                            elif hasattr(value, 'type'):  # Relationship
                                record_dict[key] = {
                                    'type': 'relationship',
                                    'rel_type': value.type,
                                    'properties': dict(value)
                                }
                            else:
                                record_dict[key] = str(value)
                        else:
                            record_dict[key] = value
                    records.append(record_dict)
                
                return {
                    'success': True,
                    'records': records,
                    'summary': {
                        'query': query,
                        'parameters': parameters,
                        'records_available': len(records)
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to execute Cypher query: {e}")
            return {
                'success': False,
                'error': str(e),
                'query': query,
                'parameters': parameters
            }

    async def get_database_info(self) -> Dict[str, Any]:
        """Get Neo4j database information"""
        try:
            with self.neo4j_driver.session() as session:
                # Get node counts by label
                node_counts = {}
                labels_result = session.run("CALL db.labels()")
                for record in labels_result:
                    label = record['label']
                    count_result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                    node_counts[label] = count_result.single()['count']
                
                # Get relationship counts by type
                rel_counts = {}
                types_result = session.run("CALL db.relationshipTypes()")
                for record in types_result:
                    rel_type = record['relationshipType']
                    count_result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
                    rel_counts[rel_type] = count_result.single()['count']
                
                # Get constraints
                constraints_result = session.run("SHOW CONSTRAINTS")
                constraints = [dict(record) for record in constraints_result]
                
                # Get indexes
                indexes_result = session.run("SHOW INDEXES")
                indexes = [dict(record) for record in indexes_result]
                
                return {
                    'node_counts': node_counts,
                    'relationship_counts': rel_counts,
                    'constraints': constraints,
                    'indexes': indexes,
                    'total_nodes': sum(node_counts.values()),
                    'total_relationships': sum(rel_counts.values())
                }
                
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {'error': str(e)}

    async def get_sample_data(self, limit: int = 10) -> Dict[str, Any]:
        """Get sample data from the database"""
        try:
            with self.neo4j_driver.session() as session:
                # Sample nodes
                nodes_query = f"MATCH (n) RETURN n LIMIT {limit}"
                nodes_result = session.run(nodes_query)
                nodes = []
                for record in nodes_result:
                    node = record['n']
                    nodes.append({
                        'labels': list(node.labels),
                        'properties': dict(node)
                    })
                
                # Sample relationships
                rels_query = f"MATCH ()-[r]->() RETURN r LIMIT {limit}"
                rels_result = session.run(rels_query)
                relationships = []
                for record in rels_result:
                    rel = record['r']
                    relationships.append({
                        'type': rel.type,
                        'properties': dict(rel)
                    })
                
                return {
                    'sample_nodes': nodes,
                    'sample_relationships': relationships
                }
                
        except Exception as e:
            logger.error(f"Failed to get sample data: {e}")
            return {'error': str(e)}

    def get_query_templates(self) -> Dict[str, str]:
        """Get common Cypher query templates"""
        return {
            'find_all_authors': """
                MATCH (a:Author)
                RETURN a.name, a.specialization
                ORDER BY a.name
            """,
            'find_articles_by_author': """
                MATCH (a:Author {name: $author_name})-[:WROTE]->(article:Article)
                RETURN article.title, article.publish_date, article.summary
                ORDER BY article.publish_date DESC
            """,
            'find_articles_by_domain': """
                MATCH (d:Domain {name: $domain_name})<-[:BELONGS_TO]-(article:Article)
                RETURN article.title, article.author, article.publish_date
                ORDER BY article.publish_date DESC
            """,
            'find_articles_by_tag': """
                MATCH (t:Tag {name: $tag_name})<-[:TAGGED_WITH]-(article:Article)
                RETURN article.title, article.author, article.domain
                ORDER BY article.title
            """,
            'find_related_articles': """
                MATCH (article1:Article {title: $article_title})-[:TAGGED_WITH]->(tag:Tag)<-[:TAGGED_WITH]-(article2:Article)
                WHERE article1 <> article2
                RETURN article2.title, article2.author, collect(tag.name) as shared_tags
                ORDER BY size(shared_tags) DESC
            """,
            'author_collaboration_network': """
                MATCH (a1:Author)-[:WROTE]->(article1:Article)-[:BELONGS_TO]->(d:Domain)<-[:BELONGS_TO]-(article2:Article)<-[:WROTE]-(a2:Author)
                WHERE a1 <> a2
                RETURN a1.name, a2.name, d.name, count(*) as shared_articles
                ORDER BY shared_articles DESC
            """,
            'domain_tag_analysis': """
                MATCH (d:Domain)<-[:BELONGS_TO]-(article:Article)-[:TAGGED_WITH]->(t:Tag)
                RETURN d.name as domain, t.name as tag, count(article) as article_count
                ORDER BY domain, article_count DESC
            """,
            'most_productive_authors': """
                MATCH (a:Author)-[:WROTE]->(article:Article)
                RETURN a.name, count(article) as article_count, 
                       collect(DISTINCT article.domain)[0..5] as domains
                ORDER BY article_count DESC
            """,
            'recent_articles': """
                MATCH (article:Article)
                WHERE article.publish_date >= date($start_date)
                RETURN article.title, article.author, article.domain, article.publish_date
                ORDER BY article.publish_date DESC
                LIMIT $limit
            """,
            'full_text_search': """
                MATCH (article:Article)
                WHERE article.title CONTAINS $search_term 
                   OR article.content CONTAINS $search_term
                   OR article.summary CONTAINS $search_term
                RETURN article.title, article.author, article.domain, article.summary
                ORDER BY article.publish_date DESC
            """
        }

    def setup_handlers(self):
        """Setup MCP server handlers"""
        
        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """List available resources"""
            return [
                Resource(
                    uri="neo4j://database-info",
                    name="Database Information",
                    description="Neo4j database schema and statistics",
                    mimeType="application/json"
                ),
                Resource(
                    uri="neo4j://sample-data",
                    name="Sample Data",
                    description="Sample nodes and relationships from the database",
                    mimeType="application/json"
                ),
                Resource(
                    uri="cypher://templates",
                    name="Query Templates",
                    description="Common Cypher query templates",
                    mimeType="application/json"
                )
            ]

        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read a specific resource"""
            if uri == "neo4j://database-info":
                info = await self.get_database_info()
                return TextContent(
                    type="text",
                    text=str(info)
                )
            elif uri == "neo4j://sample-data":
                data = await self.get_sample_data()
                return TextContent(
                    type="text",
                    text=str(data)
                )
            elif uri == "cypher://templates":
                templates = self.get_query_templates()
                return TextContent(
                    type="text",
                    text=str(templates)
                )
            else:
                raise ValueError(f"Unknown resource: {uri}")

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="execute_cypher",
                    description="Execute a Cypher query against Neo4j database",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Cypher query to execute"
                            },
                            "parameters": {
                                "type": "object",
                                "description": "Query parameters",
                                "default": {}
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_database_schema",
                    description="Get Neo4j database schema information",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="search_articles",
                    description="Search articles by various criteria",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "search_type": {
                                "type": "string",
                                "enum": ["author", "domain", "tag", "keyword", "recent"],
                                "description": "Type of search to perform"
                            },
                            "search_value": {
                                "type": "string",
                                "description": "Search term or value"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "default": 10
                            }
                        },
                        "required": ["search_type", "search_value"]
                    }
                ),
                Tool(
                    name="analyze_relationships",
                    description="Analyze relationships and patterns in the data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "analysis_type": {
                                "type": "string",
                                "enum": ["author_collaboration", "domain_distribution", "tag_analysis", "productivity"],
                                "description": "Type of analysis to perform"
                            }
                        },
                        "required": ["analysis_type"]
                    }
                ),
                Tool(
                    name="get_query_template",
                    description="Get a pre-built Cypher query template",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "template_name": {
                                "type": "string",
                                "description": "Name of the query template"
                            }
                        },
                        "required": ["template_name"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            if name == "execute_cypher":
                query = arguments.get("query")
                parameters = arguments.get("parameters", {})
                result = await self.execute_cypher(query, parameters)
                
                return [TextContent(
                    type="text",
                    text=f"Query Result:\n{result}"
                )]
                
            elif name == "get_database_schema":
                info = await self.get_database_info()
                
                return [TextContent(
                    type="text",
                    text=f"Database Schema Information:\n{info}"
                )]
                
            elif name == "search_articles":
                search_type = arguments.get("search_type")
                search_value = arguments.get("search_value")
                limit = arguments.get("limit", 10)
                
                templates = self.get_query_templates()
                
                if search_type == "author":
                    query = templates["find_articles_by_author"]
                    params = {"author_name": search_value}
                elif search_type == "domain":
                    query = templates["find_articles_by_domain"]
                    params = {"domain_name": search_value}
                elif search_type == "tag":
                    query = templates["find_articles_by_tag"]
                    params = {"tag_name": search_value}
                elif search_type == "keyword":
                    query = templates["full_text_search"]
                    params = {"search_term": search_value}
                elif search_type == "recent":
                    query = templates["recent_articles"]
                    params = {"start_date": search_value, "limit": limit}
                else:
                    return [TextContent(
                        type="text",
                        text=f"Unknown search type: {search_type}"
                    )]
                
                result = await self.execute_cypher(query, params)
                
                return [TextContent(
                    type="text",
                    text=f"Search Results ({search_type}: {search_value}):\n{result}"
                )]
                
            elif name == "analyze_relationships":
                analysis_type = arguments.get("analysis_type")
                templates = self.get_query_templates()
                
                if analysis_type == "author_collaboration":
                    query = templates["author_collaboration_network"]
                elif analysis_type == "domain_distribution":
                    query = templates["domain_tag_analysis"]
                elif analysis_type == "tag_analysis":
                    query = templates["domain_tag_analysis"]
                elif analysis_type == "productivity":
                    query = templates["most_productive_authors"]
                else:
                    return [TextContent(
                        type="text",
                        text=f"Unknown analysis type: {analysis_type}"
                    )]
                
                result = await self.execute_cypher(query)
                
                return [TextContent(
                    type="text",
                    text=f"Analysis Results ({analysis_type}):\n{result}"
                )]
                
            elif name == "get_query_template":
                template_name = arguments.get("template_name")
                templates = self.get_query_templates()
                
                if template_name in templates:
                    template = templates[template_name]
                    return [TextContent(
                        type="text",
                        text=f"Query Template '{template_name}':\n\n{template}"
                    )]
                else:
                    available = list(templates.keys())
                    return [TextContent(
                        type="text",
                        text=f"Template '{template_name}' not found. Available templates: {available}"
                    )]
            
            else:
                raise ValueError(f"Unknown tool: {name}")

async def main():
    """Main server function"""
    server_instance = CypherServer()
    await server_instance.initialize()
    server_instance.setup_handlers()
    
    logger.info("Starting MCP Neo4j Cypher Server...")
    
    async with stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream,
            write_stream,
            server_instance.server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())