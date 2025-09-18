"""
Database schema creation for Sentinel-2 satellite data analysis
Creates tables for satellite data, thresholds, and transactions
"""
import sqlite3
from datetime import datetime, timedelta
import random

def create_database():
    """Create SQLite database with required tables"""
    conn = sqlite3.connect('sentinel_analysis.db')
    cursor = conn.cursor()
    
    # Create Sentinel_hub_calls_data table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Sentinel_hub_calls_data (
        S_no INTEGER PRIMARY KEY AUTOINCREMENT,
        plot_no INTEGER NOT NULL,
        date TEXT NOT NULL,
        ndvi REAL NOT NULL,
        ndbi REAL NOT NULL,
        ndwi REAL NOT NULL
    )
    ''')
    
    # Create Thresholds table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Thresholds (
        S_no INTEGER PRIMARY KEY AUTOINCREMENT,
        threshold_short_description TEXT NOT NULL,
        vegetation_rule TEXT NOT NULL,
        construction_rule TEXT NOT NULL,
        flooding_rule TEXT NOT NULL
    )
    ''')
    
    # Create Transactions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Transactions (
        S_no INTEGER PRIMARY KEY AUTOINCREMENT,
        test_id INTEGER NOT NULL,
        plot_no INTEGER NOT NULL,
        baseline_date TEXT NOT NULL,
        target_date TEXT NOT NULL,
        ndvi_baseline REAL NOT NULL,
        ndbi_baseline REAL NOT NULL,
        ndwi_baseline REAL NOT NULL,
        ndvi_target REAL NOT NULL,
        ndbi_target REAL NOT NULL,
        ndwi_target REAL NOT NULL,
        delta_ndvi REAL NOT NULL,
        delta_ndbi REAL NOT NULL,
        delta_ndwi REAL NOT NULL,
        vegetation_rule TEXT,
        construction_rule TEXT,
        flooding_rule TEXT,
        vegetation_inference TEXT,
        construction_inference TEXT,
        flood_inference TEXT
    )
    ''')
    
    conn.commit()
    conn.close()
    print("Database schema created successfully!")

def populate_sentinel_data():
    """Populate Sentinel_hub_calls_data with sample data for 100 plots"""
    conn = sqlite3.connect('sentinel_analysis.db')
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute('DELETE FROM Sentinel_hub_calls_data')
    
    # Generate sample data for 100 plots over 4 dates
    start_date = datetime(2024, 1, 1)
    dates = [start_date + timedelta(days=i*30) for i in range(4)]  # Monthly intervals
    
    for plot_no in range(1, 101):
        # Create baseline values for each plot
        if plot_no <= 20:  # Agriculture wet land (plots 1-20)
            base_ndvi = random.uniform(0.5, 0.8)
            base_ndbi = random.uniform(0.0, 0.15)
            base_ndwi = random.uniform(0.3, 0.6)
        elif plot_no <= 40:  # Agriculture dry land (plots 21-40)
            base_ndvi = random.uniform(0.4, 0.7)
            base_ndbi = random.uniform(0.1, 0.25)
            base_ndwi = random.uniform(0.1, 0.4)
        elif plot_no <= 60:  # Urban area (plots 41-60)
            base_ndvi = random.uniform(0.1, 0.4)
            base_ndbi = random.uniform(0.3, 0.6)
            base_ndwi = random.uniform(0.1, 0.3)
        elif plot_no <= 80:  # Forest (plots 61-80)
            base_ndvi = random.uniform(0.6, 0.9)
            base_ndbi = random.uniform(0.0, 0.1)
            base_ndwi = random.uniform(0.2, 0.5)
        else:  # Grassland (plots 81-100)
            base_ndvi = random.uniform(0.3, 0.6)
            base_ndbi = random.uniform(0.0, 0.2)
            base_ndwi = random.uniform(0.2, 0.4)
        
        for i, date in enumerate(dates):
            # Create realistic changes over time that will trigger rules
            if i == 0:  # First date - baseline
                ndvi = round(base_ndvi, 2)
                ndbi = round(base_ndbi, 2)
                ndwi = round(base_ndwi, 2)
            else:
                # Create changes that will trigger different types of inferences
                change_type = plot_no % 6  # Cycle through 6 different change patterns
                
                if change_type == 0:  # Strong vegetation increase
                    ndvi = round(base_ndvi + random.uniform(0.20, 0.50), 2)
                    ndbi = round(max(0, base_ndbi - random.uniform(0.05, 0.20)), 2)
                    ndwi = round(max(0, base_ndwi - random.uniform(0.05, 0.25)), 2)
                elif change_type == 1:  # Strong construction increase
                    ndvi = round(max(0, base_ndvi - random.uniform(0.15, 0.35)), 2)
                    ndbi = round(base_ndbi + random.uniform(0.25, 0.50), 2)
                    ndwi = round(max(0, base_ndwi - random.uniform(0.05, 0.20)), 2)
                elif change_type == 2:  # Strong flooding increase
                    ndvi = round(max(0, base_ndvi - random.uniform(0.20, 0.40)), 2)
                    ndbi = round(max(0, base_ndbi - random.uniform(0.05, 0.20)), 2)
                    ndwi = round(base_ndwi + random.uniform(0.30, 0.55), 2)
                elif change_type == 3:  # Moderate vegetation + construction
                    ndvi = round(base_ndvi + random.uniform(0.10, 0.25), 2)
                    ndbi = round(base_ndbi + random.uniform(0.15, 0.30), 2)
                    ndwi = round(max(0, base_ndwi - random.uniform(0.05, 0.15)), 2)
                elif change_type == 4:  # Moderate vegetation + flooding
                    ndvi = round(base_ndvi + random.uniform(0.10, 0.25), 2)
                    ndbi = round(max(0, base_ndbi - random.uniform(0.05, 0.15)), 2)
                    ndwi = round(base_ndwi + random.uniform(0.20, 0.35), 2)
                else:  # Mixed changes with all types
                    ndvi = round(max(0, base_ndvi + random.uniform(-0.30, 0.30)), 2)
                    ndbi = round(max(0, base_ndbi + random.uniform(-0.20, 0.35)), 2)
                    ndwi = round(max(0, base_ndwi + random.uniform(-0.20, 0.40)), 2)
                
                # Ensure values stay within valid range
                ndvi = max(0, min(1, ndvi))
                ndbi = max(0, min(1, ndbi))
                ndwi = max(0, min(1, ndwi))
            
            cursor.execute('''
            INSERT INTO Sentinel_hub_calls_data (plot_no, date, ndvi, ndbi, ndwi)
            VALUES (?, ?, ?, ?, ?)
            ''', (plot_no, date.strftime('%Y-%m-%d'), ndvi, ndbi, ndwi))
    
    conn.commit()
    conn.close()
    print("Sentinel data populated successfully with 100 plots!")

def populate_thresholds():
    """Populate Thresholds table with rules for different land types"""
    conn = sqlite3.connect('sentinel_analysis.db')
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute('DELETE FROM Thresholds')
    
    # Define thresholds with soil-specific rules for accurate environmental change detection
    thresholds = [
        ('Red Soil', 
         'dvi > 0.08 OR (dbi < 0.05 AND dwi < 0.08)', 
         'dvi < -0.06 OR dbi > 0.10', 
         'dvi < -0.08 OR dwi > 0.15'),
        
        ('Black Soil', 
         'dvi > 0.10 OR (dbi < 0.04 AND dwi < 0.10)', 
         'dvi < -0.08 OR dbi > 0.08', 
         'dvi < -0.10 OR dwi > 0.22'),
        
        ('Sand Quarry', 
         'dvi > 0.05 OR (dbi < 0.15 AND dwi < 0.05)', 
         'dvi < -0.03 OR dbi > 0.20', 
         'dvi < -0.05 OR dwi > 0.10'),
        
        ('Rock Quarry', 
         'dvi > 0.03 OR (dbi < 0.20 AND dwi < 0.03)', 
         'dvi < -0.02 OR dbi > 0.25', 
         'dvi < -0.03 OR dwi > 0.08'),
        
        ('River Bed', 
         'dvi > 0.06 OR (dbi < 0.03 AND dwi < 0.20)', 
         'dvi < -0.04 OR dbi > 0.05', 
         'dvi < -0.06 OR dwi > 0.30'),
        
        ('Agriculture Wet Land', 
         'dvi > 0.10 OR (dbi < 0.03 AND dwi < 0.12)', 
         'dvi < -0.08 OR dbi > 0.10', 
         'dvi < -0.12 OR dwi > 0.30'),
        
        ('Agriculture Dry Land', 
         'dvi > 0.08 OR (dbi < 0.05 AND dwi < 0.10)', 
         'dvi < -0.06 OR dbi > 0.12', 
         'dvi < -0.10 OR dwi > 0.18'),
        
        ('Urban Area', 
         'dvi > 0.03 OR (dbi < 0.15 AND dwi < 0.03)', 
         'dvi < -0.02 OR dbi > 0.15', 
         'dvi < -0.03 OR dwi > 0.12'),
        
        ('Forest', 
         'dvi > 0.2 OR (dbi < 0.02 AND dwi < 0.12)', 
         'dvi < -0.12 OR dbi > 0.08', 
         'dvi < -0.15 OR dwi > 0.30'),
        
        ('Grassland', 
         'dvi > 0.10 OR (dbi < 0.05 AND dwi < 0.10)', 
         'dvi < -0.08 OR dbi > 0.12', 
         'dvi < -0.12 OR dwi > 0.20'),
        
        ('Wetland', 
         'dvi > 0.08 OR (dbi < 0.03 AND dwi < 0.15)', 
         'dvi < -0.06 OR dbi > 0.08', 
         'dvi < -0.10 OR dwi > 0.25'),
        
        ('Desert', 
         'dvi > 0.02 OR (dbi < 0.10 AND dwi < 0.02)', 
         'dvi < -0.01 OR dbi > 0.12', 
         'dvi < -0.02 OR dwi > 0.08'),
        
        ('Mountain', 
         'dvi > 0.12 OR (dbi < 0.03 AND dwi < 0.12)', 
         'dvi < -0.10 OR dbi > 0.08', 
         'dvi < -0.15 OR dwi > 0.18'),
        
        ('Coastal Area', 
         'dvi > 0.06 OR (dbi < 0.03 AND dwi < 0.18)', 
         'dvi < -0.04 OR dbi > 0.08', 
         'dvi < -0.08 OR dwi > 0.25'),
        
        ('Industrial Area', 
         'dvi > 0.02 OR (dbi < 0.25 AND dwi < 0.03)', 
         'dvi < -0.01 OR dbi > 0.25', 
         'dvi < -0.02 OR dwi > 0.12')
    ]
    
    # Insert thresholds into the database
    for desc, veg_rule, con_rule, flood_rule in thresholds:
        cursor.execute('''
        INSERT INTO Thresholds (threshold_short_description, vegetation_rule, construction_rule, flooding_rule)
        VALUES (?, ?, ?, ?)
        ''', (desc, veg_rule, con_rule, flood_rule))
    
    conn.commit()
    conn.close()
    print("Thresholds populated successfully with 15 land types!")

if __name__ == "__main__":
    create_database()
    populate_sentinel_data()
    populate_thresholds()
