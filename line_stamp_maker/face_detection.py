"""Face detection and cropping functionality"""

from typing import Optional, Tuple
import numpy as np
import cv2
import mediapipe as mp

class FaceDetector:
    """Detects faces in images and crops to face center using MediaPipe Face Detection"""
    def __init__(self, confidence_threshold: float = 0.5):
        self.confidence_threshold = confidence_threshold
        self.mp_face_detection = mp.solutions.face_detection
        self.detector = self.mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=confidence_threshold)

    def detect_faces(self, image: np.ndarray) -> list[Tuple[int, int, int, int]]:
        # Convert BGR to RGB
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.detector.process(rgb)
        faces = []
        if results.detections:
            h, w = image.shape[:2]
            for det in results.detections:
                box = det.location_data.relative_bounding_box
                x = int(box.xmin * w)
                y = int(box.ymin * h)
                fw = int(box.width * w)
                fh = int(box.height * h)
                faces.append((x, y, fw, fh))
        return faces

    def get_face_center(self, image: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        faces = self.detect_faces(image)
        if not faces:
            return None
        if len(faces) == 1:
            return faces[0]
        return max(faces, key=lambda f: f[2] * f[3])

    def crop_to_face(self, image: np.ndarray, margin: float = 0.2) -> Tuple[np.ndarray, Optional[Tuple[int, int, int, int]]]:
        face = self.get_face_center(image)
        if face is None:
            h, w = image.shape[:2]
            size = min(w, h)
            cx, cy = w // 2, h // 2
            x_start = max(0, cx - size // 2)
            y_start = max(0, cy - size // 2)
            x_end = x_start + size
            y_end = y_start + size
            cropped = image[y_start:y_end, x_start:x_end]
            return cropped, None
        x, y, fw, fh = face
        margin_x = int(fw * margin)
        margin_y = int(fh * margin)
        x_start = max(0, x - margin_x)
        y_start = max(0, y - margin_y)
        x_end = min(image.shape[1], x + fw + margin_x)
        y_end = min(image.shape[0], y + fh + margin_y)
        cropped = image[y_start:y_end, x_start:x_end]
        return cropped, face
