"""
Mock utilities for Neo4j testing.

This module provides mock implementations of Neo4j functionality for testing
without requiring a real Neo4j database instance.
"""

from typing import List, Dict, Any, Optional
from unittest.mock import Mock, MagicMock
import time

from modules.exceptions import Neo4jError, ErrorCodes


class MockNeo4jSession:
    """Mock Neo4j session for testing."""
    
    def __init__(self, mock_data: Dict[str, Any] = None):
        self.mock_data = mock_data or {}
        self.closed = False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def run(self, query: str, parameters: Dict[str, Any] = None):
        """Mock query execution."""
        if "RETURN 1 as test" in query:
            # Health check query
            return MockResult([{"test": 1}])
        
        elif "db.index.vector.queryNodes" in query:
            # Vector search query
            return self._mock_vector_search(parameters)
        
        elif "UNWIND $chunk_ids" in query:
            # Graph expansion query
            return self._mock_graph_expansion(parameters)
        
        elif "SHOW INDEXES" in query:
            # Index check query
            return MockResult([{"name": "chunk_embeddings", "type": "VECTOR"}])
        
        elif "MATCH (c:Chunk)" in query and "count" in query:
            # Node counts query
            return MockResult([{"chunks": 10, "articles": 5, "authors": 3}])
        
        else:
            return MockResult([])
    
    def _mock_vector_search(self, parameters: Dict[str, Any]) -> 'MockResult':
        """Mock vector search results."""
        limit = parameters.get("limit", 5)
        
        # Check if this should return empty results (for testing no results scenario)
        embedding = parameters.get("embedding", [])
        if len(embedding) > 0 and embedding[0] < 0:  # Use negative first value as signal for empty results
            return MockResult([])
        
        # Generate mock results
        results = []
        for i in range(min(limit, 3)):  # Return up to 3 mock results
            results.append({
                "chunk_id": f"chunk_{i+1}",
                "chunk_text": f"This is mock chunk text {i+1} for testing purposes.",
                "score": 0.9 - (i * 0.1),  # Decreasing scores
                "article_id": f"article_{i+1}",
                "article_title": f"Mock Article {i+1}",
                "author_id": f"author_{i+1}",
                "author_name": f"Mock Author {i+1}"
            })
        
        return MockResult(results)
    
    def _mock_graph_expansion(self, parameters: Dict[str, Any]) -> 'MockResult':
        """Mock graph expansion results."""
        chunk_ids = parameters.get("chunk_ids", [])
        
        if not chunk_ids:
            return MockResult([])
        
        results = []
        for i, chunk_id in enumerate(chunk_ids):
            results.append({
                "chunk_id": chunk_id,
                "chunk_text": f"Mock chunk text for {chunk_id}",
                "article_id": f"article_{i+1}",
                "article_title": f"Mock Article {i+1}",
                "author_id": f"author_{i+1}",
                "author_name": f"Mock Author {i+1}",
                "related_chunks": [
                    {"id": f"related_chunk_{i+1}_1", "text": f"Related chunk 1 for {chunk_id}"},
                    {"id": f"related_chunk_{i+1}_2", "text": f"Related chunk 2 for {chunk_id}"}
                ],
                "other_articles": [
                    {"id": f"other_article_{i+1}_1", "title": f"Other Article 1 by Author {i+1}"},
                    {"id": f"other_article_{i+1}_2", "title": f"Other Article 2 by Author {i+1}"}
                ]
            })
        
        return MockResult(results)
    
    def close(self):
        """Mock session close."""
        self.closed = True


class MockResult:
    """Mock Neo4j query result."""
    
    def __init__(self, records: List[Dict[str, Any]]):
        self.records = records
        self.index = 0
    
    def __iter__(self):
        return iter(self.records)
    
    def single(self):
        """Return single record."""
        if not self.records:
            return None
        return self.records[0]


class MockNeo4jDriver:
    """Mock Neo4j driver for testing."""
    
    def __init__(self, uri: str, auth: tuple, **kwargs):
        self.uri = uri
        self.auth = auth
        self.kwargs = kwargs
        self.closed = False
        
        # Simulate connection failures for specific URIs/credentials
        if "unreachable-server" in uri:
            from neo4j.exceptions import ServiceUnavailable
            raise ServiceUnavailable("Connection failed")
        
        if auth[0] == "invalid_user":
            from neo4j.exceptions import AuthError
            raise AuthError("Authentication failed")
    
    def session(self, database: str = None):
        """Create mock session."""
        return MockNeo4jSession()
    
    def close(self):
        """Mock driver close."""
        self.closed = True


def create_mock_neo4j_client():
    """Create a mock Neo4j client for testing."""
    from modules.neo4j_client import Neo4jClient
    
    # Create client with mock credentials
    client = Neo4jClient(
        uri="bolt://mock-server:7687",
        username="mock_user",
        password="mock_password"
    )
    
    # Replace the driver with a mock
    client.driver = MockNeo4jDriver(
        "bolt://mock-server:7687",
        ("mock_user", "mock_password")
    )
    
    return client


def patch_neo4j_driver():
    """Patch Neo4j GraphDatabase.driver for testing."""
    import modules.neo4j_client
    original_driver = modules.neo4j_client.GraphDatabase.driver
    
    def mock_driver(uri, auth=None, **kwargs):
        return MockNeo4jDriver(uri, auth, **kwargs)
    
    modules.neo4j_client.GraphDatabase.driver = mock_driver
    
    return original_driver


def restore_neo4j_driver(original_driver):
    """Restore original Neo4j driver after testing."""
    import modules.neo4j_client
    modules.neo4j_client.GraphDatabase.driver = original_driver