"""VoiceProvider base class + fallback chain (ElevenLabs → edge-tts → pyttsx3 → mock)."""

from abc import ABC, abstractmethod


class VoiceProvider(ABC):
    name = "base"
    available = False

    @abstractmethod
    def speak(self, text: str, language: str = "en", voice_style: str = "soft"): ...

    def stop(self): pass
    def set_voice(self, voice_id: str): pass
    def list_available_voices(self): return []
    def status(self): return {"name": self.name, "available": self.available}


class MockTTSProvider(VoiceProvider):
    """Silent TTS — prints what would be spoken. Used when nothing else works."""
    name = "MockTTS"
    available = True

    def speak(self, text, language="en", voice_style="soft"):
        print(f"[MockTTS speak ({language}/{voice_style})]: {text[:80]}")


class Pyttsx3Provider(VoiceProvider):
    """Offline Windows SAPI fallback."""
    name = "pyttsx3"

    def __init__(self):
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", 150)
            self._engine.setProperty("volume", 0.9)
            self.available = True
        except Exception as e:
            print(f"[pyttsx3 init failed: {e}]")
            self.available = False
            self._engine = None

    def speak(self, text, language="en", voice_style="soft"):
        if not self.available or not text:
            return
        try:
            import threading
            def _run():
                try:
                    self._engine.say(text)
                    self._engine.runAndWait()
                except Exception as e:
                    print(f"[pyttsx3 run error: {e}]")
            threading.Thread(target=_run, daemon=True).start()
        except Exception as e:
            print(f"[pyttsx3 thread error: {e}]")

    def stop(self):
        try:
            if self._engine:
                self._engine.stop()
        except Exception:
            pass


class EdgeTTSProvider(VoiceProvider):
    """Microsoft Edge neural voices. Free, offline-API-style."""
    name = "edge-tts"

    VOICE_MAP = {
        "en": "en-US-JennyNeural",
        "ar": "ar-EG-SalmaNeural",
        "de": "de-DE-KatjaNeural",
    }

    def __init__(self):
        try:
            import edge_tts  # noqa
            self.available = True
        except Exception:
            self.available = False

    def speak(self, text, language="en", voice_style="soft"):
        if not self.available or not text:
            return
        import threading
        threading.Thread(target=self._run, args=(text, language, voice_style),
                         daemon=True).start()

    def _run(self, text, language, voice_style):
        import asyncio, tempfile, os
        try:
            import edge_tts
            voice = self.VOICE_MAP.get(language[:2], self.VOICE_MAP["en"])
            rate = "-20%" if voice_style in ("soft", "calm") else "+0%"
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                tmp.close()
                async def gen():
                    com = edge_tts.Communicate(text, voice, rate=rate)
                    await com.save(tmp.name)
                loop.run_until_complete(gen())
            finally:
                loop.close()
            self._play_mp3(tmp.name)
            try: os.unlink(tmp.name)
            except Exception: pass
        except Exception as e:
            print(f"[edge-tts error: {e}]")

    def _play_mp3(self, path):
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            import time
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
        except Exception as e:
            print(f"[edge-tts play: {e}]")


class ElevenLabsProvider(VoiceProvider):
    """ElevenLabs premium TTS — API-ready. Falls back via VoiceManager."""
    name = "ElevenLabs"

    def __init__(self):
        import os
        from pathlib import Path
        self._key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
        if not self._key:
            env = Path(__file__).parent.parent / ".env"
            if env.exists():
                try:
                    for line in env.read_text().splitlines():
                        if line.startswith("ELEVENLABS_API_KEY="):
                            self._key = line.split("=", 1)[1].strip().strip('"').strip("'")
                            break
                except Exception:
                    pass
        self._voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "").strip() or "21m00Tcm4TlvDq8ikWAM"
        self._model = os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")
        self.available = bool(self._key)

    def set_voice(self, voice_id):
        self._voice_id = voice_id

    def speak(self, text, language="en", voice_style="soft"):
        if not self.available or not text:
            return
        import threading
        threading.Thread(target=self._run, args=(text,), daemon=True).start()

    def _run(self, text):
        import requests, tempfile, os
        try:
            r = requests.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{self._voice_id}",
                headers={"xi-api-key": self._key, "Content-Type": "application/json",
                         "Accept": "audio/mpeg"},
                json={"text": text, "model_id": self._model,
                      "voice_settings": {"stability": 0.55, "similarity_boost": 0.85,
                                         "style": 0.4, "use_speaker_boost": True}},
                timeout=30,
            )
            if r.status_code != 200:
                print(f"[ElevenLabs HTTP {r.status_code}]")
                return
            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            tmp.write(r.content); tmp.close()
            self._play(tmp.name)
            try: os.unlink(tmp.name)
            except Exception: pass
        except Exception as e:
            print(f"[ElevenLabs error: {e}]")

    def _play(self, path):
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            import time
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
        except Exception:
            pass
