"""AAC Board — pictogram sentence builder."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal

from ui.components import C, GlassCard, MAIN_STYLE


CATEGORIES = {
    "all": [
        ("🍎","apple","تفاحة"), ("💧","water","ميه"), ("🥛","milk","لبن"),
        ("🍪","cookie","بسكويت"), ("🍕","pizza","بيتزا"), ("🍦","ice cream","ايس كريم"),
        ("😊","happy","مبسوط"), ("😢","sad","زعلان"), ("😨","scared","خايف"),
        ("😴","tired","تعبان"), ("🤒","sick","تعبان جداً"), ("🙂","okay","تمام"),
        ("🛑","stop","وقف"), ("✋","wait","استنى"), ("🆘","help","ساعدني"),
        ("👤","mom","ماما"), ("👨","dad","بابا"), ("🚪","go home","عايز اروح البيت"),
        ("🚽","bathroom","الحمام"), ("🛌","sleep","نوم"), ("🎮","play","العب"),
    ],
    "food": [("🍎","apple","تفاحة"), ("🍪","cookie","بسكويت"), ("🍕","pizza","بيتزا"),
             ("🍞","bread","عيش"), ("🍦","ice cream","ايس كريم"), ("🥛","milk","لبن"),
             ("🍌","banana","موزة"), ("🥚","egg","بيضة"), ("🍝","pasta","مكرونة")],
    "water":[("💧","water","ميه"), ("🥤","juice","عصير"), ("🥛","milk","لبن")],
    "bathroom":[("🚽","toilet","الحمام"), ("🧻","tissue","ورق"), ("🚿","shower","دش"),
                ("🪥","brush teeth","غسل سناني")],
    "pain": [("🤕","head hurts","راسي بتوجعني"), ("🤢","tummy hurts","بطني بتوجعني"),
             ("🦷","tooth hurts","سنتي بتوجعني"), ("👁️","eye hurts","عيني بتوجعني")],
    "people": [("👤","mom","ماما"), ("👨","dad","بابا"), ("🧒","brother","اخويا"),
               ("👧","sister","اختي"), ("👵","grandma","تيتا"), ("👴","grandpa","جدو")],
}


class PictogramBtn(QPushButton):
    def __init__(self, icon, en, ar, parent=None):
        super().__init__(parent)
        self.icon_e = icon; self.en = en; self.ar = ar
        self.setText(f"{icon}\n{ar}\n{en}")
        self.setFixedSize(125, 130)
        self.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.08); color: {C['text']};
                border: 1.5px solid rgba(0,191,168,0.4); border-radius: 14px;
                font-size: 13px; font-weight: 600; padding: 6px;
            }}
            QPushButton:hover {{
                background: rgba(0,229,255,0.15); border-color: {C['cyan']};
            }}
        """)


class AACBoard(QWidget):
    close_requested = Signal()

    def __init__(self, controller, category="all", parent=None):
        super().__init__(parent)
        self.controller = controller
        self._sentence = []
        self.setStyleSheet(MAIN_STYLE)
        self._build_ui(category)

    def _build_ui(self, category):
        L = QVBoxLayout(self)
        L.setContentsMargins(40, 22, 40, 22)
        L.setSpacing(14)

        top = QHBoxLayout()
        back = QPushButton("← Back")
        back.setMaximumWidth(120)
        back.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0,191,168,0.12); color: {C['cyan']};
                border: 1.5px solid {C['teal']}; border-radius: 10px;
                padding: 9px 14px; font-size: 12px;
            }}
        """)
        back.clicked.connect(self.close_requested.emit)
        title = QLabel(f"🗨  Picture Board  ({category})")
        title.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {C['cyan']};")
        top.addWidget(back); top.addSpacing(16); top.addWidget(title); top.addStretch()
        L.addLayout(top)

        # Sentence strip
        strip = GlassCard(self, dark=True)
        sl = QHBoxLayout(strip); sl.setContentsMargins(20, 14, 20, 14)
        self._sentence_lbl = QLabel("…")
        self._sentence_lbl.setStyleSheet(f"font-size: 18px; color: {C['text']};")
        self._sentence_lbl.setWordWrap(True)
        sl.addWidget(self._sentence_lbl, 1)
        speak = QPushButton("🔊 Speak")
        speak.setMaximumWidth(140)
        speak.clicked.connect(self._speak)
        clear = QPushButton("✕ Clear")
        clear.setMaximumWidth(120)
        clear.setStyleSheet(f"""
            QPushButton {{ background: rgba(255,107,126,0.15);
                color: {C['alert']}; border: 1.5px solid {C['alert']};
                border-radius: 10px; padding: 8px 14px; }}
        """)
        clear.clicked.connect(self._clear)
        sl.addWidget(speak); sl.addWidget(clear)
        L.addWidget(strip)

        # Pictogram grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        grid_w = QWidget(); grid_w.setStyleSheet("background: transparent;")
        grid = QGridLayout(grid_w); grid.setSpacing(10)
        items = CATEGORIES.get(category, CATEGORIES["all"])
        for i, (icon, en, ar) in enumerate(items):
            b = PictogramBtn(icon, en, ar)
            b.clicked.connect(lambda checked, _b=b: self._add(_b))
            grid.addWidget(b, i // 6, i % 6)
        scroll.setWidget(grid_w)
        L.addWidget(scroll, 1)

    def _add(self, b):
        self._sentence.append((b.icon_e, b.en, b.ar))
        self._render()

    def _clear(self):
        self._sentence = []
        self._render()

    def _render(self):
        if not self._sentence:
            self._sentence_lbl.setText("Tap pictures to build a message…")
            return
        ar = " ".join(s[2] for s in self._sentence)
        en = " ".join(s[1] for s in self._sentence)
        icons = " ".join(s[0] for s in self._sentence)
        self._sentence_lbl.setText(f"{icons}\n{ar}\n{en}")

    def _speak(self):
        if not self._sentence: return
        ar = " ".join(s[2] for s in self._sentence)
        en = " ".join(s[1] for s in self._sentence)
        # Choose by child language
        from data import database as db
        lang = (db.get_child(self.controller.child_id) or {}).get("language", "en")
        text = ar if lang == "ar" else en
        self.controller.tts.speak(text, language=lang, voice_style="soft")
