"""TTS Engine — coordinates VoiceProvider fallback chain."""

from core.voice_provider import (
    VoiceProvider, MockTTSProvider, Pyttsx3Provider,
    EdgeTTSProvider, ElevenLabsProvider
)


class TTSEngine:
    def __init__(self):
        self._on_finish = None
        self.providers = self._build_chain()
        self.active = next((p for p in self.providers if p.available), MockTTSProvider())

    def _build_chain(self):
        chain = []
        for cls in (ElevenLabsProvider, EdgeTTSProvider, Pyttsx3Provider, MockTTSProvider):
            try:
                inst = cls()
                chain.append(inst)
            except Exception as e:
                print(f"[TTS chain skip {cls.__name__}: {e}]")
        return chain

    def refresh(self):
        """Re-init chain (e.g. after API key changes)."""
        self.providers = self._build_chain()
        self.active = next((p for p in self.providers if p.available), MockTTSProvider())

    def status(self):
        return [p.status() for p in self.providers]

    def speak(self, text, language="en", voice_style="soft"):
        if not text:
            return
        try:
            self.active.speak(text, language, voice_style)
        except Exception as e:
            print(f"[TTS error: {e}]")
        if self._on_finish:
            # Approximate: fire after speak call (real audio thread fires elsewhere)
            from PySide6.QtCore import QTimer
            QTimer.singleShot(max(800, min(6000, len(text) * 60)), self._on_finish)

    def stop(self):
        try:
            self.active.stop()
        except Exception:
            pass

    def on_finished(self, callback):
        self._on_finish = callback

    def set_voice(self, voice_id):
        try:
            self.active.set_voice(voice_id)
        except Exception:
            pass

    def set_provider(self, name):
        """Force a specific provider by name."""
        for p in self.providers:
            if p.name == name and p.available:
                self.active = p
                return True
        return False
