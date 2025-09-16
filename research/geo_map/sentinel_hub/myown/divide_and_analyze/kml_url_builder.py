import urllib.parse
import os
import argparse
import sys
from typing import Optional

class KMLURLBuilder:
    """
    A utility class to build Google Earth URLs for KML files
    """
    
    def __init__(self):
        self.google_earth_web_base = "https://earth.google.com/web/search/"
        self.google_earth_desktop_protocol = "googleearth://kml/"
    
    def build_web_url(self, kml_url: str) -> str:
        """
        Build a Google Earth Web URL for a KML file
        
        Args:
            kml_url (str): Direct URL to the KML file
            
        Returns:
            str: Google Earth Web URL
        """
        encoded_url = urllib.parse.quote(kml_url, safe='')
        return f"{self.google_earth_web_base}{encoded_url}"
    
    def build_desktop_url(self, kml_url: str) -> str:
        """
        Build a Google Earth Desktop protocol URL for a KML file
        
        Args:
            kml_url (str): Direct URL to the KML file
            
        Returns:
            str: Google Earth Desktop protocol URL
        """
        return f"{self.google_earth_desktop_protocol}{kml_url}"
    
    def build_advanced_web_url(self, kml_url: str, lat: float = 0, lon: float = 0, 
                              altitude: float = 22251752, heading: float = 0, 
                              tilt: float = 0, roll: float = 0) -> str:
        """
        Build an advanced Google Earth Web URL with camera position
        
        Args:
            kml_url (str): Direct URL to the KML file
            lat (float): Latitude for camera position
            lon (float): Longitude for camera position
            altitude (float): Altitude for camera position
            heading (float): Camera heading
            tilt (float): Camera tilt
            roll (float): Camera roll
            
        Returns:
            str: Advanced Google Earth Web URL
        """
        encoded_kml_url = urllib.parse.quote(kml_url, safe='')
        return (f"https://earth.google.com/web/@{lat},{lon},{altitude}a,"
                f"{altitude}d,35y,{heading}h,{tilt}t,{roll}r/data={encoded_kml_url}")
    
    def validate_url(self, url: str) -> bool:
        """
        Basic URL validation
        
        Args:
            url (str): URL to validate
            
        Returns:
            bool: True if URL appears valid
        """
        return url.startswith(('http://', 'https://')) and url.endswith('.kml')
    
    def process_kml_file(self, kml_url: str, output_type: str = 'web') -> dict:
        """
        Process a KML file URL and generate Google Earth URLs
        
        Args:
            kml_url (str): Direct URL to the KML file
            output_type (str): 'web', 'desktop', or 'both'
            
        Returns:
            dict: Dictionary containing the generated URLs and metadata
        """
        if not self.validate_url(kml_url):
            raise ValueError("Invalid KML URL provided")
        
        result = {
            'original_kml_url': kml_url,
            'filename': os.path.basename(kml_url),
            'urls': {}
        }
        
        if output_type in ['web', 'both']:
            result['urls']['google_earth_web'] = self.build_web_url(kml_url)
            result['urls']['google_earth_web_advanced'] = self.build_advanced_web_url(kml_url)
        
        if output_type in ['desktop', 'both']:
            result['urls']['google_earth_desktop'] = self.build_desktop_url(kml_url)
        
        return result

# Example usage and utility functions
def main():
    """
    Example usage of the KML URL Builder (Interactive mode)
    """
    builder = KMLURLBuilder()
    
    # Example KML URLs
    example_kmls = [
        "https://example.com/sample.kml",
        "https://drive.google.com/uc?id=YOUR_FILE_ID&export=download",
        "https://raw.githubusercontent.com/user/repo/main/data.kml"
    ]
    
    print("KML to Google Earth URL Builder (Interactive Mode)")
    print("=" * 50)
    print("For CLI usage, run with arguments. Use --help for options.")
    print("=" * 50)
    
    for kml_url in example_kmls:
        try:
            result = builder.process_kml_file(kml_url, 'both')
            
            print(f"\nKML File: {result['filename']}")
            print(f"Original URL: {result['original_kml_url']}")
            print("\nGenerated URLs:")
            
            for url_type, url in result['urls'].items():
                print(f"  {url_type}: {url}")
                
        except ValueError as e:
            print(f"Error processing {kml_url}: {e}")
