# Sentinel Hub Land Monitoring - Output Functionality

## Overview

The Sentinel Hub Land Monitoring system has been enhanced to automatically store all analysis outputs with timestamps and coordinates. This ensures that every analysis is properly documented and can be easily traced back to specific locations and time periods.

## Key Features

### 1. Automatic Output Organization
- All analysis results are automatically saved to timestamped directories
- Directory names include both timestamp and coordinate information
- Example: `20241201_143022_lon78p4567_lat17p3856/`

### 2. Comprehensive Metadata
Each saved result includes:
- **Timestamp**: When the analysis was performed
- **Coordinates**: Exact location of the monitored area
- **Bounding Box**: Geographic boundaries
- **Analysis Type**: Type of analysis performed
- **Date Ranges**: Time periods analyzed
- **Configuration**: Resolution, cloud coverage settings, etc.

### 3. Multiple Output Formats

#### JSON Analysis Results
- Detailed analysis data in structured JSON format
- Includes all change detection metrics (NDVI, NDBI, NDWI)
- Contains interpretations and significance flags
- Filename format: `YYYYMMDD_HHMMSS_lonXpXXXX_latYpYYYY_analysis_type_date_ranges.json`

#### Summary Reports
- Human-readable text summaries of all analyses
- Overview of significant changes detected
- Quick reference for multiple analyses
- Filename format: `YYYYMMDD_HHMMSS_lonXpXXXX_latYpYYYY_analysis_type_summary.txt`

#### Visual Comparison Images
- Side-by-side satellite image comparisons
- High-resolution PNG format
- Automatic timestamp and coordinate naming
- Filename format: `YYYYMMDD_HHMMSS_lonXpXXXX_latYpYYYY_visual_comparison_date_ranges.png`

#### Image Metadata
- JSON files containing metadata for visual comparisons
- Links images to analysis parameters
- Filename format: `image_name_metadata.json`

## File Naming Convention

### Coordinate Format
- Longitude and latitude are formatted to 4 decimal places
- Dots replaced with 'p' (e.g., 78.4567 becomes 78p4567)
- Negative values prefixed with 'n' (e.g., -17.3856 becomes n17p3856)
- Format: `lon{longitude}_lat{latitude}`

### Timestamp Format
- Format: `YYYYMMDD_HHMMSS`
- Example: `20241201_143022` (December 1, 2024, 14:30:22)

### Date Range Format
- Dates in YYYYMMDD format (no separators)
- Before period: `before{start}-{end}`
- After period: `after{start}-{end}`
- Example: `before20230101-20230131_after20240101-20240131`

## Output Directory Structure

```
analysis_results/
└── 20241201_143022_lon78p4567_lat17p3856/
    ├── 20241201_143022_lon78p4567_lat17p3856_change_detection_before20230101-20230131_after20240101-20240131.json
    ├── 20241201_143022_lon78p4567_lat17p3856_visual_comparison_before20230101-20230131_after20240101-20240131.png
    ├── 20241201_143022_lon78p4567_lat17p3856_visual_comparison_before20230101-20230131_after20240101-20240131_metadata.json
    └── 20241201_143022_lon78p4567_lat17p3856_continuous_monitoring_summary.txt
```

## Configuration

### Output Directory
Set the base output directory in `sentinel_hub_config.yml`:

```yaml
output:
  base_directory: "analysis_results"  # Base directory for all analysis outputs
  save_comparison_images: true
  comparison_image_path: "land_comparison.png"
  dpi: 300
```

## Usage Examples

### 1. Basic Change Detection
```python
monitor = SentinelHubLandMonitor(
    main_config_path="sentinel_hub_config.yml",
    user_config_path="sentinel_hub_user_config.yaml"
)
changes = monitor.detect_changes(
    before_date_range=("2023-01-01", "2023-01-31"),
    after_date_range=("2024-01-01", "2024-01-31")
)
# Result automatically saved with timestamp and coordinates
```

### 2. Visual Comparison
```python
monitor.generate_visual_comparison(
    before_date_range=("2023-01-01", "2023-01-31"),
    after_date_range=("2024-01-01", "2024-01-31")
)
# Image and metadata automatically saved
```

### 3. Continuous Monitoring
```python
results = monitor.continuous_monitoring(
    start_date="2023-01-01",
    end_date="2024-12-31"
)
# Summary report and individual significant change results saved
```

### 4. Command Line Usage
```bash
# Basic usage with required config files
python claude_sentinel_hub_image_diff_v11.py --main-config sentinel_hub_config.yml --user-config sentinel_hub_user_config.yaml

# Short form
python claude_sentinel_hub_image_diff_v11.py -m sentinel_hub_config.yml -u sentinel_hub_user_config.yaml

# With specific mode and parameters
python claude_sentinel_hub_image_diff_v11.py -m config.yml -u coordinates.yaml --mode detect --threshold 0.15
```

## Reading Saved Results

### Load Analysis Result
```python
import json

with open('analysis_results/20241201_143022_lon78p4567_lat17p3856/20241201_143022_lon78p4567_lat17p3856_change_detection_before20230101-20230131_after20240101-20240131.json', 'r') as f:
    data = json.load(f)

# Access metadata
metadata = data['metadata']
coordinates = metadata['coordinates']
timestamp = metadata['timestamp']

# Access analysis results
results = data['analysis_result']
change_summary = results['change_summary']
vegetation_change = results['vegetation_change']
```

## Benefits

1. **Traceability**: Every analysis is linked to specific coordinates and timestamps
2. **Organization**: Automatic file organization prevents data loss
3. **Reproducibility**: Complete metadata enables result reproduction
4. **Scalability**: Multiple analyses for different locations are clearly separated
5. **Compliance**: Proper documentation for regulatory or audit requirements

## Testing

Run the test script to verify the output functionality:

```bash
python test_output_functionality.py
```

This will create sample outputs and demonstrate the file naming and organization system.

## File Types Generated

1. **JSON Files**: Structured analysis data with metadata
2. **PNG Files**: High-resolution visual comparisons
3. **TXT Files**: Human-readable summary reports
4. **Metadata Files**: Additional context for visual outputs

All files are automatically named with timestamps and coordinates for easy identification and organization.
