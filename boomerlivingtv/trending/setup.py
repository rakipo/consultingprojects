#!/usr/bin/env python3
"""
Setup script for Trending Content Analyzer
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    try:
        print("Installing required packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def check_config():
    """Check if config.yaml is properly configured"""
    try:
        import yaml
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
        
        api_key = config['model']['api_key']
        if api_key == "your-openai-api-key-here" or api_key == "your-anthropic-api-key-here":
            print("⚠️  Please update your API key in config.yaml before running the analyzer")
            return False
        
        print("✅ Configuration looks good!")
        return True
    except Exception as e:
        print(f"❌ Error checking configuration: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Trending Content Analyzer...")
    
    if not install_requirements():
        sys.exit(1)
    
    if not check_config():
        print("\n📝 Next steps:")
        print("1. Edit config.yaml and add your API key")
        print("2. Run: python analyze_trending.py")
    else:
        print("\n🎉 Setup complete! You can now run: python analyze_trending.py")

if __name__ == "__main__":
    main()