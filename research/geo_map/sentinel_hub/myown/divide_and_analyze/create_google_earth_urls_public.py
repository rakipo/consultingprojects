#!/usr/bin/env python3
"""
Create Google Earth Web URLs that work with public hosting
No local server required - uses public file hosting services
"""

import os
import base64
import urllib.parse
from typing import Dict


class PublicGoogleEarthURLGenerator:
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
    
    def create_github_gist_url(self, kml_path: str, description: str) -> str:
        """Create instructions for GitHub Gist hosting"""
        try:
            with open(kml_path, 'r', encoding='utf-8') as f:
                kml_content = f.read()
            
            # Create GitHub Gist instructions
            gist_instructions = f"""
📋 To host this KML file publicly:

1. Go to https://gist.github.com/
2. Create a new gist with filename: {os.path.basename(kml_path)}
3. Paste this content:
```
{kml_content}
```
4. Click "Create secret gist"
5. Copy the "Raw" URL (ends with /raw)
6. Use that URL in Google Earth Web

Alternative: Use any file hosting service like:
- GitHub (create a repository)
- Dropbox (get shareable link)
- Google Drive (get shareable link)
- Pastebin (for smaller files)
"""
            return gist_instructions
            
        except Exception as e:
            return f"❌ Error reading KML file: {e}"
    
    def build_google_earth_url_with_kml(self, kml_path: str, public_url: str = None) -> str:
        """Build Google Earth Web URL with KML overlay"""
        if not os.path.exists(kml_path):
            print(f"❌ KML file not found: {kml_path}")
            return None
        
        # Extract coordinates
        coords = self.extract_coordinates_from_kml(kml_path)
        
        if public_url:
            # Build URL with KML overlay from public URL
            encoded_url = urllib.parse.quote(public_url, safe='')
            url = f"{self.base_url}@{coords['lat']},{coords['lon']},2000a,2000d,35y,0h,0t,0r/data={encoded_url}"
        else:
            # Build simple navigation URL
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
        """Generate URLs and hosting instructions for all KML files"""
        results = {}
        
        for kml_path, description in kml_files:
            print(f"📁 Processing: {description}")
            print(f"   File: {kml_path}")
            
            # Generate navigation URL
            nav_url = self.build_google_earth_url_with_kml(kml_path)
            search_url = self.build_search_url(kml_path)
            
            # Create hosting instructions
            hosting_instructions = self.create_github_gist_url(kml_path, description)
            
            if nav_url:
                results[description] = {
                    'file': kml_path,
                    'navigation_url': nav_url,
                    'search_url': search_url,
                    'hosting_instructions': hosting_instructions,
                    'status': 'success'
                }
                print(f"   ✅ URLs and instructions generated successfully")
                print(f"   🔗 Navigation: {nav_url}")
                print(f"   🔍 Search: {search_url}")
            else:
                results[description] = {
                    'file': kml_path,
                    'navigation_url': None,
                    'search_url': None,
                    'hosting_instructions': None,
                    'status': 'failed'
                }
                print(f"   ❌ Failed to generate URLs")
            
            print()
        
        return results


def main():
    """Main function"""
    generator = PublicGoogleEarthURLGenerator()
    
    # Define KML files
    kml_files = [
        ("output/20250824_100752/NDVI_Vegetation_Analysis.kml", "🌱 NDVI (Vegetation) - Blue Borders"),
        ("output/20250824_100752/NDBI_BuiltUp_Analysis.kml", "🏢 NDBI (Built-up Areas) - Red Borders"),
        ("output/20250824_100752/NDWI_Water_Analysis.kml", "💧 NDWI (Water/Moisture) - Yellow Borders"),
        ("output/20250824_100752/enhanced_significant_indices_squares.kml", "🌍 Combined (All Indices) - Multi-color")
    ]
    
    print("🌐 Public Google Earth Web URL Generator")
    print("=" * 60)
    print("Generating URLs and hosting instructions...")
    print("No local server required - uses public hosting")
    print("=" * 60)
    
    results = generator.generate_all_urls(kml_files)
    
    # Save results to file
    output_file = "google_earth_urls_public_hosting.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("🌐 GOOGLE EARTH WEB URLs WITH PUBLIC HOSTING\n")
        f.write("=" * 60 + "\n")
        f.write("Instructions for hosting KML files publicly\n")
        f.write("=" * 60 + "\n\n")
        
        for description, result in results.items():
            f.write(f"📁 {description}\n")
            f.write(f"📄 File: {result['file']}\n")
            f.write(f"✅ Status: {result['status']}\n")
            
            if result['navigation_url']:
                f.write(f"🔗 Navigation URL: {result['navigation_url']}\n")
                f.write(f"🔍 Search URL: {result['search_url']}\n")
                f.write(f"\n📋 HOSTING INSTRUCTIONS:\n")
                f.write(result['hosting_instructions'])
            else:
                f.write(f"❌ Failed to generate URLs\n")
            
            f.write("\n" + "-" * 40 + "\n\n")
    
    print(f"✅ Results saved to: {output_file}")
    
    # Print summary
    successful = sum(1 for r in results.values() if r['status'] == 'success')
    total = len(results)
    print(f"📊 Summary: {successful}/{total} URL sets generated successfully")
    
    print("\n" + "=" * 60)
    print("🚀 QUICK START GUIDE:")
    print("1. Use the Navigation URLs to go to the location")
    print("2. Follow the hosting instructions to upload KML files")
    print("3. Use the public URL in Google Earth Web")
    print("=" * 60)


if __name__ == "__main__":
    main()
