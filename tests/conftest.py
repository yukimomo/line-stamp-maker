"""Pytest configuration and shared fixtures"""

import sys
from pathlib import Path

# Add parent directory to path so we can import line_stamp_maker
sys.path.insert(0, str(Path(__file__).parent.parent))
