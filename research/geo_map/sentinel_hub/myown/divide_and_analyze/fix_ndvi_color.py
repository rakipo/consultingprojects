#!/usr/bin/env python3
"""
Fix NDVI KML color from red to blue
"""

import os

def fix_ndvi_color():
    """Fix the NDVI KML color from red to blue"""
    
    kml_file = "output/20250824_100752/NDVI_Vegetation_Analysis.kml"
    
    if not os.path.exists(kml_file):
        print(f"❌ KML file not found: {kml_file}")
        return
    
    # Read the file
    with open(kml_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace red color (ff0000ff) with blue color (ffff0000)
    # In KML: ABGR format where ff0000ff = red, ffff0000 = blue
    fixed_content = content.replace('ff0000ff', 'ffff0000')
    
    # Write back to file
    with open(kml_file, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print("✅ Fixed NDVI KML color from red to blue")
    print(f"📁 Updated file: {kml_file}")

if __name__ == "__main__":
    fix_ndvi_color()
