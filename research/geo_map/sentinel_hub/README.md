# Sentinel Hub Land Monitoring System

A Python-based land monitoring system that uses Sentinel Hub to detect changes in vegetation, built-up areas, and water bodies over time.

## Features

- **Change Detection**: Analyze changes in NDVI (vegetation), NDBI (built-up areas), and NDWI (water)
- **Visual Comparison**: Generate side-by-side image comparisons
- **Continuous Monitoring**: Automated monitoring with configurable intervals
- **Email Alerts**: Get notified when significant changes are detected
- **Configuration-Based**: All settings stored in YAML configuration file

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Sign up for Sentinel Hub:
   - Visit https://www.sentinel-hub.com/
   - Create an account and get your credentials

## Configuration

Edit `sentinel_hub_config.yml` to configure your monitoring system:

### Date Configuration

The dates in your configuration represent **time periods for comparison** to detect changes in land use. Here's how to interpret and set them:

#### Before Period (Baseline)
```yaml
before_period:
  start: "2023-01-01"  # Start of baseline period
  end: "2023-01-31"    # End of baseline period
```
- **Purpose**: This is your "baseline" or "reference" period
- **What it represents**: The land condition you want to compare against
- **Duration**: Usually 1-3 months to get a stable baseline

#### After Period (Current/Recent)
```yaml
after_period:
  start: "2024-01-01"  # Start of current period
  end: "2024-01-31"    # End of current period
```
- **Purpose**: This is the "current" or "recent" period to compare
- **What it represents**: The land condition you want to analyze for changes
- **Duration**: Usually 1-3 months, matching the before period

#### Continuous Monitoring
```yaml
continuous_monitoring:
  start: "2023-01-01"  # Overall monitoring start
  end: "2024-12-31"    # Overall monitoring end
```
- **Purpose**: The total time range for continuous monitoring
- **What it represents**: The entire period you want to monitor

#### Best Practices for Date Selection

**1. Avoid Cloudy Periods**
```yaml
# Good: Dry season with less clouds
before_period:
  start: "2023-12-01"  # December (dry season)
  end: "2024-02-28"
after_period:
  start: "2024-12-01"
  end: "2025-02-28"
```

**2. Consider Seasonal Changes**
```yaml
# Compare same seasons to avoid seasonal bias
before_period:
  start: "2023-03-01"  # Spring 2023
  end: "2023-05-31"
after_period:
  start: "2024-03-01"  # Spring 2024
  end: "2024-05-31"
```

**3. Account for Satellite Coverage**
```yaml
# Use periods with good satellite coverage
before_period:
  start: "2023-07-01"  # Summer (good coverage)
  end: "2023-09-30"
after_period:
  start: "2024-07-01"
  end: "2024-09-30"
```

#### Date Format Requirements
- **Format**: `"YYYY-MM-DD"`
- **Examples**: 
  - `"2023-01-15"` ✅
  - `"2024-12-31"` ✅
  - `"2023/01/15"` ❌ (wrong format)
  - `"15-01-2023"` ❌ (wrong format)

#### Recommended Date Settings for Different Use Cases

**Agricultural Monitoring**
```yaml
before_period:
  start: "2023-04-01"  # Planting season
  end: "2023-05-31"
after_period:
  start: "2023-09-01"  # Harvest season
  end: "2023-10-31"
```

**Construction Monitoring**
```yaml
before_period:
  start: "2023-01-01"  # Before construction
  end: "2023-03-31"
after_period:
  start: "2024-01-01"  # After construction
  end: "2024-03-31"
```

**Deforestation Monitoring**
```yaml
before_period:
  start: "2023-06-01"  # Peak vegetation
  end: "2023-08-31"
after_period:
  start: "2024-06-01"  # After clearing
  end: "2024-08-31"
```

### Sentinel Hub Credentials
```yaml
sentinel_hub:
  instance_id: "your-instance-id"
  client_id: "your-client-id"
  client_secret: "your-client-secret"
```

### Land Area Coordinates
Define the area you want to monitor:
```yaml
coordinates:
  - [80.033289, 14.446383]  # West-North
  - [80.033892, 14.446587]  # East-North  
  - [80.033909, 14.446203]  # East-South
  - [80.033298, 14.446032]  # West-South
```

### Email Alerts
Configure email notifications:
```yaml
email:
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  sender_email: "your_email@gmail.com"
  sender_password: "your_app_password"
  recipient_email: "recipient@gmail.com"
  enable_alerts: true
```

