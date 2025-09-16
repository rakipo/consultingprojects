#!/usr/bin/env python3
"""
Google Earth Engine Solution for KML Import
Creates Earth Engine scripts that can import KML files and display overlays
"""

import os
from typing import Dict


class EarthEngineSolution:
    def __init__(self):
        self.base_url = "https://code.earthengine.google.com/"
    
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
    
    def create_earth_engine_script(self, kml_path: str, description: str) -> str:
        """Create Google Earth Engine JavaScript code to import KML"""
        coords = self.extract_coordinates_from_kml(kml_path)
        filename = os.path.basename(kml_path)
        
        script = f"""
// Google Earth Engine Script for {description}
// This script imports KML files and displays them as overlays

// Set the map center to the analysis area
Map.setCenter({coords['lon']}, {coords['lat']}, 15);

// Method 1: Import KML from Google Drive (if uploaded)
// var kml = ee.FeatureCollection('users/your_username/{filename}');

// Method 2: Import KML from Google Cloud Storage (if uploaded)
// var kml = ee.FeatureCollection('gs://your-bucket/{filename}');

// Method 3: Create features manually from coordinates
// This is a simplified version - you'll need to add actual coordinates

// Example: Create a simple rectangle around the area
var bounds = ee.Geometry.Rectangle([
  {coords['lon'] - 0.01}, {coords['lat'] - 0.01},
  {coords['lon'] + 0.01}, {coords['lat'] + 0.01}
]);

// Add the boundary to the map
Map.addLayer(bounds, {{color: 'red'}}, 'Analysis Area Boundary');

// Add satellite imagery
var sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR')
  .filterBounds(bounds)
  .filterDate('2023-08-01', '2023-08-31')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
  .first();

Map.addLayer(sentinel2, {{
  bands: ['B4', 'B3', 'B2'],
  min: 0,
  max: 3000
}}, 'Sentinel-2 Satellite Image');

// Instructions for importing KML
print('📋 TO IMPORT YOUR KML FILE:');
print('1. Upload your KML file to Google Drive or Google Cloud Storage');
print('2. Replace the commented lines above with your actual KML import');
print('3. The overlays will appear on the satellite imagery');
print('4. File: {filename}');
print('5. Location: {coords['lat']}, {coords['lon']}');

// Add analysis information
var info = ee.Dictionary({{
  'Analysis': '{description}',
  'File': '{filename}',
  'Center': [{coords['lat']}, {coords['lon']}],
  'Date': '2023-08-09 to 2023-08-16'
}});

print('📊 Analysis Information:', info);
"""
        
        return script
    
    def create_google_maps_api_solution(self, kml_path: str, description: str) -> str:
        """Create Google Maps API solution"""
        coords = self.extract_coordinates_from_kml(kml_path)
        filename = os.path.basename(kml_path)
        
        solution = f"""
🗺️ GOOGLE MAPS API SOLUTION:

1️⃣ GOOGLE MAPS WITH KML OVERLAY:
   • URL: https://www.google.com/maps?q={coords['lat']},{coords['lon']}&z=15
   • Upload your KML file to Google Drive
   • Share the file publicly
   • Use the sharing URL in Google Maps

2️⃣ GOOGLE MAPS EMBED API:
   • Create a custom map with your KML overlay
   • Use Google Maps JavaScript API
   • Import KML using the API

3️⃣ GOOGLE MY MAPS:
   • Go to https://www.google.com/mymaps
   • Create a new map
   • Import your KML file
   • Share the map publicly

📁 FILE: {filename}
📍 LOCATION: {coords['lat']}, {coords['lon']}
"""
        
        return solution
    
    def create_github_pages_solution(self, kml_path: str, description: str) -> str:
        """Create GitHub Pages solution for hosting KML files"""
        filename = os.path.basename(kml_path)
        
        solution = f"""
🌐 GITHUB PAGES SOLUTION:

1️⃣ CREATE GITHUB REPOSITORY:
   • Go to https://github.com/new
   • Create a new repository (e.g., "kml-overlays")
   • Upload your KML files

2️⃣ ENABLE GITHUB PAGES:
   • Go to Settings → Pages
   • Select "Deploy from a branch"
   • Choose "main" branch
   • Your KML files will be available at:
     https://yourusername.github.io/kml-overlays/{filename}

3️⃣ USE IN GOOGLE EARTH WEB:
   • Go to https://earth.google.com/web/
   • Click "Projects" → "Import KML file from URL"
   • Use the GitHub Pages URL
   • The overlays will appear!

📁 FILE: {filename}
🔗 EXAMPLE URL: https://yourusername.github.io/kml-overlays/{filename}
"""
        
        return solution
    
    def generate_solutions(self, kml_files: list) -> Dict:
        """Generate multiple solutions for KML import"""
        results = {}
        
        for kml_path, description in kml_files:
            print(f"📁 Processing: {description}")
            print(f"   File: {kml_path}")
            
            # Generate different solutions
            earth_engine_script = self.create_earth_engine_script(kml_path, description)
            maps_solution = self.create_google_maps_api_solution(kml_path, description)
            github_solution = self.create_github_pages_solution(kml_path, description)
            
            results[description] = {
                'file': kml_path,
                'earth_engine_script': earth_engine_script,
                'maps_solution': maps_solution,
                'github_solution': github_solution,
                'status': 'success'
            }
            
            print(f"   ✅ Solutions generated successfully")
            print()
        
        return results


