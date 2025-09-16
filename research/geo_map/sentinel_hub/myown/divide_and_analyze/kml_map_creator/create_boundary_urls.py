#!/usr/bin/env python3
"""
Create Boundary URLs from KML Files
Generates URLs that actually show the boundary boxes from KML files
"""

import xml.etree.ElementTree as ET
import base64
import urllib.parse
import json

def parse_kml_boundaries(kml_file):
    """Extract boundary coordinates from KML file"""
    tree = ET.parse(kml_file)
    root = tree.getroot()
    
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    
    boundaries = []
    
    for placemark in root.findall('.//kml:Placemark', ns):
        name_elem = placemark.find('kml:name', ns)
        coords_elem = placemark.find('.//kml:coordinates', ns)
        
        if coords_elem is not None:
            name = name_elem.text if name_elem is not None else "Unknown"
            
            # Parse coordinates
            coord_text = coords_elem.text.strip()
            coordinates = []
            coord_pairs = coord_text.split()
            for pair in coord_pairs:
                parts = pair.split(',')
                if len(parts) >= 2:
                    lon = float(parts[0])
                    lat = float(parts[1])
                    coordinates.append((lat, lon))
            
            if len(coordinates) >= 4:  # Rectangle
                boundaries.append({
                    'name': name,
                    'coordinates': coordinates
                })
    
    return boundaries

def create_kml_data_url(kml_file):
    """Create a data URL from KML file content"""
    with open(kml_file, 'r') as f:
        kml_content = f.read()
    
    # Encode KML content
    encoded_content = base64.b64encode(kml_content.encode()).decode()
    data_url = f"data:application/vnd.google-earth.kml+xml;base64,{encoded_content}"
    return data_url

def create_google_earth_with_kml(kml_file):
    """Create Google Earth URL with embedded KML data"""
    data_url = create_kml_data_url(kml_file)
    encoded_data_url = urllib.parse.quote(data_url)
    
    # Google Earth URL with KML data
    url = f"https://earth.google.com/web/@{14.381729},{79.523023},16a,1000d,35y,0h,0t,0r/data={encoded_data_url}"
    return url

def create_geojson_boundaries(boundaries):
    """Convert boundaries to GeoJSON format"""
    features = []
    
    for boundary in boundaries:
        coords = boundary['coordinates']
        if len(coords) >= 4:
            # Convert to GeoJSON format [lon, lat]
            polygon_coords = [[coord[1], coord[0]] for coord in coords]
            
            feature = {
                "type": "Feature",
                "properties": {
                    "name": boundary['name']
                },
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
    
    return geojson

def create_geojson_viewer_url(geojson_data):
    """Create a URL for a GeoJSON viewer"""
    # Use geojson.io viewer
    json_str = json.dumps(geojson_data)
    encoded_data = urllib.parse.quote(json_str)
    url = f"http://geojson.io/#data=data:application/json,{encoded_data}"
    return url

def create_google_maps_polygon_url(boundaries):
    """Create Google Maps URL with polygon boundaries"""
    if not boundaries:
        return None
    
    # Calculate center point
    all_coords = []
    for boundary in boundaries:
        all_coords.extend(boundary['coordinates'])
    
    center_lat = sum(coord[0] for coord in all_coords) / len(all_coords)
    center_lon = sum(coord[1] for coord in all_coords) / len(all_coords)
    
    # Create polygon path for the first boundary
    first_boundary = boundaries[0]
    coords = first_boundary['coordinates']
    
    # Create path string for Google Maps
    path_parts = []
    for coord in coords:
        path_parts.append(f"{coord[0]},{coord[1]}")
    
    path_str = "|".join(path_parts)
    encoded_path = urllib.parse.quote(path_str)
    
    # Google Maps URL with polygon
    url = f"https://www.google.com/maps/@?api=1&map_action=map&center={center_lat},{center_lon}&zoom=16&path=color:red|weight:3|fillcolor:yellow|{encoded_path}"
    return url

def create_alternative_viewer_url(kml_file):
    """Create URL for alternative KML viewers"""
    # Use a public KML viewer service
    with open(kml_file, 'r') as f:
        kml_content = f.read()
    
    encoded_content = base64.b64encode(kml_content.encode()).decode()
    data_url = f"data:application/vnd.google-earth.kml+xml;base64,{encoded_content}"
    encoded_data_url = urllib.parse.quote(data_url)
    
    # Use a KML viewer service
    url = f"https://kmlviewer.nsspot.net/?url={encoded_data_url}"
    return url

def main():
    """Main function to generate boundary URLs"""
    kml_files = [
        'NDBI_BuiltUp_Analysis.kml',
        'NDVI_Vegetation_Analysis.kml', 
        'NDWI_Water_Analysis.kml'
    ]
    
    print("Boundary URL Generator for KML Files")
    print("=" * 50)
    
    for kml_file in kml_files:
        print(f"\nProcessing: {kml_file}")
        print("-" * 30)
        
        try:
            # Parse boundaries
            boundaries = parse_kml_boundaries(kml_file)
            
            if not boundaries:
                print(f"  No boundaries found in {kml_file}")
                continue
            
            print(f"  Boundaries found: {len(boundaries)}")
            
            # Generate URLs
            print(f"\n  Working URLs with Boundaries:")
            
            # 1. Google Earth with KML data
            earth_url = create_google_earth_with_kml(kml_file)
            print(f"    1. Google Earth (with KML data):")
            print(f"       {earth_url}")
            
            # 2. Google Maps with polygon
            maps_url = create_google_maps_polygon_url(boundaries)
            if maps_url:
                print(f"    2. Google Maps (with polygon):")
                print(f"       {maps_url}")
            
            # 3. GeoJSON viewer
            geojson_data = create_geojson_boundaries(boundaries)
            geojson_url = create_geojson_viewer_url(geojson_data)
            print(f"    3. GeoJSON Viewer:")
            print(f"       {geojson_url}")
            
            # 4. Alternative KML viewer
            alt_url = create_alternative_viewer_url(kml_file)
            print(f"    4. KML Viewer:")
            print(f"       {alt_url}")
            
            # 5. Simple center point (fallback)
            if boundaries:
                first_coords = boundaries[0]['coordinates']
                center_lat = sum(coord[0] for coord in first_coords) / len(first_coords)
                center_lon = sum(coord[1] for coord in first_coords) / len(first_coords)
                simple_url = f"https://www.google.com/maps/@?api=1&map_action=map&center={center_lat},{center_lon}&zoom=16&basemap=satellite"
                print(f"    5. Simple Satellite View:")
                print(f"       {simple_url}")
            
        except Exception as e:
            print(f"  Error processing {kml_file}: {e}")
    
    print("\n" + "=" * 50)
    print("URL Generation Complete!")
    print("\nRecommended: Use Google Earth URLs for best boundary visualization.")

if __name__ == "__main__":
    main()
