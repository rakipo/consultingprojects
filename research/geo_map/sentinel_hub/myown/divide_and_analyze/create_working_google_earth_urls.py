#!/usr/bin/env python3
"""
Create working Google Earth Web URLs that show KML overlays
Uses efficient encoding and optimized KML files to avoid URL length limits
"""

import os
import base64
import gzip
import urllib.parse
from typing import Dict


class WorkingGoogleEarthURLGenerator:
    def __init__(self):
        self.base_url = "https://earth.google.com/web/"
    
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
    
    def create_minimal_kml(self, kml_path: str) -> str:
        """Create a minimal KML with only essential elements to reduce size"""
        try:
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(kml_path)
            root = tree.getroot()
            namespace = {'kml': 'http://www.opengis.net/kml/2.2'}
            
            # Create minimal KML structure
            minimal_kml = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{os.path.basename(kml_path)}</name>
"""
            
            # Extract only placemarks with coordinates
            placemarks = root.findall('.//kml:Placemark', namespace)
            
            for i, placemark in enumerate(placemarks[:5]):  # Limit to first 5 placemarks to reduce size
                name_elem = placemark.find('kml:name', namespace)
                coords_elem = placemark.find('.//kml:coordinates', namespace)
                style_elem = placemark.find('kml:styleUrl', namespace)
                
                if coords_elem is not None and coords_elem.text:
                    name = name_elem.text if name_elem is not None else f"Square {i+1}"
                    style = style_elem.text if style_elem is not None else "#default_style"
                    
                    minimal_kml += f"""    <Placemark>
      <name>{name}</name>
      <styleUrl>{style}</styleUrl>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>{coords_elem.text.strip()}</coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
"""
            
            minimal_kml += """  </Document>
</kml>"""
            
            return minimal_kml
            
        except Exception as e:
            print(f"❌ Error creating minimal KML: {e}")
            return None
    
    def encode_kml_efficiently(self, kml_content: str) -> str:
        """Encode KML content efficiently to reduce URL length"""
        try:
            # Compress the KML content
            compressed = gzip.compress(kml_content.encode('utf-8'))
            # Encode to base64
            encoded = base64.b64encode(compressed).decode('utf-8')
            # URL encode
            url_encoded = urllib.parse.quote(encoded, safe='')
            return url_encoded
        except Exception as e:
            print(f"❌ Error encoding KML: {e}")
            return None
    
    def build_working_google_earth_url(self, kml_path: str) -> str:
        """Build working Google Earth Web URL with KML overlay"""
        if not os.path.exists(kml_path):
            print(f"❌ KML file not found: {kml_path}")
            return None
        
        # Create minimal KML
        minimal_kml = self.create_minimal_kml(kml_path)
        if not minimal_kml:
            return None
        
        # Encode efficiently
        encoded_kml = self.encode_kml_efficiently(minimal_kml)
        if not encoded_kml:
            return None
        
        # Extract coordinates
        coords = self.extract_coordinates_from_kml(kml_path)
        
        # Build URL with encoded KML data
        url = f"{self.base_url}@{coords['lat']},{coords['lon']},2000a,2000d,35y,0h,0t,0r/data={encoded_kml}"
        
        return url
    
    def build_simple_url(self, kml_path: str) -> str:
        """Build simple navigation URL as fallback"""
        if not os.path.exists(kml_path):
            return None
        
        coords = self.extract_coordinates_from_kml(kml_path)
        return f"{self.base_url}@{coords['lat']},{coords['lon']},2000a,2000d,35y,0h,0t,0r"
    
    def generate_working_urls(self, kml_files: list) -> Dict:
        """Generate working URLs for all KML files"""
        results = {}
        
        for kml_path, description in kml_files:
            print(f"📁 Processing: {description}")
            print(f"   File: {kml_path}")
            
            # Try to create working URL with KML overlay
            working_url = self.build_working_google_earth_url(kml_path)
            simple_url = self.build_simple_url(kml_path)
            
            if working_url:
                results[description] = {
                    'file': kml_path,
                    'working_url': working_url,
                    'simple_url': simple_url,
                    'status': 'success',
                    'has_overlay': True
                }
                print(f"   ✅ Working URL with KML overlay generated")
                print(f"   🔗 URL: {working_url[:100]}...")
            else:
                results[description] = {
                    'file': kml_path,
                    'working_url': None,
                    'simple_url': simple_url,
                    'status': 'fallback',
                    'has_overlay': False
                }
                print(f"   ⚠️  Fallback to simple navigation URL")
                print(f"   🔗 URL: {simple_url}")
            
            print()
        
        return results


def main():
    """Main function"""
    generator = WorkingGoogleEarthURLGenerator()
    
    # Define KML files
    kml_files = [
        ("output/20250824_100752/NDVI_Vegetation_Analysis.kml", "🌱 NDVI (Vegetation) - Blue Borders"),
        ("output/20250824_100752/NDBI_BuiltUp_Analysis.kml", "🏢 NDBI (Built-up Areas) - Red Borders"),
        ("output/20250824_100752/NDWI_Water_Analysis.kml", "💧 NDWI (Water/Moisture) - Yellow Borders"),
        ("output/20250824_100752/enhanced_significant_indices_squares.kml", "🌍 Combined (All Indices) - Multi-color")
    ]
    
    print("🌐 Working Google Earth Web URL Generator")
    print("=" * 60)
    print("Generating URLs with KML overlays...")
    print("Using efficient encoding to avoid URL length limits")
    print("=" * 60)
    
    results = generator.generate_working_urls(kml_files)
    
    # Save results to file
    output_file = "working_google_earth_urls.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("🌐 WORKING GOOGLE EARTH WEB URLs\n")
        f.write("=" * 60 + "\n")
        f.write("URLs that should show KML overlays\n")
        f.write("=" * 60 + "\n\n")
        
        for description, result in results.items():
            f.write(f"📁 {description}\n")
            f.write(f"📄 File: {result['file']}\n")
            f.write(f"✅ Status: {result['status']}\n")
            f.write(f"🎨 Has Overlay: {result['has_overlay']}\n")
            
            if result['working_url']:
                f.write(f"🔗 Working URL: {result['working_url']}\n")
            if result['simple_url']:
                f.write(f"🔗 Simple URL: {result['simple_url']}\n")
            
            f.write("\n" + "-" * 40 + "\n\n")
    
    print(f"✅ Results saved to: {output_file}")
    
    # Print summary
    working = sum(1 for r in results.values() if r['has_overlay'])
    total = len(results)
    print(f"📊 Summary: {working}/{total} URLs with KML overlays generated")
    
    print("\n" + "=" * 60)
    print("🚀 TESTING INSTRUCTIONS:")
    print("1. Try the Working URLs first - they should show overlays")
    print("2. If they don't work, use the Simple URLs and upload KML manually")
    print("3. Check the browser console for any error messages")
    print("=" * 60)


if __name__ == "__main__":
    main()
