"""Games — simple autism-friendly mini-games (emotion match, color match)."""

import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGridLayout
)
from PySide6.QtCore import Qt, Signal

from ui.components import C, GlassCard, MAIN_STYLE


EMOTIONS = [("😊","happy"),("😢","sad"),("😨","scared"),
            ("😴","tired"),("😠","angry"),("🙂","okay")]


class GamesScreen(QWidget):
    close_requested = Signal()

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setStyleSheet(MAIN_STYLE)
        self._score = 0
        self._target = None
        self._build()
        self._next_round()

    def _build(self):
        L = QVBoxLayout(self); L.setContentsMargins(40, 22, 40, 22); L.setSpacing(16)
        top = QHBoxLayout()
        back = QPushButton("← Back"); back.setMaximumWidth(120)
        back.setStyleSheet(f"""
            QPushButton {{ background: rgba(0,191,168,0.12); color: {C['cyan']};
                border: 1.5px solid {C['teal']}; border-radius: 10px;
                padding: 9px 14px; font-size: 12px; }}
        """)
        back.clicked.connect(self.close_requested.emit)
        t = QLabel("🎮  Emotion Match")
        t.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {C['cyan']};")
        self._score_lbl = QLabel("⭐ 0")
        self._score_lbl.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {C['warn']};")
        top.addWidget(back); top.addSpacing(16); top.addWidget(t); top.addStretch(); top.addWidget(self._score_lbl)
        L.addLayout(top)

        prompt_card = GlassCard(self, dark=True)
        pl = QVBoxLayout(prompt_card); pl.setContentsMargins(30, 28, 30, 28)
        self._prompt_lbl = QLabel("Which one feels…")
        self._prompt_lbl.setAlignment(Qt.AlignCenter)
        self._prompt_lbl.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {C['text']};")
        self._target_lbl = QLabel("")
        self._target_lbl.setAlignment(Qt.AlignCenter)
        self._target_lbl.setStyleSheet(f"font-size: 56px; padding-top: 8px;")
        pl.addWidget(self._prompt_lbl); pl.addWidget(self._target_lbl)
        L.addWidget(prompt_card)

        self._grid_wrap = QGridLayout(); self._grid_wrap.setSpacing(14)
        L.addLayout(self._grid_wrap, 1)

    def _next_round(self):
        # Pick a target emotion + render 4 options
        self._target = random.choice(EMOTIONS)
        self._prompt_lbl.setText(f"Find the face that feels {self._target[1]}")
        self._target_lbl.setText("")  # don't show emoji, ask child to identify

        # Clear grid
        while self._grid_wrap.count():
            it = self._grid_wrap.takeAt(0)
            if it.widget(): it.widget().deleteLater()

        options = [self._target] + random.sample(
            [e for e in EMOTIONS if e != self._target], 3
        )
        random.shuffle(options)
        for i, (icon, name) in enumerate(options):
            b = QPushButton(f"{icon}\n{name}")
            b.setFixedSize(160, 160)
            b.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255,255,255,0.06); color: {C['text']};
                    border: 1.5px solid rgba(0,191,168,0.4); border-radius: 18px;
                    font-size: 32px;
                }}
                QPushButton:hover {{
                    background: rgba(0,229,255,0.15); border-color: {C['cyan']};
                }}
            """)
            b.clicked.connect(lambda checked, _n=name: self._check(_n))
            self._grid_wrap.addWidget(b, i // 2, i % 2)

    def _check(self, picked):
        if picked == self._target[1]:
            self._score += 1
            self._score_lbl.setText(f"⭐ {self._score}")
            self.controller.tts.speak("Yes! Great job!", "en", "cheerful")
        else:
            self.controller.tts.speak("Try again, you got this.", "en", "soft")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(900, self._next_round)
