"""Main application controller for Telugu OCR system."""

import argparse
import sys
import time
from pathlib import Path
from typing import List, Optional, Dict, Any

from .core.telugu_ocr_system import TeluguOCRSystem
from .utils.logging_config import get_logger_config
from .utils.exceptions import OCRException


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Telugu Document OCR System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m telugu_ocr process document.pdf
  python -m telugu_ocr process document.pdf --engines tesseract easyocr
  python -m telugu_ocr process document.pdf --output-dir custom_output
  python -m telugu_ocr evaluate document.pdf --create-forms
  python -m telugu_ocr report output/2024-01-15_14-30-25/
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process PDF document with OCR')
    process_parser.add_argument('pdf_path', help='Path to PDF file to process')
    process_parser.add_argument(
        '--engines', 
        nargs='+', 
        help='Specific OCR engines to use (default: all enabled engines)'
    )
    process_parser.add_argument(
        '--output-dir', 
        help='Custom output directory (default: output/)'
    )
    process_parser.add_argument(
        '--config-dir', 
        default='config',
        help='Configuration directory (default: config/)'
    )
    process_parser.add_argument(
        '--no-preprocessing', 
        action='store_true',
        help='Skip image preprocessing'
    )
    process_parser.add_argument(
        '--debug', 
        action='store_true',
        help='Enable debug mode with detailed logging'
    )
    
    # Evaluate command
    evaluate_parser = subparsers.add_parser('evaluate', help='Create evaluation forms')
    evaluate_parser.add_argument('pdf_path', help='Path to PDF file to evaluate')
    evaluate_parser.add_argument(
        '--create-forms', 
        action='store_true',
        help='Create manual evaluation forms'
    )
    evaluate_parser.add_argument(
        '--feedback-file', 
        help='Process existing feedback file'
    )
    evaluate_parser.add_argument(
        '--output-dir', 
        help='Custom output directory for evaluation files'
    )
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate comparison reports')
    report_parser.add_argument('results_dir', help='Directory containing OCR results')
    report_parser.add_argument(
        '--format', 
        choices=['html', 'text', 'both'], 
        default='both',
        help='Report format (default: both)'
    )
    report_parser.add_argument(
        '--output-dir', 
        help='Custom output directory for reports'
    )
    
    # List engines command
    list_parser = subparsers.add_parser('list-engines', help='List available OCR engines')
    list_parser.add_argument(
        '--config-dir', 
        default='config',
        help='Configuration directory (default: config/)'
    )
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test OCR engines')
    test_parser.add_argument(
        '--engines', 
        nargs='+', 
        help='Specific engines to test (default: all enabled)'
    )
    test_parser.add_argument(
        '--config-dir', 
        default='config',
        help='Configuration directory (default: config/)'
    )
    
    return parser


