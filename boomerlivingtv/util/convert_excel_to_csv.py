#!/usr/bin/env python3
"""
Convert Excel file to CSV format
"""
import pandas as pd
import sys
import os

def convert_excel_to_csv(excel_file, csv_file):
    """Convert Excel file to CSV"""
    try:
        # Read the Excel file
        df = pd.read_excel(excel_file)
        
        # Save as CSV
        df.to_csv(csv_file, index=False)
        
        print(f"Successfully converted {excel_file} to {csv_file}")
        print(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")
        print(f"Columns: {list(df.columns)}")
        
    except Exception as e:
        print(f"Error converting file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    excel_file = "boomerlivingtv/app/init/SAMPLE_OUTPUT_CLUSTER_4_RETIREMENT_FINANCE.xlsx"
    csv_file = "trending.csv"
    
    if not os.path.exists(excel_file):
        print(f"Error: Excel file {excel_file} not found")
        sys.exit(1)
    
    convert_excel_to_csv(excel_file, csv_file)