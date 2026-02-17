"""Text rendering functionality for stickers"""

from pathlib import Path
from typing import Optional, Tuple, Literal
from PIL import Image, ImageDraw, ImageFont
import textwrap


# Font preset mappings
FONT_PRESETS = {
    "rounded": "rounded.ttf",
    "maru": "maru.ttf",  # Maru Gothic
    "kiwi": "kiwi.ttf",   # Kiwi Maru
    "noto": "noto-sans-jp.ttf",  # Noto Sans JP
}


def resolve_font_path(
    preset: Literal["rounded", "maru", "kiwi", "noto"] = "rounded",
    custom_path: Optional[Path] = None
) -> Path:
    """
    Resolve font file path from preset or custom path.
    
    Args:
        preset: Font preset name (rounded, maru, kiwi, noto)
        custom_path: Custom font file path (overrides preset)
        
    Returns:
        Path to font file
        
    Raises:
        FileNotFoundError: If font file not found
        ValueError: If preset is invalid
    """
    # If custom path provided, use it
    if custom_path:
        custom_path = Path(custom_path)
        if not custom_path.exists():
            raise FileNotFoundError(
                f"Custom font file not found: {custom_path}\n"
                "Please provide a valid path to a TTF font file."
            )
        return custom_path
    
    # Validate preset
    if preset not in FONT_PRESETS:
        raise ValueError(
            f"Invalid font preset '{preset}'. "
            f"Valid options: {', '.join(FONT_PRESETS.keys())}"
        )
    
    # Resolve bundled font file
    assets_dir = Path(__file__).parent / "assets" / "fonts"
    font_file = assets_dir / FONT_PRESETS[preset]
    
    if not font_file.exists():
        raise FileNotFoundError(
            f"Font file missing: {FONT_PRESETS[preset]}\n"
            f"Location: {font_file}\n"
            "To download fonts, run: python -m line_stamp_maker fonts-download\n"
            "Or manually place font files in line_stamp_maker/assets/fonts/"
        )
    
    return font_file


class TextRenderer:
    """Renders text on sticker images with background and outline"""
    
    def __init__(
        self,
        font_path: Optional[str] = None,
        font_size: int = 24,
        preset: Literal["rounded", "maru", "kiwi", "noto"] = "rounded"
    ):
        """
        Initialize text renderer.
        
        Args:
            font_path: Path to TTF font file (overrides preset if provided)
            font_size: Font size in pixels
            preset: Font preset to use if font_path not provided
        """
        self.font_size = font_size
        
        # Try to load specified font, fall back to default
        try:
            # Try to load font from provided path or preset
            try:
                if font_path:
                    resolved_font = Path(font_path)
                else:
                    resolved_font = resolve_font_path(preset=preset)
                self.font = ImageFont.truetype(str(resolved_font), font_size)
            except FileNotFoundError:
                # If preset font not found, try common system fonts
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
    renderer = TextRenderer(
        font_path=str(config.font_path) if config.font_path else None,
        font_size=config.font_size,
        preset=config.font_preset
    )
    
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
