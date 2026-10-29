"""
ARIA Transition Helper
Smooth transitions between activities — autistic kids often struggle with these.
Visual countdown with verbal warnings: "5 minutes left", "2 minutes left", etc.
"""

import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QTimer, QPointF, QRectF
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QPainterPath, QLinearGradient

from ui.components import GlassCard, ARIAFaceWidget, ParticleBackground
from ui.styles import MAIN_STYLE, COLORS
import database.db_manager as db


class TransitionDots(QWidget):
    def __init__(self, total_steps=5, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self._total = total_steps
        self._current = 0
        self._t = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._anim)
        self._timer.start(33)

    def set_progress(self, step):
        self._current = step
        self.update()

    def _anim(self):
        self._t += 0.04
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cy = h / 2
        gap = w / (self._total + 1)

        for i in range(self._total):
            cx = gap * (i + 1)
            if i < self._current:
                # Done — green
                color = QColor(0, 217, 160)
                painter.setBrush(color)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(cx, cy), 14, 14)
                painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
                painter.setPen(QColor("white"))
                painter.drawText(QRectF(cx - 14, cy - 14, 28, 28), Qt.AlignCenter, "✓")
            elif i == self._current:
                # Current — pulsing teal
                pulse = 0.7 + 0.3 * math.sin(self._t * 4)
                glow_color = QColor(0, 229, 255, int(120 * pulse))
                painter.setBrush(glow_color)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(cx, cy), 22, 22)
                painter.setBrush(QColor(0, 191, 168))
                painter.drawEllipse(QPointF(cx, cy), 14, 14)
                painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
                painter.setPen(QColor("white"))
                painter.drawText(QRectF(cx - 14, cy - 14, 28, 28), Qt.AlignCenter, str(i + 1))
            else:
                # Future — gray
                painter.setBrush(QColor(220, 230, 240))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(cx, cy), 14, 14)
                painter.setFont(QFont("Segoe UI", 11))
                painter.setPen(QColor(150, 165, 185))
                painter.drawText(QRectF(cx - 14, cy - 14, 28, 28), Qt.AlignCenter, str(i + 1))

            # Connector
            if i < self._total - 1:
                next_cx = gap * (i + 2)
                color = QColor(0, 217, 160) if i < self._current else QColor(220, 230, 240)
                painter.setPen(QPen(color, 2))
                painter.drawLine(QPointF(cx + 16, cy), QPointF(next_cx - 16, cy))


