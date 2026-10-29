"""
ARIA TTS Engine — RELIABLE audio playback.
edge-tts → mp3 file → pygame mixer playback.
"""

import asyncio
import os
import re
import tempfile
import threading
import time
import database.db_manager as db


# Emoji / symbol ranges that TTS engines mispronounce or spell out one letter
# at a time. Stripped from the spoken text only — the on-screen text keeps them.
_EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF"
    "\U00002190-\U000021FF\U00002B00-\U00002BFF\U0000FE00-\U0000FE0F]+",
    flags=re.UNICODE,
)


def _clean_speech_text(text: str) -> str:
    """Strip emojis and markdown so the voice never spells symbols aloud."""
    if not text:
        return text
    text = _EMOJI_RE.sub(" ", text)
    for ch in ("*", "`", "#", "_", "~", "<", ">"):
        text = text.replace(ch, "")
    return re.sub(r"\s+", " ", text).strip()


VOICE_MAP = {
    "en": {"default": "en-US-JennyNeural",  "soft": "en-US-AnaNeural",   "slow": "en-US-AriaNeural"},
    "ar": {"default": "ar-EG-SalmaNeural",  "soft": "ar-EG-SalmaNeural", "slow": "ar-EG-ShakirNeural"},
    "de": {"default": "de-DE-KatjaNeural",  "soft": "de-DE-KatjaNeural", "slow": "de-DE-AmalaNeural"},
}


# ElevenLabs Egyptian voices (premium, much better than edge-tts)
# Users can set elevenlabs_voice_id in config.
ELEVEN_DEFAULT_VOICE = {
    "ar": "EXAVITQu4vr4xnSDxMaL",  # default fallback if no voice configured
    "en": "EXAVITQu4vr4xnSDxMaL",
    "de": "EXAVITQu4vr4xnSDxMaL",
}

TTS_STYLE_RATE = {
    "very_slow": "-30%",
    "soft":      "-15%",
    "normal":    "+0%",
}

_tts_lock = threading.Lock()
_pygame_initialized = False
_finish_callbacks = []

# Mark as initialized if pre-init was done in main()
try:
    import pygame
    if pygame.mixer.get_init():
        _pygame_initialized = True
except Exception:
    pass


def on_speech_finished(callback):
    """Register a callback that fires when current speech ends."""
    _finish_callbacks.append(callback)


def clear_finished_callbacks():
    _finish_callbacks.clear()


def _init_pygame():
    """Initialize pygame mixer once. Try multiple configs."""
    global _pygame_initialized
    if _pygame_initialized:
        return True
    try:
        import pygame
        # Try a robust config
        configs = [
            (44100, -16, 2, 1024),
            (24000, -16, 2, 512),
            (22050, -16, 1, 1024),
        ]
        for freq, size, ch, buf in configs:
            try:
                pygame.mixer.quit()  # ensure clean state
            except Exception:
                pass
            try:
                pygame.mixer.init(frequency=freq, size=size, channels=ch, buffer=buf)
                _pygame_initialized = True
                print(f"[pygame mixer ok @ {freq}Hz]")
                return True
            except Exception as e:
                print(f"[pygame mixer config {freq}Hz failed: {e}]")
                continue
        return False
    except Exception as e:
        print(f"[pygame import failed: {e}]")
        return False


def _detect_text_language(text: str) -> str:
    """Detect language from text characters (fallback when child not set)."""
    arabic_chars = sum(1 for c in text if '؀' <= c <= 'ۿ' or 'ݐ' <= c <= 'ݿ')
    if arabic_chars > len(text) * 0.15:
        return "ar"
    # German has ä, ö, ü, ß
    german_chars = sum(1 for c in text if c in 'äöüÄÖÜß')
    if german_chars > 0:
        return "de"
    return "en"


def _voice_matches_lang(voice_name: str, lang: str) -> bool:
    """Check if the voice name's locale matches the language."""
    if not voice_name:
        return False
    prefix = {"en": "en-", "ar": "ar-", "de": "de-"}.get(lang, "en-")
    return voice_name.startswith(prefix)


def speak(text: str, child_id: int = None, style: str = "soft", blocking: bool = False,
          force_lang: str = None):
    """Speak text aloud. Auto-picks voice from text language."""
    if not text or not text.strip():
        return
    text = _clean_speech_text(text)
    if not text:
        return

    # Determine the language to use
    lang = "en"
    if force_lang:
        lang = force_lang
    elif child_id:
        try:
            child = db.get_child(child_id)
            if child:
                lang = child.get("language", "en")
        except Exception:
            pass

    # Always cross-check with text content — if text contains Arabic but lang says English, switch
    detected = _detect_text_language(text)
    if detected != "en":
        # Trust detection over child setting (in case AI replied in different language)
        lang = detected

    # Pick voice based on FINAL language
    voice_name = VOICE_MAP.get(lang, VOICE_MAP["en"])["default"]

    # Allow override from saved settings ONLY if it matches the language
    if child_id:
        try:
            voice_settings = db.get_voice_settings(child_id) or {}
            stored_voice = voice_settings.get("voice_name")
            if stored_voice and _voice_matches_lang(stored_voice, lang):
                voice_name = stored_voice
            stored_style = voice_settings.get("voice_style")
            if stored_style:
                style = stored_style
        except Exception:
            pass

    rate = TTS_STYLE_RATE.get(style, "-15%")

    if blocking:
        _do_speak(text, voice_name, rate)
    else:
        threading.Thread(target=_do_speak, args=(text, voice_name, rate), daemon=True).start()


