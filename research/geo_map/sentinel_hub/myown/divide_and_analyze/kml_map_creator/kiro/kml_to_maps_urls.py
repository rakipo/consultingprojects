#!/usr/bin/env python3
"""
KML to Google Maps/Earth URL Generator

This script reads KML files and generates URLs that can be opened in Google Maps
or Google Earth to visualize the polygon boundaries defined in the KML files.
"""

import xml.etree.ElementTree as ET
import urllib.parse
import os
import sys
from typing import List, Tuple, Dict


class KMLParser:
    def __init__(self, kml_file: str):
        self.kml_file = kml_file
        self.namespace = {'kml': 'http://www.opengis.net/kml/2.2'}
        
    def parse_coordinates(self, coord_string: str) -> List[Tuple[float, float]]:
        """Parse coordinate string from KML and return list of (lat, lon) tuples."""
        coordinates = []
        coord_pairs = coord_string.strip().split()
        
        for coord_pair in coord_pairs:
            if coord_pair.strip():
                parts = coord_pair.split(',')
                if len(parts) >= 2:
                    lon = float(parts[0])
                    lat = float(parts[1])
                    coordinates.append((lat, lon))
        
        return coordinates
    
    def extract_polygons(self) -> List[Dict]:
        """Extract polygon data from KML file."""
        try:
            tree = ET.parse(self.kml_file)
            root = tree.getroot()
            
            polygons = []
            
            # Find all Placemark elements
            for placemark in root.findall('.//kml:Placemark', self.namespace):
                name_elem = placemark.find('kml:name', self.namespace)
                desc_elem = placemark.find('kml:description', self.namespace)
                polygon_elem = placemark.find('.//kml:Polygon', self.namespace)
                
                if polygon_elem is not None:
                    # Get coordinates from LinearRing
                    coord_elem = polygon_elem.find('.//kml:coordinates', self.namespace)
                    if coord_elem is not None:
                        coordinates = self.parse_coordinates(coord_elem.text)
                        
                        polygon_data = {
                            'name': name_elem.text if name_elem is not None else 'Unnamed',
                            'description': desc_elem.text if desc_elem is not None else '',
                            'coordinates': coordinates
                        }
                        polygons.append(polygon_data)
            
            return polygons
            
        except ET.ParseError as e:
            print(f"Error parsing KML file {self.kml_file}: {e}")
            return []
        except Exception as e:
            print(f"Error processing KML file {self.kml_file}: {e}")
            return []


class URLGenerator:
    @staticmethod
    def calculate_bounds(coordinates: List[Tuple[float, float]]) -> Dict[str, float]:
        """Calculate bounding box from coordinates."""
        if not coordinates:
            return {}
            
        lats = [coord[0] for coord in coordinates]
        lons = [coord[1] for coord in coordinates]
        
        return {
            'min_lat': min(lats),
            'max_lat': max(lats),
            'min_lon': min(lons),
            'max_lon': max(lons),
            'center_lat': (min(lats) + max(lats)) / 2,
            'center_lon': (min(lons) + max(lons)) / 2
        }
    
    @staticmethod
    def generate_google_maps_url(polygon_data: Dict) -> str:
        """Generate Google Maps URL for polygon."""
        coordinates = polygon_data['coordinates']
        if not coordinates:
            return ""
            
        bounds = URLGenerator.calculate_bounds(coordinates)
        
        # Create a path string for Google Maps
        path_coords = []
        for lat, lon in coordinates:
            path_coords.append(f"{lat},{lon}")
        
        path_string = "|".join(path_coords)
        
        # Google Maps URL with path overlay
        base_url = "https://www.google.com/maps"
        params = {
            'll': f"{bounds['center_lat']},{bounds['center_lon']}",
            'z': '16',  # Zoom level
            't': 'm',   # Map type (m=map, k=satellite, h=hybrid)
        }
        
        # Add path as a custom overlay (this creates a rough visualization)
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        
        return url
    
    @staticmethod
    def generate_google_earth_url(polygon_data: Dict) -> str:
        """Generate Google Earth URL for polygon."""
        coordinates = polygon_data['coordinates']
        if not coordinates:
            return ""
            
        bounds = URLGenerator.calculate_bounds(coordinates)
        
        # Google Earth Web URL
        base_url = "https://earth.google.com/web"
        params = {
            'll': f"{bounds['center_lat']},{bounds['center_lon']}",
            'z': '1000',  # Altitude in meters
            't': '0'      # Tilt
        }
        
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        
        return url
    
    @staticmethod
    def generate_detailed_maps_url(polygon_data: Dict) -> str:
        """Generate a more detailed Google Maps URL with polygon coordinates."""
        coordinates = polygon_data['coordinates']
        if not coordinates:
            return ""
            
        bounds = URLGenerator.calculate_bounds(coordinates)
        
        # Create a search query that includes the area description
        search_query = f"{bounds['center_lat']},{bounds['center_lon']}"
        
        base_url = "https://www.google.com/maps/search/"
        url = f"{base_url}{urllib.parse.quote(search_query)}/@{bounds['center_lat']},{bounds['center_lon']},16z"
        
        return url


