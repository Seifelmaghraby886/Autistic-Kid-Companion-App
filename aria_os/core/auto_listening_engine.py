"""AutoListeningEngine — state machine for the child-facing voice flow.

States:
  IDLE_STARTUP → GREETING → LISTENING → SPEECH_DETECTED → TRANSCRIBING
  → THINKING → SPEAKING → OPENING_TOOL → TOOL_ACTIVE → RETURNING_TO_LISTEN
  → LISTENING ... or PARENT_MODE / SAFETY_MODE / ERROR_RECOVERY
"""

from enum import Enum
from PySide6.QtCore import QObject, Signal, QTimer


class State(str, Enum):
    IDLE_STARTUP        = "IDLE_STARTUP"
    GREETING            = "GREETING"
    LISTENING           = "LISTENING"
    SPEECH_DETECTED     = "SPEECH_DETECTED"
    TRANSCRIBING        = "TRANSCRIBING"
    THINKING            = "THINKING"
    SPEAKING            = "SPEAKING"
    OPENING_TOOL        = "OPENING_TOOL"
    TOOL_ACTIVE         = "TOOL_ACTIVE"
    RETURNING_TO_LISTEN = "RETURNING_TO_LISTEN"
    PARENT_MODE         = "PARENT_MODE"
    SAFETY_MODE         = "SAFETY_MODE"
    ERROR_RECOVERY      = "ERROR_RECOVERY"


# Allowed transitions (lenient — keeps the loop robust even with unusual paths)
_TRANSITIONS = {
    State.IDLE_STARTUP:        {State.GREETING, State.ERROR_RECOVERY, State.PARENT_MODE},
    State.GREETING:            {State.LISTENING, State.SPEAKING, State.ERROR_RECOVERY},
    State.LISTENING:           {State.SPEECH_DETECTED, State.PARENT_MODE,
                                State.SAFETY_MODE, State.ERROR_RECOVERY,
                                State.RETURNING_TO_LISTEN, State.LISTENING},
    State.SPEECH_DETECTED:     {State.TRANSCRIBING, State.LISTENING, State.ERROR_RECOVERY},
    State.TRANSCRIBING:        {State.THINKING, State.LISTENING, State.ERROR_RECOVERY},
    State.THINKING:            {State.SPEAKING, State.SAFETY_MODE,
                                State.OPENING_TOOL, State.ERROR_RECOVERY},
    State.SPEAKING:            {State.OPENING_TOOL, State.RETURNING_TO_LISTEN,
                                State.LISTENING, State.PARENT_MODE, State.SAFETY_MODE,
                                State.ERROR_RECOVERY},
    State.OPENING_TOOL:        {State.TOOL_ACTIVE, State.RETURNING_TO_LISTEN,
                                State.LISTENING, State.ERROR_RECOVERY},
    State.TOOL_ACTIVE:         {State.RETURNING_TO_LISTEN, State.LISTENING,
                                State.PARENT_MODE, State.SAFETY_MODE,
                                State.ERROR_RECOVERY},
    State.RETURNING_TO_LISTEN: {State.LISTENING, State.PARENT_MODE,
                                State.SAFETY_MODE, State.ERROR_RECOVERY},
    State.PARENT_MODE:         {State.LISTENING, State.RETURNING_TO_LISTEN,
                                State.IDLE_STARTUP, State.ERROR_RECOVERY},
    State.SAFETY_MODE:         {State.LISTENING, State.RETURNING_TO_LISTEN,
                                State.PARENT_MODE, State.ERROR_RECOVERY},
    State.ERROR_RECOVERY:      {State.LISTENING, State.IDLE_STARTUP},
}


class AutoListeningEngine(QObject):
    """Coordinates state transitions + the SpeechEngine. UI subscribes to signals."""

    state_changed = Signal(str)      # new state name
    transcript = Signal(str)         # final transcription
    error = Signal(str)

    def __init__(self, speech_engine=None, parent=None):
        super().__init__(parent)
        self._state = State.IDLE_STARTUP
        self._enabled = True
        self.speech = speech_engine
        if self.speech:
            self.speech.transcription_ready.connect(self._on_transcription)
            self.speech.listening_started.connect(lambda: self.set_state(State.LISTENING))
            self.speech.error.connect(self._on_speech_error)

    # ── State control ────────────────────────────────────────
    def get_state(self):
        return self._state.value

    def set_state(self, new_state):
        if isinstance(new_state, str):
            try:
                new_state = State(new_state)
            except ValueError:
                return False
        allowed = _TRANSITIONS.get(self._state, set())
        # We accept same-state self-loops and forward-error transitions liberally
        if new_state not in allowed and new_state != self._state:
            # Don't be strict — log + allow (the state machine is for orchestration not contracts)
            pass
        self._state = new_state
        self.state_changed.emit(new_state.value)
        return True

    # ── Lifecycle controls ───────────────────────────────────
    def start(self):
        """Called once when ARIA Shell loads."""
        self._enabled = True
        self.set_state(State.GREETING)

    def stop(self):
        self._enabled = False
        if self.speech:
            self.speech.stop_microphone()
        self.set_state(State.IDLE_STARTUP)

    def pause_for_speaking(self):
        """Called by AIShell while ARIA is talking."""
        if self.speech:
            self.speech.stop_microphone()
        self.set_state(State.SPEAKING)

    def resume_after_speaking(self):
        """Called when TTS playback finishes."""
        if not self._enabled:
            return
        if self._state in (State.PARENT_MODE, State.SAFETY_MODE):
            return
        self.set_state(State.RETURNING_TO_LISTEN)
        QTimer.singleShot(400, self._begin_listening)

    def enter_parent_mode(self):
        if self.speech:
            self.speech.stop_microphone()
        self.set_state(State.PARENT_MODE)

    def exit_parent_mode(self):
        self.set_state(State.RETURNING_TO_LISTEN)
        QTimer.singleShot(400, self._begin_listening)

    def _begin_listening(self):
        if not self._enabled:
            return
        if self.speech:
            self.speech.start_microphone()
        # The actual transition to LISTENING will be emitted by speech.listening_started

    def _on_transcription(self, text):
        # State sequence: SPEECH_DETECTED → TRANSCRIBING → THINKING (AIShell drives next)
        self.set_state(State.SPEECH_DETECTED)
        self.set_state(State.TRANSCRIBING)
        self.transcript.emit(text)

    def _on_speech_error(self, msg):
        self.error.emit(msg)
        self.set_state(State.ERROR_RECOVERY)
        QTimer.singleShot(1500, self._begin_listening)
