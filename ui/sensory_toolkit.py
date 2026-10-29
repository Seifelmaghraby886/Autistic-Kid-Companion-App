"""
ARIA Sensory Toolkit
Visual stim and calming sensory experiences for autistic children.
Includes: Lava Lamp, Liquid Galaxy, Slow Bubbles, Shape Morphing, Color Therapy.
"""

import math
import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, QTimer, Signal, QPointF, QRectF
from PySide6.QtGui import (
    QPainter, QColor, QLinearGradient, QRadialGradient,
    QPainterPath, QFont, QPen, QBrush
)

from ui.components import GlassCard, ParticleBackground
from ui.styles import MAIN_STYLE, COLORS
import database.db_manager as db


# ══════════════════════════════════════════════════════════════
#  Liquid Galaxy — flowing colorful blobs
# ══════════════════════════════════════════════════════════════
class LiquidGalaxy(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 500)
        self._t = 0.0
        self._blobs = []
        for _ in range(8):
            self._blobs.append({
                "x": random.uniform(0.2, 0.8),
                "y": random.uniform(0.2, 0.8),
                "vx": random.uniform(-0.0008, 0.0008),
                "vy": random.uniform(-0.0008, 0.0008),
                "r": random.uniform(80, 160),
                "hue": random.choice([180, 220, 280, 200, 260]),
            })
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self._timer.start(30)

    def _update(self):
        self._t += 0.01
        for b in self._blobs:
            b["x"] += b["vx"]
            b["y"] += b["vy"]
            if b["x"] < 0.1 or b["x"] > 0.9: b["vx"] *= -1
            if b["y"] < 0.1 or b["y"] > 0.9: b["vy"] *= -1
            b["hue"] = (b["hue"] + 0.15) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Background
        bg = QLinearGradient(0, 0, w, h)
        bg.setColorAt(0, QColor(10, 15, 35))
        bg.setColorAt(0.5, QColor(20, 10, 45))
        bg.setColorAt(1, QColor(15, 25, 50))
        painter.fillRect(self.rect(), bg)

        # Liquid blobs
        for b in self._blobs:
            cx = b["x"] * w
            cy = b["y"] * h + math.sin(self._t * 2 + b["x"] * 5) * 20
            r = b["r"] + math.sin(self._t + b["y"] * 3) * 15

            color = QColor.fromHsl(int(b["hue"]), 220, 140)
            grad = QRadialGradient(cx, cy, r)
            grad.setColorAt(0, QColor(color.red(), color.green(), color.blue(), 200))
            grad.setColorAt(0.5, QColor(color.red(), color.green(), color.blue(), 100))
            grad.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 0))
            painter.setBrush(grad)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(cx, cy), r, r)

        # Subtle stars
        painter.setBrush(QColor(255, 255, 255, 50))
        for i in range(60):
            x = (math.sin(i * 1.7 + self._t * 0.3) + 1) / 2 * w
            y = (math.cos(i * 2.1) + 1) / 2 * h
            r = 1 + math.sin(self._t + i) * 0.5
            painter.drawEllipse(QPointF(x, y), r, r)


# ══════════════════════════════════════════════════════════════
#  Slow Bubbles — relaxing bubbles rising
# ══════════════════════════════════════════════════════════════
class SlowBubbles(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 500)
        self._bubbles = []
        self._spawn_timer = QTimer(self)
        self._spawn_timer.timeout.connect(self._spawn_bubble)
        self._spawn_timer.start(800)
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._update)
        self._anim_timer.start(30)

    def _spawn_bubble(self):
        if len(self._bubbles) < 30:
            self._bubbles.append({
                "x": random.uniform(0.05, 0.95),
                "y": 1.1,
                "speed": random.uniform(0.001, 0.003),
                "r": random.uniform(20, 60),
                "wobble": random.uniform(0, math.pi * 2),
                "hue": random.choice([180, 200, 240, 280]),
            })

    def _update(self):
        for b in self._bubbles[:]:
            b["y"] -= b["speed"]
            b["wobble"] += 0.05
            if b["y"] < -0.1:
                self._bubbles.remove(b)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        bg = QLinearGradient(0, 0, 0, h)
        bg.setColorAt(0, QColor(10, 30, 60))
        bg.setColorAt(1, QColor(20, 60, 100))
        painter.fillRect(self.rect(), bg)

        for b in self._bubbles:
            x = b["x"] * w + math.sin(b["wobble"]) * 15
            y = b["y"] * h
            color = QColor.fromHsl(int(b["hue"]), 200, 160)

            # Outer glow
            glow = QRadialGradient(x, y, b["r"] + 10)
            glow.setColorAt(0, QColor(color.red(), color.green(), color.blue(), 80))
            glow.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setBrush(glow)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(x, y), b["r"] + 10, b["r"] + 10)

            # Bubble fill
            grad = QRadialGradient(x - b["r"] * 0.3, y - b["r"] * 0.3, b["r"])
            grad.setColorAt(0, QColor(255, 255, 255, 100))
            grad.setColorAt(0.5, QColor(color.red(), color.green(), color.blue(), 60))
            grad.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 100))
            painter.setBrush(grad)
            painter.drawEllipse(QPointF(x, y), b["r"], b["r"])

            # Bubble outline
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(255, 255, 255, 120), 1.5))
            painter.drawEllipse(QPointF(x, y), b["r"], b["r"])

            # Highlight
            painter.setBrush(QColor(255, 255, 255, 180))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(x - b["r"] * 0.4, y - b["r"] * 0.4),
                                b["r"] * 0.18, b["r"] * 0.12)


