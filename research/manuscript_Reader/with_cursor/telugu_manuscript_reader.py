#!/usr/bin/env python3
"""
Telugu Manuscript Reader
A comprehensive tool to extract Telugu text from scanned PDF manuscripts using multiple OCR methods.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json
from datetime import datetime

# Image processing and PDF handling
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from pdf2image import convert_from_path

# Google Cloud Vision (optional)
try:
    from google.cloud import vision
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False
    print("Google Cloud Vision not available. Install with: pip install google-cloud-vision")

# Document generation
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telugu_ocr.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TeluguManuscriptReader:
    """Main class for extracting Telugu text from manuscript PDFs."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the manuscript reader with configuration."""
        self.config = config or self._get_default_config()
        self.extracted_text = []
        self.page_results = []
        
        # Set up Tesseract path if needed
        if sys.platform == "darwin":  # macOS
            tesseract_path = "/opt/homebrew/bin/tesseract"
            if os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        logger.info("Telugu Manuscript Reader initialized")
    
    def _get_default_config(self) -> Dict:
        """Get default configuration settings."""
        return {
            "dpi": 300,
            "preprocessing": {
                "denoise": True,
                "enhance_contrast": True,
                "enhance_sharpness": True,
                "binarize": True
            },
            "ocr_methods": ["tesseract", "google_vision"],
            "output_formats": ["txt", "pdf", "json"],
            "confidence_threshold": 60
        }
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results."""
        logger.info("Preprocessing image for OCR")
        
        # Convert to numpy array for OpenCV processing
        img_array = np.array(image)
        
        # Convert to grayscale if needed
        if len(img_array.shape) == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Denoise
        if self.config["preprocessing"]["denoise"]:
            img_array = cv2.fastNlMeansDenoising(img_array)
        
        # Enhance contrast
        if self.config["preprocessing"]["enhance_contrast"]:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            img_array = clahe.apply(img_array)
        
        # Enhance sharpness
        if self.config["preprocessing"]["enhance_sharpness"]:
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            img_array = cv2.filter2D(img_array, -1, kernel)
        
        # Binarize (convert to black and white)
        if self.config["preprocessing"]["binarize"]:
            _, img_array = cv2.threshold(img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Convert back to PIL Image
        processed_image = Image.fromarray(img_array)
        
        # Additional PIL enhancements
        if self.config["preprocessing"]["enhance_contrast"]:
            enhancer = ImageEnhance.Contrast(processed_image)
            processed_image = enhancer.enhance(1.2)
        
        return processed_image
    
    def extract_text_tesseract(self, image: Image.Image) -> Tuple[str, float]:
        """Extract text using Tesseract OCR with Telugu language support."""
        logger.info("Extracting text using Tesseract OCR")
        
        try:
            # Configure Tesseract for Telugu
            custom_config = r'--oem 3 --psm 6 -l tel+eng'
            
            # Get detailed data including confidence
            data = pytesseract.image_to_data(image, config=custom_config, output_type=pytesseract.Output.DICT)
            
            # Extract text and calculate average confidence
            text_parts = []
            confidences = []
            
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 0:  # Only include text with confidence > 0
                    text_parts.append(data['text'][i])
                    confidences.append(int(data['conf'][i]))
            
            extracted_text = ' '.join(text_parts).strip()
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            logger.info(f"Tesseract extracted {len(extracted_text)} characters with {avg_confidence:.1f}% confidence")
            return extracted_text, avg_confidence
            
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            return "", 0
    
    def extract_text_google_vision(self, image: Image.Image) -> Tuple[str, float]:
        """Extract text using Google Cloud Vision API."""
        if not GOOGLE_VISION_AVAILABLE:
            logger.warning("Google Cloud Vision not available")
            return "", 0
        
        logger.info("Extracting text using Google Cloud Vision API")
        
        try:
            # Convert PIL image to bytes
            import io
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Initialize Google Vision client
            client = vision.ImageAnnotatorClient()
            image_vision = vision.Image(content=img_byte_arr)
            
            # Perform text detection
            response = client.document_text_detection(image=image_vision)
            
            if response.error.message:
                logger.error(f"Google Vision API error: {response.error.message}")
                return "", 0
            
            # Extract text and confidence
            extracted_text = response.full_text_annotation.text if response.full_text_annotation else ""
            
            # Calculate average confidence
            confidences = []
            for page in response.full_text_annotation.pages:
                for block in page.blocks:
                    for paragraph in block.paragraphs:
                        for word in paragraph.words:
                            confidences.append(word.property.detected_break.confidence)
            
            avg_confidence = sum(confidences) / len(confidences) if confidences else 100
            
            logger.info(f"Google Vision extracted {len(extracted_text)} characters with {avg_confidence:.1f}% confidence")
            return extracted_text, avg_confidence
            
        except Exception as e:
            logger.error(f"Google Vision OCR failed: {e}")
            return "", 0
    
    def process_pdf(self, pdf_path: str) -> List[Dict]:
        """Process PDF file and extract text from all pages."""
        logger.info(f"Processing PDF: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Convert PDF to images
        logger.info("Converting PDF pages to images")
        try:
            images = convert_from_path(
                pdf_path, 
                dpi=self.config["dpi"],
                first_page=1,
                last_page=None
            )
        except Exception as e:
            logger.error(f"Failed to convert PDF to images: {e}")
            raise
        
        logger.info(f"Converted {len(images)} pages to images")
        
        page_results = []
        
        for page_num, image in enumerate(images, 1):
            logger.info(f"Processing page {page_num}/{len(images)}")
            
            # Preprocess image
            processed_image = self.preprocess_image(image)
            
            # Save processed image for debugging
            debug_path = f"debug_page_{page_num:03d}.png"
            processed_image.save(debug_path)
            logger.info(f"Saved debug image: {debug_path}")
            
            page_result = {
                "page_number": page_num,
                "methods": {},
                "best_text": "",
                "best_confidence": 0,
                "best_method": ""
            }
            
            # Try different OCR methods
            for method in self.config["ocr_methods"]:
                if method == "tesseract":
                    text, confidence = self.extract_text_tesseract(processed_image)
                    page_result["methods"]["tesseract"] = {
                        "text": text,
                        "confidence": confidence
                    }
                elif method == "google_vision":
                    text, confidence = self.extract_text_google_vision(processed_image)
                    page_result["methods"]["google_vision"] = {
                        "text": text,
                        "confidence": confidence
                    }
            
            # Select best result based on confidence
            best_method = ""
            best_confidence = 0
            best_text = ""
            
            for method, result in page_result["methods"].items():
                if result["confidence"] > best_confidence:
                    best_confidence = result["confidence"]
                    best_text = result["text"]
                    best_method = method
            
            page_result["best_text"] = best_text
            page_result["best_confidence"] = best_confidence
            page_result["best_method"] = best_method
            
            page_results.append(page_result)
            
            logger.info(f"Page {page_num} - Best method: {best_method}, Confidence: {best_confidence:.1f}%, Text length: {len(best_text)}")
        
        self.page_results = page_results
        return page_results
    
    def save_results(self, output_dir: str = "Outputs") -> Dict[str, str]:
        """Save extracted text in multiple formats with structured folder organization."""
        logger.info(f"Saving results to {output_dir}")
        
        # Create timestamp-based directory structure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamp_dir = os.path.join(output_dir, timestamp)
        os.makedirs(timestamp_dir, exist_ok=True)
        
        saved_files = {}
        
        # Group results by method used
        methods_used = set()
        for page in self.page_results:
            if page['best_method']:
                methods_used.add(page['best_method'])
        
        # If no method was used, create a default folder
        if not methods_used:
            methods_used = {'unknown'}
        
        # Save results for each method used
        for method in methods_used:
            method_dir = os.path.join(timestamp_dir, method)
            os.makedirs(method_dir, exist_ok=True)
            
            # Filter pages for this method
            method_pages = [page for page in self.page_results if page['best_method'] == method]
            
            if method_pages:
                # Save as JSON for this method
                json_path = os.path.join(method_dir, f"telugu_extraction_{method}.json")
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(method_pages, f, ensure_ascii=False, indent=2)
                saved_files[f"{method}_json"] = json_path
                
                # Save as plain text for this method
                txt_path = os.path.join(method_dir, f"telugu_extraction_{method}.txt")
                with open(txt_path, 'w', encoding='utf-8') as f:
                    for page in method_pages:
                        f.write(f"=== Page {page['page_number']} ===\n")
                        f.write(f"Method: {page['best_method']}, Confidence: {page['best_confidence']:.1f}%\n\n")
                        f.write(page['best_text'])
                        f.write("\n\n" + "="*50 + "\n\n")
                saved_files[f"{method}_txt"] = txt_path
                
                # Save as PDF for this method
                pdf_path = os.path.join(method_dir, f"telugu_extraction_{method}.pdf")
                self._create_telugu_pdf(pdf_path, method_pages)
                saved_files[f"{method}_pdf"] = pdf_path
        
        # Also save a combined summary file in the timestamp directory
        summary_path = os.path.join(timestamp_dir, "extraction_summary.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            summary_data = {
                "timestamp": timestamp,
                "total_pages": len(self.page_results),
                "methods_used": list(methods_used),
                "page_results": self.page_results
            }
            json.dump(summary_data, f, ensure_ascii=False, indent=2)
        saved_files["summary"] = summary_path
        
        # Save combined text file
        combined_txt_path = os.path.join(timestamp_dir, "combined_extraction.txt")
        with open(combined_txt_path, 'w', encoding='utf-8') as f:
            f.write(f"Telugu Manuscript Extraction Results\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Total Pages: {len(self.page_results)}\n")
            f.write(f"Methods Used: {', '.join(methods_used)}\n")
            f.write("="*60 + "\n\n")
            
            for page in self.page_results:
                f.write(f"=== Page {page['page_number']} ===\n")
                f.write(f"Method: {page['best_method']}, Confidence: {page['best_confidence']:.1f}%\n\n")
                f.write(page['best_text'])
                f.write("\n\n" + "="*50 + "\n\n")
        saved_files["combined_txt"] = combined_txt_path
        
        logger.info(f"Results saved to: {timestamp_dir}")
        logger.info(f"Methods used: {', '.join(methods_used)}")
        return saved_files
    
    def _create_telugu_pdf(self, output_path: str, pages_data: List[Dict] = None):
        """Create a PDF with extracted Telugu text."""
        if pages_data is None:
            pages_data = self.page_results
            
        try:
            # Try to register a Telugu font
            telugu_font_paths = [
                "/System/Library/Fonts/Supplemental/NotoSansTelugu-Regular.ttf",
                "/System/Library/Fonts/Supplemental/NotoSansTelugu-Bold.ttf",
                "/usr/share/fonts/truetype/noto/NotoSansTelugu-Regular.ttf"
            ]
            
            telugu_font = None
            for font_path in telugu_font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('Telugu', font_path))
                        telugu_font = 'Telugu'
                        break
                    except:
                        continue
            
            # Create PDF document
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            styles = getSampleStyleSheet()
            
            # Create custom style for Telugu text
            if telugu_font:
                telugu_style = ParagraphStyle(
                    'TeluguStyle',
                    parent=styles['Normal'],
                    fontName=telugu_font,
                    fontSize=12,
                    leading=16
                )
            else:
                telugu_style = styles['Normal']
                logger.warning("Telugu font not found, using default font")
            
            # Build content
            content = []
            
            for page in pages_data:
                # Add page header
                content.append(Paragraph(f"Page {page['page_number']}", styles['Heading2']))
                content.append(Paragraph(f"Method: {page['best_method']} | Confidence: {page['best_confidence']:.1f}%", styles['Normal']))
                content.append(Spacer(1, 12))
                
                # Add extracted text
                if page['best_text'].strip():
                    content.append(Paragraph(page['best_text'], telugu_style))
                else:
                    content.append(Paragraph("No text extracted", styles['Normal']))
                
                content.append(Spacer(1, 20))
            
            # Build PDF
            doc.build(content)
            logger.info(f"Telugu PDF created: {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to create Telugu PDF: {e}")
            # Create a simple text-based PDF as fallback
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            styles = getSampleStyleSheet()
            content = []
            
            for page in pages_data:
                content.append(Paragraph(f"Page {page['page_number']}", styles['Heading2']))
                content.append(Paragraph(page['best_text'], styles['Normal']))
                content.append(Spacer(1, 20))
            
            doc.build(content)

def main():
    """Main function to run the Telugu manuscript reader."""
    parser = argparse.ArgumentParser(description="Extract Telugu text from manuscript PDFs")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("-o", "--output", default="Outputs", help="Output directory")
    parser.add_argument("-d", "--dpi", type=int, default=300, help="DPI for PDF conversion")
    parser.add_argument("--methods", nargs="+", choices=["tesseract", "google_vision"], 
                       default=["tesseract"], help="OCR methods to use")
    parser.add_argument("--no-preprocessing", action="store_true", 
                       help="Skip image preprocessing")
    
    args = parser.parse_args()
    
    # Create configuration
    config = {
        "dpi": args.dpi,
        "preprocessing": {
            "denoise": not args.no_preprocessing,
            "enhance_contrast": not args.no_preprocessing,
            "enhance_sharpness": not args.no_preprocessing,
            "binarize": not args.no_preprocessing
        },
        "ocr_methods": args.methods,
        "output_formats": ["txt", "pdf", "json"],
        "confidence_threshold": 60
    }
    
    try:
        # Initialize reader
        reader = TeluguManuscriptReader(config)
        
        # Process PDF
        results = reader.process_pdf(args.pdf_path)
        
        # Save results
        saved_files = reader.save_results(args.output)
        
        # Print summary
        print("\n" + "="*60)
        print("TELUGU MANUSCRIPT EXTRACTION COMPLETE")
        print("="*60)
        print(f"Total pages processed: {len(results)}")
        
        total_text_length = sum(len(page['best_text']) for page in results)
        avg_confidence = sum(page['best_confidence'] for page in results) / len(results)
        
        print(f"Total text extracted: {total_text_length} characters")
        print(f"Average confidence: {avg_confidence:.1f}%")
        print(f"Output files:")
        for format_type, file_path in saved_files.items():
            print(f"  {format_type.upper()}: {file_path}")
        
        print("\nTo activate the conda environment in the future, run:")
        print("conda activate manuscript_reader")
        
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
