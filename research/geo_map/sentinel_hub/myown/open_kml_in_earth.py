#!/usr/bin/env python3
"""
KML to Google Earth Browser Opener

This script takes a KML file path as a command line argument and opens it
in Google Earth in the default web browser.

Usage:
    python open_kml_in_earth.py <path_to_kml_file>

Example:
    python open_kml_in_earth.py divide_and_analyze/office_025acre_square.kml
"""

import sys
import os
import webbrowser
import argparse
from pathlib import Path
import urllib.parse


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


def open_kml_in_google_earth(kml_file_path):
    """
    Open a KML file in Google Earth in the browser.
    
    Args:
        kml_file_path (str): Path to the KML file
    """
    # Convert the file path to an absolute path
    abs_path = os.path.abspath(kml_file_path)
    
    # Create a file URL
    file_url = f"file://{abs_path}"
    
    # Google Earth web URL with the KML file
    # Using the earth.google.com web interface
    google_earth_url = f"https://earth.google.com/web/@{file_url}"
    
    print(f"Opening KML file: {kml_file_path}")
    print(f"File URL: {file_url}")
    print(f"Google Earth URL: {google_earth_url}")
    
    try:
        # Open in the default browser
        webbrowser.open(google_earth_url)
        print("Successfully opened Google Earth in your browser!")
        print("Note: You may need to manually load the KML file if it doesn't open automatically.")
        
    except Exception as e:
        print(f"Error opening browser: {e}")
        print("You can manually open the following URL in your browser:")
        print(google_earth_url)


def main():
    """Main function to handle command line arguments and execute the program."""
    parser = argparse.ArgumentParser(
        description="Open a KML file in Google Earth in the browser",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python open_kml_in_earth.py path/to/file.kml
  python open_kml_in_earth.py divide_and_analyze/office_025acre_square.kml
        """
    )
    
    parser.add_argument(
        'kml_file',
        help='Path to the KML file to open in Google Earth'
    )
    
    args = parser.parse_args()
    
    # Validate the KML file
    if not validate_kml_file(args.kml_file):
        sys.exit(1)
    
    # Open the KML file in Google Earth
    open_kml_in_google_earth(args.kml_file)


if __name__ == "__main__":
    main()
