"""Main Telugu OCR System class that orchestrates the entire workflow."""

import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..config.config_manager import ConfigManager
from ..processors.document_processor import DocumentProcessor
from ..processors.image_preprocessor import ImagePreprocessor
from ..ocr_engines.ocr_manager import OCRManager
from ..output.output_manager import OutputManager
from ..quality.quality_assessor import QualityAssessor
from ..quality.evaluation_manager import EvaluationManager
from ..reporting.comparison_reporter import ComparisonReporter
from ..utils.logging_config import get_logger_config
from ..utils.error_handler import ErrorHandler
from ..utils.exceptions import OCRException, UnsupportedFormatException

# Import all OCR engines
from ..ocr_engines.tesseract_engine import TesseractEngine
from ..ocr_engines.easyocr_engine import EasyOCREngine
from ..ocr_engines.paddleocr_engine import PaddleOCREngine
from ..ocr_engines.trocr_engine import TrOCREngine
from ..ocr_engines.google_vision_engine import GoogleVisionEngine
from ..ocr_engines.azure_vision_engine import AzureVisionEngine
from ..ocr_engines.aws_textract_engine import AWSTextractEngine
from ..ocr_engines.abbyy_engine import ABBYYEngine
from ..ocr_engines.nanonets_engine import NanonetsEngine
from ..ocr_engines.mathpix_engine import MathpixEngine


