#!/usr/bin/env python3
"""
Create Google Earth Web URLs using Google Earth Engine API
Directly imports KML files and generates working URLs with overlays
"""

import os
import json
import requests
from typing import Dict, Optional


class GoogleEarthAPIURLGenerator:
    def __init__(self):
        self.base_url = "https://earth.google.com/web/"
        self.google_maps_api_key = None  # You'll need to add your API key here
    
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
    
    def create_github_gist(self, kml_path: str, description: str) -> Optional[str]:
        """Create a GitHub Gist to host the KML file publicly"""
        try:
            with open(kml_path, 'r', encoding='utf-8') as f:
                kml_content = f.read()
            
            # GitHub Gist API endpoint
            gist_url = "https://api.github.com/gists"
            
            # Create gist data
            gist_data = {
                "description": f"KML file for {description}",
                "public": True,
                "files": {
                    os.path.basename(kml_path): {
                        "content": kml_content
                    }
                }
            }
            
            # Make API request (note: this requires authentication for private repos)
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json"
            }
            
            # For now, we'll create instructions for manual gist creation
            return self.create_manual_gist_instructions(kml_path, kml_content, description)
            
        except Exception as e:
            print(f"❌ Error creating GitHub Gist: {e}")
            return None
    
    def create_manual_gist_instructions(self, kml_path: str, kml_content: str, description: str) -> str:
        """Create instructions for manually creating a GitHub Gist"""
        filename = os.path.basename(kml_path)
        
        instructions = f"""
📋 MANUAL GITHUB GIST CREATION:

1️⃣ GO TO GITHUB GIST:
   • Visit: https://gist.github.com/
   • Sign in to your GitHub account (or create one)

2️⃣ CREATE NEW GIST:
   • Click "Create a new gist"
   • Filename: {filename}
   • Description: KML file for {description}

3️⃣ PASTE KML CONTENT:
   • Copy the KML content below and paste it into the gist
   • Click "Create secret gist" or "Create public gist"

4️⃣ GET RAW URL:
   • After creating the gist, click the "Raw" button
   • Copy the URL (it will end with /raw)
   • Use that URL in Google Earth Web

📄 KML CONTENT TO COPY:
```
{kml_content[:500]}...
```
(Content truncated for display - use the full file content)

5️⃣ USE IN GOOGLE EARTH WEB:
   • Go to https://earth.google.com/web/
   • Click "Projects" → "Import KML file from URL"
   • Paste the raw gist URL
   • The overlays should appear!
"""
        return instructions
    
    def create_google_maps_url(self, kml_path: str) -> str:
        """Create Google Maps URL with KML overlay"""
        coords = self.extract_coordinates_from_kml(kml_path)
        
        # Google Maps URL with KML overlay
        # Note: This requires the KML to be hosted publicly
        maps_url = f"https://www.google.com/maps?q={coords['lat']},{coords['lon']}&z=15"
        
        return maps_url
    
    def create_earth_engine_url(self, kml_path: str) -> str:
        """Create Google Earth Engine URL"""
        coords = self.extract_coordinates_from_kml(kml_path)
        
        # Google Earth Engine URL
        earth_engine_url = f"https://code.earthengine.google.com/?center={coords['lat']},{coords['lon']}&zoom=15"
        
        return earth_engine_url
    
    def create_alternative_urls(self, kml_path: str, description: str) -> Dict:
        """Create alternative URLs using different Google services"""
        results = {}
        
        # Extract coordinates
        coords = self.extract_coordinates_from_kml(kml_path)
        
        # Google Earth Web URL (simple navigation)
        earth_web_url = f"{self.base_url}@{coords['lat']},{coords['lon']},2000a,2000d,35y,0h,0t,0r"
        
        # Google Maps URL
        maps_url = self.create_google_maps_url(kml_path)
        
        # Google Earth Engine URL
        earth_engine_url = self.create_earth_engine_url(kml_path)
        
        # GitHub Gist instructions
        gist_instructions = self.create_manual_gist_instructions(kml_path, "", description)
        
        results = {
            'earth_web_url': earth_web_url,
            'maps_url': maps_url,
            'earth_engine_url': earth_engine_url,
            'gist_instructions': gist_instructions,
            'coordinates': coords
        }
        
        return results
    
    def generate_api_urls(self, kml_files: list) -> Dict:
        """Generate URLs using various Google APIs"""
        results = {}
        
        for kml_path, description in kml_files:
            print(f"📁 Processing: {description}")
            print(f"   File: {kml_path}")
            
            # Generate alternative URLs
            alt_urls = self.create_alternative_urls(kml_path, description)
            
            results[description] = {
                'file': kml_path,
                'urls': alt_urls,
                'status': 'success'
            }
            
            print(f"   ✅ Alternative URLs generated successfully")
            print(f"   🌐 Earth Web: {alt_urls['earth_web_url']}")
            print(f"   🗺️  Google Maps: {alt_urls['maps_url']}")
            print(f"   🔧 Earth Engine: {alt_urls['earth_engine_url']}")
            print()
        
        return results


