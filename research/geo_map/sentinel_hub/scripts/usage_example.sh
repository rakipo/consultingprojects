#!/bin/bash

# Sentinel Hub Land Monitoring - Usage Examples
# This script demonstrates how to use the monitoring system with required CLI parameters

echo "🛰️ Sentinel Hub Land Monitoring - Usage Examples"
echo "================================================"

# Check if config files exist
if [ ! -f "sentinel_hub_config.yml" ]; then
    echo "❌ Main config file not found: sentinel_hub_config.yml"
    echo "💡 Please ensure the main configuration file exists"
    exit 1
fi

if [ ! -f "sentinel_hub_user_config.yaml" ]; then
    echo "❌ User config file not found: sentinel_hub_user_config.yaml"
    echo "💡 Please ensure the user configuration file exists"
    exit 1
fi

echo "✅ Configuration files found"
echo ""

# Example 1: Basic usage with all modes
echo "📋 Example 1: Basic usage (all modes)"
echo "python claude_sentinel_hub_image_diff_v11.py --main-config sentinel_hub_config.yml --user-config sentinel_hub_user_config.yaml"
echo ""

# Example 2: Short form
echo "📋 Example 2: Short form"
echo "python claude_sentinel_hub_image_diff_v11.py -m sentinel_hub_config.yml -u sentinel_hub_user_config.yaml"
echo ""

# Example 3: Change detection only
echo "📋 Example 3: Change detection only"
echo "python claude_sentinel_hub_image_diff_v11.py -m sentinel_hub_config.yml -u sentinel_hub_user_config.yaml --mode detect"
echo ""

# Example 4: Visual comparison only
echo "📋 Example 4: Visual comparison only"
echo "python claude_sentinel_hub_image_diff_v11.py -m sentinel_hub_config.yml -u sentinel_hub_user_config.yaml --mode visual"
echo ""

# Example 5: With custom threshold
echo "📋 Example 5: With custom threshold"
echo "python claude_sentinel_hub_image_diff_v11.py -m sentinel_hub_config.yml -u sentinel_hub_user_config.yaml --threshold 0.15"
echo ""

# Example 6: With custom date ranges
echo "📋 Example 6: With custom date ranges"
echo "python claude_sentinel_hub_image_diff_v11.py -m sentinel_hub_config.yml -u sentinel_hub_user_config.yaml --before-start 2023-06-01 --before-end 2023-06-30 --after-start 2024-06-01 --after-end 2024-06-30"
echo ""

# Example 7: With custom output path
echo "📋 Example 7: With custom output path"
echo "python claude_sentinel_hub_image_diff_v11.py -m sentinel_hub_config.yml -u sentinel_hub_user_config.yaml --output my_comparison.png"
echo ""

echo "🚀 Running Example 1 (basic usage)..."
echo ""

# Run the basic example
python claude_sentinel_hub_image_diff_v11.py --main-config sentinel_hub_config.yml --user-config sentinel_hub_user_config.yaml

echo ""
echo "✅ Example completed!"
echo ""
echo "📁 Check the 'analysis_results' directory for output files"
echo "📖 See OUTPUT_FUNCTIONALITY_README.md for detailed documentation"
