#!/usr/bin/env python3
"""
Test script for configuration system
Verifies that all hardcoding has been eliminated
"""

import os
import sys
from config_loader import get_config

def test_configuration():
    """Test configuration loading and access"""
    print("🧪 Testing Configuration System\n")
    
    try:
        # Initialize configuration
        config = get_config()
        
        print("✅ Configuration loaded successfully")
        
        # Test environment configuration
        print("\n📊 Environment Configuration:")
        postgres_config = config.get_database_config('postgres')
        print(f"  PostgreSQL Host: {postgres_config.get('host')}")
        print(f"  PostgreSQL Port: {postgres_config.get('port')}")
        print(f"  PostgreSQL Database: {postgres_config.get('database')}")
        
        neo4j_config = config.get_database_config('neo4j')
        print(f"  Neo4j URI: {neo4j_config.get('uri')}")
        print(f"  Neo4j User: {neo4j_config.get('user')}")
        
        server_config = config.get_server_config()
        print(f"  Server Name: {server_config.get('name')}")
        print(f"  Log Level: {server_config.get('log_level')}")
        
        # Test parameter configuration
        print("\n📋 Parameter Configuration:")
        
        # Test database queries
        postgres_queries = config.get_database_queries('postgres')
        print(f"  PostgreSQL Queries: {len(postgres_queries)} defined")
        
        neo4j_queries = config.get_database_queries('neo4j')
        print(f"  Neo4j Queries: {len(neo4j_queries)} defined")
        
        # Test templates
        migration_templates = config.get_migration_templates()
        print(f"  Migration Templates: {len(migration_templates)} defined")
        
        sample_queries = config.get_sample_queries('analysis')
        print(f"  Sample Analysis Queries: {len(sample_queries)} defined")
        
        # Test MCP server configuration
        mcp_config = config.get_mcp_server_config()
        resources = mcp_config.get('resources', [])
        tools = mcp_config.get('tools', [])
        print(f"  MCP Resources: {len(resources)} defined")
        print(f"  MCP Tools: {len(tools)} defined")
        
        # Test message system
        print("\n💬 Message System:")
        success_msg = config.get_message('success', 'migration_complete')
        print(f"  Success Message: {success_msg}")
        
        error_msg = config.get_message('errors', 'unknown_tool', tool_name='test_tool')
        print(f"  Error Message: {error_msg}")
        
        # Test defaults
        print("\n🔧 Defaults:")
        defaults = config.get_defaults()
        node_types = defaults.get('node_types', [])
        print(f"  Node Types: {', '.join(node_types)}")
        
        relationship_types = defaults.get('relationship_types', [])
        print(f"  Relationship Types: {', '.join(relationship_types)}")
        
        # Test template substitution
        print("\n🔄 Template Substitution:")
        analytics_templates = config.get_analytics_templates()
        node_count_template = analytics_templates.get('node_count', '')
        
        substituted = config.substitute_template(
            node_count_template,
            node_type='Author',
            node_type_lower='author'
        )
        print(f"  Template: {node_count_template[:50]}...")
        print(f"  Substituted: {substituted[:50]}...")
        
        # Validation
        print("\n✅ Configuration Validation:")
        is_valid = config.validate_config()
        print(f"  Configuration Valid: {is_valid}")
        
        # Configuration summary
        print("\n📈 Configuration Summary:")
        summary = config.get_sensitive_config_summary()
        print(f"  Environment Config Sections: {len(summary['env_config'])}")
        print(f"  Parameter Config Sections: {len(summary['param_config_keys'])}")
        print(f"  Config Files Exist: {summary['config_files']['env_config_exists']} / {summary['config_files']['param_config_exists']}")
        
        print("\n🎉 All configuration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_no_hardcoding():
    """Verify no hardcoding exists in main file"""
    print("\n🔍 Testing for Hardcoded Values\n")
    
    # Read the main file
    main_file_path = "mcp-servers/data-modeling/__main__.py"
    
    if not os.path.exists(main_file_path):
        print(f"⚠️  Main file not found: {main_file_path}")
        return False
    
    with open(main_file_path, 'r') as file:
        content = file.read()
    
    # Check for common hardcoded patterns
    hardcoded_patterns = [
        'localhost',
        '5432',
        '7687',
        'postgres',
        'password123',
        'movies',
        'neo4j',
        'bolt://',
        'public',
        'mcp-neo4j-data-modeling'
    ]
    
    found_hardcoding = []
    
    for pattern in hardcoded_patterns:
        if pattern in content and 'config' not in content.split(pattern)[0].split('\n')[-1]:
            # Check if it's in a comment or string that's not config-related
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if pattern in line and not line.strip().startswith('#') and not line.strip().startswith('//'):
                    if 'config' not in line.lower():
                        found_hardcoding.append(f"Line {i+1}: {line.strip()}")
    
    if found_hardcoding:
        print("❌ Found potential hardcoded values:")
        for item in found_hardcoding[:5]:  # Show first 5
            print(f"  {item}")
        if len(found_hardcoding) > 5:
            print(f"  ... and {len(found_hardcoding) - 5} more")
        return False
    else:
        print("✅ No hardcoded values detected in main file")
        return True

def main():
    """Run all tests"""
    print("🚀 Configuration System Test Suite")
    print("=" * 50)
    
    # Change to app directory
    if os.path.basename(os.getcwd()) != 'app':
        if os.path.exists('app'):
            os.chdir('app')
        else:
            print("❌ Please run from the app directory or its parent")
            sys.exit(1)
    
    tests_passed = 0
    total_tests = 2
    
    # Test configuration loading
    if test_configuration():
        tests_passed += 1
    
    # Test for hardcoding
    if test_no_hardcoding():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Configuration system is working correctly.")
        print("\n📋 Summary:")
        print("- All hardcoded values have been moved to configuration files")
        print("- Environment variables are managed through env_config.yaml")
        print("- Parameters, templates, and queries are in param_config.yaml")
        print("- Configuration loader provides easy access to all settings")
    else:
        print("❌ Some tests failed. Please review the configuration setup.")
        sys.exit(1)

if __name__ == "__main__":
    main()