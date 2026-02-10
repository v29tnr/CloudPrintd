"""
Quick test script to verify CloudPrintd setup
Run this to check if everything is configured correctly
"""

import sys
import subprocess
import importlib.util

REQUIRED_PACKAGES = [
    'fastapi',
    'uvicorn',
    'pydantic',
    'httpx',
    'aiofiles',
]

OPTIONAL_PACKAGES = [
    'cups',
]

def check_python_version():
    """Check Python version."""
    print("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 11:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} (3.11+ required)")
        return False

def check_package(package_name):
    """Check if a package is installed."""
    spec = importlib.util.find_spec(package_name)
    return spec is not None

def check_required_packages():
    """Check all required packages."""
    print("\nChecking required packages...")
    all_installed = True
    
    for package in REQUIRED_PACKAGES:
        installed = check_package(package)
        status = "✓" if installed else "✗"
        print(f"{status} {package}")
        if not installed:
            all_installed = False
    
    return all_installed

def check_optional_packages():
    """Check optional packages."""
    print("\nChecking optional packages...")
    
    for package in OPTIONAL_PACKAGES:
        installed = check_package(package)
        status = "✓" if installed else "⚠"
        print(f"{status} {package} {'(available)' if installed else '(not available - CUPS printer support disabled)'}")

def check_config_files():
    """Check if configuration files exist."""
    print("\nChecking configuration files...")
    import os
    
    files = [
        'config/defaults.json',
        'config/printers.defaults.json',
        'config/update.json',
    ]
    
    all_exist = True
    for file in files:
        exists = os.path.exists(file)
        status = "✓" if exists else "✗"
        print(f"{status} {file}")
        if not exists:
            all_exist = False
    
    return all_exist

def check_app_structure():
    """Check if application structure is correct."""
    print("\nChecking application structure...")
    import os
    
    required_files = [
        'app/main.py',
        'app/models.py',
        'app/config.py',
        'app/security.py',
        'app/printer.py',
        'update_manager/manager.py',
    ]
    
    all_exist = True
    for file in required_files:
        exists = os.path.exists(file)
        status = "✓" if exists else "✗"
        print(f"{status} {file}")
        if not exists:
            all_exist = False
    
    return all_exist

def test_imports():
    """Test if we can import the main modules."""
    print("\nTesting module imports...")
    
    modules = [
        ('app.main', 'FastAPI app'),
        ('app.models', 'Pydantic models'),
        ('app.config', 'Configuration manager'),
        ('update_manager.manager', 'Update manager'),
    ]
    
    all_imported = True
    for module, description in modules:
        try:
            __import__(module)
            print(f"✓ {description}")
        except Exception as e:
            print(f"✗ {description}: {e}")
            all_imported = False
    
    return all_imported

def main():
    """Run all checks."""
    print("=" * 50)
    print("CloudPrintd Setup Verification")
    print("=" * 50)
    
    checks = [
        ("Python version", check_python_version),
        ("Required packages", check_required_packages),
        ("Configuration files", check_config_files),
        ("Application structure", check_app_structure),
        ("Module imports", test_imports),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"Error during {name}: {e}")
            results.append((name, False))
    
    # Optional checks (don't affect overall result)
    check_optional_packages()
    
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    
    all_passed = all(result for _, result in results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("✓ All checks passed! CloudPrintd is ready to run.")
        print("\nTo start the server:")
        print("  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        return 0
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        print("\nTo install missing packages:")
        print("  pip install -r requirements.txt")
        return 1

if __name__ == '__main__':
    sys.exit(main())
