#!/usr/bin/env python3
"""
Unit tests for Neo4j Data Loader
"""

import unittest
from unittest.mock import patch, mock_open, MagicMock
import tempfile
import os
import sys
import json
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.neo4j_data_loader import (
    Neo4jDataLoader, Neo4jLoaderErrorCodes
)


class TestNeo4jDataLoader(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.loader = Neo4jDataLoader()
        
        self.sample_model = {
            "nodes": [
                {
                    "label": "Article",
                    "node_id_property": "id",
                    "properties": [
                        {"name": "id", "type": "string", "unique": True},
                        {"name": "title", "type": "string", "indexed": True},
                        {"name": "content", "type": "text"}
                    ]
                },
                {
                    "label": "Chunk",
                    "node_id_property": "chunk_id",
                    "properties": [
                        {"name": "chunk_id", "type": "string", "unique": True},
                        {"name": "embedding", "type": "vector"},
                        {"name": "chunk_text", "type": "text"}
                    ]
                }
            ],
            "relationships": [
                {
                    "type": "HAS_CHUNK",
                    "start_node": "Article",
                    "end_node": "Chunk",
                    "start_property": "id",
                    "end_property": "content_id",
                    "properties": []
                }
            ]
        }
        
        self.sample_data_records = [
            {
                "id": "1",
                "title": "Test Article 1",
                "content": "This is test content for article 1. It contains multiple sentences for chunking."
            },
            {
                "id": "2", 
                "title": "Test Article 2",
                "content": "This is test content for article 2. It also contains multiple sentences."
            }
        ]

    def test_load_neo4j_model_success(self):
        """Test successful Neo4j model loading."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.sample_model, f)
            temp_path = f.name
        
        try:
            result = self.loader.load_neo4j_model(temp_path)
            self.assertEqual(result, self.sample_model)
            self.assertEqual(len(result['nodes']), 2)
            self.assertEqual(len(result['relationships']), 1)
        finally:
            os.unlink(temp_path)

    def test_load_neo4j_model_file_not_found(self):
        """Test model loading with non-existent file."""
        with self.assertRaises(Exception) as context:
            self.loader.load_neo4j_model('non_existent_model.json')
        
        self.assertIn(Neo4jLoaderErrorCodes.MODEL_LOADING_ERROR, str(context.exception))

    def test_load_neo4j_model_invalid_json(self):
        """Test model loading with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('invalid json content {')
            temp_path = f.name
        
        try:
            with self.assertRaises(Exception) as context:
                self.loader.load_neo4j_model(temp_path)
            
            self.assertIn(Neo4jLoaderErrorCodes.MODEL_LOADING_ERROR, str(context.exception))
        finally:
            os.unlink(temp_path)

    @patch('neo4j.GraphDatabase.driver')
    def test_connect_to_neo4j_success(self, mock_driver):
        """Test successful Neo4j connection."""
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.single.return_value = {"test": 1}
        mock_session.run.return_value = mock_result
        mock_driver.return_value.session.return_value.__enter__.return_value = mock_session
        
        neo4j_config = {
            'host': 'localhost',
            'port': '7687',
            'user': 'neo4j',
            'password': 'password'
        }
        
        self.loader.connect_to_neo4j(neo4j_config)
        
        mock_driver.assert_called_once()
        self.assertIsNotNone(self.loader.neo4j_driver)

    @patch('neo4j.GraphDatabase.driver')
    def test_connect_to_neo4j_failure(self, mock_driver):
        """Test Neo4j connection failure."""
        mock_driver.side_effect = Exception("Connection failed")
        
        neo4j_config = {
            'host': 'localhost',
            'port': '7687',
            'user': 'neo4j',
            'password': 'password'
        }
        
        with self.assertRaises(Exception) as context:
            self.loader.connect_to_neo4j(neo4j_config)
        
        self.assertIn(Neo4jLoaderErrorCodes.NEO4J_CONNECTION_ERROR, str(context.exception))

    def test_initialize_embedding_model_success(self):
        """Test successful embedding model initialization."""
        # This test will use the actual SentenceTransformer
        # In a real test environment, you might want to mock this
        try:
            self.loader.initialize_embedding_model()
            self.assertIsNotNone(self.loader.embedding_model)
        except Exception as e:
            # If the model can't be loaded (e.g., no internet), skip the test
            self.skipTest(f"Could not load embedding model: {str(e)}")

    @patch('src.neo4j_data_loader.SentenceTransformer')
    def test_initialize_embedding_model_failure(self, mock_transformer):
        """Test embedding model initialization failure."""
        mock_transformer.side_effect = Exception("Model loading failed")
        
        with self.assertRaises(Exception) as context:
            self.loader.initialize_embedding_model()
        
        self.assertIn(Neo4jLoaderErrorCodes.EMBEDDING_ERROR, str(context.exception))

    def test_chunk_text_content_success(self):
        """Test successful text chunking."""
        text = "This is a test text. " * 50  # Create long text
        chunks = self.loader.chunk_text_content(text, chunk_size=100, overlap=20)
        
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertIn('chunk_id', chunk)
            self.assertIn('chunk_text', chunk)
            self.assertIn('chunk_position', chunk)
            self.assertIn('chunk_order', chunk)

    def test_chunk_text_content_empty_text(self):
        """Test text chunking with empty text."""
        chunks = self.loader.chunk_text_content("")
        self.assertEqual(len(chunks), 0)
        
        chunks = self.loader.chunk_text_content("   ")
        self.assertEqual(len(chunks), 0)

    def test_chunk_text_content_error_handling(self):
        """Test text chunking error handling."""
        with self.assertRaises(Exception) as context:
            self.loader.chunk_text_content(None)
        
        self.assertIn(Neo4jLoaderErrorCodes.CHUNKING_ERROR, str(context.exception))

    @patch.object(Neo4jDataLoader, 'initialize_embedding_model')
    def test_generate_embeddings_success(self, mock_init):
        """Test successful embedding generation."""
        mock_model = MagicMock()
        # Create mock objects that have tolist() method
        mock_embedding1 = MagicMock()
        mock_embedding1.tolist.return_value = [0.1, 0.2, 0.3]
        mock_embedding2 = MagicMock()
        mock_embedding2.tolist.return_value = [0.4, 0.5, 0.6]
        mock_embeddings = [mock_embedding1, mock_embedding2]
        mock_model.encode.return_value = mock_embeddings
        self.loader.embedding_model = mock_model
        
        texts = ["text 1", "text 2"]
        result = self.loader.generate_embeddings(texts)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], [0.1, 0.2, 0.3])
        self.assertEqual(result[1], [0.4, 0.5, 0.6])
        self.assertEqual(self.loader.load_metrics["embeddings_generated"], 2)

    def test_generate_embeddings_no_model(self):
        """Test embedding generation without initialized model."""
        # Set embedding_model to None to trigger initialization
        self.loader.embedding_model = None
        
        with patch.object(self.loader, 'initialize_embedding_model') as mock_init:
            mock_model = MagicMock()
            # Create mock object that has tolist() method
            mock_embedding = MagicMock()
            mock_embedding.tolist.return_value = [0.1, 0.2]
            mock_embeddings = [mock_embedding]
            mock_model.encode.return_value = mock_embeddings
            
            # Set up the mock to set the embedding_model when called
            def set_model():
                self.loader.embedding_model = mock_model
            mock_init.side_effect = set_model
            
            result = self.loader.generate_embeddings(["test"])
            
            mock_init.assert_called_once()
            self.assertEqual(len(result), 1)

    def test_generate_embeddings_error_handling(self):
        """Test embedding generation error handling."""
        mock_model = MagicMock()
        mock_model.encode.side_effect = Exception("Encoding failed")
        self.loader.embedding_model = mock_model
        
        with self.assertRaises(Exception) as context:
            self.loader.generate_embeddings(["test"])
        
        self.assertIn(Neo4jLoaderErrorCodes.EMBEDDING_ERROR, str(context.exception))

    @patch('tempfile.NamedTemporaryFile')
    @patch('os.path.exists')
    @patch('os.unlink')
    def test_call_mcp_neo4j_cypher_success(self, mock_unlink, mock_exists, mock_temp_file):
        """Test successful MCP Neo4j Cypher call."""
        mock_temp_file.return_value.__enter__.return_value.name = '/tmp/test_file.json'
        mock_exists.return_value = True
        
        result = self.loader.call_mcp_neo4j_cypher("create node query")
        
        self.assertIsInstance(result, str)
        mock_unlink.assert_called_once()

    def test_generate_basic_cypher(self):
        """Test basic Cypher generation."""
        # Test node creation
        result = self.loader._generate_basic_cypher("create node")
        self.assertIn("MERGE", result)
        self.assertIn("Node", result)
        
        # Test relationship creation
        result = self.loader._generate_basic_cypher("create relationship")
        self.assertIn("MATCH", result)
        self.assertIn("MERGE", result)
        self.assertIn("RELATES_TO", result)

    def test_process_vector_embeddings_success(self):
        """Test successful vector embedding processing."""
        with patch.object(self.loader, 'chunk_text_content') as mock_chunk, \
             patch.object(self.loader, 'generate_embeddings') as mock_embed:
            
            mock_chunks = [
                {'chunk_id': '1', 'chunk_text': 'chunk 1', 'chunk_position': 0, 'chunk_order': 0},
                {'chunk_id': '2', 'chunk_text': 'chunk 2', 'chunk_position': 1, 'chunk_order': 1}
            ]
            mock_chunk.return_value = mock_chunks
            mock_embed.return_value = [[0.1, 0.2], [0.3, 0.4]]
            
            result = self.loader.process_vector_embeddings(self.sample_data_records, self.sample_model, {})
            
            self.assertEqual(len(result), 4)  # 2 records * 2 chunks each
            for chunk_record in result:
                self.assertIn('chunk_id', chunk_record)
                self.assertIn('embedding', chunk_record)
                self.assertIn('content_id', chunk_record)

    def test_process_vector_embeddings_no_vector_properties(self):
        """Test vector embedding processing with no vector properties."""
        model_without_vectors = {
            "nodes": [
                {
                    "label": "Article",
                    "properties": [
                        {"name": "id", "type": "string"}
                    ]
                }
            ]
        }
        
        result = self.loader.process_vector_embeddings(self.sample_data_records, model_without_vectors, {})
        self.assertEqual(len(result), 0)

    def test_write_load_metrics_success(self):
        """Test successful metrics writing."""
        # Set up some test metrics
        self.loader.load_metrics = {
            "nodes_created": {"Article": 5, "Chunk": 10},
            "relationships_created": {"HAS_CHUNK": 8},
            "nodes_failed": {"Article": 1},
            "relationships_failed": {"HAS_CHUNK": 2},
            "chunks_created": 10,
            "embeddings_generated": 10,
            "total_records_processed": 5,
            "errors": ["Test error 1", "Test error 2"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
        
        try:
            self.loader.write_load_metrics(temp_path)
            
            # Verify file was created and contains expected content
            with open(temp_path, 'r') as f:
                content = f.read()
                self.assertIn("Neo4j Data Load Metrics", content)
                self.assertIn("Article: 5", content)
                self.assertIn("Chunk: 10", content)
                self.assertIn("HAS_CHUNK: 8", content)
                self.assertIn("Total Nodes: 15", content)
                self.assertIn("Chunks created: 10", content)
                self.assertIn("Test error 1", content)
        finally:
            os.unlink(temp_path)

    def test_write_load_metrics_io_error(self):
        """Test metrics writing with IO error."""
        invalid_path = '/invalid/path/metrics.txt'
        
        with self.assertRaises(Exception) as context:
            self.loader.write_load_metrics(invalid_path)
        
        self.assertIn(Neo4jLoaderErrorCodes.METRICS_WRITE_ERROR, str(context.exception))

    @patch.object(Neo4jDataLoader, 'write_load_metrics')
    @patch.object(Neo4jDataLoader, 'load_relationships_to_neo4j')
    @patch.object(Neo4jDataLoader, 'load_nodes_to_neo4j')
    @patch.object(Neo4jDataLoader, 'process_vector_embeddings')
    @patch.object(Neo4jDataLoader, 'execute_query')
    @patch.object(Neo4jDataLoader, 'get_db_connection')
    @patch.object(Neo4jDataLoader, 'connect_to_neo4j')
    @patch.object(Neo4jDataLoader, 'load_neo4j_model')
    @patch('src.neo4j_data_loader.get_query_from_config')
    @patch('src.neo4j_data_loader.parse_postgres_config')
    @patch('src.neo4j_data_loader.load_config')
    def test_load_data_to_neo4j_success(self, mock_load_config, mock_parse_config,
                                       mock_get_query, mock_load_model, mock_connect_neo4j,
                                       mock_get_connection, mock_execute_query,
                                       mock_process_embeddings, mock_load_nodes,
                                       mock_load_relationships, mock_write_metrics):
        """Test successful end-to-end data loading."""
        # Setup mocks
        mock_load_config.return_value = {
            'database': {
                'postgres': 'host: localhost\nport: 5432',
                'neo4j': 'host: localhost\nport: 7687'
            },
            'queries': {'trending': 'SELECT * FROM test'}
        }
        mock_parse_config.return_value = {'host': 'localhost', 'port': '5432'}
        mock_get_query.return_value = 'SELECT * FROM test'
        mock_load_model.return_value = self.sample_model
        mock_connection = MagicMock()
        mock_get_connection.return_value.__enter__.return_value = mock_connection
        mock_execute_query.return_value = ([('1', 'title1', 'content1')], ['id', 'title', 'content'])
        mock_process_embeddings.return_value = []
        
        # Execute function
        self.loader.load_data_to_neo4j('config.yml', 'model.json', 'metrics.txt')
        
        # Verify all steps were called
        mock_load_config.assert_called_once()
        mock_load_model.assert_called_once()
        mock_connect_neo4j.assert_called_once()
        mock_execute_query.assert_called_once()
        mock_process_embeddings.assert_called_once()
        mock_load_nodes.assert_called()
        mock_load_relationships.assert_called_once()
        mock_write_metrics.assert_called_once()


class TestNeo4jLoaderErrorCodes(unittest.TestCase):
    """Test that all Neo4j loader error codes are unique."""
    
    def test_neo4j_loader_error_codes_unique(self):
        """Verify all Neo4j loader error codes are unique."""
        error_codes = [
            Neo4jLoaderErrorCodes.NEO4J_CONNECTION_ERROR,
            Neo4jLoaderErrorCodes.NEO4J_EXECUTION_ERROR,
            Neo4jLoaderErrorCodes.MODEL_LOADING_ERROR,
            Neo4jLoaderErrorCodes.CHUNKING_ERROR,
            Neo4jLoaderErrorCodes.EMBEDDING_ERROR,
            Neo4jLoaderErrorCodes.MCP_CONNECTION_ERROR,
            Neo4jLoaderErrorCodes.MCP_EXECUTION_ERROR,
            Neo4jLoaderErrorCodes.METRICS_WRITE_ERROR,
            Neo4jLoaderErrorCodes.DATA_VALIDATION_ERROR
        ]
        
        self.assertEqual(len(error_codes), len(set(error_codes)), 
                        "Neo4j loader error codes must be unique")


if __name__ == '__main__':
    unittest.main()