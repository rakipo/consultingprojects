# Configuration System - No Hardcoding

This system eliminates all hardcoded values from the application by using YAML configuration files and environment variables.

## 🎯 Overview

All configuration is now managed through two main files:
- **`env_config.yaml`** - Environment variables and their defaults
- **`param_config.yaml`** - Parameters, templates, queries, and static configurations

## 📁 Configuration Files

### `env_config.yaml`
Manages all environment variables with:
- Environment variable names
- Default values
- Type conversion (int, bool, float, list)
- Sensitive data marking
- Descriptions

### `param_config.yaml`
Contains all static configuration:
- Database queries and templates
- Migration templates
- Sample query patterns
- MCP server configuration
- Default values and constants
- Message templates

## 🔧 Usage

### Basic Configuration Access

```python
from config_loader import get_config

config = get_config()

# Database configuration
postgres_config = config.get_database_config('postgres')
neo4j_config = config.get_database_config('neo4j')

# Server configuration
server_config = config.get_server_config()

# Query templates
query = config.get_query_template('sample_queries.analysis', 'productive_authors')

# Messages
message = config.get_message('success', 'migration_complete')
```

### Environment Variables

Set environment variables to override defaults:

```bash
export POSTGRES_HOST=production-db.example.com
export POSTGRES_PORT=5432
export NEO4J_URI=bolt://neo4j-cluster.example.com:7687
export LOG_LEVEL=DEBUG
```

### Template Substitution

```python
template = config.get_analytics_templates()['node_count']
query = config.substitute_template(template, 
    node_type='Author', 
    node_type_lower='author'
)
```

## 🏗️ Configuration Structure

### Environment Configuration (`env_config.yaml`)

```yaml
database:
  postgres:
    host:
      env_var: "POSTGRES_HOST"
      default: "localhost"
      description: "PostgreSQL server hostname"
    port:
      env_var: "POSTGRES_PORT"
      default: 5432
      type: "int"
```

### Parameter Configuration (`param_config.yaml`)

```yaml
database_queries:
  postgres:
    schema_info: |
      SELECT table_name, column_name, data_type, is_nullable
      FROM information_schema.columns
      WHERE table_schema = $schema

sample_queries:
  analysis:
    productive_authors: |
      MATCH (a:Author)-[:WROTE]->(article:Article)
      RETURN a.name, count(article) as article_count
      ORDER BY article_count DESC
      LIMIT $limit
```

## 🔍 Configuration Loader Features

### Type Conversion
- Automatic type conversion (int, float, bool, list)
- Environment variable resolution
- Default value fallback

### Nested Access
```python
# Dot notation for nested values
value = config.get_env_config('database.postgres.host')
query = config.get_param_config('sample_queries.analysis.productive_authors')
```

### Validation
```python
# Validate configuration completeness
is_valid = config.validate_config()
```

### Security
```python
# Get configuration summary without sensitive values
summary = config.get_sensitive_config_summary()
```

## 🧪 Testing

Run the configuration test suite:

```bash
cd app
python test_config.py
```

This will:
- Verify configuration loading
- Check for remaining hardcoded values
- Test template substitution
- Validate configuration completeness

## 📊 Benefits

### 1. **No Hardcoding**
- All values externalized to configuration files
- Easy to modify without code changes
- Environment-specific configurations

### 2. **Type Safety**
- Automatic type conversion
- Validation of required values
- Clear error messages

### 3. **Security**
- Sensitive values marked and masked
- Environment variable support
- No secrets in code

### 4. **Maintainability**
- Centralized configuration
- Clear documentation
- Easy to extend

### 5. **Flexibility**
- Template-based queries
- Environment-specific overrides
- Dynamic configuration loading

## 🔧 Extending Configuration

### Adding New Environment Variables

1. Add to `env_config.yaml`:
```yaml
new_section:
  new_variable:
    env_var: "NEW_ENV_VAR"
    default: "default_value"
    type: "string"
    description: "Description of the variable"
```

2. Access in code:
```python
value = config.get_env_config('new_section.new_variable')
```

### Adding New Templates

1. Add to `param_config.yaml`:
```yaml
new_templates:
  template_name: |
    Template content with {variable} substitution
```

2. Use in code:
```python
template = config.get_param_config('new_templates.template_name')
result = config.substitute_template(template, variable='value')
```

### Adding New Queries

1. Add to `param_config.yaml`:
```yaml
database_queries:
  postgres:
    new_query: |
      SELECT * FROM table WHERE condition = $parameter
```

2. Use in code:
```python
query = config.get_database_queries('postgres')['new_query']
```

## 🚀 Migration from Hardcoded Values

### Before (Hardcoded)
```python
postgres_config = {
    'host': 'localhost',
    'port': 5432,
    'database': 'movies',
    'user': 'postgres',
    'password': 'password123'
}
```

### After (Configuration-Based)
```python
postgres_config = config.get_database_config('postgres')
```

### Environment Override
```bash
export POSTGRES_HOST=production-server
export POSTGRES_DATABASE=production_db
```

## 📋 Configuration Checklist

- [ ] All hardcoded values moved to configuration files
- [ ] Environment variables defined with defaults
- [ ] Sensitive values marked appropriately
- [ ] Templates use parameter substitution
- [ ] Configuration validation passes
- [ ] Tests verify no hardcoding remains

## 🔍 Troubleshooting

### Configuration Not Loading
- Check file paths are correct
- Verify YAML syntax is valid
- Ensure files are readable

### Environment Variables Not Working
- Check environment variable names match `env_config.yaml`
- Verify type conversion is correct
- Check default values are appropriate

### Template Substitution Failing
- Ensure all template variables are provided
- Check template syntax uses `{variable}` format
- Verify parameter names match exactly

## 📚 Best Practices

1. **Always use configuration for**:
   - Database connections
   - Server settings
   - Query templates
   - Default values
   - Messages and prompts

2. **Never hardcode**:
   - Hostnames or IPs
   - Port numbers
   - Database names
   - Passwords or secrets
   - File paths

3. **Use environment variables for**:
   - Environment-specific values
   - Sensitive information
   - Deployment configurations

4. **Use parameter files for**:
   - Static templates
   - Query patterns
   - Default constants
   - Message templates

---

This configuration system ensures complete elimination of hardcoding while providing flexibility, security, and maintainability.