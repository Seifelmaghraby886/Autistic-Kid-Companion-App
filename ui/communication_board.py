"""
ARIA Non-Verbal Communication Board
Large visual buttons for minimally verbal children.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGridLayout,
    QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import (
    QPainter, QColor, QPainterPath, QFont, QLinearGradient, QPen
)

from ui.components import GlassCard, ARIAFaceWidget, ParticleBackground
from ui.styles import MAIN_STYLE, COLORS
import database.db_manager as db


BUTTONS = {
    "en": [
        ("🛑", "I need a break",    "stop",       "#D96B6B"),
        ("😊", "I am happy",        "happy",      "#4CAF90"),
        ("😢", "I am sad",          "sad",        "#6B9FD4"),
        ("🔊", "Too loud",          "loud",       "#E8956D"),
        ("💧", "I want water",      "water",      "#38B8B0"),
        ("👨‍👩‍👧", "I want mom/dad", "parent",     "#D8A0E8"),
        ("🎮", "I want to play",    "play",       "#4CAF90"),
        ("✋", "Stop please",       "stop_now",   "#D96B6B"),
        ("😴", "I'm tired",         "tired",      "#A8B8D0"),
        ("🍎", "I'm hungry",        "hungry",     "#F0C040"),
        ("🤗", "I need a hug",      "hug",        "#FFB347"),
        ("🎵", "I like music",      "music",      "#9B8EC4"),
    ],
    "ar": [
        ("🛑", "محتاج راحة",       "stop",       "#D96B6B"),
        ("😊", "أنا مبسوط",        "happy",      "#4CAF90"),
        ("😢", "أنا زعلان",        "sad",        "#6B9FD4"),
        ("🔊", "الصوت عالي",       "loud",       "#E8956D"),
        ("💧", "عايز أشرب",        "water",      "#38B8B0"),
        ("👨‍👩‍👧", "عايز ماما/بابا", "parent",     "#D8A0E8"),
        ("🎮", "عايز ألعب",        "play",       "#4CAF90"),
        ("✋", "وقف لو سمحت",      "stop_now",   "#D96B6B"),
        ("😴", "أنا تعبان",        "tired",      "#A8B8D0"),
        ("🍎", "أنا جعان",         "hungry",     "#F0C040"),
        ("🤗", "محتاج حضن",        "hug",        "#FFB347"),
        ("🎵", "بحب الموسيقى",     "music",      "#9B8EC4"),
    ],
    "de": [
        ("🛑", "Ich brauche Pause",         "stop",    "#D96B6B"),
        ("😊", "Ich bin glücklich",          "happy",   "#4CAF90"),
        ("😢", "Ich bin traurig",            "sad",     "#6B9FD4"),
        ("🔊", "Es ist zu laut",             "loud",    "#E8956D"),
        ("💧", "Ich möchte Wasser",          "water",   "#38B8B0"),
        ("👨‍👩‍👧", "Ich möchte Mama/Papa",   "parent",  "#D8A0E8"),
        ("🎮", "Ich möchte spielen",         "play",    "#4CAF90"),
        ("✋", "Stopp bitte",                "stop_now","#D96B6B"),
        ("😴", "Ich bin müde",               "tired",   "#A8B8D0"),
        ("🍎", "Ich bin hungrig",            "hungry",  "#F0C040"),
        ("🤗", "Ich brauche Umarmung",       "hug",     "#FFB347"),
        ("🎵", "Ich mag Musik",              "music",   "#9B8EC4"),
    ],
}

ARIA_RESPONSES = {
    "en": {
        "stop":    "Okay! Let's take a break. 🛑",
        "happy":   "I'm so happy you're happy! 😊",
        "sad":     "I'm here with you. It's okay to be sad. 💙",
        "loud":    "I'll help make things quieter. 🤫",
        "water":   "Please get some water! 💧",
        "parent":  "Let's call mom or dad right now. 👨‍👩‍👧",
        "play":    "Yes! Let's play! 🎮",
        "stop_now":"Of course. Stopping right now. ✋",
        "tired":   "Rest is important. Take it easy. 😴",
        "hungry":  "Let's find something yummy to eat! 🍎",
        "hug":     "Sending you a big virtual hug! 🤗",
        "music":   "Music makes everything better! 🎵",
    },
    "ar": {
        "stop":    "تمام! خلينا ناخد راحة. 🛑",
        "happy":   "أنا مبسوط إنك مبسوط! 😊",
        "sad":     "أنا معاك. عادي تحس بزعل. 💙",
        "loud":    "هاساعدك تعمل الأمور أهدى. 🤫",
        "water":   "اشرب ماية! 💧",
        "parent":  "خلينا ننادي ماما أو بابا دلوقتي. 👨‍👩‍👧",
        "play":    "أيوه! خلينا نلعب! 🎮",
        "stop_now":"طبعاً. هوقف دلوقتي. ✋",
        "tired":   "الراحة مهمة. ارتاح شوية. 😴",
        "hungry":  "خلينا نلاقي حاجة تتاكل! 🍎",
        "hug":     "بعتلك حضن كبير! 🤗",
        "music":   "الموسيقى بتحسن كل حاجة! 🎵",
    },
    "de": {
        "stop":    "Okay! Machen wir eine Pause. 🛑",
        "happy":   "Ich freue mich, dass du glücklich bist! 😊",
        "sad":     "Ich bin bei dir. Es ist okay, traurig zu sein. 💙",
        "loud":    "Ich helfe, es ruhiger zu machen. 🤫",
        "water":   "Bitte hol dir etwas Wasser! 💧",
        "parent":  "Lass uns Mama oder Papa rufen. 👨‍👩‍👧",
        "play":    "Ja! Lass uns spielen! 🎮",
        "stop_now":"Natürlich. Ich höre sofort auf. ✋",
        "tired":   "Ruhe ist wichtig. Erhol dich. 😴",
        "hungry":  "Lass uns etwas Leckeres finden! 🍎",
        "hug":     "Ich schicke dir eine große Umarmung! 🤗",
        "music":   "Musik macht alles besser! 🎵",
    },
}


class CommButton(QWidget):
    pressed = Signal(str, str, str)  # action, label, color

    def __init__(self, icon, label, action, color, parent=None):
        super().__init__(parent)
        self._action = action
        self._color = color
        self._hover = False
        self._pressed_anim = 0.0
        self.setFixedSize(160, 120)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignCenter)

        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 40px; background: transparent;")

        label_lbl = QLabel(label)
        label_lbl.setAlignment(Qt.AlignCenter)
        label_lbl.setWordWrap(True)
        label_lbl.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {COLORS['text']}; background: transparent;")

        layout.addWidget(icon_lbl)
        layout.addWidget(label_lbl)

    def enterEvent(self, e):
        self._hover = True; self.update()
    def leaveEvent(self, e):
        self._hover = False; self.update()
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.pressed.emit(self._action, "", self._color)
            self._animate_press()
    def _animate_press(self):
        self._pressed_anim = 1.0
        self.update()
        QTimer.singleShot(150, lambda: self._reset_press())
    def _reset_press(self):
        self._pressed_anim = 0.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        c = QColor(self._color)
        path = QPainterPath()
        r = 18 - self._pressed_anim * 4
        path.addRoundedRect(4, 4, w - 8, h - 8, r, r)

        if self._pressed_anim > 0:
            c.setAlpha(200)
            painter.fillPath(path, c)
            text_c = QColor("white")
        elif self._hover:
            bg = QColor(c.red(), c.green(), c.blue(), 50)
            painter.fillPath(path, bg)
            border_c = QColor(c)
            border_c.setAlpha(200)
            from PySide6.QtGui import QPen
            painter.setPen(QPen(border_c, 2.5))
            painter.drawPath(path)
        else:
            bg = QColor(c.red(), c.green(), c.blue(), 20)
            painter.fillPath(path, bg)
            border_c = QColor(c)
            border_c.setAlpha(80)
            from PySide6.QtGui import QPen
            painter.setPen(QPen(border_c, 1.5))
            painter.drawPath(path)


class CommunicationBoardScreen(QWidget):
    go_back = Signal()

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._child_data = db.get_child(child_id) or {}
        self.setStyleSheet(MAIN_STYLE)
        self._build_ui()

    def _build_ui(self):
        self._bg = ParticleBackground(self)
        self._bg.lower()

        main = QVBoxLayout(self)
        main.setContentsMargins(28, 24, 28, 24)
        main.setSpacing(14)

        # Header
        hdr = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(56,184,176,0.10); color: {COLORS['teal_deep']};
                border: 1.5px solid {COLORS['teal']}; border-radius: 10px;
                padding: 8px 16px; font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(56,184,176,0.22); }}
        """)
        back_btn.clicked.connect(self.go_back.emit)

        lang = self._child_data.get("language", "en")
        titles = {"en": "🔤 How do you feel?", "ar": "🔤 إيه إحساسك؟", "de": "🔤 Wie fühlst du dich?"}
        title = QLabel(titles.get(lang, titles["en"]))
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {COLORS['text']};")

        hdr.addWidget(back_btn)
        hdr.addSpacing(20)
        hdr.addWidget(title)
        hdr.addStretch()
        main.addLayout(hdr)

        body = QHBoxLayout()
        body.setSpacing(18)

        # ── Left: buttons grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        buttons_w = QWidget()
        buttons_w.setStyleSheet("background: transparent;")
        grid = QGridLayout(buttons_w)
        grid.setSpacing(14)
        grid.setContentsMargins(0, 0, 0, 0)

        button_data = BUTTONS.get(lang, BUTTONS["en"])
        for i, (icon, label, action, color) in enumerate(button_data):
            btn = CommButton(icon, label, action, color, self)
            btn.pressed.connect(self._on_button_press)
            grid.addWidget(btn, i // 4, i % 4)

        scroll.setWidget(buttons_w)
        body.addWidget(scroll, 1)

        # ── Right: ARIA reaction
        right = QVBoxLayout()
        right.setSpacing(14)

        face_card = GlassCard(self, radius=22)
        fc = QVBoxLayout(face_card)
        fc.setContentsMargins(20, 20, 20, 20)
        fc.setAlignment(Qt.AlignCenter)

        self._aria_face = ARIAFaceWidget(size=140)
        fc.addWidget(self._aria_face, alignment=Qt.AlignCenter)

        self._aria_response_lbl = QLabel("Tap any button to tell ARIA how you feel!")
        self._aria_response_lbl.setAlignment(Qt.AlignCenter)
        self._aria_response_lbl.setWordWrap(True)
        self._aria_response_lbl.setStyleSheet(f"""
            font-size: 14px; font-weight: 600;
            color: {COLORS['teal_deep']}; padding: 10px;
            line-height: 1.6;
        """)
        fc.addWidget(self._aria_response_lbl)
        right.addWidget(face_card)

        # Last pressed display
        self._last_pressed = QLabel("")
        self._last_pressed.setAlignment(Qt.AlignCenter)
        self._last_pressed.setStyleSheet(f"font-size: 40px; padding: 10px;")
        right.addWidget(self._last_pressed)

        right.addStretch()
        body.addLayout(right)
        main.addLayout(body, 1)

    def _on_button_press(self, action, label, color):
        lang = self._child_data.get("language", "en")
        responses = ARIA_RESPONSES.get(lang, ARIA_RESPONSES["en"])
        response = responses.get(action, "I hear you! 💙")
        self._aria_response_lbl.setText(response)

        # Set face
        expr_map = {
            "happy":    "happy",
            "sad":      "sad",
            "stop":     "thinking",
            "stop_now": "thinking",
            "loud":     "surprised",
            "water":    "calm",
            "parent":   "calm",
            "play":     "happy",
            "tired":    "sleepy",
            "hungry":   "thinking",
            "hug":      "happy",
            "music":    "happy",
        }
        self._aria_face.set_expression(expr_map.get(action, "calm"))

        # Log
        db.log_emotion(self._child_id, action, 0.9,
                       source="comm_board", action=f"button_{action}")

        # TTS
        try:
            from speech.tts_engine import speak
            QTimer.singleShot(50, lambda: speak(response, self._child_id))
        except Exception:
            pass

    def resizeEvent(self, event):
        if hasattr(self, '_bg'):
            self._bg.resize(self.size())
        super().resizeEvent(event)
