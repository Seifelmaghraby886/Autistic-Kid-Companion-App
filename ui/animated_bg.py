"""
ARIA Animated Mesh Background
Stunning futuristic flowing gradient mesh for backgrounds.
"""

import math
import random
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import QPainter, QColor, QRadialGradient, QLinearGradient, QPen


class MeshBackground(QWidget):
    """Flowing colored blobs forming a soft mesh — feels like a futuristic OS."""

    def __init__(self, parent=None, intensity=0.7):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._t = 0.0
        self._intensity = intensity
        self._blobs = []
        for _ in range(6):
            self._blobs.append({
                "x": random.uniform(0.0, 1.0),
                "y": random.uniform(0.0, 1.0),
                "vx": random.uniform(-0.0006, 0.0006),
                "vy": random.uniform(-0.0006, 0.0006),
                "r": random.uniform(0.35, 0.55),
                "color": random.choice([
                    QColor(0, 191, 168),     # teal
                    QColor(0, 229, 255),     # neon cyan
                    QColor(179, 136, 255),   # neon purple
                    QColor(92, 229, 220),    # teal-glow
                    QColor(127, 255, 212),   # mint
                    QColor(216, 200, 255),   # lavender
                ])
            })
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        # Sensory accommodation: motion-sensitive children get one static
        # frame instead of a moving background.
        from ui.styles import reduce_motion
        if not reduce_motion():
            self._timer.start(50)

        # Grid stars
        self._stars = []
        for _ in range(25):
            self._stars.append({
                "x": random.uniform(0, 1),
                "y": random.uniform(0, 1),
                "size": random.uniform(1, 3),
                "twinkle": random.uniform(0, math.pi * 2),
            })

    def _update(self):
        self._t += 0.012
        for b in self._blobs:
            b["x"] += b["vx"]
            b["y"] += b["vy"]
            if b["x"] < 0.0 or b["x"] > 1.0: b["vx"] *= -1
            if b["y"] < 0.0 or b["y"] > 1.0: b["vy"] *= -1
        for s in self._stars:
            s["twinkle"] += 0.04
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return

        # Base gradient
        bg = QLinearGradient(0, 0, w, h)
        bg.setColorAt(0, QColor(225, 235, 250))
        bg.setColorAt(0.4, QColor(235, 240, 255))
        bg.setColorAt(0.8, QColor(230, 245, 250))
        bg.setColorAt(1, QColor(240, 235, 255))
        painter.fillRect(self.rect(), bg)

        # Grid pattern
        painter.setPen(QPen(QColor(0, 191, 168, 8), 1))
        spacing = 80
        for x in range(0, w, spacing):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, spacing):
            painter.drawLine(0, y, w, y)

        # Mesh blobs
        for b in self._blobs:
            cx = b["x"] * w + math.sin(self._t * 2 + b["x"] * 5) * 30
            cy = b["y"] * h + math.cos(self._t + b["y"] * 4) * 20
            r = b["r"] * min(w, h)
            c = QColor(b["color"])
            grad = QRadialGradient(cx, cy, r)
            c1 = QColor(c)
            c1.setAlphaF(0.30 * self._intensity)
            c2 = QColor(c)
            c2.setAlphaF(0.0)
            grad.setColorAt(0, c1)
            grad.setColorAt(1, c2)
            painter.setBrush(grad)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(cx, cy), r, r)

        # Twinkling stars
        for s in self._stars:
            twinkle = (math.sin(s["twinkle"]) + 1) / 2
            alpha = int(30 + twinkle * 80)
            x, y = s["x"] * w, s["y"] * h
            c = QColor(0, 229, 255, alpha)
            painter.setBrush(c)
            painter.setPen(Qt.NoPen)
            r = s["size"] * (0.7 + twinkle * 0.5)
            painter.drawEllipse(QPointF(x, y), r, r)
            # Cross sparkle
            painter.setPen(QPen(c, 0.5))
            painter.drawLine(QPointF(x - r * 2, y), QPointF(x + r * 2, y))
            painter.drawLine(QPointF(x, y - r * 2), QPointF(x, y + r * 2))
