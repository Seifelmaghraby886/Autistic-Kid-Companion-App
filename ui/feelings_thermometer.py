"""
ARIA Feelings Thermometer — autism-critical intensity scale.
Helps identify rising distress before meltdown.
"""

import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QSlider
)
from PySide6.QtCore import Qt, Signal, QTimer, QPointF, QRectF
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QPainterPath, QLinearGradient, QRadialGradient

from ui.components import GlassCard, ARIAFaceWidget
from ui.animated_bg import MeshBackground
from ui.styles import MAIN_STYLE, COLORS
import database.db_manager as db


LEVEL_DATA = [
    (1,  "Super calm",       "🥰", "#00D9A0"),
    (2,  "Calm",              "😊", "#00BFA8"),
    (3,  "Okay",              "🙂", "#5CE5DC"),
    (4,  "Slightly bothered", "😐", "#FFE066"),
    (5,  "Frustrated",        "😤", "#FFB73D"),
    (6,  "Annoyed",           "😠", "#FF9966"),
    (7,  "Upset",             "😣", "#FF7B5C"),
    (8,  "Very upset",        "😫", "#FF6B7E"),
    (9,  "Almost meltdown",   "😭", "#E54B5F"),
    (10, "Meltdown",          "🤯", "#C03050"),
]


SUGGESTIONS = {
    "en": {
        1: "Wonderful! Keep enjoying the calm.",
        3: "You're doing okay. Want to chat?",
        5: "Let's slow down. Try a deep breath together.",
        7: "It's okay. Let's try the Calm Zone now.",
        9: "Stop everything. Let's get safe and quiet right now.",
    },
    "ar": {
        1: "رائع! استمتع بالهدوء.",
        3: "أنت كويس. عايز تتكلم؟",
        5: "خلينا نهدى. خد نفس عميق سوا.",
        7: "مفيش مشكلة. خلينا نروح للهدوء.",
        9: "وقف كل حاجة. خلينا نهدى ونسكت دلوقتي.",
    },
    "de": {
        1: "Wunderbar! Genieße die Ruhe.",
        3: "Du bist okay. Möchtest du reden?",
        5: "Lass uns langsamer machen. Atme tief ein.",
        7: "Es ist okay. Lass uns in die Ruhezone gehen.",
        9: "Stopp alles. Lass uns sicher und ruhig sein.",
    },
}


