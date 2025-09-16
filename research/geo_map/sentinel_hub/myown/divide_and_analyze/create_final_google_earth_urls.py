#!/usr/bin/env python3
"""
Create final working Google Earth Web URLs
Short URLs that navigate to location + clear instructions for KML upload
"""

import os
from typing import Dict


class FinalGoogleEarthURLGenerator:
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
    
    def count_placemarks(self, kml_path: str) -> int:
        """Count number of placemarks in KML file"""
        try:
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(kml_path)
            root = tree.getroot()
            namespace = {'kml': 'http://www.opengis.net/kml/2.2'}
            
            placemarks = root.findall('.//kml:Placemark', namespace)
            return len(placemarks)
            
        except Exception as e:
            return 0
    
    def build_short_url(self, kml_path: str) -> str:
        """Build short Google Earth Web URL"""
        if not os.path.exists(kml_path):
            print(f"❌ KML file not found: {kml_path}")
            return None
        
        coords = self.extract_coordinates_from_kml(kml_path)
        return f"{self.base_url}@{coords['lat']},{coords['lon']},2000a,2000d,35y,0h,0t,0r"
    
    def build_search_url(self, kml_path: str) -> str:
        """Build Google Earth search URL"""
        if not os.path.exists(kml_path):
            return None
        
        coords = self.extract_coordinates_from_kml(kml_path)
        return f"https://earth.google.com/web/search/{coords['lat']},{coords['lon']}"
    
    def create_upload_instructions(self, kml_path: str, description: str) -> str:
        """Create step-by-step upload instructions"""
        placemark_count = self.count_placemarks(kml_path)
        filename = os.path.basename(kml_path)
        
        instructions = f"""
📋 STEP-BY-STEP INSTRUCTIONS TO SEE THE OVERLAYS:

1️⃣ OPEN GOOGLE EARTH WEB:
   • Use the URL above to navigate to the location
   • Or go to https://earth.google.com/web/

2️⃣ UPLOAD KML FILE:
   • Click the "Projects" button (📁 folder icon) in the left sidebar
   • Click "Import KML file from device"
   • Select this file: {filename}
   • Click "Open"

3️⃣ VIEW THE OVERLAYS:
   • The {placemark_count} colored squares should appear on the map
   • {description}
   • You can click on each square to see details

4️⃣ ALTERNATIVE METHOD:
   • Go to https://earth.google.com/web/
   • Click "Projects" → "Import KML file from device"
   • Select your KML file
   • Navigate to the location manually

📁 FILE LOCATION: {kml_path}
"""
        return instructions
    
    def generate_final_urls(self, kml_files: list) -> Dict:
        """Generate final URLs and instructions"""
        results = {}
        
        for kml_path, description in kml_files:
            print(f"📁 Processing: {description}")
            print(f"   File: {kml_path}")
            
            # Generate URLs
            short_url = self.build_short_url(kml_path)
            search_url = self.build_search_url(kml_path)
            instructions = self.create_upload_instructions(kml_path, description)
            
            if short_url:
                results[description] = {
                    'file': kml_path,
                    'short_url': short_url,
                    'search_url': search_url,
                    'instructions': instructions,
                    'status': 'success'
                }
                print(f"   ✅ URLs and instructions generated successfully")
                print(f"   🔗 Short URL: {short_url}")
            else:
                results[description] = {
                    'file': kml_path,
                    'short_url': None,
                    'search_url': None,
                    'instructions': None,
                    'status': 'failed'
                }
                print(f"   ❌ Failed to generate URLs")
            
            print()
        
        return results


def main():
    """Main function"""
    generator = FinalGoogleEarthURLGenerator()
    
    # Define KML files
    kml_files = [
        ("output/20250824_100752/NDVI_Vegetation_Analysis.kml", "🌱 NDVI (Vegetation) - Blue Borders"),
        ("output/20250824_100752/NDBI_BuiltUp_Analysis.kml", "🏢 NDBI (Built-up Areas) - Red Borders"),
        ("output/20250824_100752/NDWI_Water_Analysis.kml", "💧 NDWI (Water/Moisture) - Yellow Borders"),
        ("output/20250824_100752/enhanced_significant_indices_squares.kml", "🌍 Combined (All Indices) - Multi-color")
    ]
    
    print("🌐 Final Google Earth Web URL Generator")
    print("=" * 60)
    print("Generating short, working URLs + upload instructions")
    print("=" * 60)
    
    results = generator.generate_final_urls(kml_files)
    
    # Save results to file
    output_file = "final_google_earth_urls.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("🌐 FINAL GOOGLE EARTH WEB URLs\n")
        f.write("=" * 60 + "\n")
        f.write("Short URLs + Step-by-step upload instructions\n")
        f.write("=" * 60 + "\n\n")
        
        for description, result in results.items():
            f.write(f"📁 {description}\n")
            f.write(f"📄 File: {result['file']}\n")
            f.write(f"✅ Status: {result['status']}\n")
            
            if result['short_url']:
                f.write(f"🔗 Short URL: {result['short_url']}\n")
                f.write(f"🔍 Search URL: {result['search_url']}\n")
                f.write(result['instructions'])
            else:
                f.write(f"❌ Failed to generate URLs\n")
            
            f.write("\n" + "-" * 40 + "\n\n")
    
    print(f"✅ Results saved to: {output_file}")
    
    # Print summary
    successful = sum(1 for r in results.values() if r['status'] == 'success')
    total = len(results)
    print(f"📊 Summary: {successful}/{total} URL sets generated successfully")
    
    print("\n" + "=" * 60)
    print("🚀 QUICK START:")
    print("1. Use the Short URLs to navigate to the location")
    print("2. Follow the step-by-step instructions to upload KML files")
    print("3. You'll see the colored squares appear on the map!")
    print("=" * 60)


if __name__ == "__main__":
    main()
