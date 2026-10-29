"""
ARIA Conversation Engine
========================
The voice-first brain of ARIA OS. It owns the always-listening loop and the

    STT  ->  intent router  ->  AI companion  ->  TTS  ->  listen again

pipeline, plus multi-turn cumulative memory. The shell (and later every tool
screen) simply subscribes to its signals — nothing in the UI talks to STT,
the AI providers, or TTS directly.

`listen_now()` is the tap-to-talk backup: the child can always tap ARIA's
button to make her listen immediately, even if hands-free detection is fussy
on a particular microphone.

One instance lives for the whole session, owned by ARIAMainWindow, so the
conversation and its memory survive screen changes.
"""

import threading

from PySide6.QtCore import QObject, Signal, QTimer

import database.db_manager as db
from core.auto_listening_engine import AutoListeningEngine, ListenState
from core.intent_router import route


from core.log import log as _log


# Spoken greeting per language ({name} is filled with the child's first name).
_GREETINGS = {
    "en": "Hi {name}! I'm ARIA. I'm right here with you. What would you like to do?",
    "ar": "أهلاً {name}! أنا أريا. أنا معاك هنا. تحب نعمل ايه النهارده؟",
    "de": "Hallo {name}! Ich bin ARIA. Ich bin hier bei dir. Was möchtest du tun?",
}
_OFFLINE = {
    "en": "I'm here with you. Let's do something calm together.",
    "ar": "أنا معاك. خلينا نعمل حاجة هادية سوا.",
    "de": "Ich bin bei dir. Lass uns etwas Ruhiges machen.",
}
# spoken when the camera notices sustained distress (gentle, never forced)
_COMFORT_OFFER = {
    "en": "I'm right here with you. Would you like a calm moment together?",
    "ar": "أنا معاك هنا. تحب ناخد لحظة هدوء سوا؟",
    "de": "Ich bin hier bei dir. Möchtest du einen ruhigen Moment?",
}


def _fallback_reply(lang: str) -> dict:
    return {
        "reply": _OFFLINE.get(lang, _OFFLINE["en"]),
        "face_expression": "calm", "tts_style": "soft",
        "suggested_activity": "none", "comfort_mode": False,
        "parent_alert": False, "memory_update": "", "reason": "offline",
    }


