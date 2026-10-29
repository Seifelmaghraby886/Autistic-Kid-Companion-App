"""Story Mode — simple social/bedtime story display + TTS narration."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit
)
from PySide6.QtCore import Qt, Signal

from ui.components import C, GlassCard, MAIN_STYLE


STORIES = {
    "calm_night": {
        "title_en": "A Quiet Night",
        "title_ar": "ليلة هادية",
        "body_en": [
            "The sun was sleeping. The stars came out softly.",
            "I felt my warm blanket like a hug.",
            "I took a slow breath, then another.",
            "My eyes felt heavy. The world was quiet and safe.",
            "I closed my eyes and dreamed of friendly things.",
            "Sweet dreams. 🌙",
        ],
        "body_ar": [
            "الشمس نامت. النجوم طلعت بهدوء.",
            "حسيت بالبطانية الدافية بتحضنني.",
            "أخدت نفس عميق… وبعدين تاني.",
            "عيني حست بثقل. الدنيا هادية وأمان.",
            "قفلت عيني وحلمت بحاجات حلوة.",
            "أحلام حلوة. 🌙",
        ],
    },
    "going_school": {
        "title_en": "Going to School",
        "title_ar": "بروح المدرسة",
        "body_en": [
            "Tomorrow I will go to school.",
            "I will see my teacher and my friends.",
            "If something feels too loud, I can ask for a quiet break.",
            "It is okay to feel many things at school.",
            "I am brave and I can do this.",
        ],
        "body_ar": [
            "بكره هاروح المدرسة.",
            "هاشوف الميس والاصحاب.",
            "لو في صوت عالي، أقدر اطلب فترة هادية.",
            "عادي تحس بحاجات كتير في المدرسة.",
            "أنا شجاع وأقدر أعمل ده.",
        ],
    },
}


class StoryMode(QWidget):
    close_requested = Signal()

    def __init__(self, controller, theme="calm_night", parent=None):
        super().__init__(parent)
        self.controller = controller
        self.theme = theme if theme in STORIES else "calm_night"
        self._page = 0
        self.setStyleSheet(MAIN_STYLE)
        self._build()
        self._render()

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
        s = STORIES[self.theme]
        title = QLabel(f"📖  {s['title_en']}")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {C['cyan']};")
        top.addWidget(back); top.addSpacing(16); top.addWidget(title); top.addStretch()
        L.addLayout(top)

        card = GlassCard(self, dark=True)
        cl = QVBoxLayout(card); cl.setContentsMargins(40, 36, 40, 36)
        self._page_lbl = QLabel("")
        self._page_lbl.setWordWrap(True)
        self._page_lbl.setAlignment(Qt.AlignCenter)
        self._page_lbl.setStyleSheet(f"font-size: 22px; font-weight: 600; color: {C['text']}; line-height: 1.7;")
        cl.addWidget(self._page_lbl)
        L.addWidget(card, 1)

        nav = QHBoxLayout()
        read = QPushButton("🔊 Read")
        read.clicked.connect(self._read)
        prev = QPushButton("← Previous")
        prev.clicked.connect(self._prev)
        nxt = QPushButton("Next →")
        nxt.clicked.connect(self._next)
        nav.addWidget(prev); nav.addStretch(); nav.addWidget(read); nav.addStretch(); nav.addWidget(nxt)
        L.addLayout(nav)

    def _render(self):
        s = STORIES[self.theme]
        from data import database as db
        lang = (db.get_child(self.controller.child_id) or {}).get("language", "en")
        pages = s["body_ar"] if lang == "ar" else s["body_en"]
        self._pages = pages
        self._page_lbl.setText(pages[self._page])

    def _read(self):
        s = STORIES[self.theme]
        from data import database as db
        lang = (db.get_child(self.controller.child_id) or {}).get("language", "en")
        text = self._pages[self._page]
        self.controller.tts.speak(text, language=lang, voice_style="soft")

    def _prev(self):
        if self._page > 0:
            self._page -= 1
            self._render()

    def _next(self):
        if self._page < len(self._pages) - 1:
            self._page += 1
            self._render()
        else:
            self.close_requested.emit()
