"""
ARIA Reusable UI Components
Custom widgets with animations, glassmorphism, and autism-friendly design.
"""

import math
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout,
    QFrame, QGraphicsDropShadowEffect, QSizePolicy, QProgressBar
)
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    Property, Signal, QRect, QPointF, QSize, QThread
)
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient,
    QRadialGradient, QFont, QPainterPath, QPixmap
)
from ui.styles import COLORS, get_emotion_color


# ══════════════════════════════════════════════════════════════
#  Glass Card
# ══════════════════════════════════════════════════════════════
class GlassCard(QFrame):
    def __init__(self, parent=None, dark=False, radius=20, hover_lift=True):
        super().__init__(parent)
        self._dark = dark
        self._radius = radius
        self._hover_lift = hover_lift
        self._hover = False
        self._opacity = 0.80
        self.setMouseTracking(True)
        self._setup_shadow()

    def _setup_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(56, 184, 176, 40))
        self.setGraphicsEffect(shadow)

    def enterEvent(self, event):
        if self._hover_lift:
            self._hover = True
            self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()

        if self._dark:
            # Dark glass — fully opaque navy
            base_grad = QLinearGradient(0, 0, 0, rect.height())
            base_grad.setColorAt(0, QColor(22, 32, 58, 255))
            base_grad.setColorAt(1, QColor(15, 22, 42, 255))
            base_fill = base_grad
        else:
            base_fill = QColor(255, 255, 255, 230 if self._hover else 215)

        path = QPainterPath()
        path.addRoundedRect(rect.x(), rect.y(),
                            rect.width(), rect.height(),
                            self._radius, self._radius)

        painter.fillPath(path, base_fill)

        # Shine band
        if not self._dark:
            shine = QLinearGradient(0, 0, 0, rect.height() * 0.5)
            shine.setColorAt(0, QColor(255, 255, 255, 80 if self._hover else 55))
            shine.setColorAt(0.5, QColor(0, 229, 255, 12))
            shine.setColorAt(1, QColor(255, 255, 255, 0))
            painter.fillPath(path, shine)
        else:
            # Subtle inner glow on dark
            shine = QLinearGradient(0, 0, 0, rect.height() * 0.4)
            shine.setColorAt(0, QColor(0, 229, 255, 25))
            shine.setColorAt(1, QColor(0, 0, 0, 0))
            painter.fillPath(path, shine)

        # Border
        if self._hover and self._hover_lift:
            grad = QLinearGradient(0, 0, rect.width(), rect.height())
            grad.setColorAt(0, QColor(0, 191, 168, 220))
            grad.setColorAt(0.5, QColor(0, 229, 255, 220))
            grad.setColorAt(1, QColor(179, 136, 255, 220))
            from PySide6.QtGui import QBrush
            pen = QPen(QBrush(grad), 2)
            painter.setPen(pen)
            painter.drawPath(path)
        else:
            if self._dark:
                border_color = QColor(0, 229, 255, 70)
            else:
                border_color = QColor(0, 191, 168, 70)
            pen = QPen(border_color, 1.5)
            painter.setPen(pen)
            painter.drawPath(path)


# ══════════════════════════════════════════════════════════════
#  Animated ARIA Face — use v2 (holographic robot head)
# ══════════════════════════════════════════════════════════════
from ui.aria_face_v2 import ARIAFaceV2 as ARIAFaceWidget  # noqa: F401


