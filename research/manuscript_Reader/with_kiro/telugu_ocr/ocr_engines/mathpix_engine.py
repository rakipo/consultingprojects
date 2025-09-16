"""Mathpix OCR engine implementation."""

import time
import io
import requests
import base64
from PIL import Image
from typing import List, Dict, Any

from .base_engine import OCREngine
from ..models.data_models import OCRResult, BoundingBox
from ..utils.exceptions import EngineNotAvailableException, OCRException, APILimitExceededException


class MathpixEngine(OCREngine):
    """Mathpix OCR engine for structured documents and mathematical content."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize Mathpix engine."""
        super().__init__(config)
        self.app_id = self.config.get('app_id', '')
        self.app_key = self.config.get('app_key', '')
        self.last_confidence = 0.0
        
    def get_engine_name(self) -> str:
        """Return engine name."""
        return "mathpix"
    
    def supports_telugu(self) -> bool:
        """Return limited Telugu support for Mathpix."""
        return False  # Mathpix is primarily for mathematical content and English
    
    def get_cost_per_page(self) -> float:
        """Return cost per page for Mathpix OCR."""
        return 0.004  # Approximately $0.004 per request
    
    def _verify_dependencies(self) -> bool:
        """Verify Mathpix OCR setup and authentication."""
        try:
            # Get credentials directly from config
            app_id = self.app_id
            app_key = self.app_key
            
            if not app_id or not app_key or app_id == "your_mathpix_id" or app_key == "your_mathpix_key":
                return False  # Gracefully skip if not configured
            
            return True
            
        except Exception as e:
            return False  # Gracefully skip on any error
    
    def extract_text(self, image: Image.Image, page_number: int = 1) -> OCRResult:
        """
        Extract text from image using Mathpix OCR.
        
        Args:
            image: PIL Image to process
            page_number: Page number for tracking
            
        Returns:
            OCRResult with extracted text and metadata
        """
        start_time = time.time()
        
        try:
            if not self.app_id or not self.app_key or self.app_id == "your_mathpix_id" or self.app_key == "your_mathpix_key":
                self._verify_dependencies()
            
            # Convert PIL image to base64
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            img_base64 = base64.b64encode(img_byte_arr).decode('utf-8')
            
            # Mathpix API endpoint
            url = 'https://api.mathpix.com/v3/text'
            
            # Prepare headers
            headers = {
                'app_id': self.app_id,
                'app_key': self.app_key,
                'Content-type': 'application/json'
            }
            
            # Prepare data
            data = {
                'src': f'data:image/png;base64,{img_base64}',
                'formats': ['text', 'latex'],
                'data_options': {
                    'include_line_data': True,
                    'include_word_data': True
                }
            }
            
            # Make API request
            response = requests.post(url, json=data, headers=headers, timeout=60)
            
            if response.status_code == 429:
                raise APILimitExceededException("Mathpix API rate limit exceeded")
            elif response.status_code == 401:
                raise EngineNotAvailableException("Mathpix API authentication failed")
            elif response.status_code != 200:
                raise OCRException(f"Mathpix API error: {response.status_code} - {response.text}")
            
            # Parse response
            result = response.json()
            
            if result.get('error'):
                raise OCRException(f"Mathpix processing error: {result['error']}")
            
            # Extract text
            extracted_text = result.get('text', '')
            
            # Extract confidence (Mathpix provides overall confidence)
            confidence = result.get('confidence', 0.0)
            if confidence > 1.0:
                confidence = confidence / 100.0  # Convert percentage to 0-1 scale
            self.last_confidence = confidence
            
            # Extract bounding boxes from line data
            bounding_boxes = []
            line_data = result.get('line_data', [])
            
            for line in line_data:
                bbox = line.get('bbox')
                if bbox and len(bbox) >= 4:
                    # Mathpix returns [x, y, width, height]
                    box = BoundingBox(
                        x=int(bbox[0]),
                        y=int(bbox[1]),
                        width=int(bbox[2]),
                        height=int(bbox[3])
                    )
                    bounding_boxes.append(box)
            
            # If no line data, create single bounding box
            if not bounding_boxes:
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
            raise OCRException("Mathpix API request timed out")
        except requests.exceptions.RequestException as e:
            raise OCRException(f"Mathpix API request failed: {str(e)}")
        except Exception as e:
            if isinstance(e, (OCRException, APILimitExceededException, EngineNotAvailableException)):
                raise
            else:
                raise OCRException(f"Mathpix extraction failed: {str(e)}")
    
    def get_confidence_score(self) -> float:
        """Return the confidence score of the last extraction."""
        return self.last_confidence
    
    def get_setup_instructions(self) -> str:
        """Return setup instructions for Mathpix OCR."""
        return """
Mathpix OCR Setup Instructions:

1. Create Mathpix account:
   - Go to https://mathpix.com/
   - Sign up for an account
   - Go to the API dashboard

2. Get API credentials:
   - Create a new app in the dashboard
   - Note your app_id and app_key

3. Install required packages:
   pip install requests

4. Set up authentication:
   - Set environment variables:
     export MATHPIX_APP_ID="your_app_id"
     export MATHPIX_APP_KEY="your_app_key"
   - Or specify in configuration file

5. Pricing:
   - Free tier: 1,000 requests per month
   - Paid plans: Starting from $0.004 per request
   - Volume discounts available

6. Features:
   - Excellent for mathematical equations
   - Good for structured documents
   - LaTeX output support
   - High accuracy for printed text
   - Confidence scores provided

7. Limitations:
   - Primarily designed for English and mathematical content
   - Limited support for Telugu and other Indic scripts
   - Best for documents with mathematical content

8. Best for:
   - Documents with mathematical equations
   - Structured academic papers
   - Technical documents
   - Mixed text and mathematical content

9. Note:
   - Not recommended as primary engine for Telugu text
   - Use in combination with other engines
   - Good for documents with mixed content types
"""