def main():
    """Main function"""
    generator = EarthEngineSolution()
    
    # Define KML files
    kml_files = [
        ("output/20250824_100752/NDVI_Vegetation_Analysis.kml", "🌱 NDVI (Vegetation) - Blue Borders"),
        ("output/20250824_100752/NDBI_BuiltUp_Analysis.kml", "🏢 NDBI (Built-up Areas) - Red Borders"),
        ("output/20250824_100752/NDWI_Water_Analysis.kml", "💧 NDWI (Water/Moisture) - Yellow Borders"),
        ("output/20250824_100752/enhanced_significant_indices_squares.kml", "🌍 Combined (All Indices) - Multi-color")
    ]
    
    print("🌐 Google Earth Engine API Solutions")
    print("=" * 60)
    print("Creating multiple solutions for KML import")
    print("=" * 60)
    
    results = generator.generate_solutions(kml_files)
    
    # Save results to file
    output_file = "earth_engine_solutions.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("🌐 GOOGLE EARTH ENGINE API SOLUTIONS\n")
        f.write("=" * 60 + "\n")
        f.write("Multiple solutions for importing KML files\n")
        f.write("=" * 60 + "\n\n")
        
        for description, result in results.items():
            f.write(f"📁 {description}\n")
            f.write(f"📄 File: {result['file']}\n")
            f.write(f"✅ Status: {result['status']}\n")
            
            f.write(f"\n🔧 EARTH ENGINE SCRIPT:\n")
            f.write(result['earth_engine_script'])
            
            f.write(f"\n🗺️ GOOGLE MAPS SOLUTION:\n")
            f.write(result['maps_solution'])
            
            f.write(f"\n🌐 GITHUB PAGES SOLUTION:\n")
            f.write(result['github_solution'])
            
            f.write("\n" + "-" * 40 + "\n\n")
    
    print(f"✅ Results saved to: {output_file}")
    
    # Print summary
    successful = sum(1 for r in results.values() if r['status'] == 'success')
    total = len(results)
    print(f"📊 Summary: {successful}/{total} solutions generated successfully")
    
    print("\n" + "=" * 60)
    print("🚀 AVAILABLE SOLUTIONS:")
    print("1. Google Earth Engine Scripts (for advanced analysis)")
    print("2. Google Maps API (for web applications)")
    print("3. GitHub Pages (for public hosting)")
    print("4. Manual upload to Google Earth Web")
    print("=" * 60)


if __name__ == "__main__":
    main()
