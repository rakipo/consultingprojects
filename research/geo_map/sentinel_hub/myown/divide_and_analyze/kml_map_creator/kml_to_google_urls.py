#!/usr/bin/env python3
"""
KML to Google Earth/Maps URL Converter
Converts KML files to working Google Earth and Google Maps URLs
"""

import xml.etree.ElementTree as ET
import re
import urllib.parse

def parse_kml_coordinates(kml_file):
    """Extract all coordinates from a KML file"""
    tree = ET.parse(kml_file)
    root = tree.getroot()
    
    # Define namespace
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    
    coordinates = []
    
    # Find all coordinate elements
    for coord_elem in root.findall('.//kml:coordinates', ns):
        coord_text = coord_elem.text.strip()
        # Parse coordinate string (longitude,latitude,altitude)
        coord_pairs = coord_text.split()
        for pair in coord_pairs:
            parts = pair.split(',')
            if len(parts) >= 2:
                lon = float(parts[0])
                lat = float(parts[1])
                coordinates.append((lat, lon))
    
    return coordinates

def calculate_bounding_box(coordinates):
    """Calculate the bounding box from a list of coordinates"""
    if not coordinates:
        return None
    
    lats = [coord[0] for coord in coordinates]
    lons = [coord[1] for coord in coordinates]
    
    min_lat = min(lats)
    max_lat = max(lats)
    min_lon = min(lons)
    max_lon = max(lons)
    
    return {
        'min_lat': min_lat,
        'max_lat': max_lat,
        'min_lon': min_lon,
        'max_lon': max_lon,
        'center_lat': (min_lat + max_lat) / 2,
        'center_lon': (min_lon + max_lon) / 2
    }

def create_google_earth_url(bounding_box):
    """Create a Google Earth URL"""
    center_lat = bounding_box['center_lat']
    center_lon = bounding_box['center_lon']
    
    # Calculate zoom level based on bounding box size
    lat_diff = bounding_box['max_lat'] - bounding_box['min_lat']
    lon_diff = bounding_box['max_lon'] - bounding_box['min_lon']
    max_diff = max(lat_diff, lon_diff)
    
    # Approximate zoom level calculation
    if max_diff > 0.1:
        zoom = 10
    elif max_diff > 0.01:
        zoom = 14
    elif max_diff > 0.001:
        zoom = 16
    else:
        zoom = 18
    
    # Google Earth URL format
    url = f"https://earth.google.com/web/@{center_lat},{center_lon},{zoom}a,1000d,35y,0h,0t,0r"
    return url

def create_google_maps_url(bounding_box):
    """Create a Google Maps URL"""
    center_lat = bounding_box['center_lat']
    center_lon = bounding_box['center_lon']
    
    # Calculate zoom level based on bounding box size
    lat_diff = bounding_box['max_lat'] - bounding_box['min_lat']
    lon_diff = bounding_box['max_lon'] - bounding_box['min_lon']
    max_diff = max(lat_diff, lon_diff)
    
    # Approximate zoom level calculation
    if max_diff > 0.1:
        zoom = 10
    elif max_diff > 0.01:
        zoom = 14
    elif max_diff > 0.001:
        zoom = 16
    else:
        zoom = 18
    
    # Google Maps URL format
    url = f"https://www.google.com/maps/@?api=1&map_action=map&center={center_lat},{center_lon}&zoom={zoom}"
    return url

def create_google_maps_embed_url(bounding_box):
    """Create a Google Maps embed URL for iframe use"""
    center_lat = bounding_box['center_lat']
    center_lon = bounding_box['center_lon']
    
    # Calculate zoom level based on bounding box size
    lat_diff = bounding_box['max_lat'] - bounding_box['min_lat']
    lon_diff = bounding_box['max_lon'] - bounding_box['min_lon']
    max_diff = max(lat_diff, lon_diff)
    
    # Approximate zoom level calculation
    if max_diff > 0.1:
        zoom = 10
    elif max_diff > 0.01:
        zoom = 14
    elif max_diff > 0.001:
        zoom = 16
    else:
        zoom = 18
    
    # Google Maps embed URL format
    url = f"https://www.google.com/maps/embed/v1/view?key=YOUR_API_KEY&center={center_lat},{center_lon}&zoom={zoom}"
    return url

def main():
    """Main function to process KML files and generate URLs"""
    kml_files = [
        'NDBI_BuiltUp_Analysis.kml',
        'NDVI_Vegetation_Analysis.kml', 
        'NDWI_Water_Analysis.kml'
    ]
    
    print("KML to Google Earth/Maps URL Converter")
    print("=" * 50)
    
    for kml_file in kml_files:
        print(f"\nProcessing: {kml_file}")
        print("-" * 30)
        
        try:
            # Parse coordinates from KML file
            coordinates = parse_kml_coordinates(kml_file)
            
            if not coordinates:
                print(f"  No coordinates found in {kml_file}")
                continue
            
            # Calculate bounding box
            bbox = calculate_bounding_box(coordinates)
            
            print(f"  Coordinates found: {len(coordinates)}")
            print(f"  Bounding box:")
            print(f"    Latitude: {bbox['min_lat']:.6f} to {bbox['max_lat']:.6f}")
            print(f"    Longitude: {bbox['min_lon']:.6f} to {bbox['max_lon']:.6f}")
            print(f"    Center: {bbox['center_lat']:.6f}, {bbox['center_lon']:.6f}")
            
            # Generate URLs
            earth_url = create_google_earth_url(bbox)
            maps_url = create_google_maps_url(bbox)
            
            print(f"\n  Google Earth URL:")
            print(f"    {earth_url}")
            print(f"\n  Google Maps URL:")
            print(f"    {maps_url}")
            
        except Exception as e:
            print(f"  Error processing {kml_file}: {e}")
    
    print("\n" + "=" * 50)
    print("URL Generation Complete!")

if __name__ == "__main__":
    main()
