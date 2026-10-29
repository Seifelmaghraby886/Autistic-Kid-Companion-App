"""SafetyEngine — classifies messages into safety categories with safe replies."""

import json
from pathlib import Path

_RULES = None


def _load():
    global _RULES
    if _RULES is None:
        try:
            _RULES = json.loads((Path(__file__).parent.parent / "config" /
                                 "safety_rules.json").read_text(encoding="utf-8"))
        except Exception:
            _RULES = {"categories": {}, "high_risk_response": {}}
    return _RULES


CATEGORY_PRIORITY = [
    "SELF_HARM", "ABUSE_RISK", "MEDICAL_EMERGENCY",
    "BULLYING", "PAIN", "HUNGER_THIRST",
]


def classify_safety(text: str, lang: str = "ar") -> dict:
    """Return {category, severity, safe_reply}. Category 'NORMAL' if nothing flagged."""
    rules = _load()
    cats = rules.get("categories", {})
    if not text:
        return {"category": "NORMAL", "severity": "none", "safe_reply": ""}
    low = text.lower()
    for cat in CATEGORY_PRIORITY:
        rule = cats.get(cat, {})
        for key in ("keywords_en", "keywords_ar", "keywords_franco"):
            for kw in rule.get(key, []):
                if kw.lower() in low:
                    safe = rules.get("high_risk_response", {}).get(lang) \
                           or rules.get("high_risk_response", {}).get("en", "")
                    return {"category": cat, "severity": rule.get("severity", "medium"),
                            "safe_reply": safe}
    return {"category": "NORMAL", "severity": "none", "safe_reply": ""}
