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
    "indie-flower": "indie-flower.ttf",  # Handwriting style
    "kalam": "kalam.ttf",  # Handwriting style
    "cabin-sketch": "cabin-sketch.ttf",  # Sketch style
}


def resolve_font_path(
    preset: Literal["rounded", "maru", "kiwi", "noto", "indie-flower", "kalam", "cabin-sketch"] = "rounded",
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
                # If preset font not found, try kiwi.ttf first
                try:
                    assets_dir = Path(__file__).parent / "assets" / "fonts"
                    kiwi_font = assets_dir / "kiwi.ttf"
                    if kiwi_font.exists():
                        self.font = ImageFont.truetype(str(kiwi_font), font_size)
                    else:
                        raise FileNotFoundError()
                except (OSError, FileNotFoundError):
                    # Try common system fonts
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


class CaptionRenderer:
    """Renders captions with LINE stamp-like styles (band, bubble, none)"""
    
    # Default caption area height ratio (32% of canvas height)
    CAPTION_HEIGHT_RATIO = 0.32
    
    # Rounded rectangle corner radius
    ROUNDRECT_RADIUS = 12
    
    def __init__(
        self,
        font_path: Optional[str] = None,
        font_size_base: int = 24,
        preset: Literal["rounded", "maru", "kiwi", "noto", "indie-flower", "kalam", "cabin-sketch"] = "rounded"
    ):
        """Initialize caption renderer"""
        self.font_size_base = font_size_base
        self.font_path = font_path
        self.preset = preset
        # Base image size for font scaling (standard sticker size)
        self.base_image_height = 370
    
    def _contains_japanese(self, text: str) -> bool:
        """Check if text contains Japanese characters"""
        for char in text:
            code_point = ord(char)
            # Hiragana: 0x3040-0x309F
            # Katakana: 0x30A0-0x30FF
            # Kanji: 0x4E00-0x9FFF
            if (0x3040 <= code_point <= 0x309F or  # Hiragana
                0x30A0 <= code_point <= 0x30FF or  # Katakana
                0x4E00 <= code_point <= 0x9FFF):    # Kanji
                return True
        return False
    
    def _get_font(self, size: int, text: str = "") -> ImageFont.FreeTypeFont:
        """Load font with given size, auto-fallback to Japanese font if needed"""
        # Check if text contains Japanese
        needs_japanese = self._contains_japanese(text)
        
        try:
            if self.font_path:
                resolved_font = Path(self.font_path)
            else:
                # If Japanese detected and current font doesn't support it, use kiwi
                if needs_japanese and self.preset in ["indie-flower", "kalam", "cabin-sketch"]:
                    assets_dir = Path(__file__).parent / "assets" / "fonts"
                    resolved_font = assets_dir / "kiwi.ttf"
                else:
                    resolved_font = resolve_font_path(preset=self.preset)
            return ImageFont.truetype(str(resolved_font), size)
        except (FileNotFoundError, Exception):
            # Fallback to kiwi font if preset not found
            try:
                assets_dir = Path(__file__).parent / "assets" / "fonts"
                kiwi_font = assets_dir / "kiwi.ttf"
                if kiwi_font.exists():
                    return ImageFont.truetype(str(kiwi_font), size)
            except Exception:
                pass
            
            # Final fallback: load_default with larger size
            return ImageFont.load_default()
    
    def _measure_text(self, text: str, font: ImageFont.FreeTypeFont, width: int) -> Tuple[int, int, int]:
        """
        Measure text and calculate width/height for given font.
        Returns: (text_width, text_height, line_count)
        """
        temp_img = Image.new('RGBA', (1, 1))
        draw = ImageDraw.Draw(temp_img)
        bbox = draw.multiline_textbbox((0, 0), text, font=font)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        lines = len(text.split('\n'))
        return width, height, lines
    
    def wrap_text(
        self,
        text: str,
        max_width: int,
        font: ImageFont.FreeTypeFont,
        max_lines: int = 2
    ) -> str:
        """
        Wrap text by character count with width measurement.
        
        Args:
            text: Text to wrap
            max_width: Maximum pixel width
            font: Font to use for measurement
            max_lines: Maximum number of lines
            
        Returns:
            Wrapped text
        """
        # Respect existing newlines
        original_lines = text.split('\n')
        wrapped_lines = []
        
        for line in original_lines:
            if wrapped_lines and len(wrapped_lines) >= max_lines:
                break
            
            # Try to fit line
            if line == '':
                wrapped_lines.append(line)
                continue
            
            # Binary search for fit
            fitted_line = ''
            for i in range(len(line) + 1):
                test_text = line[:i]
                temp_img = Image.new('RGBA', (1, 1))
                draw = ImageDraw.Draw(temp_img)
                bbox = draw.textbbox((0, 0), test_text, font=font)
                if bbox[2] - bbox[0] <= max_width:
                    fitted_line = test_text
                else:
                    break
            
            if fitted_line:
                wrapped_lines.append(fitted_line)
                remaining = line[len(fitted_line):].lstrip()
                if remaining:
                    # Recursively wrap remaining text
                    more_lines = self.wrap_text(remaining, max_width, font, max_lines - len(wrapped_lines))
                    wrapped_lines.extend(more_lines.split('\n'))
            
            if len(wrapped_lines) >= max_lines:
                break
        
        return '\n'.join(wrapped_lines[:max_lines])
    
    def _auto_fit_text(
        self,
        text: str,
        available_width: int,
        available_height: int,
        max_lines: int,
        start_size: int = 64
    ) -> Tuple[str, ImageFont.FreeTypeFont, int]:
        """
        Auto-fit text by reducing font size until it fits.
        
        Returns: (wrapped_text, font, font_size)
        """
        for size in range(start_size, 14, -2):
            font = self._get_font(size, text)
            
            # Try to wrap text
            wrapped = self.wrap_text(text, available_width, font, max_lines)
            
            # Measure wrapped text
            text_width, text_height, line_count = self._measure_text(wrapped, font, available_width)
            
            # Check if fits
            if text_height <= available_height and line_count <= max_lines:
                return wrapped, font, size
        
        # Last resort: smallest size
        font = self._get_font(14, text)
        wrapped = self.wrap_text(text, available_width, font, max_lines)
        return wrapped, font, 14
    
    def _draw_rounded_rectangle(
        self,
        draw: ImageDraw.ImageDraw,
        bbox: Tuple[int, int, int, int],
        radius: int,
        fill: Tuple[int, int, int, int],
        outline: Optional[Tuple[int, int, int, int]] = None
    ) -> None:
        """Draw rounded rectangle with alpha"""
        x1, y1, x2, y2 = bbox
        r = radius
        
        # Draw four corners and connect edges
        points = [
            (x1 + r, y1),  # top left
            (x2 - r, y1),  # top right
            (x2, y1 + r),
            (x2, y2 - r),
            (x2 - r, y2),  # bottom right
            (x1 + r, y2),  # bottom left
            (x1, y2 - r),
            (x1, y1 + r),
        ]
        
        draw.polygon(points, fill=fill)
        
        # Draw corners
        draw.ellipse([x1, y1, x1 + r * 2, y1 + r * 2], fill=fill)
        draw.ellipse([x2 - r * 2, y1, x2, y1 + r * 2], fill=fill)
        draw.ellipse([x2 - r * 2, y2 - r * 2, x2, y2], fill=fill)
        draw.ellipse([x1, y2 - r * 2, x1 + r * 2, y2], fill=fill)
    
    def render_caption(
        self,
        image: Image.Image,
        text: str,
        style: Literal["band", "bubble", "none"] = "bubble",
        text_color: tuple[int, int, int] = (255, 255, 255),
        outline_color: tuple[int, int, int] = (0, 0, 0),
        outline_px: int = 6,
        padding_ratio: float = 0.06,
        max_lines: int = 2
    ) -> Image.Image:
        """
        Render caption on image with specified style.
        
        Args:
            image: Input RGBA image
            text: Caption text
            style: Caption style (band, bubble, none)
            text_color: Text color (R, G, B, default white)
            outline_color: Text outline color (R, G, B, default black)
            outline_px: Outline width in pixels
            padding_ratio: Padding ratio relative to image size
            max_lines: Maximum number of lines
            
        Returns:
            Image with caption
        """
        if not text or style == "none":
            return image
        
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        result = image.copy()
        
        # Calculate caption area dimensions (fixed at bottom)
        img_width, img_height = image.size
        
        # Scale font size based on image height (relative to base size)
        scale_factor = img_height / self.base_image_height
        scaled_font_size = max(32, int(self.font_size_base * scale_factor))
        
        caption_height = max(120, int(img_height * 0.2))  # At least 120px, max 20% height
        padding = int(12 * scale_factor)
        
        # Available width for text (with padding)
        available_width = img_width - (padding * 2)
        available_height = caption_height - (padding * 2)
        
        # Auto-fit text with scaled font size
        wrapped_text, font, final_size = self._auto_fit_text(
            text, available_width, available_height, max_lines, scaled_font_size
        )
        
        if not wrapped_text:
            return result
        
        # Measure final text
        text_width, text_height, _ = self._measure_text(wrapped_text, font, available_width)
        
        # Calculate text position for bottom area (centered horizontally, positioned in caption area)
        text_x = (img_width - text_width) // 2
        caption_y = max(img_height - caption_height - 20, int(img_height * 0.5))  # Start at least at 50% from top
        text_y = caption_y + padding
        
        if style == "band":
            result = self._render_band_caption(
                result, wrapped_text, font, text_x, text_y, 
                caption_y, caption_height, int(outline_px * scale_factor),
                text_color, outline_color
            )
        elif style == "bubble":
            result = self._render_bubble_caption(
                result, wrapped_text, font, text_x, text_y,
                text_width, text_height, padding, int(outline_px * scale_factor),
                text_color, outline_color
            )
        
        return result
    
    def _render_band_caption(
        self,
        image: Image.Image,
        text: str,
        font: ImageFont.FreeTypeFont,
        text_x: int,
        text_y: int,
        band_y: int,
        band_height: int,
        outline_px: int,
        text_color: tuple[int, int, int],
        outline_color: tuple[int, int, int]
    ) -> Image.Image:
        """Render band-style caption"""
        # Create layers
        result = image.copy()
        
        # Create background band layer (at the very bottom only)
        band_layer = Image.new('RGBA', result.size, (0, 0, 0, 0))
        band_draw = ImageDraw.Draw(band_layer)
        
        # Draw semi-transparent black band at bottom
        band_draw.rectangle(
            [0, text_y - 20, result.width, result.height],
            fill=(0, 0, 0, 100)
        )
        
        result = Image.alpha_composite(result, band_layer)
        
        # Create text layer
        text_layer = Image.new('RGBA', result.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_layer)
        
        # Draw text outline
        for adj_x in range(-outline_px, outline_px + 1):
            for adj_y in range(-outline_px, outline_px + 1):
                if abs(adj_x) + abs(adj_y) > outline_px:
                    continue
                draw.multiline_text(
                    (text_x + adj_x, text_y + adj_y),
                    text,
                    font=font,
                    fill=outline_color + (255,),
                    align='center'
                )
        
        # Draw main text
        draw.multiline_text(
            (text_x, text_y),
            text,
            font=font,
            fill=text_color + (255,),
            align='center'
        )
        
        result = Image.alpha_composite(result, text_layer)
        return result
    
    def _render_bubble_caption(
        self,
        image: Image.Image,
        text: str,
        font: ImageFont.FreeTypeFont,
        text_x: int,
        text_y: int,
        text_width: int,
        text_height: int,
        padding: int,
        outline_px: int,
        text_color: tuple[int, int, int],
        outline_color: tuple[int, int, int]
    ) -> Image.Image:
        """Render bubble-style caption with rounded rectangle at bottom"""
        result = image.copy()
        
        # Create shadow layer
        shadow_layer = Image.new('RGBA', result.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_layer)
        
        # Calculate bubble bounds with padding (fixed to bottom area)
        bubble_x1 = max(padding, text_x - padding)
        bubble_x2 = min(result.width - padding, text_x + text_width + padding)
        bubble_y1 = text_y - padding
        bubble_y2 = text_y + text_height + padding
        
        # Ensure bubble stays within bottom 40% of image
        max_bubble_y = int(result.height * 0.6)
        if bubble_y1 < max_bubble_y:
            # Move bubble down
            diff = max_bubble_y - bubble_y1
            bubble_y1 = max_bubble_y
            bubble_y2 += diff
            text_y += diff
        
        # Draw shadow (slightly offset)
        shadow_offset = 3
        self._draw_rounded_rectangle(
            shadow_draw,
            (bubble_x1 + shadow_offset, bubble_y1 + shadow_offset,
             bubble_x2 + shadow_offset, bubble_y2 + shadow_offset),
            self.ROUNDRECT_RADIUS,
            (0, 0, 0, 40)
        )
        
        result = Image.alpha_composite(result, shadow_layer)
        
        # Don't draw bubble background - just text with outline
        # Create text layer with outline
        text_layer = Image.new('RGBA', result.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_layer)
        
        # Draw text outline (thicker for contrast)
        for adj_x in range(-outline_px, outline_px + 1):
            for adj_y in range(-outline_px, outline_px + 1):
                if abs(adj_x) + abs(adj_y) > outline_px:
                    continue
                draw.multiline_text(
                    (text_x + adj_x, text_y + adj_y),
                    text,
                    font=font,
                    fill=outline_color + (255,),
                    align='center'
                )
        
        # Draw main text
        draw.multiline_text(
            (text_x, text_y),
            text,
            font=font,
            fill=text_color + (255,),
            align='center'
        )
        
        result = Image.alpha_composite(result, text_layer)
        return result
