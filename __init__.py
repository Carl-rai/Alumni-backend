"""Backend project package shim for deployment."""

from pathlib import Path
import sys

# Make the Django app packages importable when the process starts at the repo root.
PACKAGE_DIR = Path(__file__).resolve().parent
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))
