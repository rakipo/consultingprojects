#!/usr/bin/env python3
"""
Simple KML URL Generator

A streamlined script to generate Google Maps and Google Earth URLs from KML files.
Also creates importable KML content for better visualization.
"""

import xml.etree.ElementTree as ET
import urllib.parse
import os
import webbrowser
from typing import List, Tuple


def parse_kml_coordinates(coord_string: str) -> List[Tuple[float, float]]:
    """Extract lat/lon coordinates from KML coordinate string."""
    coordinates = []
    for coord in coord_string.strip().split():
        if coord.strip():
            parts = coord.split(',')
            if len(parts) >= 2:
                lon, lat = float(parts[0]), float(parts[1])
                coordinates.append((lat, lon))
    return coordinates


def get_polygon_bounds(coordinates: List[Tuple[float, float]]) -> dict:
    """Calculate bounding box and center point."""
    if not coordinates:
        return {}
    
    lats = [coord[0] for coord in coordinates]
    lons = [coord[1] for coord in coordinates]
    
    return {
        'center_lat': sum(lats) / len(lats),
        'center_lon': sum(lons) / len(lons),
        'min_lat': min(lats),
        'max_lat': max(lats),
        'min_lon': min(lons),
        'max_lon': max(lons)
    }


def create_google_maps_url(bounds: dict, name: str = "") -> str:
    """Create Google Maps URL centered on the polygon area."""
    center = f"{bounds['center_lat']},{bounds['center_lon']}"
    
    # Calculate appropriate zoom level based on bounds
    lat_diff = bounds['max_lat'] - bounds['min_lat']
    lon_diff = bounds['max_lon'] - bounds['min_lon']
    max_diff = max(lat_diff, lon_diff)
    
    # Rough zoom calculation
    if max_diff > 0.1:
        zoom = 10
    elif max_diff > 0.01:
        zoom = 14
    elif max_diff > 0.001:
        zoom = 17
    else:
        zoom = 19
    
    url = f"https://www.google.com/maps/@{center},{zoom}z"
    return url


def create_google_earth_url(bounds: dict) -> str:
    """Create Google Earth Web URL."""
    center = f"{bounds['center_lat']},{bounds['center_lon']}"
    url = f"https://earth.google.com/web/@{center},1000a,35y,0h,0t,0r"
    return url


def process_kml_file(filename: str) -> None:
    """Process a single KML file and generate URLs."""
    try:
        tree = ET.parse(filename)
        root = tree.getroot()
        
        # Handle namespace
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}
        
        print(f"\n🗺️  Processing: {filename}")
        print("=" * 50)
        
        # Find all placemarks with polygons
        placemarks = root.findall('.//kml:Placemark', ns)
        
        if not placemarks:
            print("No placemarks found in this KML file.")
            return
        
        for i, placemark in enumerate(placemarks, 1):
            name_elem = placemark.find('kml:name', ns)
            name = name_elem.text if name_elem is not None else f"Polygon {i}"
            
            # Find polygon coordinates
            coord_elem = placemark.find('.//kml:coordinates', ns)
            if coord_elem is None:
                continue
                
            coordinates = parse_kml_coordinates(coord_elem.text)
            if not coordinates:
                continue
                
            bounds = get_polygon_bounds(coordinates)
            
            print(f"\n📍 {name}")
            print(f"   Center: {bounds['center_lat']:.6f}, {bounds['center_lon']:.6f}")
            print(f"   Area: {len(coordinates)} boundary points")
            
            # Generate URLs
            maps_url = create_google_maps_url(bounds, name)
            earth_url = create_google_earth_url(bounds)
            
            print(f"\n   🌍 Google Maps: {maps_url}")
            print(f"   🌎 Google Earth: {earth_url}")
            
            # Show coordinate bounds
            print(f"   📐 Bounds: ({bounds['min_lat']:.6f}, {bounds['min_lon']:.6f}) to ({bounds['max_lat']:.6f}, {bounds['max_lon']:.6f})")
            
    except ET.ParseError as e:
        print(f"❌ Error parsing {filename}: {e}")
    except Exception as e:
        print(f"❌ Error processing {filename}: {e}")


