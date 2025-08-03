#!/usr/bin/env python3
"""
Test script for Cypher standards validation and generation
"""

from cypher_validator import CypherStandardsValidator, CypherGenerator

def test_validation():
    """Test query validation against standards"""
    print("🔍 Testing Cypher Standards Validation\n")
    
    validator = CypherStandardsValidator()
    
    # Test queries with various issues
    test_queries = [
        {
            "name": "Non-compliant query",
            "query": """
            CREATE (author:author {Name: "John Doe", Email: "john@example.com"})
            MATCH (a:article)-[wrote]->(b:Author)
            DELETE a
            """
        },
        {
            "name": "Better query with some issues",
            "query": """
            MERGE (author:Author {name: $name, email: $email})
            MATCH (a:Article)-[r:WROTE]->(b:Author)
            WHERE a.title CONTAINS $search
            RETURN a, b
            """
        },
        {
            "name": "Standards-compliant query",
            "query": """
            // Create Author node with validation
            MERGE (author:Author {
              name: $name,
              email: $email,
              created_date: datetime()
            })
            RETURN author
            LIMIT $limit
            """
        }
    ]
    
    for test in test_queries:
        print(f"📝 Testing: {test['name']}")
        print(f"Query:\n{test['query']}")
        
        results = validator.validate_query(test['query'])
        
        if results:
            print("❌ Validation Issues Found:")
            for result in results:
                print(f"  {result.level.value.upper()}: {result.message}")
                if result.suggestion:
                    print(f"    💡 Suggestion: {result.suggestion}")
        else:
            print("✅ Query passes all validation checks!")
        
        print("-" * 60)

def test_generation():
    """Test standards-compliant query generation"""
    print("\n🏗️  Testing Standards-Compliant Query Generation\n")
    
    generator = CypherGenerator()
    
    # Test node creation
    print("📝 Generated Node Creation Query:")
    node_query = generator.generate_create_node_query("Author", {
        "name": "John Doe",
        "email": "john@example.com",
        "specialization": "Healthcare"
    })
    print(node_query)
    print("-" * 60)
    
    # Test relationship creation
    print("📝 Generated Relationship Creation Query:")
    rel_query = generator.generate_create_relationship_query(
        "Author", "Article", "wrote",
        source_property="name",
        target_property="id"
    )
    print(rel_query)
    print("-" * 60)
    
    # Test search query
    print("📝 Generated Search Query:")
    search_query = generator.generate_search_query("Article", "title")
    print(search_query)
    print("-" * 60)

def test_validation_and_fix():
    """Test validation with automatic fixing"""
    print("\n🔧 Testing Validation with Auto-Fix\n")
    
    generator = CypherGenerator()
    
    problematic_query = """
    CREATE (author:author {Name: "John", Email: "john@test.com"})
    MATCH (a:article)-[wrote]->(b:Author)
    RETURN a, b
    """
    
    print("📝 Original Query:")
    print(problematic_query)
    
    fixed_query, validation_results = generator.validate_and_fix_query(problematic_query)
    
    print("\n🔍 Validation Results:")
    for result in validation_results:
        print(f"  {result.level.value.upper()}: {result.message}")
        if result.suggestion:
            print(f"    💡 Suggestion: {result.suggestion}")
    
    print(f"\n🔧 Fixed Query:")
    print(fixed_query)

if __name__ == "__main__":
    test_validation()
    test_generation()
    test_validation_and_fix()
    
    print("\n🎉 Standards testing complete!")
    print("\n📋 Summary:")
    print("- Standards are defined in cypher_standards.yaml")
    print("- Validator checks naming conventions, structure, performance, and security")
    print("- Generator creates standards-compliant queries")
    print("- Integration with MCP server enforces standards automatically")