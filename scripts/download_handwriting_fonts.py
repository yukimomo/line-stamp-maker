#!/usr/bin/env python3
"""
Download handwriting-style fonts to assets/fonts directory

Available fonts:
- M+ 1m (www.mplus-fonts.org) - Japanese/English mix
- Indie Flower (Google Fonts) - Handwriting style English
- Kalam (Google Fonts) - Handwriting style
- Ubuntu (Google Fonts) - Modern

This script can be customized to download additional fonts.
"""

import os
import sys
from pathlib import Path
import urllib.request
import zipfile
import shutil

FONTS_DIR = Path(__file__).parent.parent / "line_stamp_maker" / "assets" / "fonts"
FONTS_DIR.mkdir(parents=True, exist_ok=True)

# Font downloads
FONTS = {
    # Modern handwriting style - Japanese compatible
    "kiwi": "Already installed - Noto Sans Japanese",
    
    # Handwriting style options (English only, but good for ASCII)
    "indie-flower": {
        "url": "https://github.com/google/fonts/raw/main/ofl/indieflower/IndieFlower-Regular.ttf",
        "filename": "indie-flower.ttf"
    },
    
    "kalam": {
        "url": "https://github.com/google/fonts/raw/main/ofl/kalam/Kalam-Regular.ttf",
        "filename": "kalam.ttf"
    },
    
    # Modern rounded style
    "cabin-sketch": {
        "url": "https://github.com/google/fonts/raw/main/ofl/cabinsketch/CabinSketch-Regular.ttf",
        "filename": "cabin-sketch.ttf"
    },
}

def download_font(name, info):
    """Download a single font"""
    if isinstance(info, str):
        print(f"  {name}: {info}")
        return
    
    try:
        filepath = FONTS_DIR / info["filename"]
        print(f"  Downloading {name}...", end=" ")
        
        urllib.request.urlretrieve(info["url"], filepath)
        file_size = filepath.stat().st_size / 1024  # KB
        print(f"OK ({file_size:.1f}KB)")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("LINE Stamp Maker - Handwriting Font Downloader")
    print("=" * 60)
    print()
    
    print("Available fonts:")
    for name, info in FONTS.items():
        if isinstance(info, str):
            print(f"  - {name}: {info}")
        else:
            print(f"  - {name}: {info['filename']}")
    
    print()
    print("Downloading fonts...")
    
    success_count = 0
    for name, info in FONTS.items():
        if download_font(name, info):
            success_count += 1
    
    print()
    print(f"Downloaded {success_count} fonts to {FONTS_DIR}")
    print()
    print("To use a handwriting font, run:")
    print("  python -m line_stamp_maker process --font-preset indie-flower")
    print("Or set --caption-text-color and --caption-outline-color for custom colors")
