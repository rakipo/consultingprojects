#!/usr/bin/env python3
"""
Test script for single article analysis - randomly selects from trending.csv
"""

import pandas as pd
import random
from analyze_trending import TrendingAnalyzer

def test_single():
    # Load the trending.csv file
    try:
        df = pd.read_csv('trending.csv')
        print(f"Loaded {len(df)} articles from trending.csv")
    except FileNotFoundError:
        print("Error: trending.csv not found!")
        return
    
    # Randomly select a record
    random_index = random.randint(0, len(df) - 1)
    selected_row = df.iloc[random_index]
    
    print(f"\n=== Testing Random Article #{random_index + 1} ===")
    print(f"Title: {selected_row['article_title']}")
    print(f"Snippet: {selected_row['article_snippet'][:100]}...")
    print(f"Source: {selected_row['source_domain']}")
    print("=" * 60)
    
    # Analyze the selected article
    analyzer = TrendingAnalyzer()
    
    result = analyzer.analyze_article(
        title=selected_row['article_title'],
        snippet=selected_row['article_snippet']
    )
    
    print("\n=== Analysis Results ===")
    print(f"Topic: {result['topic']}")
    print(f"Tags: {result['tags']}")
    print(f"Community: {result['community']}")
    print(f"Thought Process: {result['thought_process_determining_topic']}")
    print(f"Classification Reason: {result['classification_reason']}")
    
    print(f"\n=== Performance Metrics ===")
    print(f"Topic Analysis - Time: {result['topic_llm_time']:.2f}s, Input: {result['topic_input_tokens']} tokens, Output: {result['topic_output_tokens']} tokens")
    print(f"Classification - Time: {result['classification_llm_time']:.2f}s, Input: {result['classification_input_tokens']} tokens, Output: {result['classification_output_tokens']} tokens")
    print(f"Total Time: {result['topic_llm_time'] + result['classification_llm_time']:.2f}s")
    print(f"Total Tokens: {result['topic_input_tokens'] + result['topic_output_tokens'] + result['classification_input_tokens'] + result['classification_output_tokens']} tokens")

if __name__ == "__main__":
    test_single()