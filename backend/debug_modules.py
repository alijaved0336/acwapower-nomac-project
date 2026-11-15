#!/usr/bin/env python3
"""
Debug script to check Python module paths and Django setup
This helps debug import issues in Azure deployment
"""

import os
import sys
from pathlib import Path


def debug_python_environment():
    """Debug Python environment and module paths"""
    print("=" * 60)
    print("PYTHON ENVIRONMENT DEBUG")
    print("=" * 60)

    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Current working directory: {os.getcwd()}")
    print()

    print("Python path:")
    for i, path in enumerate(sys.path):
        print(f"  {i}: {path}")
    print()

    print("Environment variables:")
    django_vars = {
        k: v for k, v in os.environ.items() if "DJANGO" in k or "PYTHON" in k
    }
    for key, value in django_vars.items():
        print(f"  {key}: {value}")
    print()

    # Check for nomac module
    print("Module structure check:")
    current_dir = Path(os.getcwd())

    # Check if nomac directory exists
    nomac_dir = current_dir / "nomac"
    print(f"  nomac directory exists: {nomac_dir.exists()}")
    if nomac_dir.exists():
        print(f"  nomac directory path: {nomac_dir}")
        nomac_files = list(nomac_dir.glob("*.py"))
        print(f"  nomac Python files: {[f.name for f in nomac_files]}")

    # Check if manage.py exists
    manage_py = current_dir / "manage.py"
    print(f"  manage.py exists: {manage_py.exists()}")

    # Try to import nomac
    print("\nImport test:")
    try:
        import nomac

        print(f"  ✓ Successfully imported nomac from: {nomac.__file__}")
    except ImportError as e:
        print(f"  ✗ Failed to import nomac: {e}")

        # Try adding current directory to path
        print("  Trying to add current directory to Python path...")
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))
            try:
                import nomac

                print(
                    f"  ✓ Successfully imported nomac after adding to path: {nomac.__file__}"
                )
            except ImportError as e2:
                print(f"  ✗ Still failed to import nomac: {e2}")

    # Try to import Django and test settings
    print("\nDjango setup test:")
    try:
        import django

        print(f"  ✓ Django version: {django.get_version()}")

        # Set Django settings
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nomac.settings")
        django.setup()
        print("  ✓ Django setup successful")

        from django.conf import settings

        print(f"  ✓ Django settings loaded: {settings.DEBUG}")

    except Exception as e:
        print(f"  ✗ Django setup failed: {e}")
        import traceback

        print(f"  Traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    debug_python_environment()
