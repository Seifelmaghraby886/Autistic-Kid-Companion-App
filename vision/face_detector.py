"""ARIA Face Detector using OpenCV Haar Cascades."""

import cv2
import numpy as np
import os


class FaceDetector:
    def __init__(self, min_size=(40, 40), scale_factor=1.08, min_neighbors=4):
        # More permissive defaults so a child a metre or two from the camera,
        # or sitting slightly off-axis, still registers reliably.
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self._cascade = cv2.CascadeClassifier(cascade_path)
        self._min_size = min_size
        self._scale = scale_factor
        self._min_neighbors = min_neighbors

    def detect(self, frame: np.ndarray) -> list:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        faces = self._cascade.detectMultiScale(
            gray,
            scaleFactor=self._scale,
            minNeighbors=self._min_neighbors,
            minSize=self._min_size,
            flags=cv2.CASCADE_SCALE_IMAGE,
        )
        return list(faces) if len(faces) > 0 else []

    def get_largest_face(self, frame: np.ndarray):
        faces = self.detect(frame)
        if not faces:
            return None
        return max(faces, key=lambda f: f[2] * f[3])