class ThermometerWidget(QWidget):
    """Big visual thermometer that fills based on selected level."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(120, 350)
        self._level = 1
        self._target = 1
        self._t = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self._timer.start(33)

    def set_level(self, lvl):
        self._target = max(1, min(10, lvl))

    def _update(self):
        if abs(self._level - self._target) > 0.05:
            self._level += (self._target - self._level) * 0.15
        else:
            self._level = self._target
        self._t += 0.05
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx = w / 2

        # Tube
        tube_w = 50
        tube_h = h - 100
        tube_x = cx - tube_w / 2
        tube_y = 30

        # Outer tube
        path = QPainterPath()
        path.addRoundedRect(tube_x, tube_y, tube_w, tube_h, tube_w / 2, tube_w / 2)
        painter.fillPath(path, QColor(240, 245, 250))
        painter.setPen(QPen(QColor(180, 195, 215), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        # Bulb at bottom
        bulb_r = 35
        bulb_y = h - 50
        painter.setBrush(QColor(240, 245, 250))
        painter.setPen(QPen(QColor(180, 195, 215), 2))
        painter.drawEllipse(QPointF(cx, bulb_y), bulb_r, bulb_r)

        # Determine fill color from level
        idx = max(0, min(9, int(self._level) - 1))
        fill_color = QColor(LEVEL_DATA[idx][3])

        # Fill mercury
        fill_pct = (self._level - 1) / 9
        fill_h = tube_h * fill_pct
        fill_y = tube_y + tube_h - fill_h

        painter.save()
        clip = QPainterPath()
        clip.addRoundedRect(tube_x, fill_y, tube_w, fill_h, tube_w / 2, tube_w / 2)
        clip.addEllipse(QPointF(cx, bulb_y), bulb_r - 2, bulb_r - 2)
        painter.setClipPath(clip)
        grad = QLinearGradient(0, tube_y, 0, h)
        grad.setColorAt(0, fill_color.lighter(120))
        grad.setColorAt(1, fill_color)
        painter.fillRect(QRectF(0, 0, w, h), grad)
        painter.restore()

        # Tick marks
        painter.setPen(QPen(QColor(120, 140, 160), 1.5))
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        for i in range(1, 11):
            y = tube_y + tube_h * (1 - (i - 1) / 9)
            painter.drawLine(QPointF(tube_x - 8, y), QPointF(tube_x - 2, y))
            painter.drawLine(QPointF(tube_x + tube_w + 2, y), QPointF(tube_x + tube_w + 8, y))
            painter.drawText(QRectF(tube_x - 35, y - 8, 25, 16), Qt.AlignRight | Qt.AlignVCenter, str(i))

        # Pulsing glow at current level when high
        if self._level >= 7:
            pulse = abs(math.sin(self._t * 4))
            glow = QColor(fill_color)
            glow.setAlpha(int(60 + pulse * 80))
            painter.setBrush(glow)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(cx, bulb_y), bulb_r + 10 + pulse * 8, bulb_r + 10 + pulse * 8)


class FeelingsThermometerScreen(QWidget):
    go_back = Signal()

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._child = db.get_child(child_id) or {}
        self._lang = self._child.get("language", "en")
        self._current_level = 1
        self.setStyleSheet(MAIN_STYLE)
        self._build_ui()

    def _build_ui(self):
        self._bg = MeshBackground(self, intensity=0.5)
        self._bg.lower()

        main = QVBoxLayout(self)
        main.setContentsMargins(32, 24, 32, 24)
        main.setSpacing(14)

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
        title = QLabel("🌡 Feelings Thermometer")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {COLORS['text']};")
        sub = QLabel("How big is your feeling right now?")
        sub.setStyleSheet(f"font-size: 13px; color: {COLORS['text_light']};")
        hdr.addWidget(back_btn); hdr.addSpacing(20)
        col = QVBoxLayout(); col.addWidget(title); col.addWidget(sub)
        hdr.addLayout(col); hdr.addStretch()
        main.addLayout(hdr)

        body = QHBoxLayout()
        body.setSpacing(20)

        # ── LEFT: thermometer
        therm_card = GlassCard(self, radius=22)
        therm_card.setMaximumWidth(220)
        tl = QVBoxLayout(therm_card)
        tl.setContentsMargins(20, 20, 20, 20)
        tl.setAlignment(Qt.AlignCenter)
        self._thermometer = ThermometerWidget(self)
        tl.addWidget(self._thermometer)
        body.addWidget(therm_card)

        # ── RIGHT: level buttons + ARIA
        right = QVBoxLayout()
        right.setSpacing(14)

        # ARIA reaction
        aria_card = GlassCard(self, radius=22)
        ac = QHBoxLayout(aria_card)
        ac.setContentsMargins(20, 16, 20, 16)
        self._face = ARIAFaceWidget(size=90)
        self._face.set_expression("calm")
        self._aria_msg = QLabel("Tap a number to tell me how big your feeling is right now.")
        self._aria_msg.setWordWrap(True)
        self._aria_msg.setStyleSheet(f"font-size: 14px; color: {COLORS['teal_deep']}; font-weight: 600;")
        ac.addWidget(self._face)
        ac.addSpacing(12)
        ac.addWidget(self._aria_msg, 1)
        right.addWidget(aria_card)

        # Level buttons grid
        levels_card = GlassCard(self, radius=22)
        ll = QVBoxLayout(levels_card)
        ll.setContentsMargins(20, 16, 20, 16)
        ll.addWidget(self._section("PICK YOUR LEVEL"))

        grid = QGridLayout()
        grid.setSpacing(6)
        for i, (n, name, emoji, color) in enumerate(LEVEL_DATA):
            btn = QPushButton(f"{emoji}  {n}\n{name}")
            btn.setFixedHeight(60)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255,255,255,0.85);
                    color: {COLORS['text']};
                    border: 2px solid {color}66;
                    border-radius: 12px;
                    font-size: 12px; font-weight: 700;
                    text-align: left;
                    padding-left: 12px;
                }}
                QPushButton:hover {{
                    background: {color}33;
                    border-color: {color};
                }}
            """)
            btn.clicked.connect(lambda checked, lvl=n, c=color: self._select_level(lvl, c))
            grid.addWidget(btn, i // 2, i % 2)
        ll.addLayout(grid)
        right.addWidget(levels_card, 1)

        # Action button
        self._action_btn = QPushButton("✨  Get a Strategy")
        self._action_btn.setEnabled(False)
        self._action_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #00BFA8, stop:0.5 #00E5FF, stop:1 #B388FF);
                color: white; border: none; border-radius: 14px;
                padding: 12px 28px; font-size: 14px; font-weight: 700;
            }}
            QPushButton:disabled {{ background: #C0C8D4; color: #8A9CB8; }}
        """)
        self._action_btn.clicked.connect(self._take_action)
        right.addWidget(self._action_btn)

        body.addLayout(right, 1)
        main.addLayout(body, 1)

    def _section(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {COLORS['teal_deep']}; letter-spacing: 2px; padding-bottom: 4px;")
        return lbl

    def _select_level(self, level, color):
        self._current_level = level
        self._thermometer.set_level(level)

        # Find suggestion
        suggestions = SUGGESTIONS.get(self._lang, SUGGESTIONS["en"])
        # Find closest level key
        sug = ""
        for key in sorted(suggestions.keys()):
            if level <= key:
                sug = suggestions[key]
                break
        if not sug:
            sug = suggestions[max(suggestions.keys())]

        self._aria_msg.setText(sug)

        if level >= 7:
            self._face.set_expression("comfort")
            self._action_btn.setText("🌿  Open Calm Zone Now")
            self._action_btn.setEnabled(True)
        elif level >= 5:
            self._face.set_expression("thinking")
            self._action_btn.setText("🌬️  Try Breathing")
            self._action_btn.setEnabled(True)
        elif level >= 3:
            self._face.set_expression("calm")
            self._action_btn.setText("💬  Talk with ARIA")
            self._action_btn.setEnabled(True)
        else:
            self._face.set_expression("happy")
            self._action_btn.setText("✨  Keep It Going")
            self._action_btn.setEnabled(True)

        # Log
        try:
            emotion = "anger" if level >= 7 else "calm" if level <= 3 else "neutral"
            db.log_emotion(self._child_id, emotion, level / 10.0,
                           source="thermometer", action_taken=f"level_{level}")
        except Exception:
            pass

        # Intelligence bus: self-identified arousal level feeds suggestions
        # (a hot reading steers the home card toward the Calm Zone).
        try:
            from core.child_context import get_context
            get_context().record_emotion(emotion, source="self_report")
        except Exception:
            pass

        # Speak the suggestion
        try:
            from speech.tts_engine import speak
            speak(sug, self._child_id, style="soft")
        except Exception:
            pass

    def _take_action(self):
        # Future: this could navigate to relevant screen
        if self._current_level >= 7:
            self._aria_msg.setText("Take 3 slow breaths with me. In... and out... 🌬️")
        else:
            self._aria_msg.setText("You're doing great! Keep going. 💚")

    def resizeEvent(self, event):
        if hasattr(self, '_bg'):
            self._bg.resize(self.size())
        super().resizeEvent(event)
