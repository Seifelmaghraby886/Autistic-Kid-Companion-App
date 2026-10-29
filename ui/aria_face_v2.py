"""
ARIA Face v2 — Holographic robot head with neural network aura,
eye tracking, phoneme mouth, thinking animation, and emotion-driven palette.
"""

import math
import random
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient,
    QRadialGradient, QFont, QPainterPath, QConicalGradient
)


EMOTION_PALETTES = {
    "happy":     {"primary": "#00D9A0", "accent": "#5CFFE0", "ring": "#7FFFD4"},
    "joy":       {"primary": "#00D9A0", "accent": "#5CFFE0", "ring": "#7FFFD4"},
    "calm":      {"primary": "#00BFA8", "accent": "#5CE5DC", "ring": "#00E5FF"},
    "neutral":   {"primary": "#00BFA8", "accent": "#5CE5DC", "ring": "#00E5FF"},
    "thinking":  {"primary": "#B388FF", "accent": "#C39BFF", "ring": "#9B6EFF"},
    "listening": {"primary": "#00E5FF", "accent": "#4DECFF", "ring": "#00BFFF"},
    "sad":       {"primary": "#6B9FE8", "accent": "#8BB8F0", "ring": "#4A88D0"},
    "sadness":   {"primary": "#6B9FE8", "accent": "#8BB8F0", "ring": "#4A88D0"},
    "surprised": {"primary": "#FFD840", "accent": "#FFE470", "ring": "#FFC020"},
    "surprise":  {"primary": "#FFD840", "accent": "#FFE470", "ring": "#FFC020"},
    "fear":      {"primary": "#A695FF", "accent": "#C0B0FF", "ring": "#8878E8"},
    "scared":    {"primary": "#A695FF", "accent": "#C0B0FF", "ring": "#8878E8"},
    "anger":     {"primary": "#FF8B5C", "accent": "#FFA585", "ring": "#FF6B3C"},
    "upset":     {"primary": "#FF8B5C", "accent": "#FFA585", "ring": "#FF6B3C"},
    "comfort":   {"primary": "#FF6BC4", "accent": "#FF98D8", "ring": "#E055B4"},
    "sleepy":    {"primary": "#A8B8D0", "accent": "#C0D0E0", "ring": "#8898B0"},
}


