#!/usr/bin/env python3
"""
Final summary of Telugu manuscript extraction results.
"""

import os
import pandas as pd
from datetime import datetime

def show_final_summary():
    """Show a comprehensive summary of all extraction results."""
    print("📋 TELUGU MANUSCRIPT EXTRACTION - FINAL SUMMARY")
    print("=" * 60)
    
    # Find all output directories
    output_base = "Outputs"
    if not os.path.exists(output_base):
        print("❌ No output directory found.")
        return
    
    print(f"📁 Output directory: {os.path.abspath(output_base)}")
    
    # List all timestamp directories
    timestamp_dirs = [d for d in os.listdir(output_base) if os.path.isdir(os.path.join(output_base, d))]
    timestamp_dirs.sort()
    
    print(f"\n📂 Available extraction results:")
    for i, dir_name in enumerate(timestamp_dirs, 1):
        print(f"   {i}. {dir_name}")
    
    # Show the latest cleaned results
    cleaned_dirs = [d for d in timestamp_dirs if d.startswith('cleaned_')]
    if cleaned_dirs:
        latest_cleaned = sorted(cleaned_dirs)[-1]
        cleaned_path = os.path.join(output_base, latest_cleaned)
        
        print(f"\n✨ LATEST CLEANED RESULTS: {latest_cleaned}")
        print("-" * 40)
        
        # List files in cleaned directory
        files = os.listdir(cleaned_path)
        for file in sorted(files):
            file_path = os.path.join(cleaned_path, file)
            file_size = os.path.getsize(file_path)
            print(f"   📄 {file} ({file_size:,} bytes)")
        
        # Show Excel file contents
        excel_file = os.path.join(cleaned_path, "cleaned_telugu_data.xlsx")
        if os.path.exists(excel_file):
            print(f"\n📊 Excel file contents:")
            try:
                xl_file = pd.ExcelFile(excel_file)
                for sheet_name in xl_file.sheet_names:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)
                    print(f"   📋 {sheet_name}: {df.shape[0]} rows × {df.shape[1]} columns")
            except Exception as e:
                print(f"   ❌ Error reading Excel file: {e}")
        
        # Show sample text
        text_file = os.path.join(cleaned_path, "all_pages_cleaned.txt")
        if os.path.exists(text_file):
            print(f"\n📝 Sample extracted text:")
            print("-" * 30)
            with open(text_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Show first 500 characters
                sample = content[:500]
                print(sample)
                if len(content) > 500:
                    print("...")
    
    print(f"\n🎯 EXTRACTION METHODS USED:")
    print("   1. Tesseract OCR with Telugu language support")
    print("   2. Multiple preprocessing techniques")
    print("   3. Table structure detection")
    print("   4. Text cleaning and formatting")
    
    print(f"\n📋 OUTPUT FORMATS AVAILABLE:")
    print("   • Excel (.xlsx) - Structured table data")
    print("   • CSV files - Individual page tables")
    print("   • Text files - Cleaned Telugu text")
    print("   • JSON files - Detailed extraction data")
    
    print(f"\n💡 NEXT STEPS:")
    print("   1. Open the Excel file to view structured table data")
    print("   2. Review the cleaned text files for content accuracy")
    print("   3. Use the CSV files for further data processing")
    print("   4. Check individual page files for specific content")
    
    print(f"\n🔧 TO IMPROVE ACCURACY:")
    print("   • Ensure high-quality PDF scans (300+ DPI)")
    print("   • Use clear, well-lit images")
    print("   • Consider using Google Cloud Vision API for better results")
    print("   • Manually review and correct extracted text")

if __name__ == "__main__":
    show_final_summary()
