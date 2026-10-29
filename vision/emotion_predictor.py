"""
ARIA Emotion Predictor
Loads trained TF/Keras model and predicts emotion from face crop.
"""

import json
import numpy as np
import cv2
from pathlib import Path


MODEL_PATH = Path(__file__).parent.parent / "models" / "emotion_model.h5"
LABELS_PATH = Path(__file__).parent.parent / "models" / "labels.json"

# UI mapping: model labels → app labels
MODEL_TO_APP = {
    "Natural": "neutral",
    "natural": "neutral",
    "neutral": "neutral",
    "anger":   "anger",
    "fear":    "fear",
    "joy":     "happy",
    "sadness": "sadness",
    "surprise":"surprise",
}


class EmotionPredictor:
    _instance = None
    _model = None
    _labels = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        try:
            import tensorflow as tf
            if MODEL_PATH.exists():
                self._model = tf.keras.models.load_model(str(MODEL_PATH), compile=False)
                print(f"[ARIA] Emotion model loaded: {MODEL_PATH}")
            else:
                print(f"[ARIA] Emotion model not found at {MODEL_PATH}. Run ml_training first.")
                self._model = None

            if LABELS_PATH.exists():
                with open(LABELS_PATH) as f:
                    self._labels = json.load(f)
            else:
                self._labels = ["anger", "fear", "joy", "neutral", "sadness", "surprise"]
        except ImportError:
            print("[ARIA] TensorFlow not available. Emotion detection disabled.")
            self._model = None
            self._labels = ["anger", "fear", "joy", "neutral", "sadness", "surprise"]
        except Exception as e:
            print(f"[ARIA] Model load error: {e}")
            self._model = None

    def is_loaded(self) -> bool:
        return self._model is not None

    def predict(self, face_crop: np.ndarray) -> tuple:
        """
        Returns (emotion_str, confidence, {label: prob}) tuple.
        Falls back to neutral if model not loaded.
        """
        if self._model is None:
            return self._random_fallback()

        try:
            # Determine input size from model
            input_shape = self._model.input_shape
            h = input_shape[1] or 96
            w = input_shape[2] or 96
            channels = input_shape[3] or 3

            # Preprocess
            img = cv2.resize(face_crop, (w, h))
            if channels == 1:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                img = img[..., np.newaxis]
            else:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            img = img.astype(np.float32) / 255.0
            img = np.expand_dims(img, axis=0)

            preds = self._model.predict(img, verbose=0)[0]
            idx = int(np.argmax(preds))
            conf = float(preds[idx])
            label = self._labels[idx] if idx < len(self._labels) else "neutral"
            label = MODEL_TO_APP.get(label, label)

            probs = {}
            for i, lbl in enumerate(self._labels):
                mapped = MODEL_TO_APP.get(lbl, lbl)
                probs[mapped] = float(preds[i])

            return label, conf, probs

        except Exception as e:
            print(f"[Predictor error] {e}")
            return "neutral", 0.5, {"neutral": 1.0}

    def _random_fallback(self) -> tuple:
        """Return neutral when model not available."""
        return "neutral", 0.5, {
            "neutral": 0.5, "happy": 0.1, "sad": 0.1,
            "scared": 0.1, "upset": 0.1, "surprised": 0.1
        }
