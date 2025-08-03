#!/usr/bin/env python3
"""
Dependency Checker
Checks for dependency conflicts and compatibility issues
"""

import subprocess
import sys
import pkg_resources
from typing import Dict, List, Tuple

def get_installed_packages() -> Dict[str, str]:
    """Get all installed packages and their versions"""
    installed = {}
    try:
        for dist in pkg_resources.working_set:
            installed[dist.project_name.lower()] = dist.version
    except Exception as e:
        print(f"Error getting installed packages: {e}")
    return installed

def parse_requirements() -> List[Tuple[str, str]]:
    """Parse requirements.txt file"""
    requirements = []
    try:
        with open('requirements.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Simple parsing - handle >= requirements
                    if '>=' in line:
                        name, version = line.split('>=')
                        requirements.append((name.strip(), version.strip()))
                    elif '==' in line:
                        name, version = line.split('==')
                        requirements.append((name.strip(), version.strip()))
                    else:
                        requirements.append((line.strip(), 'any'))
    except FileNotFoundError:
        print("❌ requirements.txt not found")
    return requirements

def check_compatibility():
    """Check for dependency compatibility issues"""
    print("🔍 Checking Dependency Compatibility")
    print("=" * 40)
    
    installed = get_installed_packages()
    requirements = parse_requirements()
    
    print(f"📦 Found {len(installed)} installed packages")
    print(f"📋 Found {len(requirements)} requirements")
    
    # Check if required packages are installed
    missing = []
    version_mismatches = []
    satisfied = []
    
    for req_name, req_version in requirements:
        req_name_lower = req_name.lower()
        
        if req_name_lower not in installed:
            missing.append(req_name)
        else:
            installed_version = installed[req_name_lower]
            if req_version != 'any':
                try:
                    # Simple version comparison (not perfect but good enough)
                    if req_version.replace('.', '').isdigit() and installed_version.replace('.', '').isdigit():
                        req_parts = [int(x) for x in req_version.split('.')]
                        inst_parts = [int(x) for x in installed_version.split('.')]
                        
                        # Pad shorter version with zeros
                        max_len = max(len(req_parts), len(inst_parts))
                        req_parts.extend([0] * (max_len - len(req_parts)))
                        inst_parts.extend([0] * (max_len - len(inst_parts)))
                        
                        if inst_parts >= req_parts:
                            satisfied.append((req_name, installed_version, req_version))
                        else:
                            version_mismatches.append((req_name, installed_version, req_version))
                    else:
                        satisfied.append((req_name, installed_version, req_version))
                except:
                    satisfied.append((req_name, installed_version, req_version))
            else:
                satisfied.append((req_name, installed_version, 'any'))
    
    # Report results
    print(f"\n✅ Satisfied requirements: {len(satisfied)}")
    for name, installed_ver, req_ver in satisfied[:5]:  # Show first 5
        print(f"  {name}: {installed_ver} (required: {req_ver})")
    if len(satisfied) > 5:
        print(f"  ... and {len(satisfied) - 5} more")
    
    if missing:
        print(f"\n❌ Missing packages: {len(missing)}")
        for name in missing:
            print(f"  {name}")
    
    if version_mismatches:
        print(f"\n⚠️  Version mismatches: {len(version_mismatches)}")
        for name, installed_ver, req_ver in version_mismatches:
            print(f"  {name}: {installed_ver} (required: >={req_ver})")
    
    # Check for potential conflicts
    print(f"\n🔍 Checking for potential conflicts...")
    
    # Known conflicting packages
    potential_conflicts = [
        (['langchain', 'langgraph'], "LangChain ecosystem packages"),
        (['fastapi', 'uvicorn'], "FastAPI and ASGI server"),
        (['psycopg2', 'psycopg2-binary'], "PostgreSQL drivers"),
    ]
    
    conflicts_found = []
    for conflict_group, description in potential_conflicts:
        installed_from_group = [pkg for pkg in conflict_group if pkg.lower() in installed]
        if len(installed_from_group) > 1:
            conflicts_found.append((installed_from_group, description))
    
    if conflicts_found:
        print("⚠️  Potential conflicts detected:")
        for packages, description in conflicts_found:
            print(f"  {description}: {', '.join(packages)}")
    else:
        print("✅ No obvious conflicts detected")
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"  ✅ Satisfied: {len(satisfied)}")
    print(f"  ❌ Missing: {len(missing)}")
    print(f"  ⚠️  Version issues: {len(version_mismatches)}")
    print(f"  🔍 Potential conflicts: {len(conflicts_found)}")
    
    if missing or version_mismatches:
        print(f"\n💡 Recommendation: Run 'python install_dependencies.py' to fix issues")
        return False
    else:
        print(f"\n🎉 All dependencies look good!")
        return True

def check_import_health():
    """Test importing critical modules"""
    print(f"\n🧪 Testing Critical Imports")
    print("=" * 30)
    
    critical_modules = [
        ('psycopg2', 'PostgreSQL driver'),
        ('neo4j', 'Neo4j driver'),
        ('pandas', 'Data processing'),
        ('yaml', 'YAML configuration'),
        ('fastapi', 'Web framework'),
        ('pydantic', 'Data validation'),
        ('mcp', 'MCP framework'),
    ]
    
    failed_imports = []
    
    for module, description in critical_modules:
        try:
            __import__(module)
            print(f"✅ {description} ({module})")
        except ImportError as e:
            print(f"❌ {description} ({module}): {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n❌ Failed imports: {', '.join(failed_imports)}")
        return False
    else:
        print(f"\n✅ All critical modules import successfully!")
        return True

def main():
    """Main checker function"""
    print("🔍 Boomer Living TV App - Dependency Health Check")
    print("=" * 50)
    
    compatibility_ok = check_compatibility()
    import_ok = check_import_health()
    
    print("\n" + "=" * 50)
    if compatibility_ok and import_ok:
        print("🎉 All dependency checks passed!")
        print("Your environment is ready for the Boomer Living TV App.")
    else:
        print("⚠️  Some issues were found.")
        print("Please run 'python install_dependencies.py' to resolve them.")
        sys.exit(1)

if __name__ == "__main__":
    main()