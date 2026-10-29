"""
First-Then Board — a foundational autism visual support (NCAEP EBP:
Visual Supports + Reinforcement).

The parent or child picks "First <task>" and "Then <reward>". ARIA shows
the two-panel board, speaks it aloud, and when the task is done the child
taps DONE — celebration, a star, and the reward panel lights up. Sequence
data feeds the intelligence bus so the companion can reference it.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QGridLayout, QScrollArea,
)
from PySide6.QtCore import Qt, Signal, QTimer

from ui.components import GlassCard
from ui.animated_bg import MeshBackground
from ui.styles import MAIN_STYLE, COLORS
import database.db_manager as db


# (icon, {lang: label}) — first = tasks, then = motivators
_TASKS = [
    ("🦷", {"en": "Brush teeth", "ar": "غسيل الأسنان", "de": "Zähne putzen"}),
    ("📚", {"en": "Homework",    "ar": "الواجب",        "de": "Hausaufgaben"}),
    ("🍽", {"en": "Eat food",    "ar": "الأكل",         "de": "Essen"}),
    ("🛁", {"en": "Bath time",   "ar": "الاستحمام",     "de": "Baden"}),
    ("🧸", {"en": "Tidy up",     "ar": "ترتيب اللعب",   "de": "Aufräumen"}),
    ("👕", {"en": "Get dressed", "ar": "لبس الهدوم",    "de": "Anziehen"}),
]
_REWARDS = [
    ("🎮", {"en": "Play a game",  "ar": "لعب لعبة",     "de": "Spielen"}),
    ("📺", {"en": "Watch cartoon","ar": "مشاهدة كرتون", "de": "Cartoon schauen"}),
    ("🍪", {"en": "Snack",        "ar": "حاجة حلوة",    "de": "Snack"}),
    ("🎵", {"en": "Music",        "ar": "أغنية",        "de": "Musik"}),
    ("🤗", {"en": "Big hug",      "ar": "حضن كبير",     "de": "Umarmung"}),
    ("⭐", {"en": "A star",       "ar": "نجمة",          "de": "Ein Stern"}),
]

_T = {
    "title":  {"en": "First … Then", "ar": "الأول … وبعدين", "de": "Zuerst … Dann"},
    "first":  {"en": "FIRST",  "ar": "الأول",   "de": "ZUERST"},
    "then":   {"en": "THEN",   "ar": "وبعدين",  "de": "DANN"},
    "pick_t": {"en": "Pick the task",   "ar": "اختار المهمة",  "de": "Aufgabe wählen"},
    "pick_r": {"en": "Pick the reward", "ar": "اختار الجايزة", "de": "Belohnung wählen"},
    "done":   {"en": "✅  DONE!", "ar": "✅  خلصت!", "de": "✅  FERTIG!"},
    "yay":    {"en": "Amazing! You did it! Now: ",
               "ar": "برافو عليك! خلصت! دلوقتي: ",
               "de": "Super! Geschafft! Jetzt: "},
}


class _PickBtn(QPushButton):
    def __init__(self, icon, label, color, parent=None):
        super().__init__(f"{icon}  {label}", parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self.setMinimumHeight(52)
        self.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.85); color: {COLORS['text']};
                border: 1.6px solid rgba(0,0,0,0.10); border-radius: 14px;
                padding: 8px 16px; font-size: 15px; font-weight: 600;
                text-align: left;
            }}
            QPushButton:hover  {{ border-color: {color}; }}
            QPushButton:checked {{
                background: {color}33; border: 2px solid {color};
                font-weight: 800;
            }}
        """)


