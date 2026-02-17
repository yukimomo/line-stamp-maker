"""Face detection and cropping functionality"""

from typing import Optional, Tuple
import numpy as np
import cv2
from pathlib import Path


class FaceDetector:
    """Detects faces in images and crops to face center"""
    
    def __init__(self, cascade_path: Optional[str] = None, confidence_threshold: float = 0.5):
        """
        Initialize face detector.
        
        Args:
            cascade_path: Path to cascade classifier XML file
            confidence_threshold: Confidence threshold for detection
        """
        self.confidence_threshold = confidence_threshold
        
        # Load cascade classifier
        if cascade_path is None:
            # Use default OpenCV cascade
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        
        self.cascade = cv2.CascadeClassifier(cascade_path)
        
        if self.cascade.empty():
            raise RuntimeError(f"Failed to load cascade classifier from {cascade_path}")
    
    def detect_faces(self, image: np.ndarray) -> list[Tuple[int, int, int, int]]:
        """
        Detect faces in image.
        
        Args:
            image: Input image in BGR format
            
        Returns:
            List of (x, y, w, h) tuples for each detected face
        """
        # Convert to grayscale for detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        return list(faces)
    
    def get_face_center(self, image: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """
        Get the center face in image.
        
        Args:
            image: Input image in BGR format
            
        Returns:
            (x, y, w, h) of largest/center face, or None if no face found
        """
        faces = self.detect_faces(image)
        
        if not faces:
            return None
        
        if len(faces) == 1:
            return tuple(faces[0])
        
        # If multiple faces, pick the largest one (likely main subject)
        return tuple(max(faces, key=lambda f: f[2] * f[3]))
    
    def crop_to_face(self, image: np.ndarray, margin: float = 0.2) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
        """
        Crop image to face with margin.
        
        Args:
            image: Input image in BGR format
            margin: Margin around face as fraction of face size (0.0-1.0)
            
        Returns:
            Tuple of (cropped_image, (x, y, w, h)) of face in original image
        """
        face = self.get_face_center(image)
        
        if face is None:
            # No face detected, return original with center info
            h, w = image.shape[:2]
            return image, (w // 4, h // 4, w // 2, h // 2)
        
        x, y, w, h = face
        
        # Add margin
        margin_x = int(w * margin)
        margin_y = int(h * margin)
        
        x_start = max(0, x - margin_x)
        y_start = max(0, y - margin_y)
        x_end = min(image.shape[1], x + w + margin_x)
        y_end = min(image.shape[0], y + h + margin_y)
        
        cropped = image[y_start:y_end, x_start:x_end]
        
        return cropped, face
    
    def crop_to_square(self, image: np.ndarray, face: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
        """
        Crop image to square centered on face or image center.
        
        Args:
            image: Input image in BGR format
            face: Optional face coordinates (x, y, w, h)
            
        Returns:
            Square cropped image
        """
        h, w = image.shape[:2]
        
        if face is not None:
            x, y, fw, fh = face
            # Center on face
            cx = x + fw // 2
            cy = y + fh // 2
        else:
            # Center on image
            cx = w // 2
            cy = h // 2
        
        # Use smaller dimension for square size
        size = min(w, h) // 2
        
        x_start = max(0, cx - size)
        y_start = max(0, cy - size)
        x_end = min(w, cx + size)
        y_end = min(h, cy + size)
        
        cropped = image[y_start:y_end, x_start:x_end]
        
        # Ensure it's actually square
        if cropped.shape[0] != cropped.shape[1]:
            min_dim = min(cropped.shape[0], cropped.shape[1])
            cropped = cropped[:min_dim, :min_dim]
        
        return cropped
