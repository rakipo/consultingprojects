# Configurable Satellite Analysis System

This system provides a flexible, configuration-driven approach to satellite imagery analysis using Sentinel Hub API. All parameters are externalized to a YAML configuration file, making it easy to customize without modifying code.

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   conda activate geopulse_env
   pip install pyyaml
   ```

2. **Configure parameters:**
   Edit `config.yaml` to set your desired parameters

3. **Run analysis:**
   ```bash
   python multi_location_output_configurable.py
   ```

## 📁 File Structure

```
divide_and_analyze/
├── config.yaml                           # Main configuration file
├── config_manager.py                     # Configuration management class
├── multi_location_output_configurable.py # Main analysis script
├── README_configurable.md                # This file
└── output/                               # Analysis results
    └── YYYYMMDD_HHMMSS/                  # Timestamped output directories
```

## ⚙️ Configuration Options

### Analysis Parameters

```yaml
analysis:
  square_size_acres: 1.0    # Size of each analysis square (0.1, 0.25, 1.0, etc.)
  region_type: "mixed"      # "urban", "rural", or "mixed"
  quality:
    min_quality_score: 0.7
    min_temporal_consistency: 0.8
```

### Sentinel Hub Settings

```yaml
sentinel_hub:
  data_source:
    type: "sentinel-2-l2a"  # "sentinel-2-l1c" or "sentinel-2-l2a"
  image_settings:
    width: 256
    height: 256
    timeout_seconds: 60
  data_filter:
    max_cloud_coverage: 15  # Percentage
    mosaicking_order: "leastCC"
```

### Custom Date Periods

```yaml
custom_periods:
  enabled: true
  periods:
    - start_date: "2023-08-09"
      end_date: "2023-08-16"
    - start_date: "2025-08-02"
      end_date: "2025-08-09"
```

### Thresholds

```yaml
thresholds:
  urban:
    ndvi: 0.3
    ndbi: 0.1
    ndwi: -0.1
  rural:
    ndvi: 0.5
    ndbi: -0.1
    ndwi: 0.1
  mixed:
    ndvi: 0.4
    ndbi: 0.0
    ndwi: 0.0
```

## 🎯 Key Features

### 1. Configurable Square Sizes
- **0.1 acres**: High-resolution analysis for small areas
- **0.25 acres**: Standard detailed analysis
- **1.0 acres**: Balanced resolution and performance
- **2.0+ acres**: Large area analysis

### 2. Adaptive Thresholds
- **Urban**: Lower NDVI thresholds, higher NDBI thresholds
- **Rural**: Higher NDVI thresholds, lower NDBI thresholds
- **Mixed**: Balanced thresholds for diverse areas

### 3. Quality Control
- Minimum quality score requirements
- Temporal consistency checks
- Standard deviation limits

### 4. Flexible Date Periods
- Custom date ranges for comparative analysis
- Default periods for recent analysis
- Multi-temporal aggregation

## 📊 Output Files

Each analysis creates a timestamped directory containing:

- `optimized_satellite_analysis_results.csv` - Detailed results with inferences
- `enhanced_significant_indices_squares.kml` - Combined KML visualization
- `NDVI_Vegetation_Analysis.kml` - Vegetation-specific KML
- `NDBI_BuiltUp_Analysis.kml` - Built-up area KML
- `NDWI_Water_Analysis.kml` - Water/moisture KML
- `analysis_summary.txt` - Summary report

## 🔧 Configuration Examples

### Example 1: High-Resolution Urban Analysis
```yaml
analysis:
  square_size_acres: 0.1
  region_type: "urban"

sentinel_hub:
  image_settings:
    width: 512
    height: 512
  data_filter:
    max_cloud_coverage: 10
```

### Example 2: Large Rural Area Analysis
```yaml
analysis:
  square_size_acres: 2.0
  region_type: "rural"

sentinel_hub:
  image_settings:
    width: 128
    height: 128
  data_filter:
    max_cloud_coverage: 20
```

### Example 3: Historical Comparison
```yaml
custom_periods:
  enabled: true
  periods:
    - start_date: "2020-01-01"
      end_date: "2020-01-31"
    - start_date: "2023-01-01"
      end_date: "2023-01-31"
```

## 🛠️ Advanced Configuration

### Inference Thresholds
Customize the interpretation of index values:

```yaml
ndvi_inference:
  high_vegetation: 0.6
  moderate_vegetation: 0.4
  low_vegetation: 0.2
  very_low_vegetation: 0.0
```

### KML Styling
Customize visualization colors:

```yaml
output:
  kml_styles:
    ndvi:
      color: "ff0000ff"  # Blue
      width: "3"
    ndbi:
      color: "ff0000ff"  # Red
      width: "3"
    ndwi:
      color: "ff00ffff"  # Yellow
      width: "3"
```

## 🔍 Understanding Results

### NDVI (Normalized Difference Vegetation Index)
- **High values (>0.6)**: Dense vegetation, forests
- **Moderate values (0.4-0.6)**: Grasslands, crops
- **Low values (0.2-0.4)**: Sparse vegetation
- **Very low values (<0.2)**: Urban areas, water

### NDBI (Normalized Difference Built-up Index)
- **High values (>0.2)**: Dense urban development
- **Moderate values (0.1-0.2)**: Suburban areas
- **Low values (0.0-0.1)**: Rural settlements
- **Negative values (<0.0)**: Natural areas

### NDWI (Normalized Difference Water Index)
- **High values (>0.3)**: Water bodies, wetlands
- **Moderate values (0.1-0.3)**: Moist soil, irrigated areas
- **Low values (0.0-0.1)**: Slightly moist areas
- **Negative values (<0.0)**: Dry areas

## 🚨 Troubleshooting

### Common Issues

1. **Authentication Error (401)**
   - Verify API credentials in `config.yaml`
   - Check Sentinel Hub quota limits

2. **No Data Available**
   - Increase `max_cloud_coverage` in configuration
   - Extend date ranges
   - Check area coordinates

3. **Poor Quality Results**
   - Decrease square size for higher resolution
   - Adjust quality thresholds
   - Use L2A data source for better accuracy

### Performance Optimization

- **Large areas**: Use larger square sizes (1-2 acres)
- **High resolution**: Use smaller square sizes (0.1-0.25 acres)
- **Fast processing**: Reduce image dimensions (128x128)
- **High accuracy**: Increase image dimensions (512x512)

## 📈 Best Practices

1. **Start with default settings** and adjust based on results
2. **Use appropriate region type** for your analysis area
3. **Consider seasonal variations** when setting date periods
4. **Validate results** with ground truth data when possible
5. **Monitor API usage** to stay within quota limits

## 🔄 Migration from Original Script

The configurable system maintains all features from the original script:

- ✅ Multi-temporal analysis
- ✅ Adaptive thresholds
- ✅ Quality scoring
- ✅ KML visualization
- ✅ Inference generation
- ✅ Corner coordinates
- ✅ Separate index files

Plus new features:
- ✅ External configuration
- ✅ Configurable square sizes
- ✅ Flexible date periods
- ✅ Enhanced validation
- ✅ Better error handling

## 📞 Support

For issues or questions:
1. Check the configuration validation output
2. Review the analysis summary file
3. Verify API credentials and quotas
4. Test with different square sizes
