"""Error handling and recovery strategies."""

import traceback
from typing import List, Callable, Any, Optional
from .exceptions import *
from .logging_config import get_logger_config


class ErrorHandler:
    """Handles errors and implements recovery strategies."""
    
    def __init__(self):
        """Initialize error handler."""
        self.logger_config = get_logger_config()
        self.error_logger = self.logger_config.get_error_logger()
        self.failed_engines = set()
    
    def handle_engine_error(self, engine_name: str, error: Exception, 
                          page_number: int = None) -> bool:
        """
        Handle OCR engine errors with recovery strategies.
        
        Args:
            engine_name: Name of the failed engine
            error: The exception that occurred
            page_number: Page number being processed
            
        Returns:
            bool: True if processing should continue, False if it should stop
        """
        error_context = f"Page {page_number}" if page_number else "Unknown page"
        
        # Log the error
        self.logger_config.log_error(
            error_type=type(error).__name__,
            message=f"{error_context}: {str(error)}",
            engine_name=engine_name
        )
        
        # Add to failed engines list
        self.failed_engines.add(engine_name)
        
        # Determine recovery strategy based on error type
        if isinstance(error, EngineNotAvailableException):
            self.error_logger.warning(f"Engine {engine_name} not available, skipping")
            return True  # Continue with other engines
        
        elif isinstance(error, APILimitExceededException):
            self.error_logger.warning(f"API limit exceeded for {engine_name}, skipping")
            return True  # Continue with other engines
        
        elif isinstance(error, UnsupportedFormatException):
            self.error_logger.error(f"Unsupported format for {engine_name}")
            return True  # Continue with other engines
        
        elif isinstance(error, PreprocessingException):
            self.error_logger.warning(f"Preprocessing failed for {engine_name}, trying without preprocessing")
            return True  # Could retry without preprocessing
        
        else:
            # Unknown error, log full traceback and continue
            self.error_logger.error(f"Unknown error in {engine_name}: {traceback.format_exc()}")
            return True  # Continue with other engines
    
    def should_continue_processing(self, total_engines: int) -> bool:
        """
        Determine if processing should continue based on failed engines.
        
        Args:
            total_engines: Total number of engines configured
            
        Returns:
            bool: True if processing should continue
        """
        failed_count = len(self.failed_engines)
        success_count = total_engines - failed_count
        
        # Continue if at least one engine is still working
        if success_count > 0:
            return True
        
        # All engines failed
        self.error_logger.error("All OCR engines have failed")
        return False
    
    def get_failed_engines(self) -> List[str]:
        """Get list of failed engines."""
        return list(self.failed_engines)
    
    def reset_failed_engines(self):
        """Reset the failed engines list."""
        self.failed_engines.clear()
    
    def safe_execute(self, func: Callable, *args, **kwargs) -> tuple:
        """
        Safely execute a function with error handling.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            tuple: (success: bool, result: Any, error: Exception)
        """
        try:
            result = func(*args, **kwargs)
            return True, result, None
        except Exception as e:
            return False, None, e
    
    def retry_with_backoff(self, func: Callable, max_retries: int = 3, 
                          backoff_factor: float = 1.0) -> tuple:
        """
        Retry a function with exponential backoff.
        
        Args:
            func: Function to retry
            max_retries: Maximum number of retry attempts
            backoff_factor: Backoff multiplier
            
        Returns:
            tuple: (success: bool, result: Any, error: Exception)
        """
        import time
        
        for attempt in range(max_retries + 1):
            success, result, error = self.safe_execute(func)
            
            if success:
                return True, result, None
            
            if attempt < max_retries:
                wait_time = backoff_factor * (2 ** attempt)
                self.error_logger.info(f"Retrying in {wait_time} seconds (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
        
        return False, None, error
    
    def create_error_summary(self) -> dict:
        """Create a summary of all errors encountered."""
        return {
            "failed_engines": list(self.failed_engines),
            "total_failures": len(self.failed_engines),
            "timestamp": self.logger_config.process_logger.handlers[0].formatter.formatTime(
                self.logger_config.process_logger.makeRecord(
                    "summary", 20, "", 0, "", (), None
                )
            )
        }