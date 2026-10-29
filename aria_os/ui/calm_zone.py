"""Calm Zone — breathing bubble, quiet mode, parent help."""

import math
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton)
from PySide6.QtCore import Qt, QTimer, Signal, QPointF
from PySide6.QtGui import QPainter, QColor, QRadialGradient, QPen

from ui.components import C, GlassCard, MAIN_STYLE
from data import database as db


class BreathingBubble(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(280, 280)
        self._t = 0.0
        self._timer = QTimer(self); self._timer.timeout.connect(self._tick); self._timer.start(33)
        self._phase_lbl = ""

    def _tick(self):
        self._t += 0.025
        self.update()

    def phase(self):
        cycle = (self._t % 8.0) / 8.0  # 8-second breathing cycle
        if cycle < 0.5:
            return "Breathe in…", "ar", "خد نفس…", cycle / 0.5
        else:
            return "Breathe out…", "ar", "اطلع النفس…", 1 - (cycle - 0.5) / 0.5

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        phase_en, _, phase_ar, scale = self.phase()
        r = 60 + scale * 80
        grad = QRadialGradient(cx, cy, r)
        grad.setColorAt(0, QColor(0, 229, 255, 200))
        grad.setColorAt(0.5, QColor(0, 191, 168, 150))
        grad.setColorAt(1, QColor(0, 191, 168, 30))
        p.setBrush(grad); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(cx, cy), r, r)
        p.setPen(QPen(QColor(0, 229, 255, 200), 2))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(cx, cy), r + 6, r + 6)
        p.setPen(QColor(C["text"]))
        from PySide6.QtGui import QFont
        p.setFont(QFont("Segoe UI", 16, QFont.Bold))
        p.drawText(0, int(cy - 14), w, 28, Qt.AlignCenter, phase_en)
        p.setFont(QFont("Segoe UI", 13))
        p.setPen(QColor(C["text_dim"]))
        p.drawText(0, int(cy + 16), w, 22, Qt.AlignCenter, phase_ar)


class CalmZone(QWidget):
    close_requested = Signal()

    def __init__(self, controller, safety_payload=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setStyleSheet(MAIN_STYLE)
        self._build_ui(safety_payload)

    def _build_ui(self, payload):
        L = QVBoxLayout(self)
        L.setContentsMargins(40, 24, 40, 24)
        L.setSpacing(16)

        top = QHBoxLayout()
        back = QPushButton("← I feel better")
        back.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0,217,160,0.20); color: {C['success']};
                border: 1.5px solid {C['success']}; border-radius: 12px;
                padding: 10px 22px; font-size: 13px; font-weight: 700;
            }}
        """)
        back.clicked.connect(self.close_requested.emit)
        title = QLabel("🌿  Calm Zone")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {C['cyan']};")
        top.addWidget(back); top.addSpacing(16); top.addWidget(title); top.addStretch()
        L.addLayout(top)

        if payload and payload.get("alert_type"):
            warn = GlassCard(self, dark=True)
            wl = QVBoxLayout(warn); wl.setContentsMargins(20, 14, 20, 14)
            wmsg = QLabel("💙  You are safe. A parent alert was sent.")
            wmsg.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {C['warn']};")
            wl.addWidget(wmsg)
            L.addWidget(warn)

        center = QHBoxLayout()
        center.addStretch()
        bubble = BreathingBubble()
        center.addWidget(bubble)
        center.addStretch()
        L.addLayout(center)

        msg = QLabel("I'm here with you. Breathe with me. 💙")
        msg.setAlignment(Qt.AlignCenter)
        msg.setStyleSheet(f"font-size: 16px; color: {C['soft']}; font-weight: 600;")
        L.addWidget(msg)

        actions = QHBoxLayout()
        for label, color in [
            ("Quiet Mode", C["purple"]),
            ("Ocean Sound", C["cyan"]),
            ("Talk to Parent", C["warn"]),
            ("I Feel Better ✓", C["success"]),
        ]:
            b = QPushButton(label)
            b.setMinimumHeight(56)
            b.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255,255,255,0.06); color: {color};
                    border: 1.5px solid {color}; border-radius: 14px;
                    padding: 12px 18px; font-size: 14px; font-weight: 700;
                }}
                QPushButton:hover {{ background: {color}25; }}
            """)
            if label.startswith("I Feel Better"):
                b.clicked.connect(self.close_requested.emit)
            elif label == "Talk to Parent":
                b.clicked.connect(self._alert_parent)
            actions.addWidget(b)
        L.addLayout(actions)

    def _alert_parent(self):
        try:
            db.add_alert(self.controller.child_id, "parent_help_request",
                         "medium", "Child requested parent help from Calm Zone")
        except Exception:
            pass
