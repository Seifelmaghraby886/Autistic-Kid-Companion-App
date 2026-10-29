"""AppController — wires every engine together and owns the lifecycle."""

import os
from pathlib import Path

from PySide6.QtCore import QObject, Signal, QTimer

from core.ai_shell import AIShell
from core.mock_ai import MockAIProvider
from core.claude_provider import ClaudeProvider
from core.tts_engine import TTSEngine
from core.speech_engine import SpeechEngine
from core.auto_listening_engine import AutoListeningEngine, State
from core.tool_launcher import ToolLauncher
from core.robot_bridge import RobotBridge
from core.provider_status import collect_status
from data import database as db
from data.seed_data import seed


def _load_env():
    """Tiny .env loader (no dependency)."""
    env = Path(__file__).parent.parent / ".env"
    if not env.exists():
        return
    try:
        for line in env.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            v = v.strip().strip('"').strip("'")
            if k.strip() and v and k.strip() not in os.environ:
                os.environ[k.strip()] = v
    except Exception:
        pass


class AppController(QObject):
    """Top-level coordinator. UI talks ONLY to this class."""

    # Outward signals (UI subscribes)
    aria_replied = Signal(dict)        # full JSON response
    state_changed = Signal(str)        # auto-listening state name
    transcript = Signal(str)           # last transcript
    listening_started = Signal()
    error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        _load_env()

        # DB + seed defaults
        seed()
        self.child_id = db.get_or_create_default_child()
        self.parent_id = db.get_or_create_default_parent()
        self.session_id = db.start_session(self.child_id, mode="shell")

        # AI provider chain: Claude → Mock
        self._claude = ClaudeProvider()
        self._mock = MockAIProvider()
        self.ai = self._claude if self._claude.available else self._mock

        # Voice + speech
        self.tts = TTSEngine()
        self.speech = SpeechEngine(language=db.get_child(self.child_id).get("language","en"))
        self.speech.transcription_ready.connect(self._on_transcription)
        self.speech.error.connect(self._on_speech_error)
        self.speech.listening_started.connect(self.listening_started.emit)

        # Auto-listening state machine
        self.listening = AutoListeningEngine(speech_engine=self.speech)
        self.listening.state_changed.connect(self.state_changed.emit)
        self.listening.error.connect(self.error.emit)

        # Tool launcher + robot
        self.tools = ToolLauncher()
        self.robot = RobotBridge(self.child_id)

        # AIShell wires AI + memory + tools + robot
        self.shell = AIShell(self.child_id, self.session_id,
                             self.ai, self.tools, self.robot)
        self.shell.reply_ready.connect(self._on_ai_reply)
        self.shell.error.connect(self.error.emit)

        self._auto_listening_enabled = True
        self._in_parent_mode = False

    # ── Lifecycle ────────────────────────────────────────────────
    def start(self):
        """Called by Shell UI after mount. Greets, then starts auto-listening."""
        self.listening.start()  # → GREETING
        profile = db.get_child(self.child_id) or {}
        lang = profile.get("language", "en")
        name = profile.get("name", "")
        greet = self._greeting(lang, name)
        self.aria_replied.emit({
            "reply": greet, "language": lang, "emotion": "happy",
            "voice_style": "soft", "listening_after_reply": True,
            "open_tool": "none",
        })
        self.tts.speak(greet, language=lang, voice_style="soft")
        # Brief greeting pause, then start listening
        QTimer.singleShot(2000, self._begin_listening)

    def _greeting(self, lang, name):
        nm = (" يا " + name) if (name and lang == "ar") else (", " + name if name else "")
        return {
            "ar": f"أهلاً{nm}! أنا أريا. تحب نتكلم؟",
            "en": f"Hi{nm}! I'm ARIA. What's on your mind?",
            "de": f"Hallo{nm}! Ich bin ARIA. Worüber möchtest du reden?",
        }.get(lang, f"Hi{nm}! I'm ARIA.")

    def _begin_listening(self):
        if self._auto_listening_enabled and not self._in_parent_mode:
            self.listening._begin_listening()

    # ── Voice + STT plumbing ────────────────────────────────────
    def _on_transcription(self, text):
        self.transcript.emit(text or "")
        if not text or not text.strip():
            # Silent — just resume listening
            self.listening.set_state(State.RETURNING_TO_LISTEN)
            QTimer.singleShot(600, self._begin_listening)
            return
        self.process_input(text)

    def _on_speech_error(self, msg):
        self.error.emit(msg)

    # ── Main input entry (voice OR developer text) ──────────────
    def process_input(self, text):
        """Run the full pipeline on text. UI calls this for dev text input too."""
        self.listening.pause_for_speaking()
        response = self.shell.process(text)
        # speak reply
        reply = response.get("reply", "")
        lang = response.get("language", "english")
        lang_short = {"english":"en","egyptian_arabic":"ar","german":"de"}.get(lang,"en")
        voice_style = response.get("voice_style", "soft")
        self.tts.speak(reply, language=lang_short, voice_style=voice_style)
        # After speaking, return to listening (unless safety/parent stops us)
        if response.get("listening_after_reply", True) and \
           response.get("open_tool") != "parent_pin":
            QTimer.singleShot(max(1500, min(8000, len(reply) * 80)),
                              self._after_speaking)
        return response

    def _after_speaking(self):
        if self._in_parent_mode:
            return
        self.listening.resume_after_speaking()

    def _on_ai_reply(self, response):
        self.aria_replied.emit(response)

    # ── External controls ───────────────────────────────────────
    def enter_parent_mode(self):
        self._in_parent_mode = True
        self.listening.enter_parent_mode()

    def exit_parent_mode(self):
        self._in_parent_mode = False
        self.listening.exit_parent_mode()

    def set_auto_listening(self, enabled: bool):
        self._auto_listening_enabled = bool(enabled)
        if not enabled:
            self.speech.stop_microphone()

    def shutdown(self):
        try:
            self.speech.stop_microphone()
            db.end_session(self.session_id, summary="Session ended")
        except Exception:
            pass

    # ── Provider mgmt ───────────────────────────────────────────
    def refresh_providers(self):
        """Re-read API keys + rebuild fallback chains."""
        _load_env()
        self._claude = ClaudeProvider()
        self.ai = self._claude if self._claude.available else self._mock
        self.shell.set_ai_provider(self.ai)
        self.tts.refresh()

    def provider_status(self):
        return collect_status(self.ai, self.tts)
