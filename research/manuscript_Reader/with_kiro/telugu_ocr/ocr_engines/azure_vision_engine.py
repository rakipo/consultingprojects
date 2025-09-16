"""Azure Computer Vision API OCR engine implementation."""

import time
import io
from PIL import Image
from typing import List, Dict, Any

from .base_engine import OCREngine
from ..models.data_models import OCRResult, BoundingBox
from ..utils.exceptions import EngineNotAvailableException, OCRException, APILimitExceededException


class AzureVisionEngine(OCREngine):
    """Azure Computer Vision API OCR engine."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize Azure Vision engine."""
        super().__init__(config)
        self.subscription_key = self.config.get('subscription_key', '')
        self.endpoint = self.config.get('endpoint', '')
        self.last_confidence = 0.0
        self.client = None
        
        try:
            from azure.cognitiveservices.vision.computervision import ComputerVisionClient
            from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
            from msrest.authentication import CognitiveServicesCredentials
            
            self.ComputerVisionClient = ComputerVisionClient
            self.OperationStatusCodes = OperationStatusCodes
            self.CognitiveServicesCredentials = CognitiveServicesCredentials
        except ImportError:
            raise EngineNotAvailableException(
                "azure-cognitiveservices-vision-computervision not found. "
                "Install with: pip install azure-cognitiveservices-vision-computervision"
            )
    
    def get_engine_name(self) -> str:
        """Return engine name."""
        return "azure_vision"
    
    def supports_telugu(self) -> bool:
        """Return True as Azure Vision supports Telugu."""
        return True
    
    def get_cost_per_page(self) -> float:
        """Return cost per page for Azure Vision API."""
        return 0.001  # $1.00 per 1000 transactions
    
    def _verify_dependencies(self) -> bool:
        """Verify Azure Computer Vision setup and authentication."""
        try:
            # Get credentials directly from config
            subscription_key = self.subscription_key
            endpoint = self.endpoint
            
            # Check if credentials are configured (not placeholder values)
            if (not subscription_key or not endpoint or 
                subscription_key == "your_azure_key" or 
                endpoint == "https://your-resource.cognitiveservices.azure.com/"):
                return False  # Gracefully skip if not configured
            
            # Initialize client
            credentials = self.CognitiveServicesCredentials(subscription_key)
            self.client = self.ComputerVisionClient(endpoint, credentials)
            
            return True
            
        except Exception as e:
            return False  # Gracefully skip on any error
    
    def extract_text(self, image: Image.Image, page_number: int = 1) -> OCRResult:
        """
        Extract text from image using Azure Computer Vision API.
        
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
            img_byte_arr.seek(0)
            
            # Start OCR operation
            read_response = self.client.read_in_stream(img_byte_arr, raw=True)
            
            # Get operation ID from response headers
            read_operation_location = read_response.headers["Operation-Location"]
            operation_id = read_operation_location.split("/")[-1]
            
            # Wait for operation to complete
            import time as time_module
            max_wait_time = 30  # Maximum wait time in seconds
            wait_time = 0
            
            while wait_time < max_wait_time:
                read_result = self.client.get_read_result(operation_id)
                
                if read_result.status not in ['notStarted', 'running']:
                    break
                
                time_module.sleep(1)
                wait_time += 1
            
            if read_result.status == self.OperationStatusCodes.failed:
                raise OCRException("Azure Vision OCR operation failed")
            
            if wait_time >= max_wait_time:
                raise OCRException("Azure Vision OCR operation timed out")
            
            # Extract text and bounding boxes
            text_parts = []
            bounding_boxes = []
            confidences = []
            
            if read_result.analyze_result:
                for text_result in read_result.analyze_result.read_results:
                    for line in text_result.lines:
                        text_parts.append(line.text)
                        
                        # Azure provides confidence scores
                        confidence = getattr(line, 'confidence', 0.8)
                        confidences.append(confidence)
                        
                        # Extract bounding box
                        if line.bounding_box:
                            # Azure returns [x1, y1, x2, y1, x2, y2, x1, y2]
                            bbox = line.bounding_box
                            x_coords = [bbox[i] for i in range(0, len(bbox), 2)]
                            y_coords = [bbox[i] for i in range(1, len(bbox), 2)]
                            
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
            if isinstance(e, OCRException):
                raise
            elif 'quota' in str(e).lower() or 'limit' in str(e).lower():
                raise APILimitExceededException(f"Azure Vision API limit exceeded: {str(e)}")
            else:
                raise OCRException(f"Azure Vision extraction failed: {str(e)}")
    
    def get_confidence_score(self) -> float:
        """Return the confidence score of the last extraction."""
        return self.last_confidence
    
    def get_setup_instructions(self) -> str:
        """Return setup instructions for Azure Computer Vision."""
        return """
Azure Computer Vision API Setup Instructions:

1. Install the client library:
   pip install azure-cognitiveservices-vision-computervision

2. Create Azure Cognitive Services resource:
   - Go to https://portal.azure.com/
   - Create a new Computer Vision resource
   - Note the subscription key and endpoint URL

3. Set up authentication:
   - Set environment variables:
     export AZURE_VISION_KEY="your_subscription_key"
     export AZURE_VISION_ENDPOINT="your_endpoint_url"
   - Or specify in configuration file

4. Pricing (as of 2024):
   - Free tier: 5,000 transactions per month
   - Standard tier: $1.00 per 1,000 transactions

5. Features:
   - Good Telugu language support
   - High accuracy OCR
   - Confidence scores provided
   - Bounding box information
   - Async processing for large images

6. Rate limits:
   - Free tier: 20 calls per minute
   - Standard tier: Higher limits available
"""