#!/usr/bin/env python3
"""
Interactive setup script for Telugu OCR API credentials.

This script helps users set up their API credentials interactively
and generates the necessary configuration files.
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, Any


def create_directories():
    """Create necessary directories for credentials and configuration."""
    directories = [
        "credentials",
        "config", 
        "logs",
        "output",
        "evaluation"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}/")


def setup_google_cloud_vision():
    """Interactive setup for Google Cloud Vision API."""
    print("\n🔵 Google Cloud Vision API Setup")
    print("-" * 40)
    print("1. Go to https://console.cloud.google.com/")
    print("2. Create a project and enable Vision API")
    print("3. Create a service account and download JSON key")
    print("4. Save the JSON file as 'google_vision_key.json'")
    
    json_path = input("\nEnter path to your Google Vision JSON key file (or press Enter to skip): ").strip()
    
    if json_path and Path(json_path).exists():
        # Test the JSON file
        try:
            with open(json_path, 'r') as f:
                json.load(f)
            print("✅ JSON file is valid")
            
            # Return absolute path for engines.yaml
            absolute_path = str(Path(json_path).absolute())
            print(f"✅ Will use path: {absolute_path}")
            return absolute_path
        except json.JSONDecodeError:
            print("❌ Invalid JSON file")
            return None
    elif json_path:
        print(f"❌ File not found: {json_path}")
        return None
    else:
        print("⚠️  Skipped Google Cloud Vision setup")
        return None


def setup_azure_vision():
    """Interactive setup for Azure Computer Vision."""
    print("\n🔷 Azure Computer Vision Setup")
    print("-" * 40)
    print("1. Go to https://portal.azure.com/")
    print("2. Create a Computer Vision resource")
    print("3. Get your subscription key and endpoint")
    
    subscription_key = input("\nEnter your Azure subscription key (or press Enter to skip): ").strip()
    
    if subscription_key:
        endpoint = input("Enter your Azure endpoint URL: ").strip()
        
        if endpoint:
            # Return credentials for engines.yaml
            credentials = {
                "subscription_key": subscription_key,
                "endpoint": endpoint
            }
            
            # Also save to credentials file for backup
            azure_config = {
                "subscription_key": subscription_key,
                "endpoint": endpoint
            }
            
            with open("credentials/azure_config.json", 'w') as f:
                json.dump(azure_config, f, indent=2)
            
            print("✅ Azure Vision credentials saved")
            return credentials
        else:
            print("❌ Endpoint URL is required")
            return {}
    else:
        print("⚠️  Skipped Azure Vision setup")
        return {}


def setup_aws_textract():
    """Interactive setup for AWS Textract."""
    print("\n🟠 AWS Textract Setup")
    print("-" * 40)
    print("1. Go to https://aws.amazon.com/")
    print("2. Create an IAM user with Textract permissions")
    print("3. Generate access keys")
    
    access_key = input("\nEnter your AWS Access Key ID (or press Enter to skip): ").strip()
    
    if access_key:
        secret_key = input("Enter your AWS Secret Access Key: ").strip()
        region = input("Enter your AWS region (default: us-east-1): ").strip() or "us-east-1"
        
        if secret_key:
            # Return credentials for engines.yaml
            credentials = {
                "access_key": access_key,
                "secret_key": secret_key,
                "region": region
            }
            
            # Save to credentials file for backup
            aws_config = {
                "access_key_id": access_key,
                "secret_access_key": secret_key,
                "region": region
            }
            
            with open("credentials/aws_credentials.json", 'w') as f:
                json.dump(aws_config, f, indent=2)
            
            print("✅ AWS Textract credentials saved")
            return credentials
        else:
            print("❌ Secret access key is required")
            return {}
    else:
        print("⚠️  Skipped AWS Textract setup")
        return {}


def setup_abbyy_cloud():
    """Interactive setup for ABBYY Cloud OCR."""
    print("\n🟣 ABBYY Cloud OCR Setup")
    print("-" * 40)
    print("1. Go to https://www.abbyy.com/cloud-ocr-sdk/")
    print("2. Create an account and application")
    print("3. Get your API key")
    
    api_key = input("\nEnter your ABBYY API key (or press Enter to skip): ").strip()
    
    if api_key:
        endpoint = input("Enter ABBYY endpoint (default: https://cloud-eu.abbyy.com): ").strip()
        endpoint = endpoint or "https://cloud-eu.abbyy.com"
        
        # Return credentials for engines.yaml
        credentials = {
            "api_key": api_key,
            "endpoint": endpoint
        }
        
        # Save to credentials file for backup
        abbyy_config = {
            "api_key": api_key,
            "endpoint": endpoint
        }
        
        with open("credentials/abbyy_config.json", 'w') as f:
            json.dump(abbyy_config, f, indent=2)
        
        print("✅ ABBYY Cloud credentials saved")
        return credentials
    else:
        print("⚠️  Skipped ABBYY Cloud setup")
        return {}


def setup_nanonets():
    """Interactive setup for Nanonets OCR."""
    print("\n🟢 Nanonets OCR Setup")
    print("-" * 40)
    print("1. Go to https://nanonets.com/")
    print("2. Create an OCR model")
    print("3. Train it with Telugu documents")
    print("4. Get your API key and model ID")
    
    api_key = input("\nEnter your Nanonets API key (or press Enter to skip): ").strip()
    
    if api_key:
        model_id = input("Enter your Nanonets model ID: ").strip()
        
        if model_id:
            # Return credentials for engines.yaml
            credentials = {
                "api_key": api_key,
                "model_id": model_id
            }
            
            # Save to credentials file for backup
            nanonets_config = {
                "api_key": api_key,
                "model_id": model_id
            }
            
            with open("credentials/nanonets_config.json", 'w') as f:
                json.dump(nanonets_config, f, indent=2)
            
            print("✅ Nanonets credentials saved")
            return credentials
        else:
            print("❌ Model ID is required")
            return {}
    else:
        print("⚠️  Skipped Nanonets setup")
        return {}


def setup_mathpix():
    """Interactive setup for Mathpix OCR."""
    print("\n🔵 Mathpix OCR Setup")
    print("-" * 40)
    print("1. Go to https://mathpix.com/")
    print("2. Create an application")
    print("3. Get your App ID and App Key")
    print("Note: Mathpix has limited Telugu support")
    
    app_id = input("\nEnter your Mathpix App ID (or press Enter to skip): ").strip()
    
    if app_id:
        app_key = input("Enter your Mathpix App Key: ").strip()
        
        if app_key:
            # Return credentials for engines.yaml
            credentials = {
                "app_id": app_id,
                "app_key": app_key
            }
            
            # Save to credentials file for backup
            mathpix_config = {
                "app_id": app_id,
                "app_key": app_key
            }
            
            with open("credentials/mathpix_config.json", 'w') as f:
                json.dump(mathpix_config, f, indent=2)
            
            print("✅ Mathpix credentials saved")
            return credentials
        else:
            print("❌ App Key is required")
            return {}
    else:
        print("⚠️  Skipped Mathpix setup")
        return {}


def generate_engines_config(all_credentials: Dict[str, Dict[str, str]]):
    """Generate engines.yaml file with all API credentials."""
    if not all_credentials:
        print("⚠️  No credentials to save")
        return
    
    # Load template or create base config
    template_path = Path("config/engines_template.yaml")
    config_path = Path("config/engines.yaml")
    
    if template_path.exists():
        import yaml
        with open(template_path, 'r') as f:
            config = yaml.safe_load(f)
    else:
        config = {"engines": {}}
    
    # Update with provided credentials
    for engine_name, credentials in all_credentials.items():
        if engine_name not in config["engines"]:
            config["engines"][engine_name] = {}
        
        # Update credentials and enable engine
        config["engines"][engine_name].update(credentials)
        config["engines"][engine_name]["enabled"] = True
    
    # Save updated config
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, indent=2)
    
    print(f"✅ API credentials saved to {config_path}")
    print("💡 All API keys are now stored in config/engines.yaml")





def create_gitignore():
    """Create or update .gitignore file."""
    gitignore_content = """
