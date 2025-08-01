// Neo4j Graph Model for MCP Content Management System
// Based on structured_content table (excluding 'content' field)
// Generated for mcp-neo4j-data-modeling server

// ============================================================================
// GRAPH MODEL OVERVIEW
// ============================================================================

/*
This graph model transforms the relational structured_content table into a 
rich graph structure that captures relationships between:
- Authors and their publications
- Content domains and categorization
- Tags and content classification
- Websites and publishing platforms
- Temporal relationships through publication dates
- Language and localization aspects
*/

// ============================================================================
// NODE LABELS AND PROPERTIES
// ============================================================================

// 1. ARTICLE NODES
// Represents individual publications/articles
// Properties: id, url, title, summary, publish_date, language, extracted_at, is_latest

// 2. AUTHOR NODES  
// Represents content creators/writers
// Properties: name, total_articles, specialization, first_publication, latest_publication

// 3. DOMAIN NODES
// Represents content categories/domains
// Properties: name, description, article_count, primary_tags

// 4. TAG NODES
// Represents content tags for classification
// Properties: name, usage_count, related_domains

// 5. WEBSITE NODES
// Represents publishing platforms/sites
// Properties: site_name, domain_category, article_count, base_url

// 6. LANGUAGE NODES
// Represents content languages
// Properties: code, name, article_count

// 7. CRAWL_RUN NODES
// Represents data extraction sessions
// Properties: run_id, started_at, completed_at, status, total_articles

// ============================================================================
// RELATIONSHIP TYPES
// ============================================================================

// AUTHORSHIP RELATIONSHIPS
// (Author)-[:WROTE {publish_date, article_title}]->(Article)
// (Author)-[:SPECIALIZES_IN {article_count, expertise_level}]->(Domain)

// CONTENT CLASSIFICATION
// (Article)-[:BELONGS_TO]->(Domain)
// (Article)-[:TAGGED_WITH {relevance_score}]->(Tag)
// (Article)-[:WRITTEN_IN]->(Language)

// PUBLISHING RELATIONSHIPS
// (Article)-[:PUBLISHED_ON {publish_date}]->(Website)
// (Website)-[:FOCUSES_ON]->(Domain)

// TEMPORAL RELATIONSHIPS
// (Article)-[:PUBLISHED_IN {month, day}]->(Year)
// (Article)-[:EXTRACTED_IN]->(CrawlRun)

// TAG RELATIONSHIPS
// (Tag)-[:RELATED_TO {co_occurrence_count}]->(Tag)
// (Tag)-[:COMMONLY_USED_IN]->(Domain)

// DOMAIN RELATIONSHIPS
// (Domain)-[:OVERLAPS_WITH {shared_authors, shared_tags}]->(Domain)

// ============================================================================
// CONSTRAINTS AND INDEXES
// ============================================================================

// Create unique constraints
CREATE CONSTRAINT article_id IF NOT EXISTS FOR (a:Article) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT author_name IF NOT EXISTS FOR (a:Author) REQUIRE a.name IS UNIQUE;
CREATE CONSTRAINT domain_name IF NOT EXISTS FOR (d:Domain) REQUIRE d.name IS UNIQUE;
CREATE CONSTRAINT tag_name IF NOT EXISTS FOR (t:Tag) REQUIRE t.name IS UNIQUE;
CREATE CONSTRAINT website_name IF NOT EXISTS FOR (w:Website) REQUIRE w.site_name IS UNIQUE;
CREATE CONSTRAINT language_code IF NOT EXISTS FOR (l:Language) REQUIRE l.code IS UNIQUE;
CREATE CONSTRAINT crawl_run_id IF NOT EXISTS FOR (c:CrawlRun) REQUIRE c.run_id IS UNIQUE;

// Create performance indexes
CREATE INDEX article_publish_date IF NOT EXISTS FOR (a:Article) ON (a.publish_date);
CREATE INDEX article_title IF NOT EXISTS FOR (a:Article) ON (a.title);
CREATE INDEX author_specialization IF NOT EXISTS FOR ()-[r:SPECIALIZES_IN]-() ON (r.article_count);
CREATE INDEX tag_usage IF NOT EXISTS FOR (t:Tag) ON (t.usage_count);

// ============================================================================
// DATA TRANSFORMATION QUERIES
// ============================================================================

