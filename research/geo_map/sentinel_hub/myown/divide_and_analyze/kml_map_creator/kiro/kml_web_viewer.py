#!/usr/bin/env python3
"""
KML Web Viewer Generator

Creates an HTML file with clickable links to view KML boundaries in Google Maps/Earth.
"""

import xml.etree.ElementTree as ET
import os
from typing import List, Dict


def parse_kml_file(filename: str) -> List[Dict]:
    """Parse KML file and extract polygon information."""
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
                # Parse coordinates
                coordinates = []
                for coord in coord_elem.text.strip().split():
                    if coord.strip():
                        parts = coord.split(',')
                        if len(parts) >= 2:
                            lon, lat = float(parts[0]), float(parts[1])
                            coordinates.append((lat, lon))
                
                if coordinates:
                    # Calculate center and bounds
                    lats = [c[0] for c in coordinates]
                    lons = [c[1] for c in coordinates]
                    
                    center_lat = sum(lats) / len(lats)
                    center_lon = sum(lons) / len(lons)
                    
                    # Calculate zoom level
                    lat_diff = max(lats) - min(lats)
                    lon_diff = max(lons) - min(lons)
                    max_diff = max(lat_diff, lon_diff)
                    
                    if max_diff > 0.1:
                        zoom = 10
                    elif max_diff > 0.01:
                        zoom = 14
                    elif max_diff > 0.001:
                        zoom = 17
                    else:
                        zoom = 19
                    
                    polygon_info = {
                        'name': name_elem.text if name_elem is not None else 'Unnamed',
                        'description': desc_elem.text if desc_elem is not None else '',
                        'center_lat': center_lat,
                        'center_lon': center_lon,
                        'zoom': zoom,
                        'coordinates': coordinates,
                        'source_file': filename
                    }
                    polygons.append(polygon_info)
        
        return polygons
        
    except Exception as e:
        print(f"Error parsing {filename}: {e}")
        return []


