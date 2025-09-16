# Sentinel-2 Satellite Data Analysis System

A comprehensive Python application for analyzing land use changes using Sentinel-2 satellite data through NDVI, NDBI, and NDWI indices. The system processes CSV input files and exports results to Excel with multiple worksheets and timestamps.

## Features

- **Database Management**: SQLite database with three main tables for satellite data, thresholds, and transactions
- **Rule-Based Analysis**: Configurable rules for detecting vegetation, construction, and flooding changes
- **Multiple Land Types**: Support for 15 different land/soil types with specific threshold rules
- **Delta Analysis**: Calculates changes between baseline and target dates with ±15 day tolerance
- **CSV Input Processing**: Processes CSV files with test data and plot information
- **Excel Export**: Exports all tables to Excel with multiple worksheets and timestamps
- **Comprehensive Reporting**: Detailed analysis reports with statistics and summaries

## Database Schema

### 1. Sentinel_hub_calls_data
- `S_no`: Primary key
- `plot_no`: Plot identifier (1-30)
- `date`: Observation date
- `ndvi`: Normalized Difference Vegetation Index (0-1)
- `ndbi`: Normalized Difference Built-up Index (0-1)
- `ndwi`: Normalized Difference Water Index (0-1)

### 2. Thresholds
- `S_no`: Primary key
- `threshold_short_description`: Land type description
- `vegetation_rule`: Rule for vegetation change detection
- `construction_rule`: Rule for construction change detection
- `flooding_rule`: Rule for flooding change detection

### 3. Transactions
- `S_no`: Primary key
- `test_id`: Unique test identifier
- `plot_no`: Plot identifier
- `baseline_date`: Baseline observation date
- `target_date`: Target observation date
- `ndvi_baseline`, `ndbi_baseline`, `ndwi_baseline`: Baseline values
- `ndvi_target`, `ndbi_target`, `ndwi_target`: Target values
- `delta_ndvi`, `delta_ndbi`, `delta_ndwi`: Calculated deltas
- `vegetation_rule`, `construction_rule`, `flooding_rule`: Applied rules
- `vegetation_inference`, `construction_inference`, `flood_inference`: Analysis results

## Supported Land Types

1. **Red Soil** - Agricultural land with red soil
2. **Black Soil** - Fertile agricultural land
3. **Sand Quarry** - Sand extraction areas
4. **Rock Quarry** - Rock extraction areas
5. **River Bed** - River and water body areas
6. **Agriculture Wet Land** - Irrigated agricultural areas
7. **Agriculture Dry Land** - Rain-fed agricultural areas
8. **Urban Area** - Built-up urban regions
9. **Forest** - Forested areas
10. **Grassland** - Grassland and pasture areas
11. **Wetland** - Wetland areas
12. **Desert** - Desert regions
13. **Mountain** - Mountainous areas
14. **Coastal Area** - Coastal regions
15. **Industrial Area** - Industrial zones

## Rule Format

Rules use delta values (dvi, dbi, dwi) with mathematical expressions:
- `dvi = baseline_ndvi - target_ndvi`
- `dbi = baseline_ndbi - target_ndbi`
- `dwi = baseline_ndwi - target_ndwi`

Example rule: `dvi > 0.2 AND dbi < 0 AND dwi < 0.1`

## Installation

1. **Clone or download the project files**
2. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Quick Start

1. **Initialize the database and populate with sample data:**
   ```bash
   python database_schema.py
   ```

2. **Generate sample CSV input files:**
   ```bash
   python csv_generator.py
   ```

3. **Run the complete demo:**
   ```bash
   python demo_complete.py
   ```

### Step-by-Step Usage

1. **Initialize Database:**
   ```python
   from database_schema import create_database, populate_sentinel_data, populate_thresholds
   
   create_database()
   populate_sentinel_data()
   populate_thresholds()
   ```