# ══════════════════════════════════════════════════════════════
#  Color Wash — Slowly cycling soothing colors
# ══════════════════════════════════════════════════════════════
class ColorWash(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 500)
        self._t = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self._timer.start(50)

    def _update(self):
        self._t += 0.005
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Cycling color
        hue = (self._t * 30) % 360
        color1 = QColor.fromHsl(int(hue), 180, 130)
        color2 = QColor.fromHsl(int((hue + 60) % 360), 200, 150)
        color3 = QColor.fromHsl(int((hue + 120) % 360), 170, 140)

        grad = QLinearGradient(0, 0, w, h)
        grad.setColorAt(0, color1)
        grad.setColorAt(0.5, color2)
        grad.setColorAt(1, color3)
        painter.fillRect(self.rect(), grad)

        # Gentle ripple
        painter.setPen(QPen(QColor(255, 255, 255, 30), 2))
        painter.setBrush(Qt.NoBrush)
        for i in range(5):
            r = 100 + i * 80 + math.sin(self._t * 2) * 30
            painter.drawEllipse(QPointF(w / 2, h / 2), r, r)


# ══════════════════════════════════════════════════════════════
#  Shape Morphing — repetitive calming shape
# ══════════════════════════════════════════════════════════════
class ShapeMorpher(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 500)
        self._t = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self._timer.start(20)

    def _update(self):
        self._t += 0.015
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        bg = QLinearGradient(0, 0, w, h)
        bg.setColorAt(0, QColor(15, 20, 40))
        bg.setColorAt(1, QColor(30, 15, 50))
        painter.fillRect(self.rect(), bg)

        cx, cy = w / 2, h / 2
        n_petals = 8
        base_r = min(w, h) * 0.3

        # Multiple morphing flowers
        for layer in range(3):
            offset = layer * math.pi / 3
            scale = 1.0 - layer * 0.2
            alpha = 200 - layer * 50

            path = QPainterPath()
            for i in range(360):
                angle = math.radians(i)
                petal_factor = 1 + 0.4 * math.sin(n_petals * angle + self._t + offset)
                breathing = 1 + 0.15 * math.sin(self._t * 2)
                r = base_r * scale * petal_factor * breathing

                x = cx + r * math.cos(angle)
                y = cy + r * math.sin(angle)
                if i == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
            path.closeSubpath()

            hue = (self._t * 40 + layer * 60) % 360
            c = QColor.fromHsl(int(hue), 200, 160)
            c.setAlpha(alpha)

            grad = QRadialGradient(cx, cy, base_r * scale * 1.5)
            grad.setColorAt(0, QColor(c.red(), c.green(), c.blue(), alpha))
            grad.setColorAt(1, QColor(c.red(), c.green(), c.blue(), 30))
            painter.setBrush(grad)
            painter.setPen(QPen(c.lighter(150), 1.5))
            painter.drawPath(path)


