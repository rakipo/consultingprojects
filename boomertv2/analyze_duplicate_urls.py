#!/usr/bin/env python3
"""
Analyze duplicate URLs to understand the Article count discrepancy.
"""

import psycopg2
from collections import Counter
import json

def analyze_duplicate_urls():
    """Analyze duplicate URLs in the structured_content table."""
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect('postgresql://postgres:password123@localhost:5432/boomer_tv')
        cur = conn.cursor()
        
        # Get all URLs
        cur.execute("SELECT url, id, title FROM structured_content ORDER BY url")
        records = cur.fetchall()
        
        # Count URLs
        url_counts = Counter([record[0] for record in records])
        
        # Find duplicates
        duplicates = {url: count for url, count in url_counts.items() if count > 1}
        
        print(f"📊 URL Analysis Results:")
        print(f"Total records: {len(records)}")
        print(f"Unique URLs: {len(url_counts)}")
        print(f"Duplicate URLs: {len(duplicates)}")
        print(f"Expected Article nodes: {len(records)}")
        print(f"Actual Article nodes (after MERGE): {len(url_counts)}")
        print(f"Missing Article nodes: {len(records) - len(url_counts)}")
        
        if duplicates:
            print(f"\n🔍 Duplicate URLs found:")
            for url, count in duplicates.items():
                print(f"  {url}: {count} times")
                
                # Show the records with this URL
                cur.execute("SELECT id, title FROM structured_content WHERE url = %s", (url,))
                dup_records = cur.fetchall()
                for i, (record_id, title) in enumerate(dup_records, 1):
                    print(f"    {i}. ID: {record_id}, Title: {title[:50]}...")
        
        # Show some sample URLs
        print(f"\n📋 Sample URLs (first 10):")
        for i, (url, count) in enumerate(list(url_counts.items())[:10], 1):
            print(f"  {i}. {url}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        print("PostgreSQL server might not be running.")

if __name__ == "__main__":
    analyze_duplicate_urls()
