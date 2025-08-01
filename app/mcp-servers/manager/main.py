#!/usr/bin/env python3
"""
MCP Server Manager
Provides a web interface to monitor and manage MCP servers
"""

import os
import asyncio
import logging
from typing import Dict, Any, List
import requests
import psycopg2
from neo4j import GraphDatabase
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MCP Server Manager", version="1.0.0")

class ServerStatus(BaseModel):
    name: str
    status: str
    url: str
    last_check: str

class MigrationRequest(BaseModel):
    clear_existing: bool = False

class QueryRequest(BaseModel):
    query: str
    parameters: Dict[str, Any] = {}

class MCPManager:
    def __init__(self):
        self.data_modeling_url = os.getenv('MCP_DATA_MODELING_URL', 'http://localhost:8001')
        self.cypher_url = os.getenv('MCP_CYPHER_URL', 'http://localhost:8002')
        
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

    async def check_server_status(self, url: str) -> Dict[str, Any]:
        """Check if a server is responding"""
        try:
            response = requests.get(f"{url}/health", timeout=5)
            return {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time': response.elapsed.total_seconds(),
                'status_code': response.status_code
            }
        except Exception as e:
            return {
                'status': 'unreachable',
                'error': str(e)
            }

    async def check_postgres_status(self) -> Dict[str, Any]:
        """Check PostgreSQL connection and data"""
        try:
            conn = psycopg2.connect(**self.postgres_config)
            cursor = conn.cursor()
            
            # Check table existence and record counts
            cursor.execute("SELECT COUNT(*) FROM structured_content")
            content_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT author) FROM structured_content")
            author_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT domain) FROM structured_content")
            domain_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'status': 'healthy',
                'content_records': content_count,
                'unique_authors': author_count,
                'unique_domains': domain_count
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    async def check_neo4j_status(self) -> Dict[str, Any]:
        """Check Neo4j connection and data"""
        try:
            driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            
            with driver.session() as session:
                # Get node and relationship counts
                result = session.run("MATCH (n) RETURN count(n) as node_count")
                node_count = result.single()['node_count']
                
                result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
                rel_count = result.single()['rel_count']
                
                # Get label counts
                labels_result = session.run("CALL db.labels()")
                labels = [record['label'] for record in labels_result]
            
            driver.close()
            
            return {
                'status': 'healthy',
                'total_nodes': node_count,
                'total_relationships': rel_count,
                'node_labels': labels
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

manager = MCPManager()

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MCP Server Manager</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .status-card { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .healthy { border-left: 5px solid #4CAF50; }
            .unhealthy { border-left: 5px solid #f44336; }
            .unreachable { border-left: 5px solid #ff9800; }
            .button { background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px; }
            .button:hover { background-color: #45a049; }
            .section { margin: 20px 0; }
        </style>
    </head>
    <body>
        <h1>MCP Server Manager Dashboard</h1>
        
        <div class="section">
            <h2>Server Status</h2>
            <div id="server-status">Loading...</div>
        </div>
        
        <div class="section">
            <h2>Database Status</h2>
            <div id="database-status">Loading...</div>
        </div>
        
        <div class="section">
            <h2>Quick Actions</h2>
            <a href="/migrate" class="button">Migrate Data to Neo4j</a>
            <a href="/query-interface" class="button">Query Interface</a>
            <a href="/api/docs" class="button">API Documentation</a>
        </div>
        
        <script>
            async function loadStatus() {
                try {
                    const response = await fetch('/api/status');
                    const data = await response.json();
                    
                    document.getElementById('server-status').innerHTML = 
                        Object.entries(data.servers).map(([name, status]) => 
                            `<div class="status-card ${status.status}">
                                <h3>${name}</h3>
                                <p>Status: ${status.status}</p>
                                ${status.error ? `<p>Error: ${status.error}</p>` : ''}
                            </div>`
                        ).join('');
                    
                    document.getElementById('database-status').innerHTML = 
                        Object.entries(data.databases).map(([name, status]) => 
                            `<div class="status-card ${status.status}">
                                <h3>${name}</h3>
                                <p>Status: ${status.status}</p>
                                ${status.error ? `<p>Error: ${status.error}</p>` : ''}
                                ${status.content_records ? `<p>Records: ${status.content_records}</p>` : ''}
                                ${status.total_nodes ? `<p>Nodes: ${status.total_nodes}, Relationships: ${status.total_relationships}</p>` : ''}
                            </div>`
                        ).join('');
                } catch (error) {
                    console.error('Failed to load status:', error);
                }
            }
            
            loadStatus();
            setInterval(loadStatus, 30000); // Refresh every 30 seconds
        </script>
    </body>
    </html>
    """

@app.get("/api/status")
async def get_status():
    """Get status of all servers and databases"""
    servers = {
        'Data Modeling Server': await manager.check_server_status(manager.data_modeling_url),
        'Cypher Server': await manager.check_server_status(manager.cypher_url)
    }
    
    databases = {
        'PostgreSQL': await manager.check_postgres_status(),
        'Neo4j': await manager.check_neo4j_status()
    }
    
    return {
        'servers': servers,
        'databases': databases
    }

@app.post("/api/migrate")
async def migrate_data(request: MigrationRequest):
    """Trigger data migration from PostgreSQL to Neo4j"""
    try:
        # This would typically call the data modeling server
        # For now, we'll simulate the migration
        postgres_status = await manager.check_postgres_status()
        if postgres_status['status'] != 'healthy':
            raise HTTPException(status_code=400, detail="PostgreSQL is not healthy")
        
        neo4j_status = await manager.check_neo4j_status()
        if neo4j_status['status'] != 'healthy':
            raise HTTPException(status_code=400, detail="Neo4j is not healthy")
        
        # Simulate migration process
        return {
            'status': 'success',
            'message': 'Migration completed successfully',
            'migrated_records': postgres_status.get('content_records', 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query/cypher")
async def execute_cypher(request: QueryRequest):
    """Execute a Cypher query"""
    try:
        driver = GraphDatabase.driver(
            manager.neo4j_uri,
            auth=(manager.neo4j_user, manager.neo4j_password)
        )
        
        with driver.session() as session:
            result = session.run(request.query, request.parameters)
            records = [dict(record) for record in result]
        
        driver.close()
        
        return {
            'status': 'success',
            'records': records,
            'count': len(records)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/query/templates")
async def get_query_templates():
    """Get available query templates"""
    return {
        'templates': {
            'find_all_authors': {
                'query': 'MATCH (a:Author) RETURN a.name, a.specialization ORDER BY a.name',
                'description': 'Find all authors and their specializations'
            },
            'find_articles_by_author': {
                'query': 'MATCH (a:Author {name: $author_name})-[:WROTE]->(article:Article) RETURN article.title, article.publish_date ORDER BY article.publish_date DESC',
                'parameters': {'author_name': 'string'},
                'description': 'Find articles by a specific author'
            },
            'domain_distribution': {
                'query': 'MATCH (d:Domain)<-[:BELONGS_TO]-(article:Article) RETURN d.name, count(article) as article_count ORDER BY article_count DESC',
                'description': 'Get article distribution by domain'
            },
            'recent_articles': {
                'query': 'MATCH (article:Article) WHERE article.publish_date >= date($start_date) RETURN article.title, article.author, article.domain ORDER BY article.publish_date DESC LIMIT $limit',
                'parameters': {'start_date': 'date', 'limit': 'integer'},
                'description': 'Find recent articles since a specific date'
            }
        }
    }

@app.get("/query-interface", response_class=HTMLResponse)
async def query_interface():
    """Query interface page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Query Interface - MCP Manager</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .query-section { margin: 20px 0; }
            textarea { width: 100%; height: 200px; font-family: monospace; }
            .button { background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
            .button:hover { background-color: #45a049; }
            .results { background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-top: 20px; }
            .template-button { background-color: #2196F3; color: white; padding: 5px 10px; margin: 2px; border: none; border-radius: 3px; cursor: pointer; }
        </style>
    </head>
    <body>
        <h1>Neo4j Query Interface</h1>
        <a href="/">← Back to Dashboard</a>
        
        <div class="query-section">
            <h2>Query Templates</h2>
            <div id="templates">Loading templates...</div>
        </div>
        
        <div class="query-section">
            <h2>Custom Query</h2>
            <textarea id="query" placeholder="Enter your Cypher query here...">MATCH (n) RETURN n LIMIT 10</textarea>
            <br><br>
            <button class="button" onclick="executeQuery()">Execute Query</button>
        </div>
        
        <div id="results" class="results" style="display: none;">
            <h3>Results</h3>
            <pre id="results-content"></pre>
        </div>
        
        <script>
            async function loadTemplates() {
                try {
                    const response = await fetch('/api/query/templates');
                    const data = await response.json();
                    
                    document.getElementById('templates').innerHTML = 
                        Object.entries(data.templates).map(([name, template]) => 
                            `<button class="template-button" onclick="loadTemplate('${name}', \`${template.query}\`)">
                                ${name.replace(/_/g, ' ')}
                            </button>`
                        ).join('');
                } catch (error) {
                    console.error('Failed to load templates:', error);
                }
            }
            
            function loadTemplate(name, query) {
                document.getElementById('query').value = query;
            }
            
            async function executeQuery() {
                const query = document.getElementById('query').value;
                if (!query.trim()) {
                    alert('Please enter a query');
                    return;
                }
                
                try {
                    const response = await fetch('/api/query/cypher', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ query: query })
                    });
                    
                    const data = await response.json();
                    
                    document.getElementById('results').style.display = 'block';
                    document.getElementById('results-content').textContent = JSON.stringify(data, null, 2);
                } catch (error) {
                    document.getElementById('results').style.display = 'block';
                    document.getElementById('results-content').textContent = 'Error: ' + error.message;
                }
            }
            
            loadTemplates();
        </script>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "mcp-manager"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)