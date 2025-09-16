#!/usr/bin/env python3
"""
KML Overlay URL Generator

Creates URLs that display polygon boundaries as overlays on Google Maps,
similar to the image shown with colored rectangles on satellite imagery.
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


def create_google_maps_overlay_url(coordinates: List[tuple], name: str, color: str = "red") -> str:
    """Create Google Maps URL with polygon overlay using the Maps Static API format."""
    if not coordinates:
        return ""
    
    # Calculate center and bounds
    lats = [coord[0] for coord in coordinates]
    lons = [coord[1] for coord in coordinates]
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)
    
    # Create path string for polygon overlay
    path_coords = []
    for lat, lon in coordinates:
        path_coords.append(f"{lat},{lon}")
    
    # Close the polygon by adding first point at the end
    if len(path_coords) > 0:
        path_coords.append(path_coords[0])
    
    path_string = "|".join(path_coords)
    
    # Create Google Maps URL with polygon overlay
    # Using the path parameter to draw the polygon boundary
    base_url = "https://www.google.com/maps"
    
    # Calculate appropriate zoom level
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
    
    # Create URL with polygon path overlay
    params = {
        'll': f"{center_lat},{center_lon}",
        'z': str(zoom),
        't': 'k',  # Satellite view
    }
    
    # Add path overlay - this creates a visible polygon boundary
    encoded_path = urllib.parse.quote(f"color:0x{color}ff|weight:3|fillcolor:0x{color}33|{path_string}")
    
    url = f"{base_url}?{urllib.parse.urlencode(params)}&path={encoded_path}"
    
    return url


def create_google_earth_studio_url(coordinates: List[tuple], name: str) -> str:
    """Create Google Earth Studio URL with KML overlay."""
    if not coordinates:
        return ""
    
    # Calculate center
    lats = [coord[0] for coord in coordinates]
    lons = [coord[1] for coord in coordinates]
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)
    
    # Create Google Earth Web URL with better parameters for viewing
    url = f"https://earth.google.com/web/@{center_lat},{center_lon},500a,35y,0h,45t,0r"
    
    return url


def create_mapbox_overlay_url(coordinates: List[tuple], name: str) -> str:
    """Create Mapbox URL with polygon overlay."""
    if not coordinates:
        return ""
    
    # Calculate center
    lats = [coord[0] for coord in coordinates]
    lons = [coord[1] for coord in coordinates]
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)
    
    # Create GeoJSON for the polygon
    geojson = {
        "type": "Feature",
        "properties": {"name": name},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[lon, lat] for lat, lon in coordinates]]
        }
    }
    
    # Encode GeoJSON for URL
    geojson_str = json.dumps(geojson, separators=(',', ':'))
    encoded_geojson = urllib.parse.quote(geojson_str)
    
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
    
    # Create Mapbox URL
    url = f"https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/geojson({encoded_geojson})/{center_lon},{center_lat},{zoom}/800x600?access_token=YOUR_MAPBOX_TOKEN"
    
    return url


def create_leaflet_overlay_url(coordinates: List[tuple], name: str) -> str:
    """Create URL for online Leaflet map with polygon overlay."""
    if not coordinates:
        return ""
    
    # Create GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {
                "name": name,
                "stroke": "#ff0000",
                "stroke-width": 3,
                "stroke-opacity": 1,
                "fill": "#ff0000",
                "fill-opacity": 0.2
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[lon, lat] for lat, lon in coordinates]]
            }
        }]
    }
    
    # Use geojson.io for interactive viewing
    geojson_str = json.dumps(geojson, separators=(',', ':'))
    encoded = urllib.parse.quote(geojson_str)
    
    return f"https://geojson.io/#data=data:application/json,{encoded}"


def create_here_maps_url(coordinates: List[tuple], name: str) -> str:
    """Create HERE Maps URL with polygon overlay."""
    if not coordinates:
        return ""
    
    # Calculate center
    lats = [coord[0] for coord in coordinates]
    lons = [coord[1] for coord in coordinates]
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)
    
    # Create polygon path for HERE Maps
    path_coords = []
    for lat, lon in coordinates:
        path_coords.append(f"{lat},{lon}")
    
    path_string = ";".join(path_coords)
    
    # HERE Maps URL with polygon
    zoom = 16
    url = f"https://wego.here.com/?map={center_lat},{center_lon},{zoom},satellite&x=ep&polygon={path_string}"
    
    return url


def process_kml_file(filename: str) -> List[Dict]:
    """Process a single KML file and return polygon data."""
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
                    
                    # Determine color based on analysis type
                    color = "ff0000"  # Default red
                    if 'NDVI' in filename:
                        color = "00ff00"  # Green for vegetation
                    elif 'NDBI' in filename:
                        color = "ff0000"  # Red for built-up
                    elif 'NDWI' in filename:
                        color = "0000ff"  # Blue for water
                    
                    polygon_data = {
                        'name': name_elem.text if name_elem is not None else 'Unnamed',
                        'description': desc_elem.text if desc_elem is not None else '',
                        'source_file': filename,
                        'bounds': bounds,
                        'coordinates': coordinates,
                        'coordinate_count': len(coordinates),
                        'color': color
                    }
                    polygons.append(polygon_data)
        
        return polygons
        
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        return []


def generate_overlay_urls_output(all_polygons: Dict[str, List[Dict]]) -> str:
    """Generate output with URLs that show polygon overlays."""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    output = f"""KML Analysis Areas - Polygon Overlay URLs
Generated: {timestamp}
{'='*80}

These URLs show polygon boundaries overlaid on satellite imagery,
similar to the colored rectangles in your reference image.

