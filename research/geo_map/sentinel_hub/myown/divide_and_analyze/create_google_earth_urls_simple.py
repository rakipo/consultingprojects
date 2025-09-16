#!/usr/bin/env python3
"""
Create simple Google Earth Web URLs that navigate to the location
without embedding KML data (which causes 400 errors due to URL length)
"""

import os
from typing import Dict


class SimpleGoogleEarthURLGenerator:
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
    
    def build_simple_google_earth_url(self, kml_path: str) -> str:
        """Build simple Google Earth Web URL that navigates to location"""
        if not os.path.exists(kml_path):
            print(f"❌ KML file not found: {kml_path}")
            return None
        
        # Extract coordinates
        coords = self.extract_coordinates_from_kml(kml_path)
        
        # Build simple URL that just navigates to the location
        url = f"{self.base_url}@{coords['lat']},{coords['lon']},2000a,2000d,35y,0h,0t,0r"
        
        return url
    
    def build_search_url(self, kml_path: str) -> str:
        """Build Google Earth search URL"""
        if not os.path.exists(kml_path):
            return None
        
        coords = self.extract_coordinates_from_kml(kml_path)
        search_url = f"https://earth.google.com/web/search/{coords['lat']},{coords['lon']}"
        return search_url
    
    def generate_all_urls(self, kml_files: list) -> Dict:
        """Generate URLs for all KML files"""
        results = {}
        
        for kml_path, description in kml_files:
            print(f"📁 Processing: {description}")
            print(f"   File: {kml_path}")
            
            # Generate simple navigation URL
            nav_url = self.build_simple_google_earth_url(kml_path)
            search_url = self.build_search_url(kml_path)
            
            if nav_url:
                results[description] = {
                    'file': kml_path,
                    'navigation_url': nav_url,
                    'search_url': search_url,
                    'status': 'success'
                }
                print(f"   ✅ URLs generated successfully")
                print(f"   🔗 Navigation: {nav_url}")
                print(f"   🔍 Search: {search_url}")
            else:
                results[description] = {
                    'file': kml_path,
                    'navigation_url': None,
                    'search_url': None,
                    'status': 'failed'
                }
                print(f"   ❌ Failed to generate URLs")
            
            print()
        
        return results


def main():
    """Main function"""
    generator = SimpleGoogleEarthURLGenerator()
    
    # Define KML files
    kml_files = [
        ("output/20250824_100752/NDVI_Vegetation_Analysis.kml", "🌱 NDVI (Vegetation) - Blue Borders"),
        ("output/20250824_100752/NDBI_BuiltUp_Analysis.kml", "🏢 NDBI (Built-up Areas) - Red Borders"),
        ("output/20250824_100752/NDWI_Water_Analysis.kml", "💧 NDWI (Water/Moisture) - Yellow Borders"),
        ("output/20250824_100752/enhanced_significant_indices_squares.kml", "🌍 Combined (All Indices) - Multi-color")
    ]
    
    print("🌐 Simple Google Earth Web URL Generator")
    print("=" * 60)
    print("Generating short URLs that navigate to the location...")
    print("Note: These URLs will navigate to the area but won't show KML overlays")
    print("=" * 60)
    
    results = generator.generate_all_urls(kml_files)
    
    # Save results to file
    output_file = "google_earth_urls_simple.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("🌐 SIMPLE GOOGLE EARTH WEB URLs\n")
        f.write("=" * 60 + "\n")
        f.write("Short URLs that navigate to the location (no KML overlay)\n")
        f.write("=" * 60 + "\n\n")
        
        for description, result in results.items():
            f.write(f"📁 {description}\n")
            f.write(f"📄 File: {result['file']}\n")
            f.write(f"✅ Status: {result['status']}\n")
            
            if result['navigation_url']:
                f.write(f"🔗 Navigation URL: {result['navigation_url']}\n")
                f.write(f"🔍 Search URL: {result['search_url']}\n")
            else:
                f.write(f"❌ Failed to generate URLs\n")
            
            f.write("\n" + "-" * 40 + "\n\n")
    
    print(f"✅ Results saved to: {output_file}")
    
    # Print summary
    successful = sum(1 for r in results.values() if r['status'] == 'success')
    total = len(results)
    print(f"📊 Summary: {successful}/{total} URL sets generated successfully")
    
    print("\n" + "=" * 60)
    print("📋 NEXT STEPS:")
    print("1. Use the Navigation URLs to go to the location")
    print("2. Manually upload the KML files to see the overlays")
    print("3. Or use a local web server to host the KML files")
    print("=" * 60)


if __name__ == "__main__":
    main()
