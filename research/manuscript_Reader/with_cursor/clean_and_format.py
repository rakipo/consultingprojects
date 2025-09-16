#!/usr/bin/env python3
"""
Clean and format the extracted Telugu table data for better readability.
"""

import pandas as pd
import os
import json
from datetime import datetime

def clean_telugu_text(text):
    """Clean and format Telugu text."""
    if pd.isna(text) or text == '':
        return ''
    
    # Remove extra spaces and clean up
    text = str(text).strip()
    
    # Remove common OCR artifacts
    text = text.replace('్‌', '్')  # Fix Telugu virama
    text = text.replace('౧', '1')  # Fix Telugu digit 1
    text = text.replace('౦', '0')  # Fix Telugu digit 0
    text = text.replace('౨', '2')  # Fix Telugu digit 2
    text = text.replace('౩', '3')  # Fix Telugu digit 3
    text = text.replace('౪', '4')  # Fix Telugu digit 4
    text = text.replace('౫', '5')  # Fix Telugu digit 5
    text = text.replace('౬', '6')  # Fix Telugu digit 6
    text = text.replace('౭', '7')  # Fix Telugu digit 7
    text = text.replace('౮', '8')  # Fix Telugu digit 8
    text = text.replace('౯', '9')  # Fix Telugu digit 9
    
    return text

def process_extracted_data(input_dir):
    """Process and clean the extracted data."""
    print("🧹 Cleaning and formatting extracted Telugu data...")
    
    # Read the detailed JSON file
    json_path = os.path.join(input_dir, "table_extraction_details.json")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Process each page
    cleaned_pages = []
    
    for page_data in data:
        page_num = page_data['page_number']
        raw_text = page_data['raw_text']
        table_rows = page_data['table_rows']
        
        print(f"\n📄 Processing Page {page_num}:")
        print(f"   Raw text length: {len(raw_text)} characters")
        print(f"   Table rows: {len(table_rows)}")
        
        # Clean the raw text
        cleaned_text = clean_telugu_text(raw_text)
        
        # Process table rows
        cleaned_rows = []
        for row in table_rows:
            cleaned_row = [clean_telugu_text(cell) for cell in row]
            cleaned_rows.append(cleaned_row)
        
        # Create DataFrame
        if cleaned_rows:
            df = pd.DataFrame(cleaned_rows)
            # Use first row as header if it looks like headers
            if len(cleaned_rows) > 1:
                df.columns = cleaned_rows[0]
                df = df.iloc[1:]
        else:
            df = pd.DataFrame()
        
        cleaned_pages.append({
            'page_number': page_num,
            'raw_text': cleaned_text,
            'table_data': df,
            'confidence': page_data['confidence']
        })
        
        print(f"   Cleaned text preview: {cleaned_text[:100]}...")
        if not df.empty:
            print(f"   Table shape: {df.shape}")
    
    return cleaned_pages

def save_cleaned_data(cleaned_pages, output_dir):
    """Save the cleaned data in multiple formats."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_dir = os.path.join(output_dir, f"cleaned_{timestamp}")
    os.makedirs(clean_dir, exist_ok=True)
    
    print(f"\n💾 Saving cleaned data to {clean_dir}")
    
    # Save cleaned Excel file
    excel_path = os.path.join(clean_dir, "cleaned_telugu_data.xlsx")
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        for page in cleaned_pages:
            if not page['table_data'].empty:
                sheet_name = f"Page_{page['page_number']}"
                page['table_data'].to_excel(writer, sheet_name=sheet_name, index=False)
    
    # Save cleaned text files
    for page in cleaned_pages:
        text_path = os.path.join(clean_dir, f"page_{page['page_number']}_cleaned.txt")
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(f"Page {page['page_number']} - Cleaned Telugu Text\n")
            f.write("=" * 50 + "\n\n")
            f.write(page['raw_text'])
            f.write("\n\n" + "=" * 50 + "\n")
    
    # Save combined cleaned text
    combined_text_path = os.path.join(clean_dir, "all_pages_cleaned.txt")
    with open(combined_text_path, 'w', encoding='utf-8') as f:
        f.write("Complete Telugu Manuscript - Cleaned Text\n")
        f.write("=" * 60 + "\n\n")
        
        for page in cleaned_pages:
            f.write(f"=== PAGE {page['page_number']} ===\n")
            f.write(f"Confidence: {page['confidence']:.1f}%\n\n")
            f.write(page['raw_text'])
            f.write("\n\n" + "=" * 50 + "\n\n")
    
    # Save summary
    summary_path = os.path.join(clean_dir, "cleaning_summary.txt")
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("Telugu Data Cleaning Summary\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Total pages processed: {len(cleaned_pages)}\n")
        
        total_text_length = sum(len(page['raw_text']) for page in cleaned_pages)
        avg_confidence = sum(page['confidence'] for page in cleaned_pages) / len(cleaned_pages)
        
        f.write(f"Total text length: {total_text_length} characters\n")
        f.write(f"Average confidence: {avg_confidence:.1f}%\n\n")
        
        f.write("Page-by-page summary:\n")
        f.write("-" * 30 + "\n")
        for page in cleaned_pages:
            f.write(f"Page {page['page_number']}: {len(page['raw_text'])} chars, "
                   f"{page['confidence']:.1f}% confidence\n")
    
    return clean_dir, excel_path, combined_text_path

def main():
    """Main function."""
    # Find the most recent output directory
    output_base = "Outputs"
    if not os.path.exists(output_base):
        print("❌ No output directory found. Please run the table extractor first.")
        return
    
    # Get the most recent timestamp directory
    timestamp_dirs = [d for d in os.listdir(output_base) if os.path.isdir(os.path.join(output_base, d))]
    if not timestamp_dirs:
        print("❌ No timestamp directories found.")
        return
    
    latest_dir = sorted(timestamp_dirs)[-1]
    input_dir = os.path.join(output_base, latest_dir)
    
    print(f"📁 Processing data from: {input_dir}")
    
    # Process the data
    cleaned_pages = process_extracted_data(input_dir)
    
    # Save cleaned data
    clean_dir, excel_path, text_path = save_cleaned_data(cleaned_pages, output_base)
    
    print(f"\n✅ CLEANING COMPLETE!")
    print(f"📁 Cleaned data saved to: {clean_dir}")
    print(f"📊 Excel file: {excel_path}")
    print(f"📝 Combined text: {text_path}")
    
    # Show sample of cleaned text
    if cleaned_pages and cleaned_pages[0]['raw_text']:
        print(f"\n📖 Sample cleaned text (Page 1):")
        print("-" * 40)
        sample_text = cleaned_pages[0]['raw_text'][:300]
        print(sample_text)
        if len(cleaned_pages[0]['raw_text']) > 300:
            print("...")

if __name__ == "__main__":
    main()
