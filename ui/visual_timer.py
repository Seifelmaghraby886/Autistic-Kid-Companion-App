"""
ARIA Visual Timer — autism-friendly time visualization.
Time Timer-style countdown with shrinking colored area + warnings.
"""

import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer, QPointF, QRectF
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QPainterPath, QRadialGradient

from ui.components import GlassCard, ARIAFaceWidget, ParticleBackground
from ui.styles import MAIN_STYLE, COLORS
import database.db_manager as db


class TimerCircle(QWidget):
    finished = Signal()
    halfway_warning = Signal()
    final_warning = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(360, 360)
        self._total_seconds = 300  # 5 min default
        self._remaining = self._total_seconds
        self._running = False
        self._t = 0.0
        self._half_emitted = False
        self._final_emitted = False

        self._tick_timer = QTimer(self)
        self._tick_timer.timeout.connect(self._tick)

        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._animate)
        self._anim_timer.start(33)

    def set_minutes(self, minutes):
        self._total_seconds = max(10, minutes * 60)
        self._remaining = self._total_seconds
        self._half_emitted = False
        self._final_emitted = False
        self.update()

    def start(self):
        self._running = True
        self._tick_timer.start(1000)

    def pause(self):
        self._running = False
        self._tick_timer.stop()

    def reset(self):
        self.pause()
        self._remaining = self._total_seconds
        self._half_emitted = False
        self._final_emitted = False
        self.update()

    def is_running(self):
        return self._running

    def remaining_text(self):
        m, s = divmod(self._remaining, 60)
        return f"{int(m):02d}:{int(s):02d}"

    def _tick(self):
        if self._remaining <= 0:
            self.pause()
            self.finished.emit()
            return
        self._remaining -= 1
        progress = self._remaining / self._total_seconds
        if not self._half_emitted and progress <= 0.5:
            self._half_emitted = True
            self.halfway_warning.emit()
        if not self._final_emitted and self._remaining == 30:
            self._final_emitted = True
            self.final_warning.emit()
        self.update()

    def _animate(self):
        self._t += 0.04
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        r = min(w, h) / 2 - 20

        progress = self._remaining / self._total_seconds if self._total_seconds > 0 else 0

        # Color shifts: green → yellow → red as time runs out
        if progress > 0.5:
            color = QColor(0, 217, 160)  # green
        elif progress > 0.25:
            color = QColor(255, 183, 61)  # yellow
        else:
            color = QColor(255, 107, 126)  # red

        # Outer glow ring (pulses when running)
        pulse = 0.6 + 0.4 * abs(math.sin(self._t * 2)) if self._running else 0.5
        glow_alpha = int(80 * pulse) if self._running else 50
        for i in range(4):
            glow_c = QColor(color.red(), color.green(), color.blue(), glow_alpha - i * 15)
            painter.setPen(QPen(glow_c, 4 + i * 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), r + 4 + i * 3, r + 4 + i * 3)

        # Background circle (light gray)
        painter.setBrush(QColor(240, 244, 252, 200))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), r, r)

        # Filled time pie (decreases as time runs)
        path = QPainterPath()
        path.moveTo(cx, cy)
        start_angle = 90  # top
        span = -360 * progress  # negative = clockwise
        path.arcTo(QRectF(cx - r, cy - r, r * 2, r * 2), start_angle, span)
        path.closeSubpath()

        grad = QRadialGradient(cx, cy, r)
        c1 = QColor(color.red(), color.green(), color.blue(), 230)
        c2 = QColor(color.red(), color.green(), color.blue(), 180)
        grad.setColorAt(0, c1)
        grad.setColorAt(1, c2)
        painter.setBrush(grad)
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)

        # Border
        painter.setPen(QPen(color, 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), r, r)

        # Center white disc
        inner_r = r * 0.55
        painter.setBrush(QColor(255, 255, 255, 240))
        painter.setPen(QPen(color, 2))
        painter.drawEllipse(QPointF(cx, cy), inner_r, inner_r)

        # Time text
        painter.setFont(QFont("Segoe UI", 36, QFont.Black))
        painter.setPen(color.darker(110))
        text_rect = QRectF(0, cy - 35, w, 50)
        painter.drawText(text_rect, Qt.AlignCenter, self.remaining_text())

        # Status text
        painter.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
        painter.setPen(QColor(COLORS["text_light"]))
        status = "Running..." if self._running else ("Done!" if self._remaining == 0 else "Paused")
        painter.drawText(QRectF(0, cy + 18, w, 20), Qt.AlignCenter, status)

        # Tick marks around edge
        painter.setPen(QPen(QColor(COLORS["text_light"]), 2))
        for i in range(12):
            angle = math.radians(i * 30 - 90)
            x1 = cx + (r - 8) * math.cos(angle)
            y1 = cy + (r - 8) * math.sin(angle)
            x2 = cx + r * math.cos(angle)
            y2 = cy + r * math.sin(angle)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))


