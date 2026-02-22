"""Person segmentation using MediaPipe"""

from typing import Tuple
import numpy as np
import cv2
import mediapipe as mp
from PIL import Image


class PersonSegmenter:
    """Segments person from background using MediaPipe Selfie Segmentation"""

    def crop_to_person(self, image: np.ndarray) -> np.ndarray:
        """
        segmentationマスクの最大成分領域で画像をクロップ（人物全体表示）
        面積が小さい場合は元画像全体を返す
        """
        binary_mask, _ = self.segment(image)
        # マスク全体（255の部分）の外接矩形
        mask = binary_mask
        coords = np.column_stack(np.where(mask == 255))
        if coords.size == 0:
            return image
        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0)
        w = x_max - x_min
        h = y_max - y_min
        # 面積閾値（画像全体の10%未満ならノイズとみなす）
        min_area = image.shape[0] * image.shape[1] * 0.1
        if w * h < min_area:
            return image
        # マージン追加（人物サイズの20%）
        margin_x = int(w * 0.2)
        margin_y = int(h * 0.2)
        x1 = max(0, x_min - margin_x)
        y1 = max(0, y_min - margin_y)
        x2 = min(image.shape[1], x_max + margin_x)
        y2 = min(image.shape[0], y_max + margin_y)
        cropped = image[y1:y2, x1:x2]
        return cropped
    
    def __init__(self, model_selection: int = 1):
        """
        Initialize person segmenter.
        
        Args:
            model_selection: 0 for general purpose, 1 for landscape (default)
        """
        self.mp_selfie_segmentation = mp.solutions.selfie_segmentation
        self.segmenter = self.mp_selfie_segmentation.SelfieSegmentation(
            model_selection=model_selection
        )
    
    def segment(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Segment person from background.
        
        Args:
            image: Input image in BGR format (RGB when passed to mediapipe)
            
        Returns:
            Tuple of (segmentation_mask, confidence_mask)
        """
        # Convert BGR to RGB for MediaPipe
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Get segmentation
        results = self.segmenter.process(rgb_image)
        
        # Get segmentation mask
        segmentation_mask = results.segmentation_mask
        
        # segmentation_maskは人物領域が低値（黒）、背景が高値（白）なので反転
        segmentation_mask = 1.0 - segmentation_mask
        # The mask values are 0 (background) to 1 (foreground/person)
        # Convert to binary mask (0-255), threshold=0.9
        binary_mask = (segmentation_mask > 0.9).astype(np.uint8) * 255

        # ノイズ除去: 小さな領域（面積2%未満）は除外
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_area = binary_mask.shape[0] * binary_mask.shape[1] * 0.02
        mask_clean = np.zeros_like(binary_mask)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area >= min_area:
                cv2.drawContours(mask_clean, [cnt], -1, 255, -1)
        binary_mask = mask_clean
        
        return binary_mask, segmentation_mask
    
    def create_person_image(self, image: np.ndarray, binary_mask: np.ndarray,
                           feather: int = 3, close_kernel: int = 5, open_kernel: int = 3) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create person cutout with refined mask using smooth_alpha_mask.
        """
        from .mask import smooth_alpha_mask
        refined_mask = smooth_alpha_mask(binary_mask, feather, close_kernel, open_kernel)
        b, g, r = cv2.split(image)
        alpha = refined_mask
        person_image = cv2.merge((b, g, r, alpha))
        return person_image, refined_mask
    
    def _keep_largest_component(self, mask: np.ndarray) -> np.ndarray:
        """
        Keep only the largest connected component in mask.
        
        Args:
            mask: Input mask
            
        Returns:
            Mask with only largest component
        """
        # Find connected components
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
        
        # Ignore background (label 0)
        if num_labels <= 1:
            return mask
        
        # Find the largest component (excluding background)
        largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        
        # Create new mask with only largest component
        result = np.zeros_like(mask)
        result[labels == largest_label] = 255
        
        return result
    
    def extract_person(self, image: np.ndarray, keep_largest_only: bool = True,
                      feather: int = 3, close_kernel: int = 5, open_kernel: int = 3) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract person from image with transparent background.
        
        Args:
            image: Input image in BGR format
            keep_largest_only: If True, keep only largest object
        feather, close_kernel, open_kernel: smooth_alpha_mask parameters
        Returns:
            Tuple of (person_image_RGBA, mask)
        """
        binary_mask, _ = self.segment(image)
        # 最大成分抽出は滑らか化前のバイナリマスクで行う
        if keep_largest_only:
            binary_mask = self._keep_largest_component(binary_mask)
        # 滑らか化してアルファマスク生成
        from .mask import smooth_alpha_mask
        refined_mask = smooth_alpha_mask(binary_mask, feather, close_kernel, open_kernel)
        b, g, r = cv2.split(image)
        alpha = refined_mask
        person_image_rgba = cv2.merge((b, g, r, alpha))
        return person_image_rgba, refined_mask


def segment_to_pil_with_transparency(image_bgr: np.ndarray, segmenter: PersonSegmenter) -> Image.Image:
    """
    Convert segmented image to PIL Image with transparency.
    
    Args:
        image_bgr: Input image in BGR format
        segmenter: PersonSegmenter instance
        
    Returns:
        PIL Image with RGBA mode
    """
    # Extract person
    person_img_bgra, _ = segmenter.extract_person(image_bgr)
    
    # Convert BGRA to RGBA (PIL expects RGB not BGR)
    b, g, r, a = cv2.split(person_img_bgra)
    person_img_rgba = cv2.merge((r, g, b, a))
    
    # Convert to PIL Image
    pil_img = Image.fromarray(person_img_rgba, mode='RGBA')
    
    return pil_img
