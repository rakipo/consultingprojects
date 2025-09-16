#!/usr/bin/env python3
"""
Advanced Telugu Manuscript Extractor
Uses multiple methods and preprocessing techniques for better Telugu text recognition.
"""

import os
import sys
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import pytesseract
from pdf2image import convert_from_path
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedTeluguExtractor:
    """Advanced Telugu text extractor with multiple preprocessing and OCR methods."""
    
    def __init__(self):
        """Initialize the extractor."""
        self.results = []
        
        # Set up Tesseract path for macOS
        if sys.platform == "darwin":
            tesseract_path = "/opt/homebrew/bin/tesseract"
            if os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        logger.info("Advanced Telugu Extractor initialized")
    
    def preprocess_image_advanced(self, image: Image.Image, method: str = "enhanced") -> Image.Image:
        """Advanced image preprocessing for better OCR results."""
        logger.info(f"Applying {method} preprocessing")
        
        # Convert to numpy array
        img_array = np.array(image)
        
        # Convert to grayscale if needed
        if len(img_array.shape) == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        if method == "enhanced":
            # Enhanced preprocessing
            # 1. Denoise
            img_array = cv2.fastNlMeansDenoising(img_array, h=10)
            
            # 2. Enhance contrast using CLAHE
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            img_array = clahe.apply(img_array)
            
            # 3. Morphological operations to clean up text
            kernel = np.ones((2,2), np.uint8)
            img_array = cv2.morphologyEx(img_array, cv2.MORPH_CLOSE, kernel)
            
            # 4. Gaussian blur to smooth
            img_array = cv2.GaussianBlur(img_array, (1,1), 0)
            
            # 5. Adaptive thresholding
            img_array = cv2.adaptiveThreshold(img_array, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                            cv2.THRESH_BINARY, 11, 2)
        
        elif method == "aggressive":
            # Aggressive preprocessing for poor quality images
            # 1. Resize for better processing
            height, width = img_array.shape
            if height < 1000:
                scale = 1000 / height
                new_width = int(width * scale)
                img_array = cv2.resize(img_array, (new_width, 1000), interpolation=cv2.INTER_CUBIC)
            
            # 2. Denoise
            img_array = cv2.fastNlMeansDenoising(img_array, h=15)
            
            # 3. Enhance contrast
            clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8,8))
            img_array = clahe.apply(img_array)
            
            # 4. Sharpen
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            img_array = cv2.filter2D(img_array, -1, kernel)
            
            # 5. Binarize
            _, img_array = cv2.threshold(img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        elif method == "conservative":
            # Conservative preprocessing to preserve original text
            # 1. Light denoising
            img_array = cv2.fastNlMeansDenoising(img_array, h=5)
            
            # 2. Light contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            img_array = clahe.apply(img_array)
        
        # Convert back to PIL Image
        processed_image = Image.fromarray(img_array)
        
        # Additional PIL enhancements
        if method in ["enhanced", "aggressive"]:
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(processed_image)
            processed_image = enhancer.enhance(1.3)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(processed_image)
            processed_image = enhancer.enhance(1.2)
        
        return processed_image
    
    def extract_with_tesseract_variants(self, image: Image.Image) -> dict:
        """Extract text using different Tesseract configurations."""
        results = {}
        
        # Different Tesseract configurations
        configs = {
            "telugu_only": "-l tel --oem 3 --psm 6",
            "telugu_eng": "-l tel+eng --oem 3 --psm 6", 
            "telugu_psm3": "-l tel --oem 3 --psm 3",
            "telugu_psm4": "-l tel --oem 3 --psm 4",
            "telugu_psm8": "-l tel --oem 3 --psm 8",
            "telugu_psm13": "-l tel --oem 3 --psm 13"
        }
        
        for config_name, config in configs.items():
            try:
                logger.info(f"Trying Tesseract config: {config_name}")
                
                # Get text and confidence
                data = pytesseract.image_to_data(image, config=config, output_type=pytesseract.Output.DICT)
                
                # Extract text and calculate confidence
                text_parts = []
                confidences = []
                
                for i in range(len(data['text'])):
                    if int(data['conf'][i]) > 0:
                        text_parts.append(data['text'][i])
                        confidences.append(int(data['conf'][i]))
                
                extracted_text = ' '.join(text_parts).strip()
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                
                results[config_name] = {
                    "text": extracted_text,
                    "confidence": avg_confidence,
                    "text_length": len(extracted_text)
                }
                
                logger.info(f"{config_name}: {len(extracted_text)} chars, {avg_confidence:.1f}% confidence")
                
            except Exception as e:
                logger.error(f"Tesseract config {config_name} failed: {e}")
                results[config_name] = {"text": "", "confidence": 0, "text_length": 0}
        
        return results
    
    def extract_with_preprocessing_variants(self, original_image: Image.Image) -> dict:
        """Extract text using different preprocessing methods."""
        results = {}
        
        preprocessing_methods = ["enhanced", "aggressive", "conservative"]
        
        for method in preprocessing_methods:
            try:
                logger.info(f"Trying preprocessing method: {method}")
                
                # Apply preprocessing
                processed_image = self.preprocess_image_advanced(original_image, method)
                
                # Save debug image
                debug_path = f"debug_{method}_page_{len(self.results)+1:03d}.png"
                processed_image.save(debug_path)
                logger.info(f"Saved debug image: {debug_path}")
                
                # Extract with best Tesseract config
                tesseract_results = self.extract_with_tesseract_variants(processed_image)
                
                # Find best result from this preprocessing
                best_config = max(tesseract_results.items(), key=lambda x: x[1]['confidence'])
                
                results[method] = {
                    "best_config": best_config[0],
                    "text": best_config[1]['text'],
                    "confidence": best_config[1]['confidence'],
                    "text_length": best_config[1]['text_length'],
                    "all_configs": tesseract_results
                }
                
                logger.info(f"{method}: {best_config[1]['text_length']} chars, {best_config[1]['confidence']:.1f}% confidence")
                
            except Exception as e:
                logger.error(f"Preprocessing method {method} failed: {e}")
                results[method] = {"text": "", "confidence": 0, "text_length": 0}
        
        return results
    
    def process_pdf(self, pdf_path: str) -> list:
        """Process PDF and extract text using multiple methods."""
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
            
            # Try different preprocessing methods
            preprocessing_results = self.extract_with_preprocessing_variants(image)
            
            # Find the best overall result
            best_method = ""
            best_confidence = 0
            best_text = ""
            best_config = ""
            
            for method, result in preprocessing_results.items():
                if result['confidence'] > best_confidence:
                    best_confidence = result['confidence']
                    best_text = result['text']
                    best_method = method
                    best_config = result.get('best_config', '')
            
            page_result = {
                "page_number": page_num,
                "best_method": best_method,
                "best_config": best_config,
                "best_text": best_text,
                "best_confidence": best_confidence,
                "all_methods": preprocessing_results
            }
            
            page_results.append(page_result)
            
            logger.info(f"Page {page_num} - Best: {best_method} ({best_config}), "
                       f"Confidence: {best_confidence:.1f}%, Text: {len(best_text)} chars")
        
        self.results = page_results
        return page_results
    
    def save_results(self, output_dir: str = "Outputs") -> dict:
        """Save results in organized folder structure."""
        logger.info(f"Saving results to {output_dir}")
        
        # Create timestamp-based directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamp_dir = os.path.join(output_dir, timestamp)
        os.makedirs(timestamp_dir, exist_ok=True)
        
        saved_files = {}
        
        # Save combined results
        combined_txt_path = os.path.join(timestamp_dir, "telugu_extraction_combined.txt")
        with open(combined_txt_path, 'w', encoding='utf-8') as f:
            f.write("Telugu Manuscript Extraction Results\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Total Pages: {len(self.results)}\n")
            f.write("="*60 + "\n\n")
            
            for page in self.results:
                f.write(f"=== Page {page['page_number']} ===\n")
                f.write(f"Best Method: {page['best_method']}\n")
                f.write(f"Best Config: {page['best_config']}\n")
                f.write(f"Confidence: {page['best_confidence']:.1f}%\n")
                f.write(f"Text Length: {len(page['best_text'])} characters\n\n")
                f.write("EXTRACTED TEXT:\n")
                f.write(page['best_text'])
                f.write("\n\n" + "="*50 + "\n\n")
        
        saved_files["combined_txt"] = combined_txt_path
        
        # Save detailed JSON results
        json_path = os.path.join(timestamp_dir, "detailed_results.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        saved_files["detailed_json"] = json_path
        
        # Save summary
        summary_path = os.path.join(timestamp_dir, "extraction_summary.txt")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("EXTRACTION SUMMARY\n")
            f.write("="*40 + "\n\n")
            
            total_text_length = sum(len(page['best_text']) for page in self.results)
            avg_confidence = sum(page['best_confidence'] for page in self.results) / len(self.results)
            
            f.write(f"Total Pages: {len(self.results)}\n")
            f.write(f"Total Text Extracted: {total_text_length} characters\n")
            f.write(f"Average Confidence: {avg_confidence:.1f}%\n\n")
            
            f.write("Page-by-Page Summary:\n")
            f.write("-" * 40 + "\n")
            for page in self.results:
                f.write(f"Page {page['page_number']}: {page['best_method']} "
                       f"({page['best_config']}) - {page['best_confidence']:.1f}% - "
                       f"{len(page['best_text'])} chars\n")
        
        saved_files["summary"] = summary_path
        
        logger.info(f"Results saved to: {timestamp_dir}")
        return saved_files

def main():
    """Main function to run the advanced Telugu extractor."""
    pdf_path = "/Users/ravikiranponduri/Desktop/consultingprojects/research/manuscript_Reader/test_manu.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        sys.exit(1)
    
    print("🔍 Advanced Telugu Manuscript Extractor")
    print("=" * 50)
    print(f"Processing: {pdf_path}")
    print()
    
    try:
        # Initialize extractor
        extractor = AdvancedTeluguExtractor()
        
        # Process PDF
        print("Processing PDF with multiple methods...")
        results = extractor.process_pdf(pdf_path)
        
        # Save results
        print("Saving results...")
        saved_files = extractor.save_results("Outputs")
        
        # Print summary
        print("\n" + "="*60)
        print("✅ EXTRACTION COMPLETE!")
        print("="*60)
        
        total_text_length = sum(len(page['best_text']) for page in results)
        avg_confidence = sum(page['best_confidence'] for page in results) / len(results)
        
        print(f"📄 Total pages processed: {len(results)}")
        print(f"📝 Total text extracted: {total_text_length} characters")
        print(f"🎯 Average confidence: {avg_confidence:.1f}%")
        
        print(f"\n📁 Output files:")
        for file_type, file_path in saved_files.items():
            print(f"   {file_type.upper()}: {file_path}")
        
        # Show best results per page
        print(f"\n📖 Best results per page:")
        for page in results:
            print(f"   Page {page['page_number']}: {page['best_method']} "
                  f"({page['best_config']}) - {page['best_confidence']:.1f}% - "
                  f"{len(page['best_text'])} chars")
        
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
