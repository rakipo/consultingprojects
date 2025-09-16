# Quick Start: API Setup Guide

This is a condensed guide to get you started quickly with the most important OCR APIs for Telugu documents.

## 🚀 Recommended Setup (5 minutes)

For the best Telugu OCR results, set up these **2 essential APIs**:

### 1. Google Cloud Vision API (Best Telugu Support)

**Why**: Excellent Telugu recognition, free tier available

**Quick Setup:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project → Enable Vision API → Create Service Account
3. Download JSON key file
4. Save as `credentials/google_vision_key.json`

```yaml
# config/engines.yaml
google_vision:
  enabled: true
  api_key_path: "/absolute/path/to/google_vision_credentials.json"
```

### 2. Azure Computer Vision (Good Backup)

**Why**: Good Telugu support, cost-effective

**Quick Setup:**
1. Go to [Azure Portal](https://portal.azure.com/)
2. Create Computer Vision resource
3. Copy subscription key and endpoint

```yaml
# config/engines.yaml
azure_vision:
  enabled: true
  subscription_key: "your_subscription_key"
  endpoint: "https://your-resource.cognitiveservices.azure.com/"
```

## 🛠️ Automated Setup

Use our interactive setup script:

```bash
python setup_credentials_template.py
```

This will guide you through the entire process step-by-step.

## 🧪 Test Your Setup

```bash
# Test all configurations
python test_api_keys.py

# Test OCR engines
python -m telugu_ocr test

# Process a document
python -m telugu_ocr process your_document.pdf
```

## 📊 API Comparison for Telugu

| API | Telugu Support | Cost | Setup Time | Recommended |
|-----|----------------|------|------------|-------------|
| **Google Vision** | ⭐⭐⭐⭐⭐ | $1.50/1K | 5 min | ✅ **YES** |
| **Azure Vision** | ⭐⭐⭐⭐ | $1.00/1K | 3 min | ✅ **YES** |
| **EasyOCR** | ⭐⭐⭐⭐⭐ | Free | 1 min | ✅ **YES** |
| **Tesseract** | ⭐⭐⭐ | Free | 2 min | ✅ **YES** |
| AWS Textract | ⭐⭐ | $1.50/1K | 5 min | ⚠️ Limited |
| ABBYY Cloud | ⭐⭐⭐⭐⭐ | $50/1K | 10 min | 💰 Premium |

## 🎯 Minimal Setup (Free Only)

If you want to start with free engines only:

```bash
# Install system dependencies
sudo apt-get install tesseract-ocr tesseract-ocr-tel  # Ubuntu
brew install tesseract tesseract-lang                 # macOS

# Install Python packages
pip install easyocr paddleocr

# Test
python -m telugu_ocr test --engines tesseract easyocr
```

## 🔧 Configuration Files

### Configuration Method: engines.yaml file
```yaml
# config/engines.yaml
engines:
  google_vision:
    enabled: true
    api_key_path: "/absolute/path/to/google_vision_credentials.json"
  
  azure_vision:
    enabled: true
    subscription_key: "your_azure_key"
    endpoint: "https://your-resource.cognitiveservices.azure.com/"
```

### Template Usage
```bash
# Copy template and edit
cp config/engines_template.yaml config/engines.yaml
nano config/engines.yaml

# Or use interactive setup
python setup_credentials_template.py
```

## 🚨 Security Checklist

- [ ] Add `credentials/` to `.gitignore`
- [ ] Never commit API keys to version control
- [ ] Use environment variables in production
- [ ] Set up billing alerts for cloud APIs
- [ ] Rotate keys every 90 days

## 🆘 Quick Troubleshooting

**Problem**: `google.auth.exceptions.DefaultCredentialsError`
**Solution**: Check if `GOOGLE_APPLICATION_CREDENTIALS` points to valid JSON file

**Problem**: `Azure authentication failed`
**Solution**: Verify subscription key and endpoint URL match your resource

**Problem**: `Tesseract not found`
**Solution**: Install Tesseract: `sudo apt-get install tesseract-ocr tesseract-ocr-tel`

**Problem**: `No OCR engines available`
**Solution**: Run `python -m telugu_ocr list-engines` to check configuration

## 📞 Need Help?

1. **Full Documentation**: [docs/API_KEYS_SETUP.md](API_KEYS_SETUP.md)
2. **Troubleshooting**: [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md)
3. **Test Script**: `python test_api_keys.py`
4. **Interactive Setup**: `python setup_credentials_template.py`

## 🎉 Ready to Go!

Once you have at least one API configured:

```bash
# Process your Telugu document
python -m telugu_ocr process test_manu.pdf

# Check results in output/ directory
ls output/

# Generate comparison report
python -m telugu_ocr report output/latest_timestamp/
```

**Estimated setup time**: 5-15 minutes depending on APIs chosen.

**Recommended for beginners**: Start with Google Vision + EasyOCR for best results.