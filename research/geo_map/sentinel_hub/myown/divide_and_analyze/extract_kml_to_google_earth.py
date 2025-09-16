#!/usr/bin/env python3
"""
Extract KML parameters and build Google Earth Web URLs
No local server required - all parameters embedded in URL
"""

import xml.etree.ElementTree as ET
import urllib.parse
import os
from typing import List, Dict, Tuple


class KMLToGoogleEarthConverter:
    def __init__(self):
        self.namespace = {'kml': 'http://www.opengis.net/kml/2.2'}
    
    def extract_kml_data(self, kml_path: str) -> Dict:
        """Extract all relevant data from KML file"""
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
    
    def build_google_earth_url(self, kml_data: Dict) -> str:
        """Build Google Earth Web URL with all extracted parameters"""
        if not kml_data or not kml_data['squares']:
            return None
        
        # Calculate overall center
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
        
        # Calculate appropriate altitude based on area size
        lat_span = north - south
        lon_span = east - west
        max_span = max(lat_span, lon_span)
        
        # Determine altitude (in meters)
        if max_span > 1.0:
            altitude = 100000  # 100km
        elif max_span > 0.1:
            altitude = 10000   # 10km
        elif max_span > 0.01:
            altitude = 5000    # 5km
        elif max_span > 0.001:
            altitude = 2000    # 2km
        else:
            altitude = 1000    # 1km
        
        # Build the URL with all parameters
        url = (f"https://earth.google.com/web/@{center_lat},{center_lon},"
               f"{altitude}a,{altitude}d,35y,0h,0t,0r")
        
        return url
    
    def build_search_url(self, kml_data: Dict) -> str:
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
        
        return f"https://earth.google.com/web/search/{encoded_query}"
    
    def generate_urls(self, kml_path: str) -> Dict:
        """Generate Google Earth URLs for a KML file"""
        kml_data = self.extract_kml_data(kml_path)
        if not kml_data:
            return None
        
        urls = {
            'kml_file': kml_path,
            'document_name': kml_data['document_name'],
            'total_squares': kml_data['total_squares'],
            'urls': {
                'google_earth_3d': self.build_google_earth_url(kml_data),
                'google_earth_search': self.build_search_url(kml_data)
            },
            'center_coordinates': None,
            'bounds': None
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
    converter = KMLToGoogleEarthConverter()
    
    # Define KML files
    kml_files = [
        ("output/20250824_100752/NDVI_Vegetation_Analysis.kml", "🌱 NDVI (Vegetation) - Blue Borders"),
        ("output/20250824_100752/NDBI_BuiltUp_Analysis.kml", "🏢 NDBI (Built-up Areas) - Red Borders"),
        ("output/20250824_100752/NDWI_Water_Analysis.kml", "💧 NDWI (Water/Moisture) - Yellow Borders"),
        ("output/20250824_100752/enhanced_significant_indices_squares.kml", "🌍 Combined (All Indices) - Multi-color")
    ]
    
    print("🌐 KML to Google Earth Web URL Converter")
    print("=" * 60)
    print("Extracting parameters from KML files and building URLs...")
    print("No local server required - all parameters embedded in URL")
    print("=" * 60)
    
    all_results = []
    
    for kml_path, description in kml_files:
        if not os.path.exists(kml_path):
            print(f"❌ KML file not found: {kml_path}")
            continue
        
        print(f"\n📁 Processing: {description}")
        print(f"   File: {kml_path}")
        
        result = converter.generate_urls(kml_path)
        if result:
            all_results.append(result)
            
            print(f"   ✅ Squares found: {result['total_squares']}")
            print(f"   📍 Center: {result['center_coordinates']}")
            print(f"   🔗 3D URL: {result['urls']['google_earth_3d']}")
            print(f"   🔍 Search URL: {result['urls']['google_earth_search']}")
        else:
            print(f"   ❌ Failed to process KML file")
    
    # Save results to file
    output_file = "google_earth_urls_from_kml.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("🌐 GOOGLE EARTH WEB URLs FROM KML PARAMETERS\n")
        f.write("=" * 60 + "\n")
        f.write("All parameters extracted from KML files - No local server required\n")
        f.write("=" * 60 + "\n\n")
        
        for result in all_results:
            f.write(f"📁 {result['document_name']}\n")
            f.write(f"🔢 Total Squares: {result['total_squares']}\n")
            f.write(f"📍 Center Coordinates: {result['center_coordinates']}\n\n")
            
            f.write("🔗 URLs:\n")
            f.write(f"   3D View: {result['urls']['google_earth_3d']}\n")
            f.write(f"   Search: {result['urls']['google_earth_search']}\n")
            f.write("\n" + "-" * 40 + "\n\n")
    
    print(f"\n✅ Results saved to: {output_file}")
    print(f"📋 Total KML files processed: {len(all_results)}")


if __name__ == "__main__":
    main()