// 1. CREATE ARTICLE NODES
// Transform each record in structured_content to Article node
LOAD CSV WITH HEADERS FROM 'file:///structured_content.csv' AS row
CREATE (a:Article {
    id: toInteger(row.id),
    url: row.url,
    title: row.title,
    summary: row.summary,
    publish_date: date(row.publish_date),
    language: row.language,
    extracted_at: datetime(row.extracted_at),
    is_latest: toBoolean(row.is_latest)
});

// 2. CREATE AUTHOR NODES WITH AGGREGATED PROPERTIES
MATCH (a:Article)
WITH a.author AS author_name, 
     count(a) AS total_articles,
     min(a.publish_date) AS first_publication,
     max(a.publish_date) AS latest_publication,
     collect(DISTINCT a.domain)[0] AS primary_domain
WHERE author_name IS NOT NULL
CREATE (author:Author {
    name: author_name,
    total_articles: total_articles,
    specialization: primary_domain,
    first_publication: first_publication,
    latest_publication: latest_publication
});

// 3. CREATE DOMAIN NODES WITH STATISTICS
MATCH (a:Article)
WITH a.domain AS domain_name,
     count(a) AS article_count,
     collect(DISTINCT a.author) AS authors
WHERE domain_name IS NOT NULL
CREATE (d:Domain {
    name: domain_name,
    article_count: article_count,
    author_count: size(authors),
    description: domain_name + ' related content and research'
});

// 4. CREATE TAG NODES FROM JSONB ARRAY
MATCH (a:Article)
WHERE a.tags IS NOT NULL
UNWIND a.tags AS tag_name
WITH tag_name, count(*) AS usage_count
CREATE (t:Tag {
    name: tag_name,
    usage_count: usage_count
});

// 5. CREATE WEBSITE NODES
MATCH (a:Article)
WITH a.site_name AS site_name,
     count(a) AS article_count,
     collect(DISTINCT a.domain) AS domains
WHERE site_name IS NOT NULL
CREATE (w:Website {
    site_name: site_name,
    article_count: article_count,
    domain_categories: domains,
    base_url: 'https://' + toLower(replace(site_name, ' ', '')) + '.com'
});

// 6. CREATE LANGUAGE NODES
MATCH (a:Article)
WITH a.language AS lang_code,
     count(a) AS article_count
WHERE lang_code IS NOT NULL
CREATE (l:Language {
    code: lang_code,
    name: CASE lang_code 
          WHEN 'en' THEN 'English'
          WHEN 'es' THEN 'Spanish'
          WHEN 'fr' THEN 'French'
          ELSE 'Unknown'
          END,
    article_count: article_count
});

// 7. CREATE CRAWL_RUN NODES
MATCH (a:Article)
WITH a.run_id AS run_id,
     count(a) AS total_articles,
     min(a.extracted_at) AS started_at,
     max(a.extracted_at) AS completed_at
WHERE run_id IS NOT NULL
CREATE (c:CrawlRun {
    run_id: run_id,
    total_articles: total_articles,
    started_at: started_at,
    completed_at: completed_at,
    status: 'completed'
});

// ============================================================================
// RELATIONSHIP CREATION QUERIES
// ============================================================================

// 1. AUTHOR WROTE ARTICLE RELATIONSHIPS
MATCH (author:Author), (article:Article)
WHERE author.name = article.author
CREATE (author)-[:WROTE {
    publish_date: article.publish_date,
    article_title: article.title
}]->(article);

// 2. AUTHOR SPECIALIZES IN DOMAIN RELATIONSHIPS
MATCH (author:Author)-[:WROTE]->(article:Article)
WITH author, article.domain AS domain, count(article) AS article_count
MATCH (d:Domain {name: domain})
CREATE (author)-[:SPECIALIZES_IN {
    article_count: article_count,
    expertise_level: CASE 
        WHEN article_count >= 10 THEN 'Expert'
        WHEN article_count >= 5 THEN 'Proficient'
        ELSE 'Contributor'
    END
}]->(d);

// 3. ARTICLE BELONGS TO DOMAIN RELATIONSHIPS
MATCH (article:Article), (domain:Domain)
WHERE article.domain = domain.name
CREATE (article)-[:BELONGS_TO]->(domain);

