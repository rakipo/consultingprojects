"""PaddleOCR engine implementation."""

import time
from PIL import Image
from typing import List, Dict, Any
import numpy as np

from .base_engine import OCREngine
from ..models.data_models import OCRResult, BoundingBox
from ..utils.exceptions import EngineNotAvailableException, OCRException


class PaddleOCREngine(OCREngine):
    """PaddleOCR engine with Telugu language support."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize PaddleOCR engine."""
        super().__init__(config)
        self.language = self.config.get('language', 'te')
        self.use_gpu = self.config.get('use_gpu', False)
        self.last_confidence = 0.0
        self.ocr = None
        
        # Try to import PaddleOCR
        self.PaddleOCR = None
        try:
            from paddleocr import PaddleOCR
            self.PaddleOCR = PaddleOCR
        except ImportError:
            pass  # Will be handled in _verify_dependencies
        
        # Check availability after initialization
        self.is_available = self._check_availability()
    
    def get_engine_name(self) -> str:
        """Return engine name."""
        return "paddleocr"
    
    def supports_telugu(self) -> bool:
        """Return True as PaddleOCR supports Telugu."""
        return True
    
    def _verify_dependencies(self) -> bool:
        """Verify PaddleOCR installation and initialize OCR."""
        try:
            # Check if PaddleOCR module is available
            if self.PaddleOCR is None:
                return False
                
            # Initialize PaddleOCR
            self.ocr = self.PaddleOCR(
                use_angle_cls=True,
                lang=self.language,
                use_gpu=self.use_gpu,
                show_log=False
            )
            return True
            
        except Exception as e:
            return False
    
    def extract_text(self, image: Image.Image, page_number: int = 1) -> OCRResult:
        """
        Extract text from image using PaddleOCR.
        
        Args:
            image: PIL Image to process
            page_number: Page number for tracking
            
        Returns:
            OCRResult with extracted text and metadata
        """
        start_time = time.time()
        
        try:
            if self.ocr is None:
                self._verify_dependencies()
            
            # Convert PIL image to numpy array
            image_array = np.array(image)
            
            # Extract text with bounding boxes and confidence
            results = self.ocr.ocr(image_array, cls=True)
            
            # Process results
            text_parts = []
            bounding_boxes = []
            confidences = []
            
            if results and results[0]:
                for line in results[0]:
                    if line:
                        bbox, (text, confidence) = line
                        
                        if confidence > 0.1:  # Filter low confidence detections
                            text_parts.append(text)
                            confidences.append(confidence)
                            
                            # Convert bbox to BoundingBox format
                            # PaddleOCR returns [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
                            x_coords = [point[0] for point in bbox]
                            y_coords = [point[1] for point in bbox]
                            
                            x1, x2 = min(x_coords), max(x_coords)
                            y1, y2 = min(y_coords), max(y_coords)
                            
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
            raise OCRException(f"PaddleOCR extraction failed: {str(e)}")
    
    def get_confidence_score(self) -> float:
        """Return the confidence score of the last extraction."""
        return self.last_confidence
    
    def get_setup_instructions(self) -> str:
        """Return setup instructions for PaddleOCR."""
        return """
PaddleOCR Setup Instructions:

1. Install PaddleOCR:
   pip install paddleocr

2. For GPU support (optional, faster processing):
   - Install PaddlePaddle GPU version
   - pip install paddlepaddle-gpu
   - Set use_gpu=true in configuration

3. First run will download models automatically:
   - Detection model (~47MB)
   - Recognition model for Telugu (~10MB)
   - Angle classification model (~1MB)

4. System requirements:
   - Python 3.7+
   - OpenCV (installed automatically)

5. Supported features:
   - Text detection and recognition
   - Angle classification for rotated text
   - Multi-language support including Telugu
"""
    
    def is_local_engine(self) -> bool:
        """Return True as PaddleOCR is a local engine."""
        return True
    
    def cleanup(self):
        """Clean up PaddleOCR resources."""
        if self.ocr is not None:
            del self.ocr
            self.ocr = None