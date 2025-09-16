#!/usr/bin/env python3
"""
Simple script to run Telugu manuscript extraction on the test PDF.
"""

import os
import sys
from datetime import datetime
from telugu_manuscript_reader import TeluguManuscriptReader

def main():
    """Run extraction on the test manuscript."""
    
    # Path to the test PDF
    pdf_path = "/Users/ravikiranponduri/Desktop/consultingprojects/research/manuscript_Reader/test_manu.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        sys.exit(1)
    
    print("🔍 Telugu Manuscript Reader")
    print("=" * 50)
    print(f"Processing: {pdf_path}")
    print()
    
    # Configuration for better results with handwritten text
    config = {
        "dpi": 300,
        "preprocessing": {
            "denoise": True,
            "enhance_contrast": True,
            "enhance_sharpness": True,
            "binarize": True
        },
        "ocr_methods": ["tesseract"],  # Start with Tesseract only
        "output_formats": ["txt", "pdf", "json"],
        "confidence_threshold": 50  # Lower threshold for handwritten text
    }
    
    try:
        # Initialize reader
        print("Initializing Telugu Manuscript Reader...")
        reader = TeluguManuscriptReader(config)
        
        # Process PDF
        print("Converting PDF to images and extracting text...")
        results = reader.process_pdf(pdf_path)
        
        # Save results
        print("Saving results...")
        saved_files = reader.save_results("Outputs")
        
        # Print summary
        print("\n" + "="*60)
        print("✅ EXTRACTION COMPLETE!")
        print("="*60)
        print(f"📄 Total pages processed: {len(results)}")
        
        total_text_length = sum(len(page['best_text']) for page in results)
        avg_confidence = sum(page['best_confidence'] for page in results) / len(results)
        
        print(f"📝 Total text extracted: {total_text_length} characters")
        print(f"🎯 Average confidence: {avg_confidence:.1f}%")
        print(f"📁 Output files (organized by method):")
        for format_type, file_path in saved_files.items():
            print(f"   {format_type.upper()}: {file_path}")
        
        # Show folder structure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"\n📂 Folder structure:")
        print(f"   Outputs/{timestamp}/")
        methods_used = set(page['best_method'] for page in results if page['best_method'])
        for method in methods_used:
            print(f"   ├── {method}/")
            print(f"   │   ├── telugu_extraction_{method}.json")
            print(f"   │   ├── telugu_extraction_{method}.txt")
            print(f"   │   └── telugu_extraction_{method}.pdf")
        print(f"   ├── extraction_summary.json")
        print(f"   └── combined_extraction.txt")
        
        # Show sample of extracted text
        print(f"\n📖 Sample extracted text (Page 1):")
        print("-" * 40)
        if results and results[0]['best_text']:
            sample_text = results[0]['best_text'][:200]
            print(sample_text)
            if len(results[0]['best_text']) > 200:
                print("...")
        else:
            print("No text extracted from first page")
        
        print(f"\n💡 Tips for better results:")
        print("   - Ensure the PDF has good quality scans")
        print("   - For handwritten text, try different preprocessing settings")
        print("   - Check the debug images in the current directory")
        print("   - Consider using Google Cloud Vision API for better accuracy")
        
    except Exception as e:
        print(f"❌ Error processing PDF: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