// 4. ARTICLE TAGGED WITH TAG RELATIONSHIPS
MATCH (article:Article)
WHERE article.tags IS NOT NULL
UNWIND article.tags AS tag_name
MATCH (t:Tag {name: tag_name})
CREATE (article)-[:TAGGED_WITH {
    relevance_score: rand() * 0.5 + 0.5  // Random relevance between 0.5-1.0
}]->(t);

// 5. ARTICLE WRITTEN IN LANGUAGE RELATIONSHIPS
MATCH (article:Article), (language:Language)
WHERE article.language = language.code
CREATE (article)-[:WRITTEN_IN]->(language);

// 6. ARTICLE PUBLISHED ON WEBSITE RELATIONSHIPS
MATCH (article:Article), (website:Website)
WHERE article.site_name = website.site_name
CREATE (article)-[:PUBLISHED_ON {
    publish_date: article.publish_date
}]->(website);

// 7. ARTICLE EXTRACTED IN CRAWL_RUN RELATIONSHIPS
MATCH (article:Article), (crawl:CrawlRun)
WHERE article.run_id = crawl.run_id
CREATE (article)-[:EXTRACTED_IN]->(crawl);

// 8. WEBSITE FOCUSES ON DOMAIN RELATIONSHIPS
MATCH (website:Website)-[:PUBLISHED_ON]-(article:Article)-[:BELONGS_TO]->(domain:Domain)
WITH website, domain, count(article) AS article_count
WHERE article_count >= 2  // Only create relationship if website has 2+ articles in domain
CREATE (website)-[:FOCUSES_ON {
    article_count: article_count,
    focus_strength: CASE 
        WHEN article_count >= 10 THEN 'Primary'
        WHEN article_count >= 5 THEN 'Secondary'
        ELSE 'Minor'
    END
}]->(domain);

// 9. TAG RELATED TO TAG RELATIONSHIPS (Co-occurrence)
MATCH (article:Article)-[:TAGGED_WITH]->(t1:Tag)
MATCH (article)-[:TAGGED_WITH]->(t2:Tag)
WHERE t1 <> t2
WITH t1, t2, count(article) AS co_occurrence_count
WHERE co_occurrence_count >= 2  // Only create if tags co-occur 2+ times
CREATE (t1)-[:RELATED_TO {
    co_occurrence_count: co_occurrence_count,
    strength: CASE 
        WHEN co_occurrence_count >= 10 THEN 'Strong'
        WHEN co_occurrence_count >= 5 THEN 'Moderate'
        ELSE 'Weak'
    END
}]->(t2);

// 10. TAG COMMONLY USED IN DOMAIN RELATIONSHIPS
MATCH (tag:Tag)<-[:TAGGED_WITH]-(article:Article)-[:BELONGS_TO]->(domain:Domain)
WITH tag, domain, count(article) AS usage_count
WHERE usage_count >= 2
CREATE (tag)-[:COMMONLY_USED_IN {
    usage_count: usage_count,
    usage_percentage: toFloat(usage_count) / domain.article_count * 100
}]->(domain);

// 11. DOMAIN OVERLAPS WITH DOMAIN RELATIONSHIPS
MATCH (d1:Domain)<-[:BELONGS_TO]-(article1:Article)<-[:WROTE]-(author:Author)
MATCH (author)-[:WROTE]->(article2:Article)-[:BELONGS_TO]->(d2:Domain)
WHERE d1 <> d2
WITH d1, d2, count(DISTINCT author) AS shared_authors
WHERE shared_authors >= 2
CREATE (d1)-[:OVERLAPS_WITH {
    shared_authors: shared_authors,
    overlap_type: 'Author_Overlap'
}]->(d2);

// ============================================================================
// ANALYTICAL QUERIES FOR INSIGHTS
// ============================================================================

// 1. MOST PRODUCTIVE AUTHORS
MATCH (a:Author)-[:WROTE]->(article:Article)
RETURN a.name, a.total_articles, a.specialization
ORDER BY a.total_articles DESC
LIMIT 10;

// 2. DOMAIN POPULARITY AND GROWTH
MATCH (d:Domain)<-[:BELONGS_TO]-(article:Article)
WITH d, article.publish_date.year AS year, count(article) AS articles_per_year
RETURN d.name, year, articles_per_year
ORDER BY d.name, year;

