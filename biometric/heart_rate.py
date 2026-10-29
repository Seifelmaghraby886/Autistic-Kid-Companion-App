"""
ARIA Heart-Rate / HRV module
- Apple Watch CSV import (Health export → numeric.csv)
- Mock generator for demo
- Simple HRV (SDNN, RMSSD) computation
- Stress classification based on HR + HRV
"""

import csv
import math
import random
import threading
import time
from datetime import datetime, timedelta
from PySide6.QtCore import QObject, Signal


# Resting-state ranges by age (rough — pediatric, AHA 2023)
def child_resting_range(age):
    if age <= 5:    return (80, 130)
    if age <= 10:   return (70, 110)
    if age <= 14:   return (60, 100)
    return (55, 95)


def classify_stress(bpm: int, age: int, hrv_rmssd_ms: float = None) -> dict:
    """
    Combine HR + HRV → stress score 0-100.
    HRV literature:
      - RMSSD > 40 ms = healthy parasympathetic
      - RMSSD < 20 ms = significant sympathetic dominance / stress
    HR z-score above resting:
      - +20 bpm over resting upper = mild
      - +40 bpm = high
    """
    low, high = child_resting_range(age)
    mid = (low + high) / 2

    # HR component
    if bpm < low:
        hr_score = 0
    elif bpm <= high:
        hr_score = max(0, (bpm - mid) / (high - mid)) * 20
    else:
        # Above resting upper bound — scales sharply
        over = bpm - high
        hr_score = min(60, 20 + over * 1.5)

    # HRV component (if available)
    hrv_score = 0
    if hrv_rmssd_ms is not None:
        if hrv_rmssd_ms < 15:
            hrv_score = 40
        elif hrv_rmssd_ms < 25:
            hrv_score = 25
        elif hrv_rmssd_ms < 40:
            hrv_score = 10
        else:
            hrv_score = 0

    total = min(100, hr_score + hrv_score)

    if total < 25:
        label = "calm"
    elif total < 50:
        label = "alert"
    elif total < 75:
        label = "stressed"
    else:
        label = "high_stress"

    return {
        "score": round(total, 1),
        "label": label,
        "bpm": bpm,
        "hrv_rmssd_ms": hrv_rmssd_ms,
        "resting_range": [low, high],
        "is_elevated": bpm > high,
    }


def compute_rmssd(rr_intervals_ms):
    """Root mean square of successive differences (RMSSD)."""
    if not rr_intervals_ms or len(rr_intervals_ms) < 2:
        return None
    diffs = [(rr_intervals_ms[i+1] - rr_intervals_ms[i]) ** 2
             for i in range(len(rr_intervals_ms) - 1)]
    return math.sqrt(sum(diffs) / len(diffs))


def import_apple_health_csv(path: str) -> list:
    """
    Parse Apple Health XML export converted to CSV.
    Expected columns: startDate, value (bpm)
    Returns list of (datetime, bpm).
    """
    out = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Tolerate various column names
                ts_key = None
                val_key = None
                for k in row:
                    kl = k.lower()
                    if "date" in kl or "time" in kl:
                        ts_key = ts_key or k
                    if "value" in kl or "bpm" in kl or "heart" in kl:
                        val_key = val_key or k
                if not ts_key or not val_key:
                    continue
                try:
                    ts = datetime.fromisoformat(row[ts_key].replace("Z", "+00:00"))
                    bpm = int(float(row[val_key]))
                    out.append((ts, bpm))
                except Exception:
                    continue
    except FileNotFoundError:
        return []
    return out


