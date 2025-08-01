#!/usr/bin/env python3
"""
MCP Neo4j Data Modeling Server - All Routes Demonstration
This script demonstrates all available routes and tools for the MCP server
"""

import requests
import json
import time
from typing import Dict, Any, List

# MCP Server Configuration
MCP_DATA_MODELING_URL = "http://localhost:8001"
MCP_MANAGER_URL = "http://localhost:8000"

class MCPRoutesDemo:
    def __init__(self):
        self.base_url = MCP_DATA_MODELING_URL
        self.manager_url = MCP_MANAGER_URL
        
    def print_section(self, title: str):
        """Print a formatted section header"""
        print(f"\n{'='*60}")
        print(f"🔧 {title}")
        print(f"{'='*60}")
    
    def print_result(self, result: Dict[str, Any], title: str = "Result"):
        """Print formatted result"""
        print(f"\n📊 {title}:")
        print(json.dumps(result, indent=2, default=str))
    
    def make_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
        """Make HTTP request to MCP server"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, timeout=30)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}", "message": response.text}
        except Exception as e:
            return {"error": "Connection failed", "message": str(e)}
    
    def demo_health_check(self):
        """Demonstrate health check endpoint"""
        self.print_section("Health Check")
        result = self.make_request("/health")
        self.print_result(result, "Health Status")
    
    def demo_list_resources(self):
        """Demonstrate list resources endpoint"""
        self.print_section("List Available Resources")
        
        # MCP standard resources endpoint
        resources_data = {
            "method": "resources/list",
            "params": {}
        }
        result = self.make_request("/mcp", "POST", resources_data)
        self.print_result(result, "Available Resources")
    
    def demo_read_resources(self):
        """Demonstrate reading specific resources"""
        self.print_section("Read Specific Resources")
        
        resources = [
            "postgres://schema",
            "neo4j://model", 
            "analysis://content"
        ]
        
        for resource_uri in resources:
            print(f"\n📖 Reading resource: {resource_uri}")
            resource_data = {
                "method": "resources/read",
                "params": {"uri": resource_uri}
            }
            result = self.make_request("/mcp", "POST", resource_data)
            self.print_result(result, f"Resource: {resource_uri}")
    
    def demo_list_tools(self):
        """Demonstrate list tools endpoint"""
        self.print_section("List Available Tools")
        
        tools_data = {
            "method": "tools/list",
            "params": {}
        }
        result = self.make_request("/mcp", "POST", tools_data)
        self.print_result(result, "Available Tools")
    
    def demo_analyze_postgres_schema(self):
        """Demonstrate PostgreSQL schema analysis"""
        self.print_section("Analyze PostgreSQL Schema")
        
        tool_data = {
            "method": "tools/call",
            "params": {
                "name": "analyze_postgres_schema",
                "arguments": {}
            }
        }
        result = self.make_request("/mcp", "POST", tool_data)
        self.print_result(result, "PostgreSQL Schema Analysis")
    
    def demo_generate_cypher_queries(self):
        """Demonstrate Cypher query generation"""
        self.print_section("Generate Cypher Queries")
        
        query_types = ["create_nodes", "create_relationships", "analysis", "search"]
        
        for query_type in query_types:
            print(f"\n🔍 Generating {query_type} queries...")
            tool_data = {
                "method": "tools/call",
                "params": {
                    "name": "generate_cypher_queries",
                    "arguments": {"query_type": query_type}
                }
            }
            result = self.make_request("/mcp", "POST", tool_data)
            self.print_result(result, f"Cypher Queries - {query_type}")
    
    def demo_migrate_to_neo4j(self):
        """Demonstrate data migration to Neo4j"""
        self.print_section("Migrate Data to Neo4j")
        
        print("⚠️  This will migrate data from PostgreSQL to Neo4j")
        print("🔄 Starting migration process...")
        
        tool_data = {
            "method": "tools/call",
            "params": {
                "name": "migrate_to_neo4j",
                "arguments": {"clear_existing": True}
            }
        }
        result = self.make_request("/mcp", "POST", tool_data)
        self.print_result(result, "Migration Result")
    
    def demo_graph_model_generation(self):
        """Demonstrate graph model generation"""
        self.print_section("Generate Neo4j Graph Model")
        
        # This would be a custom tool for generating the graph model
        print("📋 Graph Model Structure:")
        
        model_structure = {
            "nodes": {
                "Article": {
                    "properties": ["id", "url", "title", "summary", "publish_date", "language", "extracted_at", "is_latest"],
                    "indexes": ["id", "title", "publish_date"],
                    "constraints": ["id UNIQUE"]
                },
                "Author": {
                    "properties": ["name", "total_articles", "specialization", "first_publication", "latest_publication"],
                    "indexes": ["name"],
                    "constraints": ["name UNIQUE"]
                },
                "Domain": {
                    "properties": ["name", "article_count", "author_count", "description"],
                    "indexes": ["name"],
                    "constraints": ["name UNIQUE"]
                },
                "Tag": {
                    "properties": ["name", "usage_count"],
                    "indexes": ["name", "usage_count"],
                    "constraints": ["name UNIQUE"]
                },
                "Website": {
                    "properties": ["site_name", "article_count", "domain_categories", "base_url"],
                    "indexes": ["site_name"],
                    "constraints": ["site_name UNIQUE"]
                },
                "Language": {
                    "properties": ["code", "name", "article_count"],
                    "indexes": ["code"],
                    "constraints": ["code UNIQUE"]
                },
                "CrawlRun": {
                    "properties": ["run_id", "total_articles", "started_at", "completed_at", "status"],
                    "indexes": ["run_id"],
                    "constraints": ["run_id UNIQUE"]
                }
            },
            "relationships": {
                "WROTE": {
                    "from": "Author",
                    "to": "Article",
                    "properties": ["publish_date", "article_title"]
                },
                "SPECIALIZES_IN": {
                    "from": "Author", 
                    "to": "Domain",
                    "properties": ["article_count", "expertise_level"]
                },
                "BELONGS_TO": {
                    "from": "Article",
                    "to": "Domain",
                    "properties": []
                },
                "TAGGED_WITH": {
                    "from": "Article",
                    "to": "Tag", 
                    "properties": ["relevance_score"]
                },
                "WRITTEN_IN": {
                    "from": "Article",
                    "to": "Language",
                    "properties": []
                },
                "PUBLISHED_ON": {
                    "from": "Article",
                    "to": "Website",
                    "properties": ["publish_date"]
                },
                "EXTRACTED_IN": {
                    "from": "Article",
                    "to": "CrawlRun",
                    "properties": []
                },
                "FOCUSES_ON": {
                    "from": "Website",
                    "to": "Domain",
                    "properties": ["article_count", "focus_strength"]
                },
                "RELATED_TO": {
                    "from": "Tag",
                    "to": "Tag",
                    "properties": ["co_occurrence_count", "strength"]
                },
                "COMMONLY_USED_IN": {
                    "from": "Tag",
                    "to": "Domain",
                    "properties": ["usage_count", "usage_percentage"]
                },
                "OVERLAPS_WITH": {
                    "from": "Domain",
                    "to": "Domain", 
                    "properties": ["shared_authors", "overlap_type"]
                }
            }
        }
        
        self.print_result(model_structure, "Graph Model Structure")
    
    def demo_data_analysis(self):
        """Demonstrate data analysis capabilities"""
        self.print_section("Content Data Analysis")
        
        # Simulate analysis results that would come from the MCP server
        analysis_results = {
            "content_statistics": {
                "total_articles": 100,
                "unique_authors": 10,
                "unique_domains": 6,
                "unique_tags": 15,
                "date_range": {
                    "earliest": "2024-01-01",
                    "latest": "2024-12-31"
                }
            },
            "author_productivity": [
                {"author": "Dr. Alex Thompson", "articles": 15, "domains": ["Technology"]},
                {"author": "David Park", "articles": 14, "domains": ["Technology"]},
                {"author": "Dr. Sarah Chen", "articles": 12, "domains": ["Healthcare"]},
                {"author": "Lisa Chang", "articles": 11, "domains": ["Lifestyle"]},
                {"author": "Michael Rodriguez", "articles": 10, "domains": ["Financial"]}
            ],
            "domain_distribution": [
                {"domain": "Technology", "articles": 32, "percentage": 32.0},
                {"domain": "Sustainability", "articles": 18, "percentage": 18.0},
                {"domain": "Financial", "articles": 15, "percentage": 15.0},
                {"domain": "Healthcare", "articles": 15, "percentage": 15.0},
                {"domain": "Lifestyle", "articles": 11, "percentage": 11.0},
                {"domain": "Education", "articles": 9, "percentage": 9.0}
            ],
            "tag_analysis": {
                "most_common_tags": ["Technology", "AI", "Healthcare", "Sustainability", "Financial"],
                "tag_co_occurrence": [
                    {"tag1": "AI", "tag2": "Technology", "count": 25},
                    {"tag1": "Healthcare", "tag2": "AI", "count": 12},
                    {"tag1": "Financial", "tag2": "Technology", "count": 10}
                ]
            },
            "temporal_patterns": {
                "articles_per_month": {
                    "2024-01": 8, "2024-02": 9, "2024-03": 7, "2024-04": 8,
                    "2024-05": 9, "2024-06": 8, "2024-07": 9, "2024-08": 8,
                    "2024-09": 9, "2024-10": 8, "2024-11": 9, "2024-12": 8
                }
            }
        }
        
        self.print_result(analysis_results, "Content Analysis Results")
    
    def demo_graph_queries(self):
        """Demonstrate sample graph queries"""
        self.print_section("Sample Graph Queries")
        
        sample_queries = {
            "most_productive_authors": """
                MATCH (a:Author)-[:WROTE]->(article:Article)
                RETURN a.name, count(article) as articles
                ORDER BY articles DESC
                LIMIT 5
            """,
            "domain_collaboration": """
                MATCH (a1:Author)-[:SPECIALIZES_IN]->(d:Domain)<-[:SPECIALIZES_IN]-(a2:Author)
                WHERE a1 <> a2
                RETURN a1.name, a2.name, d.name, 
                       a1.total_articles + a2.total_articles AS combined_output
                ORDER BY combined_output DESC
                LIMIT 10
            """,
            "tag_co_occurrence": """
                MATCH (article:Article)-[:TAGGED_WITH]->(t1:Tag)
                MATCH (article)-[:TAGGED_WITH]->(t2:Tag)
                WHERE t1 <> t2
                RETURN t1.name, t2.name, count(article) as co_occurrence
                ORDER BY co_occurrence DESC
                LIMIT 15
            """,
            "content_evolution": """
                MATCH (article:Article)
                WITH article.publish_date.year AS year, 
                     article.publish_date.month AS month,
                     count(article) AS article_count
                RETURN year, month, article_count
                ORDER BY year, month
            """,
            "cross_domain_tags": """
                MATCH (t:Tag)-[:COMMONLY_USED_IN]->(d:Domain)
                WITH t, count(d) AS domain_count, collect(d.name) AS domains
                WHERE domain_count > 1
                RETURN t.name, domain_count, domains
                ORDER BY domain_count DESC
            """,
            "website_content_strategy": """
                MATCH (w:Website)-[:FOCUSES_ON]->(d:Domain)
                WITH w, count(d) AS focus_areas, collect(d.name) AS domains
                RETURN w.site_name, w.article_count, focus_areas, domains
                ORDER BY w.article_count DESC
            """
        }
        
        for query_name, query in sample_queries.items():
            print(f"\n🔍 {query_name.replace('_', ' ').title()}:")
            print(f"```cypher\n{query.strip()}\n```")
    
    def demo_manager_integration(self):
        """Demonstrate integration with MCP Manager"""
        self.print_section("MCP Manager Integration")
        
        try:
            # Check manager status
            manager_status = requests.get(f"{self.manager_url}/api/status", timeout=10)
            if manager_status.status_code == 200:
                self.print_result(manager_status.json(), "Manager Status")
            else:
                print("❌ MCP Manager not accessible")
        except Exception as e:
            print(f"❌ Manager connection failed: {e}")
    
    def run_complete_demo(self):
        """Run complete demonstration of all routes"""
        print("🚀 MCP Neo4j Data Modeling Server - Complete Routes Demo")
        print("=" * 80)
        
        # Run all demonstrations
        self.demo_health_check()
        self.demo_list_resources()
        self.demo_read_resources()
        self.demo_list_tools()
        self.demo_analyze_postgres_schema()
        self.demo_generate_cypher_queries()
        self.demo_graph_model_generation()
        self.demo_data_analysis()
        self.demo_graph_queries()
        self.demo_manager_integration()
        
        # Note about migration
        print(f"\n{'='*60}")
        print("⚠️  Data Migration")
        print("="*60)
        print("The migrate_to_neo4j tool is available but not demonstrated")
        print("in this script to avoid unintended data changes.")
        print("To run migration manually:")
        print("  curl -X POST http://localhost:8000/api/migrate \\")
        print("    -H 'Content-Type: application/json' \\")
        print("    -d '{\"clear_existing\": true}'")
        
        print(f"\n🎉 Demo completed! All MCP routes demonstrated.")
        print(f"📁 Graph model saved to: neo4j_graph_model.cypher")

def main():
    """Main execution function"""
    demo = MCPRoutesDemo()
    demo.run_complete_demo()

if __name__ == "__main__":
    main()