def generate_html_viewer(all_polygons: Dict[str, List[Dict]]) -> str:
    """Generate HTML file with clickable links."""
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KML Analysis Areas Viewer</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 30px;
        }
        .analysis-section {
            background: white;
            margin: 20px 0;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .analysis-title {
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .polygon-item {
            background: #f8f9fa;
            margin: 15px 0;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #28a745;
        }
        .polygon-name {
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        .coordinates {
            color: #666;
            font-size: 0.9em;
            margin: 5px 0;
        }
        .links {
            margin-top: 15px;
        }
        .link-button {
            display: inline-block;
            padding: 8px 16px;
            margin: 5px 10px 5px 0;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        .maps-link {
            background-color: #4285f4;
            color: white;
        }
        .maps-link:hover {
            background-color: #3367d6;
            transform: translateY(-2px);
        }
        .earth-link {
            background-color: #34a853;
            color: white;
        }
        .earth-link:hover {
            background-color: #2d8f47;
            transform: translateY(-2px);
        }
        .summary {
            background: #e3f2fd;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            border-left: 4px solid #2196f3;
        }
        .ndbi { border-left-color: #ff5722; }
        .ndvi { border-left-color: #4caf50; }
        .ndwi { border-left-color: #2196f3; }
        
        .description {
            background: #f0f0f0;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            font-size: 0.9em;
            max-height: 100px;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🗺️ KML Analysis Areas Viewer</h1>
        <p>Click the links below to view analysis boundaries in Google Maps or Google Earth</p>
    </div>
    
    <div class="summary">
        <h3>📊 Summary</h3>
"""
    
    total_polygons = sum(len(polygons) for polygons in all_polygons.values())
    html_content += f"        <p><strong>Total Analysis Areas:</strong> {total_polygons}</p>\n"
    
    for filename, polygons in all_polygons.items():
        analysis_type = filename.replace('.kml', '').replace('_', ' ')
        html_content += f"        <p><strong>{analysis_type}:</strong> {len(polygons)} areas</p>\n"
    
    html_content += """    </div>
"""
    
    # Add sections for each analysis type
    for filename, polygons in all_polygons.items():
        analysis_type = filename.replace('.kml', '').replace('_', ' ')
        
        # Determine CSS class based on analysis type
        css_class = ""
        if 'NDBI' in filename:
            css_class = "ndbi"
        elif 'NDVI' in filename:
            css_class = "ndvi"
        elif 'NDWI' in filename:
            css_class = "ndwi"
        
        html_content += f"""
    <div class="analysis-section">
        <h2 class="analysis-title">📍 {analysis_type}</h2>
        <p><em>Source: {filename}</em></p>
"""
        
        for polygon in polygons:
            maps_url = f"https://www.google.com/maps/@{polygon['center_lat']},{polygon['center_lon']},{polygon['zoom']}z"
            earth_url = f"https://earth.google.com/web/@{polygon['center_lat']},{polygon['center_lon']},1000a,35y,0h,0t,0r"
            
            html_content += f"""
        <div class="polygon-item {css_class}">
            <div class="polygon-name">{polygon['name']}</div>
            <div class="coordinates">
                📍 Center: {polygon['center_lat']:.6f}, {polygon['center_lon']:.6f} | 
                📐 {len(polygon['coordinates'])} boundary points
            </div>
"""
            
            if polygon['description'].strip():
                # Clean up description for HTML
                desc = polygon['description'].strip().replace('\n', '<br>')
                html_content += f"""
            <div class="description">
                {desc}
            </div>
"""
            
            html_content += f"""
            <div class="links">
                <a href="{maps_url}" target="_blank" class="link-button maps-link">
                    🌍 Open in Google Maps
                </a>
                <a href="{earth_url}" target="_blank" class="link-button earth-link">
                    🌎 Open in Google Earth
                </a>
            </div>
        </div>
"""
        
        html_content += """
    </div>
"""
    
    html_content += """
    <div class="summary">
        <h3>💡 Tips</h3>
        <ul>
            <li><strong>Google Maps:</strong> Shows the general area but may not display exact polygon boundaries</li>
            <li><strong>Google Earth:</strong> Better for visualizing geographic context and terrain</li>
            <li><strong>Best Visualization:</strong> Import the generated <code>combined_analysis_areas.kml</code> file into Google Earth Pro for precise boundary display</li>
            <li><strong>Mobile:</strong> Links work on mobile devices - Google Earth will open in the app if installed</li>
        </ul>
    </div>
    
    <div style="text-align: center; margin-top: 30px; color: #666;">
        <p>Generated by KML Web Viewer | <a href="combined_analysis_areas.kml">Download Combined KML</a></p>
    </div>
</body>
</html>
"""
    
    return html_content


def main():
    """Generate HTML viewer for KML files."""
    # Find KML files
    kml_files = [f for f in os.listdir('.') if f.endswith('.kml') and not f.startswith('combined_')]
    
    if not kml_files:
        print("❌ No KML files found in current directory.")
        return
    
    print("🌐 Generating HTML viewer...")
    
    all_polygons = {}
    
    # Parse all KML files
    for kml_file in kml_files:
        print(f"   Processing {kml_file}...")
        polygons = parse_kml_file(kml_file)
        if polygons:
            all_polygons[kml_file] = polygons
    
    if not all_polygons:
        print("❌ No valid polygons found in KML files.")
        return
    
    # Generate HTML
    html_content = generate_html_viewer(all_polygons)
    
    # Write HTML file
    html_filename = 'kml_analysis_viewer.html'
    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    total_areas = sum(len(polygons) for polygons in all_polygons.values())
    
    print(f"✅ Created: {html_filename}")
    print(f"📊 Processed {len(all_polygons)} KML files with {total_areas} analysis areas")
    print(f"\n💡 Open {html_filename} in your browser to view clickable links!")


if __name__ == "__main__":
    main()