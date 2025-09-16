# Sentinel-2 Rule Engine - Student Guide

## 🎯 Overview

This guide explains how the Sentinel-2 Rule Engine works and how students can easily modify rules to customize environmental change detection. The system uses string-based rules that are interpreted by Python at runtime, making it highly flexible and user-friendly.

## 📁 Files in This Project

| File | Purpose | For Students |
|------|---------|--------------|
| `README_RULE_ENGINE.md` | **Complete technical documentation** | 📚 **Start here for deep understanding** |
| `rule_engine_examples.py` | **Interactive examples and demos** | 🧪 **Run this to see how it works** |
| `rules_config_template.json` | **Template for easy rule modification** | ⚙️ **Use this to create custom rules** |
| `sentinel_analyzer.py` | Main analysis system | 🔧 Advanced users only |
| `demo_complete.py` | Complete system demo | 🎮 Try the full system |

## 🚀 Quick Start for Students

### Step 1: Understand the Basics
Read the **README_RULE_ENGINE.md** to understand:
- How rule strings work
- What variables mean (dvi, dbi, dwi)
- How Python interprets rules
- Safety mechanisms

### Step 2: Run the Examples
```bash
python rule_engine_examples.py
```
This will show you:
- How rules are evaluated step-by-step
- How to test rules with different data
- How to modify rules programmatically
- How to validate rule syntax

### Step 3: Create Your Own Rules
1. Copy `rules_config_template.json` to `my_rules.json`
2. Modify the rules in the `land_types` section
3. Test your rules using the example script
4. Load them into the system

## 🎯 Key Concepts

### Rule Variables
- **`dvi`** = Delta Vegetation Index (how much vegetation changed)
- **`dbi`** = Delta Built-up Index (how much construction changed)  
- **`dwi`** = Delta Water Index (how much water content changed)

### Rule Syntax
```python
# Simple rules
"dvi > 0.1"                    # Vegetation increased significantly
"dbi < 0.05"                   # Construction decreased slightly
"dwi > 0.2"                    # Water content increased moderately

# Complex rules
"dvi > 0.1 AND dbi < 0.05"     # Vegetation up AND construction down
"dvi < -0.1 OR dwi > 0.2"      # Vegetation down OR water up
"dvi > 0.1 OR (dbi < 0.05 AND dwi < 0.1)"  # Vegetation up OR (construction down AND water down)
```

### How Python Interprets Rules

1. **Variable Substitution**: `dvi` → `0.25`, `dbi` → `0.03`, `dwi` → `0.08`
2. **SQL to Python**: `AND` → `and`, `OR` → `or`
3. **Evaluation**: Python's `eval()` function executes the expression
4. **Result**: `True` or `False`

**Example**:
```
Rule: "dvi > 0.1 OR (dbi < 0.05 AND dwi < 0.1)"
Input: dvi=0.25, dbi=0.03, dwi=0.08

Step 1: "0.25 > 0.1 OR (0.03 < 0.05 AND 0.08 < 0.1)"
Step 2: "0.25 > 0.1 or (0.03 < 0.05 and 0.08 < 0.1)"
Step 3: True or (True and True) = True
```

## 🛠️ How to Modify Rules

### Method 1: JSON Configuration (Recommended for Students)

1. **Copy the template**:
   ```bash
   cp rules_config_template.json my_rules.json
   ```

2. **Edit the rules** in `my_rules.json`:
   ```json
   {
     "land_types": {
       "Forest": {
         "vegetation_rule": "dvi > 0.2 OR (dbi < 0.02 AND dwi < 0.12)",
         "construction_rule": "dvi < -0.15 OR dbi > 0.06",
         "flooding_rule": "dvi < -0.18 OR dwi > 0.35"
       }
     }
   }
   ```

3. **Test your rules**:
   ```python
   # Add this to rule_engine_examples.py
   demo.import_rules_from_json('my_rules.json')
   demo.demonstrate_rule_evaluation()
   ```

### Method 2: Direct Database Modification

```python
# Update a specific rule
cursor.execute('''
UPDATE Thresholds 
SET vegetation_rule = 'dvi > 0.2 OR (dbi < 0.02 AND dwi < 0.12)'
WHERE threshold_short_description = 'Forest'
''')
```

### Method 3: Programmatic Modification

```python
def update_rule(land_type, rule_type, new_rule):
    cursor.execute('''
    UPDATE Thresholds 
    SET {}_rule = ? 
    WHERE threshold_short_description = ?
    '''.format(rule_type), (new_rule, land_type))

# Example
update_rule('Forest', 'vegetation', 'dvi > 0.2 OR (dbi < 0.02 AND dwi < 0.12)')
```

## 🧪 Testing Your Rules

### Test with Sample Data
```python
# Test cases: (dvi, dbi, dwi, expected_result, description)
test_cases = [
    (0.25, 0.03, 0.08, True, "Strong vegetation increase"),
    (0.05, 0.03, 0.08, True, "Low vegetation but good conditions"),
    (0.25, 0.1, 0.15, True, "High vegetation despite poor conditions"),
    (0.05, 0.1, 0.15, False, "Low vegetation and poor conditions"),
]

rule = "dvi > 0.1 OR (dbi < 0.05 AND dwi < 0.1)"
demo.test_rule(rule, test_cases)
```

### Debug Rule Evaluation
```python
# See step-by-step evaluation
demo.debug_rule("dvi > 0.1 OR (dbi < 0.05 AND dwi < 0.1)", 0.25, 0.03, 0.08)
```