class _LegacyARIAFaceWidget(QWidget):
    """Old cartoon face — kept as fallback for any direct imports."""

    EXPRESSIONS = {
        "happy":     {"eye": "happy",   "mouth": "smile",    "color": "#4CAF90"},
        "calm":      {"eye": "normal",  "mouth": "neutral",  "color": "#38B8B0"},
        "neutral":   {"eye": "normal",  "mouth": "neutral",  "color": "#38B8B0"},
        "thinking":  {"eye": "squint",  "mouth": "small",    "color": "#7BB8C8"},
        "sad":       {"eye": "sad",     "mouth": "frown",    "color": "#6B9FD4"},
        "sadness":   {"eye": "sad",     "mouth": "frown",    "color": "#6B9FD4"},
        "surprised": {"eye": "wide",    "mouth": "open",     "color": "#F0C040"},
        "surprise":  {"eye": "wide",    "mouth": "open",     "color": "#F0C040"},
        "scared":    {"eye": "wide",    "mouth": "small",    "color": "#9B8EC4"},
        "fear":      {"eye": "wide",    "mouth": "small",    "color": "#9B8EC4"},
        "upset":     {"eye": "angry",   "mouth": "frown",    "color": "#E8956D"},
        "anger":     {"eye": "angry",   "mouth": "frown",    "color": "#E8956D"},
        "listening": {"eye": "curious", "mouth": "neutral",  "color": "#5CCFCA"},
        "sleepy":    {"eye": "sleepy",  "mouth": "small",    "color": "#A8B8D0"},
        "comfort":   {"eye": "kind",    "mouth": "soft",     "color": "#D8C8FF"},
    }

    def __init__(self, parent=None, size=200):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self._expression = "calm"
        self._target_expression = "calm"
        self._blink_state = 1.0      # 1.0 = open, 0.0 = closed
        self._breathe_scale = 1.0
        self._glow_alpha = 80
        self._transition_progress = 1.0

        # Blink timer
        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._do_blink)
        self._blink_timer.start(4000)

        # Breathe timer
        self._breathe_timer = QTimer(self)
        self._breathe_timer.timeout.connect(self._do_breathe)
        self._breathe_timer.start(30)
        self._breathe_t = 0.0

        # Glow pulse
        self._glow_timer = QTimer(self)
        self._glow_timer.timeout.connect(self._pulse_glow)
        self._glow_timer.start(30)
        self._glow_t = 0.0

        # Transition
        self._trans_timer = QTimer(self)
        self._trans_timer.timeout.connect(self._update_transition)

    def set_expression(self, expr: str, animate=True):
        if expr not in self.EXPRESSIONS:
            expr = "calm"
        if expr == self._expression:
            return
        self._target_expression = expr
        if animate:
            self._transition_progress = 0.0
            self._trans_timer.start(16)
        else:
            self._expression = expr
            self._transition_progress = 1.0
            self.update()

    def _update_transition(self):
        self._transition_progress = min(1.0, self._transition_progress + 0.06)
        if self._transition_progress >= 1.0:
            self._expression = self._target_expression
            self._trans_timer.stop()
        self.update()

    def _do_blink(self):
        steps = [1.0, 0.6, 0.2, 0.0, 0.2, 0.6, 1.0]
        self._blink_steps = iter(steps)
        self._blink_step_timer = QTimer(self)
        self._blink_step_timer.timeout.connect(self._blink_step)
        self._blink_step_timer.start(35)

    def _blink_step(self):
        try:
            self._blink_state = next(self._blink_steps)
            self.update()
        except StopIteration:
            self._blink_step_timer.stop()
            self._blink_state = 1.0
            self.update()

    def _do_breathe(self):
        self._breathe_t += 0.02
        self._breathe_scale = 1.0 + 0.012 * math.sin(self._breathe_t)
        self.update()

    def _pulse_glow(self):
        self._glow_t += 0.04
        self._glow_alpha = int(60 + 40 * math.sin(self._glow_t))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        cx, cy = self._size / 2, self._size / 2
        r = self._size / 2 - 10

        expr_data = self.EXPRESSIONS.get(self._expression, self.EXPRESSIONS["calm"])
        accent = QColor(expr_data["color"])

        # ── Outer glow ring
        glow_color = QColor(accent)
        glow_color.setAlpha(self._glow_alpha)
        glow_pen = QPen(glow_color, 3)
        painter.setPen(glow_pen)
        painter.setBrush(Qt.NoBrush)
        glow_r = r * self._breathe_scale
        painter.drawEllipse(QPointF(cx, cy), glow_r + 6, glow_r + 6)

        # Second glow ring
        glow_color2 = QColor(accent)
        glow_color2.setAlpha(self._glow_alpha // 3)
        painter.setPen(QPen(glow_color2, 6))
        painter.drawEllipse(QPointF(cx, cy), glow_r + 14, glow_r + 14)

        # ── Face circle with gradient
        face_grad = QRadialGradient(cx - r * 0.2, cy - r * 0.2, r * 1.4)
        face_grad.setColorAt(0, QColor("#FFFFFF"))
        face_grad.setColorAt(0.5, QColor("#F0F8FF"))
        face_grad.setColorAt(1, QColor(accent).lighter(180))
        painter.setPen(Qt.NoPen)
        painter.setBrush(face_grad)
        painter.drawEllipse(QPointF(cx, cy), r, r)

        # Face border
        painter.setPen(QPen(QColor(accent).lighter(130), 2.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), r, r)

        # ── Eyes
        self._draw_eyes(painter, cx, cy, r, expr_data["eye"], accent)

        # ── Mouth
        self._draw_mouth(painter, cx, cy, r, expr_data["mouth"], accent)

        # ── Cheek blushes (for happy)
        if self._expression in ("happy", "joy"):
            blush = QColor(255, 150, 150, 50)
            painter.setBrush(blush)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(cx - r * 0.45, cy + r * 0.18), r * 0.18, r * 0.10)
            painter.drawEllipse(QPointF(cx + r * 0.45, cy + r * 0.18), r * 0.18, r * 0.10)

    def _draw_eyes(self, painter, cx, cy, r, style, accent):
        ey = cy - r * 0.10
        el = cx - r * 0.32
        er = cx + r * 0.32
        ew = r * 0.22
        eh = r * 0.28

        for ex in [el, er]:
            eye_h = eh * self._blink_state

            if style == "happy":
                # Happy arc eyes
                path = QPainterPath()
                path.moveTo(ex - ew, ey)
                path.quadTo(ex, ey - eye_h * 1.2, ex + ew, ey)
                painter.setPen(QPen(accent.darker(130), 3, Qt.SolidLine, Qt.RoundCap))
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(path)

            elif style == "wide" or style == "curious":
                # Wide surprised eyes
                iris_color = QColor(accent)
                painter.setPen(Qt.NoPen)
                painter.setBrush(iris_color.darker(110))
                painter.drawEllipse(QPointF(ex, ey), ew * 1.2, eye_h * 1.2)
                painter.setBrush(QColor(255, 255, 255))
                painter.drawEllipse(QPointF(ex + ew * 0.3, ey - eye_h * 0.25), ew * 0.3, eye_h * 0.3)

            elif style == "sad":
                # Droopy eyes
                painter.setPen(QPen(accent.darker(130), 3, Qt.SolidLine, Qt.RoundCap))
                painter.setBrush(Qt.NoBrush)
                path = QPainterPath()
                path.moveTo(ex - ew, ey - eye_h * 0.3)
                path.quadTo(ex, ey + eye_h * 0.5, ex + ew, ey - eye_h * 0.3)
                painter.drawPath(path)

            elif style == "angry":
                # Angry brow + eye
                painter.setPen(QPen(accent.darker(140), 3.5, Qt.SolidLine, Qt.RoundCap))
                brow_slant = -r * 0.08 if ex < cx else r * 0.08
                painter.drawLine(
                    QPointF(ex - ew, ey - eye_h - r * 0.12 + brow_slant),
                    QPointF(ex + ew, ey - eye_h - r * 0.12 - brow_slant)
                )
                iris_color = QColor(accent)
                painter.setBrush(iris_color.darker(110))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(ex, ey), ew, eye_h)

            elif style == "sleepy":
                # Half-closed eyes
                path = QPainterPath()
                path.moveTo(ex - ew, ey)
                path.quadTo(ex, ey + eye_h * 0.5 * self._blink_state, ex + ew, ey)
                painter.setPen(QPen(accent.darker(130), 3))
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(path)

            elif style == "kind":
                # Soft curved kind eyes
                path = QPainterPath()
                path.moveTo(ex - ew, ey)
                path.quadTo(ex, ey - eye_h * 0.9 * self._blink_state, ex + ew, ey)
                painter.setPen(QPen(accent.darker(130), 3))
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(path)

            else:
                # Normal iris eyes
                iris_color = QColor(accent)
                pupil_color = accent.darker(180)
                painter.setPen(Qt.NoPen)
                painter.setBrush(iris_color)
                painter.drawEllipse(QPointF(ex, ey), ew, eye_h * self._blink_state)
                painter.setBrush(pupil_color)
                painter.drawEllipse(QPointF(ex, ey),
                                    ew * 0.5, eye_h * 0.55 * self._blink_state)
                painter.setBrush(QColor(255, 255, 255))
                painter.drawEllipse(QPointF(ex + ew * 0.25, ey - eye_h * 0.2),
                                    ew * 0.22, eye_h * 0.22 * self._blink_state)

    def _draw_mouth(self, painter, cx, cy, r, style, accent):
        my = cy + r * 0.30
        mw = r * 0.35

        painter.setPen(QPen(accent.darker(140), 2.5, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(Qt.NoBrush)

        if style == "smile":
            path = QPainterPath()
            path.moveTo(cx - mw, my - r * 0.04)
            path.quadTo(cx, my + r * 0.20, cx + mw, my - r * 0.04)
            painter.drawPath(path)
            # Dimples
            painter.setPen(QPen(accent.darker(120), 1.5))
            painter.drawPoint(QPointF(cx - mw - 2, my - r * 0.04))
            painter.drawPoint(QPointF(cx + mw + 2, my - r * 0.04))

        elif style == "frown":
            path = QPainterPath()
            path.moveTo(cx - mw, my + r * 0.10)
            path.quadTo(cx, my - r * 0.14, cx + mw, my + r * 0.10)
            painter.drawPath(path)

        elif style == "open":
            painter.setBrush(accent.darker(160))
            painter.drawEllipse(QPointF(cx, my + r * 0.04), mw * 0.6, r * 0.14)

        elif style == "soft":
            path = QPainterPath()
            path.moveTo(cx - mw * 0.7, my)
            path.quadTo(cx, my + r * 0.10, cx + mw * 0.7, my)
            painter.drawPath(path)

        else:
            # neutral small line
            painter.drawLine(QPointF(cx - mw * 0.5, my),
                             QPointF(cx + mw * 0.5, my))


# ══════════════════════════════════════════════════════════════
#  Breathing Circle for Calm Zone
# ══════════════════════════════════════════════════════════════
class BreathingCircle(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(260, 260)
        self._phase = "inhale"
        self._radius = 60.0
        self._min_r = 60.0
        self._max_r = 110.0
        self._alpha = 80
        self._t = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self._timer.start(30)
        self._cycle = 0.0
        self._cycle_speed = 0.015
        self._label_text = "Breathe In..."

    def set_speed(self, speed):
        self._cycle_speed = speed

    def _update(self):
        self._cycle += self._cycle_speed
        if self._cycle > math.pi * 2:
            self._cycle -= math.pi * 2

        # Sine wave 0→1→0
        s = (math.sin(self._cycle - math.pi / 2) + 1) / 2
        self._radius = self._min_r + s * (self._max_r - self._min_r)
        self._alpha = int(40 + s * 120)
        self._t += 0.05

        if self._cycle < math.pi:
            self._label_text = "Breathe In..."
            self._phase = "inhale"
        else:
            self._label_text = "Breathe Out..."
            self._phase = "exhale"

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        cx = self.width() / 2
        cy = self.height() / 2

        # Outer glow rings
        for i in range(4, 0, -1):
            ring_r = self._radius + i * 18
            ring_a = max(0, self._alpha - i * 20)
            c = QColor(56, 184, 176, ring_a)
            painter.setPen(Qt.NoPen)
            painter.setBrush(c)
            painter.drawEllipse(QPointF(cx, cy), ring_r, ring_r)

        # Main circle
        grad = QRadialGradient(cx, cy, self._radius)
        grad.setColorAt(0, QColor(56, 184, 176, self._alpha + 60))
        grad.setColorAt(0.6, QColor(42, 127, 168, self._alpha))
        grad.setColorAt(1, QColor(216, 200, 255, self._alpha // 2))
        painter.setBrush(grad)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), self._radius, self._radius)

        # White center dot
        painter.setBrush(QColor(255, 255, 255, 180))
        painter.drawEllipse(QPointF(cx, cy), 8, 8)

        # Label
        font = QFont("Segoe UI", 14, QFont.DemiBold)
        painter.setFont(font)
        painter.setPen(QColor(42, 127, 168, 200))
        painter.drawText(self.rect().adjusted(0, 0, 0, -20),
                         Qt.AlignBottom | Qt.AlignHCenter,
                         self._label_text)


# ══════════════════════════════════════════════════════════════
#  Status Indicator Dot
# ══════════════════════════════════════════════════════════════
class StatusDot(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(12, 12)
        self._color = QColor(COLORS["teal"])
        self._pulse = 1.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._do_pulse)
        self._timer.start(40)
        self._t = 0.0

    def set_status(self, ok: bool):
        self._color = QColor(COLORS["teal"] if ok else COLORS["danger"])
        self.update()

    def _do_pulse(self):
        self._t += 0.08
        self._pulse = 0.7 + 0.3 * math.sin(self._t)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        c = QColor(self._color)
        c.setAlpha(int(255 * self._pulse))
        painter.setBrush(c)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(1, 1, 10, 10)


# ══════════════════════════════════════════════════════════════
#  Emotion Bar (confidence visualization)
# ══════════════════════════════════════════════════════════════
class EmotionBar(QWidget):
    def __init__(self, emotion: str, parent=None):
        super().__init__(parent)
        self._emotion = emotion
        self._value = 0.0
        self._target = 0.0
        self._color = QColor(get_emotion_color(emotion))
        self.setFixedHeight(28)
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._animate)
        self._anim_timer.start(16)

    def set_value(self, v: float):
        self._target = max(0.0, min(1.0, v))
        self._anim_timer.start(16)

    def _animate(self):
        diff = self._target - self._value
        if abs(diff) < 0.002:
            self._value = self._target
            self._anim_timer.stop()
        else:
            self._value += diff * 0.12
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        bar_h = 10
        bar_y = (h - bar_h) // 2

        # Background track
        track_color = QColor(self._color)
        track_color.setAlpha(30)
        painter.setBrush(track_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(80, bar_y, w - 140, bar_h, 5, 5)

        # Fill
        fill_w = int((w - 140) * self._value)
        if fill_w > 0:
            grad = QLinearGradient(80, 0, 80 + fill_w, 0)
            grad.setColorAt(0, self._color.lighter(120))
            grad.setColorAt(1, self._color)
            painter.setBrush(grad)
            painter.drawRoundedRect(80, bar_y, fill_w, bar_h, 5, 5)

        # Emotion label
        painter.setPen(QColor(COLORS["text"]))
        painter.setFont(QFont("Segoe UI", 10, QFont.Medium))
        painter.drawText(0, 0, 78, h, Qt.AlignVCenter | Qt.AlignRight,
                         self._emotion.title())

        # Percentage
        painter.setPen(self._color)
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(w - 52, 0, 52, h, Qt.AlignVCenter | Qt.AlignHCenter,
                         f"{int(self._value * 100)}%")


# ══════════════════════════════════════════════════════════════
#  Notification Toast
# ══════════════════════════════════════════════════════════════
class ToastNotification(QWidget):
    def __init__(self, parent, message, kind="info", duration=3000):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.ToolTip)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._kind = kind
        self._message = message
        self._opacity = 0.0

        color_map = {
            "info":    COLORS["teal"],
            "success": COLORS["success"],
            "warning": COLORS["warning"],
            "error":   COLORS["danger"],
        }
        self._color = QColor(color_map.get(kind, COLORS["teal"]))

        lbl = QLabel(message, self)
        lbl.setStyleSheet(
            f"color: white; font-size: 13px; font-weight: 600; padding: 12px 20px;"
        )
        lbl.adjustSize()
        self.resize(lbl.width() + 40, 50)

        # Fade in
        self._fade_timer = QTimer(self)
        self._fade_timer.timeout.connect(self._fade_in)
        self._fade_timer.start(16)

        QTimer.singleShot(duration, self._start_fade_out)

    def _fade_in(self):
        self._opacity = min(1.0, self._opacity + 0.07)
        self.setWindowOpacity(self._opacity)
        if self._opacity >= 1.0:
            self._fade_timer.stop()

    def _start_fade_out(self):
        self._fade_timer.timeout.disconnect()
        self._fade_timer.timeout.connect(self._fade_out)
        self._fade_timer.start(16)

    def _fade_out(self):
        self._opacity = max(0.0, self._opacity - 0.05)
        self.setWindowOpacity(self._opacity)
        if self._opacity <= 0.0:
            self._fade_timer.stop()
            self.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 14, 14)
        bg = QColor(self._color)
        bg.setAlpha(230)
        painter.fillPath(path, bg)


# ══════════════════════════════════════════════════════════════
#  Animated Page Transition
# ══════════════════════════════════════════════════════════════
class FadeTransitionWidget(QWidget):
    """Wrapper that fades a widget in when shown."""

    def __init__(self, child_widget, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(child_widget)
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(400)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def show_animated(self):
        self.setWindowOpacity(0.0)
        self.show()
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()


# ══════════════════════════════════════════════════════════════
#  Sidebar Button
# ══════════════════════════════════════════════════════════════
class SidebarButton(QPushButton):
    def __init__(self, icon_text, label, parent=None):
        super().__init__(parent)
        self._icon_text = icon_text
        self._label = label
        self._active = False
        self.setFixedHeight(56)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)

    def set_active(self, v):
        self._active = v
        self.setChecked(v)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        if self._active or self.isChecked():
            grad = QLinearGradient(0, 0, w, 0)
            grad.setColorAt(0, QColor(56, 184, 176, 220))
            grad.setColorAt(1, QColor(42, 127, 168, 220))
            painter.setBrush(grad)
            painter.setPen(Qt.NoPen)
            path = QPainterPath()
            path.addRoundedRect(6, 4, w - 12, h - 8, 14, 14)
            painter.fillPath(path, grad)
            text_color = QColor("white")
        elif self.underMouse():
            bg = QColor(56, 184, 176, 40)
            painter.setBrush(bg)
            painter.setPen(Qt.NoPen)
            path = QPainterPath()
            path.addRoundedRect(6, 4, w - 12, h - 8, 14, 14)
            painter.fillPath(path, bg)
            text_color = QColor(COLORS["teal_deep"])
        else:
            text_color = QColor(COLORS["text_light"])

        # Icon
        painter.setFont(QFont("Segoe UI Emoji", 16))
        painter.setPen(text_color)
        painter.drawText(QRect(0, 0, 52, h), Qt.AlignCenter, self._icon_text)

        # Label
        painter.setFont(QFont("Segoe UI", 11, QFont.Medium))
        painter.drawText(QRect(52, 0, w - 60, h), Qt.AlignVCenter, self._label)


# ══════════════════════════════════════════════════════════════
#  Particle Background  (subtle floating dots)
# ══════════════════════════════════════════════════════════════
class ParticleBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._particles = []
        import random
        # Mix of teal and purple particles for futuristic feel
        for _ in range(28):
            hue = random.choice([176, 195, 270, 285])
            self._particles.append({
                "x": random.uniform(0, 1),
                "y": random.uniform(0, 1),
                "r": random.uniform(2, 7),
                "dx": random.uniform(-0.0004, 0.0004),
                "dy": random.uniform(-0.0003, 0.0001),
                "alpha": random.randint(25, 75),
                "hue": hue,
                "pulse": random.uniform(0, math.pi * 2),
            })
        self._t = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_particles)
        # Sensory accommodation — see ui.styles.reduce_motion.
        from ui.styles import reduce_motion
        if not reduce_motion():
            self._timer.start(40)

    def _update_particles(self):
        self._t += 0.02
        for p in self._particles:
            p["x"] = (p["x"] + p["dx"]) % 1.0
            p["y"] = (p["y"] + p["dy"]) % 1.0
            p["pulse"] += 0.04
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Subtle grid pattern (futuristic feel)
        grid_color = QColor(0, 191, 168, 8)
        painter.setPen(QPen(grid_color, 1))
        spacing = 60
        for x in range(0, w, spacing):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, spacing):
            painter.drawLine(0, y, w, y)

        # Particles with pulse + glow
        for p in self._particles:
            x, y = p["x"] * w, p["y"] * h
            pulse = (math.sin(p["pulse"]) + 1) / 2
            alpha = int(p["alpha"] * (0.6 + pulse * 0.4))
            r = p["r"] * (0.85 + pulse * 0.3)
            c = QColor.fromHsl(p["hue"], 200, 160)
            c.setAlpha(alpha)
            # Outer glow
            glow = QColor(c)
            glow.setAlpha(alpha // 3)
            painter.setBrush(glow)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(x, y), r * 2.5, r * 2.5)
            # Core
            painter.setBrush(c)
            painter.drawEllipse(QPointF(x, y), r, r)