### Change Detection Thresholds
Adjust sensitivity for different types of changes:
```yaml
change_detection:
  default_threshold: 0.1
  ndvi_thresholds:
    major_increase: 0.15
    moderate_increase: 0.05
    major_decrease: -0.15
    moderate_decrease: -0.05
```

## Usage

### Command Line Interface (CLI)

The system supports a comprehensive command-line interface for easy operation:

**⚠️ Important**: Both configuration files (`--main-config` and `--user-config`) are now **required** parameters and must be specified when running the program.

#### Quick Start
```bash
# 1. Ensure you have both config files in the current directory
ls sentinel_hub_config.yml sentinel_hub_user_config.yaml

# 2. Run the basic analysis
python claude_sentinel_hub_image_diff_v11.py -m sentinel_hub_config.yml -u sentinel_hub_user_config.yaml

# 3. Check the results in the analysis_results directory
ls analysis_results/
```

#### Basic Usage
```bash
# Required: Specify both configuration files
python claude_sentinel_hub_image_diff_v11.py --main-config sentinel_hub_config.yml --user-config sentinel_hub_user_config.yaml

# Short form
python claude_sentinel_hub_image_diff_v11.py -m sentinel_hub_config.yml -u sentinel_hub_user_config.yaml
```

#### Operation Modes
```bash
# Change detection only
python claude_sentinel_hub_image_diff_v11.py -m sentinel_hub_config.yml -u sentinel_hub_user_config.yaml --mode detect

# Visual comparison only
python claude_sentinel_hub_image_diff_v11.py -m sentinel_hub_config.yml -u sentinel_hub_user_config.yaml --mode visual

# Continuous monitoring setup
python claude_sentinel_hub_image_diff_v11.py -m sentinel_hub_config.yml -u sentinel_hub_user_config.yaml --mode continuous

# All operations (default)
python claude_sentinel_hub_image_diff_v11.py -m sentinel_hub_config.yml -u sentinel_hub_user_config.yaml --mode all
```

#### Custom Parameters
```bash
# Custom date ranges
python claude_sentinel_hub_image_diff_v11.py \
  -m sentinel_hub_config.yml -u sentinel_hub_user_config.yaml \
  --before-start 2023-06-01 --before-end 2023-06-30 \
  --after-start 2024-06-01 --after-end 2024-06-30 \
  --mode detect

# Custom threshold
python claude_sentinel_hub_image_diff_v11.py -m sentinel_hub_config.yml -u sentinel_hub_user_config.yaml --threshold 0.05 --mode detect

# Custom output file
python claude_sentinel_hub_image_diff_v11.py -m sentinel_hub_config.yml -u sentinel_hub_user_config.yaml --output my_comparison.png --mode visual
```

#### Help and Options
```bash
# Display help
python claude_sentinel_hub_image_diff_v11.py --help

# Run examples
python run_monitoring.py
```

### Available CLI Arguments

| Argument | Short | Description | Required |
|----------|-------|-------------|----------|
| `--main-config` | `-m` | Path to main YAML configuration file | **Yes** |
| `--user-config` | `-u` | Path to user YAML configuration file | **Yes** |
| `--mode` | `-M` | Operation mode: detect/visual/continuous/all | `all` |
| `--before-start` | `-bs` | Start date for before period (YYYY-MM-DD) | Config default |
| `--before-end` | `-be` | End date for before period (YYYY-MM-DD) | Config default |
| `--after-start` | `-as` | Start date for after period (YYYY-MM-DD) | Config default |
| `--after-end` | `-ae` | End date for after period (YYYY-MM-DD) | Config default |
| `--threshold` | `-t` | Change detection threshold | Config default |
| `--output` | `-o` | Output file path for comparison images | Config default |

### Programmatic Usage

You can also use the system programmatically:

```python
from claude_sentinel_hub_image_diff_v11 import SentinelHubLandMonitor

# Initialize with config files
monitor = SentinelHubLandMonitor("sentinel_hub_config.yml", "sentinel_hub_user_config.yaml")

# Detect changes between two periods
changes = monitor.detect_changes(
    before_date_range=('2023-01-01', '2023-01-31'),
    after_date_range=('2024-01-01', '2024-01-31')
)

print(f"Change Summary: {changes['change_summary']}")

# Generate side-by-side comparison
monitor.generate_visual_comparison(
    before_date_range=('2023-06-01', '2023-06-30'),
    after_date_range=('2024-06-01', '2024-06-30')
)

# Start automated monitoring
results = monitor.continuous_monitoring(
    start_date='2023-01-01',
    end_date='2024-12-31'
)
```

## Configuration Options

### Image Processing
- `resolution`: Image resolution in meters per pixel (default: 10m)
- `max_cloud_coverage`: Maximum allowed cloud coverage percentage (default: 20%)

