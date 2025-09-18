# Sentinel-2 Rule Engine Documentation

## Table of Contents
1. [Overview](#overview)
2. [Rule Engine Architecture](#rule-engine-architecture)
3. [Rule String Format](#rule-string-format)
4. [Python Rule Interpretation](#python-rule-interpretation)
5. [Rule Evaluation Process](#rule-evaluation-process)
6. [How to Modify Rules](#how-to-modify-rules)
7. [Examples and Use Cases](#examples-and-use-cases)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

## Overview

The Sentinel-2 Rule Engine is a flexible system that allows users to define environmental change detection rules as strings and evaluate them against satellite data deltas. The system uses Python's `eval()` function with safety restrictions to interpret and execute these rule strings dynamically.

### Key Features
- **String-based Rules**: Rules are stored as text strings in the database
- **Dynamic Evaluation**: Rules are interpreted and executed at runtime
- **Safety Controls**: Restricted evaluation environment prevents malicious code
- **Flexible Logic**: Supports complex logical expressions with AND/OR operations
- **Easy Modification**: Rules can be changed without code modifications

## Rule Engine Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Rule String   │───▶│  Rule Parser     │───▶│  Rule Evaluator │
│   (Database)    │    │  (safe_eval)     │    │  (evaluate_rule)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  Delta Values    │
                       │  (dvi, dbi, dwi) │
                       └──────────────────┘
```

### Components

1. **Rule Storage**: Rules stored as strings in SQLite database
2. **Rule Parser**: Converts rule strings to Python expressions
3. **Rule Evaluator**: Executes rules with actual delta values
4. **Safety Layer**: Prevents execution of dangerous code

## Rule String Format

### Basic Syntax

Rules use three main variables representing satellite data deltas:
- `dvi` = Delta Vegetation Index (NDVI_baseline - NDVI_target)
- `dbi` = Delta Built-up Index (NDBI_baseline - NDBI_target)  
- `dwi` = Delta Water Index (NDWI_baseline - NDWI_target)

### Supported Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `>` | Greater than | `dvi > 0.1` |
| `<` | Less than | `dbi < 0.05` |
| `>=` | Greater than or equal | `dwi >= 0.2` |
| `<=` | Less than or equal | `dvi <= -0.1` |
| `==` | Equal to | `dbi == 0.0` |
| `!=` | Not equal to | `dwi != 0.0` |
| `AND` | Logical AND | `dvi > 0.1 AND dbi < 0.05` |
| `OR` | Logical OR | `dvi < -0.1 OR dwi > 0.2` |
| `()` | Grouping | `(dvi > 0.1) AND (dbi < 0.05)` |

### Rule Examples

```python
# Simple rules
"dvi > 0.1"                    # Vegetation increased significantly
"dbi < 0.05"                   # Construction decreased slightly
"dwi > 0.2"                    # Water content increased moderately

# Complex rules with AND
"dvi > 0.1 AND dbi < 0.05"     # Vegetation up AND construction down
"dvi < -0.1 AND dwi > 0.2"     # Vegetation down AND water up

# Complex rules with OR
"dvi < -0.1 OR dbi > 0.1"      # Vegetation down OR construction up
"dvi > 0.05 OR dwi > 0.15"     # Vegetation up OR water up

# Mixed logical operations
"dvi > 0.1 OR (dbi < 0.05 AND dwi < 0.1)"  # Vegetation up OR (construction down AND water down)
"(dvi < -0.1 OR dbi > 0.1) AND dwi > 0.05" # (Vegetation down OR construction up) AND water up
```

## Python Rule Interpretation

### Step 1: Rule String Storage
Rules are stored in the database as strings:

```sql
INSERT INTO Thresholds (threshold_short_description, vegetation_rule, construction_rule, flooding_rule)
VALUES ('Forest', 'dvi > 0.15 OR (dbi < 0.03 AND dwi < 0.15)', 'dvi < -0.12 OR dbi > 0.08', 'dvi < -0.15 OR dwi > 0.30');
```

### Step 2: Rule Retrieval
When processing data, rules are retrieved from the database:

```python
def process_csv_input(self, csv_file_path):
    # Get all thresholds
    self.cursor.execute('SELECT * FROM Thresholds')
    thresholds = self.cursor.fetchall()
    
    # Create threshold lookup dictionary
    threshold_lookup = {t[1]: t for t in thresholds}
```

### Step 3: Rule String Processing
The `evaluate_rule` method processes rule strings:

```python
def evaluate_rule(self, rule, dvi, dbi, dwi):
    """Evaluate a rule string with given delta values"""
    try:
        # Replace variable names with actual values
        rule_eval = rule.replace('dvi', str(dvi)).replace('dbi', str(dbi)).replace('dwi', str(dwi))
        return self.safe_eval(rule_eval)
    except:
        return False
```

### Step 4: Safe Evaluation
The `safe_eval` method ensures safe execution:

```python
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
```

## Rule Evaluation Process

### Complete Flow Example

1. **Input Data**:
   ```python
   dvi = 0.25  # Vegetation increased
   dbi = -0.15 # Construction decreased  
   dwi = 0.35  # Water increased
   ```

2. **Rule String**:
   ```python
   rule = "dvi > 0.1 OR (dbi < 0.05 AND dwi > 0.2)"
   ```

3. **Variable Substitution**:
   ```python
   rule_eval = "0.25 > 0.1 OR (-0.15 < 0.05 AND 0.35 > 0.2)"
   ```

4. **SQL to Python Conversion**:
   ```python
   rule_eval = "0.25 > 0.1 or (-0.15 < 0.05 and 0.35 > 0.2)"
   ```

5. **Evaluation**:
   ```python
   result = eval("0.25 > 0.1 or (-0.15 < 0.05 and 0.35 > 0.2)")
   # result = True or (True and True) = True
   ```

### Evaluation Logic

```python
# Example evaluation breakdown
dvi = 0.25
dbi = -0.15  
dwi = 0.35

# Rule: "dvi > 0.1 OR (dbi < 0.05 AND dwi > 0.2)"
# Step 1: dvi > 0.1 → 0.25 > 0.1 → True
# Step 2: dbi < 0.05 → -0.15 < 0.05 → True  
# Step 3: dwi > 0.2 → 0.35 > 0.2 → True
# Step 4: (dbi < 0.05 AND dwi > 0.2) → (True AND True) → True
# Step 5: dvi > 0.1 OR (True) → True OR True → True
# Final Result: True
```

## How to Modify Rules

### Method 1: Direct Database Modification

```sql
-- Update a specific rule
UPDATE Thresholds 
SET vegetation_rule = 'dvi > 0.2 OR (dbi < 0.03 AND dwi < 0.1)'
WHERE threshold_short_description = 'Forest';

-- Add a new land type
INSERT INTO Thresholds (threshold_short_description, vegetation_rule, construction_rule, flooding_rule)
VALUES ('Wetland', 'dvi > 0.08 OR (dbi < 0.03 AND dwi < 0.15)', 'dvi < -0.06 OR dbi > 0.08', 'dvi < -0.10 OR dwi > 0.25');
```

### Method 2: Programmatic Modification

```python
def update_rule(land_type, rule_type, new_rule):
    """Update a rule for a specific land type"""
    conn = sqlite3.connect('sentinel_analysis.db')
    cursor = conn.cursor()
    
    if rule_type == 'vegetation':
        cursor.execute('UPDATE Thresholds SET vegetation_rule = ? WHERE threshold_short_description = ?', 
                      (new_rule, land_type))
    elif rule_type == 'construction':
        cursor.execute('UPDATE Thresholds SET construction_rule = ? WHERE threshold_short_description = ?', 
                      (new_rule, land_type))
    elif rule_type == 'flooding':
        cursor.execute('UPDATE Thresholds SET flooding_rule = ? WHERE threshold_short_description = ?', 
                      (new_rule, land_type))
    
    conn.commit()
    conn.close()

# Example usage
update_rule('Forest', 'vegetation', 'dvi > 0.2 OR (dbi < 0.02 AND dwi < 0.12)')
```

### Method 3: Configuration File Approach

Create a `rules_config.json` file:

```json
{
  "land_types": {
    "Forest": {
      "vegetation_rule": "dvi > 0.15 OR (dbi < 0.03 AND dwi < 0.15)",
      "construction_rule": "dvi < -0.12 OR dbi > 0.08", 
      "flooding_rule": "dvi < -0.15 OR dwi > 0.30"
    },
    "Urban Area": {
      "vegetation_rule": "dvi > 0.03 OR (dbi < 0.15 AND dwi < 0.03)",
      "construction_rule": "dvi < -0.02 OR dbi > 0.15",
      "flooding_rule": "dvi < -0.03 OR dwi > 0.12"
    }
  }
}
```

Then load and apply:

```python
import json

def load_rules_from_config(config_file):
    """Load rules from JSON configuration file"""
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    conn = sqlite3.connect('sentinel_analysis.db')
    cursor = conn.cursor()
    
    for land_type, rules in config['land_types'].items():
        cursor.execute('''
        UPDATE Thresholds 
        SET vegetation_rule = ?, construction_rule = ?, flooding_rule = ?
        WHERE threshold_short_description = ?
        ''', (rules['vegetation_rule'], rules['construction_rule'], 
              rules['flooding_rule'], land_type))
    
    conn.commit()
    conn.close()
```

## Examples and Use Cases

### Example 1: Agricultural Monitoring

**Scenario**: Monitor crop health and irrigation needs

```python
# Rules for Agriculture Wet Land
vegetation_rule = "dvi > 0.10 OR (dbi < 0.03 AND dwi < 0.12)"  # Healthy crops
construction_rule = "dvi < -0.08 OR dbi > 0.10"                # Farm development
flooding_rule = "dvi < -0.12 OR dwi > 0.30"                    # Irrigation/flooding
```

**Interpretation**:
- Vegetation increases when crops grow OR when there's no construction and adequate water
- Construction detected when vegetation decreases OR built-up areas increase
- Flooding detected when vegetation decreases OR water content increases significantly

### Example 2: Urban Development Monitoring

**Scenario**: Track urban expansion and environmental impact

```python
# Rules for Urban Area
vegetation_rule = "dvi > 0.03 OR (dbi < 0.15 AND dwi < 0.03)"  # Urban greening
construction_rule = "dvi < -0.02 OR dbi > 0.15"                # New construction
flooding_rule = "dvi < -0.03 OR dwi > 0.12"                    # Urban flooding
```

**Interpretation**:
- Vegetation increases with urban greening OR when construction/water are low
- Construction detected with vegetation loss OR built-up area increase
- Flooding detected with vegetation loss OR water increase

### Example 3: Forest Conservation

**Scenario**: Monitor deforestation and forest health

```python
# Rules for Forest
vegetation_rule = "dvi > 0.15 OR (dbi < 0.03 AND dwi < 0.15)"  # Forest growth
construction_rule = "dvi < -0.12 OR dbi > 0.08"                # Deforestation
flooding_rule = "dvi < -0.15 OR dwi > 0.30"                    # Forest flooding
```

**Interpretation**:
- Vegetation increases with forest growth OR when there's no construction and stable water
- Construction/deforestation detected with vegetation loss OR built-up increase
- Flooding detected with vegetation loss OR water increase

## Best Practices

### 1. Rule Design Guidelines

**Keep Rules Simple and Readable**:
```python
# Good: Clear and simple
"dvi > 0.1 AND dbi < 0.05"

# Avoid: Overly complex
"((dvi > 0.1) AND (dbi < 0.05)) OR ((dvi > 0.05) AND (dbi < 0.1) AND (dwi < 0.1))"
```

**Use Meaningful Thresholds**:
```python
# Good: Realistic thresholds based on satellite data characteristics
"dvi > 0.1"    # 10% vegetation change
"dbi > 0.05"   # 5% built-up change
"dwi > 0.2"    # 20% water change

# Avoid: Unrealistic thresholds
"dvi > 0.9"    # 90% change is unrealistic
"dbi < 0.001"  # 0.1% change is too sensitive
```

### 2. Testing Rules

**Test with Sample Data**:
```python
def test_rule(rule, test_cases):
    """Test a rule with various delta values"""
    for dvi, dbi, dwi, expected in test_cases:
        result = evaluate_rule(rule, dvi, dbi, dwi)
        print(f"Rule: {rule}")
        print(f"Input: dvi={dvi}, dbi={dbi}, dwi={dwi}")
        print(f"Expected: {expected}, Got: {result}")
        print(f"Match: {result == expected}\n")

# Test cases
test_cases = [
    (0.2, 0.1, 0.1, True),   # Should trigger
    (0.05, 0.1, 0.1, False), # Should not trigger
    (-0.1, 0.1, 0.1, True),  # Should trigger
]

test_rule("dvi > 0.1 OR dbi > 0.05", test_cases)
```

### 3. Rule Documentation

**Document Rule Logic**:
```python
# Document what each rule detects
rules = {
    'vegetation_rule': {
        'rule': 'dvi > 0.1 OR (dbi < 0.05 AND dwi < 0.1)',
        'description': 'Detects vegetation increase when NDVI increases significantly OR when there is no construction and low water content',
        'thresholds': {
            'dvi > 0.1': 'Significant vegetation increase',
            'dbi < 0.05': 'Low construction activity',
            'dwi < 0.1': 'Low water content'
        }
    }
}
```

## Troubleshooting

### Common Issues

**1. Rule Not Triggering**
```python
# Problem: Rule always returns False
# Check: Threshold values might be too high
"dvi > 0.5"  # Too high threshold

# Solution: Use realistic thresholds
"dvi > 0.1"  # More realistic
```

**2. Rule Always Triggering**
```python
# Problem: Rule always returns True
# Check: Threshold values might be too low
"dvi > 0.001"  # Too low threshold

# Solution: Use appropriate thresholds
"dvi > 0.05"  # More appropriate
```

**3. Syntax Errors**
```python
# Problem: Invalid syntax
"dvi > 0.1 AND dbi > 0.05"  # Missing quotes or wrong operators

# Solution: Check syntax carefully
"dvi > 0.1 AND dbi > 0.05"  # Correct syntax
```

**4. Evaluation Errors**
```python
# Problem: eval() fails
# Check: Allowed characters only
"dvi > 0.1; import os"  # Contains disallowed characters

# Solution: Use only allowed operators
"dvi > 0.1"  # Safe expression
```

### Debugging Tools

**Rule Testing Function**:
```python
def debug_rule(rule, dvi, dbi, dwi):
    """Debug a rule with detailed output"""
    print(f"Original rule: {rule}")
    
    # Step 1: Variable substitution
    rule_eval = rule.replace('dvi', str(dvi)).replace('dbi', str(dbi)).replace('dwi', str(dwi))
    print(f"After substitution: {rule_eval}")
    
    # Step 2: SQL to Python conversion
    rule_python = rule_eval.replace(' AND ', ' and ').replace(' OR ', ' or ')
    print(f"Python expression: {rule_python}")
    
    # Step 3: Evaluation
    try:
        result = eval(rule_python)
        print(f"Result: {result}")
        return result
    except Exception as e:
        print(f"Error: {e}")
        return False

# Example usage
debug_rule("dvi > 0.1 OR (dbi < 0.05 AND dwi < 0.1)", 0.2, 0.03, 0.08)
```

**Rule Validation Function**:
```python
def validate_rule(rule):
    """Validate rule syntax before storing"""
    try:
        # Test with dummy values
        test_rule = rule.replace('dvi', '0.1').replace('dbi', '0.1').replace('dwi', '0.1')
        test_rule = test_rule.replace(' AND ', ' and ').replace(' OR ', ' or ')
        eval(test_rule)
        return True, "Rule is valid"
    except Exception as e:
        return False, f"Rule error: {e}"

# Example usage
is_valid, message = validate_rule("dvi > 0.1 AND dbi < 0.05")
print(f"Valid: {is_valid}, Message: {message}")
```

## Conclusion

The Sentinel-2 Rule Engine provides a flexible and powerful way to define environmental change detection rules. By storing rules as strings and using Python's evaluation capabilities, users can easily modify detection logic without changing the core application code. The key to success is understanding the rule syntax, using realistic thresholds, and thoroughly testing rules with sample data.

Remember:
- Rules are evaluated as Python expressions
- Use realistic threshold values based on satellite data characteristics
- Test rules thoroughly before deployment
- Document rule logic for future maintenance
- Keep rules simple and readable

This system empowers users to customize environmental monitoring logic to their specific needs while maintaining the safety and reliability of the underlying application.



