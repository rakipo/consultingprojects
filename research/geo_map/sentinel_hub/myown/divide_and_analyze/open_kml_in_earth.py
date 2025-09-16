#!/usr/bin/env python3
"""
KML File Opener for Google Earth
Opens KML files in Google Earth with proper handling
"""

import os
import sys
import subprocess
import webbrowser
import platform
from pathlib import Path


def open_kml_in_google_earth_desktop(kml_path):
    """
    Open KML file in Google Earth Desktop application
    """
    kml_path = os.path.abspath(kml_path)
    
    if platform.system() == "Darwin":  # macOS
        try:
            # Try to open with Google Earth Pro
            subprocess.run([
                "open", "-a", "Google Earth Pro", kml_path
            ], check=True)
            print(f"✅ Opened {kml_path} in Google Earth Pro")
            return True
        except subprocess.CalledProcessError:
            try:
                # Try to open with Google Earth
                subprocess.run([
                    "open", "-a", "Google Earth", kml_path
                ], check=True)
                print(f"✅ Opened {kml_path} in Google Earth")
                return True
            except subprocess.CalledProcessError:
                print("❌ Google Earth not found on macOS")
                return False
    
    elif platform.system() == "Windows":
        try:
            # Try to open with Google Earth Pro
            subprocess.run([
                "start", "googleearthpro://", kml_path
            ], check=True, shell=True)
            print(f"✅ Opened {kml_path} in Google Earth Pro")
            return True
        except subprocess.CalledProcessError:
            try:
                # Try to open with Google Earth
                subprocess.run([
                    "start", "googleearth://", kml_path
                ], check=True, shell=True)
                print(f"✅ Opened {kml_path} in Google Earth")
                return True
            except subprocess.CalledProcessError:
                print("❌ Google Earth not found on Windows")
                return False
    
    elif platform.system() == "Linux":
        try:
            subprocess.run([
                "google-earth-pro", kml_path
            ], check=True)
            print(f"✅ Opened {kml_path} in Google Earth Pro")
            return True
        except subprocess.CalledProcessError:
            try:
                subprocess.run([
                    "google-earth", kml_path
                ], check=True)
                print(f"✅ Opened {kml_path} in Google Earth")
                return True
            except subprocess.CalledProcessError:
                print("❌ Google Earth not found on Linux")
                return False
    
    return False


def open_kml_in_google_earth_web(kml_path):
    """
    Open KML file in Google Earth Web (requires file to be accessible via URL)
    """
    print("🌐 Google Earth Web requires the KML file to be accessible via a public URL")
    print("📁 For local files, please use Google Earth Desktop application")
    print("🔗 If you have a web-accessible KML URL, you can use:")
    print("   https://earth.google.com/web/search/[YOUR_KML_URL]")
    return False


def validate_kml_file(kml_path):
    """
    Validate that the KML file exists and is readable
    """
    if not os.path.exists(kml_path):
        print(f"❌ KML file not found: {kml_path}")
        return False
    
    if not kml_path.lower().endswith('.kml'):
        print(f"❌ File is not a KML file: {kml_path}")
        return False
    
    try:
        with open(kml_path, 'r', encoding='utf-8') as f:
            content = f.read(100)  # Read first 100 characters
            if '<?xml' not in content and '<kml' not in content:
                print(f"❌ File does not appear to be a valid KML file: {kml_path}")
                return False
    except Exception as e:
        print(f"❌ Error reading KML file: {e}")
        return False
    
    return True


def main():
    """
    Main function
    """
    if len(sys.argv) != 2:
        print("Usage: python open_kml_in_earth.py <kml_file_path>")
        print("Example: python open_kml_in_earth.py output/20250824_100752/NDVI_Vegetation_Analysis.kml")
        sys.exit(1)
    
    kml_path = sys.argv[1]
    
    print("🗺️  KML File Opener for Google Earth")
    print("=" * 50)
    
    # Validate KML file
    if not validate_kml_file(kml_path):
        sys.exit(1)
    
    print(f"📁 KML File: {kml_path}")
    print(f"📏 File Size: {os.path.getsize(kml_path)} bytes")
    
    # Try to open in Google Earth Desktop first
    print("\n🖥️  Attempting to open in Google Earth Desktop...")
    if open_kml_in_google_earth_desktop(kml_path):
        print("✅ Successfully opened in Google Earth Desktop")
        return
    
    # If desktop fails, try web
    print("\n🌐 Attempting to open in Google Earth Web...")
    if open_kml_in_google_earth_web(kml_path):
        print("✅ Successfully opened in Google Earth Web")
        return
    
    # Fallback instructions
    print("\n📋 Manual Instructions:")
    print("1. Open Google Earth Desktop application")
    print("2. Go to File > Open")
    print("3. Navigate to and select your KML file:")
    print(f"   {os.path.abspath(kml_path)}")
    print("4. Click 'Open'")
    
    print("\n🔗 Alternative: Upload KML to a web service")
    print("- Google Drive (make public)")
    print("- GitHub (raw file)")
    print("- Any web server")
    print("Then use: https://earth.google.com/web/search/[URL]")


if __name__ == "__main__":
    main()
