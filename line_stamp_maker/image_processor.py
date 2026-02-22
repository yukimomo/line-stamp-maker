"""Main image processing pipeline"""

from pathlib import Path
from typing import Optional, Tuple
import cv2
from PIL import Image
import numpy as np

from .config import ProcessingConfig, ImageConfig
from .face_detection import FaceDetector
from .segmentation import PersonSegmenter
from .text_renderer import TextRenderer, CaptionRenderer, create_sticker_with_text
from .io import open_image
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
        self.text_renderer = TextRenderer(
            font_path=str(config.text_config.font_path) if config.text_config.font_path else None,
            font_size=config.text_config.font_size,
            preset=config.text_config.font_preset
        )
        self.caption_renderer = CaptionRenderer(
            font_path=str(config.text_config.font_path) if config.text_config.font_path else None,
            font_size_base=config.text_config.font_size,
            preset=config.text_config.font_preset
        )
        
        # Create output directories
        config.create_output_dirs()
    
    def process_image(self, image_path: Path, text: str = "", debug_errors: dict = None) -> Tuple[Optional[Image.Image], Optional[Image.Image], Optional[Image.Image]]:
        """
        Process single image to create sticker, main, and tab versions.
        
        Args:
            image_path: Path to input image
            text: Text to overlay on sticker
            
        Returns:
            Tuple of (sticker_image, main_image, tab_image) or (None, None, None) on error
        """
        import traceback
        try:
            stage = 'load'
            img_pil = open_image(image_path)
            stage = 'crop'
            img_cv = utils.pil_to_cv2(img_pil)
            stage = 'person_crop'
            # 人物全体表示モード: segmentation最大成分領域でクロップ
            if self.config.use_segmentation and self.segmenter:
                img_cv_before = img_cv.copy()
                img_cv = self.segmenter.crop_to_person(img_cv)
                if self.config.verbose:
                    print(f"[DEBUG] Cropped to person bounding box: shape={img_cv.shape}")
            stage = 'segment'
            if self.config.use_segmentation:
                if self.segmenter is None:
                    raise RuntimeError("Segmentation is enabled but segmenter is None")
                feather = 1
                close_kernel = 3
                open_kernel = 1
                # segmentation_maskの出力も保存
                binary_mask, segmentation_mask = self.segmenter.segment(img_cv)
                seg_mask_vis = (segmentation_mask * 255).astype(np.uint8)
                cv2.imwrite("debug_segmentation_mask.png", seg_mask_vis)
                person_img_rgba, mask = self.segmenter.extract_person(
                    img_cv, keep_largest_only=True,
                    feather=feather, close_kernel=close_kernel, open_kernel=open_kernel)
                if self.config.verbose:
                    # マスクと合成画像を一時保存
                    cv2.imwrite("debug_mask.png", mask)
                    cv2.imwrite("debug_person_rgba.png", person_img_rgba)
                    # アルファマスクも保存
                    alpha = person_img_rgba[:, :, 3] if person_img_rgba.shape[2] == 4 else mask
                    cv2.imwrite("debug_alpha_mask.png", alpha)
                    print("[DEBUG] Saved debug_mask.png, debug_person_rgba.png, debug_alpha_mask.png, debug_segmentation_mask.png")
                # OpenCVはBGR(A)なのでPIL用に変換
                person_img_rgba = cv2.cvtColor(person_img_rgba, cv2.COLOR_BGRA2RGBA)
                person_pil = Image.fromarray(person_img_rgba, mode='RGBA')
            else:
                person_pil = utils.cv2_to_pil(img_cv).convert('RGBA')
            stage = 'mask'
            # ...マスク処理
            stage = 'outline'
            # ...アウトライン処理
            stage = 'text'
            # ...テキスト処理
            stage = 'save'
            max_size = max(self.image_config.sticker_max_width, self.image_config.sticker_max_height)
            if max(person_pil.width, person_pil.height) > max_size:
                person_pil.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            bordered = person_pil
            if self.image_config.shadow_enabled:
                shadowed = utils.add_shadow(
                    bordered,
                    self.image_config.shadow_color,
                    self.image_config.shadow_offset
                )
            else:
                shadowed = bordered
            if text:
                with_text = self.caption_renderer.render_caption(
                    shadowed,
                    text,
                    style=self.text_config.caption_style,
                    text_color=self.text_config.caption_text_color,
                    outline_color=self.text_config.caption_outline_color,
                    outline_px=self.text_config.caption_outline_px,
                    padding_ratio=self.text_config.caption_padding_ratio,
                    max_lines=self.text_config.caption_max_lines
                )
            else:
                with_text = shadowed
            sticker = self._resize_to_sticker(with_text)
            main = self._resize_to_main(with_text)
            tab = self._resize_to_tab(with_text)
            return sticker, main, tab
        except Exception as e:
            tb = traceback.format_exc().splitlines()[-5:]
            if debug_errors is not None:
                debug_errors['error'] = {
                    'type': type(e).__name__,
                    'message': str(e),
                    'traceback': tb,
                    'stage': stage
                }
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
    
    def process_batch(self, mapping: dict[Path, str]) -> dict[str, dict]:
        """
        Process batch of images from mapping.
        
        Args:
            mapping: Dictionary of {Path: text}
        Returns:
            Dictionary with processing results
        """
        results = {}
        for i, (image_path, text) in enumerate(mapping.items(), 1):
            if not image_path.exists():
                results[image_path.name] = {"status": "error", "message": "File not found", "stage": "load"}
                continue
            print(f"[{i}/{len(mapping)}] Processing {image_path.name}...")
            debug_errors = {}
            sticker, main, tab = self.process_image(image_path, text, debug_errors)
            if sticker is None:
                err = debug_errors.get('error', {})
                results[image_path.name] = {"status": "error", **err}
                continue
            base_name = image_path.stem
            output_num = f"{i:02d}"
            sticker_path, main_path, tab_path = self.save_stickers(sticker, main, tab, output_num)
            results[image_path.name] = {
                "status": "success",
                "sticker": str(sticker_path),
                "main": str(main_path),
                "tab": str(tab_path)
            }
            print(f"  [OK] Saved to {sticker_path.parent}/{output_num}.png")
        return results
