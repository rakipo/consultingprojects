"""
CSV Input Generator for Sentinel-2 Analysis
Creates sample CSV input files with test data
"""
import csv
from datetime import datetime, timedelta
import random

def generate_sample_csv(filename='input_data.csv', num_tests=100):
    """Generate sample CSV input file with test data for 100 plots"""
    
    # Land types with their corresponding plot ranges (100 plots)
    land_types = [
        ('Agriculture Wet Land', (1, 20)),
        ('Agriculture Dry Land', (21, 40)),
        ('Urban Area', (41, 60)),
        ('Forest', (61, 80)),
        ('Grassland', (81, 100))
    ]
    
    # Get available dates from the database (simulated)
    start_date = datetime(2024, 1, 1)
    available_dates = [start_date + timedelta(days=i*30) for i in range(4)]
    
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['Test_id', 'plot_no', 'baseline_date', 'target_date', 'land_type']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for test_id in range(1, num_tests + 1):
            plot_no = random.randint(1, 100)  # Random plot between 1-100
            
            # Determine land type based on plot number
            land_type = 'Grassland'  # Default
            for lt, (start, end) in land_types:
                if start <= plot_no <= end:
                    land_type = lt
                    break
            
            # Select two different dates
            baseline_date, target_date = random.sample(available_dates, 2)
            
            # Add some random variation (±15 days)
            baseline_variation = random.randint(-15, 15)
            target_variation = random.randint(-15, 15)
            
            baseline_final = baseline_date + timedelta(days=baseline_variation)
            target_final = target_date + timedelta(days=target_variation)
            
            writer.writerow({
                'Test_id': test_id,
                'plot_no': plot_no,
                'baseline_date': baseline_final.strftime('%Y-%m-%d'),
                'target_date': target_final.strftime('%Y-%m-%d'),
                'land_type': land_type
            })
    
    print(f"Generated sample CSV file: {filename} with {num_tests} test cases")

def generate_realistic_csv(filename='realistic_input.csv', num_tests=100):
    """Generate more realistic CSV input with specific scenarios for 100 plots"""
    
    # Land types with their corresponding plot ranges (100 plots)
    land_types = [
        ('Agriculture Wet Land', (1, 20)),
        ('Agriculture Dry Land', (21, 40)),
        ('Urban Area', (41, 60)),
        ('Forest', (61, 80)),
        ('Grassland', (81, 100))
    ]
    
    scenarios = [
        # Agriculture monitoring
        {'plot_range': (1, 40), 'baseline_month': 1, 'target_month': 3, 'description': 'Agriculture monitoring'},
        # Urban development
        {'plot_range': (41, 60), 'baseline_month': 1, 'target_month': 4, 'description': 'Urban development'},
        # Forest monitoring
        {'plot_range': (61, 80), 'baseline_month': 1, 'target_month': 2, 'description': 'Forest monitoring'},
        # Seasonal changes
        {'plot_range': (81, 100), 'baseline_month': 1, 'target_month': 4, 'description': 'Seasonal changes'}
    ]
    
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['Test_id', 'plot_no', 'baseline_date', 'target_date', 'land_type', 'scenario']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        test_id = 1
        
        for scenario in scenarios:
            plot_start, plot_end = scenario['plot_range']
            baseline_month = scenario['baseline_month']
            target_month = scenario['target_month']
            description = scenario['description']
            
            # Generate tests for this scenario
            num_scenario_tests = (plot_end - plot_start + 1) * 2  # 2 tests per plot
            
            for i in range(num_scenario_tests):
                plot_no = random.randint(plot_start, plot_end)
                
                # Determine land type based on plot number
                land_type = 'Grassland'  # Default
                for lt, (start, end) in land_types:
                    if start <= plot_no <= end:
                        land_type = lt
                        break
                
                # Create dates with some variation
                baseline_date = datetime(2024, baseline_month, 1) + timedelta(days=random.randint(0, 28))
                target_date = datetime(2024, target_month, 1) + timedelta(days=random.randint(0, 28))
                
                # Add ±15 days variation
                baseline_final = baseline_date + timedelta(days=random.randint(-15, 15))
                target_final = target_date + timedelta(days=random.randint(-15, 15))
                
                writer.writerow({
                    'Test_id': test_id,
                    'plot_no': plot_no,
                    'baseline_date': baseline_final.strftime('%Y-%m-%d'),
                    'target_date': target_final.strftime('%Y-%m-%d'),
                    'land_type': land_type,
                    'scenario': description
                })
                
                test_id += 1
    
    print(f"Generated realistic CSV file: {filename} with {test_id - 1} test cases")

if __name__ == "__main__":
    # Generate sample CSV files
    generate_sample_csv('sample_input.csv', 30)
    generate_realistic_csv('realistic_input.csv', 50)
    
    print("\nGenerated CSV files:")
    print("1. sample_input.csv - Basic test cases")
    print("2. realistic_input.csv - Realistic scenarios")
    print("\nUse these files with sentinel_analyzer.py to process the data.")