class ConversationEngine(QObject):
    """Always-on voice companion. The UI subscribes; it never drives STT/AI/TTS."""

    # ── public signals (UI subscribes) ───────────────────────────────
    state_changed      = Signal(str)     # ListenState value
    user_said          = Signal(str)     # final transcript ("you said: ...")
    aria_replied       = Signal(object)  # full AI response dict
    partial_volume     = Signal(float)   # live mic level 0..1
    navigate_requested = Signal(str)     # destination key for main._navigate
    comfort_triggered  = Signal()        # open the Calm Zone
    emotion_updated    = Signal(str)     # ambient emotion (camera, Phase 3)
    listening_error    = Signal(str)

    # ── internal cross-thread signals (worker thread -> Qt main) ─────
    _ai_ready  = Signal(object, str)
    _tts_ready = Signal()

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self.child_id = child_id
        self._child = db.get_child(child_id) or {}
        self._lang = self._child.get("language", "en")

        self._auto = AutoListeningEngine(child_id, self)
        self._auto.heard.connect(self._on_heard)
        self._auto.state_changed.connect(self.state_changed.emit)
        self._auto.volume.connect(self.partial_volume.emit)
        self._auto.error.connect(self._on_listen_error)

        self._history = []          # [{role, content}, ...] capped at 12
        self._emotion = "neutral"
        self._last_reply = ""
        self._started = False
        self._active = False        # is hands-free listening allowed right now
        self._pending_comfort = False
        self._manual_pending = False  # a tap-to-talk request is in flight
        self._tool_screen = None      # tool-voice mode: the open tool screen
        self._tool_voice = None       # its ScreenVoiceController
        self._speaking = False        # ARIA is currently producing speech
        self._speak_token = 0         # guards the TTS watchdog

        self._ai_ready.connect(self._on_ai_ready)
        self._tts_ready.connect(self._on_tts_ready)

    # ── lifecycle ────────────────────────────────────────────────────
    def is_started(self) -> bool:
        return self._started

    def start(self):
        """Called once when the shell first mounts: greet, then auto-listen."""
        if self._started:
            return
        _log("ConversationEngine.start() — ARIA will greet, then listen")
        self._started = True
        self._active = True
        self._auto.enable()
        try:
            db.update_child_last_active(self.child_id)
        except Exception:
            pass
        self._seed_memory()
        self._greet()

    def shutdown(self):
        _log("ConversationEngine.shutdown()")
        self._active = False
        self._started = False
        try:
            self._auto.shutdown()
        except Exception:
            pass
        self._stop_speech()

    def pause_listening(self):
        """Suspend the mic — used while a tool with its own mic/camera is open."""
        if self._active:
            _log("voice paused")
        self._active = False
        try:
            self._auto.disable()
        except Exception:
            pass
        self._stop_speech()

    def resume_listening(self):
        """Re-arm the hands-free mic when returning to the shell."""
        if not self._started:
            return
        _log("voice resumed (back on the shell)")
        self._active = True
        self._auto.enable()
        if not self._auto.is_busy():
            QTimer.singleShot(300, self._listen)

    def notify_presence(self, present: bool):
        """Face presence — a child appeared (wake) or left the view (idle)."""
        if present:
            _log("presence: a child is here")
            self.resume_listening()
        else:
            _log("presence: the child left — ARIA idles")
            self.pause_listening()

    def attach_tool(self, screen):
        """Enter tool-voice mode — keep listening, route commands to `screen`."""
        from core.screen_voice import ScreenVoiceController
        self._tool_screen = screen
        self._tool_voice = ScreenVoiceController(screen)
        self._pending_comfort = False
        self._manual_pending = False
        self._active = True
        self._auto.enable()
        _log(f"tool voice attached: {type(screen).__name__}")
        if self._auto.state not in (ListenState.LISTENING, ListenState.THINKING,
                                    ListenState.SPEAKING, ListenState.GREETING):
            QTimer.singleShot(350, self._listen)

    def detach_tool(self):
        """Leave tool-voice mode."""
        if self._tool_voice is not None:
            _log("tool voice detached")
        self._tool_screen = None
        self._tool_voice = None

    def set_emotion(self, emotion: str):
        """Feed an ambient emotion (camera) so ARIA's tone can adapt."""
        if emotion and emotion != self._emotion:
            self._emotion = emotion
            self.emotion_updated.emit(emotion)

    def announce_comfort(self):
        """Speak a gentle, camera-triggered comfort offer — only if ARIA is free."""
        if not self._started or not self._active:
            return
        if self._auto.state in (ListenState.THINKING, ListenState.SPEAKING,
                                 ListenState.GREETING, ListenState.OPENING):
            return   # don't talk over ARIA — the visual offer card still shows
        line = _COMFORT_OFFER.get(self._lang, _COMFORT_OFFER["en"])
        _log("camera distress -> ARIA gently offers a calm moment")
        self._last_reply = line
        self.aria_replied.emit({
            "reply": line, "face_expression": "comfort", "tts_style": "soft",
            "suggested_activity": "breathing", "comfort_mode": False,
            "parent_alert": False, "reason": "camera_comfort_offer",
        })
        self._speak(line, "soft")

    # ── tap-to-talk (manual backup) ──────────────────────────────────
    def listen_now(self):
        """Tap-to-talk: a reliable manual backup so the child is never stuck."""
        _log("tap-to-talk pressed")
        if not self._started:
            self.start()
            return
        if not self._active:
            _log("tap-to-talk ignored — voice is paused")
            return
        if self._auto.state == ListenState.THINKING:
            _log("tap-to-talk ignored — ARIA is still thinking")
            return
        self._pending_comfort = False
        self._manual_pending = True
        self._stop_speech()
        QTimer.singleShot(200, self._do_manual_listen)

    def _do_manual_listen(self):
        if self._manual_pending:
            self._manual_pending = False
            self._listen()

    # ── greeting + memory seed ───────────────────────────────────────
    def _seed_memory(self):
        """Load the last few exchanges so the conversation feels continuous."""
        try:
            recent = db.get_chat_logs(self.child_id, limit=3)
        except Exception:
            recent = []
        for row in reversed(recent or []):
            u, a = row.get("user_message"), row.get("aria_reply")
            if u:
                self._history.append({"role": "user", "content": u})
            if a:
                self._history.append({"role": "assistant", "content": a})
        self._history = self._history[-12:]

    def _greet(self):
        name = (self._child.get("name") or "").split(" ")[0]
        text = _GREETINGS.get(self._lang, _GREETINGS["en"]).format(name=name)
        text = text.replace("  ", " ").replace(" !", "!").replace(" .", ".")
        _log(f"greeting ({self._lang})")
        self._auto.set_state(ListenState.GREETING)
        self._last_reply = text
        self.aria_replied.emit({
            "reply": text, "face_expression": "happy", "tts_style": "soft",
            "suggested_activity": "none", "comfort_mode": False,
            "parent_alert": False, "reason": "greeting",
        })
        self._speak(text, "soft")

    # ── listening loop ───────────────────────────────────────────────
    def _listen(self):
        if self._active:
            self._auto.listen()

    def _on_heard(self, text):
        if not self._active:
            return
        if not text:
            # silence — quietly try again (anti-spin guard: only re-arm if a
            # cycle isn't already running)
            if self._auto.state != ListenState.LISTENING:
                QTimer.singleShot(400, self._listen)
            return
        self.user_said.emit(text)

        # Tool-voice mode: a tool screen is open — route commands to it.
        if self._tool_voice is not None:
            try:
                result = self._tool_voice.handle(text)
            except Exception as e:
                result = ""
                _log(f"tool voice error: {e}")
            _log(f"tool voice heard {text!r} -> {result or 'no match'}")
            if self._tool_voice is not None and self._active:
                QTimer.singleShot(320, self._listen)
            return

        self._auto.set_state(ListenState.HEARD)
        kind, payload = route(text)
        _log(f"routed {text!r} -> ({kind}, {payload})")
        if kind == "navigate":
            self._auto.set_state(ListenState.OPENING)
            self.navigate_requested.emit(payload)   # window pauses us on switch
        elif kind == "command":
            if payload == "stop":
                self._stop_speech()
                self._listen()
            elif payload == "repeat" and self._last_reply:
                self._speak(self._last_reply, "soft")
            else:
                self._listen()
        else:
            self._think(text)

    def _on_listen_error(self, msg):
        _log(f"listen error: {msg}")
        self.listening_error.emit(str(msg))
        if self._active and self._started:
            QTimer.singleShot(1500, self._listen)   # recover and keep going

    # ── AI thinking (off the UI thread) ──────────────────────────────
    def _think(self, text):
        _log("thinking… (asking the AI companion)")
        self._auto.set_state(ListenState.THINKING)
        history = list(self._history)
        emotion = self._emotion

        def worker():
            resp = None
            try:
                from ai.multi_provider import get_aria_response
                resp = get_aria_response(text, self.child_id, emotion,
                                         "shell", "none", chat_history=history)
            except Exception as e:                  # pragma: no cover
                _log(f"AI error: {e}")
            if not isinstance(resp, dict) or not resp.get("reply"):
                resp = _fallback_reply(self._lang)
            self._ai_ready.emit(resp, text)

        threading.Thread(target=worker, daemon=True).start()

    def _on_ai_ready(self, resp, user_text):
        if not self._active and not self._pending_comfort:
            # The child navigated away while ARIA was thinking — drop it.
            return
        reply = resp.get("reply", "")
        _log(f"AI replied: {reply[:70]!r}")

        # cumulative memory: keep the last 6 turns
        self._history.append({"role": "user", "content": user_text})
        self._history.append({"role": "assistant", "content": reply})
        self._history = self._history[-12:]
        self._last_reply = reply

        try:
            db.log_chat(self.child_id, user_text, reply,
                        detected_emotion=resp.get("face_expression", "neutral"),
                        suggested_activity=resp.get("suggested_activity", "none"),
                        comfort_mode=bool(resp.get("comfort_mode")))
        except Exception:
            pass
        mu = resp.get("memory_update")
        if mu:
            try:
                db.update_ai_memory(self.child_id, last_topic=str(mu)[:200])
            except Exception:
                pass
        if resp.get("parent_alert"):
            try:
                db.log_emotion(self.child_id, "distress", 0.9,
                               source="conversation", action="parent_alert")
            except Exception:
                pass

        self.aria_replied.emit(resp)
        self._pending_comfort = bool(resp.get("comfort_mode"))
        self._speak(reply, resp.get("tts_style", "soft"))

    # ── TTS (off the UI thread) ──────────────────────────────────────
    def _speak(self, text, style="soft"):
        if not text:
            self._after_speech()
            return
        _log(f"speaking ({len(text)} chars, style={style})")
        self._auto.set_state(ListenState.SPEAKING)
        self._speaking = True
        self._speak_token += 1
        token = self._speak_token
        cid = self.child_id

        def worker():
            try:
                from speech import tts_engine
                tts_engine.speak(text, child_id=cid, style=style, blocking=True)
            except Exception as e:                  # pragma: no cover
                _log(f"TTS error: {e}")
            self._tts_ready.emit()

        threading.Thread(target=worker, daemon=True).start()
        # watchdog — a stuck TTS must never freeze the conversation loop
        QTimer.singleShot(min(22000, max(7000, len(text) * 140)),
                          lambda: self._tts_watchdog(token))

    def _stop_speech(self):
        try:
            from speech.tts_engine import stop_speaking
            stop_speaking()
        except Exception:
            pass

    def _on_tts_ready(self):
        if not self._speaking:
            return
        self._speaking = False
        _log("speech finished")
        self._after_speech()

    def _tts_watchdog(self, token):
        """If TTS hangs, resume the loop anyway so ARIA never goes deaf."""
        if token == self._speak_token and self._speaking:
            _log("TTS watchdog — voice took too long, resuming listening")
            self._speaking = False
            self._after_speech()

    def _after_speech(self):
        if self._pending_comfort:
            self._pending_comfort = False
            self._auto.set_state(ListenState.COMFORT)
            self.comfort_triggered.emit()   # Calm Zone opens; window pauses us
            return
        if self._manual_pending:
            return                          # tap-to-talk will start the next listen
        if self._active and self._started:
            self._listen()

    # ── external text input (on-screen keyboard / dev box) ──────────
    def process_text(self, text):
        """Inject a typed line (Phase 4 on-screen keyboard) into the pipeline."""
        text = (text or "").strip()
        if not text:
            return
        self.user_said.emit(text)
        kind, payload = route(text)
        if kind == "navigate":
            self.navigate_requested.emit(payload)
        elif kind == "command" and payload == "repeat" and self._last_reply:
            self._speak(self._last_reply, "soft")
        else:
            self._think(text)