# ─── Live HR streaming (mock + Apple Watch placeholder) ──────────────────
class HeartRateStream(QObject):
    """
    Streams live BPM updates. Sources:
      - 'mock'         — simulated based on child profile + emotion context
      - 'apple_watch'  — placeholder. Real impl needs HealthKit bridge / shortcut.
      - 'csv_replay'   — replays an imported CSV at real-time speed
    """
    bpm_updated = Signal(int, float)  # bpm, hrv_rmssd_ms (or 0)
    stress_updated = Signal(dict)
    error = Signal(str)

    def __init__(self, source="mock", child_age=8, parent=None):
        super().__init__(parent)
        self._source = source
        self._child_age = child_age
        self._running = False
        self._thread = None
        self._csv_data = []
        self._csv_idx = 0
        # mock state
        self._mock_bpm = (sum(child_resting_range(child_age)) // 2)
        self._mock_target = self._mock_bpm
        self._rr_buffer = []  # last RR intervals for HRV

    def set_emotion_context(self, emotion: str):
        """Mock mode shifts BPM target based on detected emotion."""
        low, high = child_resting_range(self._child_age)
        offset = {
            "happy": 8, "joy": 12,
            "calm": -3, "neutral": 0,
            "sad": -5, "sadness": -5,
            "fear": 25, "scared": 25,
            "anger": 30, "upset": 28,
            "surprised": 20, "surprise": 20,
            "thinking": 2,
        }.get(emotion, 0)
        self._mock_target = max(low - 5, min(high + 40, (low + high) // 2 + offset))

    def load_csv(self, path):
        self._csv_data = import_apple_health_csv(path)
        self._csv_idx = 0
        return len(self._csv_data)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        try:
            while self._running:
                if self._source == "mock":
                    bpm = self._next_mock_bpm()
                elif self._source == "csv_replay" and self._csv_data:
                    if self._csv_idx >= len(self._csv_data):
                        self._csv_idx = 0
                    bpm = self._csv_data[self._csv_idx][1]
                    self._csv_idx += 1
                else:
                    self.error.emit(f"Source '{self._source}' not connected")
                    time.sleep(2)
                    continue

                # Track RR intervals for HRV
                rr_ms = 60_000 / bpm
                self._rr_buffer.append(rr_ms)
                if len(self._rr_buffer) > 30:
                    self._rr_buffer.pop(0)
                hrv = compute_rmssd(self._rr_buffer) or 0
                # Inject small biological noise into RR
                # Reset to introduce variance (simulates real HRV)
                self._rr_buffer[-1] = rr_ms + random.uniform(-25, 25)

                self.bpm_updated.emit(bpm, hrv)
                stress = classify_stress(bpm, self._child_age, hrv)
                self.stress_updated.emit(stress)
                time.sleep(1.0)
        except Exception as e:
            self.error.emit(str(e))

    def _next_mock_bpm(self):
        # Drift toward target
        delta = self._mock_target - self._mock_bpm
        self._mock_bpm += delta * 0.15 + random.uniform(-2, 2)
        self._mock_bpm = max(40, min(220, self._mock_bpm))
        return int(self._mock_bpm)


# ─── Multimodal fusion ───────────────────────────────────────────────────
def fuse_face_and_biometric(face_emotion: str, face_conf: float,
                            stress: dict, age: int) -> dict:
    """
    Combine facial CNN/VLM emotion + biometric stress into one verdict.

    Rules (evidence-based, simplified):
      - High biometric stress + neutral face → "masking" (autism: 'frozen face')
      - Calm biometric + calm face → confirmed calm
      - High face emotion + matching biometric → confirmed
      - Face conflict with biometric → biometric weighted higher when sympathetic
        (heart rate is harder to mask than facial expression)
    """
    bio_score = stress.get("score", 0)
    bio_label = stress.get("label", "calm")
    final_emotion = face_emotion
    confidence = face_conf
    note = ""
    alert_parent = False

    high_arousal_faces = {"anger", "fear", "surprise", "upset", "scared", "surprised"}
    calm_faces = {"calm", "neutral", "sleepy"}
    happy_faces = {"happy", "joy"}

    if bio_score >= 65 and face_emotion in calm_faces:
        # Masking pattern — body says stressed, face says calm
        final_emotion = "fear"  # treat as concealed anxiety
        confidence = min(0.85, 0.40 + bio_score / 100)
        note = "Possible masking: facial expression calm but biometric stress is high."
        alert_parent = True
    elif bio_score >= 80:
        # Critical stress regardless of face
        final_emotion = "anger" if face_emotion in {"anger", "upset"} else "fear"
        confidence = 0.90
        note = f"Critical biometric stress (score={bio_score:.0f}). Suggest immediate calming."
        alert_parent = True
    elif bio_score <= 25 and face_emotion in calm_faces:
        # Confirmed calm
        confidence = min(0.95, face_conf + 0.15)
        note = "Both face and body confirm calm state."
    elif bio_score <= 25 and face_emotion in happy_faces:
        confidence = min(0.95, face_conf + 0.10)
        note = "Confirmed positive: calm body, happy face."
    elif bio_score >= 50 and face_emotion in high_arousal_faces:
        confidence = min(0.95, face_conf + 0.15)
        note = "Confirmed distress: face and body agree."
    elif bio_label == "alert" and face_emotion in calm_faces:
        note = "Body slightly elevated — monitor."

    return {
        "emotion": final_emotion,
        "confidence": confidence,
        "biometric_score": bio_score,
        "biometric_label": bio_label,
        "fusion_note": note,
        "parent_alert": alert_parent,
    }
