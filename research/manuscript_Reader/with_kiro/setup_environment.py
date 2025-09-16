#!/usr/bin/env python3
"""
Setup script for Telugu OCR System environment.
This script helps users set up the conda environment and dependencies.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def run_command(command, check=True, shell=False):
    """Run a command and return the result."""
    try:
        if shell:
            result = subprocess.run(command, shell=True, check=check, 
                                  capture_output=True, text=True)
        else:
            result = subprocess.run(command.split(), check=check, 
                                  capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr
    except FileNotFoundError:
        return False, "", f"Command not found: {command.split()[0]}"


def check_conda():
    """Check if conda is installed."""
    success, stdout, stderr = run_command("conda --version")
    if success:
        print(f"✅ Conda found: {stdout.strip()}")
        return True
    else:
        print("❌ Conda not found. Please install Anaconda or Miniconda first.")
        print("   Download from: https://docs.conda.io/en/latest/miniconda.html")
        return False


def check_system_dependencies():
    """Check system-specific dependencies."""
    system = platform.system().lower()
    print(f"\n🔍 Checking system dependencies for {system}...")
    
    if system == "darwin":  # macOS
        # Check if Homebrew is available
        success, _, _ = run_command("brew --version")
        if success:
            print("✅ Homebrew found")
            
            # Check for tesseract
            success, _, _ = run_command("tesseract --version")
            if not success:
                print("⚠️  Tesseract not found. Installing via Homebrew...")
                run_command("brew install tesseract tesseract-lang", shell=True)
            else:
                print("✅ Tesseract found")
                
            # Check for poppler
            success, _, _ = run_command("pdftoppm -h")
            if not success:
                print("⚠️  Poppler not found. Installing via Homebrew...")
                run_command("brew install poppler", shell=True)
            else:
                print("✅ Poppler found")
        else:
            print("⚠️  Homebrew not found. Please install system dependencies manually:")
            print("   - Tesseract: https://tesseract-ocr.github.io/tessdoc/Installation.html")
            print("   - Poppler: https://poppler.freedesktop.org/")
    
    elif system == "linux":
        print("ℹ️  For Linux systems, please ensure you have:")
        print("   sudo apt-get update")
        print("   sudo apt-get install tesseract-ocr tesseract-ocr-tel")
        print("   sudo apt-get install poppler-utils")
        print("   sudo apt-get install libgl1-mesa-glx")
    
    elif system == "windows":
        print("ℹ️  For Windows systems, please install:")
        print("   - Tesseract: https://github.com/UB-Mannheim/tesseract/wiki")
        print("   - Poppler: https://blog.alivate.com.au/poppler-windows/")
        print("   - Add both to your PATH environment variable")


def create_conda_environment():
    """Create the conda environment from environment.yml."""
    env_file = Path("environment.yml")
    if not env_file.exists():
        print("❌ environment.yml not found!")
        return False
    
    print("\n🔧 Creating conda environment...")
    success, stdout, stderr = run_command("conda env create -f environment.yml")
    
    if success:
        print("✅ Conda environment 'telugu_ocr' created successfully!")
        return True
    else:
        if "already exists" in stderr:
            print("ℹ️  Environment 'telugu_ocr' already exists.")
            
            # Ask user if they want to update
            response = input("Do you want to update it? (y/N): ").lower().strip()
            if response in ['y', 'yes']:
                print("🔄 Updating environment...")
                success, _, _ = run_command("conda env update -f environment.yml")
                if success:
                    print("✅ Environment updated successfully!")
                    return True
                else:
                    print("❌ Failed to update environment")
                    return False
            else:
                return True
        else:
            print(f"❌ Failed to create environment: {stderr}")
            return False


def test_installation():
    """Test the installation by running the OCR system test."""
    print("\n🧪 Testing installation...")
    
    # Activate environment and test
    if platform.system().lower() == "windows":
        activate_cmd = "conda activate telugu_ocr && python -m telugu_ocr test"
    else:
        activate_cmd = "source activate telugu_ocr && python -m telugu_ocr test"
    
    success, stdout, stderr = run_command(activate_cmd, shell=True)
    
    if success:
        print("✅ Installation test passed!")
        print(stdout)
        return True
    else:
        print("⚠️  Installation test had issues:")
        print(stderr)
        return False


def setup_config_files():
    """Set up configuration files."""
    print("\n📝 Setting up configuration files...")
    
    config_dir = Path("config")
    if not config_dir.exists():
        print("❌ Config directory not found!")
        return False
    
    # Check if engines.yaml exists
    engines_config = config_dir / "engines.yaml"
    if engines_config.exists():
        print("✅ engines.yaml found")
    else:
        print("⚠️  engines.yaml not found. Please check the config directory.")
    
    # Create credentials directory if it doesn't exist
    creds_dir = Path("credentials")
    if not creds_dir.exists():
        creds_dir.mkdir()
        print("✅ Created credentials directory")
    
    # Create output directory if it doesn't exist
    output_dir = Path("output")
    if not output_dir.exists():
        output_dir.mkdir()
        print("✅ Created output directory")
    
    return True


def print_next_steps():
    """Print next steps for the user."""
    print("\n🎉 Setup complete! Next steps:")
    print("\n1. Activate the environment:")
    print("   conda activate telugu_ocr")
    
    print("\n2. Test the system:")
    print("   python -m telugu_ocr test")
    
    print("\n3. Process a PDF:")
    print("   python -m telugu_ocr process your_document.pdf")
    
    print("\n4. Configure API keys (optional):")
    print("   Edit config/engines.yaml to add your API keys for cloud OCR services")
    
    print("\n5. Check available engines:")
    print("   python -m telugu_ocr list-engines")
    
    print("\n📚 For more information, see:")
    print("   - README.md")
    print("   - docs/QUICK_START_API_SETUP.md")


def main():
    """Main setup function."""
    print("🚀 Telugu OCR System Environment Setup")
    print("=" * 50)
    
    # Check prerequisites
    if not check_conda():
        sys.exit(1)
    
    # Check system dependencies
    check_system_dependencies()
    
    # Create conda environment
    if not create_conda_environment():
        print("\n❌ Failed to create conda environment")
        sys.exit(1)
    
    # Set up config files
    setup_config_files()
    
    # Test installation
    test_installation()
    
    # Print next steps
    print_next_steps()
    
    print("\n✅ Setup completed successfully!")


if __name__ == "__main__":
    main()