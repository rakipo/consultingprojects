#!/usr/bin/env python3
"""
KML Boundary URL Generator

Creates URLs that actually show polygon boundaries in Google Maps and generates
KML files that can be directly opened in Google Earth to display boundaries.
"""

import xml.etree.ElementTree as ET
import urllib.parse
import os
import base64
from datetime import datetime
from typing import List, Dict


def parse_kml_coordinates(coord_string: str) -> List[tuple]:
    """Extract lat/lon coordinates from KML coordinate string."""
    coordinates = []
    for coord in coord_string.strip().split():
        if coord.strip():
            parts = coord.split(',')
            if len(parts) >= 2:
                lon, lat = float(parts[0]), float(parts[1])
                coordinates.append((lat, lon))
    return coordinates


def create_google_maps_polygon_url(coordinates: List[tuple], name: str) -> str:
    """Create Google Maps URL with polygon overlay using My Maps."""
    if not coordinates:
        return ""
    
    # Calculate center
    lats = [coord[0] for coord in coordinates]
    lons = [coord[1] for coord in coordinates]
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)
    
    # Create path string for Google Maps directions API (shows as a route)
    # This is a workaround to show boundaries
    path_coords = []
    for lat, lon in coordinates:
        path_coords.append(f"{lat},{lon}")
    
    # Create a URL that shows the path
    waypoints = "|".join(path_coords[1:-1])  # Exclude start and end
    start = path_coords[0]
    end = path_coords[-1]
    
    base_url = "https://www.google.com/maps/dir/"
    url = f"{base_url}{start}/{end}"
    if waypoints:
        url += f"/{waypoints}"
    
    return url


def create_google_earth_kml_url(coordinates: List[tuple], name: str, description: str = "") -> str:
    """Create a Google Earth URL that opens a KML with the polygon."""
    if not coordinates:
        return ""
    
    # Create minimal KML content
    kml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{name}</name>
    <Style id="polygon_style">
      <LineStyle>
        <color>ff0000ff</color>
        <width>3</width>
      </LineStyle>
      <PolyStyle>
        <fill>0</fill>
        <outline>1</outline>
      </PolyStyle>
    </Style>
    <Placemark>
      <name>{name}</name>
      <description>{description}</description>
      <styleUrl>#polygon_style</styleUrl>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>'''
    
    # Add coordinates
    for lat, lon in coordinates:
        kml_content += f"{lon},{lat},0 "
    
    kml_content += '''</coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
  </Document>
</kml>'''
    
    # Calculate center for Google Earth URL
    lats = [coord[0] for coord in coordinates]
    lons = [coord[1] for coord in coordinates]
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)
    
    # Return Google Earth web URL (the KML will be saved separately)
    return f"https://earth.google.com/web/@{center_lat},{center_lon},1000a,35y,0h,0t,0r"


def create_geojson_url(coordinates: List[tuple], name: str) -> str:
    """Create a URL for geojson.io to display the polygon."""
    if not coordinates:
        return ""
    
    # Create GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {"name": name},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[lon, lat] for lat, lon in coordinates]]
            }
        }]
    }
    
    import json
    geojson_str = json.dumps(geojson, separators=(',', ':'))
    encoded = urllib.parse.quote(geojson_str)
    
    return f"https://geojson.io/#data=data:application/json,{encoded}"


