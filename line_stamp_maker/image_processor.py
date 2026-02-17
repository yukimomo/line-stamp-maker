"""Main image processing pipeline"""

from pathlib import Path
from typing import Optional, Tuple
import cv2
from PIL import Image
import numpy as np

from .config import ProcessingConfig, ImageConfig
from .face_detection import FaceDetector
from .segmentation import PersonSegmenter
from .text_renderer import TextRenderer, create_sticker_with_text
from . import utils


class ImageProcessor:
    """Main image processing pipeline for creating LINE stickers"""
    
    def __init__(self, config: ProcessingConfig):
        """
        Initialize image processor.
        
        Args:
            config: ProcessingConfig instance
        """
        self.config = config
        self.image_config = config.image_config
        self.text_config = config.text_config
        
        # Initialize tools
        self.face_detector = FaceDetector(confidence_threshold=config.face_detection_confidence) if config.detect_face else None
        self.segmenter = PersonSegmenter() if config.use_segmentation else None
        self.text_renderer = TextRenderer(font_size=config.text_config.font_size)
        
        # Create output directories
        config.create_output_dirs()
    
    def process_image(self, image_path: Path, text: str = "") -> Tuple[Optional[Image.Image], Optional[Image.Image], Optional[Image.Image]]:
        """
        Process single image to create sticker, main, and tab versions.
        
        Args:
            image_path: Path to input image
            text: Text to overlay on sticker
            
        Returns:
            Tuple of (sticker_image, main_image, tab_image) or (None, None, None) on error
        """
        try:
            # Load image
            img_pil = Image.open(image_path)
            
            # Fix EXIF orientation
            img_pil = utils.fix_image_orientation(img_pil)
            
            # Convert to BGR for OpenCV operations
            img_cv = utils.pil_to_cv2(img_pil)
            
            # Step 1: Face detection and cropping
            if self.config.detect_face and self.face_detector:
                img_cv, face_info = self.face_detector.crop_to_face(
                    img_cv,
                    margin=self.config.face_crop_margin
                )
            
            # Step 2: Person segmentation and cutout
            if self.config.use_segmentation and self.segmenter:
                person_img_rgba, mask = self.segmenter.extract_person(img_cv, keep_largest_only=True)
                
                # Convert to PIL
                b, g, r, a = cv2.split(person_img_rgba)
                person_img_rgb = cv2.merge((r, g, b, a))
                person_pil = Image.fromarray(person_img_rgb, mode='RGBA')
            else:
                # No segmentation, use image as-is
                person_pil = utils.cv2_to_pil(img_cv).convert('RGBA')
            
            # Step 3: Add white border
            bordered = utils.add_white_border(person_pil, self.image_config.border_width)
            
            # Step 4: Add shadow (optional)
            if self.image_config.shadow_enabled:
                shadowed = utils.add_shadow(
                    bordered,
                    self.image_config.shadow_color,
                    self.image_config.shadow_offset
                )
            else:
                shadowed = bordered
            
            # Step 5: Add text
            if text:
                with_text = create_sticker_with_text(shadowed, text, self.text_config)
            else:
                with_text = shadowed
            
            # Step 6: Create different sizes
            sticker = self._resize_to_sticker(with_text)
            main = self._resize_to_main(with_text)
            tab = self._resize_to_tab(with_text)
            
            return sticker, main, tab
        
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
            return None, None, None
    
    def _resize_to_sticker(self, image: Image.Image) -> Image.Image:
        """Resize image to sticker dimensions (max 370x320, PNG with transparency)"""
        image = utils.resize_to_fit(
            image,
            self.image_config.sticker_max_width,
            self.image_config.sticker_max_height
        )
        
        # Ensure RGBA
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        return image
    
    def _resize_to_main(self, image: Image.Image) -> Image.Image:
        """Resize image to main dimensions (240x240, PNG with transparency)"""
        # Create square canvas with image centered
        main = utils.create_canvas_with_image(
            image.copy(),
            self.image_config.main_width,
            self.image_config.main_height
        )
        
        # Ensure RGBA
        if main.mode != 'RGBA':
            main = main.convert('RGBA')
        
        return main
    
    def _resize_to_tab(self, image: Image.Image) -> Image.Image:
        """Resize image to tab dimensions (96x74, PNG with transparency)"""
        # Create canvas with image centered
        tab = utils.create_canvas_with_image(
            image.copy(),
            self.image_config.tab_width,
            self.image_config.tab_height
        )
        
        # Ensure RGBA
        if tab.mode != 'RGBA':
            tab = tab.convert('RGBA')
        
        return tab
    
    def save_stickers(self, sticker: Image.Image, main: Image.Image, tab: Image.Image, 
                     output_name: str) -> Tuple[Path, Path, Path]:
        """
        Save sticker images to output directory.
        
        Args:
            sticker: Sticker image
            main: Main image (240x240)
            tab: Tab image (96x74)
            output_name: Base name for output files (without extension)
            
        Returns:
            Tuple of (sticker_path, main_path, tab_path)
        """
        stickers_dir = self.config.output_dir / "stickers"
        
        # Save sticker
        sticker_path = stickers_dir / f"{output_name}.png"
        sticker.save(sticker_path, 'PNG')
        
        # Save main image
        main_path = self.config.output_dir / f"main_{output_name}.png"
        main.save(main_path, 'PNG')
        
        # Save tab image
        tab_path = self.config.output_dir / f"tab_{output_name}.png"
        tab.save(tab_path, 'PNG')
        
        return sticker_path, main_path, tab_path
    
    def process_batch(self, mapping: dict[str, str]) -> dict[str, dict]:
        """
        Process batch of images from mapping.
        
        Args:
            mapping: Dictionary of {filename: text}
            
        Returns:
            Dictionary with processing results
        """
        results = {}
        
        for i, (filename, text) in enumerate(mapping.items(), 1):
            image_path = self.config.photos_dir / filename
            
            if not image_path.exists():
                print(f"[{i}/{len(mapping)}] File not found: {image_path}")
                results[filename] = {"status": "error", "message": "File not found"}
                continue
            
            print(f"[{i}/{len(mapping)}] Processing {filename}...")
            
            # Process image
            sticker, main, tab = self.process_image(image_path, text)
            
            if sticker is None:
                results[filename] = {"status": "error", "message": "Processing failed"}
                continue
            
            # Generate output name (remove extension, use index)
            base_name = image_path.stem
            output_num = f"{i:02d}"
            
            # Save images
            sticker_path, main_path, tab_path = self.save_stickers(sticker, main, tab, output_num)
            
            results[filename] = {
                "status": "success",
                "sticker": str(sticker_path),
                "main": str(main_path),
                "tab": str(tab_path)
            }
            
            print(f"  ✓ Saved to {sticker_path.parent}/{output_num}.png")
        
        return results
