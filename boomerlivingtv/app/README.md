# MCP Neo4j Content Database - PostgreSQL Setup

This setup creates a PostgreSQL database with a comprehensive content management schema and 100 sample publications across multiple domains, designed for MCP (Model Context Protocol) Neo4j integration.

## 📋 Setup Options

- **Basic Setup**: PostgreSQL + pgAdmin only (`docker-compose.yml`)
- **Complete MCP Integration**: PostgreSQL + Neo4j + MCP Servers (`docker-compose-mcp.yml`)
- **Automated Setup**: Run `./complete-setup.sh` for full sequence
- **Manual Setup**: Follow `SETUP-SEQUENCE.md` for step-by-step instructions

## 📦 Dependencies

All dependencies are now consolidated in a single `requirements.txt` file:

```bash
# Install all dependencies
python install_dependencies.py

# Or manually
pip install -r requirements.txt

# Check dependency health
python check_dependencies.py
```

See [README_DEPENDENCIES.md](README_DEPENDENCIES.md) for detailed dependency management information.

## Quick Start

### Option 1: Basic PostgreSQL Setup
```bash
# Install dependencies first
python install_dependencies.py

# Start PostgreSQL and pgAdmin only
docker-compose up -d

# Check if containers are running
docker-compose ps
```

### Option 2: Complete MCP Neo4j Integration
```bash
# Install dependencies first
python install_dependencies.py

# Run the complete automated setup
./complete-setup.sh

# Or manually follow the detailed sequence
# See SETUP-SEQUENCE.md for step-by-step instructions
```

### 2. Database Auto-Initialization
The database automatically creates the schema and loads sample data on startup through initialization scripts:
- `01_create_extensions.sql` - Creates PostgreSQL extensions
- `02_create_mcpneo4j.sql` - Creates tables and loads 100 sample records

**Verification Commands:**
```bash
# Check if containers are running
docker-compose ps

# Verify PostgreSQL data loaded
docker exec movies_postgres psql -U postgres -d movies -c "SELECT COUNT(*) FROM structured_content;"

# Check sample data
docker exec movies_postgres psql -U postgres -d movies -c "SELECT author, COUNT(*) FROM structured_content GROUP BY author LIMIT 5;"
```

### 3. Access the Database

**PostgreSQL Connection:**
- Host: `localhost`
- Port: `5432`
- Database: `movies`
- Username: `postgres`
- Password: `password123`

**pgAdmin Web Interface:**
- URL: http://localhost:8080
- Email: `admin@movies.com`
- Password: `admin123`

**pgAdmin Server Setup (Add PostgreSQL Server):**
1. Login to pgAdmin at http://localhost:8080
2. Right-click "Servers" → "Create" → "Server..."
3. **General Tab**: Name: `MCP PostgreSQL Database`
4. **Connection Tab**:
   - Host name/address: `postgres` (use service name, not container name)
   - Port: `5432`
   - Maintenance database: `movies`
   - Username: `postgres`
   - Password: `password123`
5. Click "Save" to connect

## Database Schema

### Core Tables

#### `crawl_runs`
- `run_id` (Primary Key) - Unique identifier for crawl sessions
- `started_at`, `completed_at` - Timestamps
- `status` - Crawl status (running, completed, failed)
- `total_urls`, `successful_extractions`, `failed_extractions` - Statistics

#### `raw_html_store`
- `id` (Primary Key)
- `url` - Original webpage URL
- `raw_html` - Raw HTML content
- `headers` - HTTP headers (JSONB)
- `status_code` - HTTP response code
- `fetched_at` - Timestamp
- `run_id` - Foreign key to crawl_runs

#### `structured_content` (Main Content Table)
- `id` (Primary Key)
- `url` - Original URL
- `raw_html_id` - Foreign key to raw_html_store
- `domain` - Content domain category
- `site_name` - Website name
- `title` - Article/page title
- `author` - Author name
- `publish_date` - Publication date
- `content` - Extracted clean text (10 lines)
- `summary` - Article summary (5 lines)
- `tags` - Category tags (JSONB array)
- `language` - Language code (default: 'en')
- `extracted_at` - Processing timestamp
- `is_latest` - Latest version flag
- `run_id` - Foreign key to crawl_runs

### Views

#### `content_summary`
Aggregated view showing:
- Domain and author statistics
- Article counts per author
- Publication date ranges
- All tags used by each author

## Sample Data Overview

### 📊 **100 Publications by 10 Authors:**

1. **Dr. Sarah Chen** (Healthcare/AI) - 12 publications
2. **Michael Rodriguez** (Fintech/Financial) - 10 publications  
3. **Dr. Alex Thompson** (AI/Technology) - 15 publications
4. **Dr. Emily Watson** (Arthritis/Healthcare) - 8 publications
5. **Dr. James Wilson** (Weather/Climate) - 9 publications
6. **Lisa Chang** (Lifestyle/Wellness) - 11 publications
7. **Dr. Robert Kim** (Education) - 7 publications
8. **Dr. Maria Santos** (Sustainability) - 6 publications
9. **Jennifer Lee** (Technology/AI) - 8 publications
10. **David Park** (Mixed domains) - 8 publications

