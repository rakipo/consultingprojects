#!/usr/bin/env python3
"""
Land Area Analysis Example
Demonstrates how the batch analyzer uses land area information when calling Sentinel Hub
"""

import pandas as pd
import numpy as np
from batch_property_analyzer import BatchPropertyAnalyzer

def demonstrate_land_area_usage():
    """Demonstrate how land area information is used in Sentinel Hub analysis"""
    
    print("🏠 Land Area Analysis with Sentinel Hub")
    print("=" * 60)
    
    # Create sample data with different land areas
    sample_data = {
        'lp_no': [1, 2, 3, 4, 5],
        'extent_ac': [0.5, 5.0, 50.0, 200.0, 500.0],  # Different land areas
        'POINT_ID': [1, 2, 3, 4, 5],
        'EASTING-X': [340751.55, 340869.12, 340900.00, 340800.00, 340850.00],
        'NORTHING-Y': [1590485.86, 1590228.96, 1590300.00, 1590400.00, 1590200.00],
        'LATITUDE': [14.382015, 14.379700, 14.380500, 14.381000, 14.379000],
        'LONGITUDE': [79.523023, 79.524128, 79.524500, 79.523500, 79.524000]
    }
    
    # Create DataFrame
    df = pd.DataFrame(sample_data)
    
    # Save to CSV
    csv_file = "land_area_demo.csv"
    df.to_csv(csv_file, index=False)
    
    print("📊 Sample Properties with Different Land Areas:")
    print(df.to_string(index=False))
    print()
    
    # Calculate and display area information
    print("📏 Land Area Calculations:")
    for _, row in df.iterrows():
        acres = row['extent_ac']
        sq_meters = acres * 4046.86
        sq_feet = acres * 43560
        radius_meters = (sq_meters / 3.14159) ** 0.5 if sq_meters > 0 else 50
        
        print(f"Property {row['lp_no']}:")
        print(f"  Land Area: {acres:.2f} acres")
        print(f"  Square Meters: {sq_meters:.0f} sq m")
        print(f"  Square Feet: {sq_feet:.0f} sq ft")
        print(f"  Estimated Radius: {radius_meters:.0f} meters")
        print()
    
    # Initialize analyzer
    analyzer = BatchPropertyAnalyzer()
    
    # Define analysis periods
    before_period = ("2022-11-01", "2023-01-31")
    after_period = ("2025-01-01", "2025-03-31")
    
    print("🔍 How Land Area Affects Sentinel Hub Analysis:")
    print("1. **Bounding Box Calculation**:")
    print("   - Small areas (< 1 acre): Uses minimum 50m radius")
    print("   - Large areas (> 1 acre): Calculates radius from area")
    print("   - Formula: radius = √(area_in_sq_meters / π)")
    print()
    
    print("2. **Sentinel Hub API Calls**:")
    print("   - Each property gets its own bounding box")
    print("   - Bounding box size determines image resolution")
    print("   - Larger areas get more pixels for analysis")
    print()
    
    print("3. **Analysis Quality**:")
    print("   - Larger areas: Better statistical significance")
    print("   - Smaller areas: May need alternative data sources")
    print("   - All areas: Get NDVI, NDBI, NDWI analysis")
    print()
    
    # Run analysis
    try:
        print("🚀 Running Analysis with Land Area Consideration...")
        results = analyzer.analyze_batch_properties(csv_file, before_period, after_period)
        
        print(f"\n✅ Analysis Completed!")
        print(f"Properties Analyzed: {len(results)}")
        
        # Show results summary
        print(f"\n📋 Results Summary:")
        for _, row in results.iterrows():
            print(f"\nProperty {row['lp_no']} ({row['extent_ac']:.2f} acres):")
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
        print(f"  Date Format: DD-MMM-YYYY (e.g., 01-NOV-2022)")
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")

def show_sentinel_hub_integration():
    """Show how Sentinel Hub integration works with land area"""
    
    print("\n" + "=" * 60)
    print("🔗 Sentinel Hub Integration Details")
    print("=" * 60)
    
    print("1. **Input Processing**:")
    print("   CSV → Pandas DataFrame → Individual property analysis")
    print()
    
    print("2. **Bounding Box Creation**:")
    print("   Coordinates + Land Area → Optimal bounding box")
    print("   Larger areas → Larger bounding boxes")
    print("   Smaller areas → Minimum viable bounding boxes")
    print()
    
    print("3. **Sentinel Hub API Calls**:")
    print("   - DataCollection.SENTINEL2_L2A")
    print("   - Custom evalscript for NDVI, NDBI, NDWI")
    print("   - Time period filtering")
    print("   - Cloud coverage filtering")
    print()
    
    print("4. **Output Generation**:")
    print("   - JSON format for programmatic access")
    print("   - CSV format with DD-MMM-YYYY dates")
    print("   - Comprehensive analysis results")
    print()
    
    print("5. **Land Area Benefits**:")
    print("   ✅ Better statistical significance")
    print("   ✅ More accurate change detection")
    print("   ✅ Appropriate resolution selection")
    print("   ✅ Context-aware analysis")

if __name__ == "__main__":
    demonstrate_land_area_usage()
    show_sentinel_hub_integration()
