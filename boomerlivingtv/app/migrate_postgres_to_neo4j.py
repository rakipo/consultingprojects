#!/usr/bin/env python3
"""
Migrate PostgreSQL structured_content data to Neo4j
This script creates a comprehensive graph model based on the structured_content table
"""

import psycopg2
import json
from neo4j import GraphDatabase
from datetime import datetime
import sys

# Database configurations
POSTGRES_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'movies',
    'user': 'postgres',
    'password': 'password123'
}

NEO4J_CONFIG = {
    'uri': 'bolt://localhost:7687',
    'user': 'neo4j',
    'password': 'password123'
}

class PostgresNeo4jMigrator:
    def __init__(self):
        self.postgres_conn = None
        self.neo4j_driver = None
        
    def connect_databases(self):
        """Connect to both PostgreSQL and Neo4j"""
        try:
            # Connect to PostgreSQL
            self.postgres_conn = psycopg2.connect(**POSTGRES_CONFIG)
            print("✅ Connected to PostgreSQL")
            
            # Connect to Neo4j
            self.neo4j_driver = GraphDatabase.driver(
                NEO4J_CONFIG['uri'],
                auth=(NEO4J_CONFIG['user'], NEO4J_CONFIG['password'])
            )
            print("✅ Connected to Neo4j")
            
            # Test Neo4j connection
            with self.neo4j_driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            print("✅ Neo4j connection verified")
            
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            sys.exit(1)
    
    def clear_neo4j_data(self):
        """Clear existing Neo4j data"""
        print("🧹 Clearing existing Neo4j data...")
        with self.neo4j_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("✅ Neo4j data cleared")
    
    def create_constraints_and_indexes(self):
        """Create Neo4j constraints and indexes"""
        print("🔧 Creating constraints and indexes...")
        
        constraints_and_indexes = [
            # Constraints
            "CREATE CONSTRAINT article_id IF NOT EXISTS FOR (a:Article) REQUIRE a.id IS UNIQUE",
            "CREATE CONSTRAINT author_name IF NOT EXISTS FOR (a:Author) REQUIRE a.name IS UNIQUE",
            "CREATE CONSTRAINT domain_name IF NOT EXISTS FOR (d:Domain) REQUIRE d.name IS UNIQUE",
            "CREATE CONSTRAINT tag_name IF NOT EXISTS FOR (t:Tag) REQUIRE t.name IS UNIQUE",
            "CREATE CONSTRAINT website_name IF NOT EXISTS FOR (w:Website) REQUIRE w.site_name IS UNIQUE",
            "CREATE CONSTRAINT language_code IF NOT EXISTS FOR (l:Language) REQUIRE l.code IS UNIQUE",
            "CREATE CONSTRAINT crawl_run_id IF NOT EXISTS FOR (c:CrawlRun) REQUIRE c.run_id IS UNIQUE",
            
            # Indexes
            "CREATE INDEX article_publish_date IF NOT EXISTS FOR (a:Article) ON (a.publish_date)",
            "CREATE INDEX article_title IF NOT EXISTS FOR (a:Article) ON (a.title)",
            "CREATE INDEX tag_usage IF NOT EXISTS FOR (t:Tag) ON (t.usage_count)"
        ]
        
        with self.neo4j_driver.session() as session:
            for query in constraints_and_indexes:
                try:
                    session.run(query)
                except Exception as e:
                    print(f"⚠️  Warning: {query} - {e}")
        
        print("✅ Constraints and indexes created")
    
    def fetch_postgres_data(self):
        """Fetch all data from PostgreSQL structured_content table"""
        print("📊 Fetching data from PostgreSQL...")
        
        cursor = self.postgres_conn.cursor()
        
        # Fetch all structured content (excluding 'content' field as requested)
        cursor.execute("""
            SELECT id, url, raw_html_id, domain, site_name, title, author, 
                   publish_date, summary, tags, language, extracted_at, is_latest, run_id
            FROM structured_content
            ORDER BY id
        """)
        
        records = cursor.fetchall()
        print(f"✅ Fetched {len(records)} records from PostgreSQL")
        
        return records
    
    def create_article_nodes(self, records):
        """Create Article nodes in Neo4j"""
        print("📝 Creating Article nodes...")
        
        with self.neo4j_driver.session() as session:
            for record in records:
                (id, url, raw_html_id, domain, site_name, title, author, 
                 publish_date, summary, tags, language, extracted_at, is_latest, run_id) = record
                
                # Handle tags (could be JSON string or already a list)
                if tags:
                    if isinstance(tags, str):
                        tags_list = json.loads(tags)
                    elif isinstance(tags, list):
                        tags_list = tags
                    else:
                        tags_list = []
                else:
                    tags_list = []
                
                session.run("""
                    CREATE (a:Article {
                        id: $id,
                        url: $url,
                        title: $title,
                        summary: $summary,
                        publish_date: date($publish_date),
                        language: $language,
                        extracted_at: datetime($extracted_at),
                        is_latest: $is_latest,
                        domain: $domain,
                        site_name: $site_name,
                        author: $author,
                        run_id: $run_id,
                        tags: $tags
                    })
                """, {
                    'id': id,
                    'url': url,
                    'title': title,
                    'summary': summary,
                    'publish_date': str(publish_date) if publish_date else '2024-01-01',
                    'language': language or 'en',
                    'extracted_at': extracted_at.isoformat() if extracted_at else datetime.now().isoformat(),
                    'is_latest': is_latest if is_latest is not None else True,
                    'domain': domain,
                    'site_name': site_name,
                    'author': author,
                    'run_id': run_id,
                    'tags': tags_list
                })
        
        print(f"✅ Created {len(records)} Article nodes")
    
    def create_author_nodes(self):
        """Create Author nodes with aggregated properties"""
        print("👥 Creating Author nodes...")
        
        with self.neo4j_driver.session() as session:
            session.run("""
                MATCH (a:Article)
                WHERE a.author IS NOT NULL
                WITH a.author AS author_name, 
                     count(a) AS total_articles,
                     min(a.publish_date) AS first_publication,
                     max(a.publish_date) AS latest_publication,
                     collect(DISTINCT a.domain)[0] AS primary_domain
                CREATE (author:Author {
                    name: author_name,
                    total_articles: total_articles,
                    specialization: primary_domain,
                    first_publication: first_publication,
                    latest_publication: latest_publication
                })
            """)
        
            # Get count of created authors
            result = session.run("MATCH (a:Author) RETURN count(a) as count")
            author_count = result.single()['count']
            print(f"✅ Created {author_count} Author nodes")
    
    def create_domain_nodes(self):
        """Create Domain nodes with statistics"""
        print("🏷️ Creating Domain nodes...")
        
        with self.neo4j_driver.session() as session:
            session.run("""
                MATCH (a:Article)
                WHERE a.domain IS NOT NULL
                WITH a.domain AS domain_name,
                     count(a) AS article_count,
                     collect(DISTINCT a.author) AS authors
                CREATE (d:Domain {
                    name: domain_name,
                    article_count: article_count,
                    author_count: size(authors),
                    description: domain_name + ' related content and research'
                })
            """)
        
            result = session.run("MATCH (d:Domain) RETURN count(d) as count")
            domain_count = result.single()['count']
            print(f"✅ Created {domain_count} Domain nodes")
    
    def create_tag_nodes(self):
        """Create Tag nodes from article tags"""
        print("🔖 Creating Tag nodes...")
        
        with self.neo4j_driver.session() as session:
            session.run("""
                MATCH (a:Article)
                WHERE a.tags IS NOT NULL AND size(a.tags) > 0
                UNWIND a.tags AS tag_name
                WITH tag_name, count(*) AS usage_count
                CREATE (t:Tag {
                    name: tag_name,
                    usage_count: usage_count
                })
            """)
        
            result = session.run("MATCH (t:Tag) RETURN count(t) as count")
            tag_count = result.single()['count']
            print(f"✅ Created {tag_count} Tag nodes")
    
    def create_website_nodes(self):
        """Create Website nodes"""
        print("🌐 Creating Website nodes...")
        
        with self.neo4j_driver.session() as session:
            session.run("""
                MATCH (a:Article)
                WHERE a.site_name IS NOT NULL
                WITH a.site_name AS site_name,
                     count(a) AS article_count,
                     collect(DISTINCT a.domain) AS domains
                CREATE (w:Website {
                    site_name: site_name,
                    article_count: article_count,
                    domain_categories: domains,
                    base_url: 'https://' + toLower(replace(site_name, ' ', '')) + '.com'
                })
            """)
        
            result = session.run("MATCH (w:Website) RETURN count(w) as count")
            website_count = result.single()['count']
            print(f"✅ Created {website_count} Website nodes")
    
    def create_language_nodes(self):
        """Create Language nodes"""
        print("🌍 Creating Language nodes...")
        
        with self.neo4j_driver.session() as session:
            session.run("""
                MATCH (a:Article)
                WHERE a.language IS NOT NULL
                WITH a.language AS lang_code,
                     count(a) AS article_count
                CREATE (l:Language {
                    code: lang_code,
                    name: CASE lang_code 
                          WHEN 'en' THEN 'English'
                          WHEN 'es' THEN 'Spanish'
                          WHEN 'fr' THEN 'French'
                          ELSE 'Unknown'
                          END,
                    article_count: article_count
                })
            """)
        
            result = session.run("MATCH (l:Language) RETURN count(l) as count")
            language_count = result.single()['count']
            print(f"✅ Created {language_count} Language nodes")
    
    def create_crawl_run_nodes(self):
        """Create CrawlRun nodes"""
        print("🔄 Creating CrawlRun nodes...")
        
        with self.neo4j_driver.session() as session:
            session.run("""
                MATCH (a:Article)
                WHERE a.run_id IS NOT NULL
                WITH a.run_id AS run_id,
                     count(a) AS total_articles,
                     min(a.extracted_at) AS started_at,
                     max(a.extracted_at) AS completed_at
                CREATE (c:CrawlRun {
                    run_id: run_id,
                    total_articles: total_articles,
                    started_at: started_at,
                    completed_at: completed_at,
                    status: 'completed'
                })
            """)
        
            result = session.run("MATCH (c:CrawlRun) RETURN count(c) as count")
            crawl_count = result.single()['count']
            print(f"✅ Created {crawl_count} CrawlRun nodes")
    
    def create_relationships(self):
        """Create all relationships between nodes"""
        print("🔗 Creating relationships...")
        
        relationships = [
            # Author WROTE Article
            {
                'name': 'WROTE',
                'query': """
                    MATCH (author:Author), (article:Article)
                    WHERE author.name = article.author
                    CREATE (author)-[:WROTE {
                        publish_date: article.publish_date,
                        article_title: article.title
                    }]->(article)
                """
            },
            
            # Author SPECIALIZES_IN Domain
            {
                'name': 'SPECIALIZES_IN',
                'query': """
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
                    }]->(d)
                """
            },
            
            # Article BELONGS_TO Domain
            {
                'name': 'BELONGS_TO',
                'query': """
                    MATCH (article:Article), (domain:Domain)
                    WHERE article.domain = domain.name
                    CREATE (article)-[:BELONGS_TO]->(domain)
                """
            },
            
            # Article TAGGED_WITH Tag
            {
                'name': 'TAGGED_WITH',
                'query': """
                    MATCH (article:Article)
                    WHERE article.tags IS NOT NULL AND size(article.tags) > 0
                    UNWIND article.tags AS tag_name
                    MATCH (t:Tag {name: tag_name})
                    CREATE (article)-[:TAGGED_WITH {
                        relevance_score: rand() * 0.5 + 0.5
                    }]->(t)
                """
            },
            
            # Article WRITTEN_IN Language
            {
                'name': 'WRITTEN_IN',
                'query': """
                    MATCH (article:Article), (language:Language)
                    WHERE article.language = language.code
                    CREATE (article)-[:WRITTEN_IN]->(language)
                """
            },
            
            # Article PUBLISHED_ON Website
            {
                'name': 'PUBLISHED_ON',
                'query': """
                    MATCH (article:Article), (website:Website)
                    WHERE article.site_name = website.site_name
                    CREATE (article)-[:PUBLISHED_ON {
                        publish_date: article.publish_date
                    }]->(website)
                """
            },
            
            # Article EXTRACTED_IN CrawlRun
            {
                'name': 'EXTRACTED_IN',
                'query': """
                    MATCH (article:Article), (crawl:CrawlRun)
                    WHERE article.run_id = crawl.run_id
                    CREATE (article)-[:EXTRACTED_IN]->(crawl)
                """
            },
            
            # Website FOCUSES_ON Domain
            {
                'name': 'FOCUSES_ON',
                'query': """
                    MATCH (website:Website)<-[:PUBLISHED_ON]-(article:Article)-[:BELONGS_TO]->(domain:Domain)
                    WITH website, domain, count(article) AS article_count
                    WHERE article_count >= 1
                    CREATE (website)-[:FOCUSES_ON {
                        article_count: article_count,
                        focus_strength: CASE 
                            WHEN article_count >= 10 THEN 'Primary'
                            WHEN article_count >= 5 THEN 'Secondary'
                            ELSE 'Minor'
                        END
                    }]->(domain)
                """
            },
            
            # Tag RELATED_TO Tag (Co-occurrence)
            {
                'name': 'RELATED_TO',
                'query': """
                    MATCH (article:Article)-[:TAGGED_WITH]->(t1:Tag)
                    MATCH (article)-[:TAGGED_WITH]->(t2:Tag)
                    WHERE t1 <> t2 AND id(t1) < id(t2)
                    WITH t1, t2, count(article) AS co_occurrence_count
                    WHERE co_occurrence_count >= 2
                    CREATE (t1)-[:RELATED_TO {
                        co_occurrence_count: co_occurrence_count,
                        strength: CASE 
                            WHEN co_occurrence_count >= 10 THEN 'Strong'
                            WHEN co_occurrence_count >= 5 THEN 'Moderate'
                            ELSE 'Weak'
                        END
                    }]->(t2)
                """
            },
            
            # Tag COMMONLY_USED_IN Domain
            {
                'name': 'COMMONLY_USED_IN',
                'query': """
                    MATCH (tag:Tag)<-[:TAGGED_WITH]-(article:Article)-[:BELONGS_TO]->(domain:Domain)
                    WITH tag, domain, count(article) AS usage_count
                    WHERE usage_count >= 1
                    CREATE (tag)-[:COMMONLY_USED_IN {
                        usage_count: usage_count,
                        usage_percentage: toFloat(usage_count) / domain.article_count * 100
                    }]->(domain)
                """
            }
        ]
        
        with self.neo4j_driver.session() as session:
            for rel in relationships:
                print(f"  Creating {rel['name']} relationships...")
                result = session.run(rel['query'])
                # Get relationship count
                count_result = session.run(f"MATCH ()-[r:{rel['name']}]->() RETURN count(r) as count")
                count = count_result.single()['count']
                print(f"    ✅ Created {count} {rel['name']} relationships")
    
    def get_migration_statistics(self):
        """Get final migration statistics"""
        print("📊 Gathering migration statistics...")
        
        with self.neo4j_driver.session() as session:
            # Node counts
            node_result = session.run("""
                MATCH (n)
                RETURN labels(n) as node_type, count(n) as count
                ORDER BY count DESC
            """)
            
            print("\n📈 Node Statistics:")
            total_nodes = 0
            for record in node_result:
                node_type = record['node_type'][0] if record['node_type'] else 'Unknown'
                count = record['count']
                total_nodes += count
                print(f"  • {node_type}: {count} nodes")
            
            print(f"  📊 Total Nodes: {total_nodes}")
            
            # Relationship counts
            rel_result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as relationship_type, count(r) as count
                ORDER BY count DESC
            """)
            
            print("\n🔗 Relationship Statistics:")
            total_relationships = 0
            for record in rel_result:
                rel_type = record['relationship_type']
                count = record['count']
                total_relationships += count
                print(f"  • {rel_type}: {count} relationships")
            
            print(f"  📊 Total Relationships: {total_relationships}")
            
            return total_nodes, total_relationships
    
    def run_sample_queries(self):
        """Run sample queries to verify the migration"""
        print("\n🔍 Running sample verification queries...")
        
        with self.neo4j_driver.session() as session:
            # Most productive authors
            print("\n👥 Most Productive Authors:")
            result = session.run("""
                MATCH (a:Author)-[:WROTE]->(article:Article)
                RETURN a.name, count(article) as articles, a.specialization
                ORDER BY articles DESC
                LIMIT 5
            """)
            for record in result:
                print(f"  • {record['a.name']}: {record['articles']} articles ({record['a.specialization']})")
            
            # Domain distribution
            print("\n🏷️ Domain Distribution:")
            result = session.run("""
                MATCH (d:Domain)<-[:BELONGS_TO]-(article:Article)
                RETURN d.name, count(article) as articles
                ORDER BY articles DESC
            """)
            for record in result:
                print(f"  • {record['d.name']}: {record['articles']} articles")
            
            # Tag usage
            print("\n🔖 Most Used Tags:")
            result = session.run("""
                MATCH (t:Tag)
                RETURN t.name, t.usage_count
                ORDER BY t.usage_count DESC
                LIMIT 5
            """)
            for record in result:
                print(f"  • {record['t.name']}: {record['t.usage_count']} uses")
    
    def migrate(self):
        """Run the complete migration process"""
        print("🚀 Starting PostgreSQL to Neo4j Migration")
        print("=" * 60)
        
        try:
            # Step 1: Connect to databases
            self.connect_databases()
            
            # Step 2: Clear existing Neo4j data
            self.clear_neo4j_data()
            
            # Step 3: Create constraints and indexes
            self.create_constraints_and_indexes()
            
            # Step 4: Fetch PostgreSQL data
            records = self.fetch_postgres_data()
            
            # Step 5: Create nodes
            self.create_article_nodes(records)
            self.create_author_nodes()
            self.create_domain_nodes()
            self.create_tag_nodes()
            self.create_website_nodes()
            self.create_language_nodes()
            self.create_crawl_run_nodes()
            
            # Step 6: Create relationships
            self.create_relationships()
            
            # Step 7: Get statistics
            total_nodes, total_relationships = self.get_migration_statistics()
            
            # Step 8: Run sample queries
            self.run_sample_queries()
            
            print(f"\n🎉 Migration Completed Successfully!")
            print(f"📊 Final Results:")
            print(f"  • Total Nodes: {total_nodes}")
            print(f"  • Total Relationships: {total_relationships}")
            print(f"  • Source Records: {len(records)}")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Close connections
            if self.postgres_conn:
                self.postgres_conn.close()
            if self.neo4j_driver:
                self.neo4j_driver.close()

def main():
    """Main execution function"""
    migrator = PostgresNeo4jMigrator()
    migrator.migrate()

if __name__ == "__main__":
    main()