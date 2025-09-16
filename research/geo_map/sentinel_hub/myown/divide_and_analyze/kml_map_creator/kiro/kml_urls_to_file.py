#!/usr/bin/env python3
"""
KML URLs to File Generator

Processes KML files and saves all Google Maps/Earth URLs to output files.
"""

import xml.etree.ElementTree as ET
import os
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


def get_polygon_bounds(coordinates: List[tuple]) -> dict:
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


def create_urls(bounds: dict) -> dict:
    """Create Google Maps and Earth URLs."""
    center = f"{bounds['center_lat']},{bounds['center_lon']}"
    
    # Calculate zoom level
    lat_diff = bounds['max_lat'] - bounds['min_lat']
    lon_diff = bounds['max_lon'] - bounds['min_lon']
    max_diff = max(lat_diff, lon_diff)
    
    if max_diff > 0.1:
        zoom = 10
    elif max_diff > 0.01:
        zoom = 14
    elif max_diff > 0.001:
        zoom = 17
    else:
        zoom = 19
    
    return {
        'google_maps': f"https://www.google.com/maps/@{center},{zoom}z",
        'google_earth': f"https://earth.google.com/web/@{center},1000a,35y,0h,0t,0r",
        'google_maps_satellite': f"https://www.google.com/maps/@{center},{zoom}z/data=!3m1!1e3",
        'coordinates': center,
        'zoom_level': zoom
    }


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
                    bounds = get_polygon_bounds(coordinates)
                    urls = create_urls(bounds)
                    
                    polygon_data = {
                        'name': name_elem.text if name_elem is not None else 'Unnamed',
                        'description': desc_elem.text if desc_elem is not None else '',
                        'source_file': filename,
                        'bounds': bounds,
                        'urls': urls,
                        'coordinate_count': len(coordinates)
                    }
                    polygons.append(polygon_data)
        
        return polygons
        
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        return []


