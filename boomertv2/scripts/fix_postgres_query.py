#!/usr/bin/env python3
"""
Improved PostgreSQL query function that handles both SELECT and UPDATE/INSERT/DELETE queries.
Copy this function into your Jupyter notebook to fix the UPDATE query issue.
"""

import pandas as pd
import psycopg2
from typing import Dict

def execute_postgres_query_improved(query: str, config: Dict[str, str]) -> pd.DataFrame:
    """
    Execute a PostgreSQL query and return results as a pandas DataFrame.
    
    Args:
        query: SQL query to execute
        config: PostgreSQL connection configuration
        
    Returns:
        pandas DataFrame containing query results (empty DataFrame for UPDATE/INSERT/DELETE)
    """
    connection = None
    try:
        # Establish connection
        connection = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password']
        )
        
        print(f"Connected to PostgreSQL database: {config['database']}")
        
        # Check if query is a SELECT statement
        query_upper = query.strip().upper()
        if query_upper.startswith('SELECT'):
            # Execute SELECT query and return as DataFrame
            df = pd.read_sql_query(query, connection)
            print(f"Query executed successfully. Retrieved {len(df)} rows.")
            return df
        else:
            # Execute UPDATE/INSERT/DELETE query
            cursor = connection.cursor()
            cursor.execute(query)
            rows_affected = cursor.rowcount
            connection.commit()
            cursor.close()
            print(f"Query executed successfully. {rows_affected} rows affected.")
            return pd.DataFrame()  # Return empty DataFrame for non-SELECT queries
        
    except psycopg2.Error as e:
        print(f"PostgreSQL error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise
    finally:
        if connection:
            connection.close()
            print("Database connection closed.")

# Example usage:
if __name__ == "__main__":
    # Example configuration (replace with your actual config)
    config = {
        'host': '4.150.184.135',
        'port': '5432',
        'database': 'SERP_TREND_DEV_DB',
        'user': 'serptrend_user',
        'password': 'your_password_here'
    }
    
    # Test SELECT query
    select_query = "SELECT COUNT(*) FROM structured_content;"
    print("Testing SELECT query...")
    result = execute_postgres_query_improved(select_query, config)
    print(f"Result: {result}")
    
    # Test UPDATE query
    update_query = "UPDATE structured_content SET status_neo4j = false;"
    print("\nTesting UPDATE query...")
    result = execute_postgres_query_improved(update_query, config)
    print(f"Result: {result}")
