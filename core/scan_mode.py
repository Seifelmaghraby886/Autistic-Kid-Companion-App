"""
ARIA OS — Scan Mode
===================
Choice-scanning for non-verbal children (and for any yes/no confirmation):
ARIA reads the options aloud one at a time, and the child answers each with a
head NOD ("yes — this one") or SHAKE ("no — next"). A spoken "yes"/"no" works
too, so a partially-verbal child can use whichever is easier.

This makes menus and confirmations fully usable with zero touch and — for a
non-verbal child — zero speech.
"""

from PySide6.QtCore import QObject, Signal, QTimer

from core.log import log as _log

_YES = {"yes", "yeah", "yep", "ok", "okay", "اه", "ايوه", "أيوه", "نعم",
        "تمام", "ماشي", "صح", "ja"}
_NO = {"no", "nope", "لا", "لاء", "مش", "nein", "غلط"}


class ScanController(QObject):
    """Walks a list of options, speaking each, awaiting a nod/shake or yes/no."""

    option_spoken = Signal(int, str)   # (index, label) — the UI highlights it
    finished      = Signal(object)     # the selected value, or None if cancelled

    def __init__(self, child_id, speak_fn=None, parent=None):
        super().__init__(parent)
        self.child_id = child_id
        self._speak = speak_fn          # callable(text); injected for tests
        self._options = []
        self._on_select = None
        self._index = -1
        self._passes = 0
        self._active = False
        self._window_ms = 6000
        self._window = QTimer(self)
        self._window.setSingleShot(True)
        self._window.timeout.connect(self._advance)

    def is_active(self) -> bool:
        return self._active

    # ── lifecycle ────────────────────────────────────────────────────
    def start(self, options, on_select=None, window_ms=6000):
        """options: list of (label, value). on_select: callable(value)."""
        if not options:
            return
        self._options = list(options)
        self._on_select = on_select
        self._index = -1
        self._passes = 0
        self._window_ms = window_ms
        self._active = True
        _log(f"scan mode: started ({len(self._options)} options)")
        self._advance()

    def stop(self):
        self._active = False
        self._window.stop()

    # ── stepping through options ─────────────────────────────────────
    def _advance(self):
        if not self._active:
            return
        self._index += 1
        if self._index >= len(self._options):
            self._index = 0
            self._passes += 1
            if self._passes >= 3:           # give up after 3 full passes
                _log("scan mode: no choice after 3 passes — cancelled")
                self.stop()
                self.finished.emit(None)
                return
        label = self._options[self._index][0]
        self.option_spoken.emit(self._index, label)
        self._say(label)
        self._window.start(self._window_ms)

    def _say(self, text):
        if self._speak:
            try:
                self._speak(text)
            except Exception:
                pass
            return
        try:
            from speech import tts_engine
            tts_engine.speak(text, child_id=self.child_id, style="soft")
        except Exception:
            pass

    # ── child responses ──────────────────────────────────────────────
    def on_gesture(self, gesture):
        """Called with 'nod' or 'shake' from the FaceInputEngine."""
        if not self._active:
            return
        if gesture == "nod":
            self._select()
        elif gesture == "shake":
            self._window.stop()
            self._advance()

    def on_voice(self, text):
        """Spoken yes/no fallback for partially-verbal children."""
        if not self._active or not text:
            return
        from core.intent_router import normalize
        words = set(normalize(text).split())
        if words & _YES:
            self._select()
        elif words & _NO:
            self._window.stop()
            self._advance()

    def _select(self):
        if not self._active:
            return
        self._window.stop()
        self._active = False
        label, value = self._options[self._index]
        _log(f"scan mode: selected '{label}'")
        if self._on_select:
            try:
                self._on_select(value)
            except Exception:
                pass
        self.finished.emit(value)