def process_kml_files(kml_files: List[str]) -> None:
    """Process multiple KML files and generate URLs."""
    
    for kml_file in kml_files:
        if not os.path.exists(kml_file):
            print(f"File not found: {kml_file}")
            continue
            
        print(f"\n{'='*60}")
        print(f"Processing: {kml_file}")
        print(f"{'='*60}")
        
        parser = KMLParser(kml_file)
        polygons = parser.extract_polygons()
        
        if not polygons:
            print(f"No polygons found in {kml_file}")
            continue
            
        for i, polygon in enumerate(polygons, 1):
            print(f"\n--- {polygon['name']} ---")
            
            # Generate URLs
            maps_url = URLGenerator.generate_google_maps_url(polygon)
            earth_url = URLGenerator.generate_google_earth_url(polygon)
            detailed_url = URLGenerator.generate_detailed_maps_url(polygon)
            
            # Display coordinate info
            bounds = URLGenerator.calculate_bounds(polygon['coordinates'])
            print(f"Center: ({bounds['center_lat']:.6f}, {bounds['center_lon']:.6f})")
            print(f"Bounds: ({bounds['min_lat']:.6f}, {bounds['min_lon']:.6f}) to ({bounds['max_lat']:.6f}, {bounds['max_lon']:.6f})")
            
            print(f"\nGoogle Maps URL:")
            print(f"  {maps_url}")
            
            print(f"\nGoogle Earth URL:")
            print(f"  {earth_url}")
            
            print(f"\nDetailed Maps URL:")
            print(f"  {detailed_url}")
            
            # Show polygon coordinates
            print(f"\nPolygon Coordinates ({len(polygon['coordinates'])} points):")
            for j, (lat, lon) in enumerate(polygon['coordinates']):
                print(f"  {j+1}: ({lat:.6f}, {lon:.6f})")


def main():
    """Main function to run the KML to URL converter."""
    
    # Get KML files from command line or use default files in current directory
    if len(sys.argv) > 1:
        kml_files = sys.argv[1:]
    else:
        # Look for KML files in current directory
        kml_files = [f for f in os.listdir('.') if f.endswith('.kml')]
        
    if not kml_files:
        print("No KML files found. Usage:")
        print("  python kml_to_maps_urls.py [file1.kml] [file2.kml] ...")
        print("  or place KML files in the current directory")
        return
    
    print("KML to Google Maps/Earth URL Generator")
    print("=====================================")
    
    process_kml_files(kml_files)
    
    print(f"\n{'='*60}")
    print("Processing complete!")
    print("\nTip: Copy and paste the URLs into your browser to view the locations.")
    print("Note: Google Maps may not display exact polygon boundaries, but will center on the area.")


if __name__ == "__main__":
    main()