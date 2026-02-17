"""Text rendering functionality for stickers"""

from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import textwrap


class TextRenderer:
    """Renders text on sticker images with background and outline"""
    
    def __init__(self, font_path: Optional[str] = None, font_size: int = 24):
        """
        Initialize text renderer.
        
        Args:
            font_path: Path to TTF font file (uses default if None)
            font_size: Font size in pixels
        """
        self.font_size = font_size
        
        # Try to load specified font, fall back to default
        try:
            if font_path:
                self.font = ImageFont.truetype(font_path, font_size)
            else:
                # Try common system fonts on Windows/Linux/Mac
                font_candidates = [
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                    "/System/Library/Fonts/Helvetica.ttc",
                    "C:\\Windows\\Fonts\\Arial.ttf",
                    "C:\\Windows\\Fonts\\arial.ttf",
                ]
                
                font_found = False
                for candidate in font_candidates:
                    try:
                        self.font = ImageFont.truetype(candidate, font_size)
                        font_found = True
                        break
                    except (OSError, FileNotFoundError):
                        continue
                
                if not font_found:
                    # Use default font if no TTF found
                    self.font = ImageFont.load_default()
        except Exception:
            self.font = ImageFont.load_default()
    
    def add_text_to_image(self, image: Image.Image, text: str,
                         text_color: Tuple[int, int, int] = (255, 255, 255),
                         outline_color: Tuple[int, int, int] = (0, 0, 0),
                         outline_width: int = 2,
                         background_color: Tuple[int, int, int, int] = (100, 100, 100, 200),
                         background_height: int = 50,
                         padding: int = 10) -> Image.Image:
        """
        Add text to bottom of image with background band and outline.
        
        Args:
            image: Input PIL Image (should have alpha channel for transparency)
            text: Text to render (up to 2 lines)
            text_color: Text color (R, G, B)
            outline_color: Text outline color (R, G, B)
            outline_width: Outline width in pixels
            background_color: Background color (R, G, B, A)
            background_height: Height of background band
            padding: Padding around text
            
        Returns:
            Image with text rendered
        """
        # Ensure image has alpha channel
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Create a copy to avoid modifying original
        result = image.copy()
        
        # Normalize text (max 2 lines)
        lines = text.strip().split('\n')[:2]
        text = '\n'.join(lines)
        
        if not text:
            return result
        
        # Create text layer
        text_layer = Image.new('RGBA', result.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_layer)
        
        # Get text bounding box to calculate size
        bbox = draw.multiline_textbbox((0, 0), text, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Calculate positions
        img_width = result.width
        text_x = (img_width - text_width) // 2
        text_y = result.height - background_height + (background_height - text_height) // 2
        
        # Draw text with outline (draw multiple times with offset)
        for adj_x in range(-outline_width, outline_width + 1):
            for adj_y in range(-outline_width, outline_width + 1):
                if abs(adj_x) + abs(adj_y) > outline_width:
                    continue
                draw.multiline_text(
                    (text_x + adj_x, text_y + adj_y),
                    text,
                    font=self.font,
                    fill=outline_color + (255,),
                    align='center'
                )
        
        # Draw main text
        draw.multiline_text(
            (text_x, text_y),
            text,
            font=self.font,
            fill=text_color + (255,),
            align='center'
        )
        
        # Create background layer
        background_layer = Image.new('RGBA', result.size, (0, 0, 0, 0))
        bg_draw = ImageDraw.Draw(background_layer)
        
        # Draw background band at bottom
        bg_draw.rectangle(
            [0, result.height - background_height, result.width, result.height],
            fill=background_color
        )
        
        # Composite layers
        result = Image.alpha_composite(result, background_layer)
        result = Image.alpha_composite(result, text_layer)
        
        return result
    
    def wrap_text(self, text: str, max_width: int = 30) -> str:
        """
        Wrap text to fit within max width.
        
        Args:
            text: Text to wrap
            max_width: Maximum characters per line
            
        Returns:
            Wrapped text
        """
        # Respect existing newlines
        lines = text.split('\n')
        wrapped_lines = []
        
        for line in lines:
            if len(line) > max_width:
                wrapped_lines.extend(textwrap.wrap(line, width=max_width))
            else:
                wrapped_lines.append(line)
        
        # Keep only first 2 lines
        return '\n'.join(wrapped_lines[:2])
    
    def get_text_bbox(self, text: str) -> Tuple[int, int, int, int]:
        """
        Get bounding box for text.
        
        Args:
            text: Text to measure
            
        Returns:
            (left, top, right, bottom)
        """
        # Create temporary image for measurement
        temp_img = Image.new('RGBA', (1, 1))
        draw = ImageDraw.Draw(temp_img)
        
        return draw.multiline_textbbox((0, 0), text, font=self.font)


def create_sticker_with_text(image: Image.Image, text: str, config) -> Image.Image:
    """
    Create complete sticker with text overlay.
    
    Args:
        image: Base image (RGBA)
        text: Text to overlay
        config: TextConfig instance
        
    Returns:
        Sticker with text
    """
    renderer = TextRenderer(font_size=config.font_size)
    
    return renderer.add_text_to_image(
        image,
        text,
        text_color=config.text_color,
        outline_color=config.outline_color,
        outline_width=config.outline_width,
        background_color=config.background_color,
        background_height=config.background_height,
        padding=config.padding
    )
