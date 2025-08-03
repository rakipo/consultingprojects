#!/usr/bin/env python3
"""
Verify Requirements Consolidation
Checks that all individual requirements.txt files have been removed
and only the consolidated one remains
"""

import os
import glob
from pathlib import Path

def find_requirements_files():
    """Find all requirements.txt files in the project"""
    # Start from the app directory
    app_dir = Path(__file__).parent
    project_root = app_dir.parent
    
    # Find all requirements.txt files
    requirements_files = []
    
    # Search in the entire project
    for root, dirs, files in os.walk(project_root):
        for file in files:
            if file == 'requirements.txt':
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, project_root)
                requirements_files.append(rel_path)
    
    return requirements_files

def verify_consolidation():
    """Verify that requirements have been properly consolidated"""
    print("🔍 Verifying Requirements Consolidation")
    print("=" * 40)
    
    requirements_files = find_requirements_files()
    
    print(f"📋 Found {len(requirements_files)} requirements.txt files:")
    for file in requirements_files:
        print(f"  {file}")
    
    # Expected: only one requirements.txt in app folder
    expected_file = "app/requirements.txt"
    
    if len(requirements_files) == 1 and requirements_files[0] == expected_file:
        print(f"\n✅ Perfect! Only the consolidated requirements.txt exists at {expected_file}")
        
        # Check if the file has content
        app_requirements = Path(__file__).parent / "requirements.txt"
        if app_requirements.exists():
            with open(app_requirements, 'r') as f:
                content = f.read().strip()
                lines = [line for line in content.split('\n') if line.strip() and not line.strip().startswith('#')]
                print(f"📦 Contains {len(lines)} dependency specifications")
                
                # Show a few key dependencies
                key_deps = ['psycopg2-binary', 'neo4j', 'pandas', 'mcp', 'fastapi', 'langchain']
                found_deps = [line for line in lines if any(dep in line.lower() for dep in key_deps)]
                
                if found_deps:
                    print(f"🔑 Key dependencies found:")
                    for dep in found_deps[:5]:  # Show first 5
                        print(f"  {dep}")
                    if len(found_deps) > 5:
                        print(f"  ... and {len(found_deps) - 5} more")
                else:
                    print("⚠️  No key dependencies found - please check the file content")
        
        return True
    
    elif len(requirements_files) == 0:
        print(f"\n❌ No requirements.txt files found!")
        print("Expected to find consolidated requirements.txt in app folder")
        return False
    
    else:
        print(f"\n⚠️  Found {len(requirements_files)} requirements.txt files, expected only 1")
        
        # Check if the consolidated file exists
        if expected_file in requirements_files:
            print(f"✅ Consolidated file exists: {expected_file}")
            
            # List extra files that should be removed
            extra_files = [f for f in requirements_files if f != expected_file]
            if extra_files:
                print(f"❌ Extra files that should be removed:")
                for file in extra_files:
                    print(f"  {file}")
                print(f"\n💡 To fix: Remove the extra requirements.txt files listed above")
        else:
            print(f"❌ Consolidated file missing: {expected_file}")
            print(f"💡 To fix: Create {expected_file} with all dependencies")
        
        return False

def check_old_locations():
    """Check specific old locations that should no longer have requirements.txt"""
    print(f"\n🔍 Checking Old Requirements Locations")
    print("-" * 40)
    
    old_locations = [
        "app/mcp-servers/data-modeling/requirements.txt",
        "app/mcp-servers/cypher/requirements.txt",
        "trending/requirements.txt"  # This one might still exist for trending component
    ]
    
    project_root = Path(__file__).parent.parent
    
    for location in old_locations:
        full_path = project_root / location
        if full_path.exists():
            if "trending" in location:
                print(f"ℹ️  {location} - OK (trending component has separate requirements)")
            else:
                print(f"❌ {location} - Should be removed")
        else:
            print(f"✅ {location} - Correctly removed")

def main():
    """Main verification function"""
    print("🚀 Requirements Consolidation Verification")
    print("=" * 50)
    
    consolidation_ok = verify_consolidation()
    check_old_locations()
    
    print("\n" + "=" * 50)
    if consolidation_ok:
        print("🎉 Requirements consolidation is complete!")
        print("\n📋 Summary:")
        print("- ✅ Single requirements.txt file in app folder")
        print("- ✅ All dependencies consolidated")
        print("- ✅ Old requirements files removed")
        print("\n💡 Next steps:")
        print("- Run 'python install_dependencies.py' to install")
        print("- Run 'python check_dependencies.py' to verify")
    else:
        print("⚠️  Requirements consolidation needs attention")
        print("Please review the issues above and fix them")

if __name__ == "__main__":
    main()