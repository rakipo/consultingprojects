#!/usr/bin/env python3
"""
Online OCR Extractor for Telugu Text
Uses free online OCR services for better Telugu text recognition.
"""

import os
import sys
import requests
import json
from datetime import datetime
from pdf2image import convert_from_path
from PIL import Image
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OnlineOCRExtractor:
    """Extractor using free online OCR services."""
    
    def __init__(self):
        """Initialize the online OCR extractor."""
        self.results = []
        logger.info("Online OCR Extractor initialized")
    
    def extract_with_i2ocr(self, image_path: str) -> dict:
        """Extract text using i2OCR service."""
        logger.info("Trying i2OCR service")
        
        try:
            # i2OCR API endpoint
            url = "https://www.i2ocr.com/api/ocr"
            
            # Prepare the request
            with open(image_path, 'rb') as image_file:
                files = {'file': image_file}
                data = {
                    'language': 'tel',
                    'format': 'json'
                }
                
                response = requests.post(url, files=files, data=data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    if 'text' in result:
                        return {
                            "service": "i2ocr",
                            "text": result['text'],
                            "confidence": result.get('confidence', 0),
                            "success": True
                        }
                
                return {
                    "service": "i2ocr",
                    "text": "",
                    "confidence": 0,
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"i2OCR failed: {e}")
            return {
                "service": "i2ocr",
                "text": "",
                "confidence": 0,
                "success": False,
                "error": str(e)
            }
    
    def extract_with_ocr_space(self, image_path: str) -> dict:
        """Extract text using OCR.space API."""
        logger.info("Trying OCR.space service")
        
        try:
            # OCR.space API endpoint
            url = "https://api.ocr.space/parse/image"
            
            with open(image_path, 'rb') as image_file:
                files = {'file': image_file}
                data = {
                    'language': 'tel',
                    'isOverlayRequired': False,
                    'apikey': 'helloworld'  # Free API key
                }
                
                response = requests.post(url, files=files, data=data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('IsErroredOnProcessing', False):
                        return {
                            "service": "ocr_space",
                            "text": "",
                            "confidence": 0,
                            "success": False,
                            "error": result.get('ErrorMessage', 'Unknown error')
                        }
                    
                    parsed_results = result.get('ParsedResults', [])
                    if parsed_results:
                        text = parsed_results[0].get('ParsedText', '')
                        return {
                            "service": "ocr_space",
                            "text": text,
                            "confidence": 85,  # OCR.space doesn't provide confidence
                            "success": True
                        }
                
                return {
                    "service": "ocr_space",
                    "text": "",
                    "confidence": 0,
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"OCR.space failed: {e}")
            return {
                "service": "ocr_space",
                "text": "",
                "confidence": 0,
                "success": False,
                "error": str(e)
            }
    
    def process_pdf(self, pdf_path: str, max_pages: int = 3) -> list:
        """Process PDF using online OCR services."""
        logger.info(f"Processing PDF: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Convert PDF to images
        logger.info("Converting PDF to images")
        try:
            images = convert_from_path(pdf_path, dpi=300, first_page=1, last_page=max_pages)
        except Exception as e:
            logger.error(f"Failed to convert PDF: {e}")
            raise
        
        logger.info(f"Converted {len(images)} pages to images")
        
        page_results = []
        
        for page_num, image in enumerate(images, 1):
            logger.info(f"Processing page {page_num}/{len(images)}")
            
            # Save image temporarily
            temp_image_path = f"temp_page_{page_num}.png"
            image.save(temp_image_path)
            
            page_result = {
                "page_number": page_num,
                "services": {},
                "best_text": "",
                "best_confidence": 0,
                "best_service": ""
            }
            
            # Try different online services
            services = [
                self.extract_with_ocr_space,
                self.extract_with_i2ocr
            ]
            
            for service_func in services:
                try:
                    result = service_func(temp_image_path)
                    service_name = result['service']
                    page_result['services'][service_name] = result
                    
                    if result['success'] and result['confidence'] > page_result['best_confidence']:
                        page_result['best_text'] = result['text']
                        page_result['best_confidence'] = result['confidence']
                        page_result['best_service'] = service_name
                    
                    logger.info(f"  {service_name}: {len(result['text'])} chars, "
                               f"{result['confidence']}% confidence, success: {result['success']}")
                    
                    # Add delay between requests to be respectful
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Service failed: {e}")
            
            # Clean up temp file
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
            
            page_results.append(page_result)
            
            logger.info(f"Page {page_num} - Best: {page_result['best_service']}, "
                       f"Confidence: {page_result['best_confidence']:.1f}%, "
                       f"Text: {len(page_result['best_text'])} chars")
        
        self.results = page_results
        return page_results
    
    def save_results(self, output_dir: str = "Outputs") -> dict:
        """Save results."""
        logger.info(f"Saving results to {output_dir}")
        
        # Create timestamp-based directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamp_dir = os.path.join(output_dir, timestamp)
        os.makedirs(timestamp_dir, exist_ok=True)
        
        saved_files = {}
        
        # Save combined results
        combined_txt_path = os.path.join(timestamp_dir, "online_ocr_results.txt")
        with open(combined_txt_path, 'w', encoding='utf-8') as f:
            f.write("Online OCR Telugu Extraction Results\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Total Pages: {len(self.results)}\n")
            f.write("="*60 + "\n\n")
            
            for page in self.results:
                f.write(f"=== Page {page['page_number']} ===\n")
                f.write(f"Best Service: {page['best_service']}\n")
                f.write(f"Confidence: {page['best_confidence']:.1f}%\n")
                f.write(f"Text Length: {len(page['best_text'])} characters\n\n")
                f.write("EXTRACTED TEXT:\n")
                f.write(page['best_text'])
                f.write("\n\n" + "="*50 + "\n\n")
        
        saved_files["combined_txt"] = combined_txt_path
        
        # Save detailed JSON
        json_path = os.path.join(timestamp_dir, "online_ocr_detailed.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        saved_files["detailed_json"] = json_path
        
        logger.info(f"Results saved to: {timestamp_dir}")
        return saved_files

def main():
    """Main function."""
    pdf_path = "/Users/ravikiranponduri/Desktop/consultingprojects/research/manuscript_Reader/test_manu.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        sys.exit(1)
    
    print("🌐 Online OCR Telugu Extractor")
    print("=" * 50)
    print(f"Processing: {pdf_path}")
    print("Note: This will process first 3 pages only to avoid API limits")
    print()
    
    try:
        # Initialize extractor
        extractor = OnlineOCRExtractor()
        
        # Process PDF
        print("Processing PDF with online OCR services...")
        results = extractor.process_pdf(pdf_path, max_pages=3)
        
        # Save results
        print("Saving results...")
        saved_files = extractor.save_results("Outputs")
        
        # Print summary
        print("\n" + "="*60)
        print("✅ ONLINE OCR EXTRACTION COMPLETE!")
        print("="*60)
        
        total_text_length = sum(len(page['best_text']) for page in results)
        avg_confidence = sum(page['best_confidence'] for page in results) / len(results)
        
        print(f"📄 Total pages processed: {len(results)}")
        print(f"📝 Total text extracted: {total_text_length} characters")
        print(f"🎯 Average confidence: {avg_confidence:.1f}%")
        
        print(f"\n📁 Output files:")
        for file_type, file_path in saved_files.items():
            print(f"   {file_type.upper()}: {file_path}")
        
        # Show results per page
        print(f"\n📖 Results per page:")
        for page in results:
            print(f"   Page {page['page_number']}: {page['best_service']} - "
                  f"{page['best_confidence']:.1f}% - {len(page['best_text'])} chars")
        
        # Show sample text
        if results and results[0]['best_text']:
            print(f"\n📝 Sample extracted text (Page 1):")
            print("-" * 40)
            sample_text = results[0]['best_text'][:300]
            print(sample_text)
            if len(results[0]['best_text']) > 300:
                print("...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
