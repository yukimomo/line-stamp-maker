"""Person segmentation using MediaPipe"""

from typing import Tuple
import numpy as np
import cv2
import mediapipe as mp
from PIL import Image


class PersonSegmenter:
    """Segments person from background using MediaPipe Selfie Segmentation"""
    
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
        
        # The mask values are 0 (background) to 1 (foreground/person)
        # Convert to binary mask (0-255)
        binary_mask = (segmentation_mask > 0.5).astype(np.uint8) * 255
        
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
        person_image_rgba, refined_mask = self.create_person_image(
            image, binary_mask, feather, close_kernel, open_kernel)
        if keep_largest_only:
            refined_mask = self._keep_largest_component(refined_mask)
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
