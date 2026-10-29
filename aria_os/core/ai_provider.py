"""AIProvider base class + canonical ARIA-OS JSON schema validator."""

from abc import ABC, abstractmethod
from typing import Any
import json


# Valid enum values for ARIA's JSON output
VALID_INTENTS = {
    "talk","need_food","need_water","need_bathroom","need_parent","pain",
    "sad","angry","scared","overstimulated","open_calm_zone","open_aac",
    "open_schedule","open_tutorial","open_story","open_game","parent_mode",
    "emergency","unknown",
}
VALID_TOOLS = {
    "none","calm_zone","aac","schedule","tutorial","story","game",
    "parent_pin","safety",
}
VALID_EMOTIONS = {"happy","calm","sad","angry","scared","tired","neutral"}
VALID_VOICE_STYLES = {"soft","cheerful","calm","neutral","parent"}
VALID_ALERTS = {None,"normal","distress","pain","bullying","abuse_risk",
                "self_harm","medical_emergency"}


def fallback_response(lang="en") -> dict:
    """Safe default response when everything else fails."""
    msgs = {
        "en": "I'm here with you. Take your time.",
        "ar": "أنا معاك. خد وقتك.",
        "de": "Ich bin bei dir. Lass dir Zeit.",
    }
    return {
        "reply": msgs.get(lang, msgs["en"]),
        "language": {"en":"english","ar":"egyptian_arabic","de":"german"}.get(lang,"english"),
        "emotion": "calm", "emotion_confidence": 0.5,
        "need": None, "intent": "talk", "open_tool": "none",
        "parent_alert": False, "alert_type": None,
        "robot_command": {"face":"calm","voice":"soft","led":"calm_blue",
                          "movement":"stay_still","mode":"idle"},
        "voice_style": "soft", "listening_after_reply": True,
        "memory_update": {"current_emotion":"neutral","current_need":None,
                          "stress_level":"low","last_topic":""},
        "log_summary": "fallback_response",
    }


def validate_json_response(data: Any, lang="en") -> dict:
    """Validate and coerce JSON into a well-formed ARIA response. Never raises."""
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            return fallback_response(lang)
    if not isinstance(data, dict):
        return fallback_response(lang)

    out = fallback_response(lang)
    # Copy + validate each field
    if isinstance(data.get("reply"), str) and data["reply"].strip():
        out["reply"] = data["reply"][:400]

    if data.get("language") in ("english","egyptian_arabic","german"):
        out["language"] = data["language"]

    if data.get("emotion") in VALID_EMOTIONS:
        out["emotion"] = data["emotion"]

    try:
        conf = float(data.get("emotion_confidence", 0.5))
        out["emotion_confidence"] = max(0.0, min(1.0, conf))
    except Exception:
        pass

    n = data.get("need")
    out["need"] = n if n in ("food","water","bathroom","parent","pain") else None

    if data.get("intent") in VALID_INTENTS:
        out["intent"] = data["intent"]

    if data.get("open_tool") in VALID_TOOLS:
        out["open_tool"] = data["open_tool"]

    out["parent_alert"] = bool(data.get("parent_alert", False))

    at = data.get("alert_type")
    out["alert_type"] = at if at in VALID_ALERTS or at is None else None

    if data.get("voice_style") in VALID_VOICE_STYLES:
        out["voice_style"] = data["voice_style"]

    out["listening_after_reply"] = bool(data.get("listening_after_reply", True))

    rc = data.get("robot_command")
    if isinstance(rc, dict):
        out["robot_command"].update({k: str(v)[:40] for k, v in rc.items()
                                     if k in out["robot_command"]})

    mu = data.get("memory_update")
    if isinstance(mu, dict):
        out["memory_update"].update({k: str(v)[:80] if v is not None else None
                                     for k, v in mu.items()
                                     if k in out["memory_update"]})

    if isinstance(data.get("log_summary"), str):
        out["log_summary"] = data["log_summary"][:200]

    return out


class AIProvider(ABC):
    """Base class. Subclasses implement generate_response."""

    name = "base"
    available = False

    @abstractmethod
    def generate_response(self, child_input: str, child_profile: dict,
                          child_state: dict, session_history: list) -> dict:
        ...

    def status(self) -> dict:
        return {"name": self.name, "available": self.available}
