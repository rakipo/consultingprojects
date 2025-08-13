#!/usr/bin/env python3
"""
Test script for Batch Neo4j Data Loader
"""

import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from batch_loader import BatchNeo4jLoader

def test_batch_loader():
    """Test the batch loader with a small configuration."""
    
    # Configuration file
    config_file = "config/config_boomer_model_userdefined.yml"
    
    # Generate output files with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_file = f"output/data/neo4j_model_clean_{timestamp}.json"
    metrics_file = f"output/metrics/batch_load_metrics_{timestamp}.txt"
    
    print(f"Testing batch loader with:")
    print(f"  Config: {config_file}")
    print(f"  Model: {model_file}")
    print(f"  Metrics: {metrics_file}")
    
    try:
        # Create batch loader
        loader = BatchNeo4jLoader()
        
        # Load data in batches
        loader.load_data_in_batches(config_file, model_file, metrics_file)
        
        print("✅ Batch loader test completed successfully!")
        print(f"📊 Metrics saved to: {metrics_file}")
        
    except Exception as e:
        print(f"❌ Batch loader test failed: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_batch_loader()
    sys.exit(0 if success else 1)
