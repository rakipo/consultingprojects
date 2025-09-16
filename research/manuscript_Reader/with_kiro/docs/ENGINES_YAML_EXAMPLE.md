# Complete engines.yaml Configuration Example

This document shows a complete example of the `config/engines.yaml` file with all API keys configured.

## Complete Configuration Example

```yaml
# config/engines.yaml - Complete Configuration Example
# Copy this template and replace with your actual API keys

engines:
  # Free/Open Source Engines (No API keys required)
  tesseract:
    enabled: true
    language: "tel"
    config: "--psm 6"
    
  easyocr:
    enabled: true
    languages: ["te", "en"]
    gpu: false
    
  paddleocr:
    enabled: true
    language: "te"
    use_gpu: false
    
  trocr:
    enabled: false  # Limited Telugu support
    model_name: "microsoft/trocr-base-printed"
    
  # Cloud-based APIs (Replace with your actual keys)
  google_vision:
    enabled: true
    api_key_path: "/home/user/credentials/google_vision_key.json"
    
  azure_vision:
    enabled: true
    subscription_key: "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
    endpoint: "https://myresource.cognitiveservices.azure.com/"
    
  aws_textract:
    enabled: true
    region: "us-east-1"
    access_key: "AKIAIOSFODNN7EXAMPLE"
    secret_key: "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    
  # Premium APIs (Replace with your actual keys)
  abbyy:
    enabled: true
    api_key: "abcd1234-ef56-7890-abcd-1234567890ab"
    endpoint: "https://cloud-eu.abbyy.com"
    
  nanonets:
    enabled: true
    api_key: "12345678-abcd-efgh-ijkl-123456789012"
    model_id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    
  mathpix:
    enabled: false  # Limited Telugu support
    app_id: "myapp_123456"
    app_key: "key_abcdef123456789"
```

## Step-by-Step Configuration

### 1. Copy Template
```bash
cp config/engines_template.yaml config/engines.yaml
```

### 2. Configure Each API

#### Google Cloud Vision
```yaml
google_vision:
  enabled: true
  api_key_path: "/absolute/path/to/your/google_vision_credentials.json"
```
- Use **absolute path** to your downloaded JSON credentials file
- Example: `/home/username/telugu-ocr/credentials/google_vision_key.json`

#### Azure Computer Vision
```yaml
azure_vision:
  enabled: true
  subscription_key: "your_32_character_subscription_key"
  endpoint: "https://your-resource-name.cognitiveservices.azure.com/"
```
- Get from Azure Portal → Your Computer Vision Resource → Keys and Endpoint

#### AWS Textract
```yaml
aws_textract:
  enabled: true
  region: "us-east-1"
  access_key: "your_aws_access_key_id"
  secret_key: "your_aws_secret_access_key"
```
- Get from AWS Console → IAM → Users → Security Credentials

#### ABBYY Cloud OCR
```yaml
abbyy:
  enabled: true
  api_key: "your_abbyy_api_key"
  endpoint: "https://cloud-eu.abbyy.com"  # or https://cloud-us.abbyy.com
```
- Get from ABBYY Cloud Portal → Applications → Your App

#### Nanonets OCR
```yaml
nanonets:
  enabled: true
  api_key: "your_nanonets_api_key"
  model_id: "your_trained_model_id"
```
- Get from Nanonets Dashboard → Your Model
- **Important**: Train your model with Telugu documents first

#### Mathpix OCR
```yaml
mathpix:
  enabled: false  # Recommended: Limited Telugu support
  app_id: "your_mathpix_app_id"
  app_key: "your_mathpix_app_key"
```
- Get from Mathpix Dashboard → Your App

### 3. Security Configuration

Add to `.gitignore`:
```gitignore
# Never commit API keys!
config/engines.yaml
credentials/
*.json
```

### 4. Validate Configuration

```bash
# Test your configuration
python test_api_keys.py

# Test OCR engines
python -m telugu_ocr test

# List configured engines
python -m telugu_ocr list-engines
```

## Recommended Configurations

### Budget Setup (Free + 1 Paid)
```yaml
engines:
  tesseract:
    enabled: true
  easyocr:
    enabled: true
  google_vision:  # Best paid option for Telugu
    enabled: true
    api_key_path: "/path/to/google_key.json"
  # Disable others
  azure_vision:
    enabled: false
  aws_textract:
    enabled: false
```

### High Accuracy Setup
```yaml
engines:
  easyocr:
    enabled: true
  google_vision:
    enabled: true
    api_key_path: "/path/to/google_key.json"
  abbyy:
    enabled: true
    api_key: "your_abbyy_key"
  # Others as needed
```

### Development Setup (Free Only)
```yaml
engines:
  tesseract:
    enabled: true
  easyocr:
    enabled: true
  paddleocr:
    enabled: true
  # Disable all paid APIs
  google_vision:
    enabled: false
  azure_vision:
    enabled: false
```

## Troubleshooting

### Common Issues

1. **File not found error for Google Vision**
   - Use absolute path: `/home/user/path/to/file.json`
   - Check file exists: `ls -la /path/to/google_key.json`

2. **Azure authentication failed**
   - Verify subscription key is 32 characters
   - Check endpoint URL format: `https://resource-name.cognitiveservices.azure.com/`

3. **AWS credentials error**
   - Ensure access key starts with `AKIA`
   - Check secret key is 40 characters
   - Verify IAM user has Textract permissions

4. **Engine shows as "Not Available"**
   - Check API key format and validity
   - Verify internet connection for cloud APIs
   - Run `python test_api_keys.py` for detailed diagnostics

### Validation Commands

```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('config/engines.yaml'))"

# Test specific engine
python -m telugu_ocr test --engines google_vision

# Process test document
python -m telugu_ocr process test_document.pdf --engines easyocr google_vision
```

## Security Best Practices

1. **Never commit engines.yaml to version control**
2. **Use file permissions to protect the config**:
   ```bash
   chmod 600 config/engines.yaml
   ```
3. **Rotate API keys regularly** (every 90 days)
4. **Monitor API usage** and set billing alerts
5. **Use separate keys for development and production**

This configuration method centralizes all API keys in one secure location while maintaining flexibility to enable/disable engines as needed.