def create_combined_kml(kml_files: List[str]) -> str:
    """Create a combined KML file that can be imported into Google Earth."""
    combined_kml = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Combined Analysis Areas</name>
    <description>Combined boundaries from multiple analysis files</description>
    
    <Style id="ndbi_style">
      <LineStyle>
        <color>ff0000ff</color>
        <width>2</width>
      </LineStyle>
      <PolyStyle>
        <fill>0</fill>
        <outline>1</outline>
      </PolyStyle>
    </Style>
    
    <Style id="ndvi_style">
      <LineStyle>
        <color>ff00ff00</color>
        <width>2</width>
      </LineStyle>
      <PolyStyle>
        <fill>0</fill>
        <outline>1</outline>
      </PolyStyle>
    </Style>
    
    <Style id="ndwi_style">
      <LineStyle>
        <color>ffff0000</color>
        <width>2</width>
      </LineStyle>
      <PolyStyle>
        <fill>0</fill>
        <outline>1</outline>
      </PolyStyle>
    </Style>
'''
    
    for kml_file in kml_files:
        if not os.path.exists(kml_file):
            continue
            
        try:
            tree = ET.parse(kml_file)
            root = tree.getroot()
            ns = {'kml': 'http://www.opengis.net/kml/2.2'}
            
            # Determine style based on filename
            if 'NDBI' in kml_file:
                style = 'ndbi_style'
            elif 'NDVI' in kml_file:
                style = 'ndvi_style'
            elif 'NDWI' in kml_file:
                style = 'ndwi_style'
            else:
                style = 'ndbi_style'
            
            # Add folder for this analysis type
            analysis_type = kml_file.replace('.kml', '').replace('_', ' ')
            combined_kml += f'''
    <Folder>
      <name>{analysis_type}</name>
      <description>Areas from {kml_file}</description>
'''
            
            # Copy placemarks
            for placemark in root.findall('.//kml:Placemark', ns):
                name_elem = placemark.find('kml:name', ns)
                desc_elem = placemark.find('kml:description', ns)
                coord_elem = placemark.find('.//kml:coordinates', ns)
                
                if coord_elem is not None:
                    name = name_elem.text if name_elem is not None else "Unnamed"
                    desc = desc_elem.text if desc_elem is not None else ""
                    coords = coord_elem.text
                    
                    combined_kml += f'''
      <Placemark>
        <name>{name}</name>
        <description>{desc}</description>
        <styleUrl>#{style}</styleUrl>
        <Polygon>
          <outerBoundaryIs>
            <LinearRing>
              <coordinates>{coords}</coordinates>
            </LinearRing>
          </outerBoundaryIs>
        </Polygon>
      </Placemark>'''
            
            combined_kml += '''
    </Folder>'''
            
        except Exception as e:
            print(f"❌ Error processing {kml_file} for combined KML: {e}")
    
    combined_kml += '''
  </Document>
</kml>'''
    
    return combined_kml


def main():
    """Main function."""
    # Find KML files in current directory
    kml_files = [f for f in os.listdir('.') if f.endswith('.kml')]
    
    if not kml_files:
        print("❌ No KML files found in current directory.")
        return
    
    print("🗺️  KML to Google Maps/Earth URL Generator")
    print("=" * 50)
    print(f"Found {len(kml_files)} KML files:")
    for f in kml_files:
        print(f"  • {f}")
    
    # Process each KML file
    for kml_file in kml_files:
        process_kml_file(kml_file)
    
    # Create combined KML file
    print(f"\n📁 Creating combined KML file...")
    combined_content = create_combined_kml(kml_files)
    
    with open('combined_analysis_areas.kml', 'w', encoding='utf-8') as f:
        f.write(combined_content)
    
    print(f"✅ Created: combined_analysis_areas.kml")
    print(f"\n💡 Tips:")
    print(f"   • Copy URLs and paste into browser")
    print(f"   • Import combined_analysis_areas.kml into Google Earth for best visualization")
    print(f"   • Google Earth Pro (desktop) shows polygon boundaries more clearly")


if __name__ == "__main__":
    main()