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
                           kernel_size: int = 5, blur_size: int = 5) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create person cutout with refined mask.
        
        Args:
            image: Input image in BGR format
            binary_mask: Binary segmentation mask
            kernel_size: Kernel size for morphological operations
            blur_size: Kernel size for Gaussian blur
            
        Returns:
            Tuple of (person_image_with_alpha, refined_mask)
        """
        # Apply morphological closing multiple times to fill small holes and smooth edges
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        refined_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        # Apply morphological opening to remove small noise
        refined_mask = cv2.morphologyEx(refined_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Dilate to restore size after opening
        refined_mask = cv2.dilate(refined_mask, kernel, iterations=1)
        
        # Apply stronger Gaussian blur for smoother edges (larger kernel and iterations)
        refined_mask = cv2.GaussianBlur(refined_mask, (blur_size, blur_size), 0)
        refined_mask = cv2.GaussianBlur(refined_mask, (blur_size + 2, blur_size + 2), 0)
        
        # Find largest connected component
        refined_mask = self._keep_largest_component(refined_mask)
        
        # Apply final smoothing blur
        refined_mask = cv2.GaussianBlur(refined_mask, (blur_size, blur_size), 0)
        
        # Create RGBA image with alpha channel from mask
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
    
    def extract_person(self, image: np.ndarray, keep_largest_only: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract person from image with transparent background.
        
        Args:
            image: Input image in BGR format
            keep_largest_only: If True, keep only largest object
            
        Returns:
            Tuple of (person_image_RGBA, mask)
        """
        # Get segmentation mask
        binary_mask, _ = self.segment(image)
        
        # Refine mask with morphological operations
        person_image_rgba, refined_mask = self.create_person_image(image, binary_mask)
        
        if keep_largest_only:
            refined_mask = self._keep_largest_component(refined_mask)
            
            # Update person image with kept component
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
