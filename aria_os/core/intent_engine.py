"""Rule-based intent detection — backed by config/language_rules.json."""

import json
from pathlib import Path

_PATTERNS = None


def _load():
    global _PATTERNS
    if _PATTERNS is None:
        try:
            cfg = json.loads((Path(__file__).parent.parent / "config" /
                              "language_rules.json").read_text(encoding="utf-8"))
            _PATTERNS = cfg.get("intent_patterns", {})
        except Exception:
            _PATTERNS = {}
    return _PATTERNS


# Priority order — higher-stakes intents come first so they win ties.
PRIORITY = [
    "emergency","need_parent","pain","need_food","need_water","need_bathroom",
    "overstimulated","sad","angry","scared",
    "open_calm_zone","open_aac","open_schedule","open_tutorial",
    "open_story","open_game","parent_mode",
]


def detect_intent(text: str) -> str:
    if not text or not text.strip():
        return "unknown"
    low = text.lower()
    patterns = _load()
    hits = []
    for intent in PRIORITY:
        for kw in patterns.get(intent, []):
            if kw.lower() in low:
                hits.append(intent)
                break
    if hits:
        return hits[0]
    # Generic conversational
    if any(w in low for w in ("hi","hello","hey","اهلا","أهلا","hallo","ازيك")):
        return "talk"
    return "unknown"
