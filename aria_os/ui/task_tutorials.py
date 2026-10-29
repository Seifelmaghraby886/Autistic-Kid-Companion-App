"""Task Tutorials — step-by-step ADL skills (brushing teeth, washing hands)."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar
)
from PySide6.QtCore import Qt, Signal

from ui.components import C, GlassCard, MAIN_STYLE


TUTORIALS = {
    "brush_teeth": {
        "icon": "🪥",
        "title_en": "Brush Your Teeth",
        "title_ar": "اغسل سنانك",
        "steps": [
            ("🪥", "Pick toothbrush", "خد فرشاية"),
            ("🦷", "Put toothpaste",  "حط معجون"),
            ("⬆️", "Brush top teeth",  "اغسل سنانك من فوق"),
            ("⬇️", "Brush bottom teeth", "اغسل سنانك من تحت"),
            ("💧", "Rinse mouth",     "اشطف بفمك"),
            ("✓",  "Done — great job!", "خلصت — برافو!"),
        ],
    },
    "wash_hands": {
        "icon": "🧼",
        "title_en": "Wash Your Hands",
        "title_ar": "اغسل ايديك",
        "steps": [
            ("🚿", "Open water",  "افتح الميه"),
            ("🧼", "Put soap",    "حط صابون"),
            ("👏", "Rub hands",   "افرك ايديك"),
            ("💧", "Rinse off",   "اشطف"),
            ("🧻", "Dry hands",   "نشف"),
            ("✓",  "Done!",       "خلصت!"),
        ],
    },
}


class TaskTutorial(QWidget):
    close_requested = Signal()

    def __init__(self, controller, key="brush_teeth", parent=None):
        super().__init__(parent)
        self.controller = controller
        self.key = key if key in TUTORIALS else "brush_teeth"
        self.tut = TUTORIALS[self.key]
        self._step = 0
        self.setStyleSheet(MAIN_STYLE)
        self._build()
        self._show_step()

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
        t = QLabel(f"{self.tut['icon']}  {self.tut['title_en']}")
        t.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {C['cyan']};")
        top.addWidget(back); top.addSpacing(16); top.addWidget(t); top.addStretch()
        L.addLayout(top)

        self._progress = QProgressBar()
        self._progress.setRange(0, len(self.tut["steps"]))
        self._progress.setValue(1)
        self._progress.setTextVisible(False)
        self._progress.setMaximumHeight(8)
        self._progress.setStyleSheet(f"""
            QProgressBar {{ background: rgba(0,191,168,0.10); border-radius: 4px; }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {C['teal']}, stop:1 {C['cyan']});
                border-radius: 4px;
            }}
        """)
        L.addWidget(self._progress)

        # Step card
        card = GlassCard(self, dark=True)
        cl = QVBoxLayout(card); cl.setContentsMargins(30, 30, 30, 30); cl.setSpacing(12)
        self._step_icon = QLabel("")
        self._step_icon.setAlignment(Qt.AlignCenter)
        self._step_icon.setStyleSheet("font-size: 110px;")
        self._step_text = QLabel("")
        self._step_text.setAlignment(Qt.AlignCenter)
        self._step_text.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {C['text']};")
        self._step_ar = QLabel("")
        self._step_ar.setAlignment(Qt.AlignCenter)
        self._step_ar.setStyleSheet(f"font-size: 18px; color: {C['soft']};")
        self._step_counter = QLabel("")
        self._step_counter.setAlignment(Qt.AlignCenter)
        self._step_counter.setStyleSheet(f"font-size: 12px; color: {C['text_dim']};")
        cl.addWidget(self._step_icon)
        cl.addWidget(self._step_text)
        cl.addWidget(self._step_ar)
        cl.addWidget(self._step_counter)
        L.addWidget(card, 1)

        # Controls
        nav = QHBoxLayout()
        self._read = QPushButton("🔊 Read")
        self._read.clicked.connect(self._read_step)
        self._next = QPushButton("Next →")
        self._next.clicked.connect(self._on_next)
        nav.addWidget(self._read)
        nav.addStretch()
        nav.addWidget(self._next)
        L.addLayout(nav)

    def _show_step(self):
        i = self._step
        icon, en, ar = self.tut["steps"][i]
        self._step_icon.setText(icon)
        self._step_text.setText(en)
        self._step_ar.setText(ar)
        self._step_counter.setText(f"Step {i+1} of {len(self.tut['steps'])}")
        self._progress.setValue(i + 1)
        self._next.setText("Done ✓" if i == len(self.tut["steps"]) - 1 else "Next →")
        # Auto-read
        self._read_step()

    def _read_step(self):
        i = self._step
        _, en, ar = self.tut["steps"][i]
        from data import database as db
        lang = (db.get_child(self.controller.child_id) or {}).get("language", "en")
        self.controller.tts.speak(ar if lang == "ar" else en,
                                  language=lang, voice_style="soft")

    def _on_next(self):
        if self._step >= len(self.tut["steps"]) - 1:
            self.close_requested.emit()
            return
        self._step += 1
        self._show_step()
