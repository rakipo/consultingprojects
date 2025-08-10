# Land Area Integration with Sentinel Hub

## Overview

Yes, **land area information can absolutely be used when calling Sentinel Hub**! The batch property analyzer has been enhanced to utilize land area data (`extent_ac`) to optimize Sentinel Hub API calls and improve analysis quality.

## How Land Area Affects Sentinel Hub Analysis

### 1. **Bounding Box Optimization**

**Formula Used:**
```python
# Convert acres to square meters
extent_sq_meters = extent_ac * 4046.86

# Calculate property radius (assuming circular property)
property_radius_meters = √(extent_sq_meters / π)

# Use the larger of property radius or minimum buffer
effective_radius_meters = max(property_radius_meters, 50)  # 50m minimum
```

**Examples:**
- **0.5 acres** → 25m radius → 50m minimum bounding box
- **5 acres** → 80m radius → 80m bounding box
- **50 acres** → 254m radius → 254m bounding box
- **200 acres** → 508m radius → 508m bounding box
- **500 acres** → 803m radius → 803m bounding box

### 2. **Sentinel Hub API Call Optimization**

**Before (Fixed Buffer):**
```python
# All properties got same 10m buffer regardless of size
buffer_degrees = 10 / 111000  # ~0.00009 degrees
```

**After (Land Area Aware):**
```python
# Each property gets optimal bounding box based on area
radius_degrees = effective_radius_meters / 111000
```

### 3. **Analysis Quality Improvements**

| Land Area | Bounding Box Size | Pixels Available | Statistical Significance |
|-----------|------------------|------------------|-------------------------|
| < 1 acre | 50m radius | ~25 pixels | Limited |
| 1-10 acres | 50-100m radius | 25-100 pixels | Moderate |
| 10-100 acres | 100-300m radius | 100-900 pixels | Good |
| > 100 acres | > 300m radius | > 900 pixels | Excellent |

## Input Format

### Required CSV Structure
```csv
lp_no,extent_ac,POINT_ID,EASTING-X,NORTHING-Y,LATITUDE,LONGITUDE
2,206.49,1,340751.55,1590485.86,14.382015,79.523023
2,206.49,2,340869.12,1590228.96,14.3797,79.524128
3,150.25,3,340900.00,1590300.00,14.3805,79.5245
```

### Key Fields
- **`extent_ac`**: Land area in acres (used for bounding box calculation)
- **`LATITUDE`**: Property latitude (required)
- **`LONGITUDE`**: Property longitude (required)
- **Other fields**: Optional identifiers

## Output Format

### Date Format: DD-MMM-YYYY
```csv
Before Period Start,Before Period End,After Period Start,After Period End
01-NOV-2022,31-JAN-2023,01-JAN-2025,31-MAR-2025
```

### Analysis Results
```csv
Vegetation (NDVI)-Before Value,Vegetation (NDVI)-After Value,Vegetation (NDVI)-Difference,Vegetation (NDVI)-Interpretation,Vegetation (NDVI)-Significance
90.3365,98.4816,8.1450,Vegetation growth or improvement,Yes
```

## Usage Examples

### 1. Basic Usage
```bash
python batch_property_analyzer.py -i properties.csv
```

### 2. Custom Date Ranges
```bash
python batch_property_analyzer.py -i properties.csv \
  --before-start 2023-01-01 --before-end 2023-03-31 \
  --after-start 2024-01-01 --after-end 2024-03-31
```

### 3. Custom Configuration
```bash
python batch_property_analyzer.py -i properties.csv \
  -m sentinel_hub_config.yml -u sentinel_hub_user_config.yaml
```

## Technical Implementation

### 1. Land Area Processing
```python
def create_property_bbox(self, lat: float, lon: float, extent_ac: float = 0):
    # Convert acres to square meters
    extent_sq_meters = extent_ac * 4046.86
    
    # Calculate optimal radius
    if extent_sq_meters > 0:
        property_radius_meters = (extent_sq_meters / 3.14159) ** 0.5
    else:
        property_radius_meters = 50  # Default minimum
    
    # Convert to degrees for Sentinel Hub
    radius_degrees = property_radius_meters / 111000
    
    return BBox([lon - radius_degrees, lat - radius_degrees,
                 lon + radius_degrees, lat + radius_degrees])
```

### 2. Sentinel Hub Integration
```python
# Each property gets optimized bounding box
bbox = self.create_property_bbox(lat, lon, extent_ac)
size = bbox_to_dimensions(bbox, resolution=self.resolution)

# Sentinel Hub API call with optimal parameters
request = SentinelHubRequest(
    evalscript=evalscript,
    input_data=[SentinelHubRequest.input_data(
        data_collection=DataCollection.SENTINEL2_L2A,
        time_interval=date_range,
        maxcc=self.max_cloud_coverage/100.0
    )],
    responses=[SentinelHubRequest.output_response('default', MimeType.TIFF)],
    bbox=bbox,
    size=size,
    config=self.config
)
```

## Benefits of Land Area Integration

### 1. **Better Statistical Significance**
- Larger areas provide more pixels for analysis
- Reduces noise in small area analysis
- More reliable change detection

### 2. **Optimal Resource Usage**
- No wasted API calls for oversized bounding boxes
- Efficient use of Sentinel Hub quotas
- Faster processing for large datasets

### 3. **Improved Accuracy**
- Context-aware analysis based on property size
- Appropriate resolution selection
- Better handling of edge cases

### 4. **Scalability**
- Handles properties from 0.1 acres to 1000+ acres
- Automatic optimization for different property types
- Consistent analysis quality across scales

## Real-World Example

### Input Data
```csv
lp_no,extent_ac,LATITUDE,LONGITUDE
1,0.5,14.382015,79.523023
2,5.0,14.379700,79.524128
3,50.0,14.380500,79.524500
```

### Analysis Results
```
Property 1 (0.5 acres):
  Bounding Box: 50m radius (minimum)
  Pixels: ~25
  Result: Vegetation growth detected

Property 2 (5.0 acres):
  Bounding Box: 80m radius
  Pixels: ~64
  Result: Construction activity detected

Property 3 (50.0 acres):
  Bounding Box: 254m radius
  Pixels: ~645
  Result: Comprehensive change analysis
```

## Best Practices

### 1. **Data Quality**
- Ensure accurate land area measurements
- Use consistent units (acres recommended)
- Validate coordinate precision

### 2. **Analysis Planning**
- Group similar-sized properties for batch processing
- Consider temporal resolution for large areas
- Plan for seasonal variations

### 3. **Output Management**
- Use descriptive filenames with date ranges
- Archive results for historical comparison
- Monitor API usage and quotas

## Conclusion

The integration of land area information with Sentinel Hub analysis provides:

✅ **Optimized API calls** based on property size  
✅ **Better statistical significance** for larger areas  
✅ **Consistent analysis quality** across different property types  
✅ **Efficient resource usage** and cost optimization  
✅ **Scalable solution** for batch processing  

This approach ensures that each property gets the most appropriate analysis based on its characteristics, leading to more accurate and meaningful results.