class ARIAFaceV2(QWidget):
    """Premium holographic robot head."""

    def __init__(self, size=180, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._expression = "calm"
        self._target_expression = "calm"
        self._t = 0.0
        self._blink_t = 0.0
        self._blink_phase = 0.0
        self._next_blink = random.uniform(3, 6)
        self._is_speaking = False
        self._speaking_intensity = 0.0
        self._target_speaking = 0.0
        self._mouse_x = 0
        self._mouse_y = 0
        # Neural nodes inside head
        self._nodes = []
        for _ in range(14):
            self._nodes.append({
                "ang": random.uniform(0, math.pi * 2),
                "r_factor": random.uniform(0.15, 0.55),
                "speed": random.uniform(0.005, 0.012),
                "phase": random.uniform(0, math.pi * 2),
            })
        # Edges (pre-computed pairs)
        self._edges = []
        for i in range(len(self._nodes)):
            for j in range(i + 1, len(self._nodes)):
                if random.random() < 0.18:
                    self._edges.append((i, j))
        # Particle aura
        self._particles = []
        for _ in range(18):
            self._particles.append({
                "ang": random.uniform(0, math.pi * 2),
                "r": random.uniform(1.0, 1.3),
                "speed": random.uniform(-0.008, 0.008),
                "size": random.uniform(1.2, 3.0),
                "phase": random.uniform(0, math.pi * 2),
            })

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)

    def set_expression(self, expr):
        if expr not in EMOTION_PALETTES:
            expr = "calm"
        self._target_expression = expr
        # Immediate switch is fine — palette interpolation handled per-frame implicit
        self._expression = expr

    def set_speaking(self, speaking, intensity=1.0):
        """Activate phoneme-style mouth animation."""
        self._is_speaking = bool(speaking)
        self._target_speaking = float(intensity) if speaking else 0.0

    def mouseMoveEvent(self, e):
        self._mouse_x = e.position().x() - self._size / 2
        self._mouse_y = e.position().y() - self._size / 2

    def _tick(self):
        self._t += 0.045
        self._blink_t += 0.045

        # Blink scheduler
        if self._blink_t >= self._next_blink:
            self._blink_phase = 0.0
            self._blink_t = 0
            self._next_blink = random.uniform(3.5, 7)
        if self._blink_phase < 1.0 and self._blink_t < 0.25:
            self._blink_phase = min(1.0, self._blink_t / 0.12)

        # Speaking intensity smoothing
        self._speaking_intensity += (self._target_speaking - self._speaking_intensity) * 0.25

        # Update neural nodes
        for n in self._nodes:
            n["ang"] += n["speed"]
            n["phase"] += 0.06

        # Update particles
        for p in self._particles:
            p["ang"] += p["speed"]
            p["phase"] += 0.04

        self.update()

    def _eye_offset(self):
        """Eyes track cursor / look around when idle."""
        if abs(self._mouse_x) + abs(self._mouse_y) > 5:
            magnitude = math.sqrt(self._mouse_x ** 2 + self._mouse_y ** 2)
            if magnitude > 0:
                dx = self._mouse_x / magnitude * min(magnitude / 50, 3)
                dy = self._mouse_y / magnitude * min(magnitude / 50, 2)
                return dx, dy
        # Idle gaze wandering
        return math.sin(self._t * 0.3) * 1.5, math.cos(self._t * 0.45) * 1.0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        cx, cy = self._size / 2, self._size / 2
        head_r = self._size * 0.36

        palette = EMOTION_PALETTES.get(self._expression, EMOTION_PALETTES["calm"])
        primary = QColor(palette["primary"])
        accent = QColor(palette["accent"])
        ring = QColor(palette["ring"])

        # Layer 1: Particle aura (orbiting around head)
        for p in self._particles:
            orbit_r = head_r * p["r"] + math.sin(p["phase"]) * 4
            px = cx + math.cos(p["ang"]) * orbit_r
            py = cy + math.sin(p["ang"]) * orbit_r
            alpha = int(60 + 80 * (math.sin(p["phase"]) + 1) / 2)
            glow = QColor(accent)
            glow.setAlpha(alpha)
            painter.setBrush(glow)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(px, py), p["size"] * 1.8, p["size"] * 1.8)
            # core
            core = QColor(ring)
            core.setAlpha(min(255, alpha + 60))
            painter.setBrush(core)
            painter.drawEllipse(QPointF(px, py), p["size"], p["size"])

        # Layer 2: Outer glow halos (3 concentric pulsing)
        pulse = (math.sin(self._t * 1.8) + 1) / 2
        for i, scale in enumerate([1.55, 1.40, 1.25]):
            halo = QColor(primary)
            halo.setAlpha(int(20 + 30 * pulse * (1 - i * 0.2)))
            grad = QRadialGradient(cx, cy, head_r * scale)
            grad.setColorAt(0, QColor(halo.red(), halo.green(), halo.blue(), 0))
            grad.setColorAt(0.7, halo)
            grad.setColorAt(1, QColor(halo.red(), halo.green(), halo.blue(), 0))
            painter.setBrush(grad)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(cx, cy), head_r * scale, head_r * scale)

        # Layer 3: Rotating arc segments (ring around head)
        ring_r = head_r * 1.10
        arc_painter_pen = QPen(QColor(ring.red(), ring.green(), ring.blue(), 200), 2.5,
                                Qt.SolidLine, Qt.RoundCap)
        painter.setPen(arc_painter_pen)
        painter.setBrush(Qt.NoBrush)
        for arc_i in range(3):
            start = (self._t * 30 + arc_i * 120) % 360
            painter.drawArc(
                QRectF(cx - ring_r, cy - ring_r, ring_r * 2, ring_r * 2),
                int(start * 16), int(60 * 16),
            )

        # Layer 4: Head body (glassmorphic sphere)
        head_grad = QRadialGradient(cx - head_r * 0.25, cy - head_r * 0.3, head_r * 1.6)
        head_grad.setColorAt(0, QColor(255, 255, 255, 240))
        head_grad.setColorAt(0.4, QColor(245, 252, 255, 230))
        head_grad.setColorAt(0.85, QColor(accent.red(), accent.green(), accent.blue(), 80))
        head_grad.setColorAt(1, QColor(primary.red(), primary.green(), primary.blue(), 120))
        painter.setBrush(head_grad)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), head_r, head_r)

        # Head outline with neon
        painter.setPen(QPen(ring, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), head_r, head_r)

        # Layer 5: Neural network inside head (visible when thinking)
        is_thinking = self._expression == "thinking" or self._expression == "listening"
        if is_thinking:
            painter.save()
            # Clip to head
            clip_path = QPainterPath()
            clip_path.addEllipse(QPointF(cx, cy), head_r - 4, head_r - 4)
            painter.setClipPath(clip_path)

            # Edges
            for i, j in self._edges:
                n1 = self._nodes[i]
                n2 = self._nodes[j]
                x1 = cx + math.cos(n1["ang"]) * head_r * n1["r_factor"]
                y1 = cy + math.sin(n1["ang"]) * head_r * n1["r_factor"]
                x2 = cx + math.cos(n2["ang"]) * head_r * n2["r_factor"]
                y2 = cy + math.sin(n2["ang"]) * head_r * n2["r_factor"]
                alpha = int(40 + 80 * (math.sin(n1["phase"] + n2["phase"]) + 1) / 2)
                line_color = QColor(ring)
                line_color.setAlpha(alpha)
                painter.setPen(QPen(line_color, 1))
                painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

            # Nodes
            for n in self._nodes:
                nx = cx + math.cos(n["ang"]) * head_r * n["r_factor"]
                ny = cy + math.sin(n["ang"]) * head_r * n["r_factor"]
                node_pulse = (math.sin(n["phase"]) + 1) / 2
                node_color = QColor(primary)
                node_color.setAlpha(int(180 + node_pulse * 75))
                painter.setBrush(node_color)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(nx, ny), 2 + node_pulse * 1.5, 2 + node_pulse * 1.5)
            painter.restore()

        # Layer 6: Top highlight reflection (gives sphere shape)
        painter.save()
        highlight_path = QPainterPath()
        highlight_path.addEllipse(QPointF(cx - head_r * 0.3, cy - head_r * 0.35),
                                  head_r * 0.45, head_r * 0.25)
        h_grad = QRadialGradient(cx - head_r * 0.3, cy - head_r * 0.35, head_r * 0.45)
        h_grad.setColorAt(0, QColor(255, 255, 255, 220))
        h_grad.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setBrush(h_grad)
        painter.setPen(Qt.NoPen)
        painter.drawPath(highlight_path)
        painter.restore()

        # Layer 7: Eyes
        self._draw_eyes(painter, cx, cy, head_r, primary, accent)

        # Layer 8: Mouth
        self._draw_mouth(painter, cx, cy, head_r, primary, accent)

        # Layer 9: Tech accents (small hex/circuit marks)
        self._draw_tech_marks(painter, cx, cy, head_r, ring)

    def _draw_eyes(self, painter, cx, cy, head_r, primary, accent):
        ex_l = cx - head_r * 0.32
        ex_r = cx + head_r * 0.32
        ey = cy - head_r * 0.08
        eye_w = head_r * 0.22
        eye_h = head_r * 0.30

        # Apply blink
        blink_factor = 1.0 - (math.sin(self._blink_phase * math.pi)
                              if self._blink_phase < 1 else 0)
        h = eye_h * max(0.05, blink_factor)

        # Eye tracking offset
        dx, dy = self._eye_offset()

        for ex in (ex_l, ex_r):
            # Eye socket (dark base)
            socket_grad = QRadialGradient(ex, ey, eye_w * 1.4)
            socket_grad.setColorAt(0, QColor(15, 25, 50, 230))
            socket_grad.setColorAt(1, QColor(10, 20, 40, 100))
            painter.setBrush(socket_grad)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(ex, ey), eye_w, h)

            # Iris with glow
            if h > eye_h * 0.15:  # Only if not mid-blink
                iris_r = min(eye_w, h) * 0.85
                ix = ex + dx
                iy = ey + dy

                # Iris glow
                glow = QColor(primary)
                glow.setAlpha(150)
                for r_scale in [1.4, 1.2, 1.0]:
                    glow.setAlpha(int(60 / r_scale))
                    painter.setBrush(glow)
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(QPointF(ix, iy), iris_r * r_scale, iris_r * r_scale)

                # Iris fill (gradient)
                iris_grad = QRadialGradient(ix - iris_r * 0.2, iy - iris_r * 0.2, iris_r * 1.5)
                iris_grad.setColorAt(0, accent)
                iris_grad.setColorAt(0.5, primary)
                iris_grad.setColorAt(1, primary.darker(140))
                painter.setBrush(iris_grad)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(ix, iy), iris_r, iris_r)

                # Pupil
                painter.setBrush(QColor(15, 20, 30))
                painter.drawEllipse(QPointF(ix, iy), iris_r * 0.42, iris_r * 0.42)

                # Specular highlight
                painter.setBrush(QColor(255, 255, 255, 230))
                painter.drawEllipse(QPointF(ix - iris_r * 0.3, iy - iris_r * 0.3),
                                    iris_r * 0.20, iris_r * 0.18)
                # Tiny second highlight
                painter.setBrush(QColor(255, 255, 255, 130))
                painter.drawEllipse(QPointF(ix + iris_r * 0.15, iy + iris_r * 0.15),
                                    iris_r * 0.08, iris_r * 0.08)

        # Eyebrows for some expressions
        if self._expression in ("anger", "upset"):
            painter.setPen(QPen(primary.darker(150), 3.5, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(
                QPointF(ex_l - eye_w * 0.8, ey - eye_h * 0.9),
                QPointF(ex_l + eye_w * 0.6, ey - eye_h * 1.3)
            )
            painter.drawLine(
                QPointF(ex_r - eye_w * 0.6, ey - eye_h * 1.3),
                QPointF(ex_r + eye_w * 0.8, ey - eye_h * 0.9)
            )
        elif self._expression in ("sad", "sadness"):
            painter.setPen(QPen(primary.darker(130), 3, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(
                QPointF(ex_l - eye_w * 0.8, ey - eye_h * 1.3),
                QPointF(ex_l + eye_w * 0.6, ey - eye_h * 0.9)
            )
            painter.drawLine(
                QPointF(ex_r - eye_w * 0.6, ey - eye_h * 0.9),
                QPointF(ex_r + eye_w * 0.8, ey - eye_h * 1.3)
            )
        elif self._expression in ("surprised", "surprise"):
            # Raised brows
            painter.setPen(QPen(primary.darker(130), 2.5, Qt.SolidLine, Qt.RoundCap))
            for ex_b in (ex_l, ex_r):
                path = QPainterPath()
                path.moveTo(ex_b - eye_w * 0.8, ey - eye_h * 1.4)
                path.quadTo(ex_b, ey - eye_h * 1.7, ex_b + eye_w * 0.8, ey - eye_h * 1.4)
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(path)

    def _draw_mouth(self, painter, cx, cy, head_r, primary, accent):
        my = cy + head_r * 0.38
        mw = head_r * 0.30

        if self._is_speaking or self._speaking_intensity > 0.05:
            # Phoneme-style animated mouth — waveform shape
            mh = head_r * 0.10 * self._speaking_intensity * (1.0 + 0.3 * math.sin(self._t * 7))
            mh = max(mh, head_r * 0.02)
            path = QPainterPath()
            path.addRoundedRect(QRectF(cx - mw, my - mh / 2, mw * 2, mh),
                                mh / 2, mh / 2)
            mouth_grad = QLinearGradient(0, my - mh / 2, 0, my + mh / 2)
            mouth_grad.setColorAt(0, primary)
            mouth_grad.setColorAt(1, primary.darker(140))
            painter.setBrush(mouth_grad)
            painter.setPen(QPen(primary.darker(120), 1))
            painter.drawPath(path)
            # Inner glow
            inner_glow = QColor(accent)
            inner_glow.setAlpha(160)
            painter.setBrush(inner_glow)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(
                QRectF(cx - mw * 0.6, my - mh / 4, mw * 1.2, mh / 2),
                mh / 3, mh / 3
            )
            return

        # Expression-based static mouth
        if self._expression in ("happy", "joy"):
            # Big smile
            path = QPainterPath()
            path.moveTo(cx - mw, my)
            path.quadTo(cx, my + head_r * 0.22, cx + mw, my)
            painter.setPen(QPen(primary.darker(130), 3.5, Qt.SolidLine, Qt.RoundCap))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)
        elif self._expression in ("sad", "sadness", "comfort"):
            # Downward
            path = QPainterPath()
            path.moveTo(cx - mw, my + head_r * 0.06)
            path.quadTo(cx, my - head_r * 0.06, cx + mw, my + head_r * 0.06)
            painter.setPen(QPen(primary.darker(130), 3, Qt.SolidLine, Qt.RoundCap))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)
        elif self._expression in ("surprised", "surprise"):
            # Open O
            painter.setBrush(QColor(15, 20, 30, 180))
            painter.setPen(QPen(primary.darker(120), 2))
            painter.drawEllipse(QPointF(cx, my), mw * 0.45, mw * 0.45)
        elif self._expression in ("anger", "upset"):
            # Jagged frown
            path = QPainterPath()
            path.moveTo(cx - mw, my)
            path.lineTo(cx - mw * 0.5, my - head_r * 0.05)
            path.lineTo(cx, my + head_r * 0.02)
            path.lineTo(cx + mw * 0.5, my - head_r * 0.05)
            path.lineTo(cx + mw, my)
            painter.setPen(QPen(primary.darker(140), 3, Qt.SolidLine, Qt.RoundCap))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)
        elif self._expression == "sleepy":
            # Tiny line
            painter.setPen(QPen(primary.darker(120), 3, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(QPointF(cx - mw * 0.4, my), QPointF(cx + mw * 0.4, my))
        else:
            # Calm / thinking — gentle smile
            path = QPainterPath()
            path.moveTo(cx - mw * 0.7, my)
            path.quadTo(cx, my + head_r * 0.08, cx + mw * 0.7, my)
            painter.setPen(QPen(primary.darker(130), 2.8, Qt.SolidLine, Qt.RoundCap))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)

    def _draw_tech_marks(self, painter, cx, cy, head_r, ring):
        """Small futuristic accent marks on the face."""
        # Forehead small circle node
        painter.setPen(QPen(ring, 1))
        painter.setBrush(Qt.NoBrush)
        fy = cy - head_r * 0.75
        painter.drawEllipse(QPointF(cx, fy), 3, 3)
        # Center diamond
        glow = QColor(ring)
        glow.setAlpha(int(120 + 80 * (math.sin(self._t * 2) + 1) / 2))
        painter.setBrush(glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, fy), 2, 2)

        # Side temple lines
        painter.setPen(QPen(QColor(ring.red(), ring.green(), ring.blue(), 100), 1))
        painter.drawLine(QPointF(cx - head_r * 0.85, cy),
                         QPointF(cx - head_r * 0.95, cy))
        painter.drawLine(QPointF(cx + head_r * 0.85, cy),
                         QPointF(cx + head_r * 0.95, cy))


# Backwards-compat alias so existing imports keep working
ARIAFaceWidget = ARIAFaceV2