# ══════════════════════════════════════════════════════════════
#  Toggle Switch  (animated on/off — touch-friendly for kiosk mode)
# ══════════════════════════════════════════════════════════════
class ToggleSwitch(QWidget):
    """A sliding on/off switch. Emits `toggled(bool)` on user action."""

    toggled = Signal(bool)

    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        self._checked = bool(checked)
        self._pos = 1.0 if self._checked else 0.0   # knob position 0..1
        self.setFixedSize(62, 32)
        self.setCursor(Qt.PointingHandCursor)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, value, animate=True):
        value = bool(value)
        if value == self._checked:
            return
        self._checked = value
        if animate:
            self._timer.start(16)
        else:
            self._pos = 1.0 if value else 0.0
            self.update()

    def mousePressEvent(self, event):
        self._checked = not self._checked
        self._timer.start(16)
        self.toggled.emit(self._checked)
        super().mousePressEvent(event)

    def _animate(self):
        target = 1.0 if self._checked else 0.0
        diff = target - self._pos
        if abs(diff) < 0.05:
            self._pos = target
            self._timer.stop()
        else:
            self._pos += diff * 0.30
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # track colour interpolates grey -> green with the knob
        off, on = QColor(170, 180, 195), QColor(0, 217, 160)
        track = QColor(
            int(off.red()   + (on.red()   - off.red())   * self._pos),
            int(off.green() + (on.green() - off.green()) * self._pos),
            int(off.blue()  + (on.blue()  - off.blue())  * self._pos),
        )
        painter.setBrush(track)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, w, h, h // 2, h // 2)

        # white knob
        knob_d = h - 8
        x = 4 + self._pos * (w - knob_d - 8)
        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(QPointF(x + knob_d / 2, h / 2), knob_d / 2, knob_d / 2)
