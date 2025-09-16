#!/usr/bin/env python3
"""
Enhanced KML to Google Earth/Maps URL Converter
Creates URLs that display the actual boundary boxes from KML files
"""

import xml.etree.ElementTree as ET
import base64
import urllib.parse
import json

def parse_kml_coordinates(kml_file):
    """Extract all coordinates and placemark info from a KML file"""
    tree = ET.parse(kml_file)
    root = tree.getroot()
    
    # Define namespace
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    
    placemarks = []
    
    # Find all placemarks
    for placemark in root.findall('.//kml:Placemark', ns):
        name_elem = placemark.find('kml:name', ns)
        desc_elem = placemark.find('kml:description', ns)
        coords_elem = placemark.find('.//kml:coordinates', ns)
        
        if coords_elem is not None:
            name = name_elem.text if name_elem is not None else "Unknown"
            description = desc_elem.text if desc_elem is not None else ""
            
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
            
            placemarks.append({
                'name': name,
                'description': description,
                'coordinates': coordinates
            })
    
    return placemarks

def create_google_maps_kml_url(kml_file_path):
    """Create a Google Maps URL that loads the KML file directly"""
    # For Google Maps, we need to host the KML file somewhere or use a data URL
    # Let's create a simple approach using the file path
    encoded_path = urllib.parse.quote(kml_file_path)
    
    # Google Maps KML URL format
    url = f"https://www.google.com/maps/d/viewer?mid=1&ll=14.381729,79.523023&z=16&kml={encoded_path}"
    return url

def create_google_earth_kml_url(kml_file_path):
    """Create a Google Earth URL that loads the KML file"""
    # Google Earth can load KML files directly
    encoded_path = urllib.parse.quote(kml_file_path)
    url = f"https://earth.google.com/web/@{14.381729},{79.523023},16a,1000d,35y,0h,0t,0r/data={encoded_path}"
    return url

def create_geojson_from_kml(placemarks):
    """Convert KML placemarks to GeoJSON format"""
    features = []
    
    for placemark in placemarks:
        # Create polygon from coordinates
        coords = placemark['coordinates']
        if len(coords) >= 3:  # Need at least 3 points for a polygon
            # GeoJSON uses [lon, lat] format
            polygon_coords = [[coord[1], coord[0]] for coord in coords]
            
            feature = {
                "type": "Feature",
                "properties": {
                    "name": placemark['name'],
                    "description": placemark['description']
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

def create_geojson_url(geojson_data):
    """Create a URL with GeoJSON data"""
    # Convert GeoJSON to base64 for URL embedding
    json_str = json.dumps(geojson_data)
    encoded_data = base64.b64encode(json_str.encode()).decode()
    
    # Create a data URL
    url = f"data:application/json;base64,{encoded_data}"
    return url

def create_google_maps_with_boundaries(placemarks):
    """Create a Google Maps URL that shows the boundaries"""
    # Calculate overall bounding box
    all_coords = []
    for placemark in placemarks:
        all_coords.extend(placemark['coordinates'])
    
    if not all_coords:
        return None
    
    lats = [coord[0] for coord in all_coords]
    lons = [coord[1] for coord in all_coords]
    
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    
    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2
    
    # Calculate appropriate zoom level
    lat_diff = max_lat - min_lat
    lon_diff = max_lon - min_lon
    max_diff = max(lat_diff, lon_diff)
    
    if max_diff > 0.1:
        zoom = 10
    elif max_diff > 0.01:
        zoom = 14
    elif max_diff > 0.001:
        zoom = 16
    else:
        zoom = 18
    
    # Create URL with boundary parameters
    url = f"https://www.google.com/maps/@?api=1&map_action=map&center={center_lat},{center_lon}&zoom={zoom}&basemap=satellite"
    return url

def create_alternative_maps_url(placemarks):
    """Create an alternative maps URL using coordinates"""
    if not placemarks:
        return None
    
    # Get the first placemark's coordinates as a reference
    first_placemark = placemarks[0]
    coords = first_placemark['coordinates']
    
    if len(coords) >= 4:  # Rectangle coordinates
        # Create a path parameter for the boundary
        path_coords = []
        for coord in coords:
            path_coords.append(f"{coord[0]},{coord[1]}")
        
        path_str = "|".join(path_coords)
        encoded_path = urllib.parse.quote(path_str)
        
        center_lat = sum(coord[0] for coord in coords) / len(coords)
        center_lon = sum(coord[1] for coord in coords) / len(coords)
        
        url = f"https://www.google.com/maps/@?api=1&map_action=map&center={center_lat},{center_lon}&zoom=16&path=color:red|weight:3|fillcolor:yellow|{encoded_path}"
        return url
    
    return None

def main():
    """Main function to process KML files and generate URLs with boundaries"""
    kml_files = [
        'NDBI_BuiltUp_Analysis.kml',
        'NDVI_Vegetation_Analysis.kml', 
        'NDWI_Water_Analysis.kml'
    ]
    
    print("Enhanced KML to Google Earth/Maps URL Converter")
    print("=" * 60)
    
    for kml_file in kml_files:
        print(f"\nProcessing: {kml_file}")
        print("-" * 40)
        
        try:
            # Parse placemarks from KML file
            placemarks = parse_kml_coordinates(kml_file)
            
            if not placemarks:
                print(f"  No placemarks found in {kml_file}")
                continue
            
            print(f"  Placemarks found: {len(placemarks)}")
            
            # Generate different types of URLs
            print(f"\n  URL Options:")
            
            # 1. Google Maps with boundaries
            maps_url = create_google_maps_with_boundaries(placemarks)
            if maps_url:
                print(f"    1. Google Maps (Satellite View):")
                print(f"       {maps_url}")
            
            # 2. Alternative maps URL with path
            alt_url = create_alternative_maps_url(placemarks)
            if alt_url:
                print(f"    2. Google Maps (with Path):")
                print(f"       {alt_url}")
            
            # 3. Google Earth KML URL
            earth_url = create_google_earth_kml_url(kml_file)
            print(f"    3. Google Earth (KML):")
            print(f"       {earth_url}")
            
            # 4. Create GeoJSON for advanced use
            geojson_data = create_geojson_from_kml(placemarks)
            geojson_url = create_geojson_url(geojson_data)
            print(f"    4. GeoJSON Data URL:")
            print(f"       {geojson_url[:100]}...")
            
            # 5. Simple center point URL (fallback)
            if placemarks:
                first_coords = placemarks[0]['coordinates']
                if first_coords:
                    center_lat = sum(coord[0] for coord in first_coords) / len(first_coords)
                    center_lon = sum(coord[1] for coord in first_coords) / len(first_coords)
                    simple_url = f"https://www.google.com/maps/@?api=1&map_action=map&center={center_lat},{center_lon}&zoom=16"
                    print(f"    5. Simple Center Point:")
                    print(f"       {simple_url}")
            
        except Exception as e:
            print(f"  Error processing {kml_file}: {e}")
    
    print("\n" + "=" * 60)
    print("URL Generation Complete!")
    print("\nNote: For best boundary visualization, use Google Earth URLs or")
    print("upload the KML files to Google My Maps for interactive viewing.")

if __name__ == "__main__":
    main()