def _do_speak(text, voice, rate):
    """Generate audio with best available TTS and play with pygame."""
    if not _tts_lock.acquire(blocking=False):
        return
    try:
        # Use ElevenLabs whenever an API key is present — far better Egyptian
        # Arabic and English-inside-Arabic than edge-tts. A parent can force
        # edge-tts only by setting "tts_preferred": "edge" in app_config.json.
        cfg = _load_tts_config()
        tts_pref = cfg.get("tts_preferred", "auto")
        eleven_key = (cfg.get("elevenlabs_api_key") or "").strip()
        try:
            from core.provider_control import enabled_in
        except Exception:
            def enabled_in(_cfg, _key):   # control unavailable -> treat as ON
                return True

        if eleven_key and tts_pref != "edge" and enabled_in(cfg, "tts_elevenlabs"):
            try:
                mp3 = _generate_elevenlabs_mp3(text, eleven_key, cfg)
                if mp3 and os.path.exists(mp3):
                    _play_with_pygame(mp3)
                    try: os.unlink(mp3)
                    except Exception: pass
                    return
            except Exception as e:
                print(f"[ElevenLabs failed: {e}, falling back to edge-tts]")

        # edge-tts
        if enabled_in(cfg, "tts_edge"):
            try:
                mp3_path = _generate_edge_tts_mp3(text, voice, rate)
                if mp3_path and os.path.exists(mp3_path):
                    _play_with_pygame(mp3_path)
                    try: os.unlink(mp3_path)
                    except Exception: pass
                    return
            except Exception as e:
                print(f"[edge-tts failed: {e}, falling back to pyttsx3]")

        # offline Windows voice (pyttsx3)
        if enabled_in(cfg, "tts_pyttsx3"):
            _speak_pyttsx3(text)
    finally:
        _tts_lock.release()
        for cb in list(_finish_callbacks):
            try: cb()
            except Exception: pass


def _load_tts_config():
    try:
        import json
        from pathlib import Path
        with open(Path(__file__).parent.parent / "config" / "app_config.json") as f:
            return json.load(f)
    except Exception:
        return {}


def _generate_elevenlabs_mp3(text, api_key, cfg):
    """ElevenLabs TTS — premium quality Arabic via Multilingual v2 model."""
    import requests, tempfile
    voice_id = cfg.get("elevenlabs_voice_id", "").strip()
    if not voice_id:
        # Default voice
        voice_id = "EXAVITQu4vr4xnSDxMaL"
    model_id = cfg.get("elevenlabs_model", "eleven_multilingual_v2")
    resp = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        json={
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": 0.55,
                "similarity_boost": 0.85,
                "style": 0.40,
                "use_speaker_boost": True,
            },
        },
        timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"ElevenLabs HTTP {resp.status_code}: {resp.text[:120]}")
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.write(resp.content)
    tmp.close()
    return tmp.name


def _generate_edge_tts_mp3(text, voice, rate) -> str:
    """Generate mp3 with edge-tts, return file path."""
    try:
        import edge_tts
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)

            async def gen():
                tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                tmp.close()
                communicate = edge_tts.Communicate(text, voice, rate=rate)
                await communicate.save(tmp.name)
                return tmp.name

            return loop.run_until_complete(gen())
        finally:
            loop.close()
    except Exception as e:
        print(f"[edge-tts gen error: {e}]")
        return None


def _play_with_pygame(path):
    """Play mp3 via pygame mixer (reliable on Windows)."""
    if not _init_pygame():
        return
    try:
        import pygame
        # Stop any prior sound
        pygame.mixer.music.stop()
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(0.9)
        pygame.mixer.music.play()
        # Wait until playback finishes
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)
    except Exception as e:
        print(f"[pygame play error: {e}]")


def _speak_pyttsx3(text):
    """Final fallback: Windows SAPI via pyttsx3."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 0.9)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"[pyttsx3 error: {e}]")


def stop_speaking():
    """Stop current playback."""
    try:
        import pygame
        if _pygame_initialized:
            pygame.mixer.music.stop()
    except Exception:
        pass


def get_available_voices(lang="en"):
    try:
        import edge_tts
        async def _get():
            voices = await edge_tts.list_voices()
            prefix = {"en": "en", "ar": "ar", "de": "de"}.get(lang, "en")
            return [v for v in voices if v["Locale"].startswith(prefix)]
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(_get())
        finally:
            loop.close()
    except Exception:
        return []
