#!/usr/bin/env python3
"""
Test script to demonstrate the failure tracking system in the batch loader.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from batch_loader import BatchNeo4jLoader
import json
from datetime import datetime

def test_failure_tracking():
    """Test the failure tracking system."""
    
    # Create a batch loader instance
    loader = BatchNeo4jLoader()
    
    # Simulate some failures
    print("Simulating various types of failures...")
    
    # Track a batch failure
    loader.track_batch_failure(
        batch_num=5,
        offset=40,
        limit=10,
        error="Database connection timeout",
        record_ids=[41, 42, 43, 44, 45]
    )
    
    # Track a record failure
    loader.track_record_failure(
        record_id=123,
        record_data={"id": 123, "title": "Test Article", "url": "https://example.com"},
        error="Invalid URL format",
        failure_type="validation"
    )
    
    # Track a node failure
    loader.track_node_failure(
        node_label="Article",
        node_data={"id": 456, "title": "Another Test", "url": "https://test.com"},
        error="Duplicate key violation",
        postgres_column="url"
    )
    
    # Track a relationship failure
    loader.track_relationship_failure(
        relationship_type="PUBLISHED_ON",
        source_data={"id": 789},
        target_data={"domain": "example.com"},
        error="Target node not found"
    )
    
    # Track a constraint violation
    loader.track_constraint_violation(
        constraint_name="article_url_unique",
        constraint_type="unique",
        data={"url": "https://duplicate.com"},
        error="URL already exists in database"
    )
    
    # Write the failure report
    failure_file = "output/metrics/test_failure_report.json"
    loader.write_failure_report(failure_file)
    
    print(f"Failure report written to: {failure_file}")
    
    # Display summary
    print("\nFailure Summary:")
    print(f"Batch failures: {len(loader.failure_tracker['batch_failures'])}")
    print(f"Record failures: {len(loader.failure_tracker['record_failures'])}")
    print(f"Node failures: {len(loader.failure_tracker['node_failures'])}")
    print(f"Relationship failures: {len(loader.failure_tracker['relationship_failures'])}")
    print(f"Constraint violations: {len(loader.failure_tracker['constraint_violations'])}")
    
    # Show sample failure details
    print("\nSample Batch Failure:")
    if loader.failure_tracker['batch_failures']:
        batch_failure = loader.failure_tracker['batch_failures'][0]
        print(f"  Batch {batch_failure['batch_num']}: {batch_failure['error']}")
        print(f"  Record IDs: {batch_failure['record_ids']}")
    
    print("\nSample Node Failure:")
    if loader.failure_tracker['node_failures']:
        node_failure = loader.failure_tracker['node_failures'][0]
        print(f"  Node Label: {node_failure['node_label']}")
        print(f"  Error: {node_failure['error']}")
        print(f"  PostgreSQL Column: {node_failure['postgres_column']}")

if __name__ == "__main__":
    test_failure_tracking()