### Monitoring Schedule
- `default_interval_days`: Days between monitoring checks (default: 30)
- `period_length_days`: Length of each comparison period (default: 15)

### Output Settings
- `save_comparison_images`: Whether to save comparison images (default: true)
- `comparison_image_path`: Path for saved comparison images
- `dpi`: Image resolution for saved files (default: 300)

## Change Detection Indices

### NDVI (Normalized Difference Vegetation Index)
- Measures vegetation health and density
- Values range from -1 to 1
- Higher values indicate healthier vegetation

### NDBI (Normalized Difference Built-up Index)
- Detects built-up areas and construction
- Values range from -1 to 1
- Higher values indicate more built-up areas

### NDWI (Normalized Difference Water Index)
- Detects water bodies and moisture
- Values range from -1 to 1
- Higher values indicate more water/moisture

## Interpreting Analysis Results

### Understanding the Output
The analysis provides detailed information about changes between your specified time periods:

```json
{
  "before_period": ["2023-06-01", "2023-08-31"],
  "after_period": ["2024-06-01", "2024-08-31"],
  "vegetation_change": {
    "before_ndvi": 0.45,
    "after_ndvi": 0.52,
    "ndvi_difference": 0.07,
    "interpretation": "Moderate vegetation growth"
  },
  "buildup_change": {
    "before_ndbi": 0.12,
    "after_ndbi": 0.18,
    "ndbi_difference": 0.06,
    "interpretation": "Minor built-up area increase"
  },
  "water_change": {
    "before_ndwi": 0.08,
    "after_ndwi": 0.06,
    "ndwi_difference": -0.02,
    "interpretation": "No significant water change"
  },
  "significant_change": true,
  "change_summary": "Vegetation: Moderate vegetation growth; Built-up: Minor built-up area increase"
}
```

### What the Results Mean

#### Vegetation Changes (NDVI)
- **Positive difference** (e.g., +0.07): More vegetation growth, new crops planted, forest regrowth
- **Negative difference** (e.g., -0.05): Vegetation loss, harvesting, deforestation, drought effects
- **No change** (e.g., ±0.02): Stable vegetation conditions

#### Built-up Area Changes (NDBI)
- **Positive difference** (e.g., +0.06): Construction, new buildings, urban development
- **Negative difference** (e.g., -0.03): Demolition, clearing of structures
- **No change** (e.g., ±0.01): Stable built-up conditions

#### Water/Moisture Changes (NDWI)
- **Positive difference** (e.g., +0.10): New water bodies, increased moisture, flooding
- **Negative difference** (e.g., -0.08): Drying up, water body reduction, drought
- **No change** (e.g., ±0.02): Stable water conditions

### Significance Thresholds
- **Default threshold**: 0.1 (10% change)
- **Customizable**: Adjust in configuration based on your needs
- **Significant change**: Any index change above the threshold triggers alerts

### Common Scenarios and Interpretations

#### Agricultural Land
- **NDVI increase**: Crop growth, new planting
- **NDVI decrease**: Harvesting, crop failure, land clearing
- **NDBI increase**: Farm infrastructure development

#### Urban Development
- **NDBI increase**: New construction, urban expansion
- **NDVI decrease**: Vegetation clearing for development
- **NDWI decrease**: Drainage changes, water management

#### Natural Disasters
- **NDVI decrease**: Fire damage, storm damage
- **NDWI increase**: Flooding, water accumulation
- **NDBI decrease**: Infrastructure damage

#### Seasonal Changes
- **NDVI seasonal patterns**: Normal crop cycles, seasonal vegetation
- **NDWI seasonal patterns**: Wet/dry season variations
- **NDBI stability**: Infrastructure remains constant

## Troubleshooting

### Common Issues

1. **Configuration File Not Found**
   - Ensure `sentinel_hub_config.yml` is in the same directory as the script
   - Check file permissions

2. **Authentication Errors**
   - Verify your Sentinel Hub credentials in the config file
   - Ensure your account has the necessary permissions

3. **No Data Available**
   - Check the date range for available satellite imagery
   - Adjust cloud coverage settings
   - Verify coordinates are within Sentinel-2 coverage area

4. **Email Alerts Not Working**
   - For Gmail, use App Passwords instead of regular passwords
   - Check SMTP settings and firewall rules

## Security Notes

- Never commit your `sentinel_hub_config.yml` file with real credentials
- Use environment variables or secure credential storage in production
- Consider using `.gitignore` to exclude the config file from version control

## License

This project is for educational and research purposes. Please ensure compliance with Sentinel Hub's terms of service.
