# Neo4j Graph Model for MCP Content Management System

## 📋 Overview

This document describes the comprehensive Neo4j graph model generated from the `structured_content` PostgreSQL table for the MCP (Model Context Protocol) Neo4j data modeling server. The model excludes the `content` field as requested and focuses on metadata relationships and analytical insights.

## 🏗️ Graph Architecture

### Node Types (7 Labels)

#### 1. **Article** Nodes
**Purpose**: Represents individual publications/articles
```cypher
(:Article {
    id: Integer,           // Unique identifier
    url: String,           // Original article URL
    title: String,         // Article title
    summary: String,       // Article summary (5-line description)
    publish_date: Date,    // Publication date
    language: String,      // Language code (e.g., 'en')
    extracted_at: DateTime,// When data was extracted
    is_latest: Boolean     // Latest version flag
})
```

#### 2. **Author** Nodes
**Purpose**: Represents content creators/writers
```cypher
(:Author {
    name: String,              // Author name (unique)
    total_articles: Integer,   // Total articles written
    specialization: String,    // Primary domain of expertise
    first_publication: Date,   // Date of first article
    latest_publication: Date   // Date of most recent article
})
```

#### 3. **Domain** Nodes
**Purpose**: Represents content categories/domains
```cypher
(:Domain {
    name: String,          // Domain name (unique)
    article_count: Integer,// Number of articles in domain
    author_count: Integer, // Number of authors in domain
    description: String    // Domain description
})
```

#### 4. **Tag** Nodes
**Purpose**: Represents content tags for classification
```cypher
(:Tag {
    name: String,          // Tag name (unique)
    usage_count: Integer   // Number of times tag is used
})
```

#### 5. **Website** Nodes
**Purpose**: Represents publishing platforms/sites
```cypher
(:Website {
    site_name: String,         // Website name (unique)
    article_count: Integer,    // Number of articles published
    domain_categories: [String], // List of domains covered
    base_url: String           // Constructed base URL
})
```

#### 6. **Language** Nodes
**Purpose**: Represents content languages
```cypher
(:Language {
    code: String,          // Language code (unique, e.g., 'en')
    name: String,          // Language name (e.g., 'English')
    article_count: Integer // Number of articles in language
})
```

#### 7. **CrawlRun** Nodes
**Purpose**: Represents data extraction sessions
```cypher
(:CrawlRun {
    run_id: String,        // Unique run identifier
    total_articles: Integer,// Articles extracted in run
    started_at: DateTime,  // Run start time
    completed_at: DateTime,// Run completion time
    status: String         // Run status
})
```

### Relationship Types (11 Types)

#### 1. **WROTE** - Author to Article
```cypher
(Author)-[:WROTE {
    publish_date: Date,    // When article was published
    article_title: String // Article title for reference
}]->(Article)
```

#### 2. **SPECIALIZES_IN** - Author to Domain
```cypher
(Author)-[:SPECIALIZES_IN {
    article_count: Integer,    // Articles in this domain
    expertise_level: String    // Expert/Proficient/Contributor
}]->(Domain)
```

#### 3. **BELONGS_TO** - Article to Domain
```cypher
(Article)-[:BELONGS_TO]->(Domain)
```

#### 4. **TAGGED_WITH** - Article to Tag
```cypher
(Article)-[:TAGGED_WITH {
    relevance_score: Float     // Tag relevance (0.5-1.0)
}]->(Tag)
```

#### 5. **WRITTEN_IN** - Article to Language
```cypher
(Article)-[:WRITTEN_IN]->(Language)
```

#### 6. **PUBLISHED_ON** - Article to Website
```cypher
(Article)-[:PUBLISHED_ON {
    publish_date: Date         // Publication date
}]->(Website)
```

#### 7. **EXTRACTED_IN** - Article to CrawlRun
```cypher
(Article)-[:EXTRACTED_IN]->(CrawlRun)
```

#### 8. **FOCUSES_ON** - Website to Domain
```cypher
(Website)-[:FOCUSES_ON {
    article_count: Integer,    // Articles in domain
    focus_strength: String     // Primary/Secondary/Minor
}]->(Domain)
```

#### 9. **RELATED_TO** - Tag to Tag (Co-occurrence)
```cypher
(Tag)-[:RELATED_TO {
    co_occurrence_count: Integer, // Times tags appear together
    strength: String              // Strong/Moderate/Weak
}]->(Tag)
```

#### 10. **COMMONLY_USED_IN** - Tag to Domain
```cypher
(Tag)-[:COMMONLY_USED_IN {
    usage_count: Integer,      // Times used in domain
    usage_percentage: Float    // Percentage of domain articles
}]->(Domain)
```

#### 11. **OVERLAPS_WITH** - Domain to Domain
```cypher
(Domain)-[:OVERLAPS_WITH {
    shared_authors: Integer,   // Authors working in both domains
    overlap_type: String       // Type of overlap
}]->(Domain)
```

## 🔧 MCP Server Routes and Tools

### Available Resources

#### 1. **postgres://schema**
- **Description**: Current PostgreSQL database schema
- **Content**: Table structures, columns, constraints, indexes
- **Usage**: Understanding source data structure

#### 2. **neo4j://model**
- **Description**: Generated Neo4j data model
- **Content**: Complete Cypher model with nodes, relationships, constraints
- **Usage**: Graph database setup and migration