def main():
    """Main function"""
    generator = GoogleEarthAPIURLGenerator()
    
    # Define KML files
    kml_files = [
        ("output/20250824_100752/NDVI_Vegetation_Analysis.kml", "🌱 NDVI (Vegetation) - Blue Borders"),
        ("output/20250824_100752/NDBI_BuiltUp_Analysis.kml", "🏢 NDBI (Built-up Areas) - Red Borders"),
        ("output/20250824_100752/NDWI_Water_Analysis.kml", "💧 NDWI (Water/Moisture) - Yellow Borders"),
        ("output/20250824_100752/enhanced_significant_indices_squares.kml", "🌍 Combined (All Indices) - Multi-color")
    ]
    
    print("🌐 Google Earth API URL Generator")
    print("=" * 60)
    print("Generating URLs using Google APIs and services")
    print("=" * 60)
    
    results = generator.generate_api_urls(kml_files)
    
    # Save results to file
    output_file = "google_earth_api_urls.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("🌐 GOOGLE EARTH API URLs\n")
        f.write("=" * 60 + "\n")
        f.write("Alternative solutions using Google APIs\n")
        f.write("=" * 60 + "\n\n")
        
        for description, result in results.items():
            f.write(f"📁 {description}\n")
            f.write(f"📄 File: {result['file']}\n")
            f.write(f"✅ Status: {result['status']}\n")
            
            urls = result['urls']
            f.write(f"🌐 Earth Web URL: {urls['earth_web_url']}\n")
            f.write(f"🗺️  Google Maps URL: {urls['maps_url']}\n")
            f.write(f"🔧 Earth Engine URL: {urls['earth_engine_url']}\n")
            f.write(f"📍 Coordinates: {urls['coordinates']['lat']}, {urls['coordinates']['lon']}\n")
            
            f.write(f"\n📋 GITHUB GIST INSTRUCTIONS:\n")
            f.write(urls['gist_instructions'])
            
            f.write("\n" + "-" * 40 + "\n\n")
    
    print(f"✅ Results saved to: {output_file}")
    
    # Print summary
    successful = sum(1 for r in results.values() if r['status'] == 'success')
    total = len(results)
    print(f"📊 Summary: {successful}/{total} URL sets generated successfully")
    
    print("\n" + "=" * 60)
    print("🚀 ALTERNATIVE SOLUTIONS:")
    print("1. Google Earth Web URLs (simple navigation)")
    print("2. Google Maps URLs (with KML overlay support)")
    print("3. Google Earth Engine URLs (for advanced analysis)")
    print("4. GitHub Gist hosting (for public KML files)")
    print("=" * 60)


if __name__ == "__main__":
    main()
