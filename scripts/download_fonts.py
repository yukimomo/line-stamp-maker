#!/usr/bin/env python3
"""Download fonts for LINE Stamp Maker

Supports downloading Japanese fonts from Google Fonts and other sources.
Usage: python scripts/download_fonts.py [--force]
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from urllib.request import urlopen
from urllib.error import URLError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Font definitions
FONTS = {
    "noto-sans-jp.ttf": {
        "name": "Noto Sans JP",
        "urls": [
            "https://github.com/googlei18n/noto-cjk/raw/master/Sans/NotoSansCJK-Regular.ttc",
        ],
        "description": "Google Noto Sans JP - Unicode Japanese font",
        "fallback": True,
    },
    "rounded.ttf": {
        "name": "Rounded Font",
        "urls": [
            "https://github.com/google/fonts/raw/main/ofl/gelasio/Gelasio-Regular.ttf",
        ],
        "description": "Rounded serif font",
        "fallback": True,
    },
    "maru.ttf": {
        "name": "Maru Gothic",
        "urls": [
            "https://github.com/google/fonts/raw/main/ofl/m+/MPLUSRounded1c-Light.ttf",
        ],
        "description": "Rounded gothic font",
        "fallback": True,
    },
    "kiwi.ttf": {
        "name": "Kiwi Maru",
        "urls": [
            "https://github.com/google/fonts/raw/main/ofl/kiwimaru/KiwiMaru-Light.ttf",
        ],
        "description": "Kiwi Maru - Japanese rounded font from Google Fonts",
        "fallback": True,
    },
}


def get_fonts_dir() -> Path:
    """Get fonts directory path"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    fonts_dir = project_root / "line_stamp_maker" / "assets" / "fonts"
    return fonts_dir


def create_fonts_dir(fonts_dir: Path) -> None:
    """Create fonts directory if it doesn't exist"""
    fonts_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Fonts directory ready: {fonts_dir}")


def download_file(url: str, dest: Path, timeout: int = 30) -> bool:
    """Download a file from URL to destination"""
    try:
        logger.debug(f"  Downloading from: {url[:60]}...")
        
        response = urlopen(url, timeout=timeout)
        with open(dest, 'wb') as f:
            f.write(response.read())
        
        # Verify file size
        if dest.stat().st_size < 10000:  # Font should be > 10KB
            logger.warning(f"    Downloaded file seems too small: {dest.stat().st_size} bytes")
            return False
        
        logger.info(f"  ✓ Downloaded: {url.split('/')[-1]}")
        return True
    
    except URLError as e:
        logger.warning(f"    URLError: {e}")
        return False
    except Exception as e:
        logger.warning(f"    Error: {e}")
        return False


def download_font(
    font_name: str,
    font_path: Path,
    font_info: Dict,
    force: bool = False
) -> bool:
    """Download a font file"""
    
    if font_path.exists() and not force:
        # Check if file size is reasonable
        if font_path.stat().st_size > 10000:
            logger.info(f"✓ {font_name} already exists")
            return True
        else:
            logger.warning(f"⚠ {font_name} exists but seems corrupt, re-downloading...")
    
    logger.info(f"Downloading {font_name}...")
    
    # Try each URL
    for url in font_info.get("urls", []):
        if download_file(url, font_path):
            return True
    
    logger.error(f"✗ Failed to download {font_name}")
    return False


def test_font_file(font_path: Path) -> bool:
    """Test if font file is valid"""
    if not font_path.exists():
        return False
    
    size = font_path.stat().st_size
    return size > 10000


def show_status(fonts_dir: Path) -> None:
    """Show current font installation status"""
    logger.info("\nFont Status:")
    logger.info("=" * 60)
    
    all_good = True
    for font_name in FONTS.keys():
        font_path = fonts_dir / font_name
        if test_font_file(font_path):
            logger.info(f"  ✓ {font_name}: installed ({font_path.stat().st_size} bytes)")
        else:
            logger.info(f"  ✗ {font_name}: missing")
            all_good = False
    
    logger.info("=" * 60)
    return all_good


def show_instructions(fonts_dir: Path) -> None:
    """Show installation instructions"""
    print("\n" + "=" * 70)
    print("LINE Stamp Maker - Font Installation Instructions")
    print("=" * 70 + "\n")
    
    print("Font directory:", fonts_dir)
    print("\nSupported fonts:\n")
    
    for font_name, info in FONTS.items():
        status = "✓" if test_font_file(fonts_dir / font_name) else "✗"
        print(f"  {status} {font_name}: {info['description']}")
    
    print("\n" + "Manual Installation:")
    print("  1. Download fonts from Google Fonts: https://fonts.google.com")
    print("  2. Place TTF files in:", fonts_dir)
    print("\nRecommended fonts from Google Fonts:")
    print("  - Noto Sans JP: https://fonts.google.com/noto/specimen/Noto+Sans+JP")
    print("  - Kiwi Maru: https://fonts.google.com/specimen/Kiwi+Maru")
    print("  - M PLUS Rounded 1c: https://fonts.google.com/specimen/M+PLUS+Rounded+1c")
    print("  - Gelasio: https://fonts.google.com/specimen/Gelasio")
    print("\nPresets:")
    print("  - rounded: Use with --font-preset rounded")
    print("  - maru: Use with --font-preset maru (Maru Gothic)")
    print("  - kiwi: Use with --font-preset kiwi (Kiwi Maru)")
    print("  - noto: Use with --font-preset noto (Noto Sans JP)")
    print("\nUsage:")
    print("  python -m line_stamp_maker process --font-preset rounded \\")
    print("    --photos photos --mapping mapping.csv --output out")
    print("\n" + "=" * 70 + "\n")


def main(force: bool = False) -> int:
    """Main function"""
    fonts_dir = get_fonts_dir()
    
    logger.info("LINE Stamp Maker - Font Downloader\n")
    logger.info(f"Target directory: {fonts_dir}")
    
    # Create fonts directory
    create_fonts_dir(fonts_dir)
    
    # Try to download fonts
    downloaded = 0
    failed = 0
    
    for font_name, font_info in FONTS.items():
        font_path = fonts_dir / font_name
        if download_font(font_name, font_path, font_info, force=force):
            downloaded += 1
        else:
            failed += 1
    
    logger.info(f"\nDownload summary: {downloaded} downloaded, {failed} failed")
    
    # Show status
    all_good = show_status(fonts_dir)
    
    # Show instructions
    show_instructions(fonts_dir)
    
    if not all_good and failed > 0:
        logger.error("Some fonts could not be downloaded.")
        logger.error("Please manually download fonts from Google Fonts:")
        logger.error("  https://fonts.google.com")
        logger.error(f"And place them in: {fonts_dir}")
        return 1
    
    return 0


if __name__ == "__main__":
    force = "--force" in sys.argv or "-f" in sys.argv
    
    try:
        exit_code = main(force=force)
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
