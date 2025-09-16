"""
Sentinel-2 Satellite Data Analysis Application
Processes CSV input and analyzes vegetation, construction, and flooding changes
"""
import sqlite3
import csv
from datetime import datetime, timedelta
import re

class SentinelAnalyzer:
    def __init__(self, db_path='sentinel_analysis.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
    
    def close_connection(self):
        """Close database connection"""
        self.conn.close()
    
    def safe_eval(self, expression):
        """Safely evaluate mathematical expressions for rule evaluation"""
        try:
            # Only allow safe mathematical operations and logical operators
            allowed_chars = set('0123456789+-*/.()<>=&|! AND OR ')
            if all(c in allowed_chars for c in expression):
                # Replace AND and OR with Python equivalents
                expression = expression.replace(' AND ', ' and ').replace(' OR ', ' or ')
                return eval(expression)
            else:
                return False
        except:
            return False
    
    def evaluate_rule(self, rule, dvi, dbi, dwi):
        """Evaluate a rule string with given delta values"""
        try:
            # Replace variable names with actual values
            rule_eval = rule.replace('dvi', str(dvi)).replace('dbi', str(dbi)).replace('dwi', str(dwi))
            return self.safe_eval(rule_eval)
        except:
            return False
    
    def get_change_intensity(self, delta_value):
        """Determine change intensity based on delta value"""
        abs_delta = abs(delta_value)
        if abs_delta >= 0.3:
            return "Deep Change"
        elif abs_delta >= 0.15:
            return "Moderate Change"
        elif abs_delta >= 0.05:
            return "Slight Change"
        else:
            return None
    
    def get_change_direction(self, delta_value):
        """Determine change direction based on delta value"""
        if delta_value > 0.01:
            return "Increased"
        elif delta_value < -0.01:
            return "Decreased"
        else:
            return None
    
    def generate_inference(self, dvi, dbi, dwi, land_type):
        """Generate meaningful inference based on delta values and land type"""
        # Check for vegetation changes (NDVI)
        veg_intensity = self.get_change_intensity(dvi)
        veg_direction = self.get_change_direction(dvi)
        
        # Check for construction changes (NDBI)
        con_intensity = self.get_change_intensity(dbi)
        con_direction = self.get_change_direction(dbi)
        
        # Check for flooding changes (NDWI)
        flood_intensity = self.get_change_intensity(dwi)
        flood_direction = self.get_change_direction(dwi)
        
        # Generate vegetation inference
        veg_inference = "No Change"
        if veg_intensity and veg_direction:
            veg_inference = f"{veg_intensity} - {veg_direction}"
        
        # Generate construction inference
        con_inference = "No Change"
        if con_intensity and con_direction:
            con_inference = f"{con_intensity} - {con_direction}"
        
        # Generate flooding inference
        flood_inference = "No Change"
        if flood_intensity and flood_direction:
            flood_inference = f"{flood_intensity} - {flood_direction}"
        
        return veg_inference, con_inference, flood_inference
    
    def find_nearest_date(self, plot_no, target_date, tolerance_days=15):
        """Find the nearest date within tolerance for a given plot"""
        target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        
        # Get all dates for this plot
        self.cursor.execute('''
        SELECT date FROM Sentinel_hub_calls_data 
        WHERE plot_no = ? ORDER BY date
        ''', (plot_no,))
        dates = self.cursor.fetchall()
        
        nearest_date = None
        min_diff = float('inf')
        
        for date_tuple in dates:
            date_str = date_tuple[0]
            date_dt = datetime.strptime(date_str, '%Y-%m-%d')
            diff_days = abs((target_dt - date_dt).days)
            
            if diff_days <= tolerance_days and diff_days < min_diff:
                min_diff = diff_days
                nearest_date = date_str
        
        return nearest_date
    
    def get_satellite_data(self, plot_no, date):
        """Get satellite data for a specific plot and date"""
        self.cursor.execute('''
        SELECT ndvi, ndbi, ndwi FROM Sentinel_hub_calls_data
        WHERE plot_no = ? AND date = ?
        ''', (plot_no, date))
        return self.cursor.fetchone()
    
    def process_csv_input(self, csv_file_path):
        """Process CSV input file and populate transactions table"""
        # Clear existing transactions
        self.cursor.execute('DELETE FROM Transactions')
        
        # Get all thresholds
        self.cursor.execute('SELECT * FROM Thresholds')
        thresholds = self.cursor.fetchall()
        
        # Create threshold lookup dictionary
        threshold_lookup = {t[1]: t for t in thresholds}
        
        test_id = 1
        processed_count = 0
        error_count = 0
        
        try:
            with open(csv_file_path, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    try:
                        test_id_input = int(row['Test_id'])
                        plot_no = int(row['plot_no'])
                        baseline_date = row['baseline_date']
                        target_date = row['target_date']
                        land_type = row.get('land_type', 'Grassland')  # Default to Grassland if not specified
                        
                        # Find nearest dates within ±15 days
                        baseline_nearest = self.find_nearest_date(plot_no, baseline_date)
                        target_nearest = self.find_nearest_date(plot_no, target_date)
                        
                        if not baseline_nearest or not target_nearest:
                            print(f"Warning: No data found within ±15 days for plot {plot_no}")
                            error_count += 1
                            continue
                        
                        # Get satellite data
                        baseline_data = self.get_satellite_data(plot_no, baseline_nearest)
                        target_data = self.get_satellite_data(plot_no, target_nearest)
                        
                        if not baseline_data or not target_data:
                            print(f"Warning: Missing satellite data for plot {plot_no}")
                            error_count += 1
                            continue
                        
                        ndvi_baseline, ndbi_baseline, ndwi_baseline = baseline_data
                        ndvi_target, ndbi_target, ndwi_target = target_data
                        
                        # Calculate deltas
                        dvi = ndvi_baseline - ndvi_target
                        dbi = ndbi_baseline - ndbi_target
                        dwi = ndwi_baseline - ndwi_target
                        
                        # Get threshold rules for the specific land type
                        if land_type in threshold_lookup:
                            threshold = threshold_lookup[land_type]
                            veg_rule = threshold[2]
                            con_rule = threshold[3]
                            flood_rule = threshold[4]
                        else:
                            # Default to Grassland if land type not found
                            threshold = threshold_lookup['Grassland']
                            veg_rule = threshold[2]
                            con_rule = threshold[3]
                            flood_rule = threshold[4]
                            print(f"Warning: Land type '{land_type}' not found, using Grassland rules")
                        
                        # Generate meaningful inferences based on delta values
                        veg_inference, con_inference, flood_inference = self.generate_inference(dvi, dbi, dwi, land_type)
                        
                        # Insert transaction record
                        self.cursor.execute('''
                        INSERT INTO Transactions (
                            test_id, plot_no, baseline_date, target_date,
                            ndvi_baseline, ndbi_baseline, ndwi_baseline,
                            ndvi_target, ndbi_target, ndwi_target,
                            delta_ndvi, delta_ndbi, delta_ndwi,
                            vegetation_rule, construction_rule, flooding_rule,
                            vegetation_inference, construction_inference, flood_inference
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            test_id_input, plot_no, baseline_nearest, target_nearest,
                            ndvi_baseline, ndbi_baseline, ndwi_baseline,
                            ndvi_target, ndbi_target, ndwi_target,
                            dvi, dbi, dwi,
                            veg_rule, con_rule, flood_rule,
                            veg_inference, con_inference, flood_inference
                        ))
                        
                        processed_count += 1
                        test_id += 1
                        
                    except Exception as e:
                        print(f"Error processing row {test_id}: {e}")
                        error_count += 1
                        continue
            
            self.conn.commit()
            print(f"CSV processing completed!")
            print(f"Successfully processed: {processed_count} records")
            print(f"Errors encountered: {error_count} records")
            
        except FileNotFoundError:
            print(f"Error: CSV file '{csv_file_path}' not found")
        except Exception as e:
            print(f"Error processing CSV file: {e}")
    
    def get_transactions(self):
        """Get all transaction records"""
        self.cursor.execute('SELECT * FROM Transactions ORDER BY test_id')
        return self.cursor.fetchall()
    
    def get_plot_data(self, plot_no):
        """Get raw satellite data for a specific plot"""
        self.cursor.execute('''
        SELECT * FROM Sentinel_hub_calls_data WHERE plot_no = ? ORDER BY date
        ''', (plot_no,))
        return self.cursor.fetchall()
    
    def get_thresholds(self):
        """Get all threshold rules"""
        self.cursor.execute('SELECT * FROM Thresholds')
        return self.cursor.fetchall()
    
    def print_analysis_report(self):
        """Print a comprehensive analysis report"""
        print("\n" + "="*80)
        print("SENTINEL-2 SATELLITE DATA ANALYSIS REPORT")
        print("="*80)
        
        # Get all transactions
        transactions = self.get_transactions()
        
        if not transactions:
            print("No transaction data available. Process CSV input first.")
            return
        
        print(f"\nTotal Transactions Processed: {len(transactions)}")
        
        # Summary by plot
        print("\n" + "-"*50)
        print("ANALYSIS BY PLOT")
        print("-"*50)
        
        plots = {}
        for trans in transactions:
            plot_no = trans[2]
            if plot_no not in plots:
                plots[plot_no] = []
            plots[plot_no].append(trans)
        
        for plot_no in sorted(plots.keys()):
            print(f"\nPlot {plot_no}:")
            plot_transactions = plots[plot_no]
            
            for trans in plot_transactions:
                test_id = trans[1]
                baseline_date = trans[3]
                target_date = trans[4]
                dvi = trans[10]
                dbi = trans[11]
                dwi = trans[12]
                veg_inf = trans[16]
                con_inf = trans[17]
                flood_inf = trans[18]
                
                print(f"  Test {test_id}: {baseline_date} → {target_date}")
                print(f"    Deltas: NDVI={dvi:.3f}, NDBI={dbi:.3f}, NDWI={dwi:.3f}")
                print(f"    Vegetation: {veg_inf}")
                print(f"    Construction: {con_inf}")
                print(f"    Flooding: {flood_inf}")
        
        # Summary statistics
        print("\n" + "-"*50)
        print("SUMMARY STATISTICS")
        print("-"*50)
        
        veg_changes = sum(1 for trans in transactions if trans[16] != "No Change")
        con_changes = sum(1 for trans in transactions if trans[17] != "No Change")
        flood_changes = sum(1 for trans in transactions if trans[18] != "No Change")
        
        print(f"Vegetation Changes Detected: {veg_changes}")
        print(f"Construction Changes Detected: {con_changes}")
        print(f"Flooding Changes Detected: {flood_changes}")
        
        # Most common change types
        veg_types = {}
        con_types = {}
        flood_types = {}
        
        for trans in transactions:
            veg = trans[16]
            con = trans[17]
            flood = trans[18]
            
            veg_types[veg] = veg_types.get(veg, 0) + 1
            con_types[con] = con_types.get(con, 0) + 1
            flood_types[flood] = flood_types.get(flood, 0) + 1
        
        print(f"\nMost Common Vegetation Changes:")
        for change_type, count in sorted(veg_types.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {change_type}: {count}")
        
        print(f"\nMost Common Construction Changes:")
        for change_type, count in sorted(con_types.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {change_type}: {count}")
        
        print(f"\nMost Common Flooding Changes:")
        for change_type, count in sorted(flood_types.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {change_type}: {count}")
    
    def export_results_to_csv(self, output_file='analysis_results.csv'):
        """Export analysis results to CSV file"""
        transactions = self.get_transactions()
        
        if not transactions:
            print("No data to export. Process CSV input first.")
            return
        
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = [
                'test_id', 'plot_no', 'baseline_date', 'target_date',
                'ndvi_baseline', 'ndbi_baseline', 'ndwi_baseline',
                'ndvi_target', 'ndbi_target', 'ndwi_target',
                'delta_ndvi', 'delta_ndbi', 'delta_ndwi',
                'vegetation_rule', 'construction_rule', 'flooding_rule',
                'vegetation_inference', 'construction_inference', 'flood_inference'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for trans in transactions:
                writer.writerow({
                    'test_id': trans[1],
                    'plot_no': trans[2],
                    'baseline_date': trans[3],
                    'target_date': trans[4],
                    'ndvi_baseline': trans[5],
                    'ndbi_baseline': trans[6],
                    'ndwi_baseline': trans[7],
                    'ndvi_target': trans[8],
                    'ndbi_target': trans[9],
                    'ndwi_target': trans[10],
                    'delta_ndvi': trans[11],
                    'delta_ndbi': trans[12],
                    'delta_ndwi': trans[13],
                    'vegetation_rule': trans[14],
                    'construction_rule': trans[15],
                    'flooding_rule': trans[16],
                    'vegetation_inference': trans[17],
                    'construction_inference': trans[18],
                    'flood_inference': trans[19]
                })
        
        print(f"Results exported to {output_file}")
    
    def export_to_excel(self, output_file=None):
        """Export all tables to Excel with multiple worksheets and timestamp"""
        try:
            from excel_export import ExcelExporter
            exporter = ExcelExporter(self.db_path)
            result_file = exporter.export_to_excel(output_file)
            exporter.close_connection()
            return result_file
        except ImportError:
            print("❌ Excel export requires openpyxl library. Install with: pip install openpyxl")
            return None
        except Exception as e:
            print(f"❌ Error exporting to Excel: {e}")
            return None

def main():
    """Main function to demonstrate the analysis"""
    print("🛰️  Sentinel-2 Satellite Data Analysis System")
    print("=" * 50)
    
    # Create analyzer instance
    analyzer = SentinelAnalyzer()
    
    try:
        # Check if database exists and has data
        analyzer.cursor.execute("SELECT COUNT(*) FROM Sentinel_hub_calls_data")
        data_count = analyzer.cursor.fetchone()[0]
        
        if data_count == 0:
            print("Database not initialized. Please run database_schema.py first.")
            return
        
        print(f"Database loaded with {data_count} satellite data records")
        
        # Show available plots
        analyzer.cursor.execute("SELECT DISTINCT plot_no FROM Sentinel_hub_calls_data ORDER BY plot_no")
        plots = analyzer.cursor.fetchall()
        print(f"Available plots: {[p[0] for p in plots]}")
        
        # Show sample data for first plot
        print("\nSample data for Plot 1:")
        plot_data = analyzer.get_plot_data(1)
        for record in plot_data:
            print(f"  Date: {record[2]}, NDVI: {record[3]}, NDBI: {record[4]}, NDWI: {record[5]}")
        
        # Show thresholds
        print("\nAvailable land type thresholds:")
        thresholds = analyzer.get_thresholds()
        for threshold in thresholds[:5]:  # Show first 5
            print(f"  {threshold[1]}: Veg={threshold[2][:30]}...")
        
        print(f"\nTotal thresholds available: {len(thresholds)}")
        
    finally:
        analyzer.close_connection()

if __name__ == "__main__":
    main()
