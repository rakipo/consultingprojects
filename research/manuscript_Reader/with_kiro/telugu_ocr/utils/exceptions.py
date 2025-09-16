"""Custom exceptions for Telugu OCR system."""


class OCRException(Exception):
    """Base exception for all OCR-related errors."""
    
    def __init__(self, message: str, engine_name: str = None):
        """Initialize OCR exception."""
        self.engine_name = engine_name
        if engine_name:
            message = f"[{engine_name}] {message}"
        super().__init__(message)


class EngineNotAvailableException(OCRException):
    """Raised when an OCR engine is not properly configured or available."""
    pass


class UnsupportedFormatException(OCRException):
    """Raised when input format is not supported."""
    pass


class APILimitExceededException(OCRException):
    """Raised when cloud API limits are reached."""
    pass


class QualityThresholdException(OCRException):
    """Raised when extraction quality is below acceptable levels."""
    pass


class PreprocessingException(OCRException):
    """Raised when image preprocessing fails."""
    pass


class OutputGenerationException(OCRException):
    """Raised when output file creation fails."""
    pass


class ConfigurationException(OCRException):
    """Raised when configuration is invalid or missing."""
    pass


class DependencyException(OCRException):
    """Raised when required dependencies are not available."""
    pass