class TransitionHelperScreen(QWidget):
    go_back = Signal()

    PRESETS = [
        ("🎮", "🍽️", "Game → Dinner",      5),
        ("📺", "🛌", "TV → Bed",           10),
        ("🎮", "📚", "Play → Study",        5),
        ("🛁", "🛌", "Bath → Sleep",        3),
        ("🏠", "🏥", "Home → Doctor",       15),
        ("📚", "🍎", "School → Snack",      5),
    ]

    WARNINGS = {
        "en": {
            "start": "We're going to switch activities soon.",
            "5":     "5 minutes until we switch.",
            "2":     "2 minutes left.",
            "1":     "1 minute left. Time to wrap up.",
            "30":    "30 seconds left.",
            "10":    "Almost time. Get ready!",
            "done":  "Time to switch! Great job!",
        },
        "ar": {
            "start": "هنغير النشاط قريب.",
            "5":     "5 دقائق للتغيير.",
            "2":     "دقيقتين فاضلين.",
            "1":     "دقيقة واحدة. خلصو.",
            "30":    "30 ثانية فاضلين.",
            "10":    "قرب الوقت. استعدو!",
            "done":  "وقت التغيير! شاطر!",
        },
        "de": {
            "start": "Wir wechseln bald die Aktivität.",
            "5":     "5 Minuten bis zum Wechsel.",
            "2":     "Noch 2 Minuten.",
            "1":     "Noch 1 Minute. Beende deine Aufgabe.",
            "30":    "30 Sekunden übrig.",
            "10":    "Fast da. Mach dich bereit!",
            "done":  "Zeit zu wechseln! Gut gemacht!",
        },
    }

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._child_data = db.get_child(child_id) or {}
        self._lang = self._child_data.get("language", "en")
        self._from_activity = ""
        self._to_activity = ""
        self._duration = 5
        self._remaining = 0
        self._running = False
        self._announced = set()
        self.setStyleSheet(MAIN_STYLE)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

        self._build_ui()

    def _build_ui(self):
        self._bg = ParticleBackground(self)
        self._bg.lower()

        main = QVBoxLayout(self)
        main.setContentsMargins(32, 24, 32, 24)
        main.setSpacing(14)

        # Header
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
        title = QLabel("🔄 Transition Helper")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {COLORS['text']};")
        sub = QLabel("Smooth changes between activities")
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

        # ── LEFT: Active transition view
        left = QVBoxLayout()
        left.setSpacing(14)

        active_card = GlassCard(self, radius=24)
        ac = QVBoxLayout(active_card)
        ac.setContentsMargins(24, 22, 24, 22)
        ac.setSpacing(14)
        ac.setAlignment(Qt.AlignCenter)

        # From → To display
        ft_row = QHBoxLayout()
        ft_row.setAlignment(Qt.AlignCenter)
        ft_row.setSpacing(20)

        self._from_lbl = QLabel("?")
        self._from_lbl.setAlignment(Qt.AlignCenter)
        self._from_lbl.setStyleSheet(f"""
            font-size: 64px;
            background: rgba(0,191,168,0.1);
            border: 3px solid {COLORS['teal']};
            border-radius: 20px;
            padding: 16px;
            min-width: 100px; min-height: 100px;
        """)

        arrow_lbl = QLabel("➔")
        arrow_lbl.setStyleSheet(f"font-size: 40px; color: {COLORS['teal']}; font-weight: 900;")

        self._to_lbl = QLabel("?")
        self._to_lbl.setAlignment(Qt.AlignCenter)
        self._to_lbl.setStyleSheet(f"""
            font-size: 64px;
            background: rgba(179,136,255,0.1);
            border: 3px solid #B388FF;
            border-radius: 20px;
            padding: 16px;
            min-width: 100px; min-height: 100px;
        """)

        ft_row.addWidget(self._from_lbl)
        ft_row.addWidget(arrow_lbl)
        ft_row.addWidget(self._to_lbl)
        ac.addLayout(ft_row)

        # Time display
        self._time_lbl = QLabel("Pick a transition →")
        self._time_lbl.setAlignment(Qt.AlignCenter)
        self._time_lbl.setStyleSheet(f"font-size: 36px; font-weight: 900; color: {COLORS['teal']};")
        ac.addWidget(self._time_lbl)

        # Progress dots
        self._dots = TransitionDots(5, self)
        ac.addWidget(self._dots)

        # ARIA
        face_row = QHBoxLayout()
        self._face = ARIAFaceWidget(size=80)
        self._face.set_expression("calm")
        self._aria_msg = QLabel("Ready for a smooth change.")
        self._aria_msg.setWordWrap(True)
        self._aria_msg.setStyleSheet(f"font-size: 14px; color: {COLORS['teal_deep']}; font-weight: 600;")
        face_row.addWidget(self._face)
        face_row.addWidget(self._aria_msg, 1)
        ac.addLayout(face_row)

        # Controls
        ctrl_row = QHBoxLayout()
        self._start_btn = QPushButton("▶  Start Transition")
        self._start_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #00BFA8, stop:0.5 #00E5FF, stop:1 #B388FF);
                color: white; border: none; border-radius: 14px;
                padding: 12px 28px; font-size: 14px; font-weight: 700;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #5CE5DC, stop:0.5 #4DECFF, stop:1 #C39BFF);
            }}
            QPushButton:disabled {{ background: #C0C8D4; color: #8A9CB8; }}
        """)
        self._start_btn.clicked.connect(self._toggle)
        self._start_btn.setEnabled(False)

        cancel_btn = QPushButton("✕  Cancel")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,107,126,0.12); color: #C04055;
                border: 1.5px solid rgba(255,107,126,0.4); border-radius: 14px;
                padding: 12px 24px; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(255,107,126,0.25); }}
        """)
        cancel_btn.clicked.connect(self._cancel)
        ctrl_row.addWidget(self._start_btn)
        ctrl_row.addWidget(cancel_btn)
        ac.addLayout(ctrl_row)
        left.addWidget(active_card)
        body.addLayout(left, 2)

        # ── RIGHT: Presets + custom
        right = QVBoxLayout()
        right.setSpacing(14)

        preset_card = GlassCard(self, radius=20)
        pl = QVBoxLayout(preset_card)
        pl.setContentsMargins(18, 14, 18, 14)
        pl.addWidget(self._section("PRESETS"))
        for from_ic, to_ic, label, mins in self.PRESETS:
            btn = QPushButton(f"{from_ic} → {to_ic}\n{label}  ·  {mins} min")
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
            btn.clicked.connect(lambda checked, f=from_ic, t=to_ic, m=mins, l=label:
                                self._set_transition(f, t, m, l))
            pl.addWidget(btn)
        right.addWidget(preset_card)
        right.addStretch()
        body.addLayout(right, 1)
        main.addLayout(body, 1)

    def _section(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {COLORS['teal_deep']}; letter-spacing: 2px; padding-bottom: 4px;")
        return lbl

    def _set_transition(self, from_ic, to_ic, minutes, label):
        self._from_activity = from_ic
        self._to_activity = to_ic
        self._duration = minutes * 60
        self._remaining = self._duration
        self._announced = set()

        self._from_lbl.setText(from_ic)
        self._to_lbl.setText(to_ic)
        self._time_lbl.setText(f"{minutes}:00")
        self._aria_msg.setText(f"{label}. Press Start when ready.")
        self._face.set_expression("calm")
        self._start_btn.setEnabled(True)
        self._dots.set_progress(0)

    def _toggle(self):
        if self._running:
            self._timer.stop()
            self._running = False
            self._start_btn.setText("▶  Resume")
        else:
            if self._remaining <= 0:
                self._remaining = self._duration
            self._timer.start(1000)
            self._running = True
            self._start_btn.setText("⏸  Pause")
            self._face.set_expression("listening")
            if "start" not in self._announced:
                self._announce("start")
                self._announced.add("start")

    def _cancel(self):
        self._timer.stop()
        self._running = False
        self._remaining = 0
        self._announced.clear()
        self._dots.set_progress(0)
        self._time_lbl.setText("Cancelled")
        self._aria_msg.setText("That's okay. Try again when ready.")
        self._face.set_expression("calm")
        self._start_btn.setText("▶  Start Transition")
        self._start_btn.setEnabled(True)

    def _tick(self):
        self._remaining -= 1
        if self._remaining < 0:
            self._timer.stop()
            self._running = False
            self._announce("done")
            self._face.set_expression("happy")
            self._aria_msg.setText("🎉 Transition time!")
            self._dots.set_progress(5)
            return

        m, s = divmod(self._remaining, 60)
        self._time_lbl.setText(f"{int(m):02d}:{int(s):02d}")

        # Progress dots — split duration into 5 segments
        seg = self._duration / 5
        progress_step = int((self._duration - self._remaining) / seg)
        self._dots.set_progress(min(progress_step, 5))

        # Announcements
        if self._remaining == 300 and "5" not in self._announced and self._duration > 300:
            self._announce("5"); self._announced.add("5")
        elif self._remaining == 120 and "2" not in self._announced and self._duration > 120:
            self._announce("2"); self._announced.add("2")
        elif self._remaining == 60 and "1" not in self._announced:
            self._announce("1"); self._announced.add("1")
        elif self._remaining == 30 and "30" not in self._announced:
            self._announce("30"); self._announced.add("30")
        elif self._remaining == 10 and "10" not in self._announced:
            self._announce("10"); self._announced.add("10")

    def _announce(self, key):
        msg = self.WARNINGS.get(self._lang, self.WARNINGS["en"]).get(key, "")
        self._aria_msg.setText(msg)
        try:
            from speech.tts_engine import speak
            speak(msg, self._child_id)
        except Exception:
            pass

    def resizeEvent(self, event):
        if hasattr(self, '_bg'):
            self._bg.resize(self.size())
        super().resizeEvent(event)