### 🏷️ **10 Domain Categories:**
- Healthcare
- Financial/Fintech
- Technology
- AI
- Lifestyle
- Education
- Sustainability
- Weather
- Arthritis
- Mixed Research

### 🔖 **Tag Examples:**
Healthcare, Fintech, AI, Arthritis, Financial, Weather, Lifestyle, Technology, Education, Sustainability

## Sample Queries

### Content Analysis
```sql
-- Get all articles by domain
SELECT domain, COUNT(*) as article_count
FROM structured_content
GROUP BY domain
ORDER BY article_count DESC;

-- Find articles by specific tags
SELECT title, author, tags
FROM structured_content
WHERE tags ? 'AI'  -- Articles tagged with AI
ORDER BY publish_date DESC;

-- Author productivity analysis
SELECT author, COUNT(*) as articles, 
       MIN(publish_date) as first_pub,
       MAX(publish_date) as latest_pub
FROM structured_content
GROUP BY author
ORDER BY articles DESC;
```

### Full-Text Search
```sql
-- Search content by keywords
SELECT title, author, domain, 
       ts_rank(to_tsvector('english', title || ' ' || content), 
               plainto_tsquery('english', 'artificial intelligence')) as rank
FROM structured_content
WHERE to_tsvector('english', title || ' ' || content) @@ 
      plainto_tsquery('english', 'artificial intelligence')
ORDER BY rank DESC;

-- Find articles about specific topics
SELECT title, author, summary
FROM structured_content
WHERE content ILIKE '%machine learning%'
   OR title ILIKE '%machine learning%'
ORDER BY publish_date DESC;
```

### Tag Analysis
```sql
-- Most popular tags
SELECT tag, COUNT(*) as usage_count
FROM structured_content,
     jsonb_array_elements_text(tags) as tag
GROUP BY tag
ORDER BY usage_count DESC;

-- Articles with multiple specific tags
SELECT title, author, tags
FROM structured_content
WHERE tags ? 'Healthcare' AND tags ? 'AI'
ORDER BY publish_date DESC;
```

### Domain Cross-Analysis
```sql
-- Authors writing across multiple domains
SELECT author, 
       COUNT(DISTINCT domain) as domain_count,
       ARRAY_AGG(DISTINCT domain) as domains
FROM structured_content
GROUP BY author
HAVING COUNT(DISTINCT domain) > 1
ORDER BY domain_count DESC;
```

## Advanced Usage

### MCP Neo4j Integration
This database is designed to work with MCP (Model Context Protocol) for Neo4j integration:

```bash
# Example: Export data for Neo4j import
SELECT jsonb_build_object(
    'title', title,
    'author', author,
    'domain', domain,
    'tags', tags,
    'content', content,
    'publish_date', publish_date
) as neo4j_data
FROM structured_content
WHERE domain = 'AI';
```

### Data Export Options
```sql
-- Export as CSV
COPY (SELECT * FROM structured_content) TO '/tmp/content_export.csv' WITH CSV HEADER;

-- Export specific domains
COPY (SELECT * FROM structured_content WHERE domain = 'Healthcare') 
TO '/tmp/healthcare_content.csv' WITH CSV HEADER;
```

### Performance Optimization
The database includes several indexes for optimal performance:
- Full-text search index on title and content
- Domain and author indexes
- Tag GIN index for JSON operations
- Publication date index

## Stopping the Services

```bash
# Stop containers
docker-compose down

# Stop and remove volumes (WARNING: This deletes all data)
docker-compose down -v
```

## Troubleshooting

### Connection Issues
- Ensure PostgreSQL is healthy: `docker-compose logs postgres`
- Check if port 5432 is available: `lsof -i :5432`
- Verify initialization scripts ran: Check for 100 records in `structured_content`

### Data Loading Issues
- Check initialization logs: `docker-compose logs postgres | grep -i error`
- Verify all tables created: `\dt` in psql
- Check sample data: `SELECT COUNT(*) FROM structured_content;`

### pgAdmin Issues
- Wait for PostgreSQL to be healthy before accessing pgAdmin
- Clear browser cache if login issues persist
- **Important**: Use service name `postgres` as hostname, NOT container name or localhost
- Default server connection in pgAdmin:
  - **Host name/address**: `postgres` (Docker service name)
  - **Port**: `5432`
  - **Maintenance database**: `movies`
  - **Username**: `postgres`
  - **Password**: `password123`

### Common pgAdmin Connection Errors
- **"Server doesn't listen"**: Use `postgres` not `localhost` or `127.0.0.1`
- **"Connection refused"**: Ensure PostgreSQL container is healthy
- **"Authentication failed"**: Double-check username/password
- **"Database doesn't exist"**: Verify initialization scripts ran successfully

### Schema Issues
- Verify foreign key constraints: `\d structured_content`
- Check indexes: `\di`
- Validate sample data integrity: `SELECT COUNT(*) FROM content_summary;`

