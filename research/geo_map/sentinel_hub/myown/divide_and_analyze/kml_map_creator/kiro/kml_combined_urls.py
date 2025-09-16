#!/usr/bin/env python3
"""
KML Combined URL Generator

Creates one URL per KML file that shows ALL polygons from that file together,
like the Google Earth screenshot with all colored boxes visible at once.
"""

import xml.etree.ElementTree as ET
import urllib.parse
import os
from datetime import datetime
from typing import List, Dict
import json


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


def create_combined_geojson_url(polygons: List[Dict], analysis_type: str, color: str) -> str:
    """Create a single GeoJSON.io URL showing all polygons from one analysis type."""
    if not polygons:
        return ""
    
    # Create GeoJSON FeatureCollection with all polygons
    features = []
    
    for polygon in polygons:
        feature = {
            "type": "Feature",
            "properties": {
                "name": polygon['name'],
                "description": f"{analysis_type} - {polygon['name']}",
                "stroke": f"#{color}",
                "stroke-width": 2,
                "stroke-opacity": 1,
                "fill": f"#{color}",
                "fill-opacity": 0.3
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[lon, lat] for lat, lon in polygon['coordinates']]]
            }
        }
        features.append(feature)
    
    # Create complete GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    # Encode for URL
    geojson_str = json.dumps(geojson, separators=(',', ':'))
    encoded = urllib.parse.quote(geojson_str)
    
    return f"https://geojson.io/#data=data:application/json,{encoded}"


def create_combined_google_earth_kml(polygons: List[Dict], analysis_type: str, color: str) -> str:
    """Create a combined KML file for all polygons and return Google Earth URL."""
    if not polygons:
        return ""
    
    # Create KML content with all polygons
    kml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{analysis_type} - All Areas</name>
    <description>All analysis areas for {analysis_type}</description>
    
    <Style id="polygon_style">
      <LineStyle>
        <color>ff{color[4:6]}{color[2:4]}{color[0:2]}</color>
        <width>2</width>
      </LineStyle>
      <PolyStyle>
        <fill>1</fill>
        <color>4d{color[4:6]}{color[2:4]}{color[0:2]}</color>
        <outline>1</outline>
      </PolyStyle>
    </Style>
'''
    
    # Add all polygons
    for polygon in polygons:
        kml_content += f'''
    <Placemark>
      <name>{polygon['name']}</name>
      <description><![CDATA[
        <h3>{polygon['name']}</h3>
        <p><strong>Analysis:</strong> {analysis_type}</p>
        <p><strong>Center:</strong> {polygon['bounds']['center_lat']:.6f}, {polygon['bounds']['center_lon']:.6f}</p>
        <p><strong>Boundary Points:</strong> {polygon['coordinate_count']}</p>
      ]]></description>
      <styleUrl>#polygon_style</styleUrl>
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
    </Placemark>'''
    
    kml_content += '''
  </Document>
