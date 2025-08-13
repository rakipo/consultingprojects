#!/usr/bin/env python3
"""
Test script to verify that all imports and functionality from postgres_connect_and_analyse.ipynb work correctly.
"""

import sys
import os
import pandas as pd
import psycopg2
import yaml
from typing import Optional, Dict, Any

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

def test_imports():
    """Test all required imports."""
    print("Testing imports...")
    
    try:
        import pandas as pd
        print("✅ pandas imported successfully")
    except ImportError as e:
        print(f"❌ Error importing pandas: {e}")
        return False

    try:
        import psycopg2
        print(f"✅ psycopg2 imported successfully (version: {psycopg2.__version__})")
    except ImportError as e:
        print(f"❌ Error importing psycopg2: {e}")
        return False

    try:
        import yaml
        print("✅ yaml imported successfully")
    except ImportError as e:
        print(f"❌ Error importing yaml: {e}")
        return False

    try:
        from postgres_query_runner import PostgresQueryRunner
        print("✅ postgres_query_runner imported successfully")
    except ImportError as e:
        print(f"❌ Error importing postgres_query_runner: {e}")
        return False

    return True

def test_config_loading():
    """Test configuration loading."""
    print("\nTesting configuration loading...")
    
    try:
        config_path = '../config/config_boomer_load.yml'
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        print(f"✅ Configuration loaded successfully from {config_path}")
        print(f"Available sections: {list(config.keys())}")
        return True
    except FileNotFoundError:
        print(f"❌ Configuration file not found: {config_path}")
        return False
    except yaml.YAMLError as e:
        print(f"❌ Error parsing YAML file: {e}")
        return False

def test_postgres_connection():
    """Test PostgreSQL connection."""
    print("\nTesting PostgreSQL connection...")
    
    try:
        # Load config
        config_path = '../config/config_boomer_load.yml'
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        
        # Parse PostgreSQL config
        postgres_config_str = config['database']['postgres']
        db_config = {}
        for line in postgres_config_str.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                db_config[key.strip()] = value.strip()
        
        # Test connection
        connection = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password']
        )
        
        print(f"✅ Connected to PostgreSQL database: {db_config['database']}")
        
        # Test simple query
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM structured_content")
        count = cursor.fetchone()[0]
        print(f"✅ Query executed successfully. Total records: {count}")
        
        cursor.close()
        connection.close()
        print("✅ Database connection closed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error testing PostgreSQL connection: {e}")
        return False

def main():
    """Run all tests."""
    print("="*60)
    print("Testing postgres_connect_and_analyse.ipynb functionality")
    print("="*60)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed!")
        return False
    
    # Test config loading
    if not test_config_loading():
        print("\n❌ Config loading tests failed!")
        return False
    
    # Test PostgreSQL connection
    if not test_postgres_connection():
        print("\n❌ PostgreSQL connection tests failed!")
        return False
    
    print("\n" + "="*60)
    print("✅ All tests passed! The notebook should work correctly.")
    print("="*60)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
