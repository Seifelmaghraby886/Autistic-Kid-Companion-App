"""ARIA Emotion Smoothing — prevents rapid emotion jumps."""

from collections import deque
from datetime import datetime, timedelta


class EmotionSmoother:
    def __init__(self, window_seconds: int = 5, min_confidence: float = 0.60):
        self._window = window_seconds
        self._min_conf = min_confidence
        self._history = deque()
        self._last_emit = None
        self._last_emit_time = None

    def update(self, emotion: str, confidence: float):
        now = datetime.now()
        self._history.append((now, emotion, confidence))

        cutoff = now - timedelta(seconds=self._window)
        while self._history and self._history[0][0] < cutoff:
            self._history.popleft()

        if confidence < self._min_conf:
            return None

        if len(self._history) < 3:
            return None

        votes = {}
        for _, em, conf in self._history:
            votes[em] = votes.get(em, 0) + 1

        dominant = max(votes, key=votes.get)
        dominant_count = votes[dominant]
        ratio = dominant_count / len(self._history)

        if ratio < 0.55:
            return None

        if (self._last_emit == dominant and
                self._last_emit_time is not None and
                (now - self._last_emit_time).total_seconds() < 3):
            return None

        self._last_emit = dominant
        self._last_emit_time = now
        return dominant
