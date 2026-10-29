"""
ARIA Auto-Listening Engine
==========================
A small Qt state machine that gives ARIA a continuous, hands-free microphone.
It owns the lifecycle of one `STTWorker` per listening cycle and exposes the
result through signals. The ConversationEngine drives it: after ARIA finishes
speaking it calls `listen()` again, so the child never has to press a button.

Every step prints an `[ARIA-OS]` diagnostic line so a parent/developer can see
exactly what the microphone is doing in the console.

States:  IDLE -> GREETING -> LISTENING -> HEARD -> THINKING -> SPEAKING
         -> (OPENING a tool | back to LISTENING) ;  PAUSED / COMFORT / ERROR
"""

from enum import Enum
from PySide6.QtCore import QObject, Signal


from core.log import log as _log


class ListenState(str, Enum):
    IDLE      = "IDLE"
    GREETING  = "GREETING"
    LISTENING = "LISTENING"
    HEARD     = "HEARD"
    THINKING  = "THINKING"
    SPEAKING  = "SPEAKING"
    OPENING   = "OPENING"
    PAUSED    = "PAUSED"
    COMFORT   = "COMFORT"
    ERROR     = "ERROR"


_BUSY = {ListenState.GREETING, ListenState.THINKING,
         ListenState.SPEAKING, ListenState.OPENING}


class AutoListeningEngine(QObject):
    """Continuous hands-free microphone loop. One STT cycle per `listen()`."""

    state_changed   = Signal(str)    # ListenState value
    listening_began = Signal()       # mic warmed up, child may speak now
    heard           = Signal(str)    # final transcript (may be "")
    volume          = Signal(float)  # live mic level 0..1
    error           = Signal(str)

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self.child_id = child_id
        self._state = ListenState.IDLE
        self._enabled = False
        self._stt = None
        # Generous silence window — autistic children often speak with long
        # pauses between words; a short window cuts them off mid-sentence.
        self.max_record_seconds = 20
        self.silence_seconds = 3.5

    # ── state ────────────────────────────────────────────────────────
    @property
    def state(self) -> ListenState:
        return self._state

    def is_busy(self) -> bool:
        return self._state in _BUSY

    def set_state(self, new_state):
        if not isinstance(new_state, ListenState):
            try:
                new_state = ListenState(new_state)
            except ValueError:
                return
        if new_state is self._state:
            return
        self._state = new_state
        self.state_changed.emit(new_state.value)

    # ── enable / disable ─────────────────────────────────────────────
    def enable(self):
        self._enabled = True

    def disable(self):
        """Stop listening immediately and forbid new cycles."""
        self._enabled = False
        self._stop_stt()
        if self._state not in (ListenState.IDLE,):
            self.set_state(ListenState.PAUSED)

    @property
    def enabled(self) -> bool:
        return self._enabled

    # ── one listening cycle ──────────────────────────────────────────
    def listen(self):
        """Begin a single hands-free listening cycle (VAD auto-stops it)."""
        if not self._enabled:
            _log("auto-listen: listen() skipped — engine is disabled")
            return
        self._stop_stt()
        try:
            from speech.stt_engine import STTWorker
            _log("auto-listen: opening the microphone…")
            self._stt = STTWorker(
                self.child_id,
                auto_stop_on_silence=True,
                silence_seconds=self.silence_seconds,
                max_record_seconds=self.max_record_seconds,
            )
            self._stt.listening_started.connect(self._on_listening_started)
            self._stt.transcription_ready.connect(self._on_transcription)
            self._stt.volume_level.connect(self.volume.emit)
            self._stt.error_occurred.connect(self._on_error)
            self.set_state(ListenState.LISTENING)
            self._stt.start_recording()
        except Exception as e:                       # pragma: no cover
            _log(f"auto-listen: FAILED to start the microphone — {e}")
            self._on_error(str(e))

    # ── STT callbacks ────────────────────────────────────────────────
    def _on_listening_started(self):
        _log("auto-listen: microphone is ready — the child can speak now 🎙")
        self.set_state(ListenState.LISTENING)
        self.listening_began.emit()

    def _on_transcription(self, text):
        # The cycle is over; the ConversationEngine decides what happens next.
        text = (text or "").strip()
        if text:
            _log(f"auto-listen: heard -> {text!r}")
        else:
            _log("auto-listen: heard nothing (silence or mic too quiet)")
        self.heard.emit(text)

    def _on_error(self, msg):
        _log(f"auto-listen: ERROR — {msg}")
        self.set_state(ListenState.ERROR)
        self.error.emit(str(msg))

    # ── teardown ─────────────────────────────────────────────────────
    def _stop_stt(self):
        """Stop the current STT AND disconnect its signals — stale STT workers
        that finish their capture thread later must not fire transcription
        events into the live engine (that was the source of the STT spin)."""
        if self._stt is not None:
            old = self._stt
            self._stt = None
            try:
                old.listening_started.disconnect()
            except Exception:
                pass
            try:
                old.transcription_ready.disconnect()
            except Exception:
                pass
            try:
                old.volume_level.disconnect()
            except Exception:
                pass
            try:
                old.error_occurred.disconnect()
            except Exception:
                pass
            try:
                old.stop_recording()
            except Exception:
                pass

    def shutdown(self):
        self._enabled = False
        self._stop_stt()
        self.set_state(ListenState.IDLE)
