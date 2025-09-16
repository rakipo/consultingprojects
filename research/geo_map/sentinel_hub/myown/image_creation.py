import requests
import json
from datetime import datetime, timedelta
import base64
from PIL import Image
import io
import os

class SentinelHubImagery:
    def __init__(self, client_id, client_secret):
        """
        Initialize Sentinel Hub API client
        
        Args:
            client_id (str): Your Sentinel Hub client ID
            client_secret (str): Your Sentinel Hub client secret
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://services.sentinel-hub.com"
        self.token = None
        self.authenticate()
    
    def authenticate(self):
        """Get OAuth2 token for API access"""
        auth_url = f"{self.base_url}/oauth/token"
        
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        response = requests.post(auth_url, data=auth_data)
        
        if response.status_code == 200:
            self.token = response.json()['access_token']
            print("Authentication successful!")
        else:
            raise Exception(f"Authentication failed: {response.text}")
    
    def get_land_imagery(self, latitude, longitude, date_from, date_to, 
                        width=512, height=512, bbox_size=0.01, 
                        collection="sentinel-2-l2a", evalscript=None):
        """
        Get satellite imagery for given coordinates and date range
        
        Args:
            latitude (float): Latitude coordinate
            longitude (float): Longitude coordinate  
            date_from (str): Start date in YYYY-MM-DD format
            date_to (str): End date in YYYY-MM-DD format
            width (int): Image width in pixels
            height (int): Image height in pixels
            bbox_size (float): Bounding box size in degrees
            collection (str): Satellite collection to use
            evalscript (str): Custom evalscript for image processing
        
        Returns:
            PIL.Image: Satellite image
        """
        
        # Create bounding box around the coordinates
        bbox = [
            longitude - bbox_size/2,  # min longitude
            latitude - bbox_size/2,   # min latitude  
            longitude + bbox_size/2,  # max longitude
            latitude + bbox_size/2    # max latitude
        ]
        
        # Default evalscript for true color RGB
        if evalscript is None:
            evalscript = """
            //VERSION=3
            function setup() {
                return {
                    input: ["B02", "B03", "B04"],
                    output: { bands: 3 }
                };
            }
            
            function evaluatePixel(sample) {
                return [sample.B04 * 2.5, sample.B03 * 2.5, sample.B02 * 2.5];
            }
            """
        
        # Prepare the request payload
        payload = {
            "input": {
                "bounds": {
                    "bbox": bbox,
                    "properties": {
                        "crs": "http://www.opengis.net/def/crs/EPSG/0/4326"
                    }
                },
                "data": [
                    {
                        "type": collection,
                        "dataFilter": {
                            "timeRange": {
                                "from": f"{date_from}T00:00:00Z",
                                "to": f"{date_to}T23:59:59Z"
                            }
                        }
                    }
                ]
            },
            "output": {
                "width": width,
                "height": height,
                "responses": [
                    {
                        "identifier": "default",
                        "format": {
                            "type": "image/png"
                        }
                    }
                ]
            },
            "evalscript": evalscript
        }
        
        # Make the API request
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        api_url = f"{self.base_url}/api/v1/process"
        
        response = requests.post(api_url, headers=headers, json=payload)
        
        if response.status_code == 200:
            # Convert response to PIL Image
            image = Image.open(io.BytesIO(response.content))
            return image
        else:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
    
    def save_image(self, image, filename):
        """Save PIL Image to file"""
        image.save(filename)
        print(f"Image saved as {filename}")
    
    def get_available_dates(self, latitude, longitude, date_from, date_to, 
                           bbox_size=0.01, collection="sentinel-2-l2a"):
        """
        Get available acquisition dates for the given location and time range
        
        Returns:
            list: Available dates
        """
        bbox = [
            longitude - bbox_size/2,
            latitude - bbox_size/2,
            longitude + bbox_size/2,
            latitude + bbox_size/2
        ]
        
        payload = {
            "bbox": bbox,
            "datetime": f"{date_from}/{date_to}",
            "collections": [collection],
            "limit": 100
        }
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        catalog_url = f"{self.base_url}/api/v1/catalog/search"
        
        response = requests.post(catalog_url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            dates = []
            for feature in data.get('features', []):
                date = feature['properties']['datetime']
                dates.append(date.split('T')[0])  # Extract date part
            return sorted(list(set(dates)))  # Remove duplicates and sort
        else:
            print(f"Failed to get available dates: {response.text}")
            return []

# Example usage
def main():
    # Your Sentinel Hub credentials
    CLIENT_ID = "1ecf7748-4066-4ba1-a3df-3ea2517cf7f6"
    CLIENT_SECRET = "lCK9t1qjeD1mKjcmW9sZ1wqMCFwD1RsQ"

    
    # Initialize the client
    try:
        sentinel = SentinelHubImagery(CLIENT_ID, CLIENT_SECRET)
        
        # Example coordinates (New York Central Park)  
        latitude = 14.442940
        longitude = 80.000281
        
        # Date range
        date_from = "2024-01-01"
        date_to = "2024-08-30"
        
        print(f"Getting imagery for coordinates: {latitude}, {longitude}")
        print(f"Date range: {date_from} to {date_to}")
        
        # Check available dates first
        print("Checking available acquisition dates...")
        available_dates = sentinel.get_available_dates(
            latitude, longitude, date_from, date_to
        )
        print(f"Available dates: {available_dates}")
        
        # Get the imagery
        print("Downloading satellite imagery...")
        image = sentinel.get_land_imagery(
            latitude=latitude,
            longitude=longitude,
            date_from=date_from,
            date_to=date_to,
            width=1024,
            height=1024,
            bbox_size=0.02  # Adjust for area coverage
        )
        
        # Save the image
        filename = f"satellite_image_{latitude}_{longitude}_{date_from}_to_{date_to}.png"
        sentinel.save_image(image, filename)
        
        # Display image if running in Jupyter
        # image.show()
        
    except Exception as e:
        print(f"Error: {e}")

# Additional evalscripts for different visualizations
EVALSCRIPTS = {
    "true_color": """
        //VERSION=3
        function setup() {
            return {
                input: ["B02", "B03", "B04"],
                output: { bands: 3 }
            };
        }
        function evaluatePixel(sample) {
            return [sample.B04 * 2.5, sample.B03 * 2.5, sample.B02 * 2.5];
        }
    """,
    
    "false_color": """
        //VERSION=3
        function setup() {
            return {
                input: ["B03", "B04", "B08"],
                output: { bands: 3 }
            };
        }
        function evaluatePixel(sample) {
            return [sample.B08 * 2.5, sample.B04 * 2.5, sample.B03 * 2.5];
        }
    """,
    
    "ndvi": """
        //VERSION=3
        function setup() {
            return {
                input: ["B04", "B08"],
                output: { bands: 1 }
            };
        }
        function evaluatePixel(sample) {
            let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
            return [ndvi];
        }
    """
}

if __name__ == "__main__":
    main()