def parse_arguments():
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser(
        description="Convert KML file URLs to Google Earth URLs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://example.com/file.kml
  %(prog)s https://example.com/file.kml --type desktop
  %(prog)s https://example.com/file.kml --type both --output urls.txt
  %(prog)s file1.kml file2.kml --batch
  %(prog)s https://example.com/file.kml --lat 37.7749 --lon -122.4194 --altitude 1000
        """
    )
    
    parser.add_argument(
        'kml_urls',
        nargs='+',
        help='KML file URL(s) to convert'
    )
    
    parser.add_argument(
        '-t', '--type',
        choices=['web', 'desktop', 'both'],
        default='web',
        help='Type of Google Earth URL to generate (default: web)'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output file to save results (optional)'
    )
    
    parser.add_argument(
        '-b', '--batch',
        action='store_true',
        help='Process multiple KML files in batch mode'
    )
    
    parser.add_argument(
        '--lat',
        type=float,
        default=0,
        help='Latitude for camera position (for advanced web URLs)'
    )
    
    parser.add_argument(
        '--lon',
        type=float,
        default=0,
        help='Longitude for camera position (for advanced web URLs)'
    )
    
    parser.add_argument(
        '--altitude',
        type=float,
        default=22251752,
        help='Altitude for camera position (for advanced web URLs)'
    )
    
    parser.add_argument(
        '--heading',
        type=float,
        default=0,
        help='Camera heading (for advanced web URLs)'
    )
    
    parser.add_argument(
        '--tilt',
        type=float,
        default=0,
        help='Camera tilt (for advanced web URLs)'
    )
    
    parser.add_argument(
        '--roll',
        type=float,
        default=0,
        help='Camera roll (for advanced web URLs)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--advanced',
        action='store_true',
        help='Generate advanced web URLs with camera positioning'
    )
    
    return parser.parse_args()

def process_cli_request(args):
    """
    Process the CLI request based on parsed arguments
    """
    builder = KMLURLBuilder()
    results = []
    
    for kml_url in args.kml_urls:
        try:
            if args.verbose:
                print(f"Processing: {kml_url}")
            
            # Validate URL
            if not builder.validate_url(kml_url):
                if args.verbose:
                    print(f"Warning: {kml_url} may not be a valid KML URL")
            
            result = {
                'original_url': kml_url,
                'filename': os.path.basename(kml_url),
                'urls': {}
            }
            
            # Generate URLs based on type
            if args.type in ['web', 'both']:
                if args.advanced:
                    result['urls']['google_earth_web'] = builder.build_advanced_web_url(
                        kml_url, args.lat, args.lon, args.altitude, 
                        args.heading, args.tilt, args.roll
                    )
                else:
                    result['urls']['google_earth_web'] = builder.build_web_url(kml_url)
            
            if args.type in ['desktop', 'both']:
                result['urls']['google_earth_desktop'] = builder.build_desktop_url(kml_url)
            
            results.append(result)
            
        except Exception as e:
            error_result = {
                'original_url': kml_url,
                'error': str(e)
            }
            results.append(error_result)
            if args.verbose:
                print(f"Error processing {kml_url}: {e}")
    
    return results

def format_output(results, verbose=False):
    """
    Format results for display
    """
    output_lines = []
    
    if verbose:
        output_lines.append("KML to Google Earth URL Conversion Results")
        output_lines.append("=" * 60)
    
    for i, result in enumerate(results, 1):
        if 'error' in result:
            if verbose:
                output_lines.append(f"\n{i}. ERROR - {result['original_url']}")
                output_lines.append(f"   Error: {result['error']}")
            else:
                output_lines.append(f"ERROR: {result['original_url']} - {result['error']}")
        else:
            if verbose:
                output_lines.append(f"\n{i}. File: {result.get('filename', 'Unknown')}")
                output_lines.append(f"   Original: {result['original_url']}")
                output_lines.append("   Generated URLs:")
                for url_type, url in result['urls'].items():
                    output_lines.append(f"     {url_type}: {url}")
            else:
                for url_type, url in result['urls'].items():
                    output_lines.append(f"{url}")
    
    return "\n".join(output_lines)

def save_output(content, filename):
    """
    Save output to a file
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Results saved to: {filename}")
    except Exception as e:
        print(f"Error saving to {filename}: {e}")

def cli_main():
    """
    Main CLI function
    """
    try:
        args = parse_arguments()
        
        # Process the request
        results = process_cli_request(args)
        
        # Format output
        output = format_output(results, args.verbose)
        
        # Display results
        print(output)
        
        # Save to file if requested
        if args.output:
            save_output(output, args.output)
        
        # Return exit code based on errors
        errors = [r for r in results if 'error' in r]
        if errors:
            print(f"\nWarning: {len(errors)} error(s) occurred during processing", file=sys.stderr)
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1

def create_google_earth_url(kml_url: str, url_type: str = 'web') -> str:
    """
    Quick function to create a Google Earth URL from a KML URL
    
    Args:
        kml_url (str): Direct URL to the KML file
        url_type (str): 'web' or 'desktop'
        
    Returns:
        str: Google Earth URL
    """
    builder = KMLURLBuilder()
    
    if url_type == 'web':
        return builder.build_web_url(kml_url)
    elif url_type == 'desktop':
        return builder.build_desktop_url(kml_url)
    else:
        raise ValueError("url_type must be 'web' or 'desktop'")

def batch_process_kmls(kml_urls: list) -> dict:
    """
    Process multiple KML URLs at once
    
    Args:
        kml_urls (list): List of KML URLs
        
    Returns:
        dict: Dictionary with results for each URL
    """
    builder = KMLURLBuilder()
    results = {}
    
    for i, kml_url in enumerate(kml_urls):
        try:
            results[f"kml_{i+1}"] = builder.process_kml_file(kml_url, 'both')
        except ValueError as e:
            results[f"kml_{i+1}"] = {"error": str(e), "original_url": kml_url}
    
    return results

if __name__ == "__main__":
    # Check if running from command line with arguments
    if len(sys.argv) > 1:
        # CLI mode
        exit_code = cli_main()
        sys.exit(exit_code)
    else:
        # Interactive/example mode
        main()
        
        print("\n" + "=" * 50)
        print("Quick Example:")
        
        # Quick example
        sample_kml = "https://example.com/my-locations.kml"
        web_url = create_google_earth_url(sample_kml, 'web')
        desktop_url = create_google_earth_url(sample_kml, 'desktop')
        
        print(f"KML URL: {sample_kml}")
        print(f"Google Earth Web: {web_url}")
        print(f"Google Earth Desktop: {desktop_url}")
        
        print(f"\nTo use CLI mode, run:")
        print(f"python {sys.argv[0]} <KML_URL> [options]")
        print(f"Example: python {sys.argv[0]} https://example.com/file.kml --type both")