#### 3. **analysis://content**
- **Description**: Analysis of content structure and relationships
- **Content**: Statistics, patterns, author productivity, domain distribution
- **Usage**: Data insights and migration planning

### Available Tools

#### 1. **analyze_postgres_schema**
```json
{
  "name": "analyze_postgres_schema",
  "description": "Analyze PostgreSQL schema and suggest Neo4j model",
  "parameters": {}
}
```
**Output**: Schema analysis, content statistics, suggested graph model

#### 2. **migrate_to_neo4j**
```json
{
  "name": "migrate_to_neo4j", 
  "description": "Migrate data from PostgreSQL to Neo4j",
  "parameters": {
    "clear_existing": "boolean (default: false)"
  }
}
```
**Output**: Migration statistics, node/relationship counts, success status

#### 3. **generate_cypher_queries**
```json
{
  "name": "generate_cypher_queries",
  "description": "Generate Cypher queries for common operations", 
  "parameters": {
    "query_type": "string (create_nodes|create_relationships|analysis|search)"
  }
}
```
**Output**: Cypher queries for specified operation type

## 📊 Expected Graph Statistics

After migration from 100 PostgreSQL records:

### Node Counts
- **Article**: 100 nodes
- **Author**: 10 nodes
- **Domain**: 6 nodes  
- **Tag**: ~15 nodes
- **Website**: ~10 nodes
- **Language**: 1-2 nodes
- **CrawlRun**: 1-2 nodes

**Total Nodes**: ~135-145

### Relationship Counts
- **WROTE**: 100 relationships
- **BELONGS_TO**: 100 relationships
- **TAGGED_WITH**: ~200-300 relationships
- **PUBLISHED_ON**: 100 relationships
- **EXTRACTED_IN**: 100 relationships
- **SPECIALIZES_IN**: ~10-15 relationships
- **WRITTEN_IN**: 100 relationships
- **FOCUSES_ON**: ~20-30 relationships
- **RELATED_TO**: ~50-100 relationships
- **COMMONLY_USED_IN**: ~30-50 relationships
- **OVERLAPS_WITH**: ~10-20 relationships

**Total Relationships**: ~720-825

## 🔍 Analytical Queries

### 1. Author Productivity Analysis
```cypher
MATCH (a:Author)-[:WROTE]->(article:Article)
RETURN a.name, a.total_articles, a.specialization,
       a.first_publication, a.latest_publication
ORDER BY a.total_articles DESC
```

### 2. Domain Collaboration Patterns
```cypher
MATCH (a1:Author)-[:SPECIALIZES_IN]->(d:Domain)<-[:SPECIALIZES_IN]-(a2:Author)
WHERE a1 <> a2
RETURN a1.name, a2.name, d.name, 
       a1.total_articles + a2.total_articles AS combined_output
ORDER BY combined_output DESC
```

### 3. Tag Co-occurrence Network
```cypher
MATCH (t1:Tag)-[r:RELATED_TO]->(t2:Tag)
RETURN t1.name, t2.name, r.co_occurrence_count, r.strength
ORDER BY r.co_occurrence_count DESC
```

### 4. Content Evolution Timeline
```cypher
MATCH (article:Article)
WITH article.publish_date.year AS year, 
     article.publish_date.month AS month,
     count(article) AS article_count
RETURN year, month, article_count
ORDER BY year, month
```

### 5. Cross-Domain Tag Usage
```cypher
MATCH (t:Tag)-[:COMMONLY_USED_IN]->(d:Domain)
WITH t, count(d) AS domain_count, collect(d.name) AS domains
WHERE domain_count > 1
RETURN t.name, domain_count, domains
ORDER BY domain_count DESC
```

## 🚀 Usage Examples

### Running the Demo
```bash
# Install dependencies
pip install requests

# Run complete routes demonstration
python mcp_routes_demo.py

# View generated graph model
cat neo4j_graph_model.cypher
```

### Manual API Calls
```bash
# List available resources
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "resources/list", "params": {}}'

# Analyze PostgreSQL schema
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/call", "params": {"name": "analyze_postgres_schema", "arguments": {}}}'

# Generate analysis queries
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/call", "params": {"name": "generate_cypher_queries", "arguments": {"query_type": "analysis"}}}'
```

## 🎯 Key Benefits

### 1. **Rich Relationship Modeling**
- Captures complex relationships between authors, content, and domains
- Enables discovery of collaboration patterns and expertise areas

### 2. **Temporal Analysis**
- Tracks content evolution over time
- Identifies trends and publication patterns

### 3. **Content Classification**
- Multi-dimensional tagging system
- Cross-domain content discovery

### 4. **Author Analytics**
- Productivity metrics and specialization tracking
- Collaboration network analysis

### 5. **Content Strategy Insights**
- Website focus area analysis
- Domain overlap identification

## 📁 Files Generated

1. **`neo4j_graph_model.cypher`** - Complete graph model with all queries
2. **`mcp_routes_demo.py`** - Demonstration of all MCP server routes
3. **`NEO4J_GRAPH_MODEL.md`** - This documentation file

The graph model provides a comprehensive foundation for content analysis, author collaboration discovery, and strategic content planning while maintaining the flexibility and power of graph database relationships.