def process_command(args) -> int:
    """Handle process command."""
    try:
        # Initialize OCR system
        ocr_system = TeluguOCRSystem(
            config_dir=args.config_dir,
            output_dir=args.output_dir or "output",
            enable_preprocessing=not args.no_preprocessing,
            debug_mode=args.debug
        )
        
        # Validate input file
        pdf_path = Path(args.pdf_path)
        if not pdf_path.exists():
            print(f"Error: PDF file not found: {pdf_path}")
            return 1
        
        if pdf_path.suffix.lower() != '.pdf':
            print(f"Error: File is not a PDF: {pdf_path}")
            return 1
        
        print(f"Processing PDF: {pdf_path}")
        print(f"Output directory: {ocr_system.output_manager.base_output_dir}")
        
        # Show available engines
        available_engines = ocr_system.get_available_engines()
        if not available_engines:
            print("❌ No OCR engines are available!")
            print("💡 Install local engines (tesseract, easyocr) or configure API keys")
            return 1
        
        if args.engines:
            requested_engines = set(args.engines)
            available_set = set(available_engines)
            valid_engines = requested_engines & available_set
            invalid_engines = requested_engines - available_set
            
            if invalid_engines:
                print(f"⚠️  Requested engines not available: {', '.join(invalid_engines)}")
            if valid_engines:
                print(f"✅ Using engines: {', '.join(valid_engines)}")
            else:
                print("❌ None of the requested engines are available!")
                return 1
        else:
            local_engines = [e for e in available_engines if e in ['tesseract', 'easyocr', 'paddleocr', 'trocr']]
            api_engines = [e for e in available_engines if e not in ['tesseract', 'easyocr', 'paddleocr', 'trocr']]
            
            print(f"✅ Using all available engines ({len(available_engines)} total):")
            if local_engines:
                print(f"   📦 Local: {', '.join(local_engines)}")
            if api_engines:
                print(f"   🌐 API: {', '.join(api_engines)}")
            if not api_engines:
                print("   💡 Configure API keys in config/engines.yaml for cloud OCR engines")
        
        # Process the document
        start_time = time.time()
        results = ocr_system.process_pdf(
            str(pdf_path), 
            specific_engines=args.engines
        )
        processing_time = time.time() - start_time
        
        # Display results summary
        print(f"\nProcessing completed in {processing_time:.2f} seconds")
        print(f"Results saved to: {results['output_directory']}")
        print(f"Engines processed: {len(results['engine_results'])}")
        
        for engine_name, engine_results in results['engine_results'].items():
            if engine_results:
                avg_confidence = sum(r.confidence_score for r in engine_results) / len(engine_results)
                print(f"  {engine_name}: {len(engine_results)} pages, avg confidence: {avg_confidence:.3f}")
        
        if results.get('comparison_report'):
            print(f"Comparison report: {results['comparison_report']}")
        
        if results.get('performance_dashboard'):
            print(f"Performance dashboard: {results['performance_dashboard']}")
        
        return 0
        
    except OCRException as e:
        print(f"OCR Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


def evaluate_command(args) -> int:
    """Handle evaluate command."""
    try:
        from .quality.evaluation_manager import EvaluationManager
        
        evaluation_manager = EvaluationManager(
            output_dir=args.output_dir or "evaluation"
        )
        
        if args.create_forms:
            # Create evaluation forms for a PDF
            print(f"Creating evaluation forms for: {args.pdf_path}")
            
            # First process the PDF to get results
            ocr_system = TeluguOCRSystem()
            results = ocr_system.process_pdf(args.pdf_path)
            
            # Generate evaluation forms
            form_path = evaluation_manager.generate_evaluation_form(
                results['engine_results']
            )
            
            print(f"Evaluation form created: {form_path}")
            print("Please fill out the form and use --feedback-file to process it")
            
        elif args.feedback_file:
            # Process existing feedback file
            print(f"Processing feedback file: {args.feedback_file}")
            
            accuracy_reports = evaluation_manager.process_manual_feedback(args.feedback_file)
            
            # Update accuracy database
            db_path = evaluation_manager.update_engine_accuracy_scores(accuracy_reports)
            print(f"Accuracy database updated: {db_path}")
            
            # Generate summary
            summary_path = evaluation_manager.generate_evaluation_summary(accuracy_reports)
            print(f"Evaluation summary: {summary_path}")
            
        else:
            print("Please specify either --create-forms or --feedback-file")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"Evaluation error: {e}")
        return 1


def report_command(args) -> int:
    """Handle report command."""
    try:
        from .reporting.comparison_reporter import ComparisonReporter
        import json
        
        results_dir = Path(args.results_dir)
        if not results_dir.exists():
            print(f"Error: Results directory not found: {results_dir}")
            return 1
        
        # Load results from directory
        print(f"Loading results from: {results_dir}")
        
        # Look for comparison report and engine results
        comparison_file = results_dir / "comparison_report.json"
        if not comparison_file.exists():
            print(f"Error: No comparison report found in {results_dir}")
            return 1
        
        with open(comparison_file, 'r', encoding='utf-8') as f:
            comparison_data = json.load(f)
        
        # Initialize reporter
        reporter = ComparisonReporter(
            output_dir=args.output_dir or "reports"
        )
        
        print("Generating comparison reports...")
        
        # Generate reports based on format
        if args.format in ['html', 'both']:
            # This would need the actual results data structure
            # For now, create a basic HTML report
            html_path = reporter.output_dir / "comparison_report.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(f"""
