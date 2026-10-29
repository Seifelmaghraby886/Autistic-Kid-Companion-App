"""
ARIA Splash Screen
Futuristic animated intro with logo, particles, and loading sequence.
"""

import math
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PySide6.QtCore import Qt, QTimer, Signal, QPointF, QRectF
from PySide6.QtGui import (
    QPainter, QColor, QFont, QLinearGradient, QRadialGradient,
    QPen, QPainterPath, QBrush
)


class SplashScreen(QWidget):
    finished = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(700, 500)
        self._center_on_screen()

        # Animation state
        self._alpha = 0.0
        self._ring_scale = 0.4
        self._text_alpha = 0
        self._particle_t = 0.0
        self._progress = 0.0
        self._loading_text = "Initializing ARIA..."
        self._step = 0
        self._particles = self._init_particles()
        self._orbit_t = 0.0

        self._loading_steps = [
            (0.15, "Loading neural networks..."),
            (0.30, "Connecting emotion engine..."),
            (0.50, "Loading voice system..."),
            (0.65, "Building child profiles..."),
            (0.80, "Preparing AI companion..."),
            (0.95, "Starting ARIA..."),
            (1.00, "Welcome."),
        ]

        # Main animation timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(16)

        # Progress sequence
        self._prog_timer = QTimer(self)
        self._prog_timer.timeout.connect(self._advance_loading)
        self._prog_timer.start(600)

    def _center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def _init_particles(self):
        import random
        pts = []
        for _ in range(40):
            pts.append({
                "angle": random.uniform(0, math.pi * 2),
                "radius": random.uniform(120, 280),
                "speed": random.uniform(0.005, 0.018),
                "size": random.uniform(2, 5),
                "alpha": random.randint(30, 100),
            })
        return pts

    def _animate(self):
        # Fade in
        if self._alpha < 1.0:
            self._alpha = min(1.0, self._alpha + 0.025)

        # Ring scale
        if self._ring_scale < 1.0:
            self._ring_scale = min(1.0, self._ring_scale + 0.015)

        # Text fade in
        if self._ring_scale > 0.6 and self._text_alpha < 255:
            self._text_alpha = min(255, self._text_alpha + 8)

        # Particles
        self._particle_t += 0.015
        for p in self._particles:
            p["angle"] += p["speed"]

        self._orbit_t += 0.02
        self.setWindowOpacity(self._alpha)
        self.update()

    def _advance_loading(self):
        if self._step < len(self._loading_steps):
            target, text = self._loading_steps[self._step]
            self._progress = target
            self._loading_text = text
            self._step += 1
            self.update()
        else:
            self._prog_timer.stop()
            QTimer.singleShot(800, self._finish)

    def _finish(self):
        # Fade out
        self._fade_out_steps = 20
        self._fade_timer = QTimer(self)
        self._fade_timer.timeout.connect(self._do_fade_out)
        self._fade_timer.start(20)

    def _do_fade_out(self):
        self._fade_out_steps -= 1
        self.setWindowOpacity(self._fade_out_steps / 20)
        if self._fade_out_steps <= 0:
            self._fade_timer.stop()
            self.finished.emit()
            self.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2

        # ── Background gradient
        bg = QLinearGradient(0, 0, w, h)
        bg.setColorAt(0, QColor(15, 25, 40))
        bg.setColorAt(0.5, QColor(20, 32, 52))
        bg.setColorAt(1, QColor(10, 20, 35))
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, 28, 28)
        painter.fillPath(path, bg)

        # ── Orbiting particles
        for p in self._particles:
            x = cx + math.cos(p["angle"]) * p["radius"] * self._ring_scale
            y = cy + math.sin(p["angle"] * 0.7) * p["radius"] * 0.5 * self._ring_scale
            alpha = int(p["alpha"] * self._ring_scale)
            c = QColor(56, 184, 176, alpha)
            painter.setBrush(c)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(x, y), p["size"], p["size"])

        # ── Outer rings
        for i, (r, a) in enumerate([(180, 30), (140, 50), (105, 80)]):
            ring_r = r * self._ring_scale
            ring_c = QColor(56, 184, 176, a)
            pen = QPen(ring_c, 1.5 if i < 2 else 2.5)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), ring_r, ring_r)

        # ── Rotating arc (orbit indicator)
        arc_pen = QPen(QColor(92, 207, 202, 160), 3)
        arc_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(arc_pen)
        painter.setBrush(Qt.NoBrush)
        arc_r = 120 * self._ring_scale
        arc_rect = QRectF(cx - arc_r, cy - arc_r, arc_r * 2, arc_r * 2)
        start_angle = int(self._orbit_t * (180 / math.pi) * 16)
        painter.drawArc(arc_rect, start_angle, 120 * 16)

        # ── Center glow
        glow = QRadialGradient(cx, cy, 80)
        glow.setColorAt(0, QColor(56, 184, 176, 60))
        glow.setColorAt(0.5, QColor(42, 127, 168, 30))
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), 80, 80)

        # ── ARIA Logo text
        if self._text_alpha > 0:
            # A R I A
            font = QFont("Segoe UI", 58, QFont.Black)
            font.setLetterSpacing(QFont.AbsoluteSpacing, 18)
            painter.setFont(font)

            grad_text = QLinearGradient(cx - 120, 0, cx + 120, 0)
            grad_text.setColorAt(0, QColor(92, 207, 202, self._text_alpha))
            grad_text.setColorAt(0.5, QColor(255, 255, 255, self._text_alpha))
            grad_text.setColorAt(1, QColor(56, 184, 176, self._text_alpha))
            painter.setPen(QPen(QColor(255, 255, 255, self._text_alpha)))
            painter.drawText(QRectF(0, cy - 90, w, 80),
                             Qt.AlignCenter, "ARIA")

            # Subtitle
            sub_font = QFont("Segoe UI", 10, QFont.Normal)
            sub_font.setLetterSpacing(QFont.AbsoluteSpacing, 4)
            painter.setFont(sub_font)
            painter.setPen(QColor(150, 200, 220, self._text_alpha))
            painter.drawText(QRectF(0, cy - 12, w, 30),
                             Qt.AlignCenter,
                             "ADAPTIVE ROBOTIC INTERACTION ASSISTANT")

            # Tagline
            tag_font = QFont("Segoe UI", 9)
            painter.setFont(tag_font)
            painter.setPen(QColor(100, 160, 180, int(self._text_alpha * 0.7)))
            painter.drawText(QRectF(0, cy + 16, w, 25),
                             Qt.AlignCenter,
                             "A 24/7 AI Companion Platform for Autistic Children")

        # ── Progress bar
        bar_y = h - 65
        bar_w = w - 120
        bar_x = 60
        bar_h = 4

        # Track
        painter.setBrush(QColor(255, 255, 255, 20))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(bar_x, bar_y, bar_w, bar_h, 2, 2)

        # Fill
        fill_w = int(bar_w * self._progress)
        if fill_w > 0:
            prog_grad = QLinearGradient(bar_x, 0, bar_x + fill_w, 0)
            prog_grad.setColorAt(0, QColor(56, 184, 176))
            prog_grad.setColorAt(0.5, QColor(92, 207, 202))
            prog_grad.setColorAt(1, QColor(56, 184, 176))
            painter.setBrush(prog_grad)
            painter.drawRoundedRect(bar_x, bar_y, fill_w, bar_h, 2, 2)

            # Glow on tip
            glow_tip = QRadialGradient(bar_x + fill_w, bar_y + bar_h / 2, 12)
            glow_tip.setColorAt(0, QColor(92, 207, 202, 180))
            glow_tip.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setBrush(glow_tip)
            painter.drawEllipse(QPointF(bar_x + fill_w, bar_y + bar_h / 2), 12, 12)

        # Loading text
        font = QFont("Segoe UI", 9)
        painter.setFont(font)
        painter.setPen(QColor(100, 160, 180, int(self._text_alpha * 0.8)))
        painter.drawText(QRectF(0, bar_y + 12, w, 20),
                         Qt.AlignCenter, self._loading_text)

        # Version
        ver_font = QFont("Segoe UI", 8)
        painter.setFont(ver_font)
        painter.setPen(QColor(60, 80, 100, 120))
        painter.drawText(QRectF(w - 80, h - 22, 70, 18),
                         Qt.AlignRight, "v1.0.0")
