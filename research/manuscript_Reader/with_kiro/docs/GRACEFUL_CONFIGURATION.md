# Graceful Configuration Guide

The Telugu OCR system is designed to work gracefully with partial configuration - you don't need all API keys to get started!

## 🎯 Core Principle

**Local engines always run (if dependencies installed) + API engines run only if keys are configured**

## 🚀 Getting Started (No API Keys Required)

### Step 1: Install Local Engines

```bash
# Install the most important local engines
pip install easyocr pytesseract

# System dependencies for Tesseract (Ubuntu/Debian)
sudo apt-get install tesseract-ocr tesseract-ocr-tel

# System dependencies for Tesseract (macOS)
brew install tesseract tesseract-lang
```

### Step 2: Test Your Setup

```bash
# Test what's available
python -m telugu_ocr test

# Should show something like:
# Testing tesseract      ✅ AVAILABLE (📦 LOCAL)
# Testing easyocr        ✅ AVAILABLE (📦 LOCAL)
# Testing google_vision  ⚠️  NOT CONFIGURED (🌐 API) - No API keys
```

### Step 3: Process Documents

```bash
# This works immediately with local engines
python -m telugu_ocr process your_document.pdf

# Output will show:
# ✅ Using all available engines (2 total):
#    📦 Local: tesseract, easyocr
#    💡 Configure API keys in config/engines.yaml for cloud OCR engines
```

## 📈 Gradual Enhancement

### Add One API Engine

Pick the best API engine for Telugu and configure just that one:

```yaml
# config/engines.yaml - Add just Google Vision
engines:
  # Local engines (already working)
  tesseract:
    enabled: true
  easyocr:
    enabled: true
    
  # Add one API engine
  google_vision:
    enabled: true
    api_key_path: "/path/to/your/google_key.json"
    
  # Leave others unconfigured - they'll be skipped gracefully
  azure_vision:
    enabled: false
```

Now you'll get:
```bash
✅ Using all available engines (3 total):
   📦 Local: tesseract, easyocr
   🌐 API: google_vision
```

### Add More Over Time

Configure additional APIs as needed:

```yaml
# Add Azure for cost-effective cloud OCR
azure_vision:
  enabled: true
  subscription_key: "your_azure_key"
  endpoint: "https://your-resource.cognitiveservices.azure.com/"
```

## 🔍 Understanding Engine Status

### Engine Categories

| Type | Examples | Behavior |
|------|----------|----------|
| **Local** | tesseract, easyocr, paddleocr, trocr | Always attempt to run if Python packages installed |
| **API** | google_vision, azure_vision, aws_textract, abbyy, nanonets, mathpix | Only run if valid API keys configured |

### Status Messages

| Message | Meaning | Action |
|---------|---------|--------|
| `✅ AVAILABLE (📦 LOCAL)` | Local engine ready | None needed |
| `❌ NOT AVAILABLE (📦 LOCAL)` | Missing Python package | `pip install package_name` |
| `✅ AVAILABLE (🌐 API)` | API engine configured | None needed |
| `⚠️ NOT CONFIGURED (🌐 API)` | No API keys | Configure in `engines.yaml` or skip |

## 🎛️ Configuration Strategies

### Strategy 1: Free Only
```yaml
engines:
  tesseract:
    enabled: true
  easyocr:
    enabled: true
  paddleocr:
    enabled: true
  # All API engines disabled or unconfigured
```

**Result**: Fast, free processing with good Telugu support

### Strategy 2: Best Accuracy
```yaml
engines:
  easyocr:
    enabled: true
  google_vision:
    enabled: true
    api_key_path: "/path/to/google_key.json"
  abbyy:
    enabled: true
    api_key_path: "your_abbyy_key"
```

**Result**: Highest accuracy for Telugu text

### Strategy 3: Cost-Effective
```yaml
engines:
  tesseract:
    enabled: true
  easyocr:
    enabled: true
  azure_vision:  # Cheapest API option
    enabled: true
    subscription_key: "your_azure_key"
    endpoint: "your_endpoint"
```

**Result**: Good balance of free + affordable cloud processing

## 🔧 Troubleshooting

### "No OCR engines are available"

**Cause**: No local engines installed AND no API keys configured

**Solution**:
```bash
# Quick fix - install local engines
pip install easyocr pytesseract

# Test again
python -m telugu_ocr test
```

### "Only local engines available"

**Cause**: API engines not configured (this is normal!)

**Options**:
1. **Continue with local engines** - they work great for most documents
2. **Add API engines** - configure keys in `engines.yaml` for better accuracy

### "API engine authentication failed"

**Cause**: Invalid API keys or network issues

**Behavior**: Engine is skipped, processing continues with other engines

**Solution**: Check API key configuration or skip that engine

## 💡 Best Practices

### 1. Start Simple
- Begin with just local engines
- Add API engines gradually as needed
- Don't configure all APIs at once

### 2. Test Incrementally
```bash
# After each change, test what's available
python -m telugu_ocr test

# Process a small test document
python -m telugu_ocr process test.pdf
```

### 3. Monitor Usage
- Check which engines give best results for your documents
- Disable unused engines to speed up processing
- Monitor API costs if using paid services

### 4. Keep Backups
- Always have at least one local engine working
- Don't rely solely on API engines
- Keep multiple API options configured for redundancy

## 🎉 Benefits of Graceful Handling

1. **No Setup Friction**: Works immediately with minimal configuration
2. **Incremental Enhancement**: Add engines as needed
3. **Fault Tolerance**: Failed engines don't break the system
4. **Cost Control**: Only pay for APIs you actually configure
5. **Flexibility**: Easy to enable/disable engines for different use cases

## 📞 Getting Help

```bash
# Check what's working
python example_graceful_handling.py

# Test your setup
python test_api_keys.py

# Interactive configuration
python setup_credentials_template.py
```

The system is designed to be helpful and informative about what's available and what's missing, so you can make informed decisions about which engines to configure based on your needs and budget.