</kml>'''
    
    # Save KML file
    safe_name = analysis_type.replace(' ', '_').replace('/', '_')
    kml_filename = f"{safe_name}_combined.kml"
    
    with open(kml_filename, 'w', encoding='utf-8') as f:
        f.write(kml_content)
    
    # Calculate center of all polygons for Google Earth URL
    all_lats = []
    all_lons = []
    for polygon in polygons:
        all_lats.extend([coord[0] for coord in polygon['coordinates']])
        all_lons.extend([coord[1] for coord in polygon['coordinates']])
    
    center_lat = sum(all_lats) / len(all_lats)
    center_lon = sum(all_lons) / len(all_lons)
    
    # Calculate appropriate altitude based on area coverage
    lat_range = max(all_lats) - min(all_lats)
    lon_range = max(all_lons) - min(all_lons)
    max_range = max(lat_range, lon_range)
    
    if max_range > 0.01:
        altitude = 2000
    elif max_range > 0.005:
        altitude = 1000
    else:
        altitude = 500
    
    earth_url = f"https://earth.google.com/web/@{center_lat},{center_lon},{altitude}a,35y,0h,0t,0r"
    
    return earth_url, kml_filename


def create_combined_google_maps_url(polygons: List[Dict], analysis_type: str) -> str:
    """Create Google Maps URL showing all polygon centers."""
    if not polygons:
        return ""
    
    # Calculate overall center
    all_lats = []
    all_lons = []
    for polygon in polygons:
        all_lats.append(polygon['bounds']['center_lat'])
        all_lons.append(polygon['bounds']['center_lon'])
    
    center_lat = sum(all_lats) / len(all_lats)
    center_lon = sum(all_lons) / len(all_lons)
    
    # Calculate zoom level based on spread
    lat_range = max(all_lats) - min(all_lats)
    lon_range = max(all_lons) - min(all_lons)
    max_range = max(lat_range, lon_range)
    
    if max_range > 0.01:
        zoom = 14
    elif max_range > 0.005:
        zoom = 16
    else:
        zoom = 18
    
    # Create Google Maps URL
    url = f"https://www.google.com/maps/@{center_lat},{center_lon},{zoom}z/data=!3m1!1e3"
    
    return url


def process_kml_file(filename: str) -> List[Dict]:
    """Process a single KML file and return all polygon data."""
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


def generate_combined_urls_output(all_polygons: Dict[str, List[Dict]], created_files: List[str]) -> str:
    """Generate output with one URL per analysis type showing all polygons."""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    output = f"""KML Combined Analysis URLs - All Polygons Per Analysis Type
Generated: {timestamp}
{'='*80}

This creates ONE URL per analysis type (NDVI, NDBI, NDWI) that shows 
ALL the colored boxes together, just like your Google Earth screenshot.

Each URL displays all polygons from one analysis type with consistent colors:
🟢 NDVI (Vegetation Analysis) - Green boxes
🔴 NDBI (Built-up Analysis) - Red boxes  
🔵 NDWI (Water Analysis) - Blue boxes

{'='*80}

SUMMARY:
"""
    
    total_files = len(all_polygons)
    total_polygons = sum(len(polygons) for polygons in all_polygons.values())
    
    output += f"Analysis Types: {total_files}\n"
    output += f"Total Polygons: {total_polygons}\n"
    output += f"Combined KML Files Created: {len(created_files)}\n\n"
    
    for filename, polygons in all_polygons.items():
        analysis_type = filename.replace('.kml', '').replace('_', ' ')
        output += f"  - {analysis_type}: {len(polygons)} polygons\n"
    
    output += f"\n{'='*80}\n\n"
    
    # Process each analysis type
    for filename, polygons in all_polygons.items():
        analysis_type = filename.replace('.kml', '').replace('_', ' ')
        
        # Determine color and emoji
        if 'NDVI' in filename:
            color = "00ff00"  # Green
            emoji = "🟢"
        elif 'NDBI' in filename:
            color = "ff0000"  # Red
            emoji = "🔴"
        elif 'NDWI' in filename:
            color = "0000ff"  # Blue
            emoji = "🔵"
        else:
            color = "ffff00"  # Yellow
            emoji = "🟡"
        
        output += f"{emoji} {analysis_type.upper()}\n"
        output += f"Source: {filename}\n"
        output += f"Polygons: {len(polygons)} areas\n"
        output += f"{'-'*60}\n\n"
        
        # Create combined URLs
        geojson_url = create_combined_geojson_url(polygons, analysis_type, color)
        earth_url, kml_file = create_combined_google_earth_kml(polygons, analysis_type, color)
        maps_url = create_combined_google_maps_url(polygons, analysis_type)
        
        # Calculate overall bounds
        all_lats = []
        all_lons = []
        for polygon in polygons:
            all_lats.extend([coord[0] for coord in polygon['coordinates']])
            all_lons.extend([coord[1] for coord in polygon['coordinates']])
        
        min_lat, max_lat = min(all_lats), max(all_lats)
        min_lon, max_lon = min(all_lons), max(all_lons)
        center_lat = sum(all_lats) / len(all_lats)
        center_lon = sum(all_lons) / len(all_lons)
        
        output += f"📍 COMBINED VIEW - ALL {len(polygons)} POLYGONS TOGETHER:\n\n"
        
        output += f"🎯 Interactive Map with All Colored Boxes (BEST):\n"
        output += f"{geojson_url}\n\n"
        
        output += f"🌍 Google Earth Web (All Areas):\n"
        output += f"{earth_url}\n\n"
        
        output += f"🗺️ Google Maps (Satellite View):\n"
        output += f"{maps_url}\n\n"
        
        output += f"📁 Combined KML File (for Google Earth Pro):\n"
        output += f"{kml_file}\n"
        output += f"→ Double-click to open all polygons in Google Earth Pro\n\n"
        
        output += f"📐 Overall Coverage Area:\n"
        output += f"   Center: {center_lat:.6f}, {center_lon:.6f}\n"
        output += f"   Bounds: ({min_lat:.6f}, {min_lon:.6f}) to ({max_lat:.6f}, {max_lon:.6f})\n"
        
        # List all polygon names
        output += f"\n📋 Included Polygons:\n"
        for i, polygon in enumerate(polygons, 1):
            output += f"   {i}. {polygon['name']}\n"
        
        output += f"\n{'='*60}\n\n"
    
    output += f"""
USAGE INSTRUCTIONS:
{'='*50}

🎯 TO VIEW ALL BOXES LIKE YOUR SCREENSHOT:
1. Click the "Interactive Map with All Colored Boxes" URLs above
2. Each URL shows ALL polygons from one analysis type together
3. Colors match the analysis type (Green=NDVI, Red=NDBI, Blue=NDWI)
4. Zoom and pan to explore all areas at once

🌍 FOR GOOGLE EARTH VIEWING:
1. Click Google Earth Web URLs for 3D satellite view
2. Or double-click the combined .kml files for Google Earth Pro
3. All polygons from each analysis will be visible together

📱 FOR QUICK REFERENCE:
1. Use Google Maps URLs for general area overview
2. Shows the satellite imagery of the overall analysis region

💡 RECOMMENDED WORKFLOW:
- Use the GeoJSON.io URLs to see all colored boundaries together
- Each analysis type gets its own URL showing all its polygons
- Perfect for comparing different analysis results side by side

🔗 SHARING:
- Each URL is self-contained and shows all polygons for that analysis
- No need to open multiple links - one URL per analysis type
- Easy to share with colleagues or include in reports
"""
    
    return output


def main():
    """Main function to process KML files and generate combined URLs."""
    
    # Find KML files
    kml_files = [f for f in os.listdir('.') if f.endswith('.kml') and not f.startswith('combined_') and not f.endswith('_boundary.kml') and not f.endswith('_combined.kml')]
    
    if not kml_files:
        print("❌ No KML files found in current directory.")
        return
    
    print("🎯 Processing KML files and generating combined URLs (one per analysis type)...")
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
    created_files = []
    
    # Generate output file
    print("   📄 Generating combined URLs (one per analysis type)...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    combined_content = generate_combined_urls_output(all_polygons, created_files)
    combined_filename = f"kml_combined_analysis_urls_{timestamp}.txt"
    
    with open(combined_filename, 'w', encoding='utf-8') as f:
        f.write(combined_content)
    
    # Summary
    print(f"\n✅ Successfully generated combined analysis URLs:")
    print(f"   📄 {combined_filename} - One URL per analysis type showing all polygons")
    
    print(f"\n📊 Summary:")
    print(f"   • Processed {len(all_polygons)} analysis types")
    print(f"   • Total polygons: {total_areas}")
    print(f"   • Generated {len(all_polygons)} combined URLs (one per analysis)")
    
    print(f"\n🎯 Each URL shows ALL polygons for one analysis type:")
    for filename, polygons in all_polygons.items():
        analysis_type = filename.replace('.kml', '').replace('_', ' ')
        emoji = "🟢" if 'NDVI' in filename else "🔴" if 'NDBI' in filename else "🔵"
        print(f"   {emoji} {analysis_type}: {len(polygons)} polygons in one URL")
    
    print(f"\n💡 Perfect for viewing all boxes together like your Google Earth screenshot!")


if __name__ == "__main__":
    main()