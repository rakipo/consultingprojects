#!/usr/bin/env python3
"""
Telugu Table Extractor
Specialized for extracting table data from Telugu manuscripts and converting to Excel/CSV.
"""

import os
import sys
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from pdf2image import convert_from_path
import pandas as pd
import json
from datetime import datetime
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TeluguTableExtractor:
    """Specialized extractor for Telugu table data."""
    
    def __init__(self):
        """Initialize the table extractor."""
        self.results = []
        
        # Set up Tesseract path for macOS
        if sys.platform == "darwin":
            tesseract_path = "/opt/homebrew/bin/tesseract"
            if os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        logger.info("Telugu Table Extractor initialized")
    
    def preprocess_for_table(self, image: Image.Image) -> Image.Image:
        """Preprocess image specifically for table extraction."""
        logger.info("Preprocessing image for table extraction")
        
        # Convert to numpy array
        img_array = np.array(image)
        
        # Convert to grayscale if needed
        if len(img_array.shape) == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Resize for better processing
        height, width = img_array.shape
        if height < 1500:
            scale = 1500 / height
            new_width = int(width * scale)
            img_array = cv2.resize(img_array, (new_width, 1500), interpolation=cv2.INTER_CUBIC)
        
        # Denoise
        img_array = cv2.fastNlMeansDenoising(img_array, h=10)
        
        # Enhance contrast for better text visibility
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        img_array = clahe.apply(img_array)
        
        # Detect and enhance table lines
        # Horizontal lines
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        horizontal_lines = cv2.morphologyEx(img_array, cv2.MORPH_OPEN, horizontal_kernel)
        
        # Vertical lines
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        vertical_lines = cv2.morphologyEx(img_array, cv2.MORPH_OPEN, vertical_kernel)
        
        # Combine lines
        table_structure = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0.0)
        
        # Enhance the original image
        img_array = cv2.addWeighted(img_array, 0.8, table_structure, 0.2, 0.0)
        
        # Adaptive thresholding
        img_array = cv2.adaptiveThreshold(img_array, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                        cv2.THRESH_BINARY, 11, 2)
        
        # Convert back to PIL Image
        processed_image = Image.fromarray(img_array)
        
        # Additional PIL enhancements
        enhancer = ImageEnhance.Contrast(processed_image)
        processed_image = enhancer.enhance(1.2)
        
        enhancer = ImageEnhance.Sharpness(processed_image)
        processed_image = enhancer.enhance(1.1)
        
        return processed_image
    
    def extract_table_data(self, image: Image.Image) -> dict:
        """Extract table data using multiple OCR approaches."""
        logger.info("Extracting table data")
        
        # Try different OCR configurations for table data
        configs = {
            "telugu_table": "-l tel --oem 3 --psm 6",
            "telugu_eng_table": "-l tel+eng --oem 3 --psm 6",
            "telugu_psm4": "-l tel --oem 3 --psm 4",
            "telugu_psm3": "-l tel --oem 3 --psm 3"
        }
        
        best_result = {"text": "", "confidence": 0, "config": ""}
        
        for config_name, config in configs.items():
            try:
                logger.info(f"Trying config: {config_name}")
                
                # Get detailed data
                data = pytesseract.image_to_data(image, config=config, output_type=pytesseract.Output.DICT)
                
                # Extract text and confidence
                text_parts = []
                confidences = []
                
                for i in range(len(data['text'])):
                    if int(data['conf'][i]) > 0:
                        text_parts.append(data['text'][i])
                        confidences.append(int(data['conf'][i]))
                
                extracted_text = ' '.join(text_parts).strip()
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                
                if avg_confidence > best_result['confidence']:
                    best_result = {
                        "text": extracted_text,
                        "confidence": avg_confidence,
                        "config": config_name
                    }
                
                logger.info(f"{config_name}: {len(extracted_text)} chars, {avg_confidence:.1f}% confidence")
                
            except Exception as e:
                logger.error(f"Config {config_name} failed: {e}")
        
        return best_result
    
    def parse_table_text(self, text: str) -> list:
        """Parse extracted text to identify table structure."""
        logger.info("Parsing table text")
        
        # Split text into lines
        lines = text.split('\n')
        
        # Clean and filter lines
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line and len(line) > 2:  # Filter out very short lines
                cleaned_lines.append(line)
        
        # Try to identify table rows
        table_rows = []
        current_row = []
        
        for line in cleaned_lines:
            # Look for patterns that might indicate table cells
            # Split by common separators
            cells = re.split(r'\s{2,}|\t|\|', line)  # Split by multiple spaces, tabs, or pipes
            
            # Clean cells
            cells = [cell.strip() for cell in cells if cell.strip()]
            
            if len(cells) > 1:  # If we have multiple cells, it's likely a table row
                table_rows.append(cells)
            elif len(cells) == 1 and cells[0]:  # Single cell, might be a header or single column
                table_rows.append(cells)
        
        return table_rows
    
    def create_dataframe(self, table_rows: list) -> pd.DataFrame:
        """Create a pandas DataFrame from table rows."""
        logger.info("Creating DataFrame from table rows")
        
        if not table_rows:
            return pd.DataFrame()
        
        # Find the maximum number of columns
        max_cols = max(len(row) for row in table_rows) if table_rows else 0
        
        # Pad rows to have the same number of columns
        padded_rows = []
        for row in table_rows:
            padded_row = row + [''] * (max_cols - len(row))
            padded_rows.append(padded_row)
        
        # Create DataFrame
        df = pd.DataFrame(padded_rows)
        
        # If we have more than one row, use the first row as header
        if len(padded_rows) > 1:
            df.columns = padded_rows[0]
            df = df.iloc[1:]  # Remove the header row from data
        
        return df
    
    def process_pdf(self, pdf_path: str) -> list:
        """Process PDF and extract table data."""
        logger.info(f"Processing PDF: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Convert PDF to images
        logger.info("Converting PDF to images")
        try:
            images = convert_from_path(pdf_path, dpi=300, first_page=1, last_page=None)
        except Exception as e:
            logger.error(f"Failed to convert PDF: {e}")
            raise
        
        logger.info(f"Converted {len(images)} pages to images")
        
        page_results = []
        
        for page_num, image in enumerate(images, 1):
            logger.info(f"Processing page {page_num}/{len(images)}")
            
            # Preprocess image for table extraction
            processed_image = self.preprocess_for_table(image)
            
            # Extract table data
            ocr_result = self.extract_table_data(processed_image)
            
            # Parse table structure
            table_rows = self.parse_table_text(ocr_result['text'])
            
            # Create DataFrame
            df = self.create_dataframe(table_rows)
            
            page_result = {
                "page_number": page_num,
                "raw_text": ocr_result['text'],
                "confidence": ocr_result['confidence'],
                "config_used": ocr_result['config'],
                "table_rows": table_rows,
                "dataframe": df,
                "row_count": len(table_rows),
                "col_count": len(table_rows[0]) if table_rows else 0
            }
            
            page_results.append(page_result)
            
            logger.info(f"Page {page_num} - Confidence: {ocr_result['confidence']:.1f}%, "
                       f"Rows: {len(table_rows)}, Cols: {len(table_rows[0]) if table_rows else 0}")
        
        self.results = page_results
        return page_results
    
    def save_results(self, output_dir: str = "Outputs") -> dict:
        """Save results in Excel, CSV, and text formats."""
        logger.info(f"Saving results to {output_dir}")
        
        # Create timestamp-based directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamp_dir = os.path.join(output_dir, timestamp)
        os.makedirs(timestamp_dir, exist_ok=True)
        
        saved_files = {}
        
        # Combine all tables into one Excel file
        excel_path = os.path.join(timestamp_dir, "telugu_table_data.xlsx")
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            for page in self.results:
                if not page['dataframe'].empty:
                    sheet_name = f"Page_{page['page_number']}"
                    page['dataframe'].to_excel(writer, sheet_name=sheet_name, index=False)
        
        saved_files["excel"] = excel_path
        
        # Save individual CSV files for each page
        csv_files = []
        for page in self.results:
            if not page['dataframe'].empty:
                csv_path = os.path.join(timestamp_dir, f"page_{page['page_number']}_table.csv")
                page['dataframe'].to_csv(csv_path, index=False, encoding='utf-8')
                csv_files.append(csv_path)
        
        saved_files["csv_files"] = csv_files
        
        # Save combined CSV
        combined_csv_path = os.path.join(timestamp_dir, "combined_table_data.csv")
        all_dataframes = [page['dataframe'] for page in self.results if not page['dataframe'].empty]
        if all_dataframes:
            combined_df = pd.concat(all_dataframes, ignore_index=True)
            combined_df.to_csv(combined_csv_path, index=False, encoding='utf-8')
            saved_files["combined_csv"] = combined_csv_path
        
        # Save detailed JSON with all data
        json_path = os.path.join(timestamp_dir, "table_extraction_details.json")
        json_data = []
        for page in self.results:
            page_data = {
                "page_number": page['page_number'],
                "confidence": page['confidence'],
                "config_used": page['config_used'],
                "raw_text": page['raw_text'],
                "table_rows": page['table_rows'],
                "row_count": page['row_count'],
                "col_count": page['col_count']
            }
            json_data.append(page_data)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        saved_files["json"] = json_path
        
        # Save summary text file
        summary_path = os.path.join(timestamp_dir, "extraction_summary.txt")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("Telugu Table Extraction Summary\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Total Pages: {len(self.results)}\n\n")
            
            total_rows = sum(page['row_count'] for page in self.results)
            avg_confidence = sum(page['confidence'] for page in self.results) / len(self.results)
            
            f.write(f"Total Table Rows Extracted: {total_rows}\n")
            f.write(f"Average Confidence: {avg_confidence:.1f}%\n\n")
            
            f.write("Page-by-Page Summary:\n")
            f.write("-" * 30 + "\n")
            for page in self.results:
                f.write(f"Page {page['page_number']}: {page['row_count']} rows, "
                       f"{page['col_count']} cols, {page['confidence']:.1f}% confidence\n")
        
        saved_files["summary"] = summary_path
        
        logger.info(f"Results saved to: {timestamp_dir}")
        return saved_files

def main():
    """Main function to run the table extractor."""
    pdf_path = "/Users/ravikiranponduri/Desktop/consultingprojects/research/manuscript_Reader/test_manu.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        sys.exit(1)
    
    print("📊 Telugu Table Extractor")
    print("=" * 50)
    print(f"Processing: {pdf_path}")
    print("Focus: Table data extraction to Excel/CSV format")
    print()
    
    try:
        # Initialize extractor
        extractor = TeluguTableExtractor()
        
        # Process PDF
        print("Processing PDF for table extraction...")
        results = extractor.process_pdf(pdf_path)
        
        # Save results
        print("Saving results...")
        saved_files = extractor.save_results("Outputs")
        
        # Print summary
        print("\n" + "="*60)
        print("✅ TABLE EXTRACTION COMPLETE!")
        print("="*60)
        
        total_rows = sum(page['row_count'] for page in results)
        avg_confidence = sum(page['confidence'] for page in results) / len(results)
        
        print(f"📄 Total pages processed: {len(results)}")
        print(f"📊 Total table rows extracted: {total_rows}")
        print(f"🎯 Average confidence: {avg_confidence:.1f}%")
        
        print(f"\n📁 Output files:")
        print(f"   EXCEL: {saved_files['excel']}")
        if 'combined_csv' in saved_files:
            print(f"   COMBINED CSV: {saved_files['combined_csv']}")
        print(f"   JSON: {saved_files['json']}")
        print(f"   SUMMARY: {saved_files['summary']}")
        
        if 'csv_files' in saved_files:
            print(f"   INDIVIDUAL CSV FILES: {len(saved_files['csv_files'])} files")
        
        # Show table structure for first page
        if results and not results[0]['dataframe'].empty:
            print(f"\n📋 Sample table structure (Page 1):")
            print("-" * 40)
            df = results[0]['dataframe']
            print(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
            print("\nFirst few rows:")
            print(df.head().to_string())
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
