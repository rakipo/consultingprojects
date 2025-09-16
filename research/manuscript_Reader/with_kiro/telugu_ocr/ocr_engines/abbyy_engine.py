"""ABBYY Cloud OCR engine implementation."""

import time
import io
import requests
from PIL import Image
from typing import List, Dict, Any

from .base_engine import OCREngine
from ..models.data_models import OCRResult, BoundingBox
from ..utils.exceptions import EngineNotAvailableException, OCRException, APILimitExceededException


class ABBYYEngine(OCREngine):
    """ABBYY Cloud OCR engine for high accuracy document processing."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize ABBYY engine."""
        super().__init__(config)
        self.api_key = self.config.get('api_key', '')
        self.endpoint = self.config.get('endpoint', 'https://cloud-eu.abbyy.com')
        self.last_confidence = 0.0
        
    def get_engine_name(self) -> str:
        """Return engine name."""
        return "abbyy"
    
    def supports_telugu(self) -> bool:
        """Return True as ABBYY supports Telugu."""
        return True
    
    def get_cost_per_page(self) -> float:
        """Return cost per page for ABBYY Cloud OCR."""
        return 0.05  # Approximately $0.05 per page
    
    def _verify_dependencies(self) -> bool:
        """Verify ABBYY Cloud OCR setup and authentication."""
        try:
            # Get API key directly from config
            api_key = self.api_key
            
            if not api_key or api_key == "your_abbyy_key":
                return False  # Gracefully skip if not configured
            
            return True
            
        except Exception as e:
            return False  # Gracefully skip on any error
    
    def extract_text(self, image: Image.Image, page_number: int = 1) -> OCRResult:
        """
        Extract text from image using ABBYY Cloud OCR.
        
        Args:
            image: PIL Image to process
            page_number: Page number for tracking
            
        Returns:
            OCRResult with extracted text and metadata
        """
        start_time = time.time()
        
        try:
            if not self.api_key or self.api_key == "your_abbyy_key":
                self._verify_dependencies()
            
            # Convert PIL image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            # ABBYY Cloud OCR API endpoint
            url = f"{self.endpoint}/v2/processImage"
            
            # Prepare headers
            headers = {
                'Authorization': f'Bearer {self.api_key}'
            }
            
            # Prepare files and data
            files = {
                'file': ('image.png', img_byte_arr, 'image/png')
            }
            
            data = {
                'language': 'Telugu,English',  # Support both Telugu and English
                'exportFormat': 'txt',
                'profile': 'textExtraction'
            }
            
            # Make API request
            response = requests.post(url, headers=headers, files=files, data=data, timeout=60)
            
            if response.status_code == 429:
                raise APILimitExceededException("ABBYY API rate limit exceeded")
            elif response.status_code == 401:
                raise EngineNotAvailableException("ABBYY API authentication failed")
            elif response.status_code != 200:
                raise OCRException(f"ABBYY API error: {response.status_code} - {response.text}")
            
            # Parse response
            result = response.json()
            
            if result.get('error'):
                raise OCRException(f"ABBYY processing error: {result['error']}")
            
            # Extract text
            extracted_text = result.get('text', '')
            
            # ABBYY doesn't provide detailed confidence scores in basic API
            # Estimate confidence based on response quality
            confidence = self._estimate_confidence(extracted_text, result)
            self.last_confidence = confidence
            
            # ABBYY basic API doesn't provide bounding boxes
            # Create a single bounding box for the entire image
            width, height = image.size
            bounding_boxes = [BoundingBox(x=0, y=0, width=width, height=height)]
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                text=extracted_text.strip(),
                confidence_score=self.last_confidence,
                bounding_boxes=bounding_boxes,
                processing_time=processing_time,
                engine_name=self.get_engine_name(),
                page_number=page_number
            )
            
        except requests.exceptions.Timeout:
            raise OCRException("ABBYY API request timed out")
        except requests.exceptions.RequestException as e:
            raise OCRException(f"ABBYY API request failed: {str(e)}")
        except Exception as e:
            if isinstance(e, (OCRException, APILimitExceededException, EngineNotAvailableException)):
                raise
            else:
                raise OCRException(f"ABBYY extraction failed: {str(e)}")
    
    def _estimate_confidence(self, text: str, result: Dict) -> float:
        """
        Estimate confidence based on ABBYY response.
        
        Args:
            text: Extracted text
            result: ABBYY API response
            
        Returns:
            Estimated confidence score
        """
        if not text or not text.strip():
            return 0.0
        
        # Base confidence for ABBYY (generally high quality)
        confidence = 0.9
        
        # Check for quality indicators in response
        if result.get('quality') == 'high':
            confidence = 0.95
        elif result.get('quality') == 'low':
            confidence = 0.7
        
        # Adjust based on text characteristics
        text = text.strip()
        
        # Penalty for very short text
        if len(text) < 5:
            confidence -= 0.1
        
        # Bonus for reasonable length
        if 20 <= len(text) <= 2000:
            confidence += 0.05
        
        return max(0.0, min(1.0, confidence))
    
    def get_confidence_score(self) -> float:
        """Return the confidence score of the last extraction."""
        return self.last_confidence
    
    def get_setup_instructions(self) -> str:
        """Return setup instructions for ABBYY Cloud OCR."""
        return """
ABBYY Cloud OCR Setup Instructions:

1. Create ABBYY Cloud account:
   - Go to https://www.abbyy.com/cloud-ocr-sdk/
   - Sign up for an account
   - Get your API key from the dashboard

2. Install required packages:
   pip install requests

3. Set up authentication:
   - Set environment variable:
     export ABBYY_API_KEY="your_api_key"
   - Or specify in configuration file

4. Pricing (varies by plan):
   - Free tier: Limited number of pages per month
   - Paid plans: Starting from $0.05 per page
   - Volume discounts available

5. Features:
   - Excellent Telugu language support
   - High accuracy for complex documents
   - Support for handwritten text
   - Multiple output formats
   - Advanced document analysis

6. Limitations:
   - Requires internet connection
   - API rate limits apply
   - Cost per page for high volume usage

7. Best for:
   - High-accuracy requirements
   - Complex document layouts
   - Professional document processing
   - Mixed language documents
"""