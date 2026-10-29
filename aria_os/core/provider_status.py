"""Aggregates AI + Voice provider availability for the Parent Dashboard."""


def collect_status(ai_provider, tts_engine):
    out = {"ai": {}, "voice": [], "summary": "MockMode"}
    try:
        out["ai"] = ai_provider.status()
    except Exception as e:
        out["ai"] = {"name": "unknown", "available": False, "error": str(e)}
    try:
        out["voice"] = tts_engine.status() if tts_engine else []
    except Exception as e:
        out["voice"] = [{"name": "unknown", "available": False, "error": str(e)}]

    ai_ok = out["ai"].get("available") and out["ai"].get("name") == "Claude"
    voice_ok = any(v.get("name") == "ElevenLabs" and v.get("available") for v in out["voice"])

    if ai_ok and voice_ok:
        out["summary"] = "Premium (Claude + ElevenLabs)"
    elif ai_ok:
        out["summary"] = "Claude AI · Fallback voice"
    elif voice_ok:
        out["summary"] = "MockAI · ElevenLabs voice"
    else:
        out["summary"] = "MockMode · Offline"
    return out
