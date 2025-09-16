"""
SENTINEL HUB IMAGE TYPES EXPLAINED

This shows the different types of images you can get from Sentinel Hub API
and what they actually look like.
"""

# 1. TRUE COLOR - REAL SATELLITE PHOTOS
TRUE_COLOR_SCRIPT = """
//VERSION=3
function setup() {
    return {
        input: ["B02", "B03", "B04"],    // Blue, Green, Red visible bands
        output: { bands: 3 }
    };
}

function evaluatePixel(sample) {
    // Natural colors as human eyes would see
    return [
        sample.B04 * 2.5,  // Red
        sample.B03 * 2.5,  // Green  
        sample.B02 * 2.5   // Blue
    ];
}

// OUTPUT: Real photograph-like image
// - Buildings look like buildings
// - Water is blue
// - Vegetation is green
// - Roads are gray/black
// - Soil is brown
"""

# 2. FALSE COLOR INFRARED - ENHANCED VEGETATION
FALSE_COLOR_SCRIPT = """
//VERSION=3
function setup() {
    return {
        input: ["B03", "B04", "B08"],    // Green, Red, Near-Infrared
        output: { bands: 3 }
    };
}

function evaluatePixel(sample) {
    // Infrared visualization
    return [
        sample.B08 * 2.5,  // NIR -> Red channel (vegetation = bright red)
        sample.B04 * 2.5,  // Red -> Green channel
        sample.B03 * 2.5   // Green -> Blue channel
    ];
}

// OUTPUT: Artistic/analytical image
// - Healthy vegetation = bright red/pink
// - Water = dark blue/black
// - Urban areas = blue/gray
// - Bare soil = brown/gray
"""

# 3. NDVI - VEGETATION HEALTH HEATMAP
NDVI_SCRIPT = """
//VERSION=3
function setup() {
    return {
        input: ["B04", "B08"],    // Red and Near-Infrared
        output: { bands: 1 }
    };
}

function evaluatePixel(sample) {
    // Calculate vegetation index
    let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
    
    // Color mapping for visualization
    if (ndvi < -0.2) return [0.05, 0.05, 0.4];      // Water = blue
    if (ndvi < 0.1) return [0.75, 0.75, 0.75];      // Bare soil = gray  
    if (ndvi < 0.3) return [0.8, 0.8, 0.1];         // Sparse vegetation = yellow
    if (ndvi < 0.6) return [0.1, 0.8, 0.1];         // Moderate vegetation = green
    return [0.05, 0.4, 0.05];                        // Dense vegetation = dark green
}

// OUTPUT: Color-coded heatmap
// - NOT a real photograph
// - Shows vegetation health levels
// - Blue = water
// - Gray = no vegetation  
// - Yellow to green = increasing vegetation health
"""

# 4. ENHANCED TRUE COLOR - IMPROVED REAL PHOTOS
ENHANCED_TRUE_COLOR_SCRIPT = """
//VERSION=3
function setup() {
    return {
        input: ["B02", "B03", "B04", "SCL"],
        output: { bands: 3 }
    };
}

function evaluatePixel(sample) {
    // Enhanced true color with cloud masking
    let gain = 2.5;
    
    // Handle clouds differently
    if (sample.SCL == 3 || sample.SCL == 8 || sample.SCL == 9) {
        // Clouds - reduce saturation
        gain = 2.0;
    }
    
    // Natural but enhanced colors
    return [
        Math.min(1, sample.B04 * gain),  // Red
        Math.min(1, sample.B03 * gain),  // Green
        Math.min(1, sample.B02 * gain)   // Blue
    ];
}

// OUTPUT: Real satellite photo with enhancements
// - Still looks natural
// - Better contrast and brightness
// - Cloud handling
// - What you probably want for most use cases
"""

# Example usage showing different image types
import requests
from PIL import Image
import io

