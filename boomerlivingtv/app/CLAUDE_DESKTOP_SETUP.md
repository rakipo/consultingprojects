# Claude Desktop MCP Configuration

This guide shows you how to configure the Neo4j Cypher MCP server for Claude Desktop.

## 🎯 Quick Setup

### Step 1: Install Dependencies
```bash
cd boomerlivingtv/app
python install_dependencies.py
```

### Step 2: Configure Claude Desktop

Add this configuration to your Claude Desktop settings:

**Location of Claude Desktop config file:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

**Configuration to add:**

```json
{
  "mcpServers": {
    "neo4j-cypher": {
      "command": "python",
      "args": ["/Users/ravikiranponduri/Desktop/consultingprojects/boomerlivingtv/app/mcp-servers/cypher/__main__.py"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "password123"
      }
    }
  }
}
```

### Step 3: Start Neo4j Database
```bash
cd boomerlivingtv/app
docker-compose -f docker-compose-mcp.yml up -d neo4j postgres
```

### Step 4: Restart Claude Desktop
Close and reopen Claude Desktop application.

## 🔧 Available MCP Tools

Once configured, you'll have access to these tools in Claude:

### 1. **execute_cypher**
Execute Cypher queries against Neo4j database
```
Parameters:
- query (string): Cypher query to execute
- parameters (object): Query parameters (optional)
```

### 2. **get_database_schema**
Get Neo4j database schema information
```
No parameters required
```

### 3. **search_articles**
Search articles by various criteria
```
Parameters:
- search_type: "author", "domain", "tag", "keyword", "recent"
- search_value: Search term
- limit: Maximum results (default: 10)
```

### 4. **analyze_relationships**
Analyze relationships and patterns
```
Parameters:
- analysis_type: "author_collaboration", "domain_distribution", "tag_analysis", "productivity"
```

### 5. **get_query_template**
Get pre-built Cypher query templates
```
Parameters:
- template_name: Name of the template
```

## 📋 Available Query Templates

- `find_all_authors` - List all authors
- `find_articles_by_author` - Articles by specific author
- `find_articles_by_domain` - Articles in specific domain
- `find_articles_by_tag` - Articles with specific tag
- `find_related_articles` - Find related articles
- `author_collaboration_network` - Author collaboration analysis
- `domain_tag_analysis` - Domain and tag relationships
- `most_productive_authors` - Most active authors
- `recent_articles` - Recently published articles
- `full_text_search` - Search article content

## 🚀 Example Usage in Claude

Once configured, you can ask Claude things like:

1. **"Show me all authors in the database"**
   - Claude will use the `get_database_schema` or `execute_cypher` tool

2. **"Find articles by John Doe"**
   - Claude will use `search_articles` with search_type="author"

3. **"What are the most productive authors?"**
   - Claude will use `analyze_relationships` with analysis_type="productivity"

4. **"Execute this Cypher query: MATCH (n:Author) RETURN n.name LIMIT 5"**
   - Claude will use `execute_cypher` tool

## 🔍 Troubleshooting

### MCP Server Not Appearing
1. Check that the file path in the config is correct
2. Ensure Python can run the script: `python /path/to/__main__.py`
3. Verify Neo4j is running: `docker ps | grep neo4j`

### Connection Errors
1. Check Neo4j is accessible: `docker logs mcp_neo4j`
2. Verify credentials in the config match your setup
3. Test connection: `cypher-shell -a bolt://localhost:7687 -u neo4j -p password123`

### Dependencies Issues
1. Install requirements: `pip install -r requirements.txt`
2. Check Python version: `python --version` (should be 3.8+)

## 🔄 Alternative: Docker-based Setup

If you prefer to run via Docker (once containers are fixed):

```json
{
  "mcpServers": {
    "neo4j-cypher-docker": {
      "command": "docker",
      "args": ["exec", "-i", "mcp_cypher", "python", "__main__.py"],
      "env": {}
    }
  }
}
```

## 📊 Database Access

The MCP server connects to:
- **Neo4j**: `bolt://localhost:7687` (neo4j/password123)
- **PostgreSQL**: `localhost:5432` (postgres/password123)

Web interfaces:
- **Neo4j Browser**: http://localhost:7474
- **pgAdmin**: http://localhost:8080

## 🎉 Success Verification

After setup, you should see:
1. "neo4j-cypher" server in Claude's MCP servers list
2. Ability to ask Claude to query your Neo4j database
3. Access to all the tools and templates listed above

---

**Note**: Make sure to update the file path in the configuration to match your actual project location!