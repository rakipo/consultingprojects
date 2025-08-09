#!/usr/bin/env python3
"""
PostgreSQL Query Runner
A standalone program to connect to PostgreSQL, run queries, and save results to files.

Usage:
    python postgres_query_runner.py config_boomer.yml trending sample_data.txt
"""

import sys
import logging
import yaml
import psycopg2
import csv
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
import argparse
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

# Error codes for unique identification
class ErrorCodes:
    CONFIG_READ_ERROR = "ERR_001"
    CONFIG_PARSE_ERROR = "ERR_002" 
    DB_CONNECTION_ERROR = "ERR_003"
    QUERY_EXECUTION_ERROR = "ERR_004"
    FILE_WRITE_ERROR = "ERR_005"
    INVALID_QUERY_NAME = "ERR_006"
    MISSING_DB_CONFIG = "ERR_007"


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing configuration data
        
    Raises:
        Exception: If config file cannot be read or parsed
    """
    logger.info(f"Loading configuration from: {config_path}")
    
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            logger.info("Configuration loaded successfully")
            return config
    except FileNotFoundError as e:
        error_msg = f"{ErrorCodes.CONFIG_READ_ERROR}: Configuration file not found: {config_path}"
        logger.error(error_msg)
        raise Exception(error_msg) from e
    except yaml.YAMLError as e:
        error_msg = f"{ErrorCodes.CONFIG_PARSE_ERROR}: Error parsing YAML configuration: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg) from e
    except Exception as e:
        error_msg = f"{ErrorCodes.CONFIG_READ_ERROR}: Unexpected error reading config: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg) from e


def parse_postgres_config(config_string: str) -> Dict[str, str]:
    """
    Parse PostgreSQL configuration string.
    
    Args:
        config_string: Multi-line string containing database configuration
        
    Returns:
        Dictionary with database connection parameters
    """
    logger.info("Parsing PostgreSQL configuration")
    
    try:
        config_dict = {}
        lines_with_colons = 0
        
        for line in config_string.strip().split('\n'):
            line = line.strip()
            if line:  # Skip empty lines
                if ':' in line:
                    key, value = line.split(':', 1)
                    config_dict[key.strip()] = value.strip()
                    lines_with_colons += 1
                else:
                    # Line without colon in non-empty config is malformed
                    raise ValueError(f"Malformed configuration line: {line}")
        
        # Check if we got any valid configuration lines
        if lines_with_colons == 0:
            raise ValueError("No valid configuration lines found")
        
        logger.info("PostgreSQL configuration parsed successfully")
        return config_dict
    except Exception as e:
        error_msg = f"{ErrorCodes.CONFIG_PARSE_ERROR}: Error parsing PostgreSQL config: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg) from e


@contextmanager
def get_db_connection(db_config: Dict[str, str]):
    """
    Create database connection context manager.
    
    Args:
        db_config: Database configuration dictionary
        
    Yields:
        psycopg2 connection object
    """
    connection = None
    try:
        logger.info(f"Connecting to PostgreSQL at {db_config.get('host')}:{db_config.get('port')}")
        
        connection = psycopg2.connect(
            host=db_config['host'],
            port=int(db_config['port']),
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password']
        )
        
        logger.info("Database connection established successfully")
        yield connection
        
    except psycopg2.Error as e:
        error_msg = f"{ErrorCodes.DB_CONNECTION_ERROR}: PostgreSQL connection error: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg) from e
    except Exception as e:
        error_msg = f"{ErrorCodes.DB_CONNECTION_ERROR}: Unexpected database connection error: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg) from e
    finally:
        if connection:
            connection.close()
            logger.info("Database connection closed")


def execute_query(connection, query: str) -> List[Tuple]:
    """
    Execute SQL query and return results.
    
    Args:
        connection: Database connection object
        query: SQL query string
        
    Returns:
        List of tuples containing query results
    """
    logger.info(f"Executing query: {query[:100]}...")
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            
            # Get column names
            column_names = [desc[0] for desc in cursor.description] if cursor.description else []
            
            logger.info(f"Query executed successfully. Retrieved {len(results)} rows")
            return results, column_names
            
    except psycopg2.Error as e:
        error_msg = f"{ErrorCodes.QUERY_EXECUTION_ERROR}: Query execution error: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg) from e
    except Exception as e:
        error_msg = f"{ErrorCodes.QUERY_EXECUTION_ERROR}: Unexpected query execution error: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg) from e


def write_results_to_file(results: List[Tuple], column_names: List[str], output_file: str) -> None:
    """
    Write query results to a CSV file.
    
    Args:
        results: List of tuples containing query results
        column_names: List of column names
        output_file: Path to output file
    """
    logger.info(f"Writing {len(results)} rows to file: {output_file}")
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Write header
            if column_names:
                writer.writerow(column_names)
            
            # Write data rows
            writer.writerows(results)
            
        logger.info(f"Results successfully written to {output_file}")
        
    except IOError as e:
        error_msg = f"{ErrorCodes.FILE_WRITE_ERROR}: Error writing to file {output_file}: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg) from e
    except Exception as e:
        error_msg = f"{ErrorCodes.FILE_WRITE_ERROR}: Unexpected file write error: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg) from e


def get_query_from_config(config: Dict[str, Any], query_name: str) -> str:
    """
    Retrieve query from configuration by name.
    
    Args:
        config: Configuration dictionary
        query_name: Name of the query to retrieve
        
    Returns:
        SQL query string
    """
    logger.info(f"Retrieving query: {query_name}")
    
    try:
        if 'queries' not in config:
            raise KeyError("No 'queries' section found in configuration")
            
        if query_name not in config['queries']:
            available_queries = list(config['queries'].keys())
            raise KeyError(f"Query '{query_name}' not found. Available queries: {available_queries}")
            
        query = config['queries'][query_name]
        logger.info(f"Query retrieved successfully: {query[:50]}...")
        return query
        
    except KeyError as e:
        error_msg = f"{ErrorCodes.INVALID_QUERY_NAME}: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg) from e


class PostgresQueryRunner:
    """PostgreSQL Query Runner class for executing queries and saving results."""
    
    def get_db_connection(self, db_config: Dict[str, str]):
        """Get database connection - wrapper for the context manager."""
        return get_db_connection(db_config)
    
    def execute_query(self, connection, query: str):
        """Execute query - wrapper for the function."""
        return execute_query(connection, query)


def run_postgres_query(config_path: str, query_name: str, output_file: str) -> None:
    """
    Main function to run PostgreSQL query and save results.
    
    Args:
        config_path: Path to configuration file
        query_name: Name of query to execute
        output_file: Path to output file
    """
    logger.info(f"Starting PostgreSQL query runner with config: {config_path}, query: {query_name}, output: {output_file}")
    
    try:
        # Load configuration
        config = load_config(config_path)
        
        # Check if postgres config exists
        if 'database' not in config or 'postgres' not in config['database']:
            raise Exception(f"{ErrorCodes.MISSING_DB_CONFIG}: PostgreSQL configuration not found in config file")
        
        # Parse database configuration
        postgres_config_str = config['database']['postgres']
        db_config = parse_postgres_config(postgres_config_str)
        
        # Get query
        query = get_query_from_config(config, query_name)
        
        # Execute query and save results
        with get_db_connection(db_config) as connection:
            results, column_names = execute_query(connection, query)
            write_results_to_file(results, column_names, output_file)
        
        logger.info("PostgreSQL query runner completed successfully")
        
    except Exception as e:
        logger.error(f"PostgreSQL query runner failed: {str(e)}")
        raise


def main():
    """Main entry point for command line usage."""
    parser = argparse.ArgumentParser(description='PostgreSQL Query Runner')
    parser.add_argument('config_file', help='Path to configuration YAML file')
    parser.add_argument('query_name', help='Name of query to execute')
    parser.add_argument('output_file', help='Path to output file')
    
    args = parser.parse_args()
    
    try:
        run_postgres_query(args.config_file, args.query_name, args.output_file)
        print(f"Query executed successfully. Results saved to {args.output_file}")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()