class TeluguOCRSystem:
    """Main Telugu OCR System that coordinates all components."""
    
    def __init__(self, config_dir: str = "config", output_dir: str = "output",
                 enable_preprocessing: bool = True, debug_mode: bool = False):
        """
        Initialize the Telugu OCR System.
        
        Args:
            config_dir: Directory containing configuration files
            output_dir: Base directory for output files
            enable_preprocessing: Whether to enable image preprocessing
            debug_mode: Enable debug logging and additional output
        """
        self.config_dir = config_dir
        self.output_dir = output_dir
        self.enable_preprocessing = enable_preprocessing
        self.debug_mode = debug_mode
        
        # Initialize logging
        self.logger_config = get_logger_config()
        self.process_logger = self.logger_config.get_process_logger()
        self.error_logger = self.logger_config.get_error_logger()
        
        # Initialize components
        self.config_manager = ConfigManager(config_dir)
        self.document_processor = DocumentProcessor()
        self.image_preprocessor = ImagePreprocessor(
            self.config_manager.get_processing_config().get('preprocessing', {})
        ) if enable_preprocessing else None
        self.ocr_manager = OCRManager()
        self.output_manager = OutputManager(output_dir)
        self.quality_assessor = QualityAssessor(
            self.config_manager.get_processing_config().get('quality', {})
        )
        self.evaluation_manager = EvaluationManager()
        self.comparison_reporter = ComparisonReporter()
        self.error_handler = ErrorHandler()
        
        # Engine class mapping
        self.engine_classes = {
            'tesseract': TesseractEngine,
            'easyocr': EasyOCREngine,
            'paddleocr': PaddleOCREngine,
            'trocr': TrOCREngine,
            'google_vision': GoogleVisionEngine,
            'azure_vision': AzureVisionEngine,
            'aws_textract': AWSTextractEngine,
            'abbyy': ABBYYEngine,
            'nanonets': NanonetsEngine,
            'mathpix': MathpixEngine
        }
        
        # Initialize OCR engines
        self._initialize_ocr_engines()
        
        self.process_logger.info("Telugu OCR System initialized")
    
    def _initialize_ocr_engines(self):
        """Initialize and register OCR engines based on configuration."""
        enabled_engines = self.config_manager.get_enabled_engines()
        
        self.process_logger.info(f"Initializing {len(enabled_engines)} enabled engines")
        
        local_engines = []
        api_engines = []
        registered_engines = []
        
        for engine_name in enabled_engines:
            try:
                if engine_name in self.engine_classes:
                    engine_class = self.engine_classes[engine_name]
                    engine_config = self.config_manager.get_engine_config(engine_name)
                    
                    # Create engine instance
                    engine = engine_class(engine_config)
                    
                    # Categorize engine type
                    if engine.is_local_engine():
                        local_engines.append(engine_name)
                    else:
                        api_engines.append(engine_name)
                    
                    # Register with OCR manager
                    if self.ocr_manager.register_engine(engine):
                        registered_engines.append(engine_name)
                else:
                    self.process_logger.warning(f"Unknown engine type: {engine_name}")
                    
            except Exception as e:
                self.error_handler.handle_engine_error(engine_name, e)
        
        # Log summary
        self.process_logger.info(f"Engine initialization summary:")
        self.process_logger.info(f"  Local engines configured: {len(local_engines)} ({', '.join(local_engines)})")
        self.process_logger.info(f"  API engines configured: {len(api_engines)} ({', '.join(api_engines)})")
        self.process_logger.info(f"  Successfully registered: {len(registered_engines)} ({', '.join(registered_engines)})")
        
        if not registered_engines:
            self.process_logger.warning("No OCR engines are available! Check your configuration and dependencies.")
        elif len(registered_engines) < len(enabled_engines):
            missing = set(enabled_engines) - set(registered_engines)
            self.process_logger.info(f"Engines not available: {', '.join(missing)} (missing dependencies or API keys)")
    
    def process_pdf(self, pdf_path: str, specific_engines: List[str] = None) -> Dict[str, Any]:
        """
        Process a PDF document with OCR.
        
        Args:
            pdf_path: Path to the PDF file
            specific_engines: Optional list of specific engines to use
            
        Returns:
            Dictionary containing processing results and output paths
        """
        start_time = time.time()
        
        try:
            # Validate input
            pdf_file = Path(pdf_path)
            if not pdf_file.exists():
                raise UnsupportedFormatException(f"PDF file not found: {pdf_path}")
            
            # Log processing start
            available_engines = self.ocr_manager.get_available_engines()
            engines_to_use = specific_engines or available_engines
            
            # Categorize engines for better logging
            local_available = [e for e in available_engines if e in ['tesseract', 'easyocr', 'paddleocr', 'trocr']]
            api_available = [e for e in available_engines if e not in ['tesseract', 'easyocr', 'paddleocr', 'trocr']]
            
            self.process_logger.info(f"Available engines: {len(available_engines)} total")
            self.process_logger.info(f"  Local engines: {len(local_available)} ({', '.join(local_available)})")
            self.process_logger.info(f"  API engines: {len(api_available)} ({', '.join(api_available)})")
            
            if not available_engines:
                self.process_logger.error("No OCR engines are available! Please check your configuration.")
                raise OCRException("No OCR engines are available")
            
            self.logger_config.log_processing_start(pdf_path, engines_to_use)
            
            # Create output directory
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_directory = self.output_manager.create_output_structure(timestamp)
            
            # Step 1: Convert PDF to images
            self.process_logger.info("Converting PDF to images...")
            images = self.document_processor.convert_pdf_to_images(pdf_path)
            
            if self.debug_mode:
                # Save debug images
                debug_dir = Path(output_directory) / "debug_images"
                self.document_processor.save_images_for_debug(images, str(debug_dir))
            
            # Step 2: Preprocess images (if enabled)
            if self.enable_preprocessing and self.image_preprocessor:
                self.process_logger.info("Preprocessing images...")
                preprocessed_images = []
                
                for i, image in enumerate(images, 1):
                    try:
                        processed_image = self.image_preprocessor.preprocess_image(image, i)
                        # Apply Telugu-specific enhancements
                        processed_image = self.image_preprocessor.enhance_for_telugu(processed_image)
                        preprocessed_images.append(processed_image)
                    except Exception as e:
                        self.error_handler.handle_engine_error("preprocessor", e, i)
                        # Use original image if preprocessing fails
                        preprocessed_images.append(image)
                
                images = preprocessed_images
            
            # Step 3: Process with OCR engines
            self.process_logger.info(f"Processing with {len(engines_to_use)} OCR engines...")
            
            if specific_engines:
                # Filter OCR manager to use only specific engines
                all_results = {}
                for engine_name in specific_engines:
                    if engine_name in available_engines:
                        try:
                            results = self.ocr_manager.process_with_single_engine(engine_name, images)
                            all_results[engine_name] = results
                        except Exception as e:
                            self.error_handler.handle_engine_error(engine_name, e)
            else:
                # Use all available engines
                all_results = self.ocr_manager.process_with_all_engines(images)
            
            if not all_results:
                raise OCRException("No OCR engines produced results")
            
            # Step 4: Save results in multiple formats
            self.process_logger.info("Saving results in multiple formats...")
            saved_files = {}
            
            for engine_name, results in all_results.items():
                if results:
                    engine_files = self.output_manager.save_ocr_results(
                        results, engine_name, output_directory
                    )
                    saved_files[engine_name] = engine_files
            
            # Step 5: Quality assessment
            self.process_logger.info("Performing quality assessment...")
            quality_reports = {}
            
            for engine_name, results in all_results.items():
                if results:
                    # Extract text and confidence scores
                    extracted_text = ' '.join(r.text for r in results)
                    confidence_scores = [r.confidence_score for r in results]
                    
                    quality_report = self.quality_assessor.assess_text_quality(
                        extracted_text, confidence_scores, engine_name
                    )
                    quality_reports[engine_name] = quality_report
            
            # Step 6: Generate comparison report
            self.process_logger.info("Generating comparison report...")
            comparison_report = self.ocr_manager.get_engine_comparison(all_results)
            
            # Save comparison report
            comparison_report_path = self.output_manager.save_comparison_report(
                comparison_report, output_directory
            )
            
            # Step 7: Generate performance dashboard
            dashboard_path = None
            try:
                dashboard_path = self.comparison_reporter.generate_performance_dashboard(
                    all_results, quality_reports, 
                    str(Path(output_directory) / "performance_dashboard.html")
                )
            except Exception as e:
                self.process_logger.warning(f"Failed to generate performance dashboard: {e}")
            
            # Step 8: Create evaluation forms
            evaluation_form_path = None
            try:
                evaluation_form_path = self.evaluation_manager.generate_evaluation_form(
                    all_results, images
                )
            except Exception as e:
                self.process_logger.warning(f"Failed to create evaluation forms: {e}")
            
            # Calculate total processing time
            total_time = time.time() - start_time
            self.logger_config.log_processing_complete(pdf_path, total_time)
            
            # Prepare results summary
            results_summary = {
                'success': True,
                'pdf_path': pdf_path,
                'output_directory': output_directory,
                'processing_time': total_time,
                'pages_processed': len(images),
                'engines_used': list(all_results.keys()),
                'engine_results': all_results,
                'quality_reports': quality_reports,
                'comparison_report': comparison_report_path,
                'performance_dashboard': dashboard_path,
                'evaluation_form': evaluation_form_path,
                'saved_files': saved_files,
                'summary_stats': self._generate_summary_stats(all_results, quality_reports)
            }
            
            self.process_logger.info(f"Processing completed successfully in {total_time:.2f} seconds")
            return results_summary
            
        except Exception as e:
            total_time = time.time() - start_time
            self.error_logger.error(f"Processing failed after {total_time:.2f} seconds: {str(e)}")
            
            return {
                'success': False,
                'pdf_path': pdf_path,
                'error': str(e),
                'processing_time': total_time,
                'failed_engines': self.error_handler.get_failed_engines()
            }
    
    def _generate_summary_stats(self, all_results: Dict[str, List], 
                               quality_reports: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics for the processing session."""
        stats = {
            'total_engines': len(all_results),
            'successful_engines': len([r for r in all_results.values() if r]),
            'total_pages': 0,
            'average_confidence': 0.0,
            'average_quality_score': 0.0,
            'best_engine': None,
            'processing_times': {}
        }
        
        if not all_results:
            return stats
        
        # Calculate averages
        all_confidences = []
        all_quality_scores = []
        
        for engine_name, results in all_results.items():
            if results:
                stats['total_pages'] = max(stats['total_pages'], len(results))
                
                # Confidence scores
                engine_confidences = [r.confidence_score for r in results]
                all_confidences.extend(engine_confidences)
                
                # Processing times
                total_time = sum(r.processing_time for r in results)
                stats['processing_times'][engine_name] = total_time
                
                # Quality scores
                if quality_reports and engine_name in quality_reports:
                    quality_score = quality_reports[engine_name].overall_score
                    all_quality_scores.append(quality_score)
        
        # Calculate averages
        if all_confidences:
            stats['average_confidence'] = sum(all_confidences) / len(all_confidences)
        
        if all_quality_scores:
            stats['average_quality_score'] = sum(all_quality_scores) / len(all_quality_scores)
            # Find best engine by quality score
            best_engine = max(quality_reports.keys(), 
                            key=lambda k: quality_reports[k].overall_score)
            stats['best_engine'] = best_engine
        
        return stats
    
    def get_engine_setup_instructions(self) -> Dict[str, str]:
        """Get setup instructions for all engines."""
        return self.ocr_manager.get_engine_setup_instructions()
    
    def get_available_engines(self) -> List[str]:
        """Get list of available OCR engines."""
        return self.ocr_manager.get_available_engines()
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        return {
            'config_directory': self.config_dir,
            'output_directory': self.output_dir,
            'preprocessing_enabled': self.enable_preprocessing,
            'debug_mode': self.debug_mode,
            'available_engines': self.get_available_engines(),
            'enabled_engines': self.config_manager.get_enabled_engines(),
            'failed_engines': self.error_handler.get_failed_engines()
        }
    
    def _get_engine_class(self, engine_name: str):
        """Get engine class by name (for testing purposes)."""
        return self.engine_classes.get(engine_name)
    
    def cleanup(self):
        """Clean up system resources."""
        try:
            self.ocr_manager.cleanup()
            self.process_logger.info("System cleanup completed")
        except Exception as e:
            self.error_logger.error(f"Error during cleanup: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()