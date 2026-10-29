"""
ARIA Biometric Monitor
Live BPM + HRV + multimodal fusion. Supports Apple Watch CSV import.
"""

import math
from collections import deque
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QFrame, QComboBox
)
from PySide6.QtCore import Qt, Signal, QTimer, QPointF, QRectF
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QPainterPath, QLinearGradient, QBrush

from ui.components import GlassCard
from ui.aria_face_v2 import ARIAFaceV2
from ui.animated_bg import MeshBackground
from ui.styles import MAIN_STYLE, COLORS
from biometric.heart_rate import HeartRateStream, fuse_face_and_biometric, child_resting_range
import database.db_manager as db


class HRGraph(QWidget):
    """Real-time scrolling BPM line graph."""

    def __init__(self, max_points=60, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(160)
        self._values = deque(maxlen=max_points)
        self._max_points = max_points
        self._low = 60
        self._high = 100
        self._t = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._anim)
        self._timer.start(40)

    def push(self, bpm):
        self._values.append(bpm)
        self.update()

    def set_range(self, low, high):
        self._low = low
        self._high = high

    def _anim(self):
        self._t += 0.05
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        # bg
        painter.fillRect(0, 0, w, h, QColor("#0A1428"))
        # grid
        painter.setPen(QPen(QColor(0, 191, 168, 30), 1))
        for i in range(1, 5):
            y = h * i / 5
            painter.drawLine(0, int(y), w, int(y))
        # resting band
        y_low = h - h * (self._low - 40) / 140
        y_high = h - h * (self._high - 40) / 140
        painter.setBrush(QColor(0, 217, 160, 25))
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, int(y_high), w, int(y_low - y_high))
        # axis labels
        painter.setPen(QColor(150, 165, 185))
        painter.setFont(QFont("Segoe UI", 8))
        for bpm in (60, 100, 140, 180):
            y = h - h * (bpm - 40) / 140
            painter.drawText(4, int(y - 2), f"{bpm}")
        if len(self._values) < 2:
            painter.setPen(QColor(150, 165, 185))
            painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
            painter.drawText(QRectF(0, 0, w, h), Qt.AlignCenter, "Waiting for heartbeat...")
            return
        # line
        path = QPainterPath()
        step = w / max(1, self._max_points - 1)
        for i, v in enumerate(self._values):
            x = i * step
            y = h - h * (v - 40) / 140
            y = max(2, min(h - 2, y))
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        # Glow
        for w_pen, alpha in [(6, 40), (3, 100)]:
            grad = QLinearGradient(0, 0, w, 0)
            grad.setColorAt(0, QColor(0, 229, 255, alpha))
            grad.setColorAt(1, QColor(255, 107, 196, alpha))
            painter.setPen(QPen(QBrush(grad), w_pen, Qt.SolidLine, Qt.RoundCap))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)
        # Last value dot pulsing
        if self._values:
            last_v = self._values[-1]
            last_x = (len(self._values) - 1) * step
            last_y = h - h * (last_v - 40) / 140
            pulse = (math.sin(self._t * 4) + 1) / 2
            glow = QColor("#FF6BC4")
            glow.setAlpha(int(80 + 120 * pulse))
            painter.setBrush(glow)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(last_x, last_y), 8 + pulse * 4, 8 + pulse * 4)
            painter.setBrush(QColor("#FFFFFF"))
            painter.drawEllipse(QPointF(last_x, last_y), 4, 4)


