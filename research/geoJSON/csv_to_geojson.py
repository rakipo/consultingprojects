#!/usr/bin/env python3
"""
CSV to GeoJSON Converter

This program converts CSV data containing plot boundary points to GeoJSON format.
The CSV should have columns for plot identification (lp_no) and point ordering (POINT_ID),
along with latitude and longitude coordinates.

Usage:
    python csv_to_geojson.py input.csv output.geojson
"""

import csv
import json
import sys
from collections import defaultdict
from typing import Dict, List, Tuple, Any


def read_csv_data(csv_file: str) -> Dict[int, List[Dict[str, Any]]]:
    """
    Read CSV file and group points by plot number (lp_no).
    
    Args:
        csv_file: Path to the CSV file
        
    Returns:
        Dictionary with lp_no as key and list of points as value
    """
    plots = defaultdict(list)
    
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            try:
                lp_no = int(row['lp_no'])
                point_id = int(row['POINT_ID'])
                latitude = float(row['LATITUDE'])
                longitude = float(row['LONGITUDE'])
                
                # Store additional metadata
                point_data = {
                    'point_id': point_id,
                    'latitude': latitude,
                    'longitude': longitude,
                    'easting': float(row.get('EASTING-X', 0)),
                    'northing': float(row.get('NORTHING-Y', 0)),
                    'village_id': row.get('Village_id', ''),
                    'extent_ac': float(row.get('extent_ac', 0))
                }
                
                plots[lp_no].append(point_data)
                
            except (ValueError, KeyError) as e:
                print(f"Warning: Skipping invalid row: {row}. Error: {e}")
                continue
    
    # Sort points by POINT_ID to ensure proper polygon ordering
    for lp_no in plots:
        plots[lp_no].sort(key=lambda x: x['point_id'])
    
    return dict(plots)


def create_polygon_coordinates(points: List[Dict[str, Any]]) -> List[List[float]]:
    """
    Create polygon coordinates from a list of points.
    
    Args:
        points: List of point dictionaries with latitude and longitude
        
    Returns:
        List of coordinate pairs [longitude, latitude] for GeoJSON polygon
    """
    coordinates = []
    
    for point in points:
        # GeoJSON uses [longitude, latitude] format
        coordinates.append([point['longitude'], point['latitude']])
    
    # Close the polygon by adding the first point at the end
    if coordinates and coordinates[0] != coordinates[-1]:
        coordinates.append(coordinates[0])
    
    return coordinates


def create_geojson_feature(plot_data: List[Dict[str, Any]], lp_no: int) -> Dict[str, Any]:
    """
    Create a GeoJSON feature for a single plot.
    
    Args:
        plot_data: List of points for the plot
        lp_no: Plot number
        
    Returns:
        GeoJSON feature object
    """
    if len(plot_data) < 3:
        print(f"Warning: Plot {lp_no} has less than 3 points, skipping...")
        return None
    
    # Create polygon coordinates
    coordinates = create_polygon_coordinates(plot_data)
    
    # Create properties with metadata from the first point
    properties = {
        'plot_number': lp_no,
        'village_id': plot_data[0]['village_id'],
        'extent_acres': plot_data[0]['extent_ac'],
        'point_count': len(plot_data)
    }
    
    feature = {
        "type": "Feature",
        "properties": properties,
        "geometry": {
            "type": "Polygon",
            "coordinates": [coordinates]  # GeoJSON polygon requires array of linear rings
        }
    }
    
    return feature


def create_geojson(plots: Dict[int, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Create complete GeoJSON structure from plot data.
    
    Args:
        plots: Dictionary of plots with their boundary points
        
    Returns:
        Complete GeoJSON object
    """
    features = []
    
    for lp_no, plot_data in plots.items():
        feature = create_geojson_feature(plot_data, lp_no)
        if feature:
            features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features,
        "crs": {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
            }
        }
    }
    
    return geojson


def validate_polygon(points: List[Dict[str, Any]]) -> bool:
    """
    Validate that points form a valid polygon.
    
    Args:
        points: List of point dictionaries
        
    Returns:
        True if valid polygon, False otherwise
    """
    if len(points) < 3:
        return False
    
    # Check for duplicate consecutive points
    for i in range(len(points) - 1):
        if (points[i]['latitude'] == points[i+1]['latitude'] and 
            points[i]['longitude'] == points[i+1]['longitude']):
            return False
    
    return True


def main():
    """Main function to handle command line arguments and execute conversion."""
    if len(sys.argv) != 3:
        print("Usage: python csv_to_geojson.py input.csv output.geojson")
        print("\nExample:")
        print("python csv_to_geojson.py site1.csv output.geojson")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        print(f"Reading CSV file: {input_file}")
        plots = read_csv_data(input_file)
        
        if not plots:
            print("Error: No valid plot data found in CSV file")
            sys.exit(1)
        
        print(f"Found {len(plots)} plots:")
        for lp_no, points in plots.items():
            print(f"  Plot {lp_no}: {len(points)} boundary points")
        
        print("Creating GeoJSON...")
        geojson = create_geojson(plots)
        
        print(f"Writing GeoJSON to: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(geojson, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully created GeoJSON with {len(geojson['features'])} features")
        
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
