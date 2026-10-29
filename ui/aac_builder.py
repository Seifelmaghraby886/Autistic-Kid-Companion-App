"""
ARIA AAC Sentence Builder
Pictogram-based sentence construction for non-verbal autistic children.
Tap symbols to build a sentence, then ARIA speaks it.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QScrollArea, QStackedWidget
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPainter, QColor, QFont, QPainterPath, QPen, QLinearGradient

from ui.components import GlassCard, ARIAFaceWidget, ParticleBackground
from ui.styles import MAIN_STYLE, COLORS
import database.db_manager as db


CATEGORIES = {
    "en": {
        "I want": [
            ("🍎", "an apple"),     ("💧", "water"),       ("🥛", "milk"),
            ("🍪", "a cookie"),     ("🍕", "pizza"),       ("🍦", "ice cream"),
            ("🎮", "to play"),      ("📺", "to watch TV"), ("📚", "to read"),
            ("🛌", "to sleep"),     ("🚗", "to go in car"),("🌳", "to go outside"),
        ],
        "I feel": [
            ("😊", "happy"),    ("😢", "sad"),       ("😴", "sleepy"),
            ("😨", "scared"),   ("😤", "angry"),     ("🤒", "sick"),
            ("🥶", "cold"),     ("🥵", "hot"),       ("😐", "okay"),
            ("🤗", "loved"),    ("🤔", "confused"),  ("😎", "excited"),
        ],
        "Help": [
            ("🛑", "stop please"),    ("✋", "wait"),         ("🆘", "help me"),
            ("🤫", "too loud"),       ("💡", "too bright"),   ("👤", "too crowded"),
            ("🚪", "go home"),        ("🏥", "I'm hurt"),     ("🚽", "bathroom"),
            ("👨‍👩‍👧", "I want mom"), ("👨", "I want dad"),  ("🐕", "I want pet"),
        ],
        "Yes/No": [
            ("✅", "yes"),         ("❌", "no"),          ("🙏", "please"),
            ("💖", "thank you"),   ("👋", "hello"),       ("👋", "goodbye"),
            ("❓", "what?"),       ("❔", "where?"),       ("🤷", "I don't know"),
            ("👍", "good"),        ("👎", "bad"),         ("🆗", "okay"),
        ],
    },
    "ar": {
        "أريد": [
            ("🍎", "تفاحة"),   ("💧", "ماية"),    ("🥛", "حليب"),
            ("🍪", "بسكويت"),   ("🍕", "بيتزا"),   ("🍦", "آيس كريم"),
            ("🎮", "ألعب"),    ("📺", "أتفرج"),  ("📚", "أقرا"),
            ("🛌", "أنام"),     ("🚗", "أركب عربية"),("🌳", "أطلع برة"),
        ],
        "أحس": [
            ("😊", "مبسوط"),   ("😢", "زعلان"),   ("😴", "نعسان"),
            ("😨", "خايف"),    ("😤", "متضايق"),  ("🤒", "تعبان"),
            ("🥶", "بردان"),   ("🥵", "حران"),    ("😐", "عادي"),
            ("🤗", "محبوب"),   ("🤔", "محتار"),   ("😎", "متحمس"),
        ],
        "مساعدة": [
            ("🛑", "وقف لو سمحت"), ("✋", "استنى"),    ("🆘", "ساعدني"),
            ("🤫", "الصوت عالي"),  ("💡", "النور قوي"), ("👤", "الناس كتير"),
            ("🚪", "عايز أرجع"),   ("🏥", "أنا واجعني"),("🚽", "الحمام"),
            ("👨‍👩‍👧", "عايز ماما"),("👨", "عايز بابا"), ("🐕", "عايز حيوان"),
        ],
        "أيوه/لا": [
            ("✅", "أيوه"),     ("❌", "لأ"),       ("🙏", "من فضلك"),
            ("💖", "شكراً"),    ("👋", "أهلا"),     ("👋", "مع السلامة"),
            ("❓", "إيه؟"),     ("❔", "فين؟"),     ("🤷", "مش عارف"),
            ("👍", "كويس"),     ("👎", "وحش"),      ("🆗", "تمام"),
        ],
    },
    "de": {
        "Ich möchte": [
            ("🍎", "Apfel"),      ("💧", "Wasser"),      ("🥛", "Milch"),
            ("🍪", "Keks"),       ("🍕", "Pizza"),       ("🍦", "Eiscreme"),
            ("🎮", "spielen"),    ("📺", "fernsehen"),   ("📚", "lesen"),
            ("🛌", "schlafen"),   ("🚗", "Auto fahren"), ("🌳", "rausgehen"),
        ],
        "Ich fühle mich": [
            ("😊", "glücklich"),  ("😢", "traurig"),     ("😴", "müde"),
            ("😨", "ängstlich"),  ("😤", "wütend"),      ("🤒", "krank"),
            ("🥶", "kalt"),       ("🥵", "heiß"),        ("😐", "okay"),
            ("🤗", "geliebt"),    ("🤔", "verwirrt"),    ("😎", "aufgeregt"),
        ],
        "Hilfe": [
            ("🛑", "Stopp bitte"),    ("✋", "warten"),       ("🆘", "Hilf mir"),
            ("🤫", "zu laut"),        ("💡", "zu hell"),      ("👤", "zu viele Leute"),
            ("🚪", "nach Hause"),     ("🏥", "es tut weh"),   ("🚽", "Toilette"),
            ("👨‍👩‍👧", "Ich will Mama"),("👨", "Ich will Papa"),("🐕", "Ich will Tier"),
        ],
        "Ja/Nein": [
            ("✅", "ja"),          ("❌", "nein"),         ("🙏", "bitte"),
            ("💖", "danke"),       ("👋", "hallo"),        ("👋", "tschüss"),
            ("❓", "was?"),        ("❔", "wo?"),          ("🤷", "weiß nicht"),
            ("👍", "gut"),         ("👎", "schlecht"),     ("🆗", "okay"),
        ],
    },
}


class PictogramBtn(QPushButton):
    def __init__(self, icon, text, color, parent=None):
        super().__init__(parent)
        self._icon = icon
        self._text = text
        self._color = color
        self.setFixedSize(110, 110)
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        path = QPainterPath()
        path.addRoundedRect(4, 4, w - 8, h - 8, 18, 18)

        if self.underMouse():
            grad = QLinearGradient(0, 0, 0, h)
            grad.setColorAt(0, QColor(255, 255, 255, 240))
            c = QColor(self._color)
            grad.setColorAt(1, QColor(c.red(), c.green(), c.blue(), 70))
            painter.fillPath(path, grad)
            painter.setPen(QPen(QColor(self._color), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)
        else:
            painter.fillPath(path, QColor(255, 255, 255, 220))
            painter.setPen(QPen(QColor(self._color).lighter(160), 1.5))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)

        # Icon
        painter.setFont(QFont("Segoe UI Emoji", 32))
        painter.setPen(QColor(COLORS["text"]))
        painter.drawText(0, 8, w, 56, Qt.AlignCenter, self._icon)

        # Text
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.setPen(QColor(self._color))
        painter.drawText(4, 70, w - 8, 36, Qt.AlignCenter | Qt.TextWordWrap, self._text)


class AACBuilderScreen(QWidget):
    go_back = Signal()

    CATEGORY_COLORS = {
        0: "#00BFA8",  # I want — teal
        1: "#A695FF",  # I feel — purple
        2: "#FF8B5C",  # Help — orange
        3: "#00D9A0",  # Yes/No — green
    }

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._child_data = db.get_child(child_id) or {}
        self._lang = self._child_data.get("language", "en")
        self._sentence = []  # list of (icon, text)
        self.setStyleSheet(MAIN_STYLE)
        self._build_ui()

    def _build_ui(self):
        self._bg = ParticleBackground(self)
        self._bg.lower()

        main = QVBoxLayout(self)
        main.setContentsMargins(28, 22, 28, 22)
        main.setSpacing(12)

        # Header
        hdr = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0,191,168,0.10); color: {COLORS['teal_deep']};
                border: 1.5px solid {COLORS['teal']}; border-radius: 10px;
                padding: 8px 16px; font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(0,191,168,0.22); }}
        """)
        back_btn.clicked.connect(self.go_back.emit)
        title = QLabel("🗨️ AAC Sentence Builder")
        title.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {COLORS['text']};")
        hdr.addWidget(back_btn)
        hdr.addSpacing(20)
        hdr.addWidget(title)
        hdr.addStretch()
        main.addLayout(hdr)

        # Sentence display
        sent_card = GlassCard(self, radius=20)
        sent_card.setMinimumHeight(110)
        sl = QHBoxLayout(sent_card)
        sl.setContentsMargins(20, 14, 20, 14)
        sl.setSpacing(10)

        self._sentence_widget = QWidget()
        self._sentence_widget.setStyleSheet("background: transparent;")
        self._sentence_layout = QHBoxLayout(self._sentence_widget)
        self._sentence_layout.setContentsMargins(0, 0, 0, 0)
        self._sentence_layout.setSpacing(8)
        self._sentence_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self._placeholder = QLabel("Tap pictograms below to build a message...")
        self._placeholder.setStyleSheet(f"font-size: 14px; color: {COLORS['text_light']}; font-style: italic;")
        self._sentence_layout.addWidget(self._placeholder)

        sl.addWidget(self._sentence_widget, 1)

        # Action buttons
        act_col = QVBoxLayout()
        act_col.setSpacing(6)

        speak_btn = QPushButton("🔊 Speak")
        speak_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #00BFA8, stop:1 #00E5FF);
                color: white; border: none; border-radius: 12px;
                padding: 8px 18px; font-size: 12px; font-weight: 700;
            }}
            QPushButton:hover {{ background: #00E5FF; }}
        """)
        speak_btn.clicked.connect(self._speak)

        clear_btn = QPushButton("🗑 Clear")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,107,126,0.12); color: #C04055;
                border: 1.5px solid rgba(255,107,126,0.4); border-radius: 12px;
                padding: 8px 18px; font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(255,107,126,0.25); }}
        """)
        clear_btn.clicked.connect(self._clear)

        backspace_btn = QPushButton("⌫ Undo")
        backspace_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0,191,168,0.10); color: {COLORS['teal_deep']};
                border: 1.5px solid {COLORS['teal']}; border-radius: 12px;
                padding: 8px 18px; font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(0,191,168,0.22); }}
        """)
        backspace_btn.clicked.connect(self._undo)

        act_col.addWidget(speak_btn)
        act_col.addWidget(backspace_btn)
        act_col.addWidget(clear_btn)
        sl.addLayout(act_col)
        main.addWidget(sent_card)

        # Categories (tabs)
        from PySide6.QtWidgets import QTabWidget
        tabs = QTabWidget()
        cats = CATEGORIES.get(self._lang, CATEGORIES["en"])
        for i, (cat_name, items) in enumerate(cats.items()):
            tab = QWidget()
            tab.setStyleSheet("background: transparent;")
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setStyleSheet("background: transparent; border: none;")

            grid_w = QWidget()
            grid_w.setStyleSheet("background: transparent;")
            grid = QGridLayout(grid_w)
            grid.setSpacing(10)
            grid.setContentsMargins(8, 8, 8, 8)

            color = self.CATEGORY_COLORS.get(i, "#00BFA8")
            for j, (icon, text) in enumerate(items):
                btn = PictogramBtn(icon, text, color)
                btn.clicked.connect(lambda checked, ic=icon, tx=text: self._add_to_sentence(ic, tx))
                grid.addWidget(btn, j // 6, j % 6)

            scroll.setWidget(grid_w)
            tab_layout = QVBoxLayout(tab)
            tab_layout.setContentsMargins(0, 0, 0, 0)
            tab_layout.addWidget(scroll)
            tabs.addTab(tab, cat_name)

        main.addWidget(tabs, 1)

    def _add_to_sentence(self, icon, text):
        try:
            self._placeholder.setVisible(False)
        except RuntimeError:
            pass  # placeholder's C++ object gone — recreated in _refresh_sentence
        self._sentence.append((icon, text))
        self._refresh_sentence()

    def _refresh_sentence(self):
        # Clear all chips — but never deleteLater the placeholder: destroying
        # its C++ object makes every later touch of self._placeholder crash.
        while self._sentence_layout.count():
            item = self._sentence_layout.takeAt(0)
            w = item.widget()
            if w is self._placeholder:
                w.setVisible(False)
            elif w is not None:
                w.deleteLater()

        if not self._sentence:
            self._placeholder.setVisible(True)
            self._sentence_layout.addWidget(self._placeholder)
            return

        for icon, text in self._sentence:
            chip = QFrame()
            chip.setStyleSheet(f"""
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #00BFA8, stop:1 #00E5FF);
                border-radius: 14px;
                padding: 6px;
            """)
            chl = QHBoxLayout(chip)
            chl.setContentsMargins(10, 6, 10, 6)
            chl.setSpacing(6)
            il = QLabel(icon)
            il.setStyleSheet("font-size: 22px; background: transparent; color: white;")
            tl = QLabel(text)
            tl.setStyleSheet("font-size: 13px; font-weight: 700; color: white; background: transparent;")
            chl.addWidget(il)
            chl.addWidget(tl)
            self._sentence_layout.addWidget(chip)
        self._sentence_layout.addStretch()

    def _speak(self):
        if not self._sentence:
            return
        full_text = " ".join(item[1] for item in self._sentence)
        try:
            from speech.tts_engine import speak
            speak(full_text, self._child_id)
        except Exception:
            pass
        try:
            db.log_chat(self._child_id, full_text, "[ARIA spoke]",
                        detected_emotion="calm",
                        suggested_activity="aac",
                        comfort_mode=False)
        except Exception:
            pass
        # Intelligence bus: communicating is the whole point — reward it and
        # let the conversation engine know what the child expressed.
        try:
            from core.child_context import get_context
            get_context().record_activity("aac", f"said: {full_text[:60]}",
                                          award=1, reason="AAC sentence")
        except Exception:
            pass

    def _clear(self):
        self._sentence = []
        self._refresh_sentence()

    def _undo(self):
        if self._sentence:
            self._sentence.pop()
            self._refresh_sentence()

    def resizeEvent(self, event):
        if hasattr(self, '_bg'):
            self._bg.resize(self.size())
        super().resizeEvent(event)
