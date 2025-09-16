#!/usr/bin/env python3
"""
Build Google Earth Web URLs from KML files
Extracts coordinates and parameters to create proper URLs
"""

import xml.etree.ElementTree as ET
import re
import urllib.parse
from typing import List, Dict, Tuple
import os


class GoogleEarthURLBuilder:
    def __init__(self):
        self.google_earth_base = "https://earth.google.com/web/"
        self.namespace = {'kml': 'http://www.opengis.net/kml/2.2'}
    
    def parse_kml_file(self, kml_path: str) -> Dict:
        """Parse KML file and extract all relevant data"""
        try:
            tree = ET.parse(kml_path)
            root = tree.getroot()
            
            # Extract document info
            doc_name = root.find('.//kml:name', self.namespace)
            doc_desc = root.find('.//kml:description', self.namespace)
            
            # Extract all placemarks
            placemarks = root.findall('.//kml:Placemark', self.namespace)
            
            # Extract coordinates and metadata
            squares_data = []
            for placemark in placemarks:
                square_data = self.extract_placemark_data(placemark)
                if square_data:
                    squares_data.append(square_data)
            
            return {
                'document_name': doc_name.text if doc_name is not None else 'KML Document',
                'document_description': doc_desc.text if doc_desc is not None else '',
                'squares': squares_data,
                'total_squares': len(squares_data)
            }
            
        except Exception as e:
            print(f"❌ Error parsing KML file: {e}")
            return None
    
    def extract_placemark_data(self, placemark) -> Dict:
        """Extract data from a single placemark"""
        try:
            # Get name
            name_elem = placemark.find('kml:name', self.namespace)
            name = name_elem.text if name_elem is not None else 'Unknown'
            
            # Get description
            desc_elem = placemark.find('kml:description', self.namespace)
            description = desc_elem.text if desc_elem is not None else ''
            
            # Extract coordinates
            coords_elem = placemark.find('.//kml:coordinates', self.namespace)
            if coords_elem is not None:
                coordinates = self.parse_coordinates(coords_elem.text)
                if coordinates:
                    center_lat, center_lon = self.calculate_center(coordinates)
                    return {
                        'name': name,
                        'description': description,
                        'coordinates': coordinates,
                        'center_lat': center_lat,
                        'center_lon': center_lon,
                        'bounds': self.calculate_bounds(coordinates)
                    }
            
            return None
            
        except Exception as e:
            print(f"❌ Error extracting placemark data: {e}")
            return None
    
    def parse_coordinates(self, coord_text: str) -> List[Tuple[float, float]]:
        """Parse coordinate string into list of (lon, lat) tuples"""
        if not coord_text:
            return []
        
        coordinates = []
        # Split by spaces and process each coordinate
        coord_pairs = coord_text.strip().split()
        
        for pair in coord_pairs:
            parts = pair.split(',')
            if len(parts) >= 2:
                try:
                    lon = float(parts[0])
                    lat = float(parts[1])
                    coordinates.append((lon, lat))
                except ValueError:
                    continue
        
        return coordinates
    
    def calculate_center(self, coordinates: List[Tuple[float, float]]) -> Tuple[float, float]:
        """Calculate center point of coordinates"""
        if not coordinates:
            return (0, 0)
        
        lons = [coord[0] for coord in coordinates]
        lats = [coord[1] for coord in coordinates]
        
        center_lon = sum(lons) / len(lons)
        center_lat = sum(lats) / len(lats)
        
        return (center_lat, center_lon)
    
    def calculate_bounds(self, coordinates: List[Tuple[float, float]]) -> Dict:
        """Calculate bounding box of coordinates"""
        if not coordinates:
            return {'north': 0, 'south': 0, 'east': 0, 'west': 0}
        
        lons = [coord[0] for coord in coordinates]
        lats = [coord[1] for coord in coordinates]
        
        return {
            'north': max(lats),
            'south': min(lats),
            'east': max(lons),
            'west': min(lons)
        }
    
    def build_google_earth_url_with_kml(self, kml_data: Dict, index_type: str = "ndvi", kml_url: str = None) -> str:
        """Build Google Earth Web URL with KML data parameter"""
        if not kml_data or not kml_data['squares']:
            return None
        
        # Calculate overall center and bounds
        all_centers = [(square['center_lat'], square['center_lon']) for square in kml_data['squares']]
        center_lat = sum(center[0] for center in all_centers) / len(all_centers)
        center_lon = sum(center[1] for center in all_centers) / len(all_centers)
        
        # Calculate overall bounds
        all_lats = [square['bounds']['north'] for square in kml_data['squares']] + [square['bounds']['south'] for square in kml_data['squares']]
        all_lons = [square['bounds']['east'] for square in kml_data['squares']] + [square['bounds']['west'] for square in kml_data['squares']]
        
        north = max(all_lats)
        south = min(all_lats)
        east = max(all_lons)
        west = min(all_lons)
        
        # Calculate appropriate zoom level based on area size
        lat_span = north - south
        lon_span = east - west
        max_span = max(lat_span, lon_span)
        
        # Determine zoom level (higher zoom = closer view)
        if max_span > 1.0:
            zoom = 10
        elif max_span > 0.1:
            zoom = 12
        elif max_span > 0.01:
            zoom = 15
        elif max_span > 0.001:
            zoom = 18
        else:
            zoom = 20
        
        # Build the URL with KML data parameter
        if kml_url:
            # Encode the KML URL
            encoded_kml_url = urllib.parse.quote(kml_url, safe='')
            url = (f"{self.google_earth_base}@{center_lat},{center_lon},"
                   f"5000a,5000d,35y,0h,0t,0r/data={encoded_kml_url}")
        else:
            # Fallback to location-only URL
            url = (f"{self.google_earth_base}@{center_lat},{center_lon},"
                   f"5000a,5000d,35y,0h,0t,0r")
        
        return url
    
    def build_search_url(self, kml_data: Dict, index_type: str = "ndvi") -> str:
        """Build Google Earth search URL with coordinates"""
        if not kml_data or not kml_data['squares']:
            return None
        
        # Get center coordinates
        all_centers = [(square['center_lat'], square['center_lon']) for square in kml_data['squares']]
        center_lat = sum(center[0] for center in all_centers) / len(all_centers)
        center_lon = sum(center[1] for center in all_centers) / len(all_centers)
        
        # Build search query
        search_query = f"{center_lat},{center_lon}"
        encoded_query = urllib.parse.quote(search_query)
        
        return f"{self.google_earth_base}search/{encoded_query}"
    
    def generate_all_urls(self, kml_path: str, index_type: str = "ndvi", kml_url: str = None) -> Dict:
        """Generate all types of Google Earth URLs for a KML file"""
        kml_data = self.parse_kml_file(kml_path)
        if not kml_data:
            return None
        
        urls = {
            'kml_file': kml_path,
            'document_name': kml_data['document_name'],
            'total_squares': kml_data['total_squares'],
            'index_type': index_type,
            'urls': {
                'google_earth_3d': self.build_google_earth_url_with_kml(kml_data, index_type, kml_url),
                'google_earth_search': self.build_search_url(kml_data, index_type)
            },
            'center_coordinates': None,
            'bounds': None,
            'kml_url': kml_url
        }
        
        # Add center coordinates
        if kml_data['squares']:
            all_centers = [(square['center_lat'], square['center_lon']) for square in kml_data['squares']]
            center_lat = sum(center[0] for center in all_centers) / len(all_centers)
            center_lon = sum(center[1] for center in all_centers) / len(all_centers)
            urls['center_coordinates'] = f"{center_lat:.6f}, {center_lon:.6f}"
        
        return urls