2. **Process CSV Input:**
   ```python
   from sentinel_analyzer import SentinelAnalyzer
   
   analyzer = SentinelAnalyzer()
   analyzer.process_csv_input('your_input.csv')
   ```

3. **Export to Excel:**
   ```python
   excel_file = analyzer.export_to_excel()
   print(f"Excel file created: {excel_file}")
   ```

4. **Generate Analysis Report:**
   ```python
   analyzer.print_analysis_report()
   ```

### CSV Input Format

Create a CSV file with the following columns:
```csv
Test_id,plot_no,baseline_date,target_date
1,1,2024-01-15,2024-03-15
2,2,2024-01-20,2024-03-20
...
```

- `Test_id`: Unique identifier for each test
- `plot_no`: Plot number (1-30)
- `baseline_date`: Baseline date (YYYY-MM-DD)
- `target_date`: Target date (YYYY-MM-DD)

The system will automatically find the nearest dates within ±15 days for analysis.

## Excel Export

The system exports all data to Excel with the following worksheets:

1. **Summary** - Overview and statistics
2. **Sentinel_Data** - Raw satellite data
3. **Thresholds** - Land type rules and thresholds
4. **Transactions** - Analysis results and inferences
5. **Analysis_Stats** - Statistical analysis summary

Excel files are automatically named with timestamps: `sentinel_analysis_YYYYMMDD_HHMMSS.xlsx`

## File Structure

```
sentinel_analysis/
├── database_schema.py      # Database creation and population
├── sentinel_analyzer.py    # Main analysis application
├── excel_export.py         # Excel export functionality
├── csv_generator.py        # CSV input file generator
├── demo_complete.py        # Complete demo script
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── sentinel_analysis.db   # SQLite database (created after running)
```

## Sample Data

The system generates realistic sample data for 30 plots over 4 time periods:
- **Plots 1-6**: Agriculture wet land (high NDVI, moderate NDWI)
- **Plots 7-12**: Agriculture dry land (moderate NDVI, low NDWI)
- **Plots 13-18**: Urban area (low NDVI, high NDBI)
- **Plots 19-24**: Forest (very high NDVI, low NDBI)
- **Plots 25-30**: Grassland (moderate NDVI, low NDBI)

## Analysis Output

The system provides:
- **Change Detection**: Identifies vegetation, construction, and flooding changes
- **Delta Calculations**: Shows precise changes in indices
- **Rule Matching**: Applies appropriate rules based on land type
- **Statistical Summary**: Counts and categorizes different types of changes
- **Plot-wise Analysis**: Detailed breakdown by individual plots
- **Excel Export**: Professional Excel reports with multiple worksheets

## Technical Details

- **Database**: SQLite (no external dependencies for core functionality)
- **Python Version**: 3.6+
- **Excel Export**: Requires openpyxl library
- **Rule Evaluation**: Safe mathematical expression evaluation
- **Data Format**: 2-digit precision for all index values
- **Time Periods**: Monthly intervals for realistic change detection
- **Date Tolerance**: ±15 days for flexible date matching

## Extending the System

1. **Add New Land Types**: Insert new records in the Thresholds table
2. **Modify Rules**: Update rule expressions in the Thresholds table
3. **Add More Plots**: Insert additional records in Sentinel_hub_calls_data
4. **Custom Analysis**: Extend the SentinelAnalyzer class with new methods
5. **Custom Excel Formats**: Modify the ExcelExporter class for different layouts

## Security Note

The rule evaluation uses safe mathematical expression evaluation to prevent code injection. Only basic mathematical operations and comparisons are allowed.

## Troubleshooting

1. **Excel Export Issues**: Install openpyxl with `pip install openpyxl`
2. **Database Not Found**: Run `python database_schema.py` first
3. **CSV Processing Errors**: Check CSV format and date formats
4. **No Data Found**: Ensure dates are within ±15 days of available data

## License

This project is provided as-is for educational and research purposes.
