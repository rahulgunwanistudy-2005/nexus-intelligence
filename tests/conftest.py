"""
Pytest configuration.
Adds the project root to sys.path so imports work from any directory.
"""
import sys
from pathlib import Path

# Make sure 'src' is importable from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

# Create data dirs if they don't exist (needed for _boot_clear in main.py)
for d in ["data/raw", "data/processed"]:
    Path(d).mkdir(parents=True, exist_ok=True)