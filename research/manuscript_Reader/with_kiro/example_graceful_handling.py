#!/usr/bin/env python3
"""
Example demonstrating graceful handling of missing API keys.

This script shows how the Telugu OCR system handles:
1. Local engines (always try to run if dependencies available)
2. API engines (only run if valid API keys are configured)
"""

import sys
from pathlib import Path
from telugu_ocr.core.telugu_ocr_system import TeluguOCRSystem


def demonstrate_graceful_handling():
    """Demonstrate how the system handles missing API keys gracefully."""
    print("🚀 Telugu OCR System - Graceful API Key Handling Demo")
    print("=" * 60)
    
    try:
        # Initialize the OCR system
        print("📋 Initializing OCR system...")
        ocr_system = TeluguOCRSystem()
        
        # Get system status
        status = ocr_system.get_system_status()
        
        print(f"\n📊 System Status:")
        print(f"   Enabled engines in config: {len(status['enabled_engines'])}")
        print(f"   Available engines: {len(status['available_engines'])}")
        print(f"   Failed engines: {len(status['failed_engines'])}")
        
        # Categorize engines
        available_engines = status['available_engines']
        failed_engines = status['failed_engines']
        
        local_engines = ['tesseract', 'easyocr', 'paddleocr', 'trocr']
        api_engines = ['google_vision', 'azure_vision', 'aws_textract', 'abbyy', 'nanonets', 'mathpix']
        
        available_local = [e for e in available_engines if e in local_engines]
        available_api = [e for e in available_engines if e in api_engines]
        failed_local = [e for e in failed_engines if e in local_engines]
        failed_api = [e for e in failed_engines if e in api_engines]
        
        print(f"\n📦 Local Engines (Python packages):")
        if available_local:
            print(f"   ✅ Available: {', '.join(available_local)}")
        if failed_local:
            print(f"   ❌ Missing dependencies: {', '.join(failed_local)}")
            print(f"      💡 Install with: pip install {' '.join(failed_local)}")
        
        print(f"\n🌐 API Engines (Third-party services):")
        if available_api:
            print(f"   ✅ Configured: {', '.join(available_api)}")
        if failed_api:
            print(f"   ⚠️  Not configured: {', '.join(failed_api)}")
            print(f"      💡 Configure API keys in config/engines.yaml")
        
        # Show what will happen during processing
        print(f"\n🔄 Processing Behavior:")
        if available_engines:
            print(f"   ✅ Will process with {len(available_engines)} engines")
            print(f"   📝 Results will include comparison across available engines")
            
            if available_local and not available_api:
                print(f"   💡 Only local processing available - consider adding API engines for better accuracy")
            elif available_api and not available_local:
                print(f"   💰 Only API processing available - consider adding free local engines")
            else:
                print(f"   🎯 Good mix of local and API engines for comprehensive comparison")
        else:
            print(f"   ❌ No engines available - cannot process documents")
            print(f"   🔧 Please install local engines or configure API keys")
        
        # Demonstrate with a test document if available
        test_pdf = "test_manu.pdf"
        if Path(test_pdf).exists() and available_engines:
            print(f"\n📄 Test Processing:")
            print(f"   Found test document: {test_pdf}")
            print(f"   Would process with: {', '.join(available_engines)}")
            
            # Uncomment the next line to actually process
            # results = ocr_system.process_pdf(test_pdf)
            print(f"   💡 Uncomment line in script to actually process the document")
        
        # Show setup recommendations
        print(f"\n💡 Recommendations:")
        
        if not available_engines:
            print(f"   🚨 URGENT: No OCR engines available!")
            print(f"   1️⃣  Install local engines: pip install easyocr pytesseract")
            print(f"   2️⃣  Or configure API keys in config/engines.yaml")
        
        elif len(available_engines) < 3:
            print(f"   📈 Consider adding more engines for better comparison:")
            if not available_local:
                print(f"      📦 Add local engines: pip install easyocr pytesseract")
            if not available_api:
                print(f"      🌐 Add API engines: Configure keys in config/engines.yaml")
        
        else:
            print(f"   ✅ Good engine coverage! You're ready for comprehensive OCR processing")
        
        print(f"\n🔗 Next Steps:")
        print(f"   📖 Setup guide: docs/API_KEYS_SETUP.md")
        print(f"   🚀 Quick start: docs/QUICK_START_API_SETUP.md")
        print(f"   🧪 Test setup: python test_api_keys.py")
        print(f"   ⚙️  Interactive setup: python setup_credentials_template.py")
        
        return 0 if available_engines else 1
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        return 1


def show_engine_details():
    """Show detailed information about each engine type."""
    print(f"\n📚 Engine Details:")
    print(f"=" * 40)
    
    local_engines = {
        'tesseract': {
            'description': 'Google Tesseract OCR with Telugu language pack',
            'install': 'System: apt-get install tesseract-ocr tesseract-ocr-tel\nPython: pip install pytesseract',
            'telugu_support': '⭐⭐⭐ Good',
            'cost': 'Free'
        },
        'easyocr': {
            'description': 'Easy-to-use OCR with excellent Telugu support',
            'install': 'pip install easyocr',
            'telugu_support': '⭐⭐⭐⭐⭐ Excellent',
            'cost': 'Free'
        },
        'paddleocr': {
            'description': 'PaddlePaddle OCR with multi-language support',
            'install': 'pip install paddleocr',
            'telugu_support': '⭐⭐⭐ Good',
            'cost': 'Free'
        },
        'trocr': {
            'description': 'Transformer-based OCR (limited Telugu support)',
            'install': 'pip install transformers torch',
            'telugu_support': '⭐⭐ Limited',
            'cost': 'Free'
        }
    }
    
    api_engines = {
        'google_vision': {
            'description': 'Google Cloud Vision API',
            'setup': 'Create Google Cloud project, enable Vision API, download JSON key',
            'telugu_support': '⭐⭐⭐⭐⭐ Excellent',
            'cost': '$1.50/1K requests (1K free/month)'
        },
        'azure_vision': {
            'description': 'Azure Computer Vision API',
            'setup': 'Create Azure Computer Vision resource, get subscription key',
            'telugu_support': '⭐⭐⭐⭐ Good',
            'cost': '$1.00/1K requests (5K free/month)'
        },
        'aws_textract': {
            'description': 'AWS Textract OCR service',
            'setup': 'Create IAM user with Textract permissions, get access keys',
            'telugu_support': '⭐⭐ Limited',
            'cost': '$1.50/1K pages (1K free/month)'
        }
    }
    
    print(f"📦 LOCAL ENGINES (Python packages):")
    for engine, details in local_engines.items():
        print(f"\n   {engine.upper()}:")
        print(f"      📝 {details['description']}")
        print(f"      🔧 Install: {details['install']}")
        print(f"      🇮🇳 Telugu: {details['telugu_support']}")
        print(f"      💰 Cost: {details['cost']}")
    
    print(f"\n🌐 API ENGINES (Third-party services):")
    for engine, details in api_engines.items():
        print(f"\n   {engine.upper()}:")
        print(f"      📝 {details['description']}")
        print(f"      🔧 Setup: {details['setup']}")
        print(f"      🇮🇳 Telugu: {details['telugu_support']}")
        print(f"      💰 Cost: {details['cost']}")


def main():
    """Main demonstration function."""
    try:
        result = demonstrate_graceful_handling()
        show_engine_details()
        
        print(f"\n" + "=" * 60)
        if result == 0:
            print(f"✅ Demo completed successfully! OCR engines are available.")
        else:
            print(f"⚠️  Demo completed with warnings. Some setup required.")
        
        return result
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Demo interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())