#!/usr/bin/env python3
"""
Shared utilities for MCP servers
"""

import logging
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, date

def setup_logging(name: str, level: str = "INFO") -> logging.Logger:
    """Setup logging for MCP servers"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def serialize_neo4j_value(value: Any) -> Any:
    """Serialize Neo4j values to JSON-compatible format"""
    if hasattr(value, '__dict__'):
        if hasattr(value, 'labels'):  # Node
            return {
                'type': 'node',
                'labels': list(value.labels),
                'properties': dict(value)
            }
        elif hasattr(value, 'type'):  # Relationship
            return {
                'type': 'relationship',
                'rel_type': value.type,
                'properties': dict(value)
            }
        else:
            return str(value)
    elif isinstance(value, (datetime, date)):
        return value.isoformat()
    else:
        return value

def format_cypher_result(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Format Cypher query results for display"""
    formatted_records = []
    
    for record in records:
        formatted_record = {}
        for key, value in record.items():
            formatted_record[key] = serialize_neo4j_value(value)
        formatted_records.append(formatted_record)
    
    return {
        'records': formatted_records,
        'count': len(formatted_records),
        'columns': list(records[0].keys()) if records else []
    }

def validate_cypher_query(query: str) -> Dict[str, Any]:
    """Basic validation of Cypher queries"""
    query = query.strip().upper()
    
    # Check for dangerous operations
    dangerous_keywords = ['DELETE', 'REMOVE', 'DROP', 'CREATE CONSTRAINT', 'DROP CONSTRAINT']
    for keyword in dangerous_keywords:
        if keyword in query:
            return {
                'valid': False,
                'error': f"Query contains potentially dangerous operation: {keyword}"
            }
    
    # Check for basic syntax
    if not any(keyword in query for keyword in ['MATCH', 'CREATE', 'MERGE', 'RETURN', 'WITH']):
        return {
            'valid': False,
            'error': "Query must contain at least one Cypher keyword (MATCH, CREATE, MERGE, RETURN, WITH)"
        }
    
    return {'valid': True}

def get_sample_queries() -> Dict[str, Dict[str, Any]]:
    """Get sample Cypher queries for different use cases"""
    return {
        'basic_queries': {
            'find_all_nodes': {
                'query': 'MATCH (n) RETURN n LIMIT 25',
                'description': 'Find all nodes (limited to 25)'
            },
            'count_nodes_by_label': {
                'query': 'MATCH (n) RETURN labels(n) as labels, count(n) as count ORDER BY count DESC',
                'description': 'Count nodes by label'
            },
            'count_relationships': {
                'query': 'MATCH ()-[r]->() RETURN type(r) as relationship_type, count(r) as count ORDER BY count DESC',
                'description': 'Count relationships by type'
            }
        },
        'content_queries': {
            'authors_and_articles': {
                'query': 'MATCH (a:Author)-[:WROTE]->(article:Article) RETURN a.name, count(article) as article_count ORDER BY article_count DESC',
                'description': 'Authors and their article counts'
            },
            'domain_distribution': {
                'query': 'MATCH (d:Domain)<-[:BELONGS_TO]-(article:Article) RETURN d.name, count(article) as articles ORDER BY articles DESC',
                'description': 'Article distribution by domain'
            },
            'tag_popularity': {
                'query': 'MATCH (t:Tag)<-[:TAGGED_WITH]-(article:Article) RETURN t.name, count(article) as usage_count ORDER BY usage_count DESC LIMIT 20',
                'description': 'Most popular tags'
            },
            'recent_articles': {
                'query': 'MATCH (article:Article) WHERE article.publish_date >= date("2024-01-01") RETURN article.title, article.author, article.publish_date ORDER BY article.publish_date DESC LIMIT 10',
                'description': 'Recent articles from 2024'
            }
        },
        'analysis_queries': {
            'author_collaboration': {
                'query': 'MATCH (a1:Author)-[:WROTE]->(article1:Article)-[:BELONGS_TO]->(d:Domain)<-[:BELONGS_TO]-(article2:Article)<-[:WROTE]-(a2:Author) WHERE a1 <> a2 RETURN a1.name, a2.name, d.name, count(*) as shared_articles ORDER BY shared_articles DESC LIMIT 10',
                'description': 'Authors working in the same domains'
            },
            'cross_domain_authors': {
                'query': 'MATCH (a:Author)-[:WROTE]->(article:Article)-[:BELONGS_TO]->(d:Domain) WITH a, collect(DISTINCT d.name) as domains WHERE size(domains) > 1 RETURN a.name, domains, size(domains) as domain_count ORDER BY domain_count DESC',
                'description': 'Authors writing across multiple domains'
            },
            'tag_relationships': {
                'query': 'MATCH (article:Article)-[:TAGGED_WITH]->(t1:Tag), (article)-[:TAGGED_WITH]->(t2:Tag) WHERE t1 <> t2 RETURN t1.name, t2.name, count(article) as co_occurrence ORDER BY co_occurrence DESC LIMIT 15',
                'description': 'Tags that frequently appear together'
            }
        }
    }

class MCPError(Exception):
    """Base exception for MCP server errors"""
    pass

class DatabaseConnectionError(MCPError):
    """Database connection error"""
    pass

class QueryExecutionError(MCPError):
    """Query execution error"""
    pass