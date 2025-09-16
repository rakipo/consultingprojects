"""Logging configuration for Telugu OCR system."""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path


class LoggingConfig:
    """Manages logging configuration for the Telugu OCR system."""
    
    def __init__(self, log_dir: str = "logs"):
        """Initialize logging configuration."""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self._setup_loggers()
    
    def _setup_loggers(self):
        """Set up different loggers for different purposes."""
        # Main processing logger
        self.process_logger = self._create_logger(
            "ocr_processing",
            self.log_dir / "ocr_processing.log",
            logging.INFO
        )
        
        # Engine performance logger
        self.engine_logger = self._create_logger(
            "engine_performance",
            self.log_dir / "engine_performance.log",
            logging.INFO
        )
        
        # Error logger
        self.error_logger = self._create_logger(
            "errors",
            self.log_dir / "errors.log",
            logging.ERROR
        )
        
        # Quality assessment logger
        self.quality_logger = self._create_logger(
            "quality_assessment",
            self.log_dir / "quality_assessment.log",
            logging.INFO
        )
    
    def _create_logger(self, name: str, log_file: Path, level: int) -> logging.Logger:
        """Create a logger with specified configuration."""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Remove existing handlers to avoid duplicates
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create formatter
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
        
        # Console handler for errors and warnings
        if level <= logging.WARNING:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.WARNING)
            logger.addHandler(console_handler)
        
        return logger
    
    def get_process_logger(self) -> logging.Logger:
        """Get the main processing logger."""
        return self.process_logger
    
    def get_engine_logger(self) -> logging.Logger:
        """Get the engine performance logger."""
        return self.engine_logger
    
    def get_error_logger(self) -> logging.Logger:
        """Get the error logger."""
        return self.error_logger
    
    def get_quality_logger(self) -> logging.Logger:
        """Get the quality assessment logger."""
        return self.quality_logger
    
    def log_processing_start(self, pdf_path: str, engines: list):
        """Log the start of processing."""
        self.process_logger.info(f"Starting OCR processing for: {pdf_path}")
        self.process_logger.info(f"Enabled engines: {', '.join(engines)}")
    
    def log_processing_complete(self, pdf_path: str, total_time: float):
        """Log the completion of processing."""
        self.process_logger.info(f"Completed OCR processing for: {pdf_path}")
        self.process_logger.info(f"Total processing time: {total_time:.2f} seconds")
    
    def log_engine_performance(self, engine_name: str, page_num: int, 
                             processing_time: float, confidence: float):
        """Log engine performance metrics."""
        self.engine_logger.info(
            f"Engine: {engine_name}, Page: {page_num}, "
            f"Time: {processing_time:.2f}s, Confidence: {confidence:.2f}"
        )
    
    def log_error(self, error_type: str, message: str, engine_name: str = None):
        """Log an error with context."""
        context = f" [Engine: {engine_name}]" if engine_name else ""
        self.error_logger.error(f"{error_type}{context}: {message}")
    
    def log_quality_assessment(self, engine_name: str, quality_score: float, 
                             telugu_detection: float):
        """Log quality assessment results."""
        self.quality_logger.info(
            f"Engine: {engine_name}, Quality Score: {quality_score:.2f}, "
            f"Telugu Detection: {telugu_detection:.2f}"
        )


# Global logging instance
_logging_config = None

def get_logger_config() -> LoggingConfig:
    """Get the global logging configuration instance."""
    global _logging_config
    if _logging_config is None:
        _logging_config = LoggingConfig()
    return _logging_config