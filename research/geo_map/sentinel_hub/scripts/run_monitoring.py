#!/usr/bin/env python3
"""
Simple wrapper script to run the Sentinel Hub Land Monitoring System
This script demonstrates various ways to use the CLI interface
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and display the result"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"📝 Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ Command executed successfully!")
        print("📤 Output:")
        print(result.stdout)
        if result.stderr:
            print("⚠️  Warnings/Errors:")
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code {e.returncode}")
        print("📤 Output:")
        print(e.stdout)
        print("❌ Errors:")
        print(e.stderr)
    except FileNotFoundError:
        print("❌ Python script not found. Make sure you're in the correct directory.")

def main():
    """Demonstrate various CLI usage examples"""
    
    script_name = "claude_sentinel_hub_image_diff_v11.py"
    
    if not os.path.exists(script_name):
        print(f"❌ Script {script_name} not found in current directory")
        print("Please run this script from the sentinel_hub directory")
        sys.exit(1)
    
    print("🚀 Sentinel Hub Land Monitoring System - CLI Examples")
    print("This script demonstrates various ways to use the monitoring system via command line")
    
    # Example 1: Basic usage with default configs
    run_command(
        [sys.executable, script_name],
        "Basic usage with default configuration files"
    )
    
    # Example 2: Change detection only
    run_command(
        [sys.executable, script_name, "--mode", "detect"],
        "Change detection only mode"
    )
    
    # Example 3: Visual comparison only
    run_command(
        [sys.executable, script_name, "--mode", "visual", "--output", "comparison.png"],
        "Visual comparison with custom output file"
    )
    
    # Example 4: Custom date ranges
    run_command(
        [sys.executable, script_name, 
         "--before-start", "2023-06-01", "--before-end", "2023-06-30",
         "--after-start", "2024-06-01", "--after-end", "2024-06-30",
         "--mode", "detect"],
        "Change detection with custom date ranges"
    )
    
    # Example 5: Custom threshold
    run_command(
        [sys.executable, script_name, 
         "--threshold", "0.05", "--mode", "detect"],
        "Change detection with custom threshold (0.05)"
    )
    
    # Example 6: Help
    run_command(
        [sys.executable, script_name, "--help"],
        "Display help information"
    )
    
    print(f"\n{'='*60}")
    print("📋 Summary of Available Commands:")
    print("="*60)
    print("Basic usage:")
    print(f"  python {script_name}")
    print(f"  python {script_name} --main-config config.yml --user-config coordinates.yaml")
    print()
    print("Modes:")
    print(f"  python {script_name} --mode detect    # Change detection only")
    print(f"  python {script_name} --mode visual    # Visual comparison only")
    print(f"  python {script_name} --mode continuous # Continuous monitoring setup")
    print(f"  python {script_name} --mode all       # All operations (default)")
    print()
    print("Custom parameters:")
    print(f"  python {script_name} --before-start 2023-01-01 --before-end 2023-01-31")
    print(f"  python {script_name} --after-start 2024-01-01 --after-end 2024-01-31")
    print(f"  python {script_name} --threshold 0.05")
    print(f"  python {script_name} --output my_comparison.png")
    print()
    print("Help:")
    print(f"  python {script_name} --help")
    print("="*60)

if __name__ == "__main__":
    main()