## 📊 Understanding Thresholds

### Realistic Threshold Guidelines

| Variable | Slight Change | Moderate Change | Deep Change |
|----------|---------------|-----------------|-------------|
| **dvi** | 0.05-0.15 | 0.15-0.30 | >0.30 |
| **dbi** | 0.05-0.15 | 0.15-0.30 | >0.30 |
| **dwi** | 0.10-0.20 | 0.20-0.40 | >0.40 |

### Example Rule Thresholds

```python
# Forest (strict conservation)
"dvi > 0.15 OR (dbi < 0.03 AND dwi < 0.15)"  # High vegetation threshold

# Urban Area (relaxed monitoring)  
"dvi > 0.03 OR (dbi < 0.15 AND dwi < 0.03)"  # Low vegetation threshold

# Agriculture (balanced)
"dvi > 0.10 OR (dbi < 0.03 AND dwi < 0.12)"  # Medium vegetation threshold
```

## 🎯 Common Use Cases

### 1. Forest Conservation
**Goal**: Detect early deforestation
```python
vegetation_rule = "dvi > 0.15 OR (dbi < 0.03 AND dwi < 0.15)"
construction_rule = "dvi < -0.12 OR dbi > 0.08"
```
**Logic**: Vegetation increases with forest growth OR when there's no construction and stable water.

### 2. Urban Development
**Goal**: Monitor city expansion
```python
vegetation_rule = "dvi > 0.03 OR (dbi < 0.15 AND dwi < 0.03)"
construction_rule = "dvi < -0.02 OR dbi > 0.15"
```
**Logic**: Vegetation increases with urban greening OR when construction/water are low.

### 3. Agricultural Monitoring
**Goal**: Track crop health and irrigation
```python
vegetation_rule = "dvi > 0.10 OR (dbi < 0.03 AND dwi < 0.12)"
flooding_rule = "dvi < -0.12 OR dwi > 0.30"
```
**Logic**: Vegetation increases with healthy crops OR when there's no construction and adequate water.

## ⚠️ Common Mistakes to Avoid

### 1. Unrealistic Thresholds
```python
# ❌ Too high - will never trigger
"dvi > 0.9"

# ❌ Too low - will always trigger  
"dvi > 0.001"

# ✅ Realistic
"dvi > 0.1"
```

### 2. Syntax Errors
```python
# ❌ Missing quotes
dvi > 0.1 AND dbi < 0.05

# ❌ Wrong operators
dvi > 0.1 && dbi < 0.05

# ✅ Correct
"dvi > 0.1 AND dbi < 0.05"
```

### 3. Incomplete Expressions
```python
# ❌ Incomplete
"dvi > 0.1 AND"

# ❌ Missing closing parenthesis
"dvi > 0.1 OR (dbi < 0.05"

# ✅ Complete
"dvi > 0.1 AND dbi < 0.05"
"dvi > 0.1 OR (dbi < 0.05 AND dwi < 0.1)"
```

## 🔧 Advanced Features

### Rule Validation
```python
# Check if rule syntax is valid
is_valid = demo.validate_rule("dvi > 0.1 AND dbi < 0.05")
print(f"Rule is valid: {is_valid}")
```

### Rule Export/Import
```python
# Export current rules to JSON
demo.export_rules_to_json('my_rules.json')

# Import rules from JSON
demo.import_rules_from_json('my_rules.json')
```

### Custom Land Types
```python
# Add new land type
cursor.execute('''
INSERT INTO Thresholds (threshold_short_description, vegetation_rule, construction_rule, flooding_rule)
VALUES (?, ?, ?, ?)
''', ('Custom Land', 'dvi > 0.12', 'dvi < -0.10', 'dvi < -0.12'))
```

## 🎓 Learning Exercises

### Exercise 1: Basic Rule Creation
Create rules for a new land type "Wetland" with these requirements:
- Vegetation increases when NDVI > 0.08 OR when construction is low AND water is stable
- Construction detected when vegetation decreases OR built-up areas increase
- Flooding detected when vegetation decreases OR water increases significantly

### Exercise 2: Rule Testing
Test your Wetland rules with these scenarios:
- Strong vegetation increase, low construction, stable water
- Vegetation decrease, high construction, high water
- Low vegetation, low construction, high water

### Exercise 3: Rule Optimization
Modify existing Forest rules to be more sensitive to early deforestation:
- Lower the vegetation threshold
- Increase construction sensitivity
- Adjust water thresholds

## 📚 Additional Resources

- **README_RULE_ENGINE.md**: Complete technical documentation
- **rule_engine_examples.py**: Interactive examples and demos
- **rules_config_template.json**: Template for easy rule creation
- **demo_complete.py**: Full system demonstration

## 🎉 Next Steps

1. **Read the documentation** in README_RULE_ENGINE.md
2. **Run the examples** with `python rule_engine_examples.py`
3. **Create your own rules** using the JSON template
4. **Test your rules** with the provided functions
5. **Integrate with the main system** for real analysis

## 💡 Tips for Success

- Start with simple rules and gradually add complexity
- Test your rules thoroughly with different data scenarios
- Use realistic thresholds based on satellite data characteristics
- Document your rule logic for future reference
- Keep rules readable and maintainable

Remember: The rule engine is designed to be flexible and user-friendly. Don't be afraid to experiment and modify rules to suit your specific environmental monitoring needs!

