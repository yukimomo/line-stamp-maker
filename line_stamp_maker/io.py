"""Image I/O functions with HEIC/HEIF support"""

from pathlib import Path
from typing import Optional
from PIL import Image


def open_image(path: Path | str) -> Image.Image:
    """
    Open an image file with support for multiple formats including HEIC/HEIF.
    
    Automatically applies EXIF orientation correction if available.
    
    Args:
        path: Path to image file
        
    Returns:
        PIL Image in RGBA mode
        
    Raises:
        FileNotFoundError: If file does not exist
        IOError: If file cannot be opened
        RuntimeError: If HEIC/HEIF file is provided but pillow-heif is not installed
    """
    path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {path}")
    
    suffix = path.suffix.lower()
    
    # Handle HEIC/HEIF formats
    if suffix in {".heic", ".heif"}:
        try:
            import pillow_heif
            # Register HEIF opener
            pillow_heif.register_heif_opener()
        except ImportError:
            raise RuntimeError(
                "HEIC/HEIF support requires pillow-heif. Install with:\n"
                "  pip install pillow-heif\n"
                "Or install with optional dependencies:\n"
                "  pip install -e \".[heic]\""
            )
    
    try:
        # Open image
        img = Image.open(path)
        
        # Apply EXIF orientation correction
        img = _apply_exif_orientation(img)
        
        # Convert to RGBA for consistency
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        
        return img
    
    except Exception as e:
        if isinstance(e, RuntimeError):
            raise
        raise IOError(f"Failed to open image {path}: {e}")


def _apply_exif_orientation(image: Image.Image) -> Image.Image:
    """
    Apply EXIF orientation correction to image.
    
    Args:
        image: PIL Image object
        
    Returns:
        Image rotated according to EXIF Orientation tag
    """
    try:
        from PIL import ExifTags
        
        # Try to get EXIF data
        exif_data = None
        try:
            exif_data = image._getexif()
        except AttributeError:
            pass
        
        if exif_data is None:
            return image
        
        # Find and apply orientation tag
        for tag, value in exif_data.items():
            tag_name = ExifTags.TAGS.get(tag, "Unknown")
            if tag_name == "Orientation":
                if value == 3:
                    image = image.rotate(180, expand=True)
                elif value == 6:
                    image = image.rotate(270, expand=True)
                elif value == 8:
                    image = image.rotate(90, expand=True)
                break
    
    except (AttributeError, KeyError, TypeError, IndexError):
        # EXIF data not available, return as-is
        pass
    
    return image


def get_supported_formats() -> list[str]:
    """
    Get list of supported image file extensions.
    
    Returns:
        List of supported file extensions (lowercase, with dots)
    """
    base_formats = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"]
    heic_formats = [".heic", ".heif"]
    return base_formats + heic_formats


def is_supported_image(path: Path | str) -> bool:
    """
    Check if a file is a supported image format.
    
    Args:
        path: Path to file
        
    Returns:
        True if file extension is in supported formats
    """
    path = Path(path)
    return path.suffix.lower() in get_supported_formats()