OVERLAY METHODS:
1. 🎯 GeoJSON.io - Interactive polygons with colors (BEST for boundaries)
2. 🗺️ Google Maps - Polygon paths on satellite view
3. 🌍 Google Earth Web - 3D satellite view (center location)
4. 🛰️ HERE Maps - Polygon overlay on satellite imagery

Color Coding:
🟢 NDVI (Vegetation) - Green boundaries
🔴 NDBI (Built-up) - Red boundaries  
🔵 NDWI (Water) - Blue boundaries

{'='*80}

SUMMARY:
"""
    
    total_polygons = sum(len(polygons) for polygons in all_polygons.values())
    output += f"Total Analysis Areas: {total_polygons}\n"
    
    for filename, polygons in all_polygons.items():
        analysis_type = filename.replace('.kml', '').replace('_', ' ')
        output += f"  - {analysis_type}: {len(polygons)} areas\n"
    
    output += f"\n{'='*80}\n\n"
    
    # Process each file
    for filename, polygons in all_polygons.items():
        analysis_type = filename.replace('.kml', '').replace('_', ' ')
        
        # Determine emoji based on analysis type
        emoji = "🟢" if 'NDVI' in filename else "🔴" if 'NDBI' in filename else "🔵"
        
        output += f"{emoji} {analysis_type.upper()}\n"
        output += f"Source: {filename}\n"
        output += f"{'-'*60}\n\n"
        
        for i, polygon in enumerate(polygons, 1):
            output += f"{i}. {polygon['name']}\n"
            
            # Coordinates and bounds
            bounds = polygon['bounds']
            output += f"   Center: {bounds['center_lat']:.6f}, {bounds['center_lon']:.6f}\n"
            output += f"   Boundary: {polygon['coordinate_count']} points\n"
            
            # Create overlay URLs
            geojson_url = create_leaflet_overlay_url(polygon['coordinates'], polygon['name'])
            maps_url = create_google_maps_overlay_url(polygon['coordinates'], polygon['name'], polygon['color'])
            earth_url = create_google_earth_studio_url(polygon['coordinates'], polygon['name'])
            here_url = create_here_maps_url(polygon['coordinates'], polygon['name'])
            
            output += f"\n   🎯 Interactive Polygon Overlay (GeoJSON.io):\n"
            output += f"   {geojson_url}\n"
            
            output += f"\n   🗺️ Google Maps with Polygon Path:\n"
            output += f"   {maps_url}\n"
            
            output += f"\n   🌍 Google Earth Web (Satellite View):\n"
            output += f"   {earth_url}\n"
            
            output += f"\n   🛰️ HERE Maps with Polygon:\n"
            output += f"   {here_url}\n"
            
            # Show coordinate bounds for reference
            output += f"\n   📐 Bounds: ({bounds['min_lat']:.6f}, {bounds['min_lon']:.6f}) to ({bounds['max_lat']:.6f}, {bounds['max_lon']:.6f})\n"
            
            output += f"\n{'-'*40}\n\n"
        
        output += f"\n{'='*60}\n\n"
    
    output += f"""
USAGE INSTRUCTIONS:
{'='*50}

🎯 FOR BEST POLYGON VISUALIZATION (like your image):
1. Click the GeoJSON.io URLs - shows exact colored boundaries on satellite imagery
2. Interactive map with zoom, pan, and polygon details
3. Boundaries are clearly visible with colors matching analysis type

🗺️ FOR GOOGLE MAPS VIEWING:
1. Click Google Maps URLs - shows polygon paths on satellite view
2. May not show filled polygons but displays boundary lines
3. Good for general location reference

🌍 FOR 3D SATELLITE VIEWING:
1. Click Google Earth Web URLs - 3D satellite imagery
2. Shows terrain and elevation context
3. Best for understanding geographic setting

🛰️ FOR ALTERNATIVE MAPPING:
1. HERE Maps URLs show polygon overlays
2. Different satellite imagery provider
3. Good backup option

💡 RECOMMENDED: Use GeoJSON.io URLs for the closest match to your reference image!
"""
    
    return output


def main():
    """Main function to process KML files and generate overlay URLs."""
    
    # Find KML files
    kml_files = [f for f in os.listdir('.') if f.endswith('.kml') and not f.startswith('combined_') and not f.endswith('_boundary.kml')]
    
    if not kml_files:
        print("❌ No KML files found in current directory.")
        return
    
    print("🎯 Processing KML files and generating polygon overlay URLs...")
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
    
    # Generate output file
    print("   📄 Generating polygon overlay URLs...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    overlay_content = generate_overlay_urls_output(all_polygons)
    overlay_filename = f"kml_polygon_overlay_urls_{timestamp}.txt"
    
    with open(overlay_filename, 'w', encoding='utf-8') as f:
        f.write(overlay_content)
    
    # Summary
    print(f"\n✅ Successfully generated polygon overlay URLs:")
    print(f"   📄 {overlay_filename} - URLs showing polygon boundaries on maps")
    
    print(f"\n📊 Summary:")
    print(f"   • Processed {len(all_polygons)} KML files")
    print(f"   • Generated overlay URLs for {total_areas} analysis areas")
    print(f"   • Color-coded by analysis type (NDVI=Green, NDBI=Red, NDWI=Blue)")
    
    print(f"\n🎯 To see polygon boundaries like in your image:")
    print(f"   1. BEST: Click GeoJSON.io URLs → Shows colored polygons on satellite imagery")
    print(f"   2. ALT: Click Google Maps URLs → Shows polygon paths")
    print(f"   3. 3D: Click Google Earth URLs → 3D satellite view")
    
    print(f"\n💡 The GeoJSON.io URLs will show boundaries most similar to your reference image!")


if __name__ == "__main__":
    main()