#!/usr/bin/env python3
"""
Test script for small batch processing
"""

from analyze_trending import TrendingAnalyzer

def test_small_batch():
    analyzer = TrendingAnalyzer()
    analyzer.process_csv(input_file="test_trending.csv", output_file="test_output.csv")

if __name__ == "__main__":
    test_small_batch()