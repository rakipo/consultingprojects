#!/usr/bin/env python3
"""
GeoJSON to KML Converter

This program converts GeoJSON files to KML (Keyhole Markup Language) format.
It handles various geometry types including polygons, points, and linestrings.

Usage:
    python geojson_to_kml.py input.geojson output.kml
"""

import json
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, List, Any, Union


class GeoJSONToKMLConverter:
    """Converter class for GeoJSON to KML transformation."""
    
    def __init__(self):
        self.kml_namespace = "http://www.opengis.net/kml/2.2"
        self.gx_namespace = "http://www.google.com/kml/ext/2.2"
    
    def create_kml_document(self, geojson_data: Dict[str, Any]) -> ET.Element:
        """Create the root KML document element."""
        kml = ET.Element("kml")
        kml.set("xmlns", self.kml_namespace)
        kml.set("xmlns:gx", self.gx_namespace)
        
        document = ET.SubElement(kml, "Document")
        
        # Add document metadata
        name = ET.SubElement(document, "name")
        name.text = "GeoJSON to KML Conversion"
        
        description = ET.SubElement(document, "description")
        description.text = f"Converted from GeoJSON with {len(geojson_data.get('features', []))} features"
        
        # Add default styles
        self._add_default_styles(document)
        
        return kml
    
    def _add_default_styles(self, document: ET.Element):
        """Add default styles for different geometry types."""
        # Style for polygons
        polygon_style = ET.SubElement(document, "Style")
        polygon_style.set("id", "polygonStyle")
        
        poly_style = ET.SubElement(polygon_style, "PolyStyle")
        ET.SubElement(poly_style, "color").text = "7f00ff00"  # Semi-transparent green
        ET.SubElement(poly_style, "fill").text = "1"
        ET.SubElement(poly_style, "outline").text = "1"
        
        line_style = ET.SubElement(polygon_style, "LineStyle")
        ET.SubElement(line_style, "color").text = "ff0000ff"  # Blue outline
        ET.SubElement(line_style, "width").text = "2"
        
        # Style for points
        point_style = ET.SubElement(document, "Style")
        point_style.set("id", "pointStyle")
        
        icon_style = ET.SubElement(point_style, "IconStyle")
        ET.SubElement(icon_style, "color").text = "ff0000ff"  # Blue
        ET.SubElement(icon_style, "scale").text = "1.2"
        
        icon = ET.SubElement(icon_style, "Icon")
        ET.SubElement(icon, "href").text = "http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png"
        
        # Style for linestrings
        line_style_def = ET.SubElement(document, "Style")
        line_style_def.set("id", "lineStyle")
        
        line_style_elem = ET.SubElement(line_style_def, "LineStyle")
        ET.SubElement(line_style_elem, "color").text = "ff00ff00"  # Green
        ET.SubElement(line_style_elem, "width").text = "3"
    
    def convert_coordinates(self, coordinates: List[List[float]]) -> str:
        """Convert coordinate array to KML coordinate string."""
        coord_strings = []
        for coord in coordinates:
            if len(coord) >= 2:
                # KML format: longitude,latitude,altitude (altitude optional)
                lon, lat = coord[0], coord[1]
                altitude = coord[2] if len(coord) > 2 else 0
                coord_strings.append(f"{lon},{lat},{altitude}")
        return " ".join(coord_strings)
    
    def create_polygon_placemark(self, feature: Dict[str, Any]) -> ET.Element:
        """Create a KML placemark for a polygon feature."""
        placemark = ET.Element("Placemark")
        
        # Add name
        name = ET.SubElement(placemark, "name")
        name.text = f"Plot {feature['properties'].get('plot_number', 'Unknown')}"
        
        # Add description with properties
        description = ET.SubElement(placemark, "description")
        props = feature['properties']
        desc_text = f"""
        <![CDATA[
        <h3>Plot Information</h3>
        <table border="1">
            <tr><td><b>Plot Number:</b></td><td>{props.get('plot_number', 'N/A')}</td></tr>
            <tr><td><b>Village ID:</b></td><td>{props.get('village_id', 'N/A')}</td></tr>
            <tr><td><b>Extent (Acres):</b></td><td>{props.get('extent_acres', 'N/A')}</td></tr>
            <tr><td><b>Boundary Points:</b></td><td>{props.get('point_count', 'N/A')}</td></tr>
        </table>
        ]]>
        """
        description.text = desc_text
        
        # Add style reference
        style_url = ET.SubElement(placemark, "styleUrl")
        style_url.text = "#polygonStyle"
        
        # Add polygon geometry
        polygon = ET.SubElement(placemark, "Polygon")
        
        # Add tessellate for proper rendering on Earth's surface
        tessellate = ET.SubElement(polygon, "tessellate")
        tessellate.text = "1"
        
        # Add altitude mode
        altitude_mode = ET.SubElement(polygon, "altitudeMode")
        altitude_mode.text = "clampToGround"
        
        # Add outer boundary
        outer_boundary = ET.SubElement(polygon, "outerBoundaryIs")
        linear_ring = ET.SubElement(outer_boundary, "LinearRing")
        
        coords = ET.SubElement(linear_ring, "coordinates")
        coords.text = self.convert_coordinates(feature['geometry']['coordinates'][0])
        
        return placemark
    
    def create_point_placemark(self, feature: Dict[str, Any]) -> ET.Element:
        """Create a KML placemark for a point feature."""
        placemark = ET.Element("Placemark")
        
        # Add name
        name = ET.SubElement(placemark, "name")
        name.text = f"Point {feature['properties'].get('plot_number', 'Unknown')}"
        
        # Add description
        description = ET.SubElement(placemark, "description")
        props = feature['properties']
        desc_text = f"Plot: {props.get('plot_number', 'N/A')}, Village: {props.get('village_id', 'N/A')}"
        description.text = desc_text
        
        # Add style reference
        style_url = ET.SubElement(placemark, "styleUrl")
        style_url.text = "#pointStyle"
        
        # Add point geometry
        point = ET.SubElement(placemark, "Point")
        
        coords = ET.SubElement(point, "coordinates")
        coord = feature['geometry']['coordinates']
        coords.text = f"{coord[0]},{coord[1]},0"
        
        return placemark
    
    def create_linestring_placemark(self, feature: Dict[str, Any]) -> ET.Element:
        """Create a KML placemark for a linestring feature."""
        placemark = ET.Element("Placemark")
        
        # Add name
        name = ET.SubElement(placemark, "name")
        name.text = f"Line {feature['properties'].get('plot_number', 'Unknown')}"
        
        # Add description
        description = ET.SubElement(placemark, "description")
        props = feature['properties']
        desc_text = f"Plot: {props.get('plot_number', 'N/A')}, Village: {props.get('village_id', 'N/A')}"
        description.text = desc_text
        
        # Add style reference
        style_url = ET.SubElement(placemark, "styleUrl")
        style_url.text = "#lineStyle"
        
        # Add linestring geometry
        linestring = ET.SubElement(placemark, "LineString")
        
        # Add tessellate
        tessellate = ET.SubElement(linestring, "tessellate")
        tessellate.text = "1"
        
        # Add altitude mode
        altitude_mode = ET.SubElement(linestring, "altitudeMode")
        altitude_mode.text = "clampToGround"
        
        coords = ET.SubElement(linestring, "coordinates")
        coords.text = self.convert_coordinates(feature['geometry']['coordinates'])
        
        return placemark
    
    def convert_feature(self, feature: Dict[str, Any]) -> ET.Element:
        """Convert a single GeoJSON feature to KML placemark."""
        geometry_type = feature['geometry']['type']
        
        if geometry_type == 'Polygon':
            return self.create_polygon_placemark(feature)
        elif geometry_type == 'Point':
            return self.create_point_placemark(feature)
        elif geometry_type == 'LineString':
            return self.create_linestring_placemark(feature)
        else:
            print(f"Warning: Unsupported geometry type: {geometry_type}")
            return None
    
    def convert(self, geojson_data: Dict[str, Any]) -> ET.Element:
        """Convert GeoJSON data to KML format."""
        kml = self.create_kml_document(geojson_data)
        document = kml.find("Document")
        
        features = geojson_data.get('features', [])
        print(f"Converting {len(features)} features...")
        
        for i, feature in enumerate(features):
            placemark = self.convert_feature(feature)
            if placemark is not None:
                document.append(placemark)
                print(f"  Converted feature {i+1}: {feature['geometry']['type']}")
            else:
                print(f"  Skipped feature {i+1}: unsupported geometry type")
        
        return kml
    
    def save_kml(self, kml_root: ET.Element, output_file: str):
        """Save KML element tree to file with proper formatting."""
        # Convert to string
        rough_string = ET.tostring(kml_root, encoding='unicode')
        
        # Parse and pretty print
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")
        
        # Remove empty lines and write to file
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))


def main():
    """Main function to handle command line arguments and execute conversion."""
    if len(sys.argv) != 3:
        print("Usage: python geojson_to_kml.py input.geojson output.kml")
        print("\nExample:")
        print("python geojson_to_kml.py output.geojson output.kml")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        print(f"Reading GeoJSON file: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        
        if geojson_data.get('type') != 'FeatureCollection':
            print("Error: Input file is not a valid GeoJSON FeatureCollection")
            sys.exit(1)
        
        print("Converting to KML...")
        converter = GeoJSONToKMLConverter()
        kml_root = converter.convert(geojson_data)
        
        print(f"Writing KML to: {output_file}")
        converter.save_kml(kml_root, output_file)
        
        print("Successfully converted GeoJSON to KML!")
        
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
