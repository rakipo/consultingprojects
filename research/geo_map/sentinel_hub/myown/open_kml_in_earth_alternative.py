#!/usr/bin/env python3
"""
KML to Google Earth Opener (Alternative Version)

This script takes a KML file path as a command line argument and provides
multiple options to open it in Google Earth.

Usage:
    python open_kml_in_earth_alternative.py <path_to_kml_file>

Example:
    python open_kml_in_earth_alternative.py divide_and_analyze/office_025acre_square.kml
"""

import sys
import os
import webbrowser
import argparse
import subprocess
import platform
from pathlib import Path


def validate_kml_file(file_path):
    """
    Validate that the file exists and has a .kml extension.
    
    Args:
        file_path (str): Path to the KML file
        
    Returns:
        bool: True if valid, False otherwise
    """
    path = Path(file_path)
    
    if not path.exists():
        print(f"Error: File '{file_path}' does not exist.")
        return False
    
    if path.suffix.lower() != '.kml':
        print(f"Error: File '{file_path}' does not have a .kml extension.")
        return False
    
    return True


def open_with_google_earth_desktop(kml_file_path):
    """
    Try to open KML file with Google Earth desktop application.
    
    Args:
        kml_file_path (str): Path to the KML file
        
    Returns:
        bool: True if successful, False otherwise
    """
    system = platform.system()
    abs_path = os.path.abspath(kml_file_path)
    
    try:
        if system == "Darwin":  # macOS
            # Try to open with Google Earth Pro
            subprocess.run([
                "open", "-a", "Google Earth Pro", abs_path
            ], check=True)
            return True
            
        elif system == "Windows":
            # Try to open with Google Earth Pro on Windows
            subprocess.run([
                "start", "Google Earth Pro", abs_path
            ], check=True, shell=True)
            return True
            
        elif system == "Linux":
            # Try to open with Google Earth on Linux
            subprocess.run([
                "google-earth-pro", abs_path
            ], check=True)
            return True
            
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    
    return False


def open_with_google_earth_web(kml_file_path):
    """
    Open Google Earth web interface and provide instructions for loading KML.
    
    Args:
        kml_file_path (str): Path to the KML file
    """
    abs_path = os.path.abspath(kml_file_path)
    
    # Open Google Earth web interface
    web_url = "https://earth.google.com/web/"
    
    print(f"Opening Google Earth web interface...")
    print(f"KML file location: {abs_path}")
    print("\nTo load your KML file:")
    print("1. In Google Earth web, click the 'Projects' button (folder icon)")
    print("2. Click 'Import KML file from device'")
    print("3. Select your KML file from the file browser")
    print("4. The file will be loaded and displayed on the map")
    
    try:
        webbrowser.open(web_url)
        print(f"\nGoogle Earth web interface opened in your browser!")
    except Exception as e:
        print(f"Error opening browser: {e}")
        print(f"Please manually open: {web_url}")


def open_kml_file(kml_file_path, method="auto"):
    """
    Open a KML file using the specified method.
    
    Args:
        kml_file_path (str): Path to the KML file
        method (str): Method to use ('auto', 'desktop', 'web')
    """
    print(f"Opening KML file: {kml_file_path}")
    
    if method == "auto" or method == "desktop":
        print("Attempting to open with Google Earth desktop application...")
        if open_with_google_earth_desktop(kml_file_path):
            print("Successfully opened with Google Earth desktop application!")
            return
        else:
            print("Google Earth desktop application not found or failed to open.")
    
    if method == "auto" or method == "web":
        print("Opening Google Earth web interface...")
        open_with_google_earth_web(kml_file_path)
    
    # If we get here, provide additional options
    print("\n" + "="*50)
    print("ADDITIONAL OPTIONS:")
    print("="*50)
    print("1. Download Google Earth Pro from: https://www.google.com/earth/versions/")
    print("2. Use Google My Maps: https://www.google.com/mymaps")
    print("3. Use other KML viewers like:")
    print("   - QGIS (free GIS software)")
    print("   - Marble (KDE's virtual globe)")
    print("   - NASA World Wind")


def main():
    """Main function to handle command line arguments and execute the program."""
    parser = argparse.ArgumentParser(
        description="Open a KML file in Google Earth",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Methods:
  auto     Try desktop app first, then web interface (default)
  desktop  Try to open with Google Earth desktop application only
  web      Open Google Earth web interface only

Examples:
  python open_kml_in_earth_alternative.py path/to/file.kml
  python open_kml_in_earth_alternative.py --method web divide_and_analyze/office_025acre_square.kml
        """
    )
    
    parser.add_argument(
        'kml_file',
        help='Path to the KML file to open in Google Earth'
    )
    
    parser.add_argument(
        '--method',
        choices=['auto', 'desktop', 'web'],
        default='auto',
        help='Method to use for opening the KML file (default: auto)'
    )
    
    args = parser.parse_args()
    
    # Validate the KML file
    if not validate_kml_file(args.kml_file):
        sys.exit(1)
    
    # Open the KML file
    open_kml_file(args.kml_file, args.method)


if __name__ == "__main__":
    main()
