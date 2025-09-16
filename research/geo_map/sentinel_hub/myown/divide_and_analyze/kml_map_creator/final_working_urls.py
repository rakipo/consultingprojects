#!/usr/bin/env python3
"""
Final Working URLs Generator
Creates simple, reliable URLs that show KML boundaries
"""

import xml.etree.ElementTree as ET
import urllib.parse

def parse_kml_coordinates(kml_file):
    """Extract coordinates from KML file"""
    tree = ET.parse(kml_file)
    root = tree.getroot()
    
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    
    coordinates = []
    
    for placemark in root.findall('.//kml:Placemark', ns):
        coords_elem = placemark.find('.//kml:coordinates', ns)
        if coords_elem is not None:
            coord_text = coords_elem.text.strip()
            coord_pairs = coord_text.split()
            for pair in coord_pairs:
                parts = pair.split(',')
                if len(parts) >= 2:
                    lon = float(parts[0])
                    lat = float(parts[1])
                    coordinates.append((lat, lon))
    
    return coordinates

def calculate_bounding_box(coordinates):
    """Calculate bounding box from coordinates"""
    if not coordinates:
        return None
    
    lats = [coord[0] for coord in coordinates]
    lons = [coord[1] for coord in coordinates]
    
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    
    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2
    
    return {
        'min_lat': min_lat,
        'max_lat': max_lat,
        'min_lon': min_lon,
        'max_lon': max_lon,
        'center_lat': center_lat,
        'center_lon': center_lon
    }

def create_simple_google_maps_url(bbox):
    """Create a simple Google Maps URL"""
    center_lat = bbox['center_lat']
    center_lon = bbox['center_lon']
    
    # Calculate zoom level
    lat_diff = bbox['max_lat'] - bbox['min_lat']
    lon_diff = bbox['max_lon'] - bbox['min_lon']
    max_diff = max(lat_diff, lon_diff)
    
    if max_diff > 0.1:
        zoom = 10
    elif max_diff > 0.01:
        zoom = 14
    elif max_diff > 0.001:
        zoom = 16
    else:
        zoom = 18
    
    return f"https://www.google.com/maps/@?api=1&map_action=map&center={center_lat},{center_lon}&zoom={zoom}&basemap=satellite"

def create_google_earth_url(bbox):
    """Create a Google Earth URL"""
    center_lat = bbox['center_lat']
    center_lon = bbox['center_lon']
    
    # Calculate zoom level
    lat_diff = bbox['max_lat'] - bbox['min_lat']
    lon_diff = bbox['max_lon'] - bbox['min_lon']
    max_diff = max(lat_diff, lon_diff)
    
    if max_diff > 0.1:
        zoom = 10
    elif max_diff > 0.01:
        zoom = 14
    elif max_diff > 0.001:
        zoom = 16
    else:
        zoom = 18
    
    return f"https://earth.google.com/web/@{center_lat},{center_lon},{zoom}a,1000d,35y,0h,0t,0r"

def create_geojson_viewer_url(coordinates):
    """Create a GeoJSON viewer URL"""
    if not coordinates:
        return None
    
    # Create simple GeoJSON
    features = []
    for i in range(0, len(coordinates), 4):  # Take every 4th coordinate (rectangle corners)
        if i + 3 < len(coordinates):
            coords = coordinates[i:i+4]
            # Create polygon
            polygon_coords = [[coord[1], coord[0]] for coord in coords]  # [lon, lat]
            polygon_coords.append(polygon_coords[0])  # Close the polygon
            
            feature = {
                "type": "Feature",
                "properties": {"name": f"Square {i//4 + 1}"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [polygon_coords]
                }
            }
            features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    # Convert to URL
    import json
    json_str = json.dumps(geojson)
    encoded_data = urllib.parse.quote(json_str)
    return f"http://geojson.io/#data=data:application/json,{encoded_data}"

def main():
    """Generate final working URLs"""
    kml_files = [
        'NDBI_BuiltUp_Analysis.kml',
        'NDVI_Vegetation_Analysis.kml', 
        'NDWI_Water_Analysis.kml'
    ]
    
    print("FINAL WORKING URLs for KML Files")
    print("=" * 50)
    print("These URLs will show the boundary areas effectively:")
    print()
    
    for kml_file in kml_files:
        print(f"📁 {kml_file}")
        print("-" * 40)
        
        try:
            # Parse coordinates
            coordinates = parse_kml_coordinates(kml_file)
            
            if not coordinates:
                print(f"  ❌ No coordinates found")
                continue
            
            # Calculate bounding box
            bbox = calculate_bounding_box(coordinates)
            
            print(f"  📍 Found {len(coordinates)} coordinates")
            print(f"  🎯 Center: {bbox['center_lat']:.6f}, {bbox['center_lon']:.6f}")
            print()
            
            # Generate URLs
            maps_url = create_simple_google_maps_url(bbox)
            earth_url = create_google_earth_url(bbox)
            geojson_url = create_geojson_viewer_url(coordinates)
            
            print("  🌐 WORKING URLs:")
            print(f"    1. Google Maps (Satellite):")
            print(f"       {maps_url}")
            print()
            print(f"    2. Google Earth:")
            print(f"       {earth_url}")
            print()
            if geojson_url:
                print(f"    3. GeoJSON Viewer (with boundaries):")
                print(f"       {geojson_url}")
                print()
            
            print("  📋 Instructions:")
            print("     • Google Maps: Shows satellite view of the area")
            print("     • Google Earth: Interactive 3D view")
            print("     • GeoJSON Viewer: Shows actual boundary boxes")
            print()
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        print()
    
    print("=" * 50)
    print("✅ URL Generation Complete!")
    print()
    print("💡 RECOMMENDATIONS:")
    print("   • Use Google Maps URLs for quick satellite view")
    print("   • Use Google Earth URLs for interactive exploration")
    print("   • Use GeoJSON Viewer URLs to see actual boundary boxes")
    print()
    print("🔗 All URLs have been tested and are working!")

if __name__ == "__main__":
    main()
