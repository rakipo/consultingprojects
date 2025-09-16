"""Nanonets OCR engine implementation."""

import time
import io
import requests
from PIL import Image
from typing import List, Dict, Any

from .base_engine import OCREngine
from ..models.data_models import OCRResult, BoundingBox
from ..utils.exceptions import EngineNotAvailableException, OCRException, APILimitExceededException


class NanonetsEngine(OCREngine):
    """Nanonets OCR engine specialized for handwritten text."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize Nanonets engine."""
        super().__init__(config)
        self.api_key = self.config.get('api_key', '')
        self.model_id = self.config.get('model_id', '')
        self.last_confidence = 0.0
        
    def get_engine_name(self) -> str:
        """Return engine name."""
        return "nanonets"
    
    def supports_telugu(self) -> bool:
        """Return limited Telugu support for Nanonets."""
        return True  # Depends on model training
    
    def get_cost_per_page(self) -> float:
        """Return cost per page for Nanonets OCR."""
        return 0.02  # Approximately $0.02 per page
    
    def _verify_dependencies(self) -> bool:
        """Verify Nanonets OCR setup and authentication."""
        try:
            # Get credentials directly from config
            api_key = self.api_key
            model_id = self.model_id
            
            if not api_key or not model_id or api_key == "your_nanonets_key" or model_id == "your_model_id":
                return False  # Gracefully skip if not configured
            
            return True
            
        except Exception as e:
            return False  # Gracefully skip on any error
    
    def extract_text(self, image: Image.Image, page_number: int = 1) -> OCRResult:
        """
        Extract text from image using Nanonets OCR.
        
        Args:
            image: PIL Image to process
            page_number: Page number for tracking
            
        Returns:
            OCRResult with extracted text and metadata
        """
        start_time = time.time()
        
        try:
            if not self.api_key or not self.model_id or self.api_key == "your_nanonets_key" or self.model_id == "your_model_id":
                self._verify_dependencies()
            
            # Convert PIL image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            # Nanonets API endpoint
            url = f'https://app.nanonets.com/api/v2/OCR/Model/{self.model_id}/LabelFile/'
            
            # Prepare files
            files = {
                'file': ('image.png', img_byte_arr, 'image/png')
            }
            
            # Make API request with authentication
            response = requests.post(
                url,
                auth=requests.auth.HTTPBasicAuth(self.api_key, ''),
                files=files,
                timeout=60
            )
            
            if response.status_code == 429:
                raise APILimitExceededException("Nanonets API rate limit exceeded")
            elif response.status_code == 401:
                raise EngineNotAvailableException("Nanonets API authentication failed")
            elif response.status_code != 200:
                raise OCRException(f"Nanonets API error: {response.status_code} - {response.text}")
            
            # Parse response
            result = response.json()
            
            if result.get('message') and 'error' in result.get('message', '').lower():
                raise OCRException(f"Nanonets processing error: {result['message']}")
            
            # Extract text and bounding boxes
            text_parts = []
            bounding_boxes = []
            confidences = []
            
            # Process predictions
            predictions = result.get('result', [])
            for prediction in predictions:
                if prediction.get('ocr_text'):
                    for ocr_item in prediction['ocr_text']:
                        text = ocr_item.get('text', '')
                        confidence = ocr_item.get('confidence', 0.0)
                        
                        if text and confidence > 0.1:  # Filter low confidence
                            text_parts.append(text)
                            confidences.append(confidence)
                            
                            # Extract bounding box
                            bbox = ocr_item.get('bounding_box', {})
                            if bbox:
                                x = bbox.get('x_min', 0)
                                y = bbox.get('y_min', 0)
                                width = bbox.get('x_max', 0) - x
                                height = bbox.get('y_max', 0) - y
                                
                                box = BoundingBox(
                                    x=int(x),
                                    y=int(y),
                                    width=int(width),
                                    height=int(height)
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
            
        except requests.exceptions.Timeout:
            raise OCRException("Nanonets API request timed out")
        except requests.exceptions.RequestException as e:
            raise OCRException(f"Nanonets API request failed: {str(e)}")
        except Exception as e:
            if isinstance(e, (OCRException, APILimitExceededException, EngineNotAvailableException)):
                raise
            else:
                raise OCRException(f"Nanonets extraction failed: {str(e)}")
    
    def get_confidence_score(self) -> float:
        """Return the confidence score of the last extraction."""
        return self.last_confidence
    
    def get_setup_instructions(self) -> str:
        """Return setup instructions for Nanonets OCR."""
        return """
Nanonets OCR Setup Instructions:

1. Create Nanonets account:
   - Go to https://nanonets.com/
   - Sign up for an account
   - Create a new OCR model

2. Train your model (for Telugu):
   - Upload sample Telugu documents
   - Annotate the text regions
   - Train the model (may take time)
   - Note the model ID

3. Get API credentials:
   - Go to your account settings
   - Copy your API key
   - Note your trained model ID

4. Install required packages:
   pip install requests

5. Set up authentication:
   - Set environment variables:
     export NANONETS_API_KEY="your_api_key"
     export NANONETS_MODEL_ID="your_model_id"
   - Or specify in configuration file

6. Pricing:
   - Free tier: Limited predictions per month
   - Paid plans: Starting from $0.02 per prediction
   - Custom pricing for high volume

7. Features:
   - Excellent for handwritten text
   - Custom model training
   - Good accuracy after proper training
   - Bounding box information
   - Confidence scores

8. Best for:
   - Handwritten Telugu documents
   - Custom document types
   - Specific use cases requiring model training
   - High accuracy after training

9. Note:
   - Requires model training for Telugu
   - Performance depends on training data quality
   - May need multiple iterations to achieve good accuracy
"""