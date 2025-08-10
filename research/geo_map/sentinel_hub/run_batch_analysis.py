#!/usr/bin/env python3
"""
Batch Property Analysis Usage Example
Demonstrates how to run batch analysis on multiple properties
"""

import os
import sys
from batch_property_analyzer import BatchPropertyAnalyzer

def main():
    """Example usage of batch property analyzer"""
    
    print("🏠 Batch Property Analysis Example")
    print("=" * 50)
    
    # Check if sample CSV exists
    sample_csv = "sample_properties.csv"
    if not os.path.exists(sample_csv):
        print(f"❌ Sample CSV file '{sample_csv}' not found!")
        print("Please create a CSV file with the following columns:")
        print("  lp_no, extent_ac, POINT_ID, EASTING-X, NORTHING-Y, LATITUDE, LONGITUDE")
        return
    
    # Initialize analyzer
    analyzer = BatchPropertyAnalyzer()
    
    # Define analysis periods
    before_period = ("2022-11-01", "2023-01-31")
    after_period = ("2025-01-01", "2025-03-31")
    
    print(f"📅 Analysis Periods:")
    print(f"   Before: {before_period[0]} to {before_period[1]}")
    print(f"   After: {after_period[0]} to {after_period[1]}")
    
    # Run batch analysis
    try:
        results = analyzer.analyze_batch_properties(sample_csv, before_period, after_period)
        
        print(f"\n📊 ANALYSIS COMPLETED!")
        print(f"Total Properties Analyzed: {len(results)}")
        
        # Show sample results
        print(f"\n📋 Sample Results (first 2 properties):")
        for i, (_, row) in enumerate(results.head(2).iterrows()):
            print(f"\nProperty {i+1}: {row['LATITUDE']:.6f}, {row['LONGITUDE']:.6f}")
            print(f"  Vegetation: {row['Vegetation (NDVI)-Interpretation']}")
            print(f"  Built-up: {row['Built-up Area (NDBI)-Interpretation']}")
            print(f"  Water: {row['Water/Moisture (NDWI)-Interpretation']}")
        
        # Count significant changes
        significant_changes = 0
        for _, row in results.iterrows():
            if any(row[f'{metric}-Significance'] == 'Yes' for metric in ['Vegetation (NDVI)', 'Built-up Area (NDBI)', 'Water/Moisture (NDWI)']):
                significant_changes += 1
        
        print(f"\n🎯 Summary:")
        print(f"  Properties with Significant Changes: {significant_changes}")
        print(f"  Properties Analyzed Successfully: {len(results)}")
        
    except Exception as e:
        print(f"❌ Error during batch analysis: {str(e)}")
        print("Please check your configuration files and internet connection.")

if __name__ == "__main__":
    main()
