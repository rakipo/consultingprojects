#!/usr/bin/env python3
"""
Example usage of the Telugu Document OCR System.

This script demonstrates how to use the Telugu OCR system programmatically.
"""

import sys
from pathlib import Path
from telugu_ocr.core.telugu_ocr_system import TeluguOCRSystem


def basic_usage_example():
    """Basic usage example with default settings."""
    print("=== Basic Usage Example ===")
    
    # Initialize the OCR system with default settings
    ocr_system = TeluguOCRSystem()
    
    # Check system status
    status = ocr_system.get_system_status()
    print(f"Available engines: {status['available_engines']}")
    print(f"Enabled engines: {status['enabled_engines']}")
    
    # Process a PDF document (replace with your PDF path)
    pdf_path = "test_manu.pdf"  # Your PDF file
    
    if Path(pdf_path).exists():
        print(f"\nProcessing PDF: {pdf_path}")
        
        # Process the document
        results = ocr_system.process_pdf(pdf_path)
        
        if results['success']:
            print(f"✓ Processing completed successfully!")
            print(f"  Output directory: {results['output_directory']}")
            print(f"  Processing time: {results['processing_time']:.2f} seconds")
            print(f"  Pages processed: {results['pages_processed']}")
            print(f"  Engines used: {', '.join(results['engines_used'])}")
            
            # Show summary statistics
            stats = results['summary_stats']
            print(f"  Average confidence: {stats['average_confidence']:.3f}")
            if stats['best_engine']:
                print(f"  Best performing engine: {stats['best_engine']}")
        else:
            print(f"✗ Processing failed: {results['error']}")
    else:
        print(f"PDF file not found: {pdf_path}")
        print("Please place a Telugu PDF file named 'test_manu.pdf' in the current directory")


def advanced_usage_example():
    """Advanced usage example with custom settings."""
    print("\n=== Advanced Usage Example ===")
    
    # Initialize with custom settings
    ocr_system = TeluguOCRSystem(
        config_dir="config",
        output_dir="custom_output",
        enable_preprocessing=True,
        debug_mode=True
    )
    
    pdf_path = "test_manu.pdf"
    
    if Path(pdf_path).exists():
        # Process with specific engines only
        specific_engines = ['tesseract', 'easyocr']  # Use only these engines
        
        print(f"Processing with specific engines: {specific_engines}")
        
        results = ocr_system.process_pdf(pdf_path, specific_engines=specific_engines)
        
        if results['success']:
            print("✓ Advanced processing completed!")
            
            # Show detailed results for each engine
            for engine_name, engine_results in results['engine_results'].items():
                if engine_results:
                    avg_confidence = sum(r.confidence_score for r in engine_results) / len(engine_results)
                    total_chars = sum(len(r.text) for r in engine_results)
                    print(f"  {engine_name}:")
                    print(f"    - Average confidence: {avg_confidence:.3f}")
                    print(f"    - Total characters: {total_chars}")
            
            # Show quality reports
            if results['quality_reports']:
                print("\n  Quality Assessment:")
                for engine_name, quality_report in results['quality_reports'].items():
                    print(f"    {engine_name}:")
                    print(f"      - Overall score: {quality_report.overall_score:.3f}")
                    print(f"      - Telugu detection: {quality_report.telugu_detection_rate:.3f}")
                    if quality_report.recommendations:
                        print(f"      - Top recommendation: {quality_report.recommendations[0]}")
        else:
            print(f"✗ Advanced processing failed: {results['error']}")


def engine_testing_example():
    """Example of testing OCR engines."""
    print("\n=== Engine Testing Example ===")
    
    ocr_system = TeluguOCRSystem()
    
    # Get setup instructions for all engines
    setup_instructions = ocr_system.get_engine_setup_instructions()
    
    print("Setup instructions for OCR engines:")
    for engine_name, instructions in setup_instructions.items():
        print(f"\n{engine_name.upper()}:")
        print(instructions[:200] + "..." if len(instructions) > 200 else instructions)


def evaluation_example():
    """Example of using the evaluation system."""
    print("\n=== Evaluation Example ===")
    
    from telugu_ocr.quality.evaluation_manager import EvaluationManager
    
    # Initialize evaluation manager
    eval_manager = EvaluationManager()
    
    # Create feedback questions template
    template_path = eval_manager.create_feedback_questions_template()
    print(f"Created feedback template: {template_path}")
    
    print("Use this template to provide feedback on OCR results.")
    print("After processing a document, you can:")
    print("1. Fill out the evaluation CSV generated in the output directory")
    print("2. Use the feedback template to provide detailed feedback")
    print("3. Process the feedback to improve future OCR accuracy")


def context_manager_example():
    """Example using context manager for automatic cleanup."""
    print("\n=== Context Manager Example ===")
    
    pdf_path = "test_manu.pdf"
    
    if Path(pdf_path).exists():
        # Use context manager for automatic cleanup
        with TeluguOCRSystem(debug_mode=True) as ocr_system:
            print("Processing with automatic cleanup...")
            results = ocr_system.process_pdf(pdf_path)
            
            if results['success']:
                print("✓ Processing completed with automatic cleanup")
            else:
                print(f"✗ Processing failed: {results['error']}")
        
        print("System automatically cleaned up resources")
    else:
        print(f"PDF file not found: {pdf_path}")


def main():
    """Run all examples."""
    print("Telugu Document OCR System - Usage Examples")
    print("=" * 50)
    
    try:
        # Run examples
        basic_usage_example()
        advanced_usage_example()
        engine_testing_example()
        evaluation_example()
        context_manager_example()
        
        print("\n" + "=" * 50)
        print("Examples completed successfully!")
        print("\nNext steps:")
        print("1. Place your Telugu PDF files in the current directory")
        print("2. Run: python example_usage.py")
        print("3. Check the output directory for results")
        print("4. Use the evaluation forms to provide feedback")
        print("5. Generate comparison reports for multiple documents")
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please install the required dependencies:")
        print("pip install -r requirements.txt")
        return 1
    
    except Exception as e:
        print(f"Error running examples: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())