class SentinelImageTypes:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://services.sentinel-hub.com"
        self.token = None
        self.authenticate()
    
    def authenticate(self):
        """Get OAuth2 token"""
        auth_url = f"{self.base_url}/oauth/token"
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        response = requests.post(auth_url, data=auth_data)
        if response.status_code == 200:
            self.token = response.json()['access_token']
        else:
            raise Exception(f"Authentication failed: {response.text}")
    
    def get_image_by_type(self, lat, lon, date, image_type="true_color", 
                         bbox_size=0.01, width=1024, height=1024):
        """
        Get different types of satellite images
        
        Args:
            lat, lon: Coordinates
            date: Date in YYYY-MM-DD format
            image_type: 'true_color', 'false_color', 'ndvi', 'enhanced_true_color'
        """
        
        # Choose evalscript based on type
        scripts = {
            'true_color': TRUE_COLOR_SCRIPT,
            'false_color': FALSE_COLOR_SCRIPT,
            'ndvi': NDVI_SCRIPT,
            'enhanced_true_color': ENHANCED_TRUE_COLOR_SCRIPT
        }
        
        evalscript = scripts.get(image_type, TRUE_COLOR_SCRIPT)
        
        bbox = [
            lon - bbox_size/2, lat - bbox_size/2,
            lon + bbox_size/2, lat + bbox_size/2
        ]
        
        payload = {
            "input": {
                "bounds": {
                    "bbox": bbox,
                    "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}
                },
                "data": [{
                    "type": "sentinel-2-l2a",
                    "dataFilter": {
                        "timeRange": {
                            "from": f"{date}T00:00:00Z",
                            "to": f"{date}T23:59:59Z"
                        }
                    }
                }]
            },
            "output": {
                "width": width,
                "height": height,
                "responses": [{
                    "identifier": "default",
                    "format": {"type": "image/png"}
                }]
            },
            "evalscript": evalscript
        }
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(f"{self.base_url}/api/v1/process", 
                               headers=headers, json=payload)
        
        if response.status_code == 200:
            image = Image.open(io.BytesIO(response.content))
            return image, image_type
        else:
            print(f"Error getting {image_type}: {response.text}")
            return None, image_type

def compare_image_types():
    """Example showing different image types for same location"""
    
    # Your coordinates  
    lat, lon = 14.382015, 79.523023
    date = "2024-06-15"
    
    print("🛰️ SENTINEL HUB IMAGE TYPES COMPARISON")
    print("="*50)
    
    # Would need valid credentials to run
    """
    sentinel = SentinelImageTypes("YOUR_CLIENT_ID", "YOUR_CLIENT_SECRET")
    
    image_types = [
        ("true_color", "📸 Real Satellite Photo"),
        ("enhanced_true_color", "📸 Enhanced Real Photo"), 
        ("false_color", "🎨 False Color Infrared"),
        ("ndvi", "🌡️ NDVI Vegetation Heatmap")
    ]
    
    for img_type, description in image_types:
        print(f"\nGetting {description}...")
        image, _ = sentinel.get_image_by_type(lat, lon, date, img_type)
        
        if image:
            filename = f"sentinel_{img_type}_{lat}_{lon}.png"
            image.save(filename)
            print(f"✅ Saved: {filename}")
            
            # Describe what you'll see
            if img_type == "true_color":
                print("   👀 Looks like a real photograph from space")
            elif img_type == "false_color":
                print("   👀 Vegetation appears red/pink, not natural colors")
            elif img_type == "ndvi":
                print("   👀 Color-coded heatmap, not a photograph")
    """
    
    print("\n📋 SUMMARY:")
    print("✅ TRUE COLOR = Real satellite photographs")
    print("🎨 FALSE COLOR = Artistic/analytical (vegetation = red)")  
    print("🌡️ NDVI = Heatmap style (vegetation health colors)")
    print("⚠️  Choose 'true_color' or 'enhanced_true_color' for real images!")

if __name__ == "__main__":
    compare_image_types()