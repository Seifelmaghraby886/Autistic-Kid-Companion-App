"""
ARIA OS — Virtual Keyboard  (kiosk mode)
========================================
An on-screen keyboard so ARIA OS runs with no physical keyboard. The
KeyboardManager installs one app-wide: whenever a text field gets focus the
keyboard slides up from the bottom; short password fields (the parent PIN)
get a big number pad instead of the full QWERTY layout.

The keys never steal focus (NoFocus policy) so the text field keeps the
caret — tapping a key inserts straight into it.
"""

from PySide6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QLineEdit, QTextEdit, QPlainTextEdit, QApplication,
)
from PySide6.QtCore import Qt, QObject, QEvent, QPoint

from ui.styles import COLORS


_NUM_ROW = "1234567890"
_EN_ROWS = ["qwertyuiop", "asdfghjkl", "zxcvbnm"]
_AR_ROWS = ["ضصثقفغعهخحج", "شسيبلاتنمكط", "ذئءؤرىةوزظد"]


class VirtualKeyboard(QWidget):
    """A frameless on-screen keyboard that types into the focused text field."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        # show without stealing activation -> the text field keeps focus
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setStyleSheet("background: rgba(16,24,46,0.98);")

        self._target = None
        self._mode = "full"          # "full" | "numpad"
        self._arabic = False
        self._caps = False
        self._panel = None

        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(10, 8, 10, 10)
        self._rebuild()

    # ── public API ───────────────────────────────────────────────────
    def show_for(self, widget, mode="full"):
        self._target = widget
        if mode != self._mode:
            self._mode = mode
            self._rebuild()
        self.show()
        self.raise_()

    # ── key styling ──────────────────────────────────────────────────
    @staticmethod
    def _style(kind="char"):
        if kind == "char":
            return ("QPushButton { background: #EEF3FB; color: #1A2432;"
                    " border: none; border-radius: 9px; font-size: 19px;"
                    " font-weight: 600; }"
                    "QPushButton:pressed { background: #00E5FF; }")
        if kind == "accent":
            return (f"QPushButton {{ background: {COLORS['teal']}; color: white;"
                    " border: none; border-radius: 9px; font-size: 15px;"
                    " font-weight: 700; }"
                    f"QPushButton:pressed {{ background: {COLORS['teal_deep']}; }}")
        return ("QPushButton { background: rgba(255,255,255,0.16); color: white;"
                " border: none; border-radius: 9px; font-size: 15px;"
                " font-weight: 700; }"
                "QPushButton:pressed { background: rgba(0,229,255,0.5); }")

    def _key(self, label, slot, kind="char", stretch=1):
        b = QPushButton(label)
        b.setFocusPolicy(Qt.NoFocus)            # never take focus off the field
        b.setMinimumHeight(56)
        b.setCursor(Qt.PointingHandCursor)
        b.setStyleSheet(self._style(kind))
        b.clicked.connect(slot)
        return b, stretch

    # ── layout building ──────────────────────────────────────────────
    def _rebuild(self):
        if self._panel is not None:
            self._outer.removeWidget(self._panel)
            self._panel.deleteLater()
        self._panel = QWidget()
        box = QVBoxLayout(self._panel)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(7)
        if self._mode == "numpad":
            self._build_numpad(box)
        else:
            self._build_full(box)
        self._outer.addWidget(self._panel)

    def _add_row(self, box, keys):
        row = QHBoxLayout()
        row.setSpacing(7)
        for widget, stretch in keys:
            row.addWidget(widget, stretch)
        box.addLayout(row)

    def _build_full(self, box):
        self._add_row(box, [self._key(c, lambda _=0, ch=c: self._insert(ch))
                            for c in _NUM_ROW])
        letter_rows = _AR_ROWS if self._arabic else _EN_ROWS
        for r in letter_rows:
            keys = []
            for c in r:
                shown = c.upper() if (self._caps and not self._arabic) else c
                keys.append(self._key(shown,
                            lambda _=0, ch=c: self._insert(self._cased(ch))))
            self._add_row(box, keys)
        # function row
        lang_lbl = "ENG" if self._arabic else "ع"
        self._add_row(box, [
            self._key(lang_lbl, self._toggle_language, "func", 2),
            self._key("⇪", self._toggle_caps, "func", 2),
            self._key("space", lambda: self._insert(" "), "char", 6),
            self._key("⌫", self._backspace, "func", 2),
            self._key("↵", self._enter, "accent", 2),
            self._key("⌄", self.hide, "func", 2),
        ])

    def _build_numpad(self, box):
        for r in ("123", "456", "789"):
            self._add_row(box, [self._key(c, lambda _=0, ch=c: self._insert(ch))
                                for c in r])
        self._add_row(box, [
            self._key("Clear", self._clear, "func"),
            self._key("0", lambda: self._insert("0")),
            self._key("⌫", self._backspace, "func"),
        ])
        self._add_row(box, [self._key("Done", self._enter, "accent")])

    # ── typing actions ───────────────────────────────────────────────
    def _cased(self, ch):
        return ch.upper() if (self._caps and not self._arabic) else ch

    def _insert(self, text):
        t = self._target
        try:
            if isinstance(t, QLineEdit):
                t.insert(text)
            elif isinstance(t, (QTextEdit, QPlainTextEdit)):
                t.insertPlainText(text)
        except Exception:
            pass

    def _backspace(self):
        t = self._target
        try:
            if isinstance(t, QLineEdit):
                t.backspace()
            elif isinstance(t, (QTextEdit, QPlainTextEdit)):
                cur = t.textCursor()
                cur.deletePreviousChar()
        except Exception:
            pass

    def _clear(self):
        t = self._target
        try:
            if isinstance(t, QLineEdit):
                t.clear()
            elif isinstance(t, (QTextEdit, QPlainTextEdit)):
                t.clear()
        except Exception:
            pass

    def _enter(self):
        t = self._target
        if isinstance(t, QLineEdit):
            try:
                t.returnPressed.emit()
            except Exception:
                pass
        self.hide()

    def _toggle_language(self):
        self._arabic = not self._arabic
        self._rebuild()

    def _toggle_caps(self):
        self._caps = not self._caps
        self._rebuild()


class KeyboardManager(QObject):
    """Shows the VirtualKeyboard whenever a text field is focused (kiosk mode)."""

    def __init__(self, app, host_window):
        super().__init__(host_window)
        self._app = app
        self._host = host_window
        self._kb = VirtualKeyboard()
        self._kb.hide()
        app.focusChanged.connect(self._on_focus_changed)
        host_window.installEventFilter(self)

    # reposition the keyboard if the host window moves or resizes
    def eventFilter(self, obj, event):
        if obj is self._host and event.type() in (
            QEvent.Type.Resize, QEvent.Type.Move
        ) and self._kb.isVisible():
            self._reposition()
        return False

    def _on_focus_changed(self, old, now):
        editable = (isinstance(now, (QLineEdit, QTextEdit, QPlainTextEdit))
                    and now.isEnabled() and not now.isReadOnly())
        if editable:
            self._kb.show_for(now, self._mode_for(now))
            self._reposition()
        else:
            self._kb.hide()

    @staticmethod
    def _mode_for(field):
        # short password fields (the parent PIN) get a number pad
        if isinstance(field, QLineEdit):
            ml = field.maxLength()
            if field.echoMode() != QLineEdit.EchoMode.Normal and 0 < ml <= 8:
                return "numpad"
        return "full"

    def _reposition(self):
        host = self._host
        kb_h = max(240, min(340, int(host.height() * 0.42)))
        top_left = host.mapToGlobal(QPoint(0, host.height() - kb_h))
        self._kb.setGeometry(top_left.x(), top_left.y(), host.width(), kb_h)
        self._kb.raise_()


def install(app, host_window):
    """Install the app-wide on-screen keyboard. Returns the KeyboardManager."""
    return KeyboardManager(app, host_window)