# ══════════════════════════════════════════════════════════════
#  Sensory Toolkit Screen
# ══════════════════════════════════════════════════════════════
class SensoryToolkitScreen(QWidget):
    go_back = Signal()

    EXPERIENCES = [
        ("galaxy",  "🌌", "Liquid Galaxy",   "Soothing colorful flow",     "#7B6EC4"),
        ("bubbles", "🫧", "Slow Bubbles",    "Floating bubbles",           "#5CCFCA"),
        ("wash",    "🎨", "Color Wash",      "Cycling soft colors",        "#E8956D"),
        ("morph",   "🌸", "Shape Bloom",     "Breathing flower shapes",    "#D8A0E8"),
    ]

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self.setStyleSheet(MAIN_STYLE)
        self._build_ui()

    def _build_ui(self):
        self._stack = QStackedWidget(self)
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(self._stack)

        self._stack.addWidget(self._build_lobby())

    def _build_lobby(self):
        w = QWidget()
        self._bg = ParticleBackground(w)
        layout = QVBoxLayout(w)
        layout.setContentsMargins(36, 28, 36, 28)
        layout.setSpacing(16)

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
        title = QLabel("✨ Sensory Toolkit")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {COLORS['text']};")
        sub = QLabel("Choose a calming visual experience")
        sub.setStyleSheet(f"font-size: 13px; color: {COLORS['text_light']};")

        hdr.addWidget(back_btn)
        hdr.addSpacing(20)
        col = QVBoxLayout()
        col.addWidget(title)
        col.addWidget(sub)
        hdr.addLayout(col)
        hdr.addStretch()
        layout.addLayout(hdr)

        # Experience cards
        grid = QGridLayout()
        grid.setSpacing(16)
        for i, (key, icon, name, desc, color) in enumerate(self.EXPERIENCES):
            card = self._exp_card(key, icon, name, desc, color)
            grid.addWidget(card, i // 2, i % 2)

        grid_w = QWidget()
        grid_w.setLayout(grid)
        layout.addWidget(grid_w, 1)
        return w

    def _exp_card(self, key, icon, name, desc, color):
        card = GlassCard(self, radius=24, hover_lift=True)
        card.setMinimumHeight(180)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 18)
        layout.setSpacing(8)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 48px; background: transparent;")
        title_lbl = QLabel(name)
        title_lbl.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {COLORS['text']}; background: transparent;")
        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet(f"font-size: 13px; color: {COLORS['text_light']}; background: transparent;")

        play_btn = QPushButton("▶  Start Experience")
        play_btn.setStyleSheet(f"""
            QPushButton {{
                background: {color}; color: white;
                border: none; border-radius: 12px;
                padding: 10px 20px; font-size: 12px; font-weight: 700;
            }}
            QPushButton:hover {{ background: {color}AA; }}
        """)
        play_btn.clicked.connect(lambda: self._launch(key))

        layout.addWidget(icon_lbl)
        layout.addWidget(title_lbl)
        layout.addWidget(desc_lbl)
        layout.addStretch()
        layout.addWidget(play_btn)
        return card

    def _launch(self, key):
        widgets = {
            "galaxy":  LiquidGalaxy,
            "bubbles": SlowBubbles,
            "wash":    ColorWash,
            "morph":   ShapeMorpher,
        }
        if key not in widgets:
            return

        wrapper = QWidget()
        vl = QVBoxLayout(wrapper)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(0)

        # Top bar
        top_bar = QFrame()
        top_bar.setStyleSheet("background: rgba(10,15,30,0.95);")
        top_bar.setFixedHeight(56)
        tl = QHBoxLayout(top_bar)
        tl.setContentsMargins(20, 8, 20, 8)
        back = QPushButton("← Back to Toolkit")
        back.setStyleSheet(f"""
            QPushButton {{
                background: rgba(56,184,176,0.20); color: {COLORS['teal_glow']};
                border: 1px solid rgba(56,184,176,0.4); border-radius: 10px;
                padding: 8px 18px; font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(56,184,176,0.35); }}
        """)
        back.clicked.connect(lambda: self._stack.setCurrentIndex(0))
        info = QLabel("✨ Tap anywhere — relax and enjoy")
        info.setStyleSheet("color: rgba(200,220,240,0.7); font-size: 12px;")
        tl.addWidget(back)
        tl.addStretch()
        tl.addWidget(info)

        widget = widgets[key](wrapper)
        vl.addWidget(top_bar)
        vl.addWidget(widget, 1)

        self._stack.addWidget(wrapper)
        self._stack.setCurrentWidget(wrapper)

        try:
            db.log_emotion(self._child_id, "calm", 0.85,
                           source="sensory_toolkit", action_taken=key)
        except Exception:
            pass

    def resizeEvent(self, event):
        if hasattr(self, '_bg'):
            self._bg.resize(self.size())
        super().resizeEvent(event)
