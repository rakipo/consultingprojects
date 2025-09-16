"""AWS Textract OCR engine implementation."""

import time
import io
from PIL import Image
from typing import List, Dict, Any

from .base_engine import OCREngine
from ..models.data_models import OCRResult, BoundingBox
from ..utils.exceptions import EngineNotAvailableException, OCRException, APILimitExceededException


class AWSTextractEngine(OCREngine):
    """AWS Textract OCR engine."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize AWS Textract engine."""
        super().__init__(config)
        self.region = self.config.get('region', 'us-east-1')
        self.access_key = self.config.get('access_key', '')
        self.secret_key = self.config.get('secret_key', '')
        self.last_confidence = 0.0
        self.client = None
        
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError
            self.boto3 = boto3
            self.ClientError = ClientError
            self.NoCredentialsError = NoCredentialsError
        except ImportError:
            raise EngineNotAvailableException(
                "boto3 not found. Install with: pip install boto3"
            )
    
    def get_engine_name(self) -> str:
        """Return engine name."""
        return "aws_textract"
    
    def supports_telugu(self) -> bool:
        """Return limited Telugu support for AWS Textract."""
        return False  # AWS Textract has limited support for Telugu
    
    def get_cost_per_page(self) -> float:
        """Return cost per page for AWS Textract."""
        return 0.0015  # $1.50 per 1000 pages
    
    def _verify_dependencies(self) -> bool:
        """Verify AWS Textract setup and authentication."""
        try:
            # Get credentials directly from config
            access_key = self.access_key
            secret_key = self.secret_key
            
            # Check if credentials are configured (not placeholder values)
            if (access_key == "your_aws_key" or secret_key == "your_aws_secret" or
                not access_key or not secret_key):
                return False  # Gracefully skip if not configured
            
            # Initialize client
            self.client = self.boto3.client(
                'textract',
                region_name=self.region,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key
            )
            
            return True
            
        except Exception as e:
            return False  # Gracefully skip on any error
    
    def extract_text(self, image: Image.Image, page_number: int = 1) -> OCRResult:
        """
        Extract text from image using AWS Textract.
        
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
            
            # Call Textract
            response = self.client.detect_document_text(
                Document={'Bytes': img_byte_arr}
            )
            
            # Extract text and bounding boxes
            text_parts = []
            bounding_boxes = []
            confidences = []
            
            # Get image dimensions for bounding box conversion
            width, height = image.size
            
            for block in response['Blocks']:
                if block['BlockType'] == 'LINE':
                    text_parts.append(block['Text'])
                    
                    # AWS Textract provides confidence scores
                    confidence = block.get('Confidence', 0) / 100.0  # Convert to 0-1 scale
                    confidences.append(confidence)
                    
                    # Extract bounding box
                    if 'Geometry' in block and 'BoundingBox' in block['Geometry']:
                        bbox = block['Geometry']['BoundingBox']
                        
                        # AWS returns normalized coordinates (0-1)
                        x = int(bbox['Left'] * width)
                        y = int(bbox['Top'] * height)
                        w = int(bbox['Width'] * width)
                        h = int(bbox['Height'] * height)
                        
                        box = BoundingBox(x=x, y=y, width=w, height=h)
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
            
        except self.ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['Throttling', 'TooManyRequestsException']:
                raise APILimitExceededException(f"AWS Textract rate limit exceeded: {str(e)}")
            else:
                raise OCRException(f"AWS Textract API error: {str(e)}")
        except self.NoCredentialsError:
            raise EngineNotAvailableException("AWS credentials not found")
        except Exception as e:
            raise OCRException(f"AWS Textract extraction failed: {str(e)}")
    
    def get_confidence_score(self) -> float:
        """Return the confidence score of the last extraction."""
        return self.last_confidence
    
    def get_setup_instructions(self) -> str:
        """Return setup instructions for AWS Textract."""
        return """
AWS Textract Setup Instructions:

1. Install the AWS SDK:
   pip install boto3

2. Set up AWS account and credentials:
   - Create AWS account at https://aws.amazon.com/
   - Create IAM user with Textract permissions
   - Note access key and secret key

3. Configure credentials (choose one method):
   a) Environment variables:
      export AWS_ACCESS_KEY_ID="your_access_key"
      export AWS_SECRET_ACCESS_KEY="your_secret_key"
   
   b) AWS CLI configuration:
      aws configure
   
   c) IAM role (if running on EC2)

4. Pricing (as of 2024):
   - First 1,000 pages per month: Free
   - Additional pages: $1.50 per 1,000 pages

5. Features:
   - High accuracy for English text
   - Limited support for other languages (including Telugu)
   - Confidence scores provided
   - Bounding box information
   - Table detection capabilities

6. Limitations:
   - Best for English and Latin scripts
   - Limited Telugu language support
   - Consider other engines for Telugu-specific needs

7. Rate limits:
   - Synchronous: 5 transactions per second
   - Asynchronous: Higher limits available
"""