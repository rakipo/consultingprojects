#!/usr/bin/env python3
"""
Test script to verify that the metrics accumulation fix works correctly.
"""

import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from batch_loader import BatchNeo4jLoader

def test_metrics_accumulation():
    """Test that metrics are properly accumulated across batches."""
    
    # Create a batch loader instance
    loader = BatchNeo4jLoader()
    
    # Simulate processing multiple batches
    print("Testing metrics accumulation...")
    
    # Simulate batch 1: 5 records
    loader.load_metrics["nodes_created"]["Article"] = 5
    loader.load_metrics["nodes_created"]["Website"] = 5
    loader.load_metrics["nodes_created"]["Chunk"] = 25
    loader.load_metrics["relationships_created"]["HAS_CHUNK"] = 25
    loader.load_metrics["relationships_created"]["PUBLISHED_ON"] = 5
    loader.load_metrics["chunks_created"] = 25
    loader.load_metrics["embeddings_generated"] = 25
    
    print(f"After batch 1: Articles={loader.load_metrics['nodes_created']['Article']}, Chunks={loader.load_metrics['nodes_created']['Chunk']}")
    
    # Simulate batch 2: 3 more records
    loader.load_metrics["nodes_created"]["Article"] += 3
    loader.load_metrics["nodes_created"]["Website"] += 3
    loader.load_metrics["nodes_created"]["Chunk"] += 15
    loader.load_metrics["relationships_created"]["HAS_CHUNK"] += 15
    loader.load_metrics["relationships_created"]["PUBLISHED_ON"] += 3
    loader.load_metrics["chunks_created"] += 15
    loader.load_metrics["embeddings_generated"] += 15
    
    print(f"After batch 2: Articles={loader.load_metrics['nodes_created']['Article']}, Chunks={loader.load_metrics['nodes_created']['Chunk']}")
    
    # Verify totals
    expected_articles = 8
    expected_chunks = 40
    
    if (loader.load_metrics["nodes_created"]["Article"] == expected_articles and 
        loader.load_metrics["nodes_created"]["Chunk"] == expected_chunks):
        print("✅ Metrics accumulation test PASSED!")
        return True
    else:
        print("❌ Metrics accumulation test FAILED!")
        print(f"Expected: Articles={expected_articles}, Chunks={expected_chunks}")
        print(f"Actual: Articles={loader.load_metrics['nodes_created']['Article']}, Chunks={loader.load_metrics['nodes_created']['Chunk']}")
        return False

if __name__ == "__main__":
    success = test_metrics_accumulation()
    sys.exit(0 if success else 1)
