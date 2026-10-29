"""ARIA Response Parser — robust JSON extraction with truncation repair."""

import json
import re


VALID_EXPRESSIONS = {"happy", "calm", "thinking", "sad", "surprised", "listening", "sleepy", "comfort"}
VALID_ACTIVITIES = {"none", "breathing", "emotion_matching", "social_story", "visual_schedule", "game", "communication_board"}
VALID_TTS = {"soft", "normal", "very_slow"}


FALLBACK = {
    "reply": "I'm here with you.",
    "face_expression": "calm",
    "tts_style": "soft",
    "suggested_activity": "none",
    "comfort_mode": False,
    "parent_alert": False,
    "memory_update": "",
    "reason": "parse_fallback"
}


def _try_repair_json(s: str) -> str:
    """Attempt to repair common JSON truncation issues."""
    s = s.strip()
    if not s:
        return s
    # Strip code fences
    s = re.sub(r'```(?:json)?', '', s).strip()
    # Find first {
    start = s.find("{")
    if start < 0:
        return s
    s = s[start:]
    # If unbalanced, attempt to close
    open_count = 0
    close_count = 0
    in_string = False
    escape = False
    last_complete = -1
    for i, ch in enumerate(s):
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            open_count += 1
        elif ch == "}":
            close_count += 1
            if open_count == close_count:
                last_complete = i
                break
    if last_complete >= 0:
        return s[:last_complete + 1]
    # Truncated — try to close minimally
    if in_string:
        s = s + '"'
    missing = open_count - close_count
    return s + ("}" * max(0, missing))


def parse_aria_response(raw: str) -> dict:
    """Extract and validate ARIA JSON from any text. Repairs truncation."""
    if not raw or not raw.strip():
        return FALLBACK.copy()

    # Try direct
    candidate = _try_repair_json(raw)
    data = None
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError:
        # Try regex
        match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', raw, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError:
                pass

    if not data or not isinstance(data, dict):
        # Last-ditch: extract reply from anywhere
        reply_match = re.search(r'"reply"\s*:\s*"([^"]+)"', raw)
        if reply_match:
            r = FALLBACK.copy()
            r["reply"] = reply_match.group(1)[:400]
            r["reason"] = "extracted_reply_only"
            return r
        return FALLBACK.copy()

    result = FALLBACK.copy()
    result["reply"] = str(data.get("reply", "I'm here with you."))[:600]

    expr = str(data.get("face_expression", "calm")).lower()
    result["face_expression"] = expr if expr in VALID_EXPRESSIONS else "calm"

    tts = str(data.get("tts_style", "soft")).lower()
    result["tts_style"] = tts if tts in VALID_TTS else "soft"

    act = str(data.get("suggested_activity", "none")).lower()
    result["suggested_activity"] = act if act in VALID_ACTIVITIES else "none"

    result["comfort_mode"] = bool(data.get("comfort_mode", False))
    result["parent_alert"] = bool(data.get("parent_alert", False))
    result["memory_update"] = str(data.get("memory_update", ""))[:200]
    result["reason"] = str(data.get("reason", "ok"))[:200]

    return result
