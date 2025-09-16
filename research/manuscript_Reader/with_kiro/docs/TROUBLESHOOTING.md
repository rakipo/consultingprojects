# Troubleshooting Guide

This guide helps you resolve common issues with the Telugu Document OCR system.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [OCR Engine Problems](#ocr-engine-problems)
3. [API Authentication Issues](#api-authentication-issues)
4. [Processing Errors](#processing-errors)
5. [Quality Issues](#quality-issues)
6. [Performance Problems](#performance-problems)
7. [Output Issues](#output-issues)
8. [System Requirements](#system-requirements)

## Installation Issues

### Python Dependencies

**Problem:** `pip install` fails with dependency conflicts
```bash
ERROR: Could not find a version that satisfies the requirement...
```

**Solution:**
```bash
# Create a virtual environment
python -m venv telugu_ocr_env
source telugu_ocr_env/bin/activate  # Linux/macOS
# or
telugu_ocr_env\Scripts\activate  # Windows

# Upgrade pip
pip install --upgrade pip

# Install dependencies one by one if needed
pip install pillow opencv-python pdf2image
pip install pytesseract easyocr paddleocr
```

### System Dependencies

**Problem:** Tesseract not found
```
TesseractNotFoundError: tesseract is not installed
```

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-tel

# macOS
brew install tesseract tesseract-lang

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
# Add to PATH environment variable
```

**Problem:** PDF conversion fails
```
PDFInfoNotInstalledError: Unable to get page count
```

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install poppler-utils

# macOS
brew install poppler

# Windows
# Download poppler from: https://blog.alivate.com.au/poppler-windows/
# Add to PATH
```

**Problem:** OpenCV import error
```
ImportError: libGL.so.1: cannot open shared object file
```

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install libgl1-mesa-glx libglib2.0-0

# Alternative: Use headless OpenCV
pip uninstall opencv-python
pip install opencv-python-headless
```

## OCR Engine Problems

### Tesseract Issues

**Problem:** Telugu language not available
```bash
tesseract --list-langs
# 'tel' not in the list
```

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr-tel

# macOS
brew install tesseract-lang

# Verify installation
tesseract --list-langs | grep tel
```

**Problem:** Poor Tesseract accuracy
**Solution:**
1. Check image quality and preprocessing
2. Try different PSM (Page Segmentation Mode) values:
   ```yaml
   tesseract:
     config: "--psm 3"  # Try values 3, 6, 8, 11, 13
   ```
3. Adjust OCR Engine Mode (OEM):
   ```yaml
   tesseract:
     config: "--psm 6 --oem 3"  # Try OEM values 0, 1, 2, 3
   ```

### EasyOCR Issues

**Problem:** Model download fails
```
URLError: <urlopen error [Errno -3] Temporary failure in name resolution>
```

**Solution:**
1. Check internet connection
2. Clear cache and retry:
   ```bash
   rm -rf ~/.EasyOCR/
   python -c "import easyocr; reader = easyocr.Reader(['te', 'en'])"
   ```
3. Manual model download:
   ```python
   import easyocr
   reader = easyocr.Reader(['te', 'en'], download_enabled=True)
   ```

**Problem:** CUDA out of memory (GPU)
```
RuntimeError: CUDA out of memory
```

**Solution:**
```yaml
# Disable GPU in configuration
easyocr:
  gpu: false
```

### PaddleOCR Issues

**Problem:** Model download timeout
**Solution:**
1. Set longer timeout:
   ```python
   import os
   os.environ['PADDLEOCR_TIMEOUT'] = '300'  # 5 minutes
   ```
2. Manual model download from PaddleOCR GitHub releases

**Problem:** Angle classification errors
**Solution:**
```yaml
paddleocr:
  use_angle_cls: false  # Disable angle classification
```

## API Authentication Issues

### Google Cloud Vision

**Problem:** Authentication failed
```
google.auth.exceptions.DefaultCredentialsError: Could not automatically determine credentials
```

**Solution:**
1. Check credentials file path:
   ```bash
   ls -la $GOOGLE_APPLICATION_CREDENTIALS
   ```
2. Verify JSON format:
   ```bash
   python -c "import json; json.load(open('path/to/credentials.json'))"
   ```
3. Test authentication:
   ```python
   from google.cloud import vision
   client = vision.ImageAnnotatorClient()
   ```

**Problem:** API not enabled
```
google.api_core.exceptions.Forbidden: Cloud Vision API has not been used
```

**Solution:**
1. Go to Google Cloud Console
2. Enable the Cloud Vision API
3. Wait a few minutes for activation

### Azure Computer Vision

**Problem:** Invalid subscription key
```
ComputerVisionErrorException: Access denied due to invalid subscription key
```

**Solution:**
1. Verify key in Azure portal
2. Check environment variable:
   ```bash
   echo $AZURE_VISION_KEY
   ```
3. Ensure key matches the region

**Problem:** Endpoint URL incorrect
```
requests.exceptions.ConnectionError: Failed to establish a new connection
```

**Solution:**
1. Check endpoint format:
   ```
   https://your-resource-name.cognitiveservices.azure.com/
   ```
2. Verify region matches your resource

### AWS Textract

**Problem:** Credentials not found
```
botocore.exceptions.NoCredentialsError: Unable to locate credentials
```

**Solution:**
1. Set environment variables:
   ```bash
   export AWS_ACCESS_KEY_ID="your_key"
   export AWS_SECRET_ACCESS_KEY="your_secret"
   ```
2. Or configure AWS CLI:
   ```bash
   aws configure
   ```
3. Or use IAM roles (on EC2)

## Processing Errors

### PDF Processing

**Problem:** PDF file corrupted or encrypted
```
PDFSyntaxError: No /Root object! - Is this really a PDF?
```

**Solution:**
1. Verify PDF file integrity
2. Try with a different PDF
3. Decrypt password-protected PDFs first
4. Convert to images manually:
   ```bash
   pdftoppm -png input.pdf output
   ```

**Problem:** Memory error with large PDFs
```
MemoryError: Unable to allocate array
```

**Solution:**
1. Process pages individually:
   ```python
   # Set max pages per batch
   ocr_system.process_pdf("large.pdf", max_pages_per_batch=5)
   ```
2. Reduce image resolution:
   ```yaml
   preprocessing:
     resize_factor: 1.0  # Reduce from 2.0
   ```
3. Increase system memory or use swap

### Image Processing

**Problem:** Image format not supported
```
PIL.UnidentifiedImageError: cannot identify image file
```

**Solution:**
1. Convert to supported format (PNG, JPEG)
2. Check file corruption
3. Use different image processing library

**Problem:** Image too large
```
PIL.Image.DecompressionBombError: Image size exceeds limit
```

**Solution:**
```python
from PIL import Image
Image.MAX_IMAGE_PIXELS = None  # Remove limit (use carefully)
```

## Quality Issues

### Poor OCR Accuracy

**Problem:** Low confidence scores across all engines

**Diagnosis:**
1. Check image quality:
   ```python
   from telugu_ocr.processors import ImagePreprocessor
   preprocessor = ImagePreprocessor()
   # Save debug images to inspect quality
   preprocessor.save_debug_images(images, "debug/")
   ```

**Solutions:**
1. Improve image preprocessing:
   ```yaml
   preprocessing:
     resize_factor: 3.0  # Increase resolution
     noise_reduction: true
     contrast_enhancement: true
     deskew: true
     binarization: true
   ```

2. Try different engines:
   ```python
   # Test with multiple engines
   best_engines = ['easyocr', 'google_vision', 'abbyy']
   ```

3. Manual image enhancement:
   - Scan at higher DPI (300+ recommended)
   - Ensure good lighting
   - Avoid shadows and reflections
   - Use high contrast settings

### Telugu Script Issues

**Problem:** Low Telugu detection rate

**Solutions:**
1. Use engines with better Telugu support:
   - EasyOCR (recommended)
   - Google Vision API
   - ABBYY Cloud OCR

2. Check font and script quality:
   - Ensure clear, readable Telugu text
   - Avoid decorative or stylized fonts
   - Check for proper Unicode encoding

3. Preprocessing for Telugu:
   ```yaml
   preprocessing:
     telugu_specific: true
     font_enhancement: true
   ```

### Table Structure Issues

**Problem:** Table structure not preserved

**Solutions:**
1. Use engines with table detection:
   - AWS Textract
   - ABBYY Cloud OCR
   - Azure Form Recognizer

2. Preprocessing for tables:
   ```yaml
   preprocessing:
     table_detection: true
     line_enhancement: true
   ```

3. Post-processing:
   - Manual table structure correction
   - Use specialized table extraction tools

## Performance Problems

### Slow Processing

**Problem:** Very slow OCR processing

**Solutions:**
1. Enable GPU acceleration:
   ```yaml
   easyocr:
     gpu: true
   paddleocr:
     use_gpu: true
   ```

2. Optimize image size:
   ```yaml
   preprocessing:
     resize_factor: 1.5  # Reduce from 2.0
     max_image_size: 2048  # Limit maximum dimension
   ```

3. Use faster engines for initial processing:
   - Tesseract (fastest)
   - EasyOCR (good balance)

4. Parallel processing:
   ```python
   ocr_manager = OCRManager(max_concurrent=2)
   ```

### Memory Issues

**Problem:** Out of memory errors

**Solutions:**
1. Process pages individually:
   ```python
   for page in pages:
       result = process_single_page(page)
   ```

2. Reduce image resolution:
   ```yaml
   preprocessing:
     resize_factor: 1.0
     max_image_size: 1024
   ```

3. Clear cache regularly:
   ```python
   import gc
   gc.collect()
   ```

### API Rate Limits

**Problem:** API rate limit exceeded

**Solutions:**
1. Implement retry with backoff:
   ```python
   import time
   import random
   
   def retry_with_backoff(func, max_retries=3):
       for attempt in range(max_retries):
           try:
               return func()
           except APILimitExceededException:
               wait_time = (2 ** attempt) + random.uniform(0, 1)
               time.sleep(wait_time)
   ```

2. Use multiple API keys:
   ```python
   api_keys = ['key1', 'key2', 'key3']
   current_key_index = 0
   ```

3. Switch to local engines:
   ```python
   fallback_engines = ['tesseract', 'easyocr']
   ```

## Output Issues

### File Generation Problems

**Problem:** Permission denied when saving files
```
PermissionError: [Errno 13] Permission denied: 'output/...'
```

**Solution:**
1. Check directory permissions:
   ```bash
   ls -la output/
   chmod 755 output/
   ```

2. Run with appropriate permissions
3. Change output directory:
   ```python
   output_manager = OutputManager(base_output_dir="/tmp/ocr_output")
   ```

**Problem:** CSV encoding issues with Telugu text
```
UnicodeEncodeError: 'ascii' codec can't encode character
```

**Solution:**
1. Ensure UTF-8 encoding:
   ```python
   with open(file_path, 'w', encoding='utf-8') as f:
       writer = csv.writer(f)
   ```

2. Set system locale:
   ```bash
   export LC_ALL=en_US.UTF-8
   export LANG=en_US.UTF-8
   ```

### Report Generation Issues

**Problem:** Matplotlib display issues
```
UserWarning: Matplotlib is currently using agg, which is a non-GUI backend
```

**Solution:**
1. Install GUI backend:
   ```bash
   pip install tkinter  # Linux
   # or
   pip install PyQt5
   ```

2. Use non-interactive backend:
   ```python
   import matplotlib
   matplotlib.use('Agg')
   ```

## System Requirements

### Minimum Requirements
- Python 3.7+
- 4GB RAM
- 2GB free disk space
- Internet connection (for cloud APIs and model downloads)

### Recommended Requirements
- Python 3.9+
- 8GB RAM
- 5GB free disk space
- GPU with CUDA support (for acceleration)
- SSD storage (for faster I/O)

### Platform-Specific Notes

**Linux (Ubuntu/Debian):**
- Install system packages with apt-get
- Use virtual environments
- Consider Docker for isolation

**macOS:**
- Use Homebrew for system dependencies
- May need Xcode command line tools
- M1/M2 Macs: Use compatible PyTorch versions

**Windows:**
- Use Windows Subsystem for Linux (WSL) if possible
- Install Visual C++ Build Tools for some packages
- Use Anaconda for easier dependency management

## Getting Help

### Log Files
Check log files for detailed error information:
```
logs/
├── ocr_processing.log
├── engine_performance.log
├── errors.log
└── quality_assessment.log
```

### Debug Mode
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### System Information
Collect system information for bug reports:
```python
import sys
import platform
print(f"Python: {sys.version}")
print(f"Platform: {platform.platform()}")
print(f"Architecture: {platform.architecture()}")
```

### Common Commands for Diagnosis
```bash
# Check Python environment
python --version
pip list | grep -E "(tesseract|easyocr|paddleocr|opencv|pillow)"

# Check system dependencies
tesseract --version
tesseract --list-langs

# Check GPU availability
python -c "import torch; print(torch.cuda.is_available())"

# Test basic functionality
python -c "from telugu_ocr import TeluguOCRSystem; print('Import successful')"
```

If you continue to experience issues after following this guide, please:
1. Check the GitHub issues page
2. Create a new issue with:
   - Error messages
   - System information
   - Steps to reproduce
   - Log files (if relevant)