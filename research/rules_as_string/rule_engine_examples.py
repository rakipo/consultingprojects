#!/usr/bin/env python3
"""
Sentinel-2 Rule Engine Examples
===============================

This script demonstrates how to work with the rule engine system.
It shows how to create, test, and modify rules for environmental change detection.

Author: Sentinel-2 Analysis System
Date: 2024
"""

import sqlite3
import json
from datetime import datetime

class RuleEngineDemo:
    """Demonstration class for the Sentinel-2 Rule Engine"""
    
    def __init__(self, db_path='sentinel_analysis.db'):
        """Initialize the rule engine demo"""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
    
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
    
    def debug_rule(self, rule, dvi, dbi, dwi):
        """Debug a rule with detailed output"""
        print(f"🔍 Debugging Rule: {rule}")
        print(f"📊 Input Values: dvi={dvi}, dbi={dbi}, dwi={dwi}")
        print("-" * 50)
        
        # Step 1: Variable substitution
        rule_eval = rule.replace('dvi', str(dvi)).replace('dbi', str(dbi)).replace('dwi', str(dwi))
        print(f"1️⃣ After substitution: {rule_eval}")
        
        # Step 2: SQL to Python conversion
        rule_python = rule_eval.replace(' AND ', ' and ').replace(' OR ', ' or ')
        print(f"2️⃣ Python expression: {rule_python}")
        
        # Step 3: Evaluation
        try:
            result = eval(rule_python)
            print(f"3️⃣ Result: {result}")
            return result
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def test_rule(self, rule, test_cases):
        """Test a rule with various delta values"""
        print(f"🧪 Testing Rule: {rule}")
        print("=" * 60)
        
        for i, (dvi, dbi, dwi, expected, description) in enumerate(test_cases, 1):
            result = self.evaluate_rule(rule, dvi, dbi, dwi)
            status = "✅ PASS" if result == expected else "❌ FAIL"
            
            print(f"Test {i}: {description}")
            print(f"  Input: dvi={dvi}, dbi={dbi}, dwi={dwi}")
            print(f"  Expected: {expected}, Got: {result}")
            print(f"  Status: {status}")
            print()
    
    def create_sample_rules(self):
        """Create sample rules for demonstration"""
        sample_rules = [
            ('Forest', 
             'dvi > 0.15 OR (dbi < 0.03 AND dwi < 0.15)', 
             'dvi < -0.12 OR dbi > 0.08', 
             'dvi < -0.15 OR dwi > 0.30'),
            
            ('Urban Area', 
             'dvi > 0.03 OR (dbi < 0.15 AND dwi < 0.03)', 
             'dvi < -0.02 OR dbi > 0.15', 
             'dvi < -0.03 OR dwi > 0.12'),
            
            ('Agriculture Wet Land', 
             'dvi > 0.10 OR (dbi < 0.03 AND dwi < 0.12)', 
             'dvi < -0.08 OR dbi > 0.10', 
             'dvi < -0.12 OR dwi > 0.30')
        ]
        
        print("📝 Creating sample rules...")
        for land_type, veg_rule, con_rule, flood_rule in sample_rules:
            self.cursor.execute('''
            INSERT OR REPLACE INTO Thresholds 
            (threshold_short_description, vegetation_rule, construction_rule, flooding_rule)
            VALUES (?, ?, ?, ?)
            ''', (land_type, veg_rule, con_rule, flood_rule))
        
        self.conn.commit()
        print("✅ Sample rules created successfully!")
    
    def demonstrate_rule_evaluation(self):
        """Demonstrate rule evaluation with examples"""
        print("\n🎯 Rule Evaluation Demonstration")
        print("=" * 50)
        
        # Example 1: Simple rule
        print("\n1️⃣ Simple Rule Example:")
        rule1 = "dvi > 0.1"
        self.debug_rule(rule1, 0.25, 0.05, 0.15)
        
        # Example 2: Complex rule with AND
        print("\n2️⃣ Complex Rule with AND:")
        rule2 = "dvi > 0.1 AND dbi < 0.05"
        self.debug_rule(rule2, 0.25, 0.03, 0.15)
        
        # Example 3: Complex rule with OR
        print("\n3️⃣ Complex Rule with OR:")
        rule3 = "dvi < -0.1 OR dwi > 0.2"
        self.debug_rule(rule3, -0.05, 0.1, 0.25)
        
        # Example 4: Mixed logical operations
        print("\n4️⃣ Mixed Logical Operations:")
        rule4 = "dvi > 0.1 OR (dbi < 0.05 AND dwi < 0.1)"
        self.debug_rule(rule4, 0.25, 0.03, 0.08)
    
    def demonstrate_rule_testing(self):
        """Demonstrate rule testing with test cases"""
        print("\n🧪 Rule Testing Demonstration")
        print("=" * 50)
        
        # Test case for vegetation rule
        vegetation_rule = "dvi > 0.1 OR (dbi < 0.05 AND dwi < 0.1)"
        test_cases = [
            (0.25, 0.03, 0.08, True, "Strong vegetation increase, low construction, low water"),
            (0.05, 0.03, 0.08, True, "Low vegetation increase, but low construction and water"),
            (0.25, 0.1, 0.15, True, "Strong vegetation increase, high construction and water"),
            (0.05, 0.1, 0.15, False, "Low vegetation increase, high construction and water"),
            (-0.1, 0.03, 0.08, False, "Vegetation decrease, low construction and water"),
        ]
        
        self.test_rule(vegetation_rule, test_cases)
    
    def demonstrate_rule_modification(self):
        """Demonstrate how to modify rules"""
        print("\n🔧 Rule Modification Demonstration")
        print("=" * 50)
        
        # Show current rules
        print("\n📋 Current Rules:")
        self.cursor.execute('SELECT * FROM Thresholds LIMIT 3')
        rules = self.cursor.fetchall()
        
        for rule in rules:
            print(f"Land Type: {rule[1]}")
            print(f"  Vegetation: {rule[2]}")
            print(f"  Construction: {rule[3]}")
            print(f"  Flooding: {rule[4]}")
            print()
        
        # Modify a rule
        print("🔨 Modifying Forest vegetation rule...")
        new_rule = "dvi > 0.2 OR (dbi < 0.02 AND dwi < 0.12)"  # More strict thresholds
        self.cursor.execute('''
        UPDATE Thresholds 
        SET vegetation_rule = ? 
        WHERE threshold_short_description = 'Forest'
        ''', (new_rule,))
        self.conn.commit()
        
        print(f"✅ Updated rule: {new_rule}")
        
        # Test the modified rule
        print("\n🧪 Testing modified rule:")
        self.debug_rule(new_rule, 0.15, 0.01, 0.10)
    
    def demonstrate_rule_validation(self):
        """Demonstrate rule validation"""
        print("\n✅ Rule Validation Demonstration")
        print("=" * 50)
        
        # Valid rules
        valid_rules = [
            "dvi > 0.1",
            "dvi > 0.1 AND dbi < 0.05",
            "dvi < -0.1 OR dwi > 0.2",
            "dvi > 0.1 OR (dbi < 0.05 AND dwi < 0.1)"
        ]
        
        # Invalid rules
        invalid_rules = [
            "dvi > 0.1; import os",  # Contains disallowed characters
            "dvi > 0.1 AND",  # Incomplete expression
            "dvi > 0.1 AND dbi > 0.05 AND",  # Incomplete expression
            "dvi > 0.1 AND dbi > 0.05 AND dwi > 0.1 AND",  # Incomplete expression
        ]
        
        print("✅ Valid Rules:")
        for rule in valid_rules:
            is_valid = self.validate_rule(rule)
            print(f"  {rule} → {is_valid}")
        
        print("\n❌ Invalid Rules:")
        for rule in invalid_rules:
            is_valid = self.validate_rule(rule)
            print(f"  {rule} → {is_valid}")
    
    def validate_rule(self, rule):
        """Validate rule syntax"""
        try:
            # Test with dummy values
            test_rule = rule.replace('dvi', '0.1').replace('dbi', '0.1').replace('dwi', '0.1')
            test_rule = test_rule.replace(' AND ', ' and ').replace(' OR ', ' or ')
            eval(test_rule)
            return True
        except:
            return False
    
    def export_rules_to_json(self, filename='rules_export.json'):
        """Export rules to JSON file"""
        print(f"\n📤 Exporting rules to {filename}...")
        
        self.cursor.execute('SELECT * FROM Thresholds')
        rules = self.cursor.fetchall()
        
        rules_data = {
            'export_date': datetime.now().isoformat(),
            'land_types': {}
        }
        
        for rule in rules:
            land_type = rule[1]
            rules_data['land_types'][land_type] = {
                'vegetation_rule': rule[2],
                'construction_rule': rule[3],
                'flooding_rule': rule[4]
            }
        
        with open(filename, 'w') as f:
            json.dump(rules_data, f, indent=2)
        
        print(f"✅ Rules exported to {filename}")
    
    def import_rules_from_json(self, filename='rules_export.json'):
        """Import rules from JSON file"""
        print(f"\n📥 Importing rules from {filename}...")
        
        try:
            with open(filename, 'r') as f:
                rules_data = json.load(f)
            
            for land_type, rules in rules_data['land_types'].items():
                self.cursor.execute('''
                INSERT OR REPLACE INTO Thresholds 
                (threshold_short_description, vegetation_rule, construction_rule, flooding_rule)
                VALUES (?, ?, ?, ?)
                ''', (land_type, rules['vegetation_rule'], 
                      rules['construction_rule'], rules['flooding_rule']))
            
            self.conn.commit()
            print(f"✅ Rules imported from {filename}")
            
        except FileNotFoundError:
            print(f"❌ File {filename} not found")
        except Exception as e:
            print(f"❌ Error importing rules: {e}")
    
    def close(self):
        """Close database connection"""
        self.conn.close()

def main():
    """Main demonstration function"""
    print("🛰️  Sentinel-2 Rule Engine Demonstration")
    print("=" * 60)
    
    # Initialize demo
    demo = RuleEngineDemo()
    
    try:
        # Create sample rules
        demo.create_sample_rules()
        
        # Demonstrate rule evaluation
        demo.demonstrate_rule_evaluation()
        
        # Demonstrate rule testing
        demo.demonstrate_rule_testing()
        
        # Demonstrate rule modification
        demo.demonstrate_rule_modification()
        
        # Demonstrate rule validation
        demo.demonstrate_rule_validation()
        
        # Export rules
        demo.export_rules_to_json()
        
        print("\n🎉 Demonstration completed successfully!")
        print("\n📚 Next Steps:")
        print("1. Read the README_RULE_ENGINE.md for detailed documentation")
        print("2. Modify rules in the database or JSON file")
        print("3. Test your rules with the provided functions")
        print("4. Integrate with the main Sentinel-2 analysis system")
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
    
    finally:
        demo.close()

if __name__ == "__main__":
    main()


