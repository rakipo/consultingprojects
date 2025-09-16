"""EasyOCR engine implementation."""

import time
from PIL import Image
from typing import List, Dict, Any
import numpy as np

from .base_engine import OCREngine
from ..models.data_models import OCRResult, BoundingBox
from ..utils.exceptions import EngineNotAvailableException, OCRException


class EasyOCREngine(OCREngine):
    """EasyOCR engine with Telugu language support."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize EasyOCR engine."""
        super().__init__(config)
        self.languages = self.config.get('languages', ['te', 'en'])
        self.use_gpu = self.config.get('gpu', False)
        self.last_confidence = 0.0
        self.reader = None
        
        # Try to import easyocr
        self.easyocr = None
        try:
            import easyocr
            self.easyocr = easyocr
        except ImportError:
            pass  # Will be handled in _verify_dependencies
        
        # Check availability after initialization
        self.is_available = self._check_availability()
    
    def get_engine_name(self) -> str:
        """Return engine name."""
        return "easyocr"
    
    def supports_telugu(self) -> bool:
        """Return True as EasyOCR supports Telugu."""
        return True
    
    def _verify_dependencies(self) -> bool:
        """Verify EasyOCR installation and initialize reader."""
        try:
            # Check if easyocr module is available
            if self.easyocr is None:
                return False
                
            # Initialize EasyOCR reader
            self.reader = self.easyocr.Reader(
                self.languages, 
                gpu=self.use_gpu
            )
            return True
            
        except Exception as e:
            return False
    
    def extract_text(self, image: Image.Image, page_number: int = 1) -> OCRResult:
        """
        Extract text from image using EasyOCR.
        
        Args:
            image: PIL Image to process
            page_number: Page number for tracking
            
        Returns:
            OCRResult with extracted text and metadata
        """
        start_time = time.time()
        
        try:
            if self.reader is None:
                self._verify_dependencies()
            
            # Convert PIL image to numpy array
            image_array = np.array(image)
            
            # Extract text with bounding boxes and confidence
            results = self.reader.readtext(image_array)
            
            # Process results
            text_parts = []
            bounding_boxes = []
            confidences = []
            
            for (bbox, text, confidence) in results:
                if confidence > 0.1:  # Filter low confidence detections
                    text_parts.append(text)
                    confidences.append(confidence)
                    
                    # Convert bbox to BoundingBox format
                    # EasyOCR returns [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
                    x1, y1 = bbox[0]
                    x2, y2 = bbox[2]
                    
                    box = BoundingBox(
                        x=int(x1),
                        y=int(y1),
                        width=int(x2 - x1),
                        height=int(y2 - y1)
                    )
                    bounding_boxes.append(box)
            
            # Combine text and calculate average confidence
            combined_text = ' '.join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            self.last_confidence = avg_confidence
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                text=combined_text.strip(),
                confidence_score=self.last_confidence,
                bounding_boxes=bounding_boxes,
                processing_time=processing_time,
                engine_name=self.get_engine_name(),
                page_number=page_number
            )
            
        except Exception as e:
            raise OCRException(f"EasyOCR extraction failed: {str(e)}")
    
    def get_confidence_score(self) -> float:
        """Return the confidence score of the last extraction."""
        return self.last_confidence
    
    def get_setup_instructions(self) -> str:
        """Return setup instructions for EasyOCR."""
        return """
EasyOCR Setup Instructions:

1. Install EasyOCR:
   pip install easyocr

2. For GPU support (optional, faster processing):
   - Install PyTorch with CUDA support
   - Set gpu=true in configuration

3. First run will download language models automatically
   - Telugu model (~50MB) will be downloaded on first use
   - Models are cached for future use

4. No additional system dependencies required
   - EasyOCR is self-contained

5. Supported languages include Telugu ('te') and English ('en')
"""
    
    def is_local_engine(self) -> bool:
        """Return True as EasyOCR is a local engine."""
        return True
    
    def cleanup(self):
        """Clean up EasyOCR resources."""
        if self.reader is not None:
            del self.reader
            self.reader = None