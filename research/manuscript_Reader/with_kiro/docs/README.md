# Telugu Document OCR System

A comprehensive OCR system for extracting text from Telugu documents with support for multiple OCR engines, quality assessment, and detailed reporting.

## Features

- **Multiple OCR Engines**: Support for 9+ OCR engines including free, cloud-based, and premium options
- **Telugu Language Support**: Optimized for Telugu script recognition
- **Quality Assessment**: Automated quality evaluation with improvement recommendations
- **Multiple Output Formats**: CSV, Excel, text, and JSON outputs
- **Comprehensive Reporting**: Performance comparison and accuracy analysis
- **Manual Evaluation**: Tools for manual accuracy assessment and feedback collection
- **Organized Output**: Timestamped directory structure with method-specific organization

## Supported OCR Engines

### Free/Open Source
- **Tesseract OCR**: With Telugu language pack
- **EasyOCR**: Excellent Telugu support out of the box
- **PaddleOCR**: Multi-language including Telugu
- **TrOCR**: Transformer-based OCR (limited Telugu support)

### Cloud-based (Free Tier Available)
- **Google Cloud Vision API**: Excellent Telugu support
- **Azure Computer Vision**: Good Telugu support
- **AWS Textract**: Limited Telugu support

### Premium/Paid
- **ABBYY Cloud OCR**: High accuracy for complex documents
- **Nanonets OCR**: Specialized for handwritten text (requires training)
- **Mathpix OCR**: Good for structured documents (limited Telugu support)

## Installation

### Prerequisites

```bash
# Python 3.7 or higher
python --version

# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-tel
sudo apt-get install poppler-utils  # For PDF processing
sudo apt-get install libgl1-mesa-glx  # For OpenCV

# macOS
brew install tesseract tesseract-lang
brew install poppler
```

### Python Dependencies

```bash
# Clone the repository
git clone <repository-url>
cd telugu-document-ocr

# Install Python dependencies
pip install -r requirements.txt
```

### Requirements.txt
```
# Core dependencies
pillow>=9.0.0
opencv-python>=4.5.0
pdf2image>=3.1.0
numpy>=1.21.0
pandas>=1.3.0
pyyaml>=6.0

# OCR engines
pytesseract>=0.3.10
easyocr>=1.6.0
paddleocr>=2.6.0
transformers>=4.20.0
torch>=1.12.0

# Cloud APIs
google-cloud-vision>=3.0.0
azure-cognitiveservices-vision-computervision>=0.9.0
boto3>=1.24.0

# Premium APIs
requests>=2.28.0

# Quality assessment
nltk>=3.7
python-Levenshtein>=0.12.2

# Output formats
openpyxl>=3.0.10
python-docx>=0.8.11

# Visualization
matplotlib>=3.5.0
seaborn>=0.11.0

# Utilities
tqdm>=4.64.0
```

## Quick Start

### Basic Usage

```python
from telugu_ocr import TeluguOCRSystem

# Initialize the OCR system
ocr_system = TeluguOCRSystem()

# Process a PDF document
# System will automatically use all available engines
# (local engines + any configured API engines)
results = ocr_system.process_pdf("path/to/your/document.pdf")

# Results will be saved to output/<timestamp>/ directory
print(f"Processing complete. Results saved to: {results['output_directory']}")
```

### Graceful API Key Handling

The system automatically handles missing API keys:

- **Local Engines** (Tesseract, EasyOCR, PaddleOCR, TrOCR): Always attempt to run if dependencies are installed
- **API Engines** (Google Vision, Azure, AWS, etc.): Only run if valid API keys are configured
- **No Failures**: Missing API keys don't cause crashes - engines are simply skipped

```python
# This works even with no API keys configured
# Will use available local engines only
ocr_system = TeluguOCRSystem()
results = ocr_system.process_pdf("document.pdf")
```

### Command Line Usage

```bash
# Process a single PDF with all available engines
# Automatically uses local engines + any configured API engines
python -m telugu_ocr process document.pdf

# Process with specific engines only
python -m telugu_ocr process document.pdf --engines tesseract easyocr

# Test which engines are available
python -m telugu_ocr test

# List all configured engines
python -m telugu_ocr list-engines

# Generate evaluation forms for manual review
python -m telugu_ocr evaluate document.pdf --create-forms

# Generate comparison report
python -m telugu_ocr report output/2024-01-15_14-30-25/
```

## Configuration

### Engine Configuration

Edit `config/engines.yaml` to enable/disable engines and set parameters:

