#!/usr/bin/env python3
"""
Create Google Earth Web URLs with base64-encoded KML data
Generates URLs in the correct format that Google Earth Web expects
"""

import base64
import urllib.parse
import os
from typing import Dict


class GoogleEarthURLGenerator:
    def __init__(self):
        self.base_url = "https://earth.google.com/web/"
    
    def encode_kml_to_base64(self, kml_path: str) -> str:
        """Encode KML file content to base64"""
        try:
            with open(kml_path, 'rb') as f:
                kml_content = f.read()
            
            # Encode to base64
            encoded = base64.b64encode(kml_content).decode('utf-8')
            return encoded
            
        except Exception as e:
            print(f"❌ Error encoding KML file: {e}")
            return None
    
    def extract_coordinates_from_kml(self, kml_path: str) -> Dict:
        """Extract center coordinates from KML file"""
        try:
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(kml_path)
            root = tree.getroot()
            namespace = {'kml': 'http://www.opengis.net/kml/2.2'}
            
            # Find all coordinates
            coords_elements = root.findall('.//kml:coordinates', namespace)
            
            if not coords_elements:
                return {'lat': 14.38172873, 'lon': 79.523023}  # Default coordinates
            
            # Parse coordinates to find center
            all_lats = []
            all_lons = []
            
            for coords_elem in coords_elements:
                coord_text = coords_elem.text
                if coord_text:
                    coord_pairs = coord_text.strip().split()
                    for pair in coord_pairs:
                        parts = pair.split(',')
                        if len(parts) >= 2:
                            try:
                                lon = float(parts[0])
                                lat = float(parts[1])
                                all_lons.append(lon)
                                all_lats.append(lat)
                            except ValueError:
                                continue
            
            if all_lats and all_lons:
                center_lat = sum(all_lats) / len(all_lats)
                center_lon = sum(all_lons) / len(all_lons)
                return {'lat': center_lat, 'lon': center_lon}
            else:
                return {'lat': 14.38172873, 'lon': 79.523023}  # Default coordinates
                
        except Exception as e:
            print(f"❌ Error extracting coordinates: {e}")
            return {'lat': 14.38172873, 'lon': 79.523023}  # Default coordinates
    
    def build_google_earth_url(self, kml_path: str) -> str:
        """Build Google Earth Web URL with base64-encoded KML data"""
        if not os.path.exists(kml_path):
            print(f"❌ KML file not found: {kml_path}")
            return None
        
        # Encode KML to base64
        encoded_kml = self.encode_kml_to_base64(kml_path)
        if not encoded_kml:
            return None
        
        # Extract coordinates
        coords = self.extract_coordinates_from_kml(kml_path)
        
        # Build URL in the correct format
        url = (f"{self.base_url}@{coords['lat']},{coords['lon']},"
               f"141.52332262a,1000.00228507d,30.000006y,0h,0t,0r/"
               f"data={encoded_kml}")
        
        return url
    
    def generate_all_urls(self, kml_files: list) -> Dict:
        """Generate URLs for all KML files"""
        results = {}
        
        for kml_path, description in kml_files:
            print(f"📁 Processing: {description}")
            print(f"   File: {kml_path}")
            
            url = self.build_google_earth_url(kml_path)
            if url:
                results[description] = {
                    'file': kml_path,
                    'url': url,
                    'status': 'success'
                }
                print(f"   ✅ URL generated successfully")
                print(f"   🔗 URL: {url[:100]}...")
            else:
                results[description] = {
                    'file': kml_path,
                    'url': None,
                    'status': 'failed'
                }
                print(f"   ❌ Failed to generate URL")
            
            print()
        
        return results


def main():
    """Main function"""
    generator = GoogleEarthURLGenerator()
    
    # Define KML files
    kml_files = [
        ("output/20250824_100752/NDVI_Vegetation_Analysis.kml", "🌱 NDVI (Vegetation) - Blue Borders"),
        ("output/20250824_100752/NDBI_BuiltUp_Analysis.kml", "🏢 NDBI (Built-up Areas) - Red Borders"),
        ("output/20250824_100752/NDWI_Water_Analysis.kml", "💧 NDWI (Water/Moisture) - Yellow Borders"),
        ("output/20250824_100752/enhanced_significant_indices_squares.kml", "🌍 Combined (All Indices) - Multi-color")
    ]
    
    print("🌐 Google Earth Web URL Generator")
    print("=" * 60)
    print("Generating URLs with base64-encoded KML data...")
    print("=" * 60)
    
    results = generator.generate_all_urls(kml_files)
    
    # Save results to file
    output_file = "google_earth_urls_correct_format.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("🌐 GOOGLE EARTH WEB URLs (CORRECT FORMAT)\n")
        f.write("=" * 60 + "\n")
        f.write("URLs with base64-encoded KML data - Ready to use!\n")
        f.write("=" * 60 + "\n\n")
        
        for description, result in results.items():
            f.write(f"📁 {description}\n")
            f.write(f"📄 File: {result['file']}\n")
            f.write(f"✅ Status: {result['status']}\n")
            
            if result['url']:
                f.write(f"🔗 URL: {result['url']}\n")
            else:
                f.write(f"❌ Failed to generate URL\n")
            
            f.write("\n" + "-" * 40 + "\n\n")
    
    print(f"✅ Results saved to: {output_file}")
    
    # Print summary
    successful = sum(1 for r in results.values() if r['status'] == 'success')
    total = len(results)
    print(f"📊 Summary: {successful}/{total} URLs generated successfully")


if __name__ == "__main__":
    main()
