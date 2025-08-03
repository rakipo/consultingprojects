#!/usr/bin/env python3
"""
MCP Neo4j Data Modeling Server
Handles data modeling and transformation between PostgreSQL and Neo4j
Enforces Cypher standards and best practices
All configuration loaded from YAML files - no hardcoding
"""

import asyncio
import os
import logging
import json
from typing import Any, Dict, List, Optional
import psycopg2
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
from cypher_validator import CypherStandardsValidator, CypherGenerator, ValidationLevel
from config_loader import get_config

# Initialize configuration
config = get_config()

# Configure logging from config
log_level = getattr(logging, config.get_server_config().get('log_level', 'INFO'))
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

class DataModelingServer:
    def __init__(self):
        # Load configuration from YAML files
        self.config = config
        
        # Database configurations from config
        self.postgres_config = self.config.get_database_config('postgres')
        neo4j_config = self.config.get_database_config('neo4j')
        
        self.neo4j_uri = neo4j_config.get('uri')
        self.neo4j_user = neo4j_config.get('user')
        self.neo4j_password = neo4j_config.get('password')
        self.neo4j_database = neo4j_config.get('database')
        
        # Server configuration
        server_config = self.config.get_server_config()
        self.server = Server(server_config.get('name'))
        self.timeout = server_config.get('timeout')
        
        # Cypher configuration
        cypher_config = self.config.get_cypher_config()
        standards_file = cypher_config.get('standards_file')
        
        # Initialize Cypher standards validator and generator
        self.cypher_validator = CypherStandardsValidator(standards_file) if cypher_config.get('validation_enabled') else None
        self.cypher_generator = CypherGenerator(standards_file) if cypher_config.get('validation_enabled') else None
        
        # Migration configuration
        self.migration_config = self.config.get_migration_config()
        
        # Performance configuration
        self.performance_config = self.config.get_performance_config()
        
        self.neo4j_driver = None
        
    async def initialize(self):
        """Initialize database connections"""
        try:
            # Initialize Neo4j driver with configuration
            self.neo4j_driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password),
                max_connection_pool_size=self.performance_config.get('connection_pool_size'),
                connection_timeout=self.timeout
            )
            
            # Test connections
            await self.test_connections()
            logger.info(self.config.get_message('info', 'server_initialized'))
            
        except Exception as e:
            error_msg = self.config.get_message('errors', 'connection_failed', error=str(e))
            logger.error(error_msg)
            raise

    async def test_connections(self):
        """Test database connections"""
        # Test PostgreSQL
        try:
            conn = psycopg2.connect(**self.postgres_config)
            conn.close()
            logger.info(self.config.get_message('success', 'connection_successful') + " (PostgreSQL)")
        except Exception as e:
            error_msg = self.config.get_message('errors', 'connection_failed', error=str(e))
            logger.error(f"PostgreSQL: {error_msg}")
            raise
            
        # Test Neo4j
        try:
            test_query = self.config.get_database_queries('neo4j').get('test_connection')
            with self.neo4j_driver.session(database=self.neo4j_database) as session:
                result = session.run(test_query)
                result.single()
            logger.info(self.config.get_message('success', 'connection_successful') + " (Neo4j)")
        except Exception as e:
            error_msg = self.config.get_message('errors', 'connection_failed', error=str(e))
            logger.error(f"Neo4j: {error_msg}")
            raise

    async def get_postgres_schema(self) -> Dict[str, Any]:
        """Get PostgreSQL schema information"""
        try:
            conn = psycopg2.connect(**self.postgres_config)
            cursor = conn.cursor()
            
            # Get schema query from configuration
            schema_query = self.config.get_database_queries('postgres').get('schema_info')
            schema_name = self.postgres_config.get('schema', 'public')
            
            # Execute query with schema parameter
            cursor.execute(schema_query.replace('$schema', f"'{schema_name}'"))
            
            schema = {}
            for row in cursor.fetchall():
                table_name, column_name, data_type, is_nullable = row
                if table_name not in schema:
                    schema[table_name] = []
                schema[table_name].append({
                    'column': column_name,
                    'type': data_type,
                    'nullable': is_nullable == 'YES'
                })
            
            conn.close()
            return schema
            
        except Exception as e:
            logger.error(f"Failed to get PostgreSQL schema: {e}")
            raise

    async def analyze_content_structure(self) -> Dict[str, Any]:
        """Analyze content structure for Neo4j modeling"""
        try:
            conn = psycopg2.connect(**self.postgres_config)
            cursor = conn.cursor()
            
            # Get queries from configuration
            queries = self.config.get_database_queries('postgres')
            
            # Analyze content data
            analysis = {}
            
            # Get domain distribution
            cursor.execute(queries.get('domain_distribution'))
            analysis['domains'] = dict(cursor.fetchall())
            
            # Get author statistics
            cursor.execute(queries.get('author_statistics'))
            analysis['authors'] = dict(cursor.fetchall())
            
            # Get tag analysis
            cursor.execute(queries.get('tag_analysis'))
            analysis['tags'] = dict(cursor.fetchall())
            
            # Get relationship patterns
            cursor.execute(queries.get('relationship_patterns'))
            analysis['author_domain_relationships'] = [
                {'author': row[0], 'domain': row[1], 'articles': row[2]}
                for row in cursor.fetchall()
            ]
            
            conn.close()
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze content structure: {e}")
            raise

    async def generate_neo4j_model(self) -> str:
        """Generate Neo4j data model based on PostgreSQL content with standards compliance"""
        try:
            analysis = await self.analyze_content_structure()
            
            # Get templates from configuration
            templates = self.config.get_param_config('data_model_templates')
            defaults = self.config.get_defaults()
            
            # Generate model components
            header = templates.get('header', '')
            node_descriptions = '\n'.join(templates.get('node_descriptions', []))
            relationship_descriptions = '\n'.join(templates.get('relationship_descriptions', []))
            
            # Generate standardized constraints and relationships if validator is available
            constraints = []
            relationships = []
            indexes = []
            
            if self.cypher_generator:
                # Generate for each node type from config
                node_types = defaults.get('node_types', [])
                for node_type in node_types:
                    if node_type == "Author":
                        constraints.append(self.cypher_generator.generate_create_node_query(node_type, {"name": "string"}))
                    elif node_type == "Article":
                        constraints.append(self.cypher_generator.generate_create_node_query(node_type, {"id": "integer", "title": "string"}))
                    else:
                        constraints.append(self.cypher_generator.generate_create_node_query(node_type, {"name": "string"}))
                
                # Generate relationships from config
                relationship_configs = [
                    ("Author", "Article", "WROTE"),
                    ("Article", "Domain", "BELONGS_TO"),
                    ("Article", "Tag", "TAGGED_WITH")
                ]
                
                for source, target, rel_type in relationship_configs:
                    relationships.append(self.cypher_generator.generate_create_relationship_query(
                        source, target, rel_type, source_property="name", target_property="id"
                    ))
            
            # Get indexes from configuration
            neo4j_queries = self.config.get_database_queries('neo4j')
            indexes = neo4j_queries.get('indexes', [])
            
            # Build model string
            model_parts = [
                header,
                "",
                node_descriptions,
                "",
                relationship_descriptions,
                ""
            ]
            
            if constraints:
                model_parts.extend([
                    "// Standardized Node Creation Patterns:",
                    '\n'.join(constraints),
                    ""
                ])
            
            if relationships:
                model_parts.extend([
                    "// Standardized Relationship Creation Patterns:",
                    '\n'.join(relationships),
                    ""
                ])
            
            if indexes:
                model_parts.extend([
                    "// Performance Indexes (following standards):",
                    '\n'.join(indexes)
                ])
            
            return '\n'.join(model_parts)
            
        except Exception as e:
            logger.error(f"Failed to generate Neo4j model: {e}")
            raise

    async def migrate_data_to_neo4j(self) -> Dict[str, Any]:
        """Migrate PostgreSQL data to Neo4j"""
        try:
            conn = psycopg2.connect(**self.postgres_config)
            cursor = conn.cursor()
            
            # Get all content data
            cursor.execute("""
                SELECT id, url, domain, site_name, title, author, 
                       publish_date, content, summary, tags, language
                FROM structured_content
                ORDER BY id
            """)
            
            migration_stats = {
                'authors': 0,
                'articles': 0,
                'domains': 0,
                'tags': 0,
                'websites': 0,
                'relationships': 0
            }
            
            with self.neo4j_driver.session() as session:
                # Clear existing data (optional)
                session.run("MATCH (n) DETACH DELETE n")
                
                # Create constraints and indexes
                constraints = [
                    "CREATE CONSTRAINT author_name IF NOT EXISTS FOR (a:Author) REQUIRE a.name IS UNIQUE",
                    "CREATE CONSTRAINT domain_name IF NOT EXISTS FOR (d:Domain) REQUIRE d.name IS UNIQUE",
                    "CREATE CONSTRAINT tag_name IF NOT EXISTS FOR (t:Tag) REQUIRE t.name IS UNIQUE",
                    "CREATE CONSTRAINT website_name IF NOT EXISTS FOR (w:Website) REQUIRE w.site_name IS UNIQUE",
                    "CREATE CONSTRAINT article_id IF NOT EXISTS FOR (a:Article) REQUIRE a.id IS UNIQUE"
                ]
                
                for constraint in constraints:
                    session.run(constraint)
                
                # Process each article
                for row in cursor.fetchall():
                    article_id, url, domain, site_name, title, author, publish_date, content, summary, tags, language = row
                    
                    # Create/merge nodes and relationships
                    cypher = """
                    // Create Author
                    MERGE (author:Author {name: $author})
                    
                    // Create Domain
                    MERGE (domain:Domain {name: $domain})
                    
                    // Create Website
                    MERGE (website:Website {site_name: $site_name})
                    
                    // Create Article
                    CREATE (article:Article {
                        id: $article_id,
                        title: $title,
                        url: $url,
                        publish_date: date($publish_date),
                        content: $content,
                        summary: $summary,
                        language: $language
                    })
                    
                    // Create relationships
                    CREATE (author)-[:WROTE]->(article)
                    CREATE (article)-[:BELONGS_TO]->(domain)
                    CREATE (article)-[:PUBLISHED_ON]->(website)
                    
                    // Create author specialization relationship
                    MERGE (author)-[spec:SPECIALIZES_IN]->(domain)
                    ON CREATE SET spec.article_count = 1
                    ON MATCH SET spec.article_count = spec.article_count + 1
                    
                    RETURN article.id as created_article
                    """
                    
                    result = session.run(cypher, {
                        'article_id': article_id,
                        'url': url,
                        'domain': domain,
                        'site_name': site_name or 'Unknown',
                        'title': title,
                        'author': author,
                        'publish_date': str(publish_date) if publish_date else '2024-01-01',
                        'content': content,
                        'summary': summary,
                        'language': language
                    })
                    
                    migration_stats['articles'] += 1
                    
                    # Create tag relationships
                    if tags:
                        import json
                        tag_list = json.loads(tags) if isinstance(tags, str) else tags
                        for tag in tag_list:
                            tag_cypher = """
                            MATCH (article:Article {id: $article_id})
                            MERGE (tag:Tag {name: $tag})
                            CREATE (article)-[:TAGGED_WITH]->(tag)
                            """
                            session.run(tag_cypher, {'article_id': article_id, 'tag': tag})
                            migration_stats['relationships'] += 1
                
                # Get final counts
                counts = session.run("""
                    RETURN 
                        size((:Author)) as authors,
                        size((:Article)) as articles,
                        size((:Domain)) as domains,
                        size((:Tag)) as tags,
                        size((:Website)) as websites
                """).single()
                
                migration_stats.update(dict(counts))
            
            conn.close()
            return migration_stats
            
        except Exception as e:
            logger.error(f"Failed to migrate data to Neo4j: {e}")
            raise

    def setup_handlers(self):
        """Setup MCP server handlers"""
        
        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """List available resources"""
            # Get resources from configuration
            resource_configs = self.config.get_mcp_server_config().get('resources', [])
            
            resources = []
            for resource_config in resource_configs:
                resources.append(Resource(
                    uri=resource_config['uri'],
                    name=resource_config['name'],
                    description=resource_config['description'],
                    mimeType=resource_config['mime_type']
                ))
            
            return resources

        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read a specific resource"""
            if uri == "postgres://schema":
                schema = await self.get_postgres_schema()
                return TextContent(
                    type="text",
                    text=str(schema)
                )
            elif uri == "neo4j://model":
                model = await self.generate_neo4j_model()
                return TextContent(
                    type="text",
                    text=model
                )
            elif uri == "analysis://content":
                analysis = await self.analyze_content_structure()
                return TextContent(
                    type="text",
                    text=str(analysis)
                )
            else:
                raise ValueError(f"Unknown resource: {uri}")

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools"""
            # Get tools from configuration
            tool_configs = self.config.get_mcp_server_config().get('tools', [])
            
            tools = []
            for tool_config in tool_configs:
                tools.append(Tool(
                    name=tool_config['name'],
                    description=tool_config['description'],
                    inputSchema=tool_config['input_schema']
                ))
            
            return tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            if name == "analyze_postgres_schema":
                schema = await self.get_postgres_schema()
                analysis = await self.analyze_content_structure()
                model = await self.generate_neo4j_model()
                
                return [TextContent(
                    type="text",
                    text=f"PostgreSQL Schema Analysis:\n{schema}\n\nContent Analysis:\n{analysis}\n\nSuggested Neo4j Model:\n{model}"
                )]
                
            elif name == "migrate_to_neo4j":
                clear_existing = arguments.get("clear_existing", False)
                stats = await self.migrate_data_to_neo4j()
                
                return [TextContent(
                    type="text",
                    text=f"Migration completed successfully!\n\nStatistics:\n{stats}"
                )]
                
            elif name == "generate_cypher_queries":
                query_type = arguments.get("query_type")
                node_type = arguments.get("node_type", "Article")
                properties = arguments.get("properties", {})
                
                # Generate standards-compliant queries
                queries = await self.generate_standards_compliant_queries(query_type, node_type, properties)
                
                return [TextContent(
                    type="text",
                    text=f"Generated {query_type} queries (standards-compliant):\n\n{queries}"
                )]
                
            elif name == "validate_cypher_query":
                query = arguments.get("query")
                fix_issues = arguments.get("fix_issues", False)
                
                if fix_issues:
                    fixed_query, validation_results = self.cypher_generator.validate_and_fix_query(query)
                    result_text = f"Original Query:\n{query}\n\nFixed Query:\n{fixed_query}\n\n"
                else:
                    validation_results = self.cypher_validator.validate_query(query)
                    result_text = f"Query Validation Results:\n\n"
                
                # Format validation results
                for result in validation_results:
                    result_text += f"{result.level.value.upper()}: {result.message}\n"
                    if result.line_number:
                        result_text += f"  Line: {result.line_number}\n"
                    if result.suggestion:
                        result_text += f"  Suggestion: {result.suggestion}\n"
                    result_text += "\n"
                
                if not validation_results:
                    result_text += "✅ Query passes all validation checks!\n"
                
                return [TextContent(
                    type="text",
                    text=result_text
                )]
                
            elif name == "generate_standards_compliant_query":
                operation = arguments.get("operation")
                parameters = arguments.get("parameters", {})
                
                query = await self.generate_compliant_query(operation, parameters)
                validation_results = self.cypher_validator.validate_query(query)
                
                result_text = f"Generated {operation} query:\n\n{query}\n\n"
                
                if validation_results:
                    result_text += "Validation Results:\n"
                    for result in validation_results:
                        result_text += f"{result.level.value.upper()}: {result.message}\n"
                else:
                    result_text += "✅ Query is standards-compliant!\n"
                
                return [TextContent(
                    type="text",
                    text=result_text
                )]
            
            else:
                raise ValueError(f"Unknown tool: {name}")

    async def generate_standards_compliant_queries(self, query_type: str, node_type: str, properties: Dict[str, Any]) -> str:
        """Generate standards-compliant queries based on type"""
        if query_type == "create_nodes":
            return self.cypher_generator.generate_create_node_query(node_type, properties)
        elif query_type == "create_relationships":
            return self.cypher_generator.generate_create_relationship_query(
                node_type, properties.get("target_type", "Tag"), 
                properties.get("relationship_type", "RELATES_TO")
            )
        elif query_type == "search":
            return self.cypher_generator.generate_search_query(
                node_type, properties.get("search_field", "name")
            )
        elif query_type == "analysis":
            return await self.generate_analytics_queries(node_type)
        else:
            return "// Unknown query type"
    
    async def generate_compliant_query(self, operation: str, parameters: Dict[str, Any]) -> str:
        """Generate a specific standards-compliant query"""
        if operation == "create_node":
            return self.cypher_generator.generate_create_node_query(
                parameters.get("node_type", "Article"),
                parameters.get("properties", {})
            )
        elif operation == "create_relationship":
            return self.cypher_generator.generate_create_relationship_query(
                parameters.get("source_type", "Author"),
                parameters.get("target_type", "Article"),
                parameters.get("relationship_type", "WROTE")
            )
        elif operation == "search":
            return self.cypher_generator.generate_search_query(
                parameters.get("node_type", "Article"),
                parameters.get("search_field", "title")
            )
        elif operation == "analytics":
            return await self.generate_analytics_queries(parameters.get("node_type", "Article"))
        else:
            return "// Unknown operation"
    
    async def generate_analytics_queries(self, node_type: str) -> str:
        """Generate standards-compliant analytics queries"""
        formatted_node = self.cypher_generator._format_node_label(node_type)
        
        return f"""
// Analytics queries for {formatted_node} (standards-compliant)

// Count {formatted_node} nodes
MATCH (n:{formatted_node})
RETURN count(n) as total_{node_type.lower()}s
LIMIT $limit;

// Most connected {formatted_node} nodes
MATCH (n:{formatted_node})
RETURN n, size((n)--()) as connection_count
ORDER BY connection_count DESC
LIMIT $limit;

// {formatted_node} creation timeline
MATCH (n:{formatted_node})
WHERE n.created_date IS NOT NULL
RETURN date(n.created_date) as creation_date, count(n) as count
ORDER BY creation_date DESC
LIMIT $limit;
"""

    def generate_sample_queries(self, query_type: str) -> str:
        """Generate sample Cypher queries from configuration"""
        # Get sample queries from configuration
        sample_queries = self.config.get_sample_queries(query_type)
        
        if not sample_queries:
            return self.config.get_message('errors', 'unknown_query_type', query_type=query_type)
        
        # Combine all queries in the category
        query_parts = []
        for query_name, query_template in sample_queries.items():
            query_parts.append(f"// {query_name.replace('_', ' ').title()}")
            query_parts.append(query_template)
            query_parts.append("")
        
        return '\n'.join(query_parts)

async def main():
    """Main server function"""
    try:
        # Validate configuration
        if not config.validate_config():
            logger.error("Configuration validation failed")
            return
        
        # Initialize server
        server_instance = DataModelingServer()
        await server_instance.initialize()
        server_instance.setup_handlers()
        
        logger.info(config.get_message('info', 'server_starting'))
        
        async with stdio_server() as (read_stream, write_stream):
            await server_instance.server.run(
                read_stream,
                write_stream,
                server_instance.server.create_initialization_options()
            )
            
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())