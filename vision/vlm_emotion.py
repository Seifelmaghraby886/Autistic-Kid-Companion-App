"""
ARIA VLM Emotion Detector
Vision-Language Model analysis: rich descriptions beyond simple emotion labels.
Uses Groq Llama-3.2-Vision (free) → Gemini Flash (free) fallback.
"""

import io
import json
import re
from PySide6.QtCore import QObject, Signal, QThread


VLM_PROMPT = """Analyze the face in this image. You are helping support an autistic child.

Output ONLY this JSON (no markdown, no explanation):
{
  "emotion": "happy|calm|sad|fear|anger|surprise|neutral",
  "confidence": 0.85,
  "secondary_emotion": "tired|focused|excited|content|or empty string",
  "description": "1-2 sentence observation of facial cues",
  "body_language": "1 sentence on posture/gesture if visible, else empty",
  "suggested_action": "1 sentence — what ARIA could do to help right now"
}

Be specific and clinical. Notice subtle cues like fatigue, tension, or distraction."""


def _frame_to_jpeg_bytes(frame) -> bytes:
    """Convert OpenCV BGR frame to JPEG bytes."""
    try:
        import cv2
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if ok:
            return buf.tobytes()
    except Exception as e:
        print(f"[Frame encode error: {e}]")
    return b""


def analyze_frame(frame, child_context: dict = None) -> dict:
    """Analyze a video frame using VLM. Returns rich emotion analysis dict."""
    img_bytes = _frame_to_jpeg_bytes(frame)
    if not img_bytes:
        return {"error": "Could not encode frame"}

    prompt = VLM_PROMPT
    if child_context:
        name = child_context.get("name", "the child")
        age = child_context.get("age", 7)
        prompt = (
            f"You are analyzing the face of {name}, an autistic {age}-year-old.\n\n"
            + prompt
        )

    try:
        from ai.multi_provider import generate_vision
        raw = generate_vision(img_bytes, prompt, json_mode=True)
        if not raw:
            return {"error": "VLM returned empty"}

        raw = re.sub(r'```(?:json)?', '', raw).strip()
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
            return data
        return {"error": "Could not parse VLM response"}
    except Exception as e:
        print(f"[VLM analyze error: {e}]")
        return {"error": str(e)}


class VLMEmotionWorker(QObject):
    """Background worker for VLM analysis (slow, ~1-2 sec per call)."""
    result_ready = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, frame, child_context=None):
        super().__init__()
        # Copy frame to avoid race conditions
        try:
            import numpy as np
            self._frame = np.copy(frame)
        except Exception:
            self._frame = frame
        self._child_context = child_context

    def run(self):
        try:
            result = analyze_frame(self._frame, self._child_context)
            if "error" in result:
                self.error_occurred.emit(result["error"])
            else:
                self.result_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))