def main():
    """Main function to generate URLs for all KML files"""
    builder = GoogleEarthURLBuilder()
    
    # Define KML files and their types with web server URLs
    kml_files = [
        ("output/20250824_100752/NDVI_Vegetation_Analysis.kml", "ndvi", "🌱 NDVI (Vegetation) - Blue Borders", "http://localhost:8000/NDVI_Vegetation_Analysis.kml"),
        ("output/20250824_100752/NDBI_BuiltUp_Analysis.kml", "ndbi", "🏢 NDBI (Built-up Areas) - Red Borders", "http://localhost:8000/NDBI_BuiltUp_Analysis.kml"),
        ("output/20250824_100752/NDWI_Water_Analysis.kml", "ndwi", "💧 NDWI (Water/Moisture) - Yellow Borders", "http://localhost:8000/NDWI_Water_Analysis.kml"),
        ("output/20250824_100752/enhanced_significant_indices_squares.kml", "combined", "🌍 Combined (All Indices) - Multi-color", "http://localhost:8000/enhanced_significant_indices_squares.kml")
    ]
    
    print("🌐 Google Earth Web URL Generator with KML Overlay")
    print("=" * 60)
    
    all_results = []
    
    for kml_path, index_type, description, kml_url in kml_files:
        if not os.path.exists(kml_path):
            print(f"❌ KML file not found: {kml_path}")
            continue
        
        print(f"\n📁 Processing: {description}")
        print(f"   File: {kml_path}")
        print(f"   🌐 KML URL: {kml_url}")
        
        result = builder.generate_all_urls(kml_path, index_type, kml_url)
        if result:
            all_results.append(result)
            
            print(f"   ✅ Squares found: {result['total_squares']}")
            print(f"   📍 Center: {result['center_coordinates']}")
            print(f"   🔗 3D URL with KML: {result['urls']['google_earth_3d']}")
            print(f"   🔍 Search URL: {result['urls']['google_earth_search']}")
        else:
            print(f"   ❌ Failed to process KML file")
    
    # Save results to file
    output_file = "google_earth_urls_with_params.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("🌐 GOOGLE EARTH WEB URLs WITH PARAMETERS\n")
        f.write("=" * 60 + "\n\n")
        
        for result in all_results:
            f.write(f"📁 {result['document_name']}\n")
            f.write(f"🔢 Total Squares: {result['total_squares']}\n")
            f.write(f"📍 Center Coordinates: {result['center_coordinates']}\n")
            f.write(f"🎯 Index Type: {result['index_type'].upper()}\n\n")
            
            f.write("🔗 URLs:\n")
            f.write(f"   3D View: {result['urls']['google_earth_3d']}\n")
            f.write(f"   Search: {result['urls']['google_earth_search']}\n")
            f.write("\n" + "-" * 40 + "\n\n")
    
    print(f"\n✅ Results saved to: {output_file}")
    print(f"📋 Total KML files processed: {len(all_results)}")


if __name__ == "__main__":
    main()
