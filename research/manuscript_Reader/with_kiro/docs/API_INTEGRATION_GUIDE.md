# API Integration Guide

This guide provides step-by-step instructions for integrating each OCR API supported by the Telugu Document OCR system.

## Table of Contents

1. [Free/Open Source Engines](#freeopen-source-engines)
2. [Cloud-based APIs](#cloud-based-apis)
3. [Premium APIs](#premium-apis)
4. [Authentication Setup](#authentication-setup)
5. [Rate Limits and Quotas](#rate-limits-and-quotas)
6. [Cost Analysis](#cost-analysis)
7. [Troubleshooting](#troubleshooting)

## Free/Open Source Engines

### Tesseract OCR

**Installation:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-tel

# macOS
brew install tesseract tesseract-lang

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

**Python Package:**
```bash
pip install pytesseract
```

**Configuration:**
```yaml
# config/engines.yaml
tesseract:
  enabled: true
  language: "tel"
  config: "--psm 6"  # Page segmentation mode
```

**Verification:**
```bash
# Check installation
tesseract --version

# Check Telugu language availability
tesseract --list-langs
# Should include 'tel'
```

**Telugu Support:** Excellent (with language pack)
**Cost:** Free
**Best For:** General Telugu text, printed documents

---

### EasyOCR

**Installation:**
```bash
pip install easyocr
```

**Configuration:**
```yaml
# config/engines.yaml
easyocr:
  enabled: true
  languages: ["te", "en"]  # Telugu and English
  gpu: false  # Set to true for GPU acceleration
```

**GPU Support (Optional):**
```bash
# Install PyTorch with CUDA support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**First Run:**
- Models will be downloaded automatically (~50MB for Telugu)
- Models are cached for future use

**Telugu Support:** Excellent
**Cost:** Free
**Best For:** Mixed Telugu/English text, handwritten text

---

### PaddleOCR

**Installation:**
```bash
pip install paddleocr
```

**Configuration:**
```yaml
# config/engines.yaml
paddleocr:
  enabled: true
  language: "te"  # Telugu
  use_gpu: false
```

**GPU Support (Optional):**
```bash
pip install paddlepaddle-gpu
```

**First Run:**
- Models download automatically (~60MB total)
- Includes detection, recognition, and angle classification models

**Telugu Support:** Good
**Cost:** Free
**Best For:** Structured documents, rotated text

---

### TrOCR

**Installation:**
```bash
pip install transformers torch
```

**Configuration:**
```yaml
# config/engines.yaml
trocr:
  enabled: false  # Limited Telugu support
  model_name: "microsoft/trocr-base-printed"
```

**Models Available:**
- `microsoft/trocr-base-printed` - For printed text
- `microsoft/trocr-base-handwritten` - For handwritten text
- `microsoft/trocr-large-printed` - Larger model, better accuracy

**Telugu Support:** Poor (primarily English)
**Cost:** Free
**Best For:** English text, mathematical content

## Cloud-based APIs

### Google Cloud Vision API

**Setup Steps:**

1. **Create Google Cloud Project:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable the Cloud Vision API

2. **Create Service Account:**
   - Go to IAM & Admin > Service Accounts
   - Create a new service account
   - Download the JSON key file

3. **Install Client Library:**
   ```bash
   pip install google-cloud-vision
   ```

4. **Authentication:**
   ```bash
   # Method 1: Environment variable
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/credentials.json"
   
   # Method 2: Configuration file
   # Set api_key_path in config/engines.yaml
   ```

5. **Configuration:**
   ```yaml
   # config/engines.yaml
   google_vision:
     enabled: true
     api_key_path: "credentials/google_vision_key.json"
   ```

**Pricing (2024):**
- First 1,000 requests/month: Free
- Additional requests: $1.50 per 1,000 requests

**Rate Limits:**
- 1,800 requests per minute
- 600 requests per minute per IP

**Telugu Support:** Excellent
**Best For:** High accuracy requirements, mixed content

---

### Azure Computer Vision

**Setup Steps:**

1. **Create Azure Resource:**
   - Go to [Azure Portal](https://portal.azure.com/)
   - Create a Computer Vision resource
   - Note the subscription key and endpoint URL

2. **Install Client Library:**
   ```bash
   pip install azure-cognitiveservices-vision-computervision
   ```

3. **Authentication:**
   ```bash
   export AZURE_VISION_KEY="your_subscription_key"
   export AZURE_VISION_ENDPOINT="your_endpoint_url"
   ```

4. **Configuration:**
   ```yaml
   # config/engines.yaml
   azure_vision:
     enabled: true
     subscription_key: "env:AZURE_VISION_KEY"
     endpoint: "env:AZURE_VISION_ENDPOINT"
   ```

**Pricing (2024):**
- Free tier: 5,000 transactions/month
- Standard tier: $1.00 per 1,000 transactions

**Rate Limits:**
- Free tier: 20 calls per minute
- Standard tier: Higher limits available

**Telugu Support:** Good
**Best For:** Cost-effective cloud OCR, batch processing

---

### AWS Textract

**Setup Steps:**

1. **Create AWS Account:**
   - Sign up at [AWS](https://aws.amazon.com/)
   - Create IAM user with Textract permissions

2. **Install SDK:**
   ```bash
   pip install boto3
   ```

3. **Authentication:**
   ```bash
   # Method 1: Environment variables
   export AWS_ACCESS_KEY_ID="your_access_key"
   export AWS_SECRET_ACCESS_KEY="your_secret_key"
   
   # Method 2: AWS CLI
   aws configure
   
   # Method 3: IAM role (if running on EC2)
   ```

4. **Configuration:**
   ```yaml
   # config/engines.yaml
   aws_textract:
     enabled: true
     region: "us-east-1"
     access_key: "env:AWS_ACCESS_KEY"
     secret_key: "env:AWS_SECRET_KEY"
   ```

**Pricing (2024):**
- First 1,000 pages/month: Free
- Additional pages: $1.50 per 1,000 pages

**Rate Limits:**
- Synchronous: 5 transactions per second
- Asynchronous: Higher limits available

**Telugu Support:** Limited
**Best For:** English documents, table extraction

## Premium APIs

### ABBYY Cloud OCR

**Setup Steps:**

1. **Create Account:**
   - Sign up at [ABBYY Cloud](https://www.abbyy.com/cloud-ocr-sdk/)
   - Get API key from dashboard

2. **Authentication:**
   ```bash
   export ABBYY_API_KEY="your_api_key"
   ```

3. **Configuration:**
   ```yaml
   # config/engines.yaml
   abbyy:
     enabled: true
     api_key: "env:ABBYY_API_KEY"
     endpoint: "https://cloud-eu.abbyy.com"
   ```

**Pricing:**
- Free tier: Limited pages/month
- Paid plans: Starting from $0.05 per page
- Volume discounts available

**Telugu Support:** Excellent
**Best For:** High accuracy, complex documents, handwritten text

---

### Nanonets OCR

**Setup Steps:**

1. **Create Account:**
   - Sign up at [Nanonets](https://nanonets.com/)
   - Create a new OCR model

2. **Train Model for Telugu:**
   - Upload sample Telugu documents
   - Annotate text regions
   - Train the model (may take time)
   - Note the model ID

3. **Authentication:**
   ```bash
   export NANONETS_API_KEY="your_api_key"
   export NANONETS_MODEL_ID="your_model_id"
   ```

4. **Configuration:**
   ```yaml
   # config/engines.yaml
   nanonets:
     enabled: true
     api_key: "env:NANONETS_API_KEY"
     model_id: "env:NANONETS_MODEL_ID"
   ```

**Pricing:**
- Free tier: Limited predictions/month
- Paid plans: Starting from $0.02 per prediction

**Telugu Support:** Good (with proper training)
**Best For:** Handwritten Telugu, custom document types

---

### Mathpix OCR

**Setup Steps:**

1. **Create Account:**
   - Sign up at [Mathpix](https://mathpix.com/)
   - Create a new app in dashboard
   - Note app_id and app_key

2. **Authentication:**
   ```bash
   export MATHPIX_APP_ID="your_app_id"
   export MATHPIX_APP_KEY="your_app_key"
   ```

3. **Configuration:**
   ```yaml
   # config/engines.yaml
   mathpix:
     enabled: false  # Limited Telugu support
     app_id: "env:MATHPIX_APP_ID"
     app_key: "env:MATHPIX_APP_KEY"
   ```

**Pricing:**
- Free tier: 1,000 requests/month
- Paid plans: Starting from $0.004 per request

**Telugu Support:** Poor
**Best For:** Mathematical equations, structured documents

## Authentication Setup

### Environment Variables

Create a `.env` file in your project root:

```bash
# Google Cloud Vision
GOOGLE_APPLICATION_CREDENTIALS="/path/to/google-credentials.json"

# Azure Computer Vision
AZURE_VISION_KEY="your_azure_key"
AZURE_VISION_ENDPOINT="https://your-resource.cognitiveservices.azure.com/"

# AWS Textract
AWS_ACCESS_KEY_ID="your_aws_access_key"
AWS_SECRET_ACCESS_KEY="your_aws_secret_key"

# ABBYY Cloud OCR
ABBYY_API_KEY="your_abbyy_key"

# Nanonets OCR
NANONETS_API_KEY="your_nanonets_key"
NANONETS_MODEL_ID="your_model_id"

# Mathpix OCR
MATHPIX_APP_ID="your_mathpix_app_id"
MATHPIX_APP_KEY="your_mathpix_app_key"
```

### Credential Files

Store credential files securely:

```
credentials/
├── google_vision_key.json
├── azure_config.json
└── aws_credentials.json
```

## Rate Limits and Quotas

| Engine | Free Tier Limit | Rate Limit | Notes |
|--------|----------------|------------|-------|
| Tesseract | Unlimited | Local processing | No network required |
| EasyOCR | Unlimited | Local processing | GPU recommended |
| PaddleOCR | Unlimited | Local processing | Good for batch |
| Google Vision | 1,000/month | 1,800/min | Excellent accuracy |
| Azure Vision | 5,000/month | 20/min (free) | Good value |
| AWS Textract | 1,000/month | 5/sec | Limited Telugu |
| ABBYY | Varies | API limits | High accuracy |
| Nanonets | Varies | API limits | Requires training |
| Mathpix | 1,000/month | API limits | Math focused |

## Cost Analysis

### Cost per 1,000 Pages (USD)

| Engine | Cost | Telugu Support | Accuracy |
|--------|------|----------------|----------|
| Tesseract | $0.00 | Excellent | Good |
| EasyOCR | $0.00 | Excellent | Excellent |
| PaddleOCR | $0.00 | Good | Good |
| Google Vision | $1.50 | Excellent | Excellent |
| Azure Vision | $1.00 | Good | Good |
| AWS Textract | $1.50 | Limited | Good |
| ABBYY | $50.00 | Excellent | Excellent |
| Nanonets | $20.00 | Good* | Good* |
| Mathpix | $4.00 | Poor | Good |

*Depends on model training quality

### Recommendations by Use Case

**Budget-conscious (Free):**
- Primary: EasyOCR
- Backup: Tesseract

**High Accuracy (Paid):**
- Primary: ABBYY Cloud OCR
- Backup: Google Vision

**Balanced (Mixed):**
- Primary: EasyOCR (free)
- Secondary: Google Vision (paid)

## Troubleshooting

### Common Issues

1. **Authentication Errors:**
   ```bash
   # Check environment variables
   echo $GOOGLE_APPLICATION_CREDENTIALS
   echo $AZURE_VISION_KEY
   
   # Verify file permissions
   ls -la credentials/
   ```

2. **Rate Limit Exceeded:**
   - Implement retry logic with exponential backoff
   - Use multiple API keys if allowed
   - Switch to local engines for high volume

3. **API Quota Exceeded:**
   - Monitor usage in cloud consoles
   - Set up billing alerts
   - Implement usage tracking

4. **Network Issues:**
   ```bash
   # Test connectivity
   curl -I https://vision.googleapis.com
   curl -I https://api.cognitive.microsoft.com
   ```

5. **Model Download Failures:**
   ```bash
   # Clear cache and retry
   rm -rf ~/.cache/torch/hub/
   rm -rf ~/.EasyOCR/
   ```

### Performance Optimization

1. **Batch Processing:**
   - Process multiple pages together
   - Use async processing where available

2. **Image Preprocessing:**
   - Resize images appropriately
   - Enhance contrast and reduce noise
   - Convert to optimal formats

3. **Engine Selection:**
   - Use free engines for initial processing
   - Use paid engines for verification
   - Combine results from multiple engines

4. **Caching:**
   - Cache results to avoid reprocessing
   - Store intermediate results

### Monitoring and Logging

1. **API Usage Tracking:**
   ```python
   # Track API calls and costs
   from telugu_ocr.utils.logging_config import get_logger_config
   
   logger = get_logger_config().get_engine_logger()
   logger.info(f"API call: {engine_name}, cost: ${cost}")
   ```

2. **Error Monitoring:**
   ```python
   # Monitor API errors
   try:
       result = engine.extract_text(image)
   except APILimitExceededException as e:
       logger.warning(f"Rate limit exceeded: {e}")
   except EngineNotAvailableException as e:
       logger.error(f"Engine unavailable: {e}")
   ```

3. **Performance Metrics:**
   - Track processing times
   - Monitor accuracy rates
   - Analyze cost per page

For additional support, check the main documentation or open an issue in the repository.