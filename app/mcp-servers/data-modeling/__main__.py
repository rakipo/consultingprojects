#!/usr/bin/env python3
"""
MCP Neo4j Data Modeling Server
Handles data modeling and transformation between PostgreSQL and Neo4j
"""

import asyncio
import os
import logging
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataModelingServer:
    def __init__(self):
        self.postgres_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'database': os.getenv('POSTGRES_DB', 'movies'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', 'password123')
        }
        
        self.neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
        self.neo4j_password = os.getenv('NEO4J_PASSWORD', 'password123')
        
        self.neo4j_driver = None
        self.server = Server("mcp-neo4j-data-modeling")
        
    async def initialize(self):
        """Initialize database connections"""
        try:
            # Initialize Neo4j driver
            self.neo4j_driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            
            # Test connections
            await self.test_connections()
            logger.info("Data modeling server initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize server: {e}")
            raise

    async def test_connections(self):
        """Test database connections"""
        # Test PostgreSQL
        try:
            conn = psycopg2.connect(**self.postgres_config)
            conn.close()
            logger.info("PostgreSQL connection successful")
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            raise
            
        # Test Neo4j
        try:
            with self.neo4j_driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            logger.info("Neo4j connection successful")
        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}")
            raise

    async def get_postgres_schema(self) -> Dict[str, Any]:
        """Get PostgreSQL schema information"""
        try:
            conn = psycopg2.connect(**self.postgres_config)
            cursor = conn.cursor()
            
            # Get table information
            cursor.execute("""
                SELECT table_name, column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
            """)
            
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
            
            # Analyze content data
            analysis = {}
            
            # Get domain distribution
            cursor.execute("SELECT domain, COUNT(*) FROM structured_content GROUP BY domain")
            analysis['domains'] = dict(cursor.fetchall())
            
            # Get author statistics
            cursor.execute("SELECT author, COUNT(*) FROM structured_content GROUP BY author")
            analysis['authors'] = dict(cursor.fetchall())
            
            # Get tag analysis
            cursor.execute("""
                SELECT tag, COUNT(*) as count
                FROM structured_content,
                     jsonb_array_elements_text(tags) as tag
                GROUP BY tag
                ORDER BY count DESC
            """)
            analysis['tags'] = dict(cursor.fetchall())
            
            # Get relationship patterns
            cursor.execute("""
                SELECT author, domain, COUNT(*) as articles
                FROM structured_content
                GROUP BY author, domain
                ORDER BY articles DESC
            """)
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
        """Generate Neo4j data model based on PostgreSQL content"""
        try:
            analysis = await self.analyze_content_structure()
            
            model = """
// Neo4j Data Model for Content Management System

// Node Labels:
// - Author: Content creators
// - Article: Individual publications
// - Domain: Content categories
// - Tag: Content tags
// - Website: Source websites

// Relationships:
// - (Author)-[:WROTE]->(Article)
// - (Article)-[:BELONGS_TO]->(Domain)
// - (Article)-[:TAGGED_WITH]->(Tag)
// - (Article)-[:PUBLISHED_ON]->(Website)
// - (Author)-[:SPECIALIZES_IN]->(Domain)
// - (Tag)-[:RELATED_TO]->(Domain)

// Sample Cypher Queries:

// Create Author nodes
CREATE CONSTRAINT author_name IF NOT EXISTS FOR (a:Author) REQUIRE a.name IS UNIQUE;

// Create Domain nodes
CREATE CONSTRAINT domain_name IF NOT EXISTS FOR (d:Domain) REQUIRE d.name IS UNIQUE;

// Create Tag nodes
CREATE CONSTRAINT tag_name IF NOT EXISTS FOR (t:Tag) REQUIRE t.name IS UNIQUE;

// Create Website nodes
CREATE CONSTRAINT website_url IF NOT EXISTS FOR (w:Website) REQUIRE w.site_name IS UNIQUE;

// Create Article nodes
CREATE CONSTRAINT article_id IF NOT EXISTS FOR (a:Article) REQUIRE a.id IS UNIQUE;

// Indexes for performance
CREATE INDEX article_title IF NOT EXISTS FOR (a:Article) ON (a.title);
CREATE INDEX article_publish_date IF NOT EXISTS FOR (a:Article) ON (a.publish_date);
CREATE INDEX author_specialization IF NOT EXISTS FOR ()-[r:SPECIALIZES_IN]-() ON (r.article_count);
"""
            
            return model
            
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
            return [
                Resource(
                    uri="postgres://schema",
                    name="PostgreSQL Schema",
                    description="Current PostgreSQL database schema",
                    mimeType="application/json"
                ),
                Resource(
                    uri="neo4j://model",
                    name="Neo4j Data Model",
                    description="Generated Neo4j data model",
                    mimeType="text/plain"
                ),
                Resource(
                    uri="analysis://content",
                    name="Content Analysis",
                    description="Analysis of content structure and relationships",
                    mimeType="application/json"
                )
            ]

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
            return [
                Tool(
                    name="analyze_postgres_schema",
                    description="Analyze PostgreSQL schema and suggest Neo4j model",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="migrate_to_neo4j",
                    description="Migrate data from PostgreSQL to Neo4j",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "clear_existing": {
                                "type": "boolean",
                                "description": "Clear existing Neo4j data before migration",
                                "default": False
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="generate_cypher_queries",
                    description="Generate Cypher queries for common operations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query_type": {
                                "type": "string",
                                "enum": ["create_nodes", "create_relationships", "analysis", "search"],
                                "description": "Type of queries to generate"
                            }
                        },
                        "required": ["query_type"]
                    }
                )
            ]

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
                # Generate different types of queries based on request
                queries = self.generate_sample_queries(query_type)
                
                return [TextContent(
                    type="text",
                    text=f"Generated {query_type} queries:\n\n{queries}"
                )]
            
            else:
                raise ValueError(f"Unknown tool: {name}")

    def generate_sample_queries(self, query_type: str) -> str:
        """Generate sample Cypher queries"""
        if query_type == "create_nodes":
            return """
// Create Author nodes
MERGE (a:Author {name: "Dr. Sarah Chen"})
SET a.specialization = "Healthcare/AI"

// Create Domain nodes
MERGE (d:Domain {name: "Healthcare"})
SET d.description = "Medical and health-related content"

// Create Tag nodes
MERGE (t:Tag {name: "AI"})
SET t.category = "Technology"
"""
        elif query_type == "create_relationships":
            return """
// Author writes articles
MATCH (author:Author {name: "Dr. Sarah Chen"})
MATCH (article:Article {title: "AI-Powered Medical Diagnosis Revolution"})
CREATE (author)-[:WROTE {date: date("2024-12-15")}]->(article)

// Articles belong to domains
MATCH (article:Article)
MATCH (domain:Domain {name: "Healthcare"})
WHERE article.title CONTAINS "medical" OR article.title CONTAINS "health"
CREATE (article)-[:BELONGS_TO]->(domain)
"""
        elif query_type == "analysis":
            return """
// Most productive authors
MATCH (a:Author)-[:WROTE]->(article:Article)
RETURN a.name, count(article) as article_count
ORDER BY article_count DESC

// Domain distribution
MATCH (d:Domain)<-[:BELONGS_TO]-(article:Article)
RETURN d.name, count(article) as article_count
ORDER BY article_count DESC

// Author specializations
MATCH (a:Author)-[s:SPECIALIZES_IN]->(d:Domain)
RETURN a.name, d.name, s.article_count
ORDER BY s.article_count DESC
"""
        elif query_type == "search":
            return """
// Find articles by keyword
MATCH (article:Article)
WHERE article.title CONTAINS "AI" OR article.content CONTAINS "artificial intelligence"
RETURN article.title, article.author, article.publish_date

// Find related articles through tags
MATCH (article1:Article)-[:TAGGED_WITH]->(tag:Tag)<-[:TAGGED_WITH]-(article2:Article)
WHERE article1.title = "AI-Powered Medical Diagnosis Revolution"
AND article1 <> article2
RETURN article2.title, article2.author, collect(tag.name) as shared_tags

// Find author collaborations (articles in same domain)
MATCH (a1:Author)-[:WROTE]->(article1:Article)-[:BELONGS_TO]->(d:Domain)<-[:BELONGS_TO]-(article2:Article)<-[:WROTE]-(a2:Author)
WHERE a1 <> a2
RETURN a1.name, a2.name, d.name, count(*) as shared_domain_articles
ORDER BY shared_domain_articles DESC
"""
        else:
            return "// Unknown query type"

async def main():
    """Main server function"""
    server_instance = DataModelingServer()
    await server_instance.initialize()
    server_instance.setup_handlers()
    
    logger.info("Starting MCP Neo4j Data Modeling Server...")
    
    async with stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream,
            write_stream,
            server_instance.server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())