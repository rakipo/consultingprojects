"""Tesseract OCR engine implementation."""

import time
from PIL import Image
from typing import List, Dict, Any
import numpy as np

from .base_engine import OCREngine
from ..models.data_models import OCRResult, BoundingBox
from ..utils.exceptions import EngineNotAvailableException, OCRException


class TesseractEngine(OCREngine):
    """Tesseract OCR engine with Telugu language support."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize Tesseract engine."""
        super().__init__(config)
        self.language = self.config.get('language', 'tel')
        self.psm_config = self.config.get('config', '--psm 6')
        self.last_confidence = 0.0
        
        # Try to import pytesseract
        self.pytesseract = None
        try:
            import pytesseract
            self.pytesseract = pytesseract
        except ImportError:
            pass  # Will be handled in _verify_dependencies
        
        # Check availability after initialization
        self.is_available = self._check_availability()
    
    def get_engine_name(self) -> str:
        """Return engine name."""
        return "tesseract"
    
    def supports_telugu(self) -> bool:
        """Return True as Tesseract supports Telugu."""
        return True
    
    def _verify_dependencies(self) -> bool:
        """Verify Tesseract installation and Telugu language pack."""
        try:
            # Check if pytesseract is available
            if self.pytesseract is None:
                try:
                    import pytesseract
                    self.pytesseract = pytesseract
                except ImportError:
                    return False  # pytesseract not installed
            
            # Check if tesseract is installed
            version = self.pytesseract.get_tesseract_version()
            
            # Check if Telugu language is available
            languages = self.pytesseract.get_languages()
            if 'tel' not in languages:
                return False  # Telugu language pack not available
            
            return True
            
        except Exception as e:
            return False  # Any other error
    
    def extract_text(self, image: Image.Image, page_number: int = 1) -> OCRResult:
        """
        Extract text from image using Tesseract.
        
        Args:
            image: PIL Image to process
            page_number: Page number for tracking
            
        Returns:
            OCRResult with extracted text and metadata
        """
        start_time = time.time()
        
        try:
            # Configure Tesseract
            config = f'-l {self.language} {self.psm_config}'
            
            # Extract text
            text = self.pytesseract.image_to_string(image, config=config)
            
            # Get detailed data for confidence and bounding boxes
            data = self.pytesseract.image_to_data(
                image, 
                config=config, 
                output_type=self.pytesseract.Output.DICT
            )
            
            # Calculate confidence score
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            self.last_confidence = avg_confidence / 100.0  # Convert to 0-1 scale
            
            # Extract bounding boxes
            bounding_boxes = self._extract_bounding_boxes(data)
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                text=text.strip(),
                confidence_score=self.last_confidence,
                bounding_boxes=bounding_boxes,
                processing_time=processing_time,
                engine_name=self.get_engine_name(),
                page_number=page_number
            )
            
        except Exception as e:
            raise OCRException(f"Tesseract extraction failed: {str(e)}")
    
    def _extract_bounding_boxes(self, data: Dict) -> List[BoundingBox]:
        """Extract bounding boxes from Tesseract data."""
        boxes = []
        
        for i in range(len(data['text'])):
            if int(data['conf'][i]) > 0:  # Only include confident detections
                box = BoundingBox(
                    x=data['left'][i],
                    y=data['top'][i],
                    width=data['width'][i],
                    height=data['height'][i]
                )
                boxes.append(box)
        
        return boxes
    
    def get_confidence_score(self) -> float:
        """Return the confidence score of the last extraction."""
        return self.last_confidence
    
    def is_local_engine(self) -> bool:
        """Return True as Tesseract is a local engine."""
        return True
    
    def get_setup_instructions(self) -> str:
        """Return setup instructions for Tesseract."""
        return """
Tesseract OCR Setup Instructions:

1. Install Tesseract OCR:
   - Ubuntu/Debian: sudo apt-get install tesseract-ocr
   - macOS: brew install tesseract
   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki

2. Install Telugu language pack:
   - Ubuntu/Debian: sudo apt-get install tesseract-ocr-tel
   - macOS: brew install tesseract-lang
   - Windows: Download tel.traineddata and place in tessdata folder

3. Install Python wrapper:
   pip install pytesseract

4. Verify installation:
   tesseract --list-langs (should include 'tel')
"""