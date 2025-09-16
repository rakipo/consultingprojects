"""OCR Engine Manager for coordinating multiple OCR engines."""

import time
from typing import Dict, List, Optional
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base_engine import OCREngine
from ..models.data_models import OCRResult, ComparisonReport
from ..utils.exceptions import OCRException
from ..utils.error_handler import ErrorHandler
from ..utils.logging_config import get_logger_config


class OCRManager:
    """Manages multiple OCR engines and coordinates their execution."""
    
    def __init__(self, max_concurrent: int = 3):
        """
        Initialize OCR manager.
        
        Args:
            max_concurrent: Maximum number of engines to run concurrently
        """
        self.engines: Dict[str, OCREngine] = {}
        self.max_concurrent = max_concurrent
        self.error_handler = ErrorHandler()
        self.logger_config = get_logger_config()
        self.process_logger = self.logger_config.get_process_logger()
        self.engine_logger = self.logger_config.get_engine_logger()
    
    def register_engine(self, engine: OCREngine) -> bool:
        """
        Register an OCR engine.
        
        Args:
            engine: OCR engine instance
            
        Returns:
            bool: True if registration successful
        """
        try:
            engine_name = engine.get_engine_name()
            
            if not engine.is_available:
                if engine.is_local_engine():
                    self.process_logger.warning(f"Local engine {engine_name} is not available (missing dependencies)")
                else:
                    self.process_logger.info(f"API engine {engine_name} is not configured (no API keys), skipping")
                return False
            
            self.engines[engine_name] = engine
            engine_type = "local" if engine.is_local_engine() else "API"
            self.process_logger.info(f"Registered {engine_type} OCR engine: {engine_name}")
            return True
            
        except Exception as e:
            self.error_handler.handle_engine_error(
                engine_name=getattr(engine, 'name', 'unknown'),
                error=e
            )
            return False
    
    def get_available_engines(self) -> List[str]:
        """Get list of available engine names."""
        return list(self.engines.keys())
    
    def process_with_all_engines(self, images: List[Image.Image]) -> Dict[str, List[OCRResult]]:
        """
        Process images with all registered engines.
        
        Args:
            images: List of PIL Images to process
            
        Returns:
            Dictionary mapping engine names to lists of OCR results
        """
        if not self.engines:
            raise OCRException("No OCR engines registered")
        
        if not images:
            raise OCRException("No images provided for processing")
        
        self.process_logger.info(f"Processing {len(images)} images with {len(self.engines)} engines")
        
        results = {}
        
        # Process each engine
        for engine_name, engine in self.engines.items():
            try:
                self.process_logger.info(f"Starting processing with {engine_name}")
                engine_results = self._process_with_single_engine(engine, images)
                results[engine_name] = engine_results
                
            except Exception as e:
                should_continue = self.error_handler.handle_engine_error(
                    engine_name=engine_name,
                    error=e
                )
                if not should_continue:
                    break
        
        # Check if we have any successful results
        if not results:
            raise OCRException("All OCR engines failed to process images")
        
        self.process_logger.info(f"Processing completed. Successful engines: {list(results.keys())}")
        return results
    
    def process_with_single_engine(self, engine_name: str, images: List[Image.Image]) -> List[OCRResult]:
        """
        Process images with a specific engine.
        
        Args:
            engine_name: Name of the engine to use
            images: List of PIL Images to process
            
        Returns:
            List of OCR results
        """
        if engine_name not in self.engines:
            raise OCRException(f"Engine {engine_name} not found")
        
        engine = self.engines[engine_name]
        return self._process_with_single_engine(engine, images)
    
    def _process_with_single_engine(self, engine: OCREngine, images: List[Image.Image]) -> List[OCRResult]:
        """
        Process images with a single engine.
        
        Args:
            engine: OCR engine instance
            images: List of PIL Images to process
            
        Returns:
            List of OCR results
        """
        results = []
        engine_name = engine.get_engine_name()
        
        for page_num, image in enumerate(images, 1):
            try:
                start_time = time.time()
                
                # Extract text from image
                result = engine.extract_text(image, page_num)
                
                processing_time = time.time() - start_time
                result.processing_time = processing_time
                
                # Log performance
                self.logger_config.log_engine_performance(
                    engine_name=engine_name,
                    page_num=page_num,
                    processing_time=processing_time,
                    confidence=result.confidence_score
                )
                
                results.append(result)
                
            except Exception as e:
                should_continue = self.error_handler.handle_engine_error(
                    engine_name=engine_name,
                    error=e,
                    page_number=page_num
                )
                
                if not should_continue:
                    break
                
                # Continue with next page
                continue
        
        return results
    
    def get_engine_comparison(self, all_results: Dict[str, List[OCRResult]]) -> ComparisonReport:
        """
        Generate comparison report across engines.
        
        Args:
            all_results: Results from all engines
            
        Returns:
            ComparisonReport with performance comparison
        """
        if not all_results:
            raise OCRException("No results available for comparison")
        
        # Calculate average metrics for each engine
        engine_metrics = {}
        processing_times = {}
        cost_analysis = {}
        
        for engine_name, results in all_results.items():
            if not results:
                continue
            
            # Calculate averages
            avg_confidence = sum(r.confidence_score for r in results) / len(results)
            total_time = sum(r.processing_time for r in results)
            avg_time_per_page = total_time / len(results)
            
            engine_metrics[engine_name] = avg_confidence
            processing_times[engine_name] = avg_time_per_page
            
            # Get cost information
            engine = self.engines.get(engine_name)
            if engine:
                cost_per_page = engine.get_cost_per_page()
                cost_analysis[engine_name] = cost_per_page * len(results)
        
        # Rank engines by confidence score
        quality_rankings = sorted(
            engine_metrics.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Determine best performing engine
        best_engine = quality_rankings[0][0] if quality_rankings else "none"
        
        # Get a representative result from each engine for comparison
        engine_results = {}
        for engine_name, results in all_results.items():
            if results:
                # Use the result with highest confidence as representative
                best_result = max(results, key=lambda r: r.confidence_score)
                engine_results[engine_name] = best_result
        
        return ComparisonReport(
            engine_results=engine_results,
            best_performing_engine=best_engine,
            quality_rankings=quality_rankings,
            processing_times=processing_times,
            cost_analysis=cost_analysis
        )
    
    def get_engine_setup_instructions(self) -> Dict[str, str]:
        """Get setup instructions for all registered engines."""
        instructions = {}
        for engine_name, engine in self.engines.items():
            instructions[engine_name] = engine.get_setup_instructions()
        return instructions
    
    def cleanup(self):
        """Clean up resources used by engines."""
        for engine_name, engine in self.engines.items():
            try:
                if hasattr(engine, 'cleanup'):
                    engine.cleanup()
            except Exception as e:
                self.process_logger.warning(f"Error cleaning up engine {engine_name}: {str(e)}")
        
        self.engines.clear()
        self.error_handler.reset_failed_engines()