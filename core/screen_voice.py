"""
ARIA Screen Voice Controller
============================
Voice-enables every tool screen with no per-screen rewriting. When a tool is
open, the ConversationEngine hands spoken lines here and this controller turns
them into actions:

  * "go back" / "home" / "exit"  -> the screen's `go_back` signal
  * a command word ("next", "done", "yes", "again"...) or any word that
    matches a visible control's label -> activates that control

It matches against BOTH ordinary QPushButtons AND custom clickable tiles —
any visible widget exposing a `clicked` or `pressed` signal (e.g. calm_zone's
ActivityTile, communication_board's CommButton, the home tiles). Custom tiles
are activated by synthesising a mouse-press, so all 25 tool screens are
voice-operable generically with zero changes to the screens themselves.
"""

from PySide6.QtWidgets import QAbstractButton, QWidget, QLabel
from PySide6.QtGui import QMouseEvent
from PySide6.QtCore import Qt, QEvent, QPointF

from core.intent_router import normalize
from core.log import log as _log


# words that mean "leave this screen and go home"
_BACK = ["back", "go back", "home", "exit", "close", "leave", "go home",
         "ارجع", "رجوع", "البيت", "اقفل", "اخرج", "خروج", "الرئيسيه",
         "zuruck", "nach hause"]

# synonym groups — a spoken word and a control label in the SAME group match.
# Each group mixes English, Egyptian Arabic and German.
_GROUPS = [
    ["next", "forward", "continue", "weiter", "التالي", "بعده", "اللي بعده",
     "كمل", "كمل بقى"],
    ["done", "finish", "finished", "complete", "fertig", "خلصت", "خلاص",
     "تمام", "كده تمام"],
    ["start", "begin", "play", "go", "starten", "ابدا", "ابدأ", "العب", "يلا"],
    ["yes", "yeah", "yep", "correct", "right", "ja", "ايوه", "اه", "نعم",
     "صح", "ماشي"],
    ["no", "nope", "wrong", "nein", "لا", "لاء", "غلط"],
    ["again", "retry", "restart", "repeat", "nochmal", "تاني", "عيد",
     "كمان مره", "من الاول"],
    ["skip", "pass", "ueberspringen", "تخطي", "عدي", "سيب"],
    ["stop", "pause", "stopp", "قف", "وقف", "بطل"],
    ["help", "hilfe", "ساعدني", "نجده", "محتاج مساعده"],
    ["save", "speichern", "احفظ", "حفظ"],
    ["new", "add", "neu", "جديد", "ضيف", "اضف"],
]


class ScreenVoiceController:
    """Routes a spoken command to a tool screen: go-back, or activate a control."""

    def __init__(self, screen):
        self.screen = screen

    def handle(self, transcript: str) -> str:
        """Act on a spoken line. Returns a short description, or '' if no match."""
        norm = normalize(transcript)
        if not norm:
            return ""
        words = set(norm.split())

        # 1) universal — leave the screen
        if self._has(norm, words, _BACK):
            self._go_back()
            return "back"

        # 2) activate the control that best matches what was said
        target = self._match_target(norm, words)
        if target is not None:
            widget, raw_label, activate = target
            try:
                activate()
            except Exception:
                return ""
            label = (raw_label or "").strip()
            return f"clicked '{label}'" if label else "activated a control"
        return ""

    # ── go back ──────────────────────────────────────────────────────
    def _go_back(self):
        sig = getattr(self.screen, "go_back", None)
        if sig is not None:
            try:
                sig.emit()
            except Exception:
                pass

    # ── collecting voice-activatable controls ────────────────────────
    def _targets(self):
        """Every voice-activatable control on the screen.

        Returns a list of (widget, label_text, activate_callable). Covers
        QPushButtons AND custom clickable tiles (any visible widget with a
        `clicked` or `pressed` signal).
        """
        out, seen = [], set()
        try:
            widgets = self.screen.findChildren(QWidget)
        except Exception:
            return out
        for w in widgets:
            try:
                if not (w.isVisible() and w.isEnabled()):
                    continue
                key = id(w)
                if key in seen:
                    continue
                if isinstance(w, QAbstractButton):
                    seen.add(key)
                    out.append((w, w.text() or "", w.click))
                elif hasattr(w, "clicked") or hasattr(w, "pressed"):
                    seen.add(key)
                    out.append((w, self._widget_label(w),
                                lambda x=w: self._activate(x)))
            except Exception:
                continue
        return out

    @staticmethod
    def _widget_label(widget):
        """A custom tile's text = the longest label among its child QLabels."""
        best = ""
        try:
            for lbl in widget.findChildren(QLabel):
                text = (lbl.text() or "").strip()
                if len(text) > len(best):
                    best = text
        except Exception:
            pass
        return best

    @staticmethod
    def _activate(widget):
        """Activate a custom clickable tile by synthesising a left mouse press."""
        try:
            center = QPointF(widget.rect().center())
            event = QMouseEvent(
                QEvent.Type.MouseButtonPress, center, center,
                Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            )
            widget.mousePressEvent(event)
        except Exception as e:
            _log(f"screen voice: could not activate widget — {e}")

    # ── matching ─────────────────────────────────────────────────────
    def _match_target(self, norm, words):
        targets = self._targets()
        if not targets:
            return None
        # which synonym groups does the spoken line belong to?
        spoken_groups = [g for g in _GROUPS if self._has(norm, words, g)]

        best, best_score = None, 0
        for widget, raw_label, activate in targets:
            label = normalize(raw_label or "")
            if not label:
                continue
            lwords = set(label.split())
            score = 0
            # (a) the label shares the spoken command's synonym group
            for group in spoken_groups:
                if any(self._token_in(s, label, lwords) for s in group):
                    score += 5
                    break
            # (b) a spoken word literally appears on the control
            score += 2 * len(words & lwords)
            # (c) the whole phrase matches the label
            if norm == label:
                score += 4
            if score > best_score:
                best, best_score = (widget, raw_label, activate), score
        return best if best_score >= 2 else None

    # ── helpers ──────────────────────────────────────────────────────
    @staticmethod
    def _token_in(phrase, text, words):
        if " " in phrase:
            return phrase in text
        return phrase in words

    @staticmethod
    def _has(norm, words, phrases):
        for p in phrases:
            if " " in p:
                if p in norm:
                    return True
            elif p in words:
                return True
        return False
