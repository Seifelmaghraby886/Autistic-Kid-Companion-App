"""Language detection + Franco-Arabic normalisation."""

import json
import re
from pathlib import Path

_CFG = None


def _load():
    global _CFG
    if _CFG is None:
        try:
            _CFG = json.loads((Path(__file__).parent.parent / "config" /
                               "language_rules.json").read_text(encoding="utf-8"))
        except Exception:
            _CFG = {"franco_to_arabic": {}, "intent_patterns": {}}
    return _CFG


def detect_language(text: str) -> str:
    """Heuristic: returns 'ar', 'de', or 'en'."""
    if not text:
        return "en"
    # Arabic Unicode block
    arab = sum(1 for ch in text if '؀' <= ch <= 'ۿ')
    if arab >= max(2, int(len(text) * 0.15)):
        return "ar"
    # Franco-Arabic markers
    franco_kw = ("ana", "msh", "3ayz", "ga3an", "mama", "baba")
    low = text.lower()
    if any(k in low for k in franco_kw):
        return "ar"
    # German markers
    if any(ch in text for ch in "äöüÄÖÜß"):
        return "de"
    return "en"


def normalize_franco(text: str) -> str:
    """Convert common Franco-Arabic tokens to Arabic for downstream matching."""
    if not text:
        return text
    cfg = _load()
    mapping = cfg.get("franco_to_arabic", {})
    # Token-level replace (longest-first to avoid partial collisions)
    keys = sorted(mapping.keys(), key=len, reverse=True)
    low = " " + text + " "
    for k in keys:
        # Replace whole-word (Latin token) — case-insensitive
        low = re.sub(rf"(?<![A-Za-z0-9]){re.escape(k)}(?![A-Za-z0-9])",
                     mapping[k], low, flags=re.IGNORECASE)
    return low.strip()
