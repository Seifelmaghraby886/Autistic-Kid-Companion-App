"""
ARIA Ambient Emotion Monitor
============================
While the child is on the ARIA OS home shell, this quietly watches the camera
in a background thread — detecting their face, estimating emotion, and
smoothing it over a few seconds. It never shows a camera feed; it just lets
ARIA's home gently *notice* how the child feels.

Outputs (Qt signals, delivered to the main thread):
    emotion_detected(emotion, confidence)  — a new, settled mood
    distress_detected(emotion)             — sustained sad / fear / anger
    monitor_error(message)                 — camera/vision unavailable

The monitor releases the camera the moment it is stopped, so camera tools
(Live Camera, Photo Test) can take over without a device conflict.
"""

import threading
import time

from PySide6.QtCore import QObject, Signal

import database.db_manager as db


# emotions that should gently trigger a Calm Zone offer
_DISTRESS = {"sad", "sadness", "fear", "scared", "anger", "angry", "upset"}


from core.log import log as _log


class EmotionMonitor(QObject):
    """Background camera emotion watcher for the ARIA OS shell."""

    emotion_detected  = Signal(str, float)
    distress_detected = Signal(str)
    monitor_error     = Signal(str)

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self.child_id = child_id
        self._running = False
        self._thread = None
        self._cap = None
        self._last_emotion = None
        self._last_distress_ts = 0.0
        self._distress_cooldown = 60.0     # seconds between Calm Zone offers

    # ── lifecycle ────────────────────────────────────────────────────
    def is_running(self) -> bool:
        return self._running

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop watching and release the camera (so camera tools can open it)."""
        if not self._running and self._thread is None:
            return
        self._running = False
        t = self._thread
        self._thread = None
        if t is not None and t.is_alive():
            t.join(timeout=1.8)
        if self._cap is not None:           # defensive — thread normally frees it
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None

    def shutdown(self):
        self.stop()

    # ── background capture loop ──────────────────────────────────────
    def _loop(self):
        try:
            import cv2
            from vision.face_detector import FaceDetector
            from vision.emotion_predictor import EmotionPredictor
            from vision.emotion_smoothing import EmotionSmoother
        except Exception as e:                       # pragma: no cover
            self.monitor_error.emit(f"vision libraries unavailable: {e}")
            self._running = False
            return

        cam_id = self._camera_id()
        try:
            from vision.camera import open_camera
            self._cap = open_camera(cam_id)
        except Exception as e:
            self._cap = None
            self.monitor_error.emit(f"camera open failed: {e}")

        if self._cap is None or not self._cap.isOpened():
            self.monitor_error.emit("camera not available for ambient monitor")
            self._running = False
            if self._cap is not None:
                try:
                    self._cap.release()
                except Exception:
                    pass
                self._cap = None
            return

        try:
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        except Exception:
            pass

        detector = FaceDetector()
        predictor = EmotionPredictor()
        smoother = EmotionSmoother(window_seconds=6, min_confidence=0.55)
        _log("ambient emotion monitor: camera on, watching gently")

        misses = 0
        while self._running:
            try:
                ok, frame = self._cap.read()
                if not ok or frame is None:
                    misses += 1
                    if misses > 25:
                        self.monitor_error.emit("camera stopped returning frames")
                        break
                    time.sleep(0.4)
                    continue
                misses = 0

                face = detector.get_largest_face(frame)
                if face is not None:
                    x, y, w, h = face
                    crop = frame[max(0, y):y + h, max(0, x):x + w]
                    if crop.size > 0:
                        emotion, conf, _ = predictor.predict(crop)
                        settled = smoother.update(emotion, conf)
                        if settled and settled != self._last_emotion:
                            self._last_emotion = settled
                            self.emotion_detected.emit(settled, float(conf))
                            try:
                                db.log_emotion(self.child_id, settled, float(conf),
                                               source="ambient_camera")
                            except Exception:
                                pass
                            self._maybe_distress(settled)
            except Exception as e:                   # pragma: no cover
                self.monitor_error.emit(str(e))
                time.sleep(0.6)
            time.sleep(0.5)                          # ~2 checks/second — light

        # cleanup — always free the camera
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None
        _log("ambient emotion monitor: camera released")

    # ── helpers ──────────────────────────────────────────────────────
    def _camera_id(self) -> int:
        try:
            settings = db.get_device_settings(self.child_id) or {}
            cid = settings.get("camera_id")
            if cid is not None and int(cid) >= 0:
                return int(cid)
        except Exception:
            pass
        return 0

    def _maybe_distress(self, emotion: str):
        if emotion.lower() not in _DISTRESS:
            return
        now = time.time()
        if now - self._last_distress_ts < self._distress_cooldown:
            return
        self._last_distress_ts = now
        _log(f"ambient emotion monitor: sustained '{emotion}' — offering comfort")
        self.distress_detected.emit(emotion)