```yaml
engines:
  tesseract:
    enabled: true
    language: "tel"
    config: "--psm 6"
    
  easyocr:
    enabled: true
    languages: ["te", "en"]
    gpu: false
    
  google_vision:
    enabled: false  # Set to true and configure credentials
    api_key_path: "credentials/google_vision_key.json"
```

### Processing Configuration

Edit `config/processing.yaml` for preprocessing and output settings:

```yaml
preprocessing:
  resize_factor: 2.0
  noise_reduction: true
  contrast_enhancement: true
  
output:
  formats: ["csv", "xlsx", "txt"]
  include_confidence: true
  
quality:
  minimum_confidence: 0.6
  telugu_detection_threshold: 0.7
```

## API Keys and Authentication

### Google Cloud Vision
1. Create a Google Cloud project
2. Enable the Vision API
3. Create a service account and download the JSON key
4. Set the path in `config/engines.yaml` or set environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/credentials.json"
   ```

### Azure Computer Vision
```bash
export AZURE_VISION_KEY="your_subscription_key"
export AZURE_VISION_ENDPOINT="your_endpoint_url"
```

### AWS Textract
```bash
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
```

### Premium APIs
```bash
export ABBYY_API_KEY="your_abbyy_key"
export NANONETS_API_KEY="your_nanonets_key"
export NANONETS_MODEL_ID="your_model_id"
export MATHPIX_APP_ID="your_app_id"
export MATHPIX_APP_KEY="your_app_key"
```

## Output Structure

```
output/
└── 2024-01-15_14-30-25/
    ├── tesseract/
    │   ├── page_001.csv
    │   ├── page_001.xlsx
    │   ├── page_002.csv
    │   ├── page_002.xlsx
    │   ├── consolidated_text.txt
    │   └── detailed_results.json
    ├── easyocr/
    │   └── ...
    ├── comparison_report.json
    ├── performance_dashboard.html
    └── evaluation_form.csv
```

## Manual Evaluation

The system generates evaluation forms for manual accuracy assessment:

1. **Evaluation CSV**: Side-by-side comparison for manual correction
2. **Feedback Forms**: Detailed evaluation with rating scales
3. **Quality Reports**: Automated quality assessment with recommendations

### Using Evaluation Forms

1. Process your document to generate results
2. Open the generated `evaluation_form.csv`
3. Fill in the correct text and accuracy ratings
4. Use the feedback to improve OCR settings

## Quality Assessment

The system provides automated quality assessment including:

- **Telugu Script Detection**: Percentage of Telugu characters recognized
- **Confidence Analysis**: OCR engine confidence score evaluation
- **Table Structure**: Preservation of table layouts
- **Error Analysis**: Character and word-level error detection
- **Improvement Recommendations**: Specific suggestions for better results

## Performance Comparison

Generate comprehensive comparison reports:

```python
from telugu_ocr.reporting import ComparisonReporter

reporter = ComparisonReporter()

# Generate HTML dashboard
dashboard_path = reporter.generate_performance_dashboard(all_results, quality_reports)

# Create detailed comparison report
report_path = reporter.create_detailed_comparison_report(all_results, quality_reports)

# Generate performance charts
chart_paths = reporter.generate_performance_charts(all_results, quality_reports)
```

## Troubleshooting

### Common Issues

1. **Tesseract not found**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr tesseract-ocr-tel
   
   # macOS
   brew install tesseract tesseract-lang
   ```

2. **Telugu language pack missing**
   ```bash
   # Check available languages
   tesseract --list-langs
   
   # Should include 'tel' for Telugu
   ```

3. **PDF conversion fails**
   ```bash
   # Install poppler
   sudo apt-get install poppler-utils  # Ubuntu/Debian
   brew install poppler  # macOS
   ```

4. **Cloud API authentication errors**
   - Verify API keys are correctly set
   - Check API quotas and billing
   - Ensure proper permissions are granted

### Performance Optimization

1. **Image Preprocessing**: Adjust preprocessing parameters in `config/processing.yaml`
2. **Engine Selection**: Use engines best suited for your document type
3. **Batch Processing**: Process multiple documents together for efficiency
4. **GPU Acceleration**: Enable GPU for supported engines (EasyOCR, PaddleOCR)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the documentation in the `docs/` directory
- Review the troubleshooting section
- Open an issue on the repository
- Check the logs in the `logs/` directory for detailed error information

## Acknowledgments

- Tesseract OCR team for the excellent OCR engine
- EasyOCR team for Telugu language support
- All the cloud providers for their OCR APIs
- The Telugu language community for feedback and testing