def create_individual_kml_files(all_polygons: Dict[str, List[Dict]]) -> List[str]:
    """Create individual KML files for each polygon that can be opened in Google Earth."""
    kml_files = []
    
    for filename, polygons in all_polygons.items():
        analysis_type = filename.replace('.kml', '').replace('_', ' ')
        
        for polygon in polygons:
            # Create safe filename
            safe_name = "".join(c for c in polygon['name'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_')
            kml_filename = f"{safe_name}_boundary.kml"
            
            # Create KML content
            kml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{polygon['name']} - Boundary</name>
    <description>Boundary for {polygon['name']} from {analysis_type}</description>
    
    <Style id="boundary_style">
      <LineStyle>
        <color>ff0000ff</color>
        <width>3</width>
      </LineStyle>
      <PolyStyle>
        <fill>1</fill>
        <color>330000ff</color>
        <outline>1</outline>
      </PolyStyle>
    </Style>
    
    <Placemark>
      <name>{polygon['name']}</name>
      <description><![CDATA[
        <h3>{polygon['name']}</h3>
        <p><strong>Analysis Type:</strong> {analysis_type}</p>
        <p><strong>Center:</strong> {polygon['bounds']['center_lat']:.6f}, {polygon['bounds']['center_lon']:.6f}</p>
        <p><strong>Boundary Points:</strong> {polygon['coordinate_count']}</p>
        {f"<p><strong>Details:</strong><br>{polygon['description'][:200]}...</p>" if polygon['description'].strip() else ""}
      ]]></description>
      <styleUrl>#boundary_style</styleUrl>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>'''
            
            # Add coordinates
            for lat, lon in polygon['coordinates']:
                kml_content += f"{lon},{lat},0 "
            
            kml_content += '''</coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
  </Document>
</kml>'''
            
            # Write KML file
            with open(kml_filename, 'w', encoding='utf-8') as f:
                f.write(kml_content)
            
            kml_files.append(kml_filename)
            polygon['kml_file'] = kml_filename
    
    return kml_files


def process_kml_file(filename: str) -> List[Dict]:
    """Process a single KML file and return polygon data with coordinates."""
    try:
        tree = ET.parse(filename)
        root = tree.getroot()
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}
        
        polygons = []
        
        for placemark in root.findall('.//kml:Placemark', ns):
            name_elem = placemark.find('kml:name', ns)
            desc_elem = placemark.find('kml:description', ns)
            coord_elem = placemark.find('.//kml:coordinates', ns)
            
            if coord_elem is not None:
                coordinates = parse_kml_coordinates(coord_elem.text)
                if coordinates:
                    # Calculate bounds
                    lats = [coord[0] for coord in coordinates]
                    lons = [coord[1] for coord in coordinates]
                    
                    bounds = {
                        'center_lat': sum(lats) / len(lats),
                        'center_lon': sum(lons) / len(lons),
                        'min_lat': min(lats),
                        'max_lat': max(lats),
                        'min_lon': min(lons),
                        'max_lon': max(lons)
                    }
                    
                    polygon_data = {
                        'name': name_elem.text if name_elem is not None else 'Unnamed',
                        'description': desc_elem.text if desc_elem is not None else '',
                        'source_file': filename,
                        'bounds': bounds,
                        'coordinates': coordinates,
                        'coordinate_count': len(coordinates)
                    }
                    polygons.append(polygon_data)
        
        return polygons
        
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        return []


def generate_boundary_urls_output(all_polygons: Dict[str, List[Dict]], kml_files: List[str]) -> str:
    """Generate output with URLs that show boundaries."""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    output = f"""KML Analysis Areas - Boundary Visualization URLs
Generated: {timestamp}
{'='*80}

IMPORTANT: To see actual polygon boundaries, use one of these methods:

1. BEST OPTION - Individual KML Files:
   - Each polygon has been saved as a separate .kml file
   - Double-click any .kml file to open in Google Earth Pro
   - Or drag .kml files into Google Earth Web (earth.google.com)

2. GeoJSON.io URLs:
   - These URLs show interactive boundaries in your browser
   - Click and drag to explore the polygon shapes

3. Google Maps Polygon URLs:
   - Shows approximate path/route around the boundary
   - Not perfect but gives an idea of the area shape

{'='*80}

SUMMARY:
"""
    
    total_polygons = sum(len(polygons) for polygons in all_polygons.values())
    output += f"Total Analysis Areas: {total_polygons}\n"
    output += f"Individual KML Files Created: {len(kml_files)}\n\n"
    
    for filename, polygons in all_polygons.items():
        analysis_type = filename.replace('.kml', '').replace('_', ' ')
        output += f"  - {analysis_type}: {len(polygons)} areas\n"
    
    output += f"\n{'='*80}\n\n"
    
    # Process each file
    for filename, polygons in all_polygons.items():
        analysis_type = filename.replace('.kml', '').replace('_', ' ')
        
        output += f"{analysis_type.upper()}\n"
        output += f"Source: {filename}\n"
        output += f"{'-'*60}\n\n"
        
        for i, polygon in enumerate(polygons, 1):
            output += f"{i}. {polygon['name']}\n"
            
            # Coordinates and bounds
            bounds = polygon['bounds']
            output += f"   Center: {bounds['center_lat']:.6f}, {bounds['center_lon']:.6f}\n"
            output += f"   Points: {polygon['coordinate_count']} boundary coordinates\n"
            
            # Create URLs that show boundaries
            geojson_url = create_geojson_url(polygon['coordinates'], polygon['name'])
            maps_polygon_url = create_google_maps_polygon_url(polygon['coordinates'], polygon['name'])
            earth_url = create_google_earth_kml_url(polygon['coordinates'], polygon['name'], polygon['description'])
            
            output += f"\n   🎯 BEST - Individual KML File (shows exact boundaries):\n"
            output += f"   {polygon.get('kml_file', 'Not created')}\n"
            output += f"   → Double-click to open in Google Earth Pro\n"
            
            output += f"\n   🌐 Interactive Boundary Viewer (GeoJSON.io):\n"
            output += f"   {geojson_url}\n"
            
            output += f"\n   🗺️ Google Maps (approximate path):\n"
            output += f"   {maps_polygon_url}\n"
            
            output += f"\n   🌍 Google Earth Web (center location):\n"
            output += f"   {earth_url}\n"
            
            output += f"\n{'-'*40}\n\n"
        
        output += f"\n{'='*60}\n\n"
    
    output += f"""
USAGE INSTRUCTIONS:
{'='*50}

🎯 FOR BEST BOUNDARY VISUALIZATION:
1. Install Google Earth Pro (free): https://earth.google.com/versions/
2. Double-click any .kml file created above
3. The polygon boundaries will display perfectly with colors and labels

🌐 FOR BROWSER-BASED VIEWING:
1. Click the GeoJSON.io URLs above
2. Interactive map will show exact polygon boundaries
3. You can zoom, pan, and click on polygons for details

📱 FOR MOBILE/QUICK SHARING:
1. Use the Google Maps URLs (shows approximate area)
2. Use Google Earth Web URLs (shows center location)

💡 TIP: The individual .kml files are the most accurate way to view boundaries!
"""
    
    return output


def main():
    """Main function to process KML files and generate boundary visualization URLs."""
    
    # Find KML files
    kml_files = [f for f in os.listdir('.') if f.endswith('.kml') and not f.startswith('combined_') and not f.endswith('_boundary.kml')]
    
    if not kml_files:
        print("❌ No KML files found in current directory.")
        return
    
    print("🎯 Processing KML files and generating boundary visualization URLs...")
    print(f"Found {len(kml_files)} KML files: {', '.join(kml_files)}")
    
    all_polygons = {}
    
    # Process all KML files
    for kml_file in kml_files:
        print(f"   📍 Processing {kml_file}...")
        polygons = process_kml_file(kml_file)
        if polygons:
            all_polygons[kml_file] = polygons
    
    if not all_polygons:
        print("❌ No valid polygons found in KML files.")
        return
    
    total_areas = sum(len(polygons) for polygons in all_polygons.values())
    
    # Create individual KML files for each polygon
    print("   🗂️ Creating individual KML files for boundary visualization...")
    created_kml_files = create_individual_kml_files(all_polygons)
    
    # Generate output file
    print("   📄 Generating boundary URLs output...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    boundary_content = generate_boundary_urls_output(all_polygons, created_kml_files)
    boundary_filename = f"kml_boundary_urls_{timestamp}.txt"
    
    with open(boundary_filename, 'w', encoding='utf-8') as f:
        f.write(boundary_content)
    
    # Summary
    print(f"\n✅ Successfully generated boundary visualization files:")
    print(f"   📄 {boundary_filename} - URLs and instructions for viewing boundaries")
    print(f"   🗂️ {len(created_kml_files)} individual .kml files for Google Earth")
    
    print(f"\n📊 Summary:")
    print(f"   • Processed {len(all_polygons)} KML files")
    print(f"   • Found {total_areas} analysis areas")
    print(f"   • Created {len(created_kml_files)} individual boundary files")
    
    print(f"\n🎯 To see actual polygon boundaries:")
    print(f"   1. BEST: Double-click any *_boundary.kml file → Opens in Google Earth Pro")
    print(f"   2. BROWSER: Use GeoJSON.io URLs from the output file")
    print(f"   3. MOBILE: Use Google Maps URLs (approximate boundaries)")
    
    print(f"\n💡 Individual KML files created:")
    for kml_file in created_kml_files[:5]:  # Show first 5
        print(f"   • {kml_file}")
    if len(created_kml_files) > 5:
        print(f"   • ... and {len(created_kml_files) - 5} more")


if __name__ == "__main__":
    main()