<!DOCTYPE html>
<html>
<head><title>OCR Comparison Report</title></head>
<body>
<h1>OCR Comparison Report</h1>
<p>Generated from: {results_dir}</p>
<p>Best performing engine: {comparison_data.get('best_performing_engine', 'Unknown')}</p>
<pre>{json.dumps(comparison_data, indent=2)}</pre>
</body>
</html>
                """)
            print(f"HTML report: {html_path}")
        
        if args.format in ['text', 'both']:
            text_path = reporter.output_dir / "comparison_report.txt"
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write("OCR COMPARISON REPORT\n")
                f.write("=" * 30 + "\n\n")
                f.write(f"Generated from: {results_dir}\n")
                f.write(f"Best performing engine: {comparison_data.get('best_performing_engine', 'Unknown')}\n\n")
                f.write("Detailed Results:\n")
                f.write(json.dumps(comparison_data, indent=2))
            print(f"Text report: {text_path}")
        
        return 0
        
    except Exception as e:
        print(f"Report generation error: {e}")
        return 1


def list_engines_command(args) -> int:
    """Handle list-engines command."""
    try:
        from .config.config_manager import ConfigManager
        
        config_manager = ConfigManager(args.config_dir)
        enabled_engines = config_manager.get_enabled_engines()
        all_engines = list(config_manager.engines_config.get("engines", {}).keys())
        
        print("OCR ENGINES STATUS")
        print("=" * 30)
        print(f"Configuration directory: {args.config_dir}")
        print(f"Total engines configured: {len(all_engines)}")
        print(f"Enabled engines: {len(enabled_engines)}")
        print()
        
        print("ENGINE STATUS:")
        print("-" * 20)
        
        for engine_name in all_engines:
            status = "ENABLED" if engine_name in enabled_engines else "DISABLED"
            config = config_manager.get_engine_config(engine_name)
            
            print(f"{engine_name:15} [{status:8}]")
            
            # Show key configuration
            if config:
                for key, value in list(config.items())[:3]:  # Show first 3 config items
                    if key != 'enabled':
                        print(f"                  {key}: {value}")
        
        print()
        print("To enable/disable engines, edit config/engines.yaml")
        
        return 0
        
    except Exception as e:
        print(f"Error listing engines: {e}")
        return 1


def test_command(args) -> int:
    """Handle test command."""
    try:
        from .core.telugu_ocr_system import TeluguOCRSystem
        
        print("Testing OCR engines...")
        
        # Initialize system
        ocr_system = TeluguOCRSystem(config_dir=args.config_dir)
        
        # Test engine availability
        available_engines = []
        failed_engines = []
        
        engines_to_test = args.engines or ocr_system.config_manager.get_enabled_engines()
        
        for engine_name in engines_to_test:
            try:
                print(f"Testing {engine_name:15} ", end="")
                
                # Try to initialize the engine
                engine_class = ocr_system._get_engine_class(engine_name)
                if engine_class:
                    config = ocr_system.config_manager.get_engine_config(engine_name)
                    engine = engine_class(config)
                    
                    engine_type = "📦 LOCAL" if engine.is_local_engine() else "🌐 API"
                    
                    if engine.is_available:
                        available_engines.append(engine_name)
                        print(f"✅ AVAILABLE ({engine_type})")
                    else:
                        failed_engines.append(engine_name)
                        if engine.is_local_engine():
                            print(f"❌ NOT AVAILABLE ({engine_type}) - Missing dependencies")
                        else:
                            print(f"⚠️  NOT CONFIGURED ({engine_type}) - No API keys")
                else:
                    failed_engines.append(engine_name)
                    print("❌ NOT IMPLEMENTED")
                    
            except Exception as e:
                failed_engines.append(engine_name)
                print(f"❌ ERROR: {str(e)[:50]}...")
        
        print()
        print("TEST SUMMARY")
        print("=" * 20)
        print(f"Available engines: {len(available_engines)}")
        print(f"Failed engines: {len(failed_engines)}")
        
        if available_engines:
            print(f"\nAvailable: {', '.join(available_engines)}")
        
        if failed_engines:
            print(f"\nFailed: {', '.join(failed_engines)}")
            print("\nCheck the documentation for setup instructions.")
        
        return 0 if available_engines else 1
        
    except Exception as e:
        print(f"Test error: {e}")
        return 1


def main() -> int:
    """Main entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Set up logging level based on debug flag
    if hasattr(args, 'debug') and args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    # Route to appropriate command handler
    if args.command == 'process':
        return process_command(args)
    elif args.command == 'evaluate':
        return evaluate_command(args)
    elif args.command == 'report':
        return report_command(args)
    elif args.command == 'list-engines':
        return list_engines_command(args)
    elif args.command == 'test':
        return test_command(args)
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())