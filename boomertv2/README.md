# PostgreSQL to Neo4j Pipeline

A comprehensive Python pipeline for connecting to PostgreSQL servers, executing queries, and generating Neo4j graph models using MCP (Model Context Protocol).

## Project Structure

```
├── src/                          # Source code
│   ├── postgres_query_runner.py # PostgreSQL query execution
│   ├── neo4j_model_generator.py # Neo4j model generation
│   └── neo4j_data_loader.py     # Neo4j data loading
├── tests/                        # Unit tests
│   ├── test_postgres_query_runner.py
│   ├── test_neo4j_model_generator.py
│   └── test_neo4j_data_loader.py
├── config/                       # Configuration files
│   ├── config_boomer_load.yml    # Data loading configuration
│   ├── config_boomer_model.yml   # Model generation configuration
│   ├── environment.yml           # Conda environment
│   └── docker-compose-neo4j-mcp.yml
├── scripts/                      # Utility scripts
│   ├── debug_chunking.py         # Debug text chunking
│   ├── load_embeddings_to_neo4j.py
│   └── reset_neo4j_database.sh
├── output/                       # Generated outputs
│   ├── data/                     # Data files and models
│   ├── metrics/                  # Load metrics
│   └── logs/                     # Log files
├── sql/                          # SQL and Cypher queries
│   ├── *.cypher                  # Cypher query files
│   └── *.cql                     # CQL query files
└── docs/                         # Documentation
    └── *.md                      # Markdown documentation
```

## Features

### PostgreSQL Query Runner
- Load configuration from YAML files
- Execute named queries from configuration
- Save results to CSV files
- Comprehensive logging and error handling
- Unique error codes for debugging
- Unit tests for all functions
- Can be used as standalone script or imported as module

### Neo4j Model Generator
- Inherits from PostgreSQL Query Runner
- Generates Neo4j graph models from PostgreSQL data
- Uses MCP Neo4j data modeling service
- Outputs structured JSON models
- Supports timestamp-based file naming
- Comprehensive error handling with unique error codes

### Neo4j Data Loader
- Inherits from PostgreSQL Query Runner
- Loads data from PostgreSQL into Neo4j based on generated models
- Uses MCP Neo4j Cypher service for query generation
- Supports vector embeddings with automatic text chunking
- Generates comprehensive load metrics
- Handles both nodes and relationships with best practices
- Comprehensive error handling and logging

## Installation

### Using Conda (Recommended)
```bash
# Create main environment
conda env create -f config/environment.yml
conda activate postgres-neo4j-pipeline

# Or create specific functionality environments
conda env create -f config/environment_postgres.yml  # PostgreSQL functionality only
conda env create -f config/environment_neo4j.yml     # Neo4j functionality only
```

### Using Pip
```bash
pip install -r requirements.txt
```

## Usage

### PostgreSQL Query Runner

#### Command Line
```bash
python src/postgres_query_runner.py config/config_boomer_load.yml trending output/data/sample_data.txt
```

#### As a Module
```python
from src.postgres_query_runner import run_postgres_query

run_postgres_query('config/config_boomer_load.yml', 'trending', 'output/data/output.csv')
```

### Neo4j Model Generator

#### Command Line
```bash
python src/neo4j_model_generator.py config/config_boomer_model.yml trending output/data/neo4j_model_20250807.json
```

#### As a Module
```python
from src.neo4j_model_generator import Neo4jModelGenerator

generator = Neo4jModelGenerator()
generator.generate_neo4j_model_from_query('config/config_boomer_model.yml', 'trending', 'output/data/model.json')
```

### Neo4j Data Loader

#### Command Line
```bash
python src/neo4j_data_loader.py config/config_boomer_load.yml output/data/neo4j_model_20250807.json output/metrics/neo4j_load_metrics_20250807.txt
```

#### As a Module
```python
from src.neo4j_data_loader import Neo4jDataLoader

loader = Neo4jDataLoader()
loader.load_data_to_neo4j('config/config_boomer_load.yml', 'output/data/model.json', 'output/metrics/metrics.txt')
```

## Configuration Format

```yaml
database:
  postgres: |
    host: your-host
    port: 5432
    database: your-database
    user: your-username
    password: your-password
  neo4j: |
    host: localhost
    port: 7687
    database: neo4j
    user: neo4j
    password: password123

queries:
  trending: 'SELECT * FROM structured_content LIMIT 10;'
  users: 'SELECT id, name, email FROM users;'
```

## Running Tests

```bash
# Test PostgreSQL functionality
python -m unittest tests.test_postgres_query_runner -v

# Test Neo4j functionality
python -m unittest tests.test_neo4j_model_generator -v

# Test Neo4j loader functionality
python -m unittest tests.test_neo4j_data_loader -v

# Run all tests
python -m unittest discover tests -v
```

## Error Codes