# Telugu OCR System - Generated files and credentials

# API Keys and Credentials (NEVER COMMIT THESE!)
config/engines.yaml
credentials/
*.json

# Logs
logs/
*.log

# Output directories
output/
evaluation/
reports/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""
    
    with open(".gitignore", 'w') as f:
        f.write(gitignore_content.strip())
    
    print("✅ Created .gitignore file")


def main():
    """Main setup function."""
    print("🚀 Telugu OCR System - Interactive Credentials Setup")
    print("=" * 60)
    print("This script will help you set up API credentials for OCR engines.")
    print("You can skip any service you don't want to configure now.")
    print("=" * 60)
    
    try:
        # Create directories
        create_directories()
        
        # Collect all credentials for engines.yaml
        all_credentials = {}
        
        # Setup each service
        google_path = setup_google_cloud_vision()
        if google_path:
            all_credentials["google_vision"] = {"api_key_path": google_path}
        
        azure_creds = setup_azure_vision()
        if azure_creds:
            all_credentials["azure_vision"] = azure_creds
            
        aws_creds = setup_aws_textract()
        if aws_creds:
            all_credentials["aws_textract"] = aws_creds
            
        abbyy_creds = setup_abbyy_cloud()
        if abbyy_creds:
            all_credentials["abbyy"] = abbyy_creds
            
        nanonets_creds = setup_nanonets()
        if nanonets_creds:
            all_credentials["nanonets"] = nanonets_creds
            
        mathpix_creds = setup_mathpix()
        if mathpix_creds:
            all_credentials["mathpix"] = mathpix_creds
        
        # Generate configuration files
        generate_engines_config(all_credentials)
        create_gitignore()
        
        # Final summary
        print("\n" + "=" * 60)
        print("🎉 SETUP COMPLETE!")
        print("=" * 60)
        
        configured_services = []
        if Path("credentials/google_vision_key.json").exists():
            configured_services.append("Google Cloud Vision")
        if Path("credentials/azure_config.json").exists():
            configured_services.append("Azure Computer Vision")
        if Path("credentials/aws_credentials.json").exists():
            configured_services.append("AWS Textract")
        if Path("credentials/abbyy_config.json").exists():
            configured_services.append("ABBYY Cloud OCR")
        if Path("credentials/nanonets_config.json").exists():
            configured_services.append("Nanonets OCR")
        if Path("credentials/mathpix_config.json").exists():
            configured_services.append("Mathpix OCR")
        
        if configured_services:
            print(f"✅ Configured services: {', '.join(configured_services)}")
        else:
            print("⚠️  No API services configured - you can still use free local engines")
        
        print("\n📋 Next Steps:")
        print("1. Test your setup: python test_api_keys.py")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Test OCR engines: python -m telugu_ocr test")
        print("4. Process a document: python -m telugu_ocr process your_document.pdf")
        
        print("\n📚 Documentation:")
        print("- Full setup guide: docs/API_KEYS_SETUP.md")
        print("- Usage examples: example_usage.py")
        print("- Troubleshooting: docs/TROUBLESHOOTING.md")
        
        print("\n🔒 Security Reminder:")
        print("- Never commit credentials to version control")
        print("- The .gitignore file has been configured to protect your keys")
        print("- Rotate your API keys regularly")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Setup failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())