        caption_style: Literal["band", "bubble", "none"] = Field("bubble", description="Caption style (band, bubble, none)")
        bubble_stroke: int = Field(3, description="Bubble stroke width (px)")
        bubble_shadow: bool = Field(True, description="Enable bubble shadow")
    outline_outer: int = Field(10, description="Outer outline thickness (px)")
    outline_inner: int = Field(4, description="Inner outline thickness (px)")
    shadow_enabled: bool = Field(True, description="Enable sticker shadow")
"""Configuration and Pydantic models for LINE stamp maker"""

from pathlib import Path
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


class ImageConfig(BaseModel):
    """Configuration for image processing"""
    # Mask smoothing parameters
    mask_feather: int = Field(3, description="Feather (px) for mask edge smoothing")
    mask_close_kernel: int = Field(5, description="Morphological close kernel size (px)")
    mask_open_kernel: int = Field(3, description="Morphological open kernel size (px)")
    # Outline settings
    outline_outer: int = Field(10, description="Outer outline thickness (px)")
    outline_inner: int = Field(4, description="Inner outline thickness (px)")
    shadow_enabled: bool = Field(True, description="Enable sticker shadow")

from pathlib import Path
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


class ImageConfig(BaseModel):
    """Configuration for image processing"""
    
    # Sticker dimensions (PNG with transparency)
    sticker_max_width: int = Field(370, description="Maximum width for sticker")
    sticker_max_height: int = Field(320, description="Maximum height for sticker")
    
    # Main image (240x240)
    main_width: int = Field(240, description="Width for main image")
    main_height: int = Field(240, description="Height for main image")
    
    # Tab image (96x74)
    tab_width: int = Field(96, description="Width for tab image")
    tab_height: int = Field(74, description="Height for tab image")
    
    # White border settings
    border_width: int = Field(8, description="White border width in pixels")
    
    # Shadow settings
    shadow_enabled: bool = Field(True, description="Whether to add shadow")
    shadow_color: tuple[int, int, int, int] = Field((0, 0, 0, 30), description="Shadow color (R, G, B, A)")
    shadow_offset: int = Field(3, description="Shadow offset in pixels")
    
    # Blur settings for mask
    blur_kernel_size: int = Field(5, description="Kernel size for mask blur")
    morphology_kernel_size: int = Field(3, description="Kernel size for morphology operations")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sticker_max_width": 370,
                "sticker_max_height": 320,
                "main_width": 240,
                "main_height": 240,
                "tab_width": 96,
                "tab_height": 74,
                "border_width": 8,
            }
        }


class TextConfig(BaseModel):
    """Configuration for text rendering"""
    
    # Font settings
    font_preset: Literal["rounded", "maru", "kiwi", "noto", "indie-flower", "kalam", "cabin-sketch"] = Field(
        "rounded", description="Font preset (rounded, maru, kiwi, noto, indie-flower, kalam, cabin-sketch)"
    )
    font_path: Optional[Path] = Field(
        None, description="Custom font file path (overrides preset)"
    )
    
    max_lines: int = Field(2, description="Maximum number of text lines")
    font_size: int = Field(24, description="Font size for text")
    text_color: tuple[int, int, int] = Field((255, 255, 255), description="Text color (R, G, B)")
    outline_color: tuple[int, int, int] = Field((0, 0, 0), description="Text outline color (R, G, B)")
    outline_width: int = Field(2, description="Text outline width in pixels")
    background_color: tuple[int, int, int, int] = Field((100, 100, 100, 200), description="Text background color (R, G, B, A)")
    background_height: int = Field(50, description="Height of text background area")
    padding: int = Field(10, description="Padding for text area")
    
    # Caption style settings
    caption_style: Literal["band", "bubble", "none"] = Field(
        "bubble", description="Caption style (band, bubble, none)"
    )
    bubble_stroke: int = Field(3, description="Bubble stroke width (px)")
    bubble_shadow: bool = Field(True, description="Enable bubble shadow")
    caption_text_color: tuple[int, int, int] = Field(
        (255, 255, 255), description="Caption text color (R, G, B) - white by default"
    )
    caption_outline_color: tuple[int, int, int] = Field(
        (0, 0, 0), description="Caption text outline color (R, G, B) - black by default"
    )
    caption_outline_px: int = Field(8, description="Caption text outline width in pixels")
    caption_padding_ratio: float = Field(
        0.06, description="Caption padding ratio (0.0-1.0) relative to canvas size"
    )
    caption_max_lines: int = Field(2, description="Maximum number of caption lines")


class ProcessingConfig(BaseModel):
    """Overall processing configuration"""
    
    image_config: ImageConfig = Field(default_factory=ImageConfig)
    text_config: TextConfig = Field(default_factory=TextConfig)
    
    # Input/Output paths
    photos_dir: Path = Field(Path("photos"), description="Directory containing input photos")
    mapping_file: Path = Field(Path("mapping.csv"), description="CSV file with filename and text mapping")
    output_dir: Path = Field(Path("out"), description="Output directory")
    
    # File resolution options
    ext_priority: str = Field(
        "heic,jpg,jpeg,png,webp",
        description="Priority order for file extensions (comma-separated, without dots)"
    )
    
    # Processing options
    detect_face: bool = Field(False, description="Whether to detect face for cropping")
    use_segmentation: bool = Field(True, description="Whether to use person segmentation")
    create_zip: bool = Field(True, description="Whether to create upload.zip")
    
    # Face detection parameters
    face_detection_confidence: float = Field(0.5, description="Confidence threshold for face detection")
    face_crop_margin: float = Field(0.2, description="Margin around face for cropping (0.0-1.0)")
    
    @field_validator('face_detection_confidence')
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Validate confidence is between 0 and 1"""
        if not 0 <= v <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        return v
    
    @field_validator('face_crop_margin')
    @classmethod
    def validate_margin(cls, v: float) -> float:
        """Validate margin is between 0 and 1"""
        if not 0 <= v <= 1:
            raise ValueError("Face crop margin must be between 0 and 1")
        return v
    
    def create_output_dirs(self) -> None:
        """Create necessary output directories"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "stickers").mkdir(exist_ok=True)
