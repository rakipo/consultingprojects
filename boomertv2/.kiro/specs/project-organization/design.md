# Design Document

## Overview

This design document outlines the reorganization of the Neo4j Data Loader project into a clean, maintainable structure. The design follows Python best practices and creates clear separation between different types of files.

## Architecture

### New Directory Structure

```
project-root/
├── config/                     # Configuration files
│   ├── config_boomer_load.yml
│   ├── config_boomer_model.yml
│   ├── config_boomer_temp.yml
│   ├── environment_neo4j_loader.yml
│   ├── environment_neo4j.yml
│   ├── environment_postgres.yml
│   ├── environment.yml
│   └── docker-compose-neo4j-mcp.yml
├── tests/                      # Test files
│   ├── __init__.py
│   ├── test_chunk_config.py
│   ├── test_config_loading.py
│   ├── test_neo4j_data_loader.py
│   ├── test_neo4j_loader_config.py
│   ├── test_neo4j_model_generator.py
│   ├── test_postgres_query_runner.py
│   ├── test_trending_query_simple.py
│   └── test_trending_query.py
├── output/                     # Generated output files
│   ├── metrics/
│   │   ├── neo4j_load_metrics_20250807.txt
│   │   └── test_metrics.txt
│   ├── data/
│   │   ├── embeddings_output.json
│   │   ├── neo4j_model_best_practices_20250807_200801.json
│   │   └── sample_data.txt
│   └── logs/
├── scripts/                    # Utility and debug scripts
│   ├── debug_chunk_loading_offline.py
│   ├── debug_chunk_loading.py
│   ├── debug_chunking.py
│   ├── load_embeddings_to_neo4j.py
│   ├── reset_neo4j_database.sh
│   └── verify_neo4j_chunks.py
├── sql/                        # SQL and Cypher queries
│   ├── cosine_similarity_functions.cypher
│   ├── create_neo4j_schema.cypher
│   ├── cypher_queries_scrap.cql
│   └── test_embedding_insert.cypher
├── src/                        # Main source code
│   ├── __init__.py
│   ├── neo4j_data_loader.py
│   ├── neo4j_model_generator.py
│   └── postgres_query_runner.py
├── docs/                       # Documentation
│   ├── neo4j_best_practices_summary.md
│   └── neo4j_data_loader_summary.md
├── requirements.txt
└── README.md
```

## Components and Interfaces

### Configuration Management

**Component:** Configuration Loader
- **Location:** `config/` directory
- **Interface:** All scripts will use relative paths to load configurations
- **Pattern:** `config/filename.yml` instead of `./filename.yml`

### Test Organization

**Component:** Test Suite
- **Location:** `tests/` directory
- **Interface:** Python test discovery will find tests in the new location
- **Pattern:** Import statements will use `sys.path` manipulation or package imports

### Output Management

**Component:** Output Handler
- **Location:** `output/` directory with subdirectories
- **Interface:** Scripts will create output directories if they don't exist
- **Pattern:** All generated files go to appropriate output subdirectories

### Source Code Organization

**Component:** Main Application Code
- **Location:** `src/` directory
- **Interface:** Clean separation of core functionality
- **Pattern:** Proper Python package structure with `__init__.py` files

## Data Models

### File Path Configuration

```python
# Path configuration constants
CONFIG_DIR = "config"
OUTPUT_DIR = "output"
TESTS_DIR = "tests"
SRC_DIR = "src"
SCRIPTS_DIR = "scripts"
SQL_DIR = "sql"
DOCS_DIR = "docs"

# Output subdirectories
METRICS_DIR = os.path.join(OUTPUT_DIR, "metrics")
DATA_DIR = os.path.join(OUTPUT_DIR, "data")
LOGS_DIR = os.path.join(OUTPUT_DIR, "logs")
```

### Import Path Updates

```python
# Before reorganization
from neo4j_data_loader import Neo4jDataLoader

# After reorganization
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from neo4j_data_loader import Neo4jDataLoader
```

## Error Handling

### Missing Directory Handling

- **Strategy:** Create directories automatically if they don't exist
- **Implementation:** Use `os.makedirs(path, exist_ok=True)` pattern
- **Fallback:** Graceful error messages if directory creation fails

### Path Resolution

- **Strategy:** Use relative paths from project root
- **Implementation:** Calculate paths relative to script location
- **Fallback:** Environment variable override for custom paths

### Import Resolution

- **Strategy:** Dynamic path manipulation for imports
- **Implementation:** Add source directories to `sys.path`
- **Fallback:** Clear error messages for missing modules

## Testing Strategy

### Test Discovery

- **Approach:** Use pytest with automatic test discovery
- **Configuration:** Update pytest configuration for new test location
- **Execution:** Tests run from project root with `pytest tests/`

### Import Testing

- **Approach:** Verify all imports work after reorganization
- **Implementation:** Test each module's import statements
- **Validation:** Ensure no circular dependencies

### Path Testing

- **Approach:** Test file path resolution in different environments
- **Implementation:** Unit tests for path calculation functions
- **Coverage:** Test both relative and absolute path scenarios

## Migration Strategy

### Phase 1: Create Directory Structure
1. Create new directories (`config/`, `tests/`, `output/`, etc.)
2. Add `__init__.py` files where needed
3. Create output subdirectories

### Phase 2: Move Files
1. Move configuration files to `config/`
2. Move test files to `tests/`
3. Move output files to appropriate `output/` subdirectories
4. Move source files to `src/`
5. Move utility scripts to `scripts/`
6. Move SQL/Cypher files to `sql/`
7. Move documentation to `docs/`

### Phase 3: Update References
1. Update import statements in all Python files
2. Update configuration file paths in scripts
3. Update output file paths in scripts
4. Update README and documentation

### Phase 4: Validation
1. Run all tests to ensure they pass
2. Execute main scripts to verify functionality
3. Check that all file paths resolve correctly
4. Validate that outputs are generated in correct locations