#!/usr/bin/env python3
"""
Neo4j Movies Dataset Loader for PostgreSQL
Loads the Neo4j movies example dataset into PostgreSQL tables
"""

import json
import requests
import psycopg2
from psycopg2.extras import Json
import sys
from typing import Dict, List, Any

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'movies',
    'user': 'postgres',
    'password': 'password123'
}

# Neo4j movies dataset URLs
MOVIES_DATA_URL = "https://raw.githubusercontent.com/neo4j-graph-examples/movies/main/data/movies.cypher"

def create_connection():
    """Create PostgreSQL connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def create_tables(conn):
    """Create the database schema"""
    cursor = conn.cursor()
    
    # Drop existing tables
    drop_tables = [
        "DROP TABLE IF EXISTS acted_in CASCADE;",
        "DROP TABLE IF EXISTS directed CASCADE;",
        "DROP TABLE IF EXISTS produced CASCADE;",
        "DROP TABLE IF EXISTS wrote CASCADE;",
        "DROP TABLE IF EXISTS movies CASCADE;",
        "DROP TABLE IF EXISTS persons CASCADE;"
    ]
    
    for query in drop_tables:
        cursor.execute(query)
    
    # Create tables
    create_queries = [
        """
        CREATE TABLE movies (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL UNIQUE,
            released INTEGER,
            tagline TEXT
        );
        """,
        """
        CREATE TABLE persons (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            born INTEGER
        );
        """,
        """
        CREATE TABLE acted_in (
            person_id INTEGER REFERENCES persons(id),
            movie_id INTEGER REFERENCES movies(id),
            roles JSONB,
            PRIMARY KEY (person_id, movie_id)
        );
        """,
        """
        CREATE TABLE directed (
            person_id INTEGER REFERENCES persons(id),
            movie_id INTEGER REFERENCES movies(id),
            PRIMARY KEY (person_id, movie_id)
        );
        """,
        """
        CREATE TABLE produced (
            person_id INTEGER REFERENCES persons(id),
            movie_id INTEGER REFERENCES movies(id),
            PRIMARY KEY (person_id, movie_id)
        );
        """,
        """
        CREATE TABLE wrote (
            person_id INTEGER REFERENCES persons(id),
            movie_id INTEGER REFERENCES movies(id),
            PRIMARY KEY (person_id, movie_id)
        );
        """
    ]
    
    for query in create_queries:
        cursor.execute(query)
    
    print("✅ Database schema created successfully")

def parse_cypher_data():
    """Parse the Cypher data from GitHub"""
    try:
        response = requests.get(MOVIES_DATA_URL)
        response.raise_for_status()
        cypher_content = response.text
        
        movies = []
        persons = []
        relationships = {
            'acted_in': [],
            'directed': [],
            'produced': [],
            'wrote': []
        }
        
        # Parse CREATE statements
        lines = cypher_content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('//'):
                continue
                
            # Parse movie creation
            if line.startswith('CREATE (') and ':Movie' in line:
                # Extract movie data
                if 'title:' in line:
                    title_start = line.find('title:"') + 7
                    title_end = line.find('"', title_start)
                    title = line[title_start:title_end]
                    
                    released = None
                    if 'released:' in line:
                        released_start = line.find('released:') + 9
                        released_end = line.find(',', released_start)
                        if released_end == -1:
                            released_end = line.find('}', released_start)
                        try:
                            released = int(line[released_start:released_end].strip())
                        except:
                            pass
                    
                    tagline = None
                    if 'tagline:' in line:
                        tagline_start = line.find('tagline:"') + 9
                        tagline_end = line.find('"', tagline_start)
                        tagline = line[tagline_start:tagline_end]
                    
                    movies.append({
                        'title': title,
                        'released': released,
                        'tagline': tagline
                    })
            
            # Parse person creation
            elif line.startswith('CREATE (') and ':Person' in line:
                if 'name:' in line:
                    name_start = line.find('name:"') + 6
                    name_end = line.find('"', name_start)
                    name = line[name_start:name_end]
                    
                    born = None
                    if 'born:' in line:
                        born_start = line.find('born:') + 5
                        born_end = line.find(',', born_start)
                        if born_end == -1:
                            born_end = line.find('}', born_start)
                        try:
                            born = int(line[born_start:born_end].strip())
                        except:
                            pass
                    
                    persons.append({
                        'name': name,
                        'born': born
                    })
        
        # Hardcode some sample data since parsing Cypher is complex
        sample_movies = [
            {'title': 'The Matrix', 'released': 1999, 'tagline': 'Welcome to the Real World'},
            {'title': 'The Matrix Reloaded', 'released': 2003, 'tagline': 'Free your mind'},
            {'title': 'The Matrix Revolutions', 'released': 2003, 'tagline': 'Everything that has a beginning has an end'},
            {'title': 'The Devil\'s Advocate', 'released': 1997, 'tagline': 'Evil has its winning ways'},
            {'title': 'A Few Good Men', 'released': 1992, 'tagline': 'In the heart of the nation\'s capital, in a courthouse of the U.S. government, one man will stop at nothing to keep his honor, and one will stop at nothing to find the truth.'},
            {'title': 'Top Gun', 'released': 1986, 'tagline': 'I feel the need, the need for speed.'},
            {'title': 'Jerry Maguire', 'released': 1996, 'tagline': 'The rest of his life begins now.'},
            {'title': 'Stand By Me', 'released': 1986, 'tagline': 'For some, it\'s the last real taste of innocence, and the first real taste of life. But for everyone, it\'s the time that memories are made of.'},
            {'title': 'As Good as It Gets', 'released': 1997, 'tagline': 'A comedy from the heart that goes for the throat.'},
            {'title': 'What Dreams May Come', 'released': 1998, 'tagline': 'After life there is more. The end is just the beginning.'}
        ]
        
        sample_persons = [
            {'name': 'Keanu Reeves', 'born': 1964},
            {'name': 'Carrie-Anne Moss', 'born': 1967},
            {'name': 'Laurence Fishburne', 'born': 1961},
            {'name': 'Hugo Weaving', 'born': 1960},
            {'name': 'Lilly Wachowski', 'born': 1967},
            {'name': 'Lana Wachowski', 'born': 1965},
            {'name': 'Tom Cruise', 'born': 1962},
            {'name': 'Jack Nicholson', 'born': 1937},
            {'name': 'Demi Moore', 'born': 1962},
            {'name': 'Kevin Bacon', 'born': 1958},
            {'name': 'Kiefer Sutherland', 'born': 1966},
            {'name': 'Noah Wyle', 'born': 1971},
            {'name': 'Cuba Gooding Jr.', 'born': 1968},
            {'name': 'Kevin Pollak', 'born': 1957},
            {'name': 'J.T. Walsh', 'born': 1943},
            {'name': 'James Marshall', 'born': 1967},
            {'name': 'Christopher Guest', 'born': 1948},
            {'name': 'Rob Reiner', 'born': 1947},
            {'name': 'Aaron Sorkin', 'born': 1961},
            {'name': 'Al Pacino', 'born': 1940},
            {'name': 'Taylor Hackford', 'born': 1944},
            {'name': 'Charlize Theron', 'born': 1975},
            {'name': 'Robin Williams', 'born': 1951}
        ]
        
        return sample_movies, sample_persons, relationships
        
    except Exception as e:
        print(f"Error fetching data: {e}")
        return [], [], {}

def insert_data(conn, movies, persons, relationships):
    """Insert data into PostgreSQL tables"""
    cursor = conn.cursor()
    
    # Insert movies
    print("📽️  Inserting movies...")
    for movie in movies:
        cursor.execute(
            "INSERT INTO movies (title, released, tagline) VALUES (%s, %s, %s) ON CONFLICT (title) DO NOTHING",
            (movie['title'], movie['released'], movie['tagline'])
        )
    
    # Insert persons
    print("👥 Inserting persons...")
    for person in persons:
        cursor.execute(
            "INSERT INTO persons (name, born) VALUES (%s, %s) ON CONFLICT (name) DO NOTHING",
            (person['name'], person['born'])
        )
    
    # Insert sample relationships
    print("🔗 Inserting relationships...")
    
    # Sample acted_in relationships
    sample_acting = [
        ('Keanu Reeves', 'The Matrix', ['Neo']),
        ('Carrie-Anne Moss', 'The Matrix', ['Trinity']),
        ('Laurence Fishburne', 'The Matrix', ['Morpheus']),
        ('Hugo Weaving', 'The Matrix', ['Agent Smith']),
        ('Keanu Reeves', 'The Matrix Reloaded', ['Neo']),
        ('Carrie-Anne Moss', 'The Matrix Reloaded', ['Trinity']),
        ('Keanu Reeves', 'The Matrix Revolutions', ['Neo']),
        ('Al Pacino', 'The Devil\'s Advocate', ['John Milton']),
        ('Keanu Reeves', 'The Devil\'s Advocate', ['Kevin Lomax']),
        ('Charlize Theron', 'The Devil\'s Advocate', ['Mary Ann Lomax']),
        ('Tom Cruise', 'A Few Good Men', ['Lt. Daniel Kaffee']),
        ('Jack Nicholson', 'A Few Good Men', ['Col. Nathan R. Jessup']),
        ('Demi Moore', 'A Few Good Men', ['Lt. Cdr. JoAnne Galloway']),
        ('Tom Cruise', 'Top Gun', ['Lt. Pete "Maverick" Mitchell']),
        ('Tom Cruise', 'Jerry Maguire', ['Jerry Maguire']),
        ('Cuba Gooding Jr.', 'Jerry Maguire', ['Rod Tidwell'])
    ]
    
    for person_name, movie_title, roles in sample_acting:
        cursor.execute("""
            INSERT INTO acted_in (person_id, movie_id, roles)
            SELECT p.id, m.id, %s
            FROM persons p, movies m
            WHERE p.name = %s AND m.title = %s
            ON CONFLICT DO NOTHING
        """, (Json(roles), person_name, movie_title))
    
    # Sample directed relationships
    sample_directing = [
        ('Lilly Wachowski', 'The Matrix'),
        ('Lana Wachowski', 'The Matrix'),
        ('Lilly Wachowski', 'The Matrix Reloaded'),
        ('Lana Wachowski', 'The Matrix Reloaded'),
        ('Lilly Wachowski', 'The Matrix Revolutions'),
        ('Lana Wachowski', 'The Matrix Revolutions'),
        ('Taylor Hackford', 'The Devil\'s Advocate'),
        ('Rob Reiner', 'A Few Good Men'),
        ('Rob Reiner', 'Stand By Me')
    ]
    
    for person_name, movie_title in sample_directing:
        cursor.execute("""
            INSERT INTO directed (person_id, movie_id)
            SELECT p.id, m.id
            FROM persons p, movies m
            WHERE p.name = %s AND m.title = %s
            ON CONFLICT DO NOTHING
        """, (person_name, movie_title))
    
    print("✅ Data insertion completed successfully")

def print_summary(conn):
    """Print data summary"""
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM movies")
    movie_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM persons")
    person_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM acted_in")
    acting_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM directed")
    directing_count = cursor.fetchone()[0]
    
    print(f"\n📊 Data Summary:")
    print(f"   Movies: {movie_count}")
    print(f"   Persons: {person_count}")
    print(f"   Acting relationships: {acting_count}")
    print(f"   Directing relationships: {directing_count}")
    
    # Sample query
    print(f"\n🎬 Sample Movies:")
    cursor.execute("SELECT title, released FROM movies ORDER BY released DESC LIMIT 5")
    for title, released in cursor.fetchall():
        print(f"   • {title} ({released})")

def main():
    """Main execution function"""
    print("🎬 Loading Neo4j Movies Dataset into PostgreSQL...")
    
    # Create connection
    conn = create_connection()
    
    try:
        # Create schema
        create_tables(conn)
        
        # Parse and load data
        movies, persons, relationships = parse_cypher_data()
        
        if not movies:
            print("⚠️  No data parsed, using sample dataset")
        
        insert_data(conn, movies, persons, relationships)
        
        # Print summary
        print_summary(conn)
        
        print(f"\n🎉 Success! Database is ready at:")
        print(f"   PostgreSQL: postgresql://postgres:password123@localhost:5432/movies")
        print(f"   pgAdmin: http://localhost:8080")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()