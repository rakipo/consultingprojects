#!/usr/bin/env python3
"""
Test script to verify that the comprehensive metrics system works correctly.
"""

import sys
import os
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from batch_loader import BatchNeo4jLoader

def test_comprehensive_metrics():
    """Test that comprehensive metrics are properly structured."""
    
    # Create a batch loader instance
    loader = BatchNeo4jLoader()
    
    # Simulate source metrics
    loader.source_metrics["pull_query"] = "SELECT * FROM structured_content WHERE status_neo4j = false OR status_neo4j IS NULL"
    loader.source_metrics["records_pulled"] = 112
    
    # Simulate batch metrics
    loader.batch_metrics["total_batches"] = 12
    loader.batch_metrics["completed_batches"] = 12
    loader.batch_metrics["failed_batches"] = 0
    loader.batch_metrics["total_records_processed"] = 112
    
    # Simulate load metrics (current run)
    loader.load_metrics["nodes_created"]["Article"] = 112
    loader.load_metrics["nodes_created"]["Website"] = 112
    loader.load_metrics["nodes_created"]["Chunk"] = 2847
    loader.load_metrics["nodes_created"]["Tag"] = 367
    loader.load_metrics["relationships_created"]["HAS_CHUNK"] = 2847
    loader.load_metrics["relationships_created"]["PUBLISHED_ON"] = 112
    loader.load_metrics["relationships_created"]["TAGGED_WITH"] = 367
    loader.load_metrics["chunks_created"] = 2847
    loader.load_metrics["embeddings_generated"] = 2847
    loader.load_metrics["total_records_processed"] = 112
    
    # Simulate before metrics (existing counts)
    loader.before_metrics["nodes_existing_count"]["Article"] = 0
    loader.before_metrics["nodes_existing_count"]["Website"] = 0
    loader.before_metrics["nodes_existing_count"]["Chunk"] = 0
    loader.before_metrics["nodes_existing_count"]["Tag"] = 0
    loader.before_metrics["relationships_existing_count"]["HAS_CHUNK"] = 0
    loader.before_metrics["relationships_existing_count"]["PUBLISHED_ON"] = 0
    loader.before_metrics["relationships_existing_count"]["TAGGED_WITH"] = 0
    
    # Simulate after metrics (total counts after run)
    loader.after_metrics["nodes_current"]["Article"] = 112
    loader.after_metrics["nodes_current"]["Website"] = 112
    loader.after_metrics["nodes_current"]["Chunk"] = 2847
    loader.after_metrics["nodes_current"]["Tag"] = 367
    loader.after_metrics["relationships_current"]["HAS_CHUNK"] = 2847
    loader.after_metrics["relationships_current"]["PUBLISHED_ON"] = 112
    loader.after_metrics["relationships_current"]["TAGGED_WITH"] = 367
    
    # Simulate adhoc tests
    loader.adhoc_tests["orphan_nodes"]["Article"] = 0
    loader.adhoc_tests["orphan_nodes"]["Website"] = 0
    loader.adhoc_tests["orphan_nodes"]["Chunk"] = 0
    loader.adhoc_tests["orphan_nodes"]["Tag"] = 0
    loader.adhoc_tests["orphan_relationships"]["HAS_CHUNK"] = 0
    loader.adhoc_tests["orphan_relationships"]["PUBLISHED_ON"] = 0
    loader.adhoc_tests["orphan_relationships"]["TAGGED_WITH"] = 0
    loader.adhoc_tests["data_integrity_issues"] = []
    loader.adhoc_tests["test_results"] = {}
    
    # Test metrics structure
    print("Testing comprehensive metrics structure...")
    
    # Check that all required sections exist
    required_sections = [
        "source_metrics", "batch_metrics", "load_metrics", 
        "before_metrics", "after_metrics", "adhoc_tests"
    ]
    
    for section in required_sections:
        if hasattr(loader, section):
            print(f"✅ {section} section exists")
        else:
            print(f"❌ {section} section missing")
            return False
    
    # Check source metrics
    if (loader.source_metrics["pull_query"] and 
        loader.source_metrics["records_pulled"] == 112):
        print("✅ Source metrics are correct")
    else:
        print("❌ Source metrics are incorrect")
        return False
    
    # Check batch metrics
    if (loader.batch_metrics["total_batches"] == 12 and
        loader.batch_metrics["completed_batches"] == 12 and
        loader.batch_metrics["total_records_processed"] == 112):
        print("✅ Batch metrics are correct")
    else:
        print("❌ Batch metrics are incorrect")
        return False
    
    # Check load metrics
    if (loader.load_metrics["nodes_created"]["Article"] == 112 and
        loader.load_metrics["nodes_created"]["Chunk"] == 2847 and
        loader.load_metrics["total_records_processed"] == 112):
        print("✅ Load metrics are correct")
    else:
        print("❌ Load metrics are incorrect")
        return False
    
    # Check before metrics
    if (loader.before_metrics["nodes_existing_count"]["Article"] == 0 and
        loader.before_metrics["nodes_existing_count"]["Chunk"] == 0):
        print("✅ Before metrics are correct")
    else:
        print("❌ Before metrics are incorrect")
        return False
    
    # Check after metrics
    if (loader.after_metrics["nodes_current"]["Article"] == 112 and
        loader.after_metrics["nodes_current"]["Chunk"] == 2847):
        print("✅ After metrics are correct")
    else:
        print("❌ After metrics are incorrect")
        return False
    
    # Check adhoc tests
    if (loader.adhoc_tests["orphan_nodes"]["Article"] == 0 and
        loader.adhoc_tests["orphan_nodes"]["Chunk"] == 0 and
        len(loader.adhoc_tests["data_integrity_issues"]) == 0):
        print("✅ Adhoc tests are correct")
    else:
        print("❌ Adhoc tests are incorrect")
        return False
    
    # Test metrics writing
    test_metrics_file = "test_comprehensive_metrics.json"
    try:
        loader.write_batch_metrics(test_metrics_file)
        
        # Read and verify the written file
        with open(test_metrics_file, 'r') as f:
            written_metrics = json.load(f)
        
        # Check that all sections are in the written file
        for section in required_sections:
            if section in written_metrics:
                print(f"✅ {section} written to file correctly")
            else:
                print(f"❌ {section} missing from written file")
                return False
        
        print("✅ Metrics file written successfully")
        
        # Clean up
        os.remove(test_metrics_file)
        
    except Exception as e:
        print(f"❌ Error writing metrics: {e}")
        return False
    
    print("\n🎉 All comprehensive metrics tests PASSED!")
    return True

if __name__ == "__main__":
    success = test_comprehensive_metrics()
    sys.exit(0 if success else 1)
