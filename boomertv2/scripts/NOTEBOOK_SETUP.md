# PostgreSQL Analysis Notebook Setup

## Overview

The `postgres_connect_and_analyse.ipynb` notebook provides functionality to connect to PostgreSQL and run queries with results returned as pandas DataFrames.

## Environment Setup

### Prerequisites

1. **Conda Environment**: Make sure you're using the `postgres-neo4j-pipeline` conda environment
2. **Required Packages**: The notebook requires the following packages:
   - `pandas`
   - `psycopg2-binary==2.9.7`
   - `PyYAML==6.0.1`

### Installation Steps

1. **Activate the correct environment**:
   ```bash
   conda activate postgres-neo4j-pipeline
   ```

2. **Install missing packages** (if needed):
   ```bash
   pip install pandas PyYAML
   ```

3. **Verify installation**:
   ```bash
   python test_notebook_imports.py
   ```

## Running the Notebook

1. **Start Jupyter** from the `boomertv2` directory:
   ```bash
   conda activate postgres-neo4j-pipeline
   cd boomertv2
   jupyter notebook scripts/postgres_connect_and_analyse.ipynb
   ```

2. **Run all cells** in order to:
   - Install required packages
   - Import libraries
   - Load configuration
   - Test PostgreSQL connection
   - Execute sample queries

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError: No module named 'pandas'**
   - **Solution**: Make sure you're in the `postgres-neo4j-pipeline` conda environment
   - **Command**: `conda activate postgres-neo4j-pipeline`

2. **Configuration file not found**
   - **Solution**: Make sure you're running the notebook from the `scripts` directory
   - **Path**: The notebook expects `../config/config_boomer_load.yml`

3. **PostgreSQL connection errors**
   - **Solution**: Check that the database is accessible and credentials are correct
   - **Test**: Run `python test_notebook_imports.py` to verify connection

### Testing

Use the provided test script to verify everything works:

```bash
cd scripts
python test_notebook_imports.py
```

This will test:
- ✅ All required imports
- ✅ Configuration file loading
- ✅ PostgreSQL connection
- ✅ Sample query execution

## Features

The notebook provides:

- **Automatic package installation** for missing dependencies
- **Configuration loading** from YAML files
- **PostgreSQL connection** with automatic cleanup
- **Query execution** with pandas DataFrame results
- **Error handling** with detailed error messages
- **Sample queries** for data exploration

## Configuration

The notebook uses configuration from `../config/config_boomer_load.yml` which contains:

- **Database connection parameters** (host, port, database, user, password)
- **Query definitions** for common operations
- **Neo4j loading configuration** for data pipeline operations

## Usage Examples

```python
# Execute any PostgreSQL query
df = execute_postgres_query("SELECT * FROM structured_content LIMIT 10", postgres_config)

# Get record count
count_df = execute_postgres_query("SELECT COUNT(*) FROM structured_content", postgres_config)

# Explore data structure
explore_df = execute_postgres_query("SELECT * FROM structured_content LIMIT 1", postgres_config)
```
