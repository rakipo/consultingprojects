#!/usr/bin/env python3
"""
Complete Demo Script for Sentinel-2 Satellite Data Analysis System
Demonstrates the entire workflow from database setup to analysis
"""
from database_schema import create_database, populate_sentinel_data, populate_thresholds
from sentinel_analyzer import SentinelAnalyzer
from csv_generator import generate_sample_csv, generate_realistic_csv
import os

def run_complete_demo():
    """Run a complete demo of the Sentinel analysis system"""
    print("🛰️  Sentinel-2 Satellite Data Analysis - Complete Demo")
    print("=" * 60)
    
    # Step 1: Initialize database
    print("\n1. 📊 Initializing database and populating with sample data...")
    create_database()
    populate_sentinel_data()
    populate_thresholds()
    print("✅ Database initialized successfully")
    
    # Step 2: Generate sample CSV input files
    print("\n2. 📝 Generating sample CSV input files...")
    generate_sample_csv('demo_input.csv', 100)
    generate_realistic_csv('demo_realistic.csv', 100)
    print("✅ CSV files generated successfully")
    
    # Step 3: Process CSV input and analyze
    print("\n3. 🔍 Processing CSV input and performing analysis...")
    analyzer = SentinelAnalyzer()
    
    try:
        # Process the sample CSV
        print("\nProcessing demo_input.csv...")
        analyzer.process_csv_input('demo_input.csv')
        
        # Show analysis results
        print("\n4. 📈 Analysis Results:")
        analyzer.print_analysis_report()
        
        # Export results
        print("\n5. 💾 Exporting results...")
        analyzer.export_results_to_csv('demo_results.csv')
        
        # Export to Excel with multiple worksheets
        print("\n6. 📊 Exporting to Excel with multiple worksheets...")
        excel_file = analyzer.export_to_excel()
        if excel_file:
            print(f"✅ Excel file created: {excel_file}")
        else:
            print("❌ Excel export failed. Install openpyxl: pip install openpyxl")
        
        # Show sample of raw data
        print("\n7. 📋 Sample Raw Data (Plot 1):")
        plot_data = analyzer.get_plot_data(1)
        for record in plot_data:
            print(f"  Date: {record[2]}, NDVI: {record[3]:.2f}, NDBI: {record[4]:.2f}, NDWI: {record[5]:.2f}")
        
        # Show available thresholds
        print("\n8. 🎯 Available Land Type Thresholds:")
        thresholds = analyzer.get_thresholds()
        for i, threshold in enumerate(thresholds[:10]):  # Show first 10
            print(f"  {i+1:2d}. {threshold[1]}")
            print(f"      Vegetation: {threshold[2]}")
            print(f"      Construction: {threshold[3]}")
            print(f"      Flooding: {threshold[4]}")
            print()
        
        if len(thresholds) > 10:
            print(f"      ... and {len(thresholds) - 10} more land types")
        
        # Show transaction summary
        transactions = analyzer.get_transactions()
        print(f"\n9. 📊 Transaction Summary:")
        print(f"   Total transactions processed: {len(transactions)}")
        
        # Count changes by type
        veg_changes = sum(1 for t in transactions if t[16] != "No Change")
        con_changes = sum(1 for t in transactions if t[17] != "No Change")
        flood_changes = sum(1 for t in transactions if t[18] != "No Change")
        
        print(f"   Vegetation changes detected: {veg_changes}")
        print(f"   Construction changes detected: {con_changes}")
        print(f"   Flooding changes detected: {flood_changes}")
        
        # Show sample transactions
        print(f"\n10. 🔍 Sample Transactions (first 5):")
        for i, trans in enumerate(transactions[:5]):
            print(f"   Test {trans[1]}: Plot {trans[2]}")
            print(f"     Period: {trans[3]} → {trans[4]}")
            print(f"     Deltas: NDVI={trans[10]:.3f}, NDBI={trans[11]:.3f}, NDWI={trans[12]:.3f}")
            print(f"     Results: Veg={trans[16]}, Con={trans[17]}, Flood={trans[18]}")
            print()
    
    finally:
        analyzer.close_connection()
    
    # Step 4: Show file structure
    print("\n11. 📁 Generated Files:")
    files = [
        'sentinel_analysis.db',
        'demo_input.csv',
        'demo_realistic.csv',
        'demo_results.csv'
    ]
    
    for file in files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"   ✅ {file} ({size} bytes)")
        else:
            print(f"   ❌ {file} (not found)")
    
    print("\n🎉 Complete demo finished successfully!")
    print("\nNext steps:")
    print("1. Modify demo_input.csv with your own test data")
    print("2. Run: python sentinel_analyzer.py")
    print("3. Check demo_results.csv for analysis results")
    print("4. Modify thresholds in database_schema.py for different rules")

def show_usage_examples():
    """Show usage examples for the system"""
    print("\n" + "="*60)
    print("USAGE EXAMPLES")
    print("="*60)
    
    print("\n1. Initialize database:")
    print("   python database_schema.py")
    
    print("\n2. Generate sample CSV input:")
    print("   python csv_generator.py")
    
    print("\n3. Process CSV and analyze:")
    print("   from sentinel_analyzer import SentinelAnalyzer")
    print("   analyzer = SentinelAnalyzer()")
    print("   analyzer.process_csv_input('your_input.csv')")
    print("   analyzer.print_analysis_report()")
    print("   analyzer.export_results_to_csv('results.csv')")
    
    print("\n4. Custom analysis:")
    print("   # Get specific plot data")
    print("   plot_data = analyzer.get_plot_data(plot_no=1)")
    print("   ")
    print("   # Get all transactions")
    print("   transactions = analyzer.get_transactions()")
    print("   ")
    print("   # Get thresholds")
    print("   thresholds = analyzer.get_thresholds()")

if __name__ == "__main__":
    run_complete_demo()
    show_usage_examples()