class HeartIcon(QWidget):
    """Pulsing heart that beats at the actual BPM."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(120, 120)
        self._bpm = 75
        self._t = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._beat)
        self._timer.start(30)

    def set_bpm(self, bpm):
        self._bpm = max(30, bpm)

    def _beat(self):
        self._t += 0.03
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        # beat phase from BPM
        beat_freq = self._bpm / 60
        phase = (self._t * beat_freq) % 1.0
        # double thump shape (lub-dub)
        if phase < 0.10:
            scale = 1.0 + 0.18 * (phase / 0.10)
        elif phase < 0.20:
            scale = 1.18 - 0.18 * ((phase - 0.10) / 0.10)
        elif phase < 0.30:
            scale = 1.0 + 0.10 * ((phase - 0.20) / 0.10)
        elif phase < 0.40:
            scale = 1.10 - 0.10 * ((phase - 0.30) / 0.10)
        else:
            scale = 1.0

        r = 32 * scale
        # Glow
        for i, alpha in [(12, 30), (6, 80)]:
            glow = QColor("#FF6BC4")
            glow.setAlpha(alpha)
            painter.setBrush(glow)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(cx, cy), r + i, r + i)
        # Heart shape
        path = QPainterPath()
        path.moveTo(cx, cy + r * 0.35)
        path.cubicTo(cx + r * 1.3, cy - r * 0.3,
                     cx + r * 0.3, cy - r * 1.1,
                     cx, cy - r * 0.3)
        path.cubicTo(cx - r * 0.3, cy - r * 1.1,
                     cx - r * 1.3, cy - r * 0.3,
                     cx, cy + r * 0.35)
        grad = QLinearGradient(cx, cy - r, cx, cy + r)
        grad.setColorAt(0, QColor("#FF98D8"))
        grad.setColorAt(1, QColor("#E055B4"))
        painter.setBrush(grad)
        painter.setPen(QPen(QColor("#FFFFFF"), 2))
        painter.drawPath(path)


class BiometricScreen(QWidget):
    go_back = Signal()

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._child = db.get_child(child_id) or {}
        self._age = self._child.get("age", 8)
        self._last_face_emotion = "calm"
        self._face_conf = 0.7
        self._latest_bpm = 0
        self._latest_hrv = 0
        self._latest_stress = None
        self.setStyleSheet(MAIN_STYLE)
        self._stream = HeartRateStream(source="mock", child_age=self._age)
        self._stream.bpm_updated.connect(self._on_bpm)
        self._stream.stress_updated.connect(self._on_stress)
        self._stream.error.connect(self._on_error)
        self._build_ui()

    def _build_ui(self):
        self._bg = MeshBackground(self, intensity=0.5)
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
        back_btn.clicked.connect(self._on_back)
        title = QLabel("❤️  Biometric Monitor")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {COLORS['text']};")
        sub = QLabel("Heart rate + HRV + multimodal emotion fusion")
        sub.setStyleSheet(f"font-size: 13px; color: {COLORS['text_light']};")
        hdr.addWidget(back_btn); hdr.addSpacing(20)
        col = QVBoxLayout(); col.addWidget(title); col.addWidget(sub)
        hdr.addLayout(col); hdr.addStretch()
        main.addLayout(hdr)

        body = QHBoxLayout()
        body.setSpacing(16)

        # ── LEFT: live stats
        left = QVBoxLayout()
        left.setSpacing(14)

        live_card = GlassCard(self, radius=22)
        ll = QVBoxLayout(live_card)
        ll.setContentsMargins(20, 18, 20, 18)
        ll.setSpacing(8)

        ll.addWidget(self._section("LIVE HEART RATE"))
        hr_row = QHBoxLayout()
        self._heart = HeartIcon()
        hr_col = QVBoxLayout()
        self._bpm_lbl = QLabel("--")
        self._bpm_lbl.setStyleSheet(f"font-size: 72px; font-weight: 900; color: {COLORS['text']}; line-height: 1;")
        bpm_unit = QLabel("BPM")
        bpm_unit.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {COLORS['text_light']}; letter-spacing: 3px;")
        hr_col.addWidget(self._bpm_lbl)
        hr_col.addWidget(bpm_unit)
        hr_row.addWidget(self._heart)
        hr_row.addSpacing(16)
        hr_row.addLayout(hr_col)
        hr_row.addStretch()
        ll.addLayout(hr_row)

        # HRV row
        hrv_row = QHBoxLayout()
        self._hrv_lbl = QLabel("HRV (RMSSD): -- ms")
        self._hrv_lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {COLORS['teal_deep']};")
        self._range_lbl = QLabel("")
        self._range_lbl.setStyleSheet(f"font-size: 12px; color: {COLORS['text_light']};")
        hrv_row.addWidget(self._hrv_lbl)
        hrv_row.addStretch()
        hrv_row.addWidget(self._range_lbl)
        ll.addLayout(hrv_row)

        left.addWidget(live_card)

        # Source selector
        src_card = GlassCard(self, radius=18)
        sl = QVBoxLayout(src_card)
        sl.setContentsMargins(20, 14, 20, 14)
        sl.addWidget(self._section("DATA SOURCE"))
        self._source_combo = QComboBox()
        self._source_combo.addItem("Mock (demo)", "mock")
        self._source_combo.addItem("Apple Watch CSV replay", "csv_replay")
        sl.addWidget(self._source_combo)

        btn_row = QHBoxLayout()
        import_btn = QPushButton("📂 Import Apple Watch CSV")
        import_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0,191,168,0.10); color: {COLORS['teal_deep']};
                border: 1.5px solid {COLORS['teal']}; border-radius: 10px;
                padding: 9px 14px; font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(0,191,168,0.22); }}
        """)
        import_btn.clicked.connect(self._import_csv)
        btn_row.addWidget(import_btn)
        sl.addLayout(btn_row)

        ctrl_row = QHBoxLayout()
        self._start_btn = QPushButton("▶  Start")
        self._start_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #00BFA8, stop:1 #00E5FF);
                color: white; border: none; border-radius: 12px;
                padding: 11px 22px; font-size: 13px; font-weight: 700;
            }}
            QPushButton:hover {{ background: #5CE5DC; }}
        """)
        self._start_btn.clicked.connect(self._toggle_stream)
        ctrl_row.addWidget(self._start_btn)
        ctrl_row.addStretch()
        sl.addLayout(ctrl_row)

        left.addWidget(src_card)
        left.addStretch()
        body.addLayout(left, 1)

        # ── RIGHT: graph + fusion verdict
        right = QVBoxLayout()
        right.setSpacing(14)

        graph_card = GlassCard(self, radius=22)
        gl = QVBoxLayout(graph_card)
        gl.setContentsMargins(16, 12, 16, 12)
        gl.addWidget(self._section("BPM TIMELINE (last 60 s)"))
        self._graph = HRGraph(max_points=60)
        low, high = child_resting_range(self._age)
        self._graph.set_range(low, high)
        self._range_lbl.setText(f"Resting range: {low}–{high} BPM (age {self._age})")
        gl.addWidget(self._graph)
        right.addWidget(graph_card)

        # Fusion card
        fuse_card = GlassCard(self, radius=22)
        fl = QHBoxLayout(fuse_card)
        fl.setContentsMargins(20, 16, 20, 16)
        fl.setSpacing(16)

        self._face = ARIAFaceV2(size=130)
        self._face.set_expression("calm")
        fl.addWidget(self._face)

        verdict_col = QVBoxLayout()
        verdict_col.setSpacing(4)
        verdict_col.addWidget(self._section("MULTIMODAL FUSION VERDICT"))
        self._verdict_lbl = QLabel("Calm")
        self._verdict_lbl.setStyleSheet(f"font-size: 28px; font-weight: 800; color: {COLORS['teal_deep']};")
        self._stress_lbl = QLabel("Stress score: --")
        self._stress_lbl.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {COLORS['text']};")
        self._note_lbl = QLabel("Waiting for data...")
        self._note_lbl.setWordWrap(True)
        self._note_lbl.setStyleSheet(f"font-size: 12px; color: {COLORS['text_light']}; padding-top: 4px;")
        verdict_col.addWidget(self._verdict_lbl)
        verdict_col.addWidget(self._stress_lbl)
        verdict_col.addWidget(self._note_lbl)
        verdict_col.addStretch()
        fl.addLayout(verdict_col, 1)
        right.addWidget(fuse_card)

        body.addLayout(right, 2)
        main.addLayout(body, 1)

    def _section(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {COLORS['teal_deep']}; letter-spacing: 2px;")
        return lbl

    def set_face_emotion(self, emotion, confidence):
        """Called by Live Camera when emotion is detected (future integration)."""
        self._last_face_emotion = emotion
        self._face_conf = confidence

    def _toggle_stream(self):
        if self._stream._running:
            self._stream.stop()
            self._start_btn.setText("▶  Start")
        else:
            source = self._source_combo.currentData()
            self._stream._source = source
            self._stream.start()
            self._start_btn.setText("⏸  Pause")

    def _import_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Apple Health CSV", "",
                                              "CSV Files (*.csv)")
        if not path:
            return
        count = self._stream.load_csv(path)
        if count == 0:
            self._note_lbl.setText("⚠️ Could not read CSV. Need columns: date + value/bpm.")
        else:
            self._note_lbl.setText(f"✅ Loaded {count} samples. Select 'CSV replay' + Start.")
            self._source_combo.setCurrentIndex(1)

    def _on_bpm(self, bpm, hrv):
        self._latest_bpm = bpm
        self._latest_hrv = hrv
        self._bpm_lbl.setText(str(bpm))
        self._heart.set_bpm(bpm)
        self._graph.push(bpm)
        if hrv > 0:
            self._hrv_lbl.setText(f"HRV (RMSSD): {hrv:.0f} ms")

    def _on_stress(self, stress):
        self._latest_stress = stress
        score = stress["score"]
        self._stress_lbl.setText(f"Stress score: {score:.0f} / 100  ({stress['label']})")

        # Fuse with latest face emotion
        fused = fuse_face_and_biometric(self._last_face_emotion, self._face_conf,
                                        stress, self._age)
        self._verdict_lbl.setText(fused["emotion"].title())
        color = {
            "calm": COLORS["teal"], "happy": "#00D9A0", "neutral": COLORS["teal"],
            "sad": "#6B9FE8", "fear": "#A695FF", "anger": "#FF8B5C",
            "surprise": "#FFD840", "comfort": "#FF6BC4",
        }.get(fused["emotion"], COLORS["teal_deep"])
        self._verdict_lbl.setStyleSheet(f"font-size: 28px; font-weight: 800; color: {color};")
        self._face.set_expression(fused["emotion"])

        note = fused["fusion_note"]
        if fused["parent_alert"]:
            note = "⚠ " + note + " (Parent alert)"
        self._note_lbl.setText(note or "Both signals agree.")

        # Log to DB
        try:
            db.log_emotion(self._child_id, fused["emotion"], fused["confidence"],
                           source="biometric_fusion",
                           action_taken=f"bpm={self._latest_bpm} hrv={self._latest_hrv:.0f} stress={score:.0f}")
        except Exception:
            pass

    def _on_error(self, msg):
        self._note_lbl.setText(f"⚠️ {msg}")

    def _on_back(self):
        try:
            self._stream.stop()
        except Exception:
            pass
        self.go_back.emit()

    def resizeEvent(self, event):
        if hasattr(self, '_bg'):
            self._bg.resize(self.size())
        super().resizeEvent(event)
