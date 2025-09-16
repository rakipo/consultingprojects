"""TrOCR (Transformer-based OCR) engine implementation."""

import time
from PIL import Image
from typing import List, Dict, Any
import numpy as np

from .base_engine import OCREngine
from ..models.data_models import OCRResult, BoundingBox
from ..utils.exceptions import EngineNotAvailableException, OCRException


class TrOCREngine(OCREngine):
    """TrOCR transformer-based OCR engine."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize TrOCR engine."""
        super().__init__(config)
        self.model_name = self.config.get('model_name', 'microsoft/trocr-base-printed')
        self.last_confidence = 0.0
        self.processor = None
        self.model = None
        
        # Try to import transformers
        self.TrOCRProcessor = None
        self.VisionEncoderDecoderModel = None
        self.torch = None
        try:
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel
            import torch
            self.TrOCRProcessor = TrOCRProcessor
            self.VisionEncoderDecoderModel = VisionEncoderDecoderModel
            self.torch = torch
        except ImportError:
            pass  # Will be handled in _verify_dependencies
        
        # Check availability after initialization
        self.is_available = self._check_availability()
    
    def get_engine_name(self) -> str:
        """Return engine name."""
        return "trocr"
    
    def supports_telugu(self) -> bool:
        """Return limited Telugu support (depends on model)."""
        return False  # Base TrOCR models don't support Telugu well
    
    def _verify_dependencies(self) -> bool:
        """Verify TrOCR installation and load models."""
        try:
            # Check if transformers modules are available
            if not all([self.TrOCRProcessor, self.VisionEncoderDecoderModel, self.torch]):
                return False
                
            # Load processor and model
            self.processor = self.TrOCRProcessor.from_pretrained(self.model_name)
            self.model = self.VisionEncoderDecoderModel.from_pretrained(self.model_name)
            
            # Set model to evaluation mode
            self.model.eval()
            
            return True
            
        except Exception as e:
            return False
    
    def extract_text(self, image: Image.Image, page_number: int = 1) -> OCRResult:
        """
        Extract text from image using TrOCR.
        
        Args:
            image: PIL Image to process
            page_number: Page number for tracking
            
        Returns:
            OCRResult with extracted text and metadata
        """
        start_time = time.time()
        
        try:
            if self.processor is None or self.model is None:
                self._verify_dependencies()
            
            # Convert image to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Process image
            pixel_values = self.processor(image, return_tensors="pt").pixel_values
            
            # Generate text
            with self.torch.no_grad():
                generated_ids = self.model.generate(pixel_values)
            
            # Decode generated text
            generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            # TrOCR doesn't provide confidence scores directly
            # We'll use a heuristic based on text length and characters
            self.last_confidence = self._estimate_confidence(generated_text)
            
            # TrOCR doesn't provide bounding boxes for individual words
            # Create a single bounding box for the entire image
            width, height = image.size
            bounding_boxes = [BoundingBox(x=0, y=0, width=width, height=height)]
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                text=generated_text.strip(),
                confidence_score=self.last_confidence,
                bounding_boxes=bounding_boxes,
                processing_time=processing_time,
                engine_name=self.get_engine_name(),
                page_number=page_number
            )
            
        except Exception as e:
            raise OCRException(f"TrOCR extraction failed: {str(e)}")
    
    def _estimate_confidence(self, text: str) -> float:
        """
        Estimate confidence based on text characteristics.
        
        Args:
            text: Extracted text
            
        Returns:
            Estimated confidence score (0-1)
        """
        if not text or not text.strip():
            return 0.0
        
        # Simple heuristic: longer text with more alphanumeric characters = higher confidence
        text = text.strip()
        
        # Base confidence
        confidence = 0.5
        
        # Bonus for reasonable length
        if 10 <= len(text) <= 1000:
            confidence += 0.2
        
        # Bonus for alphanumeric content
        alnum_ratio = sum(c.isalnum() for c in text) / len(text)
        confidence += alnum_ratio * 0.3
        
        # Penalty for too many special characters
        special_ratio = sum(not c.isalnum() and not c.isspace() for c in text) / len(text)
        if special_ratio > 0.3:
            confidence -= 0.2
        
        return max(0.0, min(1.0, confidence))
    
    def get_confidence_score(self) -> float:
        """Return the confidence score of the last extraction."""
        return self.last_confidence
    
    def get_setup_instructions(self) -> str:
        """Return setup instructions for TrOCR."""
        return """
TrOCR Setup Instructions:

1. Install required packages:
   pip install transformers torch torchvision

2. For GPU support (recommended):
   - Install PyTorch with CUDA support
   - pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

3. Available models:
   - microsoft/trocr-base-printed (printed text)
   - microsoft/trocr-base-handwritten (handwritten text)
   - microsoft/trocr-large-printed (larger model, better accuracy)

4. First run will download models:
   - Base model: ~1.4GB
   - Large model: ~3.4GB

5. Note: TrOCR works best with English text
   - Limited support for other languages including Telugu
   - Consider using other engines for Telugu text

6. Memory requirements:
   - Base model: ~2GB RAM
   - Large model: ~4GB RAM
"""
    
    def is_local_engine(self) -> bool:
        """Return True as TrOCR is a local engine."""
        return True
    
    def cleanup(self):
        """Clean up TrOCR resources."""
        if self.model is not None:
            del self.model
            self.model = None
        
        if self.processor is not None:
            del self.processor
            self.processor = None