def generate_text_output(all_polygons: Dict[str, List[Dict]]) -> str:
    """Generate comprehensive text output with all URLs."""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    output = f"""KML Analysis Areas - Google Maps/Earth URLs
Generated: {timestamp}
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
        
        output += f"{analysis_type.upper()}\n"
        output += f"Source: {filename}\n"
        output += f"{'-'*60}\n\n"
        
        for i, polygon in enumerate(polygons, 1):
            output += f"{i}. {polygon['name']}\n"
            
            # Coordinates and bounds
            bounds = polygon['bounds']
            output += f"   Center: {bounds['center_lat']:.6f}, {bounds['center_lon']:.6f}\n"
            output += f"   Bounds: ({bounds['min_lat']:.6f}, {bounds['min_lon']:.6f}) to ({bounds['max_lat']:.6f}, {bounds['max_lon']:.6f})\n"
            output += f"   Points: {polygon['coordinate_count']} boundary coordinates\n"
            
            # URLs
            urls = polygon['urls']
            output += f"\n   Google Maps (Standard):\n   {urls['google_maps']}\n"
            output += f"\n   Google Maps (Satellite):\n   {urls['google_maps_satellite']}\n"
            output += f"\n   Google Earth Web:\n   {urls['google_earth']}\n"
            
            # Description if available
            if polygon['description'].strip():
                desc_lines = polygon['description'].strip().split('\n')
                output += f"\n   Description:\n"
                for line in desc_lines[:5]:  # Limit to first 5 lines
                    if line.strip():
                        output += f"   {line.strip()}\n"
                if len(desc_lines) > 5:
                    output += f"   ... (truncated)\n"
            
            output += f"\n{'-'*40}\n\n"
        
        output += f"\n{'='*60}\n\n"
    
    return output


def generate_csv_output(all_polygons: Dict[str, List[Dict]]) -> str:
    """Generate CSV format output."""
    
    csv_content = "Analysis_Type,Polygon_Name,Center_Lat,Center_Lon,Google_Maps_URL,Google_Earth_URL,Google_Maps_Satellite_URL,Source_File\n"
    
    for filename, polygons in all_polygons.items():
        analysis_type = filename.replace('.kml', '').replace('_', ' ')
        
        for polygon in polygons:
            bounds = polygon['bounds']
            urls = polygon['urls']
            
            # Clean name for CSV
            name = polygon['name'].replace(',', ';').replace('"', "'")
            
            csv_content += f'"{analysis_type}","{name}",{bounds["center_lat"]:.6f},{bounds["center_lon"]:.6f},"{urls["google_maps"]}","{urls["google_earth"]}","{urls["google_maps_satellite"]}","{filename}"\n'
    
    return csv_content


def generate_json_output(all_polygons: Dict[str, List[Dict]]) -> str:
    """Generate JSON format output."""
    import json
    
    json_data = {
        "generated": datetime.now().isoformat(),
        "total_areas": sum(len(polygons) for polygons in all_polygons.values()),
        "analysis_files": {}
    }
    
    for filename, polygons in all_polygons.items():
        analysis_type = filename.replace('.kml', '').replace('_', ' ')
        
        json_data["analysis_files"][analysis_type] = {
            "source_file": filename,
            "area_count": len(polygons),
            "areas": []
        }
        
        for polygon in polygons:
            area_data = {
                "name": polygon['name'],
                "center": {
                    "latitude": polygon['bounds']['center_lat'],
                    "longitude": polygon['bounds']['center_lon']
                },
                "bounds": {
                    "min_lat": polygon['bounds']['min_lat'],
                    "max_lat": polygon['bounds']['max_lat'],
                    "min_lon": polygon['bounds']['min_lon'],
                    "max_lon": polygon['bounds']['max_lon']
                },
                "urls": polygon['urls'],
                "coordinate_count": polygon['coordinate_count']
            }
            
            if polygon['description'].strip():
                area_data["description"] = polygon['description'].strip()
            
            json_data["analysis_files"][analysis_type]["areas"].append(area_data)
    
    return json.dumps(json_data, indent=2)


def main():
    """Main function to process KML files and generate output files."""
    
    # Find KML files
    kml_files = [f for f in os.listdir('.') if f.endswith('.kml') and not f.startswith('combined_')]
    
    if not kml_files:
        print("❌ No KML files found in current directory.")
        return
    
    print("📄 Processing KML files and generating URL output files...")
    print(f"Found {len(kml_files)} KML files: {', '.join(kml_files)}")
    
    all_polygons = {}
    
    # Process all KML files
    for kml_file in kml_files:
        print(f"   Processing {kml_file}...")
        polygons = process_kml_file(kml_file)
        if polygons:
            all_polygons[kml_file] = polygons
    
    if not all_polygons:
        print("❌ No valid polygons found in KML files.")
        return
    
    total_areas = sum(len(polygons) for polygons in all_polygons.values())
    
    # Generate output files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Text format
    print("   Generating text output...")
    text_content = generate_text_output(all_polygons)
    text_filename = f"kml_urls_{timestamp}.txt"
    with open(text_filename, 'w', encoding='utf-8') as f:
        f.write(text_content)
    
    # 2. CSV format
    print("   Generating CSV output...")
    csv_content = generate_csv_output(all_polygons)
    csv_filename = f"kml_urls_{timestamp}.csv"
    with open(csv_filename, 'w', encoding='utf-8') as f:
        f.write(csv_content)
    
    # 3. JSON format
    print("   Generating JSON output...")
    json_content = generate_json_output(all_polygons)
    json_filename = f"kml_urls_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        f.write(json_content)
    
    # 4. Simple URLs only file
    print("   Generating simple URLs file...")
    simple_content = f"KML Analysis Areas URLs - Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    simple_content += "="*80 + "\n\n"
    
    for filename, polygons in all_polygons.items():
        analysis_type = filename.replace('.kml', '').replace('_', ' ')
        simple_content += f"{analysis_type.upper()}\n{'-'*40}\n"
        
        for polygon in polygons:
            simple_content += f"{polygon['name']}\n"
            simple_content += f"Google Maps: {polygon['urls']['google_maps']}\n"
            simple_content += f"Google Earth: {polygon['urls']['google_earth']}\n\n"
        
        simple_content += "\n"
    
    simple_filename = f"kml_urls_simple_{timestamp}.txt"
    with open(simple_filename, 'w', encoding='utf-8') as f:
        f.write(simple_content)
    
    # Summary
    print(f"\n✅ Successfully generated URL output files:")
    print(f"   📄 {text_filename} - Detailed text format with all information")
    print(f"   📊 {csv_filename} - CSV format for spreadsheet import")
    print(f"   🔗 {json_filename} - JSON format for programmatic use")
    print(f"   📝 {simple_filename} - Simple URLs only")
    
    print(f"\n📊 Summary:")
    print(f"   • Processed {len(all_polygons)} KML files")
    print(f"   • Generated URLs for {total_areas} analysis areas")
    print(f"   • Created 4 different output formats")
    
    print(f"\n💡 Usage:")
    print(f"   • Open .txt files in any text editor")
    print(f"   • Import .csv file into Excel/Google Sheets")
    print(f"   • Use .json file for web applications")


if __name__ == "__main__":
    main()