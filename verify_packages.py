#!/usr/bin/env python3
"""
Package Verification Script
Checks if all required packages are installed correctly
"""

import sys

def check_package(package_name, import_name=None, required=True):
    """Check if a package is installed and importable"""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        status = "✅"
        message = f"{status} {package_name}"
        return True, message
    except ImportError:
        status = "❌" if required else "⚠️"
        req_text = "REQUIRED" if required else "OPTIONAL"
        message = f"{status} {package_name} - {req_text} - NOT INSTALLED"
        return not required, message

def main():
    print("=" * 60)
    print("AI Database View Generator - Package Verification")
    print("=" * 60)
    print()
    
    # Core packages (required)
    print("Core Packages (Required):")
    print("-" * 60)
    
    core_packages = [
        ("pydantic", "pydantic", True),
        ("requests", "requests", True),
        ("networkx", "networkx", True),
        ("pandas", "pandas", True),
        ("numpy", "numpy", True),
        ("streamlit", "streamlit", True),
        ("openpyxl", "openpyxl", True),
    ]
    
    core_ok = True
    for pkg_name, import_name, required in core_packages:
        ok, msg = check_package(pkg_name, import_name, required)
        print(msg)
        core_ok = core_ok and ok
    
    print()
    
    # Optional packages
    print("Optional Packages:")
    print("-" * 60)
    
    optional_packages = [
        ("litellm", "litellm", False),
        ("psycopg2-binary", "psycopg2", False),
        ("plotly", "plotly", False),
        ("python-dotenv", "dotenv", False),
        ("pytest", "pytest", False),
    ]
    
    for pkg_name, import_name, required in optional_packages:
        ok, msg = check_package(pkg_name, import_name, required)
        print(msg)
    
    print()
    print("=" * 60)
    
    # Python version check
    py_version = sys.version_info
    print(f"Python Version: {py_version.major}.{py_version.minor}.{py_version.micro}")
    
    if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 8):
        print("❌ Python 3.8 or higher required")
        print()
        return False
    else:
        print("✅ Python version OK")
    
    print()
    
    # Test imports from project
    print("Project Modules:")
    print("-" * 60)
    
    project_modules = [
        "schema_parser",
        "llm_interface",
        "models",
        "validation",
        "pipeline",
        "config",
    ]
    
    modules_ok = True
    for module in project_modules:
        try:
            __import__(module)
            print(f"✅ {module}.py")
        except ImportError as e:
            print(f"❌ {module}.py - NOT FOUND")
            modules_ok = False
        except Exception as e:
            print(f"⚠️  {module}.py - ERROR: {str(e)[:50]}")
            modules_ok = False
    
    print()
    print("=" * 60)
    
    # Final result
    if core_ok and modules_ok:
        print("✅ ALL REQUIRED PACKAGES AND MODULES INSTALLED")
        print()
        print("You can now run:")
        print("  • streamlit run app.py")
        print("  • python cli.py --schema demo_schema.json --num-views 3")
        print()
        return True
    elif core_ok:
        print("⚠️  CORE PACKAGES OK, BUT SOME PROJECT MODULES MISSING")
        print()
        print("Make sure you're in the project directory.")
        print()
        return False
    else:
        print("❌ SOME REQUIRED PACKAGES ARE MISSING")
        print()
        print("Install missing packages with:")
        print("  pip install -r requirements.txt")
        print()
        print("Or install minimal packages:")
        print("  pip install -r requirements-minimal.txt")
        print()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
