# Telugu OCR System - Installation Guide

This guide provides step-by-step instructions for setting up the Telugu OCR System on different platforms.

## Quick Start (Recommended)

### Option 1: Automated Setup with Conda

1. **Install Conda** (if not already installed):
   - Download Miniconda: https://docs.conda.io/en/latest/miniconda.html
   - Or Anaconda: https://www.anaconda.com/products/distribution

2. **Clone/Download the project** and navigate to the directory

3. **Run the automated setup**:
   ```bash
   python setup_environment.py
   ```

4. **Activate the environment**:
   ```bash
   conda activate telugu_ocr
   ```

5. **Test the installation**:
   ```bash
   python -m telugu_ocr test
   ```

### Option 2: Manual Conda Setup

1. **Create environment from file**:
   ```bash
   conda env create -f environment.yml
   ```

2. **Activate environment**:
   ```bash
   conda activate telugu_ocr
   ```

3. **Test installation**:
   ```bash
   python -m telugu_ocr test
   ```

### Option 3: Pip Installation

If you prefer pip or don't have conda:

1. **Create virtual environment** (recommended):
   ```bash
   python -m venv telugu_ocr_env
   source telugu_ocr_env/bin/activate  # On Windows: telugu_ocr_env\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install system dependencies** (see platform-specific sections below)

## Platform-Specific Instructions

### macOS

#### Prerequisites
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install system dependencies
brew install tesseract tesseract-lang
brew install poppler
```

#### Verify Tesseract Telugu Support
```bash
tesseract --list-langs | grep tel
```

### Linux (Ubuntu/Debian)

#### Prerequisites
```bash
# Update package list
sudo apt-get update

# Install Tesseract with Telugu support
sudo apt-get install tesseract-ocr tesseract-ocr-tel

# Install Poppler for PDF processing
sudo apt-get install poppler-utils

# Install OpenGL libraries (for OpenCV)
sudo apt-get install libgl1-mesa-glx

# Optional: Install additional language packs
sudo apt-get install tesseract-ocr-eng tesseract-ocr-hin
```

### Windows

#### Prerequisites
1. **Install Tesseract**:
   - Download from: https://github.com/UB-Mannheim/tesseract/wiki
   - During installation, make sure to select Telugu language pack
   - Add Tesseract to your PATH environment variable

2. **Install Poppler**:
   - Download from: https://blog.alivate.com.au/poppler-windows/
   - Extract and add to PATH environment variable

3. **Verify installation**:
   ```cmd
   tesseract --version
   tesseract --list-langs
   pdftoppm -h
   ```

## GPU Support (Optional)

For faster processing with EasyOCR and PaddleOCR:

### NVIDIA GPU with CUDA

1. **Check CUDA version**:
   ```bash
   nvidia-smi
   ```

2. **Install PyTorch with CUDA** (replace cu118 with your CUDA version):
   ```bash
   # For CUDA 11.8
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   
   # For CUDA 12.1
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
   ```

3. **Update engine configuration**:
   Edit `config/engines.yaml` and set `gpu: true` for supported engines.

## Verification

### Test OCR Engines
```bash
python -m telugu_ocr test
```

Expected output should show available engines:
```
Testing OCR engines...
Testing tesseract       ✅ AVAILABLE (📦 LOCAL)
Testing easyocr         ✅ AVAILABLE (📦 LOCAL)
...
```

### Test with Sample PDF
```bash
python -m telugu_ocr process sample.pdf
```

### List Available Engines
```bash
python -m telugu_ocr list-engines
```

## Troubleshooting

### Common Issues

#### 1. Tesseract not found
```bash
# Check if tesseract is in PATH
tesseract --version

# If not found, add to PATH or reinstall
```

#### 2. Telugu language not available
```bash
# Check available languages
tesseract --list-langs

# If 'tel' not listed, install Telugu language pack
```

#### 3. PDF processing fails
```bash
# Check if poppler is installed
pdftoppm -h

# Install poppler if missing
```

#### 4. EasyOCR fails to initialize
```bash
# Check PyTorch installation
python -c "import torch; print(torch.__version__)"

# Reinstall if needed
pip install torch torchvision
```

#### 5. Permission errors on macOS/Linux
```bash
# Make sure you have write permissions
chmod +x setup_environment.py
```

### Getting Help

1. **Check logs**: Look in the `logs/` directory for detailed error messages
2. **Test individual engines**: Use `python -m telugu_ocr test --engines tesseract`
3. **Check configuration**: Verify `config/engines.yaml` settings
4. **System resources**: Ensure sufficient RAM (4GB minimum, 8GB recommended)

## Cloud OCR APIs (Optional)

To use cloud-based OCR services, you'll need API keys:

### Google Cloud Vision
1. Create a Google Cloud project
2. Enable Vision API
3. Create service account and download JSON key
4. Set environment variable: `export GOOGLE_APPLICATION_CREDENTIALS=path/to/key.json`

### Azure Computer Vision
1. Create Azure Cognitive Services resource
2. Get subscription key and endpoint
3. Set in `config/engines.yaml` or environment variables

### AWS Textract
1. Create AWS account and IAM user
2. Get access key and secret key
3. Set AWS credentials via AWS CLI or environment variables

See `docs/QUICK_START_API_SETUP.md` for detailed API setup instructions.

## System Requirements

### Minimum
- **OS**: Windows 10, macOS 10.14, Ubuntu 18.04 or newer
- **RAM**: 4GB
- **Storage**: 2GB free space
- **Python**: 3.8 or newer

### Recommended
- **RAM**: 8GB or more
- **Storage**: 5GB free space (for models and cache)
- **CPU**: Multi-core processor
- **GPU**: NVIDIA GPU with CUDA support (optional, for faster processing)

## Next Steps

After successful installation:

1. **Configure engines**: Edit `config/engines.yaml` to enable/disable specific OCR engines
2. **Set up API keys**: Add cloud OCR service credentials if needed
3. **Process documents**: Start with `python -m telugu_ocr process your_document.pdf`
4. **Explore features**: Try different output formats and quality assessment tools

For more information, see the main README.md and documentation in the `docs/` directory.