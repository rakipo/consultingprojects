#!/usr/bin/env python3
"""
Dependency Installation Script
Installs all required dependencies for the Boomer Living TV App
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {command}")
        print(f"   Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required, but found {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def install_dependencies():
    """Install all dependencies"""
    print("🚀 Installing Boomer Living TV App Dependencies")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Change to app directory
    app_dir = Path(__file__).parent
    os.chdir(app_dir)
    print(f"📁 Working directory: {app_dir}")
    
    # Upgrade pip first
    if not run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install requirements
    if not run_command(f"{sys.executable} -m pip install -r requirements.txt", "Installing dependencies"):
        return False
    
    # Verify critical imports
    critical_imports = [
        ("psycopg2", "PostgreSQL driver"),
        ("neo4j", "Neo4j driver"),
        ("pandas", "Data processing"),
        ("yaml", "YAML configuration"),
        ("mcp", "MCP framework"),
        ("fastapi", "Web framework")
    ]
    
    print("\n🔍 Verifying critical imports...")
    failed_imports = []
    
    for module, description in critical_imports:
        try:
            __import__(module)
            print(f"✅ {description} ({module}) - OK")
        except ImportError as e:
            print(f"❌ {description} ({module}) - FAILED: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n❌ Failed to import: {', '.join(failed_imports)}")
        print("Please check the installation and try again.")
        return False
    
    print("\n🎉 All dependencies installed and verified successfully!")
    print("\n📋 Next steps:")
    print("1. Configure your environment variables in env_config.yaml")
    print("2. Update param_config.yaml with your specific settings")
    print("3. Run the application components as needed")
    
    return True

def show_installed_packages():
    """Show installed packages for verification"""
    print("\n📦 Installed packages:")
    try:
        result = subprocess.run(f"{sys.executable} -m pip list", shell=True, capture_output=True, text=True)
        relevant_packages = []
        for line in result.stdout.split('\n'):
            if any(pkg in line.lower() for pkg in ['psycopg2', 'neo4j', 'pandas', 'yaml', 'mcp', 'fastapi', 'langchain', 'langgraph']):
                relevant_packages.append(line)
        
        if relevant_packages:
            for package in relevant_packages:
                print(f"  {package}")
        else:
            print("  No relevant packages found in pip list")
    except Exception as e:
        print(f"  Could not retrieve package list: {e}")

def main():
    """Main installation function"""
    try:
        success = install_dependencies()
        
        if success:
            show_installed_packages()
            print("\n✅ Installation completed successfully!")
        else:
            print("\n❌ Installation failed. Please check the errors above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during installation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()