// 3. TAG CO-OCCURRENCE NETWORK
MATCH (t1:Tag)-[r:RELATED_TO]->(t2:Tag)
RETURN t1.name, t2.name, r.co_occurrence_count, r.strength
ORDER BY r.co_occurrence_count DESC
LIMIT 20;

// 4. AUTHOR COLLABORATION PATTERNS
MATCH (a1:Author)-[:SPECIALIZES_IN]->(d:Domain)<-[:SPECIALIZES_IN]-(a2:Author)
WHERE a1 <> a2
RETURN a1.name, a2.name, d.name, 
       a1.total_articles + a2.total_articles AS combined_articles
ORDER BY combined_articles DESC
LIMIT 15;

// 5. CONTENT EVOLUTION OVER TIME
MATCH (article:Article)
WITH article.publish_date.year AS year, 
     article.publish_date.month AS month,
     count(article) AS article_count
RETURN year, month, article_count
ORDER BY year, month;

// 6. CROSS-DOMAIN TAG USAGE
MATCH (t:Tag)-[:COMMONLY_USED_IN]->(d:Domain)
WITH t, count(d) AS domain_count, collect(d.name) AS domains
WHERE domain_count > 1
RETURN t.name, domain_count, domains
ORDER BY domain_count DESC;

// 7. WEBSITE CONTENT STRATEGY ANALYSIS
MATCH (w:Website)-[:FOCUSES_ON]->(d:Domain)
WITH w, count(d) AS domain_focus_count, collect(d.name) AS focused_domains
RETURN w.site_name, w.article_count, domain_focus_count, focused_domains
ORDER BY w.article_count DESC;

// ============================================================================
// GRAPH STATISTICS AND VALIDATION
// ============================================================================

// Count all nodes by type
MATCH (n)
RETURN labels(n) AS node_type, count(n) AS count
ORDER BY count DESC;

// Count all relationships by type
MATCH ()-[r]->()
RETURN type(r) AS relationship_type, count(r) AS count
ORDER BY count DESC;

// Validate data integrity
MATCH (a:Article)
WHERE a.author IS NULL OR a.domain IS NULL OR a.title IS NULL
RETURN count(a) AS articles_with_missing_data;

// Check for orphaned nodes
MATCH (n)
WHERE NOT (n)--()
RETURN labels(n) AS orphaned_node_type, count(n) AS count;

// ============================================================================
// EXPORT QUERIES FOR MCP SERVER
// ============================================================================

// Export graph structure for visualization
MATCH (n)-[r]->(m)
RETURN id(n) AS source_id, labels(n) AS source_labels, n.name AS source_name,
       type(r) AS relationship_type, properties(r) AS relationship_props,
       id(m) AS target_id, labels(m) AS target_labels, m.name AS target_name
LIMIT 1000;

// Export node statistics for dashboard
MATCH (n)
WITH labels(n)[0] AS node_type, count(n) AS node_count
RETURN node_type, node_count
ORDER BY node_count DESC;

// Export relationship statistics
MATCH ()-[r]->()
WITH type(r) AS rel_type, count(r) AS rel_count
RETURN rel_type, rel_count
ORDER BY rel_count DESC;

// ============================================================================
// CLEANUP AND MAINTENANCE QUERIES
// ============================================================================

// Remove duplicate relationships
MATCH (a)-[r1:WROTE]->(b), (a)-[r2:WROTE]->(b)
WHERE id(r1) > id(r2)
DELETE r2;

// Update node statistics
MATCH (a:Author)-[:WROTE]->(article:Article)
WITH a, count(article) AS actual_count
SET a.total_articles = actual_count;

// Refresh tag usage counts
MATCH (t:Tag)<-[:TAGGED_WITH]-(article:Article)
WITH t, count(article) AS actual_usage
SET t.usage_count = actual_usage;

// ============================================================================
// END OF GRAPH MODEL
// ============================================================================

/*
This comprehensive graph model transforms the structured_content table into
a rich, interconnected graph that enables:

1. Content Discovery: Find related articles through tags, domains, and authors
2. Author Analysis: Understand author expertise and collaboration patterns  
3. Trend Analysis: Track content evolution over time and domains
4. Content Strategy: Analyze website focus areas and content gaps
5. Semantic Relationships: Explore tag co-occurrence and domain overlaps
6. Quality Metrics: Measure content distribution and author productivity

The model excludes the 'content' field as requested, focusing on metadata
and relationships that provide analytical value without storing large text.
*/