### PostgreSQL Query Runner (ERR_001 - ERR_007)
- ERR_001: Configuration file read error
- ERR_002: Configuration parsing error
- ERR_003: Database connection error
- ERR_004: Query execution error
- ERR_005: File write error
- ERR_006: Invalid query name
- ERR_007: Missing database configuration

### Neo4j Model Generator (ERR_N001 - ERR_N007)
- ERR_N001: MCP connection error
- ERR_N002: MCP execution error
- ERR_N003: Data processing error
- ERR_N004: Model generation error
- ERR_N005: JSON serialization error
- ERR_N006: Timestamp generation error
- ERR_N007: MCP tool not available

### Neo4j Data Loader (ERR_L001 - ERR_L009)
- ERR_L001: Neo4j connection error
- ERR_L002: Neo4j execution error
- ERR_L003: Model loading error
- ERR_L004: Text chunking error
- ERR_L005: Embedding generation error
- ERR_L006: MCP connection error
- ERR_L007: MCP execution error
- ERR_L008: Metrics write error
- ERR_L009: Data validation error

## Output Formats

### PostgreSQL Query Results
- CSV format with headers
- UTF-8 encoding
- Handles NULL values appropriately

### Neo4j Model JSON Structure
```json
{
  "model_info": {
    "generated_by": "Neo4j Model Generator",
    "generated_at": "2025-01-01T00:00:00",
    "source_table_columns": ["id", "title", "content"],
    "total_records": 100
  },
  "nodes": [
    {
      "label": "Content",
      "properties": [
        {"name": "id", "type": "string", "unique": true},
        {"name": "title", "type": "string", "indexed": true}
      ]
    }
  ],
  "relationships": [],
  "constraints": [
    {
      "type": "UNIQUE",
      "node_label": "Content",
      "property": "id",
      "cypher": "CREATE CONSTRAINT content_id_unique IF NOT EXISTS FOR (n:Content) REQUIRE n.id IS UNIQUE"
    }
  ],
  "indexes": [],
  "import_queries": [
    {
      "description": "Basic import from CSV",
      "cypher": "LOAD CSV WITH HEADERS FROM 'file:///data.csv' AS row CREATE (n:Content {id: row.id, title: row.title})"
    }
  ]
}
```

## Logging

Both programs use Python's logging module with INFO level by default. Logs include:
- Function names and line numbers
- Timestamps
- Detailed error messages with unique error codes
- Execution flow tracking

## Architecture

```
PostgresQueryRunner (Base Class)
    ├── Database connection management
    ├── Query execution
    ├── Result processing
    └── File output
    
Neo4jModelGenerator (Inherits from PostgresQueryRunner)
    ├── Data preparation for modeling
    ├── MCP service integration
    ├── Neo4j model generation
    └── JSON output formatting
```

## CLI Commands Reference

### Environment Setup
```bash
# Create and activate main environment
conda env create -f config/environment.yml
conda activate postgres-neo4j-pipeline

# Create PostgreSQL-only environment
conda env create -f config/environment_postgres.yml
conda activate postgres-functionality

# Create Neo4j-only environment
conda env create -f config/environment_neo4j.yml
conda activate neo4j-modeling-functionality

# Create Neo4j Loader-only environment
conda env create -f config/environment_neo4j_loader.yml
conda activate neo4j-loader-functionality
```

### Running Applications
```bash
# PostgreSQL Query Runner
python src/postgres_query_runner.py config/config_boomer_load.yml trending output/data/sample_data.txt
python src/postgres_query_runner.py config/config_boomer_load.yml users output/data/user_data.csv

# Neo4j Model Generator
python src/neo4j_model_generator.py config/config_boomer_model.yml trending output/data/neo4j_model_$(date +%Y%m%d_%H%M%S).json
python src/neo4j_model_generator.py config/config_boomer_model.yml users output/data/neo4j_user_model.json

# Neo4j Data Loader
python src/neo4j_data_loader.py config/config_boomer_load.yml output/data/neo4j_model_20250807.json output/metrics/neo4j_load_metrics_$(date +%Y%m%d_%H%M%S).txt
python src/neo4j_data_loader.py config/config_boomer_load.yml output/data/neo4j_user_model.json output/metrics/neo4j_user_metrics.txt
```

### Testing
```bash
# Run all tests
python -m unittest discover -v

# Run specific test files
python -m unittest tests.test_postgres_query_runner -v
python -m unittest tests.test_neo4j_model_generator -v
python -m unittest tests.test_neo4j_data_loader -v

# Run tests with coverage
pip install pytest-cov
pytest --cov=. --cov-report=html
```

### Docker Operations
```bash
# Start Neo4j and MCP services
docker-compose -f config/docker-compose-neo4j-mcp.yml up -d

# Stop services
docker-compose -f config/docker-compose-neo4j-mcp.yml down

# View logs
docker-compose -f config/docker-compose-neo4j-mcp.yml logs
```

### Development
```bash
# Format code
black src/ tests/ scripts/

# Lint code
flake8 src/ tests/ scripts/

# Install development dependencies
pip install -r requirements.txt
```