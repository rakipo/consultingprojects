import ee

def detect_property_changes(property_coords, start_date, end_date):
    # Define area of interest around property
    aoi = ee.Geometry.Point(property_coords).buffer(100)
    
    # Get before and after imagery
    before = ee.ImageCollection('LANDSAT/LC08/C01/T1_SR') \
        .filterDate(start_date, start_date + 30) \
        .filterBounds(aoi) \
        .median()
    
    after = ee.ImageCollection('LANDSAT/LC08/C01/T1_SR') \
        .filterDate(end_date, end_date + 30) \
        .filterBounds(aoi) \
        .median()
    
    # Calculate difference
    difference = after.subtract(before)
    
    return difference

if __name__ == "__main__":
    # Initialize Earth Engine (you may need to specify a project)
    try:
        ee.Initialize(project='n8n-arxiv')
    except Exception as e:
        print(f"Error initializing Earth Engine: {e}")
        print("You may need to specify a Google Cloud project.")
        print("Visit https://console.cloud.google.com to create a project if needed.")
        print("Then run: ee.Initialize(project='your-project-id')")
        exit(1)
    
    # Example usage - coordinates for a sample location (longitude, latitude)
    coords = [-122.4194, 37.7749]  # San Francisco coordinates
    start = '2020-01-01'
    end = '2021-01-01'
    
    print("Detecting property changes...")
    result = detect_property_changes(coords, start, end)
    print(f"Change detection completed for coordinates {coords}")
    print(f"Result type: {type(result)}")
    print("To visualize results, you'll need to export or display the image using Earth Engine's visualization tools.")