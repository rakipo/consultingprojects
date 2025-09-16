"""
Enhanced mock utilities for comprehensive GraphRAG testing.

This module provides sophisticated mock implementations that can simulate
realistic GraphRAG behavior for integration testing without requiring
actual Neo4j or embedding model dependencies.
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch
import random

# Add parent directories to path for module imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modules.exceptions import Neo4jError, EmbeddingError, ErrorCodes


class MockDataManager:
    """Manages mock data for testing."""
    
    def __init__(self, sample_data_path: str = "tests/fixtures/sample_data.yaml"):
        self.sample_data_path = sample_data_path
        self.data = self._load_sample_data()
    
    def _load_sample_data(self) -> Dict[str, Any]:
        """Load sample data from YAML file."""
        try:
            with open(self.sample_data_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Could not load sample data: {e}")
            return {}
    
    def get_chunks(self) -> List[Dict[str, Any]]:
        """Get sample chunks."""
        return self.data.get("sample_chunks", [])
    
    def get_articles(self) -> List[Dict[str, Any]]:
        """Get sample articles."""
        return self.data.get("sample_articles", [])
    
    def get_authors(self) -> List[Dict[str, Any]]:
        """Get sample authors."""
        return self.data.get("sample_authors", [])
    
    def get_test_queries(self) -> List[Dict[str, Any]]:
        """Get test queries with expected results."""
        return self.data.get("test_queries", [])
    
    def get_integration_tests(self) -> List[Dict[str, Any]]:
        """Get integration test scenarios."""
        return self.data.get("integration_tests", [])


class EnhancedMockNeo4jClient:
    """Enhanced mock Neo4j client with realistic behavior."""
    
    def __init__(self, data_manager: MockDataManager):
        self.data_manager = data_manager
        self.connected = False
        self.chunks = data_manager.get_chunks()
        self.articles = data_manager.get_articles()
        self.authors = data_manager.get_authors()
    
    def connect(self):
        """Mock connection."""
        self.connected = True
    
    def close(self):
        """Mock close."""
        self.connected = False
    
    def vector_search(self, embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """Mock vector search with similarity calculation."""
        if not self.connected:
            raise Neo4jError(ErrorCodes.NEO4J_CONNECTION_LOST, "Not connected")
        
        # Calculate similarity scores (simplified cosine similarity)
        results = []
        for chunk in self.chunks:
            chunk_embedding = chunk.get("embedding", [])
            if len(chunk_embedding) == len(embedding):
                # Simple dot product similarity
                similarity = sum(a * b for a, b in zip(embedding, chunk_embedding))
                
                # Find related article and author
                article = next((a for a in self.articles if a["id"] == chunk["article_id"]), {})
                author = next((a for a in self.authors if a["id"] == chunk["author_id"]), {})
                
                result = {
                    "chunk_id": chunk["id"],
                    "chunk_text": chunk["text"],
                    "score": similarity,
                    "article_id": article.get("id"),
                    "article_title": article.get("title"),
                    "author_id": author.get("id"),
                    "author_name": author.get("name")
                }
                results.append(result)
        
        # Sort by score and limit results
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
    
    def expand_graph(self, chunk_ids: List[str]) -> List[Dict[str, Any]]:
        """Mock graph expansion."""
        if not self.connected:
            raise Neo4jError(ErrorCodes.NEO4J_CONNECTION_LOST, "Not connected")
        
        expanded_data = []
        for chunk_id in chunk_ids:
            chunk = next((c for c in self.chunks if c["id"] == chunk_id), None)
            if not chunk:
                continue
            
            # Find article and author
            article = next((a for a in self.articles if a["id"] == chunk["article_id"]), {})
            author = next((a for a in self.authors if a["id"] == chunk["author_id"]), {})
            
            # Find related chunks from same article
            related_chunks = [
                {"id": c["id"], "text": c["text"]}
                for c in self.chunks
                if c["article_id"] == chunk["article_id"] and c["id"] != chunk_id
            ]
            
            # Find other articles by same author
            other_articles = [
                {"id": a["id"], "title": a["title"]}
                for a in self.articles
                if a["author_id"] == chunk["author_id"] and a["id"] != chunk["article_id"]
            ]
            
            expansion_data = {
                "chunk_id": chunk_id,
                "chunk_text": chunk["text"],
                "article_id": article.get("id"),
                "article_title": article.get("title"),
                "author_id": author.get("id"),
                "author_name": author.get("name"),
                "related_chunks": related_chunks,
                "other_articles": other_articles
            }
            expanded_data.append(expansion_data)
        
        return expanded_data
    
    def health_check(self) -> Dict[str, Any]:
        """Mock health check."""
        return {
            "connection": self.connected,
            "database": "mock_db",
            "indexes": {"chunk_embeddings": {"exists": True, "type": "VECTOR"}},
            "node_counts": {
                "chunks": len(self.chunks),
                "articles": len(self.articles),
                "authors": len(self.authors)
            },
            "timestamp": 1234567890
        }


class MockEmbeddingGenerator:
    """Mock embedding generator with deterministic behavior."""
    
    def __init__(self, dimension: int = 5):
        self.dimension = dimension
        self.model_loaded = False
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate mock embedding based on text content."""
        if not text or not text.strip():
            raise EmbeddingError(
                ErrorCodes.EMBEDDING_TEXT_ENCODING_ERROR,
                "Cannot generate embedding for empty text"
            )
        
        # Generate deterministic embedding based on text hash
        text_hash = hash(text.lower())
        random.seed(text_hash)
        
        # Generate normalized embedding
        embedding = [random.uniform(-1, 1) for _ in range(self.dimension)]
        
        # Normalize to unit vector
        norm = sum(x*x for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get mock model info."""
        return {
            "model_name": "mock-embedding-model",
            "embedding_dimension": self.dimension,
            "max_sequence_length": 512,
            "device": "cpu"
        }


class IntegrationTestRunner:
    """Runs integration tests with mock data."""
    
    def __init__(self):
        self.data_manager = MockDataManager()
        self.mock_neo4j = EnhancedMockNeo4jClient(self.data_manager)
        self.mock_embedding = MockEmbeddingGenerator()
    
    def setup_mocks(self):
        """Set up all necessary mocks for integration testing."""
        # Patch Neo4j client
        self.neo4j_patcher = patch('modules.neo4j_client.get_neo4j_client')
        mock_get_client = self.neo4j_patcher.start()
        mock_get_client.return_value = self.mock_neo4j
        
        # Patch embedding generator
        self.embedding_patcher = patch('modules.embedding.generate_embedding')
        mock_generate = self.embedding_patcher.start()
        mock_generate.side_effect = self.mock_embedding.generate_embedding
        
        # Patch model info
        self.model_info_patcher = patch('modules.embedding.get_model_info')
        mock_model_info = self.model_info_patcher.start()
        mock_model_info.return_value = self.mock_embedding.get_model_info()
        
        # Connect mock Neo4j
        self.mock_neo4j.connect()
    
    def teardown_mocks(self):
        """Clean up mocks after testing."""
        if hasattr(self, 'neo4j_patcher'):
            self.neo4j_patcher.stop()
        if hasattr(self, 'embedding_patcher'):
            self.embedding_patcher.stop()
        if hasattr(self, 'model_info_patcher'):
            self.model_info_patcher.stop()
    
    def run_integration_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single integration test case."""
        from modules.retrieval import GraphRetriever
        
        # Create retriever with mock credentials
        retriever = GraphRetriever(
            neo4j_uri="bolt://mock:7687",
            neo4j_username="mock",
            neo4j_password="mock"
        )
        
        # Override the Neo4j client
        retriever._neo4j_client = self.mock_neo4j
        
        # Run the test
        query = test_case.get("query", "")
        expand_graph = test_case.get("expand_graph", True)
        
        results = retriever.retrieve(query, limit=5, expand_graph=expand_graph)
        
        # Analyze results
        analysis = {
            "query": query,
            "results_count": len(results),
            "expand_graph": expand_graph,
            "has_results": len(results) > 0,
            "has_context": any(
                result.get("context", {}).get("related_chunks") or
                result.get("context", {}).get("other_articles")
                for result in results
            ) if expand_graph else False,
            "score_range": [
                min(r["score"] for r in results),
                max(r["score"] for r in results)
            ] if results else [0, 0],
            "unique_authors": len(set(
                r.get("author", {}).get("name")
                for r in results
                if r.get("author", {}).get("name")
            )),
            "unique_articles": len(set(
                r.get("article", {}).get("title")
                for r in results
                if r.get("article", {}).get("title")
            ))
        }
        
        return analysis
    
    def run_all_integration_tests(self) -> List[Dict[str, Any]]:
        """Run all integration tests."""
        test_cases = self.data_manager.get_integration_tests()
        results = []
        
        self.setup_mocks()
        try:
            for test_case in test_cases:
                result = self.run_integration_test(test_case)
                result["test_name"] = test_case.get("name", "unknown")
                result["test_description"] = test_case.get("description", "")
                results.append(result)
        finally:
            self.teardown_mocks()
        
        return results


def run_integration_tests() -> None:
    """Run integration tests and display results."""
    print("=== GraphRAG Integration Tests ===\n")
    
    runner = IntegrationTestRunner()
    results = runner.run_all_integration_tests()
    
    for result in results:
        print(f"Test: {result['test_name']}")
        print(f"Description: {result['test_description']}")
        print(f"Query: {result['query']}")
        print(f"Results: {result['results_count']}")
        print(f"Score Range: {result['score_range'][0]:.3f} - {result['score_range'][1]:.3f}")
        print(f"Unique Authors: {result['unique_authors']}")
        print(f"Unique Articles: {result['unique_articles']}")
        print(f"Has Context: {result['has_context']}")
        print("---")
    
    print(f"\nCompleted {len(results)} integration tests")


if __name__ == "__main__":
    run_integration_tests()