class FirstThenScreen(QWidget):
    go_back = Signal()

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._child = db.get_child(child_id) or {}
        self._lang = self._child.get("language", "en")
        self._first = None   # (icon, label)
        self._then = None
        self.setStyleSheet(MAIN_STYLE)
        self._build_ui()

    def _tr(self, key):
        d = _T[key]
        return d.get(self._lang, d["en"])

    def _pick_label(self, labels):
        return labels.get(self._lang, labels["en"])

    def _build_ui(self):
        self._bg = MeshBackground(self, intensity=0.5)
        self._bg.lower()

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 22, 32, 22)
        root.setSpacing(14)

        # header
        hdr = QHBoxLayout()
        back = QPushButton("← Back")
        back.setStyleSheet(f"""
            QPushButton {{
                background: rgba(56,184,176,0.10); color: {COLORS['teal_deep']};
                border: 1.5px solid {COLORS['teal']}; border-radius: 10px;
                padding: 8px 16px; font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(56,184,176,0.22); }}
        """)
        back.clicked.connect(self.go_back.emit)
        title = QLabel(f"🧩 {self._tr('title')}")
        title.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {COLORS['text']};")
        hdr.addWidget(back)
        hdr.addSpacing(16)
        hdr.addWidget(title)
        hdr.addStretch()
        root.addLayout(hdr)

        # the two-panel board
        board = QHBoxLayout()
        board.setSpacing(18)
        self._first_panel, self._first_icon, self._first_lbl = \
            self._panel(self._tr("first"), COLORS["teal"])
        self._then_panel, self._then_icon, self._then_lbl = \
            self._panel(self._tr("then"), "#B388FF")
        arrow = QLabel("➜")
        arrow.setAlignment(Qt.AlignCenter)
        arrow.setStyleSheet(f"font-size: 42px; color: {COLORS['text_light']};")
        board.addWidget(self._first_panel, 1)
        board.addWidget(arrow)
        board.addWidget(self._then_panel, 1)
        root.addLayout(board, 2)

        # pickers
        pickers = QHBoxLayout()
        pickers.setSpacing(18)
        pickers.addWidget(self._picker(self._tr("pick_t"), _TASKS,
                                       COLORS["teal"], is_first=True), 1)
        pickers.addWidget(self._picker(self._tr("pick_r"), _REWARDS,
                                       "#B388FF", is_first=False), 1)
        root.addLayout(pickers, 3)

        # done button
        self._done_btn = QPushButton(self._tr("done"))
        self._done_btn.setEnabled(False)
        self._done_btn.setMinimumHeight(62)
        self._done_btn.setCursor(Qt.PointingHandCursor)
        self._done_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {COLORS['teal']}, stop:1 #B388FF);
                color: white; border: none; border-radius: 18px;
                font-size: 20px; font-weight: 800; padding: 12px 40px;
            }}
            QPushButton:disabled {{ background: rgba(120,130,150,0.25); }}
        """)
        self._done_btn.clicked.connect(self._on_done)
        root.addWidget(self._done_btn)

        if self._lang == "ar":
            self.setLayoutDirection(Qt.RightToLeft)

    def _panel(self, caption, color):
        card = GlassCard(self, radius=22)
        v = QVBoxLayout(card)
        v.setContentsMargins(18, 14, 18, 16)
        v.setAlignment(Qt.AlignCenter)
        cap = QLabel(caption)
        cap.setAlignment(Qt.AlignCenter)
        cap.setStyleSheet(
            f"font-size: 15px; font-weight: 900; letter-spacing: 3px;"
            f"color: {color}; background: transparent;")
        icon = QLabel("❔")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 64px; background: transparent;")
        lbl = QLabel("—")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(
            f"font-size: 18px; font-weight: 700; color: {COLORS['text']};"
            f"background: transparent;")
        v.addWidget(cap)
        v.addWidget(icon)
        v.addWidget(lbl)
        return card, icon, lbl

    def _picker(self, caption, items, color, is_first):
        card = GlassCard(self, radius=18)
        v = QVBoxLayout(card)
        v.setContentsMargins(16, 12, 16, 12)
        v.setSpacing(8)
        cap = QLabel(caption)
        cap.setStyleSheet(
            f"font-size: 12px; font-weight: 800; letter-spacing: 2px;"
            f"color: {COLORS['text_light']}; background: transparent;")
        v.addWidget(cap)

        grid = QGridLayout()
        grid.setSpacing(8)
        btns = []

        def choose(idx):
            icon, labels = items[idx]
            label = self._pick_label(labels)
            for j, b in enumerate(btns):
                b.setChecked(j == idx)
            if is_first:
                self._first = (icon, label)
                self._first_icon.setText(icon)
                self._first_lbl.setText(label)
            else:
                self._then = (icon, label)
                self._then_icon.setText(icon)
                self._then_lbl.setText(label)
            self._maybe_ready()

        for i, (icon, labels) in enumerate(items):
            b = _PickBtn(icon, self._pick_label(labels), color)
            b.clicked.connect(lambda checked, k=i: choose(k))
            grid.addWidget(b, i // 2, i % 2)
            btns.append(b)
        v.addLayout(grid)
        v.addStretch()
        return card

    def _maybe_ready(self):
        if self._first and self._then:
            self._done_btn.setEnabled(True)
            # speak the plan: "First homework, then games"
            f, t = self._first[1], self._then[1]
            phrase = {
                "en": f"First {f}, then {t}!",
                "ar": f"الأول {f}، وبعدين {t}!",
                "de": f"Zuerst {f}, dann {t}!",
            }.get(self._lang)
            self._say(phrase)

    def _on_done(self):
        f = self._first[1] if self._first else "task"
        t = self._then[1] if self._then else "reward"
        self._say(self._tr("yay") + t)
        self._done_btn.setText("🎉 " + self._tr("done"))
        self._done_btn.setEnabled(False)
        # celebration flash on the reward panel
        self._then_panel.setStyleSheet("background: rgba(179,136,255,0.20); border-radius: 22px;")
        QTimer.singleShot(1800, lambda: self._then_panel.setStyleSheet(""))
        try:
            db.log_emotion(self._child_id, "happy", 0.9, source="first_then",
                           action_taken=f"completed:{f}->{t}")
        except Exception:
            pass
        try:
            from core.child_context import get_context
            get_context().record_activity("first_then", f"done:{f}",
                                          award=1, reason="first-then completed")
        except Exception:
            pass

    def _say(self, text):
        try:
            from speech.tts_engine import speak
            speak(text, self._child_id)
        except Exception:
            pass

    def resizeEvent(self, event):
        if hasattr(self, "_bg"):
            self._bg.resize(self.size())
        super().resizeEvent(event)
