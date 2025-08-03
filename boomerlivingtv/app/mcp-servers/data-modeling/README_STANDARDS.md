# Cypher Standards Implementation

This system enforces consistent Cypher query standards and best practices for Neo4j database operations.

## 🎯 Overview

The standards system consists of:
- **Configuration**: `cypher_standards.yaml` - Defines all rules and standards
- **Validator**: `cypher_validator.py` - Validates queries against standards
- **Generator**: Creates standards-compliant queries automatically
- **Integration**: Built into the MCP server for automatic enforcement

## 📋 Standards Enforced

### 1. Naming Conventions
- **Node Labels**: PascalCase (e.g., `Author`, `Article`)
- **Relationship Types**: UPPER_SNAKE_CASE (e.g., `WROTE`, `BELONGS_TO`)
- **Properties**: snake_case (e.g., `created_date`, `author_name`)

### 2. Query Structure
- **Parameterized Queries**: Use `$parameter` syntax
- **LIMIT Clauses**: Required for potentially large result sets
- **Comments**: Required for complex queries
- **Formatting**: Consistent indentation and line length

### 3. Performance
- **Index Suggestions**: Auto-suggest indexes for queried properties
- **Cartesian Product Detection**: Warn about potential performance issues
- **Query Complexity**: Monitor and limit complex operations

### 4. Security
- **Injection Prevention**: Detect potential injection vulnerabilities
- **Sensitive Data**: Identify and warn about sensitive data patterns
- **Access Control**: Enforce role-based access patterns (optional)

## 🛠️ Usage

### Basic Validation

```python
from cypher_validator import CypherStandardsValidator

validator = CypherStandardsValidator()
results = validator.validate_query(your_query)

for result in results:
    print(f"{result.level}: {result.message}")
```

### Standards-Compliant Generation

```python
from cypher_validator import CypherGenerator

generator = CypherGenerator()

# Generate node creation query
node_query = generator.generate_create_node_query("Author", {
    "name": "John Doe",
    "email": "john@example.com"
})

# Generate relationship query
rel_query = generator.generate_create_relationship_query(
    "Author", "Article", "WROTE"
)
```

### MCP Server Integration

The standards are automatically enforced when using the MCP server tools:

```bash
# Validate a query
mcp call validate_cypher_query '{"query": "CREATE (a:author {name: \"test\"})"}'

# Generate compliant query
mcp call generate_standards_compliant_query '{
    "operation": "create_node",
    "parameters": {"node_type": "Author", "properties": {"name": "string"}}
}'
```

## ⚙️ Configuration

### Customizing Standards

Edit `cypher_standards.yaml` to customize rules:

```yaml
naming_conventions:
  nodes:
    label_case: "PascalCase"  # Change to "snake_case" if needed
    max_label_length: 50      # Adjust length limits
    
query_structure:
  patterns:
    require_parameters: true  # Enforce parameterized queries
    default_limit: 1000      # Default LIMIT value
```

### Adding Custom Rules

Add custom validation rules:

```yaml
validation_rules:
  custom_rules:
    - name: "require_created_date"
      description: "All nodes must have created_date property"
      pattern: "created_date:\\s*datetime\\(\\)"
      required: true
```

### Template Customization

Modify query templates:

```yaml
templates:
  create_node: |
    // Custom node creation template
    MERGE (n:{node_type} {{
      {properties},
      created_date: datetime(),
      updated_date: datetime()
    }})
    RETURN n
```

## 🧪 Testing

Run the test suite to verify standards enforcement:

```bash
python test_standards.py
```

This will test:
- Query validation with various compliance levels
- Standards-compliant query generation
- Automatic fixing of common issues

## 📊 Validation Levels

### ERROR
- **Naming Convention Violations**: Wrong case for labels/relationships
- **Security Issues**: Potential injection vulnerabilities
- **Dangerous Operations**: DELETE without WHERE clause

### WARNING
- **Performance Issues**: Missing indexes, potential Cartesian products
- **Best Practice Violations**: Non-parameterized queries
- **Sensitive Data**: Potential exposure of sensitive information

### INFO
- **Optimization Suggestions**: Index recommendations
- **Formatting Issues**: Line length, indentation
- **Enhancement Opportunities**: Query improvements

## 🔧 Integration Examples

### Automatic Validation in CI/CD

```yaml
# .github/workflows/cypher-validation.yml
name: Validate Cypher Queries
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Validate Cypher
        run: |
          python -m cypher_validator validate_directory ./queries/
```

### Pre-commit Hook

```bash
#!/bin/sh
# .git/hooks/pre-commit
python -m cypher_validator validate_staged_files
```

### IDE Integration

Configure your IDE to use the validator for real-time feedback:

```json
// VS Code settings.json
{
    "cypher.validator.enabled": true,
    "cypher.validator.standards_file": "./cypher_standards.yaml"
}
```

## 📈 Benefits

1. **Consistency**: All team members follow the same standards
2. **Performance**: Automatic optimization suggestions
3. **Security**: Built-in security best practices
4. **Maintainability**: Readable, well-structured queries
5. **Quality**: Reduced bugs and improved reliability

## 🚀 Advanced Features

### Dynamic Rule Loading
Load different standards for different environments:

```python
# Development standards (more lenient)
dev_validator = CypherStandardsValidator("standards_dev.yaml")

# Production standards (strict)
prod_validator = CypherStandardsValidator("standards_prod.yaml")
```

### Custom Validators
Extend the validator with custom rules:

```python
class CustomCypherValidator(CypherStandardsValidator):
    def validate_business_rules(self, query: str):
        # Add your custom business logic validation
        pass
```

### Metrics and Reporting
Track compliance metrics:

```python
validator = CypherStandardsValidator()
metrics = validator.get_compliance_metrics(query_list)
print(f"Compliance Score: {metrics.compliance_percentage}%")
```

## 🤝 Contributing

To add new standards or improve existing ones:

1. Update `cypher_standards.yaml` with new rules
2. Add validation logic in `cypher_validator.py`
3. Update templates if needed
4. Add tests in `test_standards.py`
5. Update this documentation

## 📚 Resources

- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/)
- [Neo4j Performance Tuning](https://neo4j.com/docs/operations-manual/current/performance/)
- [Graph Database Best Practices](https://neo4j.com/developer/guide-data-modeling/)

---

**Note**: These standards are designed to be flexible and customizable. Adjust them according to your team's needs and project requirements.