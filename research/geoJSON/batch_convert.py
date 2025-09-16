#!/usr/bin/env python3
"""
Batch Converter: CSV -> GeoJSON -> KML

This script performs a complete conversion pipeline:
1. Convert CSV to GeoJSON
2. Convert GeoJSON to KML

Usage:
    python batch_convert.py input.csv output.kml
"""

import subprocess
import sys
import os
import tempfile


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"Command output: {e.stdout}")
        print(f"Command error: {e.stderr}")
        return False


def main():
    """Main function for batch conversion."""
    if len(sys.argv) != 3:
        print("Usage: python batch_convert.py input.csv output.kml")
        print("\nExample:")
        print("python batch_convert.py site1.csv final_output.kml")
        sys.exit(1)
    
    input_csv = sys.argv[1]
    output_kml = sys.argv[2]
    
    # Create temporary GeoJSON file
    temp_geojson = tempfile.mktemp(suffix='.geojson')
    
    try:
        # Step 1: CSV to GeoJSON
        csv_to_geojson_cmd = f"python csv_to_geojson.py {input_csv} {temp_geojson}"
        if not run_command(csv_to_geojson_cmd, "Converting CSV to GeoJSON"):
            sys.exit(1)
        
        # Step 2: GeoJSON to KML
        geojson_to_kml_cmd = f"python geojson_to_kml.py {temp_geojson} {output_kml}"
        if not run_command(geojson_to_kml_cmd, "Converting GeoJSON to KML"):
            sys.exit(1)
        
        print(f"\n✅ Successfully converted {input_csv} to {output_kml}")
        print(f"📁 Intermediate GeoJSON file: {temp_geojson}")
        
    except Exception as e:
        print(f"Error during batch conversion: {e}")
        sys.exit(1)
    
    finally:
        # Clean up temporary file
        if os.path.exists(temp_geojson):
            os.remove(temp_geojson)
            print(f"🧹 Cleaned up temporary file: {temp_geojson}")


if __name__ == "__main__":
    main()
