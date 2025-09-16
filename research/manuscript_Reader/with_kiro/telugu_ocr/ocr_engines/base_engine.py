"""Base OCR engine interface."""

from abc import ABC, abstractmethod
from PIL import Image
from typing import List, Dict, Any
from ..models.data_models import OCRResult


class OCREngine(ABC):
    """Abstract base class for all OCR engine implementations."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the OCR engine with configuration."""
        self.config = config or {}
        self.name = self.get_engine_name()
        # Note: is_available will be set by subclass after initialization
    
    @abstractmethod
    def extract_text(self, image: Image.Image, page_number: int = 1) -> OCRResult:
        """
        Extract text from an image.
        
        Args:
            image: PIL Image object
            page_number: Page number for tracking
            
        Returns:
            OCRResult containing extracted text and metadata
        """
        pass
    
    @abstractmethod
    def get_engine_name(self) -> str:
        """Return the name of the OCR engine."""
        pass
    
    @abstractmethod
    def get_confidence_score(self) -> float:
        """Return the confidence score of the last extraction."""
        pass
    
    @abstractmethod
    def supports_telugu(self) -> bool:
        """Return True if the engine supports Telugu language."""
        pass
    
    def _check_availability(self) -> bool:
        """Check if the engine is available and properly configured."""
        try:
            return self._verify_dependencies()
        except Exception as e:
            # Log the reason for unavailability but don't raise exception
            print(f"Engine {self.get_engine_name()} not available: {str(e)}")
            return False
    
    @abstractmethod
    def _verify_dependencies(self) -> bool:
        """Verify that all required dependencies are available."""
        pass
    
    def get_cost_per_page(self) -> float:
        """Return the cost per page for this engine (0.0 for free engines)."""
        return 0.0
    
    def get_setup_instructions(self) -> str:
        """Return setup instructions for this engine."""
        return f"Setup instructions for {self.get_engine_name()} not available."
    
    def is_local_engine(self) -> bool:
        """Return True if this is a local engine (no API keys required)."""
        return False
    
    def requires_api_key(self) -> bool:
        """Return True if this engine requires API keys."""
        return not self.is_local_engine()