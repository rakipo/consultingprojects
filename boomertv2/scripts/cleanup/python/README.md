# Neo4j Database Reset Script (Python)

This Python script replicates the functionality of the `reset_neo4j_database_remote.sh` shell script, providing a more flexible and maintainable way to reset remote Neo4j databases.

## Features

- 🔗 Connect to remote Neo4j databases using bolt+s protocol
- 🗑️ Delete all nodes and relationships in batches
- 📊 Drop all custom indexes and constraints
- ✅ Verify the reset operation
- 🔧 Configurable through YAML files
- 🛡️ User confirmation before destructive operations
- 📝 Comprehensive logging

## Prerequisites

- Python 3.7 or higher
- Access to a remote Neo4j database
- Neo4j credentials (username, password, URI)

## Installation

1. Navigate to the script directory:
   ```bash
   cd boomertv2/scripts/cleanup/python
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### 1. Credentials Configuration (`config.yaml`)

Edit the `config.yaml` file with your Neo4j connection details:

```yaml
neo4j:
  uri: "bolt+s://your-neo4j-server.com:7687"
  username: "neo4j"
  password: "your_password_here"
  database: "neo4j"
```

**⚠️ Security Warning**: Never commit credentials to version control. Consider using environment variables or a secure secrets manager in production.

### 2. Queries Configuration (`queries.yaml`)

The `queries.yaml` file contains all the Cypher queries used for the reset operation. You can customize these queries as needed for your specific database schema.

## Usage

### Basic Usage

```bash
python reset_neo4j_database_remote.py
```

This will use the default configuration files (`config.yaml` and `queries.yaml`).

### Custom Configuration Files

```bash
python reset_neo4j_database_remote.py --config my_config.yaml --queries my_queries.yaml
```

### Help

```bash
python reset_neo4j_database_remote.py --help
```

## What the Script Does

1. **Connection Test**: Verifies connectivity to the Neo4j database
2. **Data Deletion**: 
   - Deletes all relationships first (to avoid constraint violations)
   - Deletes all nodes in batches of 1000
3. **Index Cleanup**: Drops all custom indexes (excluding system indexes)
4. **Constraint Cleanup**: Drops all constraints (excluding system constraints)
5. **Verification**: Counts remaining nodes and relationships, lists remaining indexes and constraints

## Safety Features

- **Confirmation Required**: The script asks for explicit confirmation before proceeding
- **Batch Processing**: Large deletions are performed in batches to avoid memory issues
- **Error Handling**: Comprehensive error handling with detailed logging
- **Fallback Methods**: Alternative approaches if primary methods fail

## Example Output

```
🔄 Remote Neo4j Database Reset Script
=====================================

This will clear all data from the remote Neo4j database:
  URI: bolt+s://your-neo4j-server.com:7687
  Database: neo4j
  Username: neo4j

⚠️  WARNING: This will permanently delete ALL data in the Neo4j database!
⚠️  This action cannot be undone!

Are you sure you want to clear the remote Neo4j database? (type 'RESET' to confirm): RESET

🗑️ Starting remote Neo4j database reset...

🔗 Connecting to remote Neo4j server...
✅ Successfully connected to Neo4j server
✅ Connection test completed
1️⃣ Clearing all nodes and relationships...
✅ Delete all relationships completed
✅ Delete all nodes completed
2️⃣ Dropping all custom indexes...
✅ Drop custom indexes completed
3️⃣ Dropping all constraints...
✅ Drop all constraints completed
4️⃣ Verification...
Remaining nodes: 0
Remaining relationships: 0
🎉 Remote Neo4j database successfully reset!
✅ Database is now empty and ready for fresh data
```

## Troubleshooting

### Connection Issues

- Verify the Neo4j URI format: `bolt+s://hostname:port`
- Check that the username and password are correct
- Ensure the Neo4j server is accessible from your network
- Verify that the database name exists

### Permission Issues

- Ensure the Neo4j user has sufficient privileges to delete data and drop indexes/constraints
- Check if the database is in read-only mode

### Large Database Issues

- For very large databases, the script uses batch processing to avoid memory issues
- If you encounter timeout issues, consider increasing the connection timeout in the config

## Comparison with Shell Script

| Feature | Shell Script | Python Script |
|---------|-------------|---------------|
| Dependencies | cypher-shell | Python + neo4j driver |
| Configuration | Command line args | YAML files |
| Error Handling | Basic | Comprehensive |
| Logging | Basic | Structured logging |
| Extensibility | Limited | High (object-oriented) |
| Cross-platform | Limited | Full support |
| Testing | Manual | Unit testable |

## Contributing

To extend the script:

1. Add new queries to `queries.yaml`
2. Extend the `Neo4jResetManager` class
3. Add new command-line options if needed
4. Update the documentation

## License

This script is part of the BoomerTV project and follows the same licensing terms.
