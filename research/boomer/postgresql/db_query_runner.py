#!/usr/bin/env python3
"""
PostgreSQL Database Query Runner

This script connects to a PostgreSQL database using configuration from config.py,
reads queries from queries.yml, executes them, and writes results to timestamped output files.
"""

import psycopg2
import yaml
from datetime import datetime
import sys
import argparse
import os


class DatabaseQueryRunner:
    def __init__(self, config_file="config.yml", queries_file="queries.yml"):
        self.connection = None
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create output directory if it doesn't exist
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.output_file = os.path.join(self.output_dir, f"output_{self.timestamp}.txt")
        self.config_file = config_file
        self.queries_file = queries_file
        self.database_config = self.load_config()
    
    def load_config(self):
        """Load database configuration from YAML file"""
        try:
            with open(self.config_file, 'r') as file:
                data = yaml.safe_load(file)
                return data.get('database', {})
        except FileNotFoundError:
            print(f"Error: {self.config_file} not found")
            return {}
        except yaml.YAMLError as e:
            print(f"Error parsing config YAML file: {e}")
            return {}
    
    def connect_to_database(self):
        """Establish connection to PostgreSQL database"""
        if not self.database_config:
            print("Error: No database configuration found")
            return False
            
        try:
            self.connection = psycopg2.connect(**self.database_config)
            print(f"Successfully connected to database: {self.database_config['database']}")
            return True
        except psycopg2.Error as e:
            print(f"Error connecting to database: {e}")
            return False
    
    def load_queries(self):
        """Load queries from YAML file"""
        try:
            with open(self.queries_file, 'r') as file:
                data = yaml.safe_load(file)
                return data.get('queries', [])
        except FileNotFoundError:
            print(f"Error: {self.queries_file} not found")
            return []
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}")
            return []
    
    def execute_query(self, query_info):
        """Execute a single query and return results"""
        if not self.connection:
            return None, "No database connection"
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query_info['sql'])
            
            # Fetch results for SELECT queries
            if query_info['sql'].strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description]
                return {'columns': column_names, 'rows': results}, None
            else:
                # For non-SELECT queries, return affected row count
                return {'affected_rows': cursor.rowcount}, None
                
        except psycopg2.Error as e:
            return None, str(e)
        finally:
            if cursor:
                cursor.close()
    
    def format_results(self, query_info, results, error):
        """Format query results for output"""
        output = []
        output.append("=" * 80)
        output.append(f"Query: {query_info['name']}")
        output.append(f"Description: {query_info['description']}")
        output.append(f"SQL: {query_info['sql']}")
        output.append("-" * 80)
        
        if error:
            output.append(f"ERROR: {error}")
        else:
            if 'columns' in results:
                # Format SELECT query results
                output.append(f"Columns: {', '.join(results['columns'])}")
                output.append(f"Row count: {len(results['rows'])}")
                output.append("")
                
                # Display first 10 rows
                for i, row in enumerate(results['rows'][:10]):
                    output.append(f"Row {i+1}: {row}")
                
                if len(results['rows']) > 10:
                    output.append(f"... and {len(results['rows']) - 10} more rows")
            else:
                # Format non-SELECT query results
                output.append(f"Affected rows: {results['affected_rows']}")
        
        output.append("")
        return "\n".join(output)
    
    def run_all_queries(self):
        """Execute all queries and write results to output file"""
        if not self.connect_to_database():
            return False
        
        queries = self.load_queries()
        if not queries:
            print("No queries found to execute")
            return False
        
        print(f"Executing {len(queries)} queries...")
        print(f"Results will be written to: {self.output_file}")
        
        with open(self.output_file, 'w') as output:
            output.write(f"Database Query Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            output.write(f"Database: {self.database_config.get('database', 'N/A')}\n")
            output.write(f"Host: {self.database_config.get('host', 'N/A')}\n\n")
            
            for i, query_info in enumerate(queries, 1):
                print(f"Executing query {i}/{len(queries)}: {query_info['name']}")
                
                results, error = self.execute_query(query_info)
                formatted_output = self.format_results(query_info, results, error)
                
                output.write(formatted_output)
                
                if error:
                    print(f"  ERROR: {error}")
                else:
                    print(f"  SUCCESS")
        
        self.close_connection()
        print(f"All queries completed. Results saved to {self.output_file}")
        return True
    
    def close_connection(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            print("Database connection closed")


def main():
    """Main function to run the query runner"""
    parser = argparse.ArgumentParser(
        description="PostgreSQL Database Query Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python db_query_runner.py                                    # Use default files
  python db_query_runner.py -c config.yml -q queries.yml      # Specify both files
  python db_query_runner.py --config prod_config.yml          # Use production config
  python db_query_runner.py --queries test_queries.yml        # Use test queries
        """
    )
    
    parser.add_argument(
        '-c', '--config',
        default='config.yml',
        help='Configuration file path (default: config.yml)'
    )
    
    parser.add_argument(
        '-q', '--queries',
        default='queries.yml',
        help='Queries file path (default: queries.yml)'
    )
    
    args = parser.parse_args()
    
    print(f"Using config file: {args.config}")
    print(f"Using queries file: {args.queries}")
    print()
    
    runner = DatabaseQueryRunner(config_file=args.config, queries_file=args.queries)
    
    try:
        success = runner.run_all_queries()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        runner.close_connection()
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        runner.close_connection()
        sys.exit(1)


if __name__ == "__main__":
    main()