"""Utility functions for image processing"""

import csv
from pathlib import Path
from typing import Optional
import numpy as np
from PIL import Image
import cv2


def fix_image_orientation(image: Image.Image) -> Image.Image:
    """
    Fix image orientation based on EXIF data.
    
    Args:
        image: PIL Image object
        
    Returns:
        Rotated image if needed
    """
    try:
        from PIL import ExifTags
        
        # Get EXIF data
        exif_data = image._getexif()
        if exif_data is None:
            return image
        
        # Find orientation tag
        for tag, value in exif_data.items():
            if ExifTags.TAGS.get(tag) == "Orientation":
                if value == 3:
                    return image.rotate(180, expand=True)
                elif value == 6:
                    return image.rotate(270, expand=True)
                elif value == 8:
                    return image.rotate(90, expand=True)
    except (AttributeError, KeyError, TypeError):
        pass
    
    return image


def center_crop(image: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    """
    Crop image from center.
    
    Args:
        image: Input image (numpy array)
        size: Target size (width, height)
        
    Returns:
        Cropped image
    """
    h, w = image.shape[:2]
    target_w, target_h = size
    
    # Calculate crop coordinates
    left = max(0, (w - target_w) // 2)
    top = max(0, (h - target_h) // 2)
    right = min(w, left + target_w)
    bottom = min(h, top + target_h)
    
    return image[top:bottom, left:right]


def resize_to_fit(image: Image.Image, max_width: int, max_height: int) -> Image.Image:
    """
    Resize image to fit within max dimensions while maintaining aspect ratio.
    
    Args:
        image: PIL Image object
        max_width: Maximum width
        max_height: Maximum height
        
    Returns:
        Resized image
    """
    image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    return image


def create_canvas_with_image(image: Image.Image, canvas_width: int, canvas_height: int, 
                             background_color: tuple[int, int, int, int] = (255, 255, 255, 0)) -> Image.Image:
    """
    Create a canvas and place image in center.
    
    Args:
        image: PIL Image object (may have alpha channel)
        canvas_width: Canvas width
        canvas_height: Canvas height
        background_color: Background color (R, G, B, A) for RGBA images
        
    Returns:
        Image on canvas
    """
    if image.mode == 'RGBA':
        canvas = Image.new('RGBA', (canvas_width, canvas_height), background_color)
    else:
        canvas = Image.new('RGB', (canvas_width, canvas_height), background_color[:3])
    
    x = (canvas_width - image.width) // 2
    y = (canvas_height - image.height) // 2
    
    if image.mode == 'RGBA':
        canvas.paste(image, (x, y), image)
    else:
        canvas.paste(image, (x, y))
    
    return canvas


def add_white_border(image: Image.Image, border_width: int) -> Image.Image:
    """
    Add white border to image with transparent background.
    
    Args:
        image: PIL Image object
        border_width: Border width in pixels
        
    Returns:
        Image with white border and transparent background
    """
    new_width = image.width + border_width * 2
    new_height = image.height + border_width * 2
    
    if image.mode == 'RGBA':
        # Create transparent background
        result = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
        
        # Create border layer with transparent background and white border
        from PIL import ImageDraw
        border_layer = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(border_layer)
        
        # Draw white filled rectangle for border
        for i in range(border_width):
            draw.rectangle(
                [(i, i), (new_width - 1 - i, new_height - 1 - i)],
                outline=(255, 255, 255, 255)
            )
        
        # Fill border area completely white
        draw.rectangle(
            [(0, 0), (new_width - 1, border_width - 1)],
            fill=(255, 255, 255, 255)
        )
        draw.rectangle(
            [(0, new_height - border_width), (new_width - 1, new_height - 1)],
            fill=(255, 255, 255, 255)
        )
        draw.rectangle(
            [(0, 0), (border_width - 1, new_height - 1)],
            fill=(255, 255, 255, 255)
        )
        draw.rectangle(
            [(new_width - border_width, 0), (new_width - 1, new_height - 1)],
            fill=(255, 255, 255, 255)
        )
        
        result = Image.alpha_composite(result, border_layer)
        result.paste(image, (border_width, border_width), image)
    else:
        border_image = Image.new('RGB', (new_width, new_height), (255, 255, 255))
        border_image.paste(image, (border_width, border_width))
        result = border_image
    
    return result


def add_shadow(image: Image.Image, shadow_color: tuple[int, int, int, int], 
               shadow_offset: int) -> Image.Image:
    """
    Add subtle shadow to image.
    
    Args:
        image: PIL Image object with alpha channel
        shadow_color: Shadow color (R, G, B, A)
        shadow_offset: Shadow offset in pixels
        
    Returns:
        Image with shadow
    """
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Create shadow layer
    shadow_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
    shadow_mask = Image.new('L', image.size, 0)
    
    # Get alpha channel
    alpha = image.split()[3] if image.mode == 'RGBA' else Image.new('L', image.size, 255)
    
    # Create shadow by darkening
    shadow_data = shadow_layer.load()
    alpha_data = alpha.load()
    
    for y in range(image.height):
        for x in range(image.width):
            if alpha_data[x, y] > 0:
                shadow_data[x, y] = shadow_color
    
    # Create output with shadow offset
    output = Image.new('RGBA', image.size, (255, 255, 255, 0))
    output.paste(shadow_layer, (shadow_offset, shadow_offset), shadow_layer)
    output.paste(image, (0, 0), image)
    
    return output


def pil_to_cv2(image: Image.Image) -> np.ndarray:
    """Convert PIL Image to OpenCV format"""
    if image.mode == 'RGBA':
        image = image.convert('RGB')
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def cv2_to_pil(image: np.ndarray) -> Image.Image:
    """Convert OpenCV image to PIL Image"""
    return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))


def find_largest_contour(mask: np.ndarray) -> Optional[np.ndarray]:
    """
    Find the largest contour in a binary mask.
    
    Args:
        mask: Binary mask (numpy array)
        
    Returns:
        Largest contour or None if no contours found
    """
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return None
    
    # Find largest contour
    largest_contour = max(contours, key=cv2.contourArea)
    return largest_contour


def apply_morphology(mask: np.ndarray, kernel_size: int, operation: str = 'close') -> np.ndarray:
    """
    Apply morphological operations to mask.
    
    Args:
        mask: Binary mask (numpy array)
        kernel_size: Kernel size
        operation: 'open', 'close', 'dilate', or 'erode'
        
    Returns:
        Processed mask
    """
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    
    if operation == 'open':
        return cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    elif operation == 'close':
        return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    elif operation == 'dilate':
        return cv2.dilate(mask, kernel, iterations=1)
    elif operation == 'erode':
        return cv2.erode(mask, kernel, iterations=1)
    else:
        return mask
