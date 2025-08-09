#!/usr/bin/env python3
"""
Unit tests for PostgreSQL Query Runner
"""

import unittest
from unittest.mock import patch, mock_open, MagicMock
import tempfile
import os
import sys
import yaml

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.postgres_query_runner import (
    load_config, parse_postgres_config, execute_query, 
    write_results_to_file, get_query_from_config, run_postgres_query,
    ErrorCodes
)


class TestPostgresQueryRunner(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_config = {
            'database': {
                'postgres': 'host: localhost\nport: 5432\ndatabase: testdb\nuser: testuser\npassword: testpass'
            },
            'queries': {
                'test_query': 'SELECT * FROM test_table;',
                'another_query': 'SELECT id, name FROM users;'
            }
        }
        
        self.sample_db_config = {
            'host': 'localhost',
            'port': '5432',
            'database': 'testdb',
            'user': 'testuser',
            'password': 'testpass'
        }

    def test_load_config_success(self):
        """Test successful configuration loading."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(self.sample_config, f)
            temp_path = f.name
        
        try:
            result = load_config(temp_path)
            self.assertEqual(result, self.sample_config)
        finally:
            os.unlink(temp_path)

    def test_load_config_file_not_found(self):
        """Test configuration loading with non-existent file."""
        with self.assertRaises(Exception) as context:
            load_config('non_existent_file.yml')
        
        self.assertIn(ErrorCodes.CONFIG_READ_ERROR, str(context.exception))

    def test_load_config_invalid_yaml(self):
        """Test configuration loading with invalid YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write('invalid: yaml: content: [')
            temp_path = f.name
        
        try:
            with self.assertRaises(Exception) as context:
                load_config(temp_path)
            
            self.assertIn(ErrorCodes.CONFIG_PARSE_ERROR, str(context.exception))
        finally:
            os.unlink(temp_path)

    def test_parse_postgres_config_success(self):
        """Test successful PostgreSQL configuration parsing."""
        config_string = 'host: localhost\nport: 5432\ndatabase: testdb\nuser: testuser\npassword: testpass'
        result = parse_postgres_config(config_string)
        
        expected = {
            'host': 'localhost',
            'port': '5432',
            'database': 'testdb',
            'user': 'testuser',
            'password': 'testpass'
        }
        
        self.assertEqual(result, expected)

    def test_parse_postgres_config_malformed(self):
        """Test PostgreSQL configuration parsing with malformed input."""
        config_string = 'malformed config without colons'
        
        with self.assertRaises(Exception) as context:
            parse_postgres_config(config_string)
        
        self.assertIn(ErrorCodes.CONFIG_PARSE_ERROR, str(context.exception))

    @patch('psycopg2.connect')
    def test_execute_query_success(self, mock_connect):
        """Test successful query execution."""
        # Mock database connection and cursor
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [('row1_col1', 'row1_col2'), ('row2_col1', 'row2_col2')]
        mock_cursor.description = [('col1',), ('col2',)]
        
        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        query = "SELECT * FROM test_table"
        results, columns = execute_query(mock_connection, query)
        
        self.assertEqual(len(results), 2)
        self.assertEqual(columns, ['col1', 'col2'])
        mock_cursor.execute.assert_called_once_with(query)

    @patch('psycopg2.connect')
    def test_execute_query_database_error(self, mock_connect):
        """Test query execution with database error."""
        import psycopg2
        
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg2.Error("Database error")
        
        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        with self.assertRaises(Exception) as context:
            execute_query(mock_connection, "SELECT * FROM test_table")
        
        self.assertIn(ErrorCodes.QUERY_EXECUTION_ERROR, str(context.exception))

    def test_write_results_to_file_success(self):
        """Test successful writing of results to file."""
        results = [('row1_col1', 'row1_col2'), ('row2_col1', 'row2_col2')]
        columns = ['col1', 'col2']
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
        
        try:
            write_results_to_file(results, columns, temp_path)
            
            # Verify file contents
            with open(temp_path, 'r') as f:
                content = f.read()
                self.assertIn('col1,col2', content)
                self.assertIn('row1_col1,row1_col2', content)
                self.assertIn('row2_col1,row2_col2', content)
        finally:
            os.unlink(temp_path)

    def test_write_results_to_file_io_error(self):
        """Test writing results with IO error."""
        results = [('data1', 'data2')]
        columns = ['col1', 'col2']
        invalid_path = '/invalid/path/file.csv'
        
        with self.assertRaises(Exception) as context:
            write_results_to_file(results, columns, invalid_path)
        
        self.assertIn(ErrorCodes.FILE_WRITE_ERROR, str(context.exception))

    def test_get_query_from_config_success(self):
        """Test successful query retrieval from config."""
        query = get_query_from_config(self.sample_config, 'test_query')
        self.assertEqual(query, 'SELECT * FROM test_table;')

    def test_get_query_from_config_missing_query(self):
        """Test query retrieval with non-existent query name."""
        with self.assertRaises(Exception) as context:
            get_query_from_config(self.sample_config, 'non_existent_query')
        
        self.assertIn(ErrorCodes.INVALID_QUERY_NAME, str(context.exception))

    def test_get_query_from_config_no_queries_section(self):
        """Test query retrieval with missing queries section."""
        config_without_queries = {'database': {'postgres': 'host: localhost'}}
        
        with self.assertRaises(Exception) as context:
            get_query_from_config(config_without_queries, 'any_query')
        
        self.assertIn(ErrorCodes.INVALID_QUERY_NAME, str(context.exception))

    @patch('src.postgres_query_runner.write_results_to_file')
    @patch('src.postgres_query_runner.execute_query')
    @patch('src.postgres_query_runner.get_db_connection')
    @patch('src.postgres_query_runner.load_config')
    def test_run_postgres_query_success(self, mock_load_config, mock_get_connection, 
                                       mock_execute_query, mock_write_results):
        """Test successful end-to-end query execution."""
        # Setup mocks
        mock_load_config.return_value = self.sample_config
        mock_connection = MagicMock()
        mock_get_connection.return_value.__enter__.return_value = mock_connection
        mock_execute_query.return_value = ([('data1', 'data2')], ['col1', 'col2'])
        
        # Execute function
        run_postgres_query('config.yml', 'test_query', 'output.csv')
        
        # Verify calls
        mock_load_config.assert_called_once_with('config.yml')
        mock_execute_query.assert_called_once_with(mock_connection, 'SELECT * FROM test_table;')
        mock_write_results.assert_called_once_with([('data1', 'data2')], ['col1', 'col2'], 'output.csv')

    @patch('src.postgres_query_runner.load_config')
    def test_run_postgres_query_missing_db_config(self, mock_load_config):
        """Test query execution with missing database configuration."""
        config_without_db = {'queries': {'test': 'SELECT 1'}}
        mock_load_config.return_value = config_without_db
        
        with self.assertRaises(Exception) as context:
            run_postgres_query('config.yml', 'test', 'output.csv')
        
        self.assertIn(ErrorCodes.MISSING_DB_CONFIG, str(context.exception))


class TestErrorCodes(unittest.TestCase):
    """Test that all error codes are unique."""
    
    def test_error_codes_unique(self):
        """Verify all error codes are unique."""
        error_codes = [
            ErrorCodes.CONFIG_READ_ERROR,
            ErrorCodes.CONFIG_PARSE_ERROR,
            ErrorCodes.DB_CONNECTION_ERROR,
            ErrorCodes.QUERY_EXECUTION_ERROR,
            ErrorCodes.FILE_WRITE_ERROR,
            ErrorCodes.INVALID_QUERY_NAME,
            ErrorCodes.MISSING_DB_CONFIG
        ]
        
        self.assertEqual(len(error_codes), len(set(error_codes)), 
                        "Error codes must be unique")


if __name__ == '__main__':
    unittest.main()