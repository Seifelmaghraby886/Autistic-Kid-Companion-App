"""Shared widgets: ARIA face, waveform, glass cards."""

import math
import random
from PySide6.QtWidgets import QWidget, QFrame, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient,
    QRadialGradient, QPainterPath, QFont,
)


# Theme tokens (dark navy + teal/cyan + soft glow)
C = {
    "bg":         "#0A1428",
    "bg2":        "#050B18",
    "panel":      "#101A33",
    "teal":       "#00BFA8",
    "cyan":       "#00E5FF",
    "purple":     "#B388FF",
    "soft":       "#5CE5DC",
    "text":       "#E8F0FA",
    "text_dim":   "#8A9CB8",
    "alert":      "#FF6B7E",
    "warn":       "#FFB73D",
    "success":    "#00D9A0",
}


# ══════════════════════════════════════════════════════════════
#  ARIA Face — friendly holographic head
# ══════════════════════════════════════════════════════════════
class ARIAFace(QWidget):
    """Soft animated robot face. Reflects emotion state."""

    EMOTIONS = {
        "happy":   {"core": "#00D9A0", "ring": "#7FFFD4"},
        "calm":    {"core": "#00BFA8", "ring": "#5CE5DC"},
        "neutral": {"core": "#00BFA8", "ring": "#5CE5DC"},
        "sad":     {"core": "#6B9FE8", "ring": "#8BB8F0"},
        "scared":  {"core": "#A695FF", "ring": "#C0B0FF"},
        "angry":   {"core": "#FF8B5C", "ring": "#FFA585"},
        "tired":   {"core": "#A8B8D0", "ring": "#C0D0E0"},
        "thinking":{"core": "#B388FF", "ring": "#C39BFF"},
        "listening":{"core":"#00E5FF","ring":"#4DECFF"},
    }

    def __init__(self, size=240, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._size = size
        self._emotion = "calm"
        self._t = 0.0
        self._blink_t = 0.0
        self._next_blink = random.uniform(3, 6)
        self._speaking = False
        self._listening = False

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)

    def set_emotion(self, emotion):
        if emotion in self.EMOTIONS:
            self._emotion = emotion
            self.update()

    def set_speaking(self, v: bool):
        self._speaking = bool(v)

    def set_listening(self, v: bool):
        self._listening = bool(v)
        if v:
            self.set_emotion("listening")

    def _tick(self):
        self._t += 0.04
        self._blink_t += 0.04
        if self._blink_t >= self._next_blink:
            self._blink_t = 0
            self._next_blink = random.uniform(3, 6)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx, cy = self._size / 2, self._size / 2
        r = self._size * 0.38

        em = self.EMOTIONS.get(self._emotion, self.EMOTIONS["calm"])
        core = QColor(em["core"])
        ring = QColor(em["ring"])

        # Pulsing halos
        pulse = (math.sin(self._t * 2) + 1) / 2
        for i, scale in enumerate([1.55, 1.35, 1.15]):
            halo = QColor(core)
            halo.setAlpha(int(30 + 40 * pulse * (1 - i * 0.2)))
            grad = QRadialGradient(cx, cy, r * scale)
            grad.setColorAt(0, QColor(halo.red(), halo.green(), halo.blue(), 0))
            grad.setColorAt(0.7, halo)
            grad.setColorAt(1, QColor(halo.red(), halo.green(), halo.blue(), 0))
            p.setBrush(grad)
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(cx, cy), r * scale, r * scale)

        # Rotating arcs when listening
        if self._listening:
            p.setPen(QPen(QColor(ring.red(), ring.green(), ring.blue(), 200), 2.5,
                          Qt.SolidLine, Qt.RoundCap))
            p.setBrush(Qt.NoBrush)
            for i in range(3):
                start = (self._t * 40 + i * 120) % 360
                p.drawArc(QRectF(cx - r * 1.08, cy - r * 1.08, r * 2.16, r * 2.16),
                          int(start * 16), int(60 * 16))

        # Head sphere
        head_grad = QRadialGradient(cx - r * 0.25, cy - r * 0.3, r * 1.6)
        head_grad.setColorAt(0, QColor(255, 255, 255, 240))
        head_grad.setColorAt(0.4, QColor(245, 252, 255, 230))
        head_grad.setColorAt(0.85, QColor(ring.red(), ring.green(), ring.blue(), 80))
        head_grad.setColorAt(1, QColor(core.red(), core.green(), core.blue(), 120))
        p.setBrush(head_grad)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(cx, cy), r, r)
        p.setPen(QPen(ring, 2))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(cx, cy), r, r)

        # Top reflection
        hl = QPainterPath()
        hl.addEllipse(QPointF(cx - r * 0.3, cy - r * 0.35), r * 0.4, r * 0.22)
        p.setBrush(QColor(255, 255, 255, 130))
        p.setPen(Qt.NoPen)
        p.drawPath(hl)

        # Eyes (with blink)
        blink = 0.05 if 0 < self._blink_t < 0.15 else 1.0
        ex_l = cx - r * 0.32
        ex_r = cx + r * 0.32
        ey = cy - r * 0.05
        ew = r * 0.22
        eh = r * 0.28 * blink

        for ex in (ex_l, ex_r):
            grad = QRadialGradient(ex, ey, ew * 1.4)
            grad.setColorAt(0, QColor(15, 25, 50, 220))
            grad.setColorAt(1, QColor(10, 20, 40, 80))
            p.setBrush(grad)
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(ex, ey), ew, eh)
            if blink > 0.3:
                # Iris glow + pupil
                p.setBrush(core)
                p.drawEllipse(QPointF(ex, ey), ew * 0.7, eh * 0.7)
                p.setBrush(QColor(15, 20, 30))
                p.drawEllipse(QPointF(ex, ey), ew * 0.32, eh * 0.32)
                p.setBrush(QColor(255, 255, 255, 220))
                p.drawEllipse(QPointF(ex - ew * 0.25, ey - eh * 0.3),
                              ew * 0.18, eh * 0.16)

        # Mouth
        my = cy + r * 0.4
        mw = r * 0.28
        if self._speaking:
            mh = r * 0.08 * (1.0 + 0.3 * math.sin(self._t * 7))
            mh = max(mh, r * 0.02)
            path = QPainterPath()
            path.addRoundedRect(QRectF(cx - mw, my - mh / 2, mw * 2, mh),
                                mh / 2, mh / 2)
            p.setBrush(core); p.setPen(QPen(core.darker(120), 1))
            p.drawPath(path)
        elif self._emotion in ("happy",):
            path = QPainterPath()
            path.moveTo(cx - mw, my)
            path.quadTo(cx, my + r * 0.18, cx + mw, my)
            p.setPen(QPen(core.darker(140), 3.5, Qt.SolidLine, Qt.RoundCap))
            p.setBrush(Qt.NoBrush)
            p.drawPath(path)
        elif self._emotion in ("sad",):
            path = QPainterPath()
            path.moveTo(cx - mw, my + r * 0.05)
            path.quadTo(cx, my - r * 0.05, cx + mw, my + r * 0.05)
            p.setPen(QPen(core.darker(140), 3, Qt.SolidLine, Qt.RoundCap))
            p.setBrush(Qt.NoBrush)
            p.drawPath(path)
        else:
            p.setPen(QPen(core.darker(130), 2.8, Qt.SolidLine, Qt.RoundCap))
            path = QPainterPath()
            path.moveTo(cx - mw * 0.7, my)
            path.quadTo(cx, my + r * 0.06, cx + mw * 0.7, my)
            p.setBrush(Qt.NoBrush)
            p.drawPath(path)


# ══════════════════════════════════════════════════════════════
#  Listening waveform
# ══════════════════════════════════════════════════════════════
class WaveformBar(QWidget):
    """Animated audio bars. Pulses faster when listening."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(70)
        self._t = 0.0
        self._active = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)

    def set_active(self, on: bool):
        self._active = bool(on)

    def _tick(self):
        if self._active:
            self._t += 0.08
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cy = h / 2
        bars = 40
        bw = (w - 20) / bars
        for i in range(bars):
            phase = self._t + i * 0.25
            if self._active:
                amp = abs(math.sin(phase) + math.sin(phase * 1.6)) / 2
                bh = 6 + amp * (h * 0.65)
            else:
                bh = 4
            x = 10 + i * bw
            grad = QLinearGradient(0, cy - bh / 2, 0, cy + bh / 2)
            grad.setColorAt(0, QColor(C["soft"]))
            grad.setColorAt(0.5, QColor(C["teal"]))
            grad.setColorAt(1, QColor(C["cyan"]))
            p.setBrush(grad)
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(int(x), int(cy - bh / 2), int(bw - 2), int(bh), 2, 2)


# ══════════════════════════════════════════════════════════════
#  Glass card
# ══════════════════════════════════════════════════════════════
class GlassCard(QFrame):
    def __init__(self, parent=None, radius=18, dark=True):
        super().__init__(parent)
        self._radius = radius
        self._dark = dark
        self.setStyleSheet("background: transparent;")
        try:
            eff = QGraphicsDropShadowEffect(self)
            eff.setBlurRadius(28)
            eff.setOffset(0, 6)
            eff.setColor(QColor(0, 191, 168, 60))
            self.setGraphicsEffect(eff)
        except Exception:
            pass

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(0, 0, rect.width(), rect.height(),
                            self._radius, self._radius)
        if self._dark:
            grad = QLinearGradient(0, 0, 0, rect.height())
            grad.setColorAt(0, QColor(22, 32, 58, 240))
            grad.setColorAt(1, QColor(15, 22, 42, 240))
            p.fillPath(path, grad)
            p.setPen(QPen(QColor(0, 229, 255, 80), 1.2))
        else:
            p.fillPath(path, QColor(255, 255, 255, 220))
            p.setPen(QPen(QColor(0, 191, 168, 80), 1.2))
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)


# ══════════════════════════════════════════════════════════════
#  Main stylesheet
# ══════════════════════════════════════════════════════════════
MAIN_STYLE = f"""
QWidget {{
    background: {C['bg']};
    color: {C['text']};
    font-family: 'Segoe UI', 'Inter', sans-serif;
}}
QPushButton {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {C['teal']}, stop:0.5 {C['cyan']}, stop:1 {C['purple']});
    color: white; border: none; border-radius: 14px;
    padding: 12px 24px; font-size: 14px; font-weight: 700;
}}
QPushButton:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {C['soft']}, stop:1 {C['cyan']});
}}
QPushButton:disabled {{
    background: #2A3A55; color: #6B7A95;
}}
QLineEdit, QTextEdit {{
    background: rgba(255,255,255,0.08);
    border: 1.5px solid rgba(0,191,168,0.4);
    border-radius: 12px;
    padding: 10px 14px;
    color: {C['text']};
    font-size: 14px;
}}
QLineEdit:focus, QTextEdit:focus {{
    border-color: {C['cyan']};
}}
QComboBox {{
    background: rgba(255,255,255,0.08);
    border: 1.5px solid rgba(0,191,168,0.4);
    border-radius: 10px;
    padding: 8px 12px;
    color: {C['text']};
}}
QLabel {{ background: transparent; }}
QScrollBar:vertical {{ background: rgba(0,191,168,0.05); width: 8px; }}
QScrollBar::handle:vertical {{ background: rgba(0,191,168,0.5); border-radius: 4px; }}
"""
