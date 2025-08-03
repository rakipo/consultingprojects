#!/usr/bin/env python3
"""
Test script for the Trending Content Analyzer
"""

import pandas as pd
from analyze_trending import TrendingAnalyzer

def test_single_article():
    """Test analysis of a single article"""
    print("🧪 Testing single article analysis...")
    
    try:
        analyzer = TrendingAnalyzer()
        
        # Test with sample data
        title = "The Country With the Highest Retirement Age in the World Will Surprise You"
        snippet = "Libya has the highest official retirement age in the world, and Denmark will soon join it. The United States isn't too far off..."
        
        result = analyzer.analyze_article(title, snippet)
        
        print(f"✅ Analysis successful!")
        print(f"Topic: {result['topic']}")
        print(f"Tags: {', '.join(result['tags'])}")
        print(f"Community: {result['community']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_csv_structure():
    """Test if CSV has required columns"""
    print("📊 Testing CSV structure...")
    
    try:
        df = pd.read_csv('trending.csv')
        required_columns = ['article_title', 'article_snippet']
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"❌ Missing required columns: {missing_columns}")
            return False
        
        print(f"✅ CSV structure is valid ({len(df)} rows, {len(df.columns)} columns)")
        return True
        
    except Exception as e:
        print(f"❌ CSV test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🔍 Running tests for Trending Content Analyzer...\n")
    
    tests = [
        test_csv_structure,
        test_single_article
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📈 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Ready to run the full analysis.")
    else:
        print("⚠️  Some tests failed. Please check your configuration.")

if __name__ == "__main__":
    main()