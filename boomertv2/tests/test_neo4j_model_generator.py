#!/usr/bin/env python3
"""
Unit tests for Neo4j Model Generator
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

from src.neo4j_model_generator import (
    Neo4jModelGenerator, Neo4jErrorCodes
)


class TestNeo4jModelGenerator(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = Neo4jModelGenerator()
        
        self.sample_results = [
            (1, 'Test Title 1', 'https://example.com/1', 'Test content 1', '2025-01-01'),
            (2, 'Test Title 2', 'https://example.com/2', 'Test content 2', '2025-01-02')
        ]
        
        self.sample_columns = ['id', 'title', 'url', 'content', 'date']
        
        self.sample_modeling_data = {
            "source": "postgresql",
            "table_info": {
                "columns": self.sample_columns,
                "row_count": 2,
                "sample_data": [
                    {"id": 1, "title": "Test Title 1", "url": "https://example.com/1", 
                     "content": "Test content 1", "date": "2025-01-01"},
                    {"id": 2, "title": "Test Title 2", "url": "https://example.com/2", 
                     "content": "Test content 2", "date": "2025-01-02"}
                ]
            },
            "full_data": [
                {"id": 1, "title": "Test Title 1", "url": "https://example.com/1", 
                 "content": "Test content 1", "date": "2025-01-01"},
                {"id": 2, "title": "Test Title 2", "url": "https://example.com/2", 
                 "content": "Test content 2", "date": "2025-01-02"}
            ],
            "metadata": {
                "generated_at": "2025-01-01T00:00:00",
                "total_records": 2,
                "column_count": 5
            }
        }

    def test_generate_timestamp(self):
        """Test timestamp generation."""
        timestamp = self.generator.generate_timestamp()
        
        # Check format (YYYYMMDD_HHMMSS)
        self.assertEqual(len(timestamp), 15)
        self.assertIn('_', timestamp)
        
        # Check if it's a valid datetime format
        datetime.strptime(timestamp, "%Y%m%d_%H%M%S")

    def test_generate_timestamp_error_handling(self):
        """Test timestamp generation error handling."""
        with patch('src.neo4j_model_generator.datetime') as mock_datetime:
            mock_datetime.now.side_effect = Exception("DateTime error")
            
            with self.assertRaises(Exception) as context:
                self.generator.generate_timestamp()
            
            self.assertIn(Neo4jErrorCodes.TIMESTAMP_GENERATION_ERROR, str(context.exception))

    def test_prepare_data_for_modeling_success(self):
        """Test successful data preparation for modeling."""
        result = self.generator.prepare_data_for_modeling(self.sample_results, self.sample_columns)
        
        self.assertEqual(result['source'], 'postgresql')
        self.assertEqual(result['table_info']['columns'], self.sample_columns)
        self.assertEqual(result['table_info']['row_count'], 2)
        self.assertEqual(len(result['full_data']), 2)
        self.assertEqual(result['metadata']['total_records'], 2)
        self.assertEqual(result['metadata']['column_count'], 5)

    def test_prepare_data_for_modeling_with_none_values(self):
        """Test data preparation with None values."""
        results_with_none = [
            (1, 'Test Title', None, 'Content', '2025-01-01'),
            (2, None, 'https://example.com', None, '2025-01-02')
        ]
        
        result = self.generator.prepare_data_for_modeling(results_with_none, self.sample_columns)
        
        self.assertIsNone(result['full_data'][0]['url'])
        self.assertIsNone(result['full_data'][1]['title'])
        self.assertIsNone(result['full_data'][1]['content'])

    def test_prepare_data_for_modeling_error_handling(self):
        """Test data preparation error handling."""
        # Test with None results
        with self.assertRaises(Exception) as context:
            self.generator.prepare_data_for_modeling(None, self.sample_columns)
        
        self.assertIn(Neo4jErrorCodes.DATA_PROCESSING_ERROR, str(context.exception))

    def test_generate_basic_neo4j_model_success(self):
        """Test successful basic Neo4j model generation."""
        model = self.generator._generate_basic_neo4j_model(self.sample_modeling_data)
        
        self.assertIn('model_info', model)
        self.assertIn('nodes', model)
        self.assertIn('relationships', model)
        self.assertIn('constraints', model)
        self.assertIn('indexes', model)
        self.assertIn('import_queries', model)
        
        # Check that nodes were created
        self.assertGreater(len(model['nodes']), 0)
        
        # Check that the primary node has properties
        primary_node = model['nodes'][0]
        self.assertIn('label', primary_node)
        self.assertIn('properties', primary_node)
        self.assertGreater(len(primary_node['properties']), 0)

    def test_generate_basic_neo4j_model_with_id_columns(self):
        """Test Neo4j model generation with ID columns."""
        model = self.generator._generate_basic_neo4j_model(self.sample_modeling_data)
        
        # Check that constraints were created for ID columns
        id_constraints = [c for c in model['constraints'] if 'id' in c['property']]
        self.assertGreater(len(id_constraints), 0)

    def test_generate_basic_neo4j_model_with_text_columns(self):
        """Test Neo4j model generation with text columns."""
        model = self.generator._generate_basic_neo4j_model(self.sample_modeling_data)
        
        # Check that indexes were created for text columns
        text_indexes = [i for i in model['indexes'] if any(col in i['property'] 
                       for col in ['title', 'content'])]
        self.assertGreater(len(text_indexes), 0)

    def test_generate_basic_neo4j_model_error_handling(self):
        """Test basic Neo4j model generation error handling."""
        invalid_data = {"invalid": "structure"}
        
        with self.assertRaises(Exception) as context:
            self.generator._generate_basic_neo4j_model(invalid_data)
        
        self.assertIn(Neo4jErrorCodes.MODEL_GENERATION_ERROR, str(context.exception))

    @patch('tempfile.NamedTemporaryFile')
    @patch('os.path.exists')
    @patch('os.unlink')
    def test_call_mcp_neo4j_modeling_success(self, mock_unlink, mock_exists, mock_temp_file):
        """Test successful MCP Neo4j modeling call."""
        # Setup mocks
        mock_temp_file.return_value.__enter__.return_value.name = '/tmp/test_file.json'
        mock_exists.return_value = True
        
        result = self.generator.call_mcp_neo4j_modeling(self.sample_modeling_data)
        
        # Should return a model structure
        self.assertIn('model_info', result)
        self.assertIn('nodes', result)
        
        # Verify cleanup was called
        mock_unlink.assert_called_once()

    @patch('tempfile.NamedTemporaryFile')
    def test_call_mcp_neo4j_modeling_error_handling(self, mock_temp_file):
        """Test MCP Neo4j modeling error handling."""
        mock_temp_file.side_effect = Exception("Temp file error")
        
        with self.assertRaises(Exception) as context:
            self.generator.call_mcp_neo4j_modeling(self.sample_modeling_data)
        
        self.assertIn(Neo4jErrorCodes.MCP_CONNECTION_ERROR, str(context.exception))

    def test_save_neo4j_model_success(self):
        """Test successful Neo4j model saving."""
        model = {"test": "model", "nodes": [], "relationships": []}
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
        
        try:
            self.generator.save_neo4j_model(model, temp_path)
            
            # Verify file was created and contains correct data
            with open(temp_path, 'r') as f:
                saved_model = json.load(f)
                self.assertEqual(saved_model, model)
        finally:
            os.unlink(temp_path)

    def test_save_neo4j_model_json_error(self):
        """Test Neo4j model saving with JSON serialization error."""
        # Create a model with non-serializable data
        class NonSerializable:
            def __repr__(self):
                return "NonSerializable"
        
        model = {"test": NonSerializable()}
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
        
        try:
            with self.assertRaises(Exception) as context:
                self.generator.save_neo4j_model(model, temp_path)
            
            self.assertIn(Neo4jErrorCodes.JSON_SERIALIZATION_ERROR, str(context.exception))
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_save_neo4j_model_io_error(self):
        """Test Neo4j model saving with IO error."""
        model = {"test": "model"}
        invalid_path = '/invalid/path/model.json'
        
        with self.assertRaises(Exception) as context:
            self.generator.save_neo4j_model(model, invalid_path)
        
        # Should contain file write error code or JSON serialization error
        error_str = str(context.exception)
        self.assertTrue('ERR_005' in error_str or 'ERR_N005' in error_str)

    @patch.object(Neo4jModelGenerator, 'save_neo4j_model')
    @patch.object(Neo4jModelGenerator, 'call_mcp_neo4j_modeling')
    @patch.object(Neo4jModelGenerator, 'prepare_data_for_modeling')
    @patch.object(Neo4jModelGenerator, 'execute_query')
    @patch.object(Neo4jModelGenerator, 'get_db_connection')
    @patch('src.neo4j_model_generator.get_query_from_config')
    @patch('src.neo4j_model_generator.parse_postgres_config')
    @patch('src.neo4j_model_generator.load_config')
    def test_generate_neo4j_model_from_query_success(self, mock_load_config, mock_parse_config,
                                                   mock_get_query, mock_get_connection,
                                                   mock_execute_query, mock_prepare_data,
                                                   mock_call_mcp, mock_save_model):
        """Test successful end-to-end Neo4j model generation."""
        # Setup mocks
        mock_load_config.return_value = {
            'database': {'postgres': 'host: localhost\nport: 5432'},
            'queries': {'test': 'SELECT * FROM test'}
        }
        mock_parse_config.return_value = {'host': 'localhost', 'port': '5432'}
        mock_get_query.return_value = 'SELECT * FROM test'
        mock_connection = MagicMock()
        mock_get_connection.return_value.__enter__.return_value = mock_connection
        mock_execute_query.return_value = (self.sample_results, self.sample_columns)
        mock_prepare_data.return_value = self.sample_modeling_data
        mock_call_mcp.return_value = {"model": "test"}
        
        # Execute function
        self.generator.generate_neo4j_model_from_query('config.yml', 'test', 'output.json')
        
        # Verify all steps were called
        mock_load_config.assert_called_once()
        mock_execute_query.assert_called_once()
        mock_prepare_data.assert_called_once()
        mock_call_mcp.assert_called_once()
        mock_save_model.assert_called_once()

    @patch('src.neo4j_model_generator.load_config')
    def test_generate_neo4j_model_from_query_missing_db_config(self, mock_load_config):
        """Test model generation with missing database configuration."""
        mock_load_config.return_value = {'queries': {'test': 'SELECT 1'}}
        
        with self.assertRaises(Exception) as context:
            self.generator.generate_neo4j_model_from_query('config.yml', 'test', 'output.json')
        
        self.assertIn('ERR_007', str(context.exception))


class TestNeo4jErrorCodes(unittest.TestCase):
    """Test that all Neo4j error codes are unique."""
    
    def test_neo4j_error_codes_unique(self):
        """Verify all Neo4j error codes are unique."""
        error_codes = [
            Neo4jErrorCodes.MCP_CONNECTION_ERROR,
            Neo4jErrorCodes.MCP_EXECUTION_ERROR,
            Neo4jErrorCodes.DATA_PROCESSING_ERROR,
            Neo4jErrorCodes.MODEL_GENERATION_ERROR,
            Neo4jErrorCodes.JSON_SERIALIZATION_ERROR,
            Neo4jErrorCodes.TIMESTAMP_GENERATION_ERROR,
            Neo4jErrorCodes.MCP_TOOL_NOT_AVAILABLE
        ]
        
        self.assertEqual(len(error_codes), len(set(error_codes)), 
                        "Neo4j error codes must be unique")


if __name__ == '__main__':
    unittest.main()