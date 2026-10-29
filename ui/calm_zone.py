"""
ARIA Calm Zone
Breathing exercises, comfort mode, and emotion regulation.
"""

import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QColor, QLinearGradient, QRadialGradient, QFont, QPainterPath

from ui.components import GlassCard, ARIAFaceWidget, BreathingCircle, ParticleBackground
from ui.styles import MAIN_STYLE, COLORS
import database.db_manager as db


class ComfortPhraseCard(QWidget):
    def __init__(self, icon, text, color, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        self.setStyleSheet(f"""
            background: rgba(255,255,255,0.85);
            border: 1px solid {color}44;
            border-left: 4px solid {color};
            border-radius: 12px;
        """)
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 22px; background: transparent;")
        text_lbl = QLabel(text)
        text_lbl.setStyleSheet(f"font-size: 14px; color: {COLORS['text']}; background: transparent;")
        text_lbl.setWordWrap(True)
        layout.addWidget(icon_lbl)
        layout.addWidget(text_lbl, 1)


class ActivityTile(QWidget):
    clicked = Signal(str)

    def __init__(self, key, icon, title, desc, color, parent=None):
        super().__init__(parent)
        self._key = key
        self._color = color
        self._hover = False
        self.setFixedSize(180, 130)
        self.setCursor(Qt.PointingHandCursor)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 12)
        layout.setSpacing(4)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 30px; background: transparent;")
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLORS['text']}; background: transparent;")
        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet(f"font-size: 10px; color: {COLORS['text_light']}; background: transparent;")
        desc_lbl.setWordWrap(True)

        layout.addWidget(icon_lbl)
        layout.addWidget(title_lbl)
        layout.addWidget(desc_lbl)
        layout.addStretch()

    def enterEvent(self, e):
        self._hover = True; self.update()
    def leaveEvent(self, e):
        self._hover = False; self.update()
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit(self._key)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 18, 18)
        if self._hover:
            bg = QLinearGradient(0, 0, self.width(), self.height())
            c = QColor(self._color)
            bg.setColorAt(0, QColor(255, 255, 255, 230))
            bg.setColorAt(1, QColor(c.red(), c.green(), c.blue(), 30))
            painter.fillPath(path, bg)
            from PySide6.QtGui import QPen
            painter.setPen(QPen(QColor(self._color), 2))
            painter.drawPath(path)
        else:
            painter.fillPath(path, QColor(255, 255, 255, 180))
            from PySide6.QtGui import QPen
            painter.setPen(QPen(QColor(56, 184, 176, 40), 1.5))
            painter.drawPath(path)


class CalmZoneScreen(QWidget):
    go_back = Signal()
    activity_started = Signal(str)

    def __init__(self, child_id, auto_start=False, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._child_data = db.get_child(child_id) or {}
        self._auto_start = auto_start
        self.setStyleSheet(MAIN_STYLE)
        self._build_ui()
        if auto_start:
            QTimer.singleShot(500, self._auto_comfort_start)

    def _build_ui(self):
        self._bg = ParticleBackground(self)
        self._bg.lower()

        # Calm background overlay
        self.setStyleSheet(self.styleSheet() + """
            QWidget#calmBg {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #EAF8F8, stop:0.5 #F0EEFF, stop:1 #EAF8F8);
            }
        """)

        main = QVBoxLayout(self)
        main.setContentsMargins(36, 28, 36, 28)
        main.setSpacing(16)

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

        title = QLabel("🌿 Calm Zone")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {COLORS['text']};")
        subtitle = QLabel("A safe space to relax and feel better")
        subtitle.setStyleSheet(f"font-size: 13px; color: {COLORS['text_light']};")

        hdr.addWidget(back_btn)
        hdr.addSpacing(20)
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        hdr.addLayout(title_col)
        hdr.addStretch()
        main.addLayout(hdr)

        # Body
        body = QHBoxLayout()
        body.setSpacing(18)

        # ── Left: Breathing + ARIA
        left = QVBoxLayout()
        left.setSpacing(14)

        # ARIA comfort face
        face_card = GlassCard(self, radius=24)
        face_layout = QVBoxLayout(face_card)
        face_layout.setContentsMargins(20, 20, 20, 20)
        face_layout.setAlignment(Qt.AlignCenter)

        self._aria_face = ARIAFaceWidget(size=130)
        self._aria_face.set_expression("comfort")
        face_layout.addWidget(self._aria_face, alignment=Qt.AlignCenter)

        self._comfort_msg = QLabel("I'm here with you 💙")
        self._comfort_msg.setAlignment(Qt.AlignCenter)
        self._comfort_msg.setWordWrap(True)
        self._comfort_msg.setStyleSheet(f"""
            font-size: 15px; font-weight: 600;
            color: {COLORS['teal_deep']}; padding: 8px;
        """)
        face_layout.addWidget(self._comfort_msg)
        left.addWidget(face_card)

        # Breathing circle
        breathe_card = GlassCard(self, radius=24)
        breathe_layout = QVBoxLayout(breathe_card)
        breathe_layout.setContentsMargins(16, 14, 16, 14)
        breathe_layout.setAlignment(Qt.AlignCenter)

        breathe_title = QLabel("BREATHING EXERCISE")
        breathe_title.setAlignment(Qt.AlignCenter)
        breathe_title.setStyleSheet(f"""
            font-size: 10px; font-weight: 700;
            color: {COLORS['teal_deep']}; letter-spacing: 2px;
        """)
        breathe_layout.addWidget(breathe_title)

        self._breathing = BreathingCircle(self)
        breathe_layout.addWidget(self._breathing, alignment=Qt.AlignCenter)

        speed_row = QHBoxLayout()
        for label, speed in [("Slow 🐢", 0.010), ("Normal 😌", 0.015), ("Guided 🌊", 0.008)]:
            btn = QPushButton(label)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(56,184,176,0.10); color: {COLORS['teal_deep']};
                    border: 1px solid rgba(56,184,176,0.25); border-radius: 10px;
                    padding: 6px 12px; font-size: 11px;
                }}
                QPushButton:hover {{ background: rgba(56,184,176,0.22); }}
            """)
            btn.clicked.connect(lambda checked, s=speed: self._breathing.set_speed(s))
            speed_row.addWidget(btn)
        breathe_layout.addLayout(speed_row)
        left.addWidget(breathe_card)
        body.addLayout(left)

        # ── Right: Comfort phrases + activities
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setFrameShape(QFrame.NoFrame)
        right_scroll.setStyleSheet("background: transparent; border: none;")

        right_content = QWidget()
        right_content.setStyleSheet("background: transparent;")
        right = QVBoxLayout(right_content)
        right.setSpacing(14)

        # Comfort phrases
        lang = self._child_data.get("language", "en")
        name = self._child_data.get("name", "")
        phrases = self._get_phrases(lang, name)

        phrases_card = GlassCard(self, radius=22)
        pl = QVBoxLayout(phrases_card)
        pl.setContentsMargins(18, 16, 18, 16)
        pl.setSpacing(8)
        pl_title = QLabel("COMFORT PHRASES")
        pl_title.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {COLORS['teal_deep']}; letter-spacing: 2px;")
        pl.addWidget(pl_title)
        for icon, text in phrases:
            pl.addWidget(ComfortPhraseCard(icon, text, COLORS["teal"]))
        right.addWidget(phrases_card)

        # Calming activities
        act_card = GlassCard(self, radius=22)
        al = QVBoxLayout(act_card)
        al.setContentsMargins(18, 16, 18, 16)
        al.setSpacing(10)
        al_title = QLabel("CALMING ACTIVITIES")
        al_title.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {COLORS['teal_deep']}; letter-spacing: 2px;")
        al.addWidget(al_title)

        tiles_grid = QHBoxLayout()
        tiles_grid.setSpacing(12)
        activities = [
            ("breathing", "🌬️", "Breathing", "Slow breaths",   "#38B8B0"),
            ("counting",  "🔢", "Counting",  "Count to 10",    "#6B9FD4"),
            ("story",     "📖", "Story",     "Calm story",     "#D8A0E8"),
            ("music",     "🎵", "Music",     "Soothing tones", "#4CAF90"),
        ]
        for key, icon, title, desc, color in activities:
            tile = ActivityTile(key, icon, title, desc, color, self)
            tile.clicked.connect(self._on_activity)
            tiles_grid.addWidget(tile)
        tiles_grid.addStretch()
        al.addLayout(tiles_grid)
        right.addWidget(act_card)

        # Quick help buttons (non-verbal)
        help_card = GlassCard(self, radius=22)
        hl = QVBoxLayout(help_card)
        hl.setContentsMargins(18, 16, 18, 16)
        hl.setSpacing(10)
        hl_title = QLabel("QUICK HELP")
        hl_title.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {COLORS['teal_deep']}; letter-spacing: 2px;")
        hl.addWidget(hl_title)

        help_btns = QGridLayout()
        help_btns.setSpacing(10)
        helps = self._get_help_buttons(lang)
        for i, (icon, text, action) in enumerate(helps):
            btn = QPushButton(f"{icon}  {text}")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(56,184,176,0.10);
                    color: {COLORS['text']};
                    border: 1.5px solid rgba(56,184,176,0.3);
                    border-radius: 14px; padding: 12px 16px;
                    font-size: 13px; font-weight: 600;
                    text-align: left;
                }}
                QPushButton:hover {{ background: rgba(56,184,176,0.22); }}
            """)
            btn.clicked.connect(lambda checked, a=action: self._on_help(a))
            help_btns.addWidget(btn, i // 2, i % 2)
        hl.addLayout(help_btns)
        right.addWidget(help_card)
        right.addStretch()

        right_scroll.setWidget(right_content)
        body.addWidget(right_scroll, 1)

        main.addLayout(body, 1)

    def _get_phrases(self, lang, name):
        n = f" {name}" if name else ""
        phrases_map = {
            "en": [
                ("💙", f"I'm here with you{n}."),
                ("🌬️", "Let's take one slow breath together."),
                ("🤗", "It's okay. We can slow down."),
                ("🤫", "You don't have to talk right now."),
                ("🌿", "Everything will be okay."),
            ],
            "ar": [
                ("💙", f"أنا معاك{n}."),
                ("🌬️", "خلينا ناخد نفس صغير سوا."),
                ("🤗", "مفيش مشكلة، نقدر نهدى شوية."),
                ("🤫", "مش لازم تتكلم دلوقتي."),
                ("🌿", "هيبقى كله تمام."),
            ],
            "de": [
                ("💙", f"Ich bin bei dir{n}."),
                ("🌬️", "Lass uns langsam zusammen atmen."),
                ("🤗", "Das ist okay. Wir können ruhig bleiben."),
                ("🤫", "Du musst jetzt nicht sprechen."),
                ("🌿", "Alles wird gut."),
            ],
        }
        return phrases_map.get(lang, phrases_map["en"])

    def _get_help_buttons(self, lang):
        helps_map = {
            "en": [
                ("🫁", "I need to breathe",   "breathing"),
                ("🤗", "I need a hug",         "hug"),
                ("🤫", "I need quiet",         "quiet"),
                ("💧", "I want water",         "water"),
                ("🛑", "Stop please",          "stop"),
                ("👨‍👩‍👧", "I want mom/dad",  "parent"),
            ],
            "ar": [
                ("🫁", "محتاج اتنفس",    "breathing"),
                ("🤗", "محتاج حضن",      "hug"),
                ("🤫", "محتاج سكوت",     "quiet"),
                ("💧", "عايز أشرب",      "water"),
                ("🛑", "وقف لو سمحت",    "stop"),
                ("👨‍👩‍👧", "عايز ماما/بابا", "parent"),
            ],
            "de": [
                ("🫁", "Ich möchte atmen",         "breathing"),
                ("🤗", "Ich brauche eine Umarmung", "hug"),
                ("🤫", "Ich brauche Stille",        "quiet"),
                ("💧", "Ich möchte Wasser",         "water"),
                ("🛑", "Stopp bitte",               "stop"),
                ("👨‍👩‍👧", "Ich möchte Mama/Papa", "parent"),
            ],
        }
        return helps_map.get(lang, helps_map["en"])

    def _on_activity(self, key):
        self.activity_started.emit(key)
        db.log_emotion(self._child_id, "calm", 0.8, source="calm_zone",
                       action=f"started_{key}")
        # Intelligence bus: calming counts — one star, and the session
        # context (AI suggestions, conversation memory) knows about it.
        try:
            from core.child_context import get_context
            get_context().record_activity(f"calm:{key}", "completed",
                                          award=1, reason="calm activity")
        except Exception:
            pass

    def _on_help(self, action):
        lang = self._child_data.get("language", "en")
        messages = {
            "breathing": {"en": "Let's breathe together.", "ar": "خلينا نتنفس سوا.", "de": "Lass uns zusammen atmen."},
            "hug":       {"en": "I'm sending you a virtual hug! 🤗", "ar": "بعتلك حضن افتراضي! 🤗", "de": "Ich schicke dir eine virtuelle Umarmung! 🤗"},
            "quiet":     {"en": "Shhh. Nice and quiet. 🤫", "ar": "هادي وهادي. 🤫", "de": "Ruhig und leise. 🤫"},
            "water":     {"en": "Please get some water. 💧", "ar": "اشرب ماية. 💧", "de": "Bitte hol Wasser. 💧"},
            "stop":      {"en": "I'm stopping now. Take your time.", "ar": "هأوقف دلوقتي. خد وقتك.", "de": "Ich halte jetzt an. Nimm dir Zeit."},
            "parent":    {"en": "Let's call mom or dad.", "ar": "خلينا نندي ماما أو بابا.", "de": "Lass uns Mama oder Papa rufen."},
        }
        msg = messages.get(action, {}).get(lang, messages.get(action, {}).get("en", ""))
        if msg:
            self._comfort_msg.setText(msg)
            db.log_emotion(self._child_id, "calm", 0.7, source="calm_zone",
                           action=f"help_{action}")

    def _auto_comfort_start(self):
        lang = self._child_data.get("language", "en")
        name = self._child_data.get("name", "")
        msgs = {
            "en": f"I'm here with you{', ' + name if name else ''}. Let's take a slow breath together. 💙",
            "ar": f"أنا معاك{' يا ' + name if name else ''}. خلينا ناخد نفس صغير سوا. 💙",
            "de": f"Ich bin bei dir{', ' + name if name else ''}. Lass uns zusammen atmen. 💙",
        }
        self._comfort_msg.setText(msgs.get(lang, msgs["en"]))
        self._aria_face.set_expression("comfort")

    def resizeEvent(self, event):
        if hasattr(self, '_bg'):
            self._bg.resize(self.size())
        super().resizeEvent(event)