class VisualTimerScreen(QWidget):
    go_back = Signal()

    PRESETS = [
        ("⚡", "Quick", 1),
        ("☕", "Short", 5),
        ("🎮", "Play", 15),
        ("📚", "Focus", 25),
        ("🌙", "Long", 45),
    ]

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
        main.setContentsMargins(32, 24, 32, 24)
        main.setSpacing(16)

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
        title = QLabel("⏱ Visual Timer")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {COLORS['text']};")
        sub = QLabel("See time disappear — calm and predictable")
        sub.setStyleSheet(f"font-size: 13px; color: {COLORS['text_light']};")
        hdr.addWidget(back_btn)
        hdr.addSpacing(20)
        col = QVBoxLayout()
        col.addWidget(title)
        col.addWidget(sub)
        hdr.addLayout(col)
        hdr.addStretch()
        main.addLayout(hdr)

        body = QHBoxLayout()
        body.setSpacing(20)

        # ── LEFT: Timer
        left = QVBoxLayout()
        timer_card = GlassCard(self, radius=24)
        tl = QVBoxLayout(timer_card)
        tl.setContentsMargins(20, 20, 20, 20)
        tl.setAlignment(Qt.AlignCenter)
        self._timer_circle = TimerCircle(self)
        self._timer_circle.finished.connect(self._on_done)
        self._timer_circle.halfway_warning.connect(self._on_halfway)
        self._timer_circle.final_warning.connect(self._on_final)
        tl.addWidget(self._timer_circle, alignment=Qt.AlignCenter)
        left.addWidget(timer_card)

        # Controls
        ctl_card = GlassCard(self, radius=18)
        cl = QHBoxLayout(ctl_card)
        cl.setContentsMargins(18, 12, 18, 12)
        cl.setSpacing(10)

        self._start_btn = QPushButton("▶  Start")
        self._start_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #00BFA8, stop:1 #00D9A0);
                color: white; border: none; border-radius: 12px;
                padding: 11px 24px; font-size: 14px; font-weight: 700;
            }}
            QPushButton:hover {{ background: #00D9A0; }}
        """)
        self._start_btn.clicked.connect(self._toggle_timer)

        reset_btn = QPushButton("↻  Reset")
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0,191,168,0.10); color: {COLORS['teal_deep']};
                border: 1.5px solid {COLORS['teal']}; border-radius: 12px;
                padding: 11px 24px; font-size: 14px; font-weight: 700;
            }}
            QPushButton:hover {{ background: rgba(0,191,168,0.22); }}
        """)
        reset_btn.clicked.connect(self._reset)
        cl.addWidget(self._start_btn)
        cl.addWidget(reset_btn)
        left.addWidget(ctl_card)
        body.addLayout(left, 2)

        # ── RIGHT: Presets + ARIA + custom
        right = QVBoxLayout()
        right.setSpacing(14)

        face_card = GlassCard(self, radius=22)
        fc = QVBoxLayout(face_card)
        fc.setContentsMargins(20, 18, 20, 18)
        fc.setAlignment(Qt.AlignCenter)
        self._face = ARIAFaceWidget(size=110)
        fc.addWidget(self._face, alignment=Qt.AlignCenter)
        self._aria_msg = QLabel("Pick a time below or set your own.")
        self._aria_msg.setAlignment(Qt.AlignCenter)
        self._aria_msg.setWordWrap(True)
        self._aria_msg.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {COLORS['teal_deep']};")
        fc.addWidget(self._aria_msg)
        right.addWidget(face_card)

        preset_card = GlassCard(self, radius=20)
        pl = QVBoxLayout(preset_card)
        pl.setContentsMargins(18, 14, 18, 14)
        pl.addWidget(self._section("QUICK PRESETS"))
        for icon, name, mins in self.PRESETS:
            btn = QPushButton(f"{icon}  {name}  ·  {mins} min")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255,255,255,0.85);
                    color: {COLORS['text']};
                    border: 1.5px solid rgba(0,191,168,0.25);
                    border-radius: 12px; padding: 10px 14px;
                    font-size: 12px; font-weight: 600;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background: rgba(0,191,168,0.15);
                    border-color: {COLORS['teal']};
                }}
            """)
            btn.clicked.connect(lambda checked, m=mins, n=name: self._set_preset(m, n))
            pl.addWidget(btn)
        right.addWidget(preset_card)

        custom_card = GlassCard(self, radius=18)
        ccl = QVBoxLayout(custom_card)
        ccl.setContentsMargins(18, 12, 18, 12)
        ccl.addWidget(self._section("CUSTOM"))
        row = QHBoxLayout()
        self._mins_spin = QSpinBox()
        self._mins_spin.setRange(1, 120)
        self._mins_spin.setValue(5)
        self._mins_spin.setSuffix(" min")
        set_btn = QPushButton("Set")
        set_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['teal']}; color: white;
                border: none; border-radius: 10px;
                padding: 8px 16px; font-size: 12px; font-weight: 700;
            }}
            QPushButton:hover {{ background: {COLORS['teal_glow']}; }}
        """)
        set_btn.clicked.connect(self._set_custom)
        row.addWidget(self._mins_spin)
        row.addWidget(set_btn)
        ccl.addLayout(row)
        right.addWidget(custom_card)
        right.addStretch()

        body.addLayout(right, 1)
        main.addLayout(body, 1)

    def _section(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {COLORS['teal_deep']}; letter-spacing: 2px; padding-bottom: 4px;")
        return lbl

    def _set_preset(self, mins, name):
        self._timer_circle.set_minutes(mins)
        self._aria_msg.setText(f"Set to {mins} min. Press Start when ready! ⏱")
        self._face.set_expression("calm")

    def _set_custom(self):
        m = self._mins_spin.value()
        self._timer_circle.set_minutes(m)
        self._aria_msg.setText(f"Set to {m} min. Press Start when ready! ⏱")

    def _toggle_timer(self):
        if self._timer_circle.is_running():
            self._timer_circle.pause()
            self._start_btn.setText("▶  Resume")
            self._face.set_expression("calm")
            self._aria_msg.setText("Paused. Press Resume to continue.")
        else:
            self._timer_circle.start()
            self._start_btn.setText("⏸  Pause")
            self._face.set_expression("listening")
            self._aria_msg.setText("Timer running. I'll let you know!")

    def _reset(self):
        self._timer_circle.reset()
        self._start_btn.setText("▶  Start")
        self._face.set_expression("calm")
        self._aria_msg.setText("Reset. Pick a new time!")

    def _on_halfway(self):
        self._face.set_expression("happy")
        self._aria_msg.setText("Halfway there! You're doing great! 🌟")
        try:
            from speech.tts_engine import speak
            speak("You are halfway there!", self._child_id)
        except Exception:
            pass

    def _on_final(self):
        self._face.set_expression("thinking")
        self._aria_msg.setText("30 seconds left. Almost done! ⚡")
        try:
            from speech.tts_engine import speak
            speak("Thirty seconds left.", self._child_id)
        except Exception:
            pass

    def _on_done(self):
        self._face.set_expression("happy")
        self._aria_msg.setText("🎉 Time's up! Great job!")
        self._start_btn.setText("▶  Start")
        try:
            from speech.tts_engine import speak
            speak("Time is up. Great job!", self._child_id)
        except Exception:
            pass

    def resizeEvent(self, event):
        if hasattr(self, '_bg'):
            self._bg.resize(self.size())
        super().resizeEvent(event)
