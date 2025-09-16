"""Google Cloud Vision API OCR engine implementation."""

import time
import io
from PIL import Image
from typing import List, Dict, Any

from .base_engine import OCREngine
from ..models.data_models import OCRResult, BoundingBox
from ..utils.exceptions import EngineNotAvailableException, OCRException, APILimitExceededException


class GoogleVisionEngine(OCREngine):
    """Google Cloud Vision API OCR engine."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize Google Vision engine."""
        super().__init__(config)
        self.api_key_path = self.config.get('api_key_path', '')
        self.last_confidence = 0.0
        self.client = None
        
        # Try to import Google Cloud Vision
        self.vision = None
        self.google_auth = None
        try:
            from google.cloud import vision
            import google.auth
            self.vision = vision
            self.google_auth = google.auth
        except ImportError:
            pass  # Will be handled in _verify_dependencies
        
        # Check availability after initialization
        self.is_available = self._check_availability()
    
    def get_engine_name(self) -> str:
        """Return engine name."""
        return "google_vision"
    
    def supports_telugu(self) -> bool:
        """Return True as Google Vision supports Telugu."""
        return True
    
    def get_cost_per_page(self) -> float:
        """Return cost per page for Google Vision API."""
        return 0.0015  # $1.50 per 1000 requests
    
    def _verify_dependencies(self) -> bool:
        """Verify Google Cloud Vision setup and authentication."""
        try:
            # Check if API key path is configured and valid
            if not self.api_key_path or self.api_key_path == "/path/to/google_key.json":
                return False  # Gracefully skip if not configured
            
            # Verify the credentials file exists
            from pathlib import Path
            if not Path(self.api_key_path).exists():
                return False  # Gracefully skip if file not found
            
            # Set up authentication
            import os
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.api_key_path
            
            # Initialize client
            self.client = self.vision.ImageAnnotatorClient()
            
            return True
            
        except Exception as e:
            return False  # Gracefully skip on any error
    
    def extract_text(self, image: Image.Image, page_number: int = 1) -> OCRResult:
        """
        Extract text from image using Google Cloud Vision API.
        
        Args:
            image: PIL Image to process
            page_number: Page number for tracking
            
        Returns:
            OCRResult with extracted text and metadata
        """
        start_time = time.time()
        
        try:
            if self.client is None:
                self._verify_dependencies()
            
            # Convert PIL image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Create Vision API image object
            vision_image = self.vision.Image(content=img_byte_arr)
            
            # Perform text detection
            response = self.client.text_detection(image=vision_image)
            
            # Check for API errors
            if response.error.message:
                if 'quota' in response.error.message.lower():
                    raise APILimitExceededException(f"Google Vision API quota exceeded: {response.error.message}")
                else:
                    raise OCRException(f"Google Vision API error: {response.error.message}")
            
            # Extract text and annotations
            texts = response.text_annotations
            
            if not texts:
                # No text detected
                return OCRResult(
                    text="",
                    confidence_score=0.0,
                    bounding_boxes=[],
                    processing_time=time.time() - start_time,
                    engine_name=self.get_engine_name(),
                    page_number=page_number
                )
            
            # First annotation contains the full text
            full_text = texts[0].description
            
            # Extract bounding boxes from individual text annotations
            bounding_boxes = []
            confidences = []
            
            for text_annotation in texts[1:]:  # Skip the first one (full text)
                # Google Vision doesn't provide confidence scores directly
                # We'll use a heuristic based on bounding box size and text length
                confidence = self._estimate_confidence(text_annotation)
                confidences.append(confidence)
                
                # Extract bounding box
                vertices = text_annotation.bounding_poly.vertices
                if vertices:
                    x_coords = [v.x for v in vertices]
                    y_coords = [v.y for v in vertices]
                    
                    x1, x2 = min(x_coords), max(x_coords)
                    y1, y2 = min(y_coords), max(y_coords)
                    
                    box = BoundingBox(
                        x=x1,
                        y=y1,
                        width=x2 - x1,
                        height=y2 - y1
                    )
                    bounding_boxes.append(box)
            
            # Calculate average confidence
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.8
            self.last_confidence = avg_confidence
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                text=full_text.strip() if full_text else "",
                confidence_score=self.last_confidence,
                bounding_boxes=bounding_boxes,
                processing_time=processing_time,
                engine_name=self.get_engine_name(),
                page_number=page_number
            )
            
        except Exception as e:
            if isinstance(e, (OCRException, APILimitExceededException)):
                raise
            else:
                raise OCRException(f"Google Vision extraction failed: {str(e)}")
    
    def _estimate_confidence(self, text_annotation) -> float:
        """
        Estimate confidence for Google Vision text annotation.
        
        Args:
            text_annotation: Google Vision text annotation
            
        Returns:
            Estimated confidence score
        """
        # Google Vision doesn't provide confidence scores
        # Use heuristics based on text characteristics
        
        text = text_annotation.description
        if not text:
            return 0.0
        
        # Base confidence for Google Vision (generally high quality)
        confidence = 0.85
        
        # Adjust based on text length
        if len(text) == 1:  # Single character
            confidence -= 0.1
        elif len(text) > 10:  # Longer text
            confidence += 0.05
        
        # Adjust based on bounding box size (larger boxes generally more reliable)
        vertices = text_annotation.bounding_poly.vertices
        if vertices:
            x_coords = [v.x for v in vertices]
            y_coords = [v.y for v in vertices]
            
            width = max(x_coords) - min(x_coords)
            height = max(y_coords) - min(y_coords)
            
            # Very small bounding boxes might be less reliable
            if width < 10 or height < 10:
                confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def get_confidence_score(self) -> float:
        """Return the confidence score of the last extraction."""
        return self.last_confidence
    
    def get_setup_instructions(self) -> str:
        """Return setup instructions for Google Cloud Vision."""
        return """
Google Cloud Vision API Setup Instructions:

1. Install the client library:
   pip install google-cloud-vision

2. Set up Google Cloud Project:
   - Go to https://console.cloud.google.com/
   - Create a new project or select existing one
   - Enable the Cloud Vision API

3. Create service account credentials:
   - Go to IAM & Admin > Service Accounts
   - Create a new service account
   - Download the JSON key file

4. Set up authentication:
   - Set GOOGLE_APPLICATION_CREDENTIALS environment variable:
     export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/credentials.json"
   - Or specify api_key_path in configuration

5. Pricing (as of 2024):
   - First 1,000 requests per month: Free
   - Additional requests: $1.50 per 1,000 requests

6. Features:
   - Excellent Telugu language support
   - High accuracy for printed and handwritten text
   - Automatic language detection
   - Bounding box information
"""