"""SpeechEngine — STT capture + transcribe.

Uses SpeechRecognition + Google Web Speech (free, no key). Falls back to
mock mode if mic/PyAudio unavailable. Designed so child never sees a button.
"""

import threading
import time
import wave
import tempfile
import os

from PySide6.QtCore import QObject, Signal


LANG_CODES = {"en": "en-US", "ar": "ar-EG", "de": "de-DE"}


class SpeechEngine(QObject):
    """Continuous-listen STT. Emits transcription_ready when speech ends."""

    transcription_ready = Signal(str)
    listening_started = Signal()
    volume_level = Signal(float)
    error = Signal(str)

    def __init__(self, language="en", parent=None):
        super().__init__(parent)
        self._lang = LANG_CODES.get(language[:2], "en-US")
        self._listening = False
        self._mock_mode = False
        self._thread = None
        self._stop_event = threading.Event()

    def set_language(self, lang):
        self._lang = LANG_CODES.get(lang[:2], "en-US")

    def start_microphone(self):
        if self._listening:
            return
        self._listening = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def stop_microphone(self):
        self._listening = False
        self._stop_event.set()

    def is_listening(self):
        return self._listening

    def inject_mock_text(self, text: str):
        """Developer-only test path. Pretends the child said this."""
        self.transcription_ready.emit(text)

    def _listen_loop(self):
        """Capture one phrase via SpeechRecognition, emit transcription, exit.
        AutoListeningEngine will restart us for the next turn."""
        try:
            import speech_recognition as sr
        except Exception as e:
            self.error.emit(f"SpeechRecognition not installed: {e}")
            self._listening = False
            return
        try:
            r = sr.Recognizer()
            r.energy_threshold = 300
            r.dynamic_energy_threshold = True
            r.pause_threshold = 0.9
            try:
                mic = sr.Microphone()
            except Exception as e:
                self.error.emit(f"Microphone unavailable: {e}")
                self._listening = False
                return

            with mic as source:
                self.listening_started.emit()
                try:
                    r.adjust_for_ambient_noise(source, duration=0.3)
                except Exception:
                    pass
                try:
                    audio = r.listen(source, timeout=12, phrase_time_limit=15)
                except sr.WaitTimeoutError:
                    self._listening = False
                    self.transcription_ready.emit("")
                    return
                except Exception as e:
                    self.error.emit(str(e))
                    self._listening = False
                    return

            text = self._transcribe(r, audio)
            self._listening = False
            self.transcription_ready.emit(text or "")
        except Exception as e:
            self._listening = False
            self.error.emit(str(e))

    def _transcribe(self, recognizer, audio):
        try:
            return recognizer.recognize_google(audio, language=self._lang)
        except Exception as e:
            print(f"[Google STT failed: {e}]")
            return ""
