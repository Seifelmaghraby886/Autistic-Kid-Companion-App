"""VoiceActivityDetector — real (RMS-based) + mock modes."""

import math
import struct
import threading
import time


class VoiceActivityDetector:
    """Simple energy-based VAD with mock fallback for testing."""

    def __init__(self, sensitivity="medium", mock_mode=False):
        self.mock_mode = mock_mode
        self.sensitivity = sensitivity
        self._mock_speaking = False
        self.thresholds = {"low": 800, "medium": 350, "high": 180}

    def threshold(self):
        return self.thresholds.get(self.sensitivity, 350)

    def detect_speech(self, audio_chunk: bytes) -> bool:
        """Real detection from int16 PCM bytes."""
        if self.mock_mode:
            return self._mock_speaking
        try:
            count = len(audio_chunk) // 2
            if count == 0:
                return False
            shorts = struct.unpack(f"{count}h", audio_chunk)
            rms = math.sqrt(sum(s * s for s in shorts) / count)
            return rms >= self.threshold()
        except Exception:
            return False

    def mock_detect_speech(self, speaking: bool):
        """For test injection."""
        self._mock_speaking = speaking
