"""
ARIA Provider Control
=====================
Central on/off control for every AI, TTS and STT provider. The Provider
Control Center screen flips these switches; the engines read them so a
parent or developer can choose exactly which services run at any moment.

State lives in config/app_config.json under "providers_enabled", so it
survives restarts and takes effect live — the engines re-read the config
on every request, so a toggle applies to the very next AI reply / spoken
line / transcription with no restart needed.
"""

import json
from pathlib import Path

_CFG_PATH = Path(__file__).parent.parent / "config" / "app_config.json"

# provider key -> default enabled.  Prefixes: ai_ / tts_ / stt_
DEFAULT_PROVIDERS = {
    # AI brain — tried top-to-bottom; first enabled + reachable one wins
    "ai_groq":        True,
    "ai_cerebras":    True,
    "ai_gemini":      True,
    "ai_openrouter":  True,
    "ai_anthropic":   True,
    "ai_openai":      True,
    "ai_ollama":      False,
    # ARIA's voice (TTS)
    "tts_elevenlabs": True,
    "tts_edge":       True,
    "tts_pyttsx3":    True,
    # Listening (STT)
    "stt_elevenlabs": True,
    "stt_whisper":    True,
    "stt_google":     True,
}


def _load() -> dict:
    try:
        from core.secrets import merge_secrets
        return merge_secrets(json.loads(_CFG_PATH.read_text(encoding="utf-8")))
    except Exception:
        return {}


def _save(cfg: dict) -> bool:
    try:
        from core.secrets import strip_secrets
        _CFG_PATH.write_text(
            json.dumps(strip_secrets(cfg), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return True
    except Exception:
        return False


def enabled_in(cfg: dict, key: str) -> bool:
    """Check a provider against an already-loaded config dict (no file read)."""
    table = (cfg or {}).get("providers_enabled", {})
    return bool(table.get(key, DEFAULT_PROVIDERS.get(key, True)))


def is_enabled(key: str) -> bool:
    """Check a provider, reading config from disk (when no cfg is at hand)."""
    return enabled_in(_load(), key)


def all_states() -> dict:
    """Return {key: bool} for every provider, with defaults filled in."""
    table = _load().get("providers_enabled", {})
    return {k: bool(table.get(k, d)) for k, d in DEFAULT_PROVIDERS.items()}


def set_enabled(key: str, value: bool) -> bool:
    """Flip one provider on/off and persist it. Returns True on success."""
    if key not in DEFAULT_PROVIDERS:
        return False
    cfg = _load()
    table = cfg.get("providers_enabled", {})
    for k, d in DEFAULT_PROVIDERS.items():   # keep the file self-documenting
        table.setdefault(k, d)
    table[key] = bool(value)
    cfg["providers_enabled"] = table
    return _save(cfg)


def set_api_key(cfg_key: str, value: str) -> bool:
    """Save (or clear) an API key in app_config.json. Returns True on success."""
    value = (value or "").strip()
    if not value:
        from core.secrets import clear_secret
        clear_secret(cfg_key)
    cfg = _load()
    cfg[cfg_key] = value
    return _save(cfg)


def get_api_key(cfg_key: str) -> str:
    """Read an API key from app_config.json (empty string if unset)."""
    return str(_load().get(cfg_key, "") or "")