## 🔄 Switching Between Setups

### Current Setup Check
```bash
# Check which PostgreSQL container is running
docker ps --filter "name=postgres" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"

# Check port usage
lsof -i :5432
```

### Switch to MCP Setup
```bash
# Stop current setup
docker-compose down

# Start MCP setup
docker-compose -f docker-compose-mcp.yml up -d
```

### Switch to Original Setup  
```bash
# Stop MCP setup
docker-compose -f docker-compose-mcp.yml down

# Start original setup
docker-compose up -d
```

## 📊 Container Details

### Original Setup (`docker-compose.yml`)
- **PostgreSQL Container**: `movies_postgres`
- **pgAdmin Container**: `movies_pgadmin`
- **Services**: 2 containers
- **Purpose**: Basic PostgreSQL + pgAdmin setup

### MCP Setup (`docker-compose-mcp.yml`)
- **PostgreSQL Container**: `mcp_postgres`
- **Neo4j Container**: `mcp_neo4j`
- **pgAdmin Container**: `mcp_pgadmin`
- **MCP Servers**: `mcp_data_modeling`, `mcp_cypher`, `mcp_manager`
- **Services**: 6 containers
- **Purpose**: Full MCP Neo4j integration

## 🌐 Network Configuration

Both setups use Docker networks for service communication:
- **Original**: Default Docker Compose network
- **MCP**: Custom `mcp-network` bridge network

This is why pgAdmin uses `postgres` (service name) as hostname instead of `localhost` or container names.
## 🚀 Qu
ick Reference

### Essential Commands
```bash
# Start services
docker-compose up -d                    # Original setup
docker-compose -f docker-compose-mcp.yml up -d  # MCP setup

# Check status
docker-compose ps
docker ps --filter "name=postgres"

# Access databases
docker exec -it movies_postgres psql -U postgres -d movies    # Original
docker exec -it mcp_postgres psql -U postgres -d movies       # MCP

# View logs
docker-compose logs postgres
docker-compose logs pgadmin

# Stop services
docker-compose down
docker-compose down -v  # Remove volumes (deletes data)
```

### Access URLs
- **pgAdmin**: http://localhost:8080 (`admin@movies.com` / `admin123`)
- **PostgreSQL**: `localhost:5432` (`postgres` / `password123`)

### pgAdmin Server Setup (Quick)
```
Name: PostgreSQL Database
Host: postgres
Port: 5432
Database: movies
Username: postgres
Password: password123
```

### Sample Data Verification
```sql
-- Check total records
SELECT COUNT(*) FROM structured_content;

-- Check authors
SELECT author, COUNT(*) FROM structured_content GROUP BY author;

-- Check domains  
SELECT domain, COUNT(*) FROM structured_content GROUP BY domain;

-- Check tags
SELECT jsonb_array_elements_text(tags) as tag, COUNT(*) 
FROM structured_content 
GROUP BY tag 
ORDER BY count DESC;
```## 🔄
 Complete Setup Sequence (PostgreSQL → Neo4j)

For the full MCP Neo4j integration with graph population:

### Automated Setup (Recommended)
```bash
# Run the complete automated sequence
./complete-setup.sh

# Expected results:
# - PostgreSQL: 100 sample articles
# - Neo4j: ~135 nodes, ~250+ relationships
# - All services running and connected
```

### Manual Setup Sequence
```bash
# 1. Start all MCP services
docker-compose -f docker-compose-mcp.yml up -d

# 2. Wait for services (PostgreSQL ~60s, Neo4j ~90s)
until docker exec mcp_postgres pg_isready -U postgres; do sleep 2; done
until docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "RETURN 1" > /dev/null 2>&1; do sleep 3; done

# 3. Insert sample data if needed
python generate_full_dataset.py

# 4. Verify PostgreSQL data (should be 100 records)
docker exec mcp_postgres psql -U postgres -d movies -c "SELECT COUNT(*) FROM structured_content;"

# 4. Migrate data to Neo4j
curl -X POST http://localhost:8000/api/migrate -H "Content-Type: application/json" -d '{"clear_existing": true}'

# 5. Verify Neo4j graph population
docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "MATCH (n) RETURN count(n) as nodes"
docker exec mcp_neo4j cypher-shell -u neo4j -p password123 "MATCH ()-[r]->() RETURN count(r) as relationships"
```

### Expected Final State
- **PostgreSQL**: 100 articles, 10 authors, 10 domains
- **Neo4j Graph**:
  - 100 Article nodes
  - 10 Author nodes  
  - 10 Domain nodes
  - ~15 Tag nodes
  - ~10 Website nodes
  - 250+ relationships connecting all entities

### Access Points After Setup
- **MCP Manager**: http://localhost:8000 (monitoring & queries)
- **Neo4j Browser**: http://localhost:7474 (neo4j/password123)
- **pgAdmin**: http://localhost:8080 (admin@movies.com/admin123)

For detailed step-by-step instructions, see **`SETUP-SEQUENCE.md`**.