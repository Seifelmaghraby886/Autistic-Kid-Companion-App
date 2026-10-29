"""
ARIA OS — Face Input Engine
===========================
Turns the camera into an INPUT channel, so a child can drive ARIA with no
touch — and, for non-verbal children, no speech either:

  * presence  — a face appears  -> ARIA wakes;  the child leaves -> ARIA idles
  * look      — the child turns toward the camera -> ARIA starts a listening
                turn ("look-to-listen")
  * gestures  — a NOD means "yes", a SHAKE means "no"

It runs a background camera thread with the same lifecycle as EmotionMonitor
and reuses only `vision.face_detector.FaceDetector`. The gesture maths is a
pure, unit-testable function — `analyze_gesture()` — with no Qt and no camera.
"""

import threading
import time
from collections import deque

from PySide6.QtCore import QObject, Signal

import database.db_manager as db
from core.log import log as _log


# ── pure gesture analysis (no Qt, no camera — unit-testable) ──────────
def _smooth(series, w=3):
    if len(series) < w:
        return list(series)
    out = []
    for i in range(len(series)):
        lo, hi = max(0, i - w // 2), min(len(series), i + w // 2 + 1)
        out.append(sum(series[lo:hi]) / (hi - lo))
    return out


def _zero_crossings(series):
    """How many times the series crosses its own mean — i.e. oscillations."""
    if len(series) < 3:
        return 0
    mean = sum(series) / len(series)
    signs = [1 if v > mean else (-1 if v < mean else 0) for v in series]
    signs = [s for s in signs if s != 0]
    return sum(1 for i in range(1, len(signs)) if signs[i] != signs[i - 1])


def analyze_gesture(samples, box_w, min_amp=0.08):
    """
    Classify a short window of face-box centres as a head gesture.

    Returns (gesture, debug)  where gesture is 'nod' | 'shake' | None and
    debug carries the measured amplitudes / oscillations so callers can
    log them when no gesture fires (helps tune thresholds).
    """
    if len(samples) < 6 or box_w <= 0:
        return None, None
    xs = _smooth([s[1] for s in samples])
    ys = _smooth([s[2] for s in samples])
    amp_x = (max(xs) - min(xs)) / box_w
    amp_y = (max(ys) - min(ys)) / box_w
    osc_x = _zero_crossings(xs)
    osc_y = _zero_crossings(ys)
    debug = {"ax": amp_x, "ay": amp_y, "ox": osc_x, "oy": osc_y}
    # a real gesture oscillates (>=1 mean-crossing per direction) with
    # enough amplitude, and one axis must clearly dominate the other.
    if amp_y >= min_amp and osc_y >= 1 and amp_y > amp_x * 1.15:
        return "nod", debug
    if amp_x >= min_amp and osc_x >= 1 and amp_x > amp_y * 1.15:
        return "shake", debug
    return None, debug


class FaceInputEngine(QObject):
    """Background camera watcher — presence + head gestures."""

    presence_changed = Signal(bool)   # True: child present / False: gone
    gesture_detected = Signal(str)    # 'nod' | 'shake'
    monitor_error    = Signal(str)

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self.child_id = child_id
        self._running = False
        self._thread = None
        self._cap = None

        sensitivity = float(self._load_cfg().get("gesture_sensitivity", 1.0) or 1.0)
        # higher sensitivity -> lower amplitude needed to register a gesture
        self._min_amp = max(0.05, min(0.16, 0.09 / max(0.5, sensitivity)))

        self._present = False
        self._face_since = 0.0
        self._last_face_ts = 0.0
        self._last_gesture_ts = 0.0
        self._last_motion_log = 0.0
        self._samples = deque()

    @staticmethod
    def _load_cfg():
        import json
        from pathlib import Path
        try:
            return json.loads((Path(__file__).parent.parent / "config" /
                               "app_config.json").read_text(encoding="utf-8"))
        except Exception:
            return {}

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
        """Stop watching and release the camera (so camera tools can use it)."""
        if not self._running and self._thread is None:
            return
        self._running = False
        t = self._thread
        self._thread = None
        if t is not None and t.is_alive():
            t.join(timeout=1.8)
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None
        self._present = False
        self._face_since = 0.0
        self._samples.clear()

    def shutdown(self):
        self.stop()

    # ── camera loop ──────────────────────────────────────────────────
    def _camera_id(self) -> int:
        try:
            settings = db.get_device_settings(self.child_id) or {}
            cid = settings.get("camera_id")
            if cid is not None and int(cid) >= 0:
                return int(cid)
        except Exception:
            pass
        return 0

    def _loop(self):
        try:
            import cv2
            from vision.face_detector import FaceDetector
        except Exception as e:                         # pragma: no cover
            self.monitor_error.emit(f"vision libraries unavailable: {e}")
            self._running = False
            return
        try:
            from vision.camera import open_camera
            self._cap = open_camera(self._camera_id())
        except Exception as e:
            self._cap = None
            self.monitor_error.emit(f"camera open failed: {e}")
        if self._cap is None or not self._cap.isOpened():
            self.monitor_error.emit("camera not available for face input")
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

        # very permissive Haar settings — autistic children may sit
        # off-centre or move; we want to *find* the face, not be picky.
        detector = FaceDetector(min_size=(40, 40),
                                scale_factor=1.08, min_neighbors=3)
        _log("face input: camera on (presence + look + gestures)")
        misses = 0
        last_status_log = time.time()
        frames_with_face = 0
        frames_without = 0
        while self._running:
            try:
                ok, frame = self._cap.read()
                if not ok or frame is None:
                    misses += 1
                    if misses > 25:
                        self.monitor_error.emit("camera stopped returning frames")
                        break
                    time.sleep(0.25)
                    continue
                misses = 0
                frame_w = frame.shape[1]
                face = detector.get_largest_face(frame)
                now = time.time()
                self._process(face, frame_w, now)
                # periodic visibility for the parent / developer
                if face is not None:
                    frames_with_face += 1
                else:
                    frames_without += 1
                if now - last_status_log >= 4.0:
                    total = frames_with_face + frames_without
                    pct = (100 * frames_with_face // total) if total else 0
                    _log(f"face input: last 4s -> {frames_with_face}/{total} "
                         f"frames had a face ({pct}%)")
                    last_status_log = now
                    frames_with_face = frames_without = 0
            except Exception as e:                      # pragma: no cover
                self.monitor_error.emit(str(e))
                time.sleep(0.4)
            time.sleep(0.08)                            # ~12 fps

        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None
        _log("face input: camera released")

    # ── per-frame processing ─────────────────────────────────────────
    def _process(self, face, frame_w, now):
        if face is not None:
            x, y, w, h = face
            cx, cy = x + w / 2.0, y + h / 2.0
            self._last_face_ts = now
            if self._face_since == 0.0:
                self._face_since = now

            # presence — a face held steady for >0.8 s (snappy wake)
            if not self._present and (now - self._face_since) >= 0.8:
                self._present = True
                self.presence_changed.emit(True)

            # head gestures
            self._samples.append((now, cx, cy))
            while self._samples and now - self._samples[0][0] > 1.5:
                self._samples.popleft()
            if now - self._last_gesture_ts >= 1.2 and len(self._samples) >= 6:
                gesture, dbg = analyze_gesture(list(self._samples), w,
                                                self._min_amp)
                # Log non-trivial motion so a parent / developer can see WHY
                # a head movement may not be classifying yet (and tune the
                # gesture_sensitivity in app_config.json from the numbers).
                if (dbg and (dbg["ax"] > 0.03 or dbg["ay"] > 0.03)
                        and now - self._last_motion_log >= 1.2):
                    self._last_motion_log = now
                    _log(f"face input: motion ax={dbg['ax']:.2f} "
                         f"ay={dbg['ay']:.2f}  osc x={dbg['ox']} y={dbg['oy']} "
                         f"(threshold {self._min_amp:.2f})")
                if gesture:
                    self._last_gesture_ts = now
                    self._samples.clear()
                    _log(f"face input: gesture '{gesture}' "
                         f"(ax={dbg['ax']:.2f} ay={dbg['ay']:.2f})")
                    self.gesture_detected.emit(gesture)
        else:
            # no face in frame
            self._face_since = 0.0
            self._samples.clear()
            if self._present and (now - self._last_face_ts) >= 4.0:
                self._present = False
                self.presence_changed.emit(False)
