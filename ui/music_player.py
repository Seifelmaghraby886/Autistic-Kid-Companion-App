"""
ARIA Sound Garden — autism-friendly procedural music player.
Brown noise, ocean, rain, ambient — all generated, no licensing.
"""

import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QSlider, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QTimer, QPointF
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QPainterPath, QLinearGradient, QRadialGradient

from ui.components import GlassCard, ARIAFaceWidget
from ui.animated_bg import MeshBackground
from ui.styles import MAIN_STYLE, COLORS
import database.db_manager as db


class WaveformVisualizer(QWidget):
    """Animated audio waveform — pretends to react to playing audio."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(80)
        self._t = 0.0
        self._active = False
        self._color = QColor(0, 191, 168)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self._timer.start(33)

    def set_active(self, active, color=None):
        self._active = active
        if color:
            self._color = QColor(color)
        self.update()

    def _update(self):
        if self._active:
            self._t += 0.08
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cy = h / 2
        bars = 40
        bar_w = (w - 20) / bars

        for i in range(bars):
            phase = self._t + i * 0.3
            if self._active:
                amp = (math.sin(phase) + math.sin(phase * 1.7) + math.sin(phase * 0.5)) / 3
                amp = abs(amp)
                bar_h = 6 + amp * (h * 0.7)
            else:
                bar_h = 4

            x = 10 + i * bar_w
            grad = QLinearGradient(0, cy - bar_h / 2, 0, cy + bar_h / 2)
            grad.setColorAt(0, self._color.lighter(140))
            grad.setColorAt(0.5, self._color)
            grad.setColorAt(1, self._color.darker(120))
            painter.setBrush(grad)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(int(x), int(cy - bar_h / 2),
                                    int(bar_w - 2), int(bar_h), 2, 2)


class SoundCard(QWidget):
    play_requested = Signal(str)

    def __init__(self, key, name, desc, color, icon, parent=None):
        super().__init__(parent)
        self._key = key
        self._color = color
        self._playing = False
        self._hover = False
        self.setFixedSize(200, 160)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(4)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 36px; background: transparent;")
        layout.addWidget(icon_lbl)

        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {COLORS['text']}; background: transparent;")
        layout.addWidget(name_lbl)

        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet(f"font-size: 10px; color: {COLORS['text_light']}; background: transparent;")
        desc_lbl.setWordWrap(True)
        layout.addWidget(desc_lbl)

        layout.addStretch()
        self._status_lbl = QLabel("Tap to play")
        self._status_lbl.setStyleSheet(f"font-size: 11px; color: {color}; font-weight: 600; background: transparent;")
        layout.addWidget(self._status_lbl)

    def set_playing(self, playing):
        self._playing = playing
        self._status_lbl.setText("● Playing..." if playing else "Tap to play")
        self.update()

    def enterEvent(self, e):
        self._hover = True
        self.update()
    def leaveEvent(self, e):
        self._hover = False
        self.update()
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.play_requested.emit(self._key)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, 18, 18)

        c = QColor(self._color)
        if self._playing:
            grad = QLinearGradient(0, 0, w, h)
            grad.setColorAt(0, QColor(255, 255, 255, 245))
            grad.setColorAt(1, QColor(c.red(), c.green(), c.blue(), 80))
            painter.fillPath(path, grad)
            painter.setPen(QPen(c, 3))
            painter.drawPath(path)
        elif self._hover:
            grad = QLinearGradient(0, 0, w, h)
            grad.setColorAt(0, QColor(255, 255, 255, 240))
            grad.setColorAt(1, QColor(c.red(), c.green(), c.blue(), 40))
            painter.fillPath(path, grad)
            painter.setPen(QPen(c, 2))
            painter.drawPath(path)
        else:
            painter.fillPath(path, QColor(255, 255, 255, 195))
            painter.setPen(QPen(QColor(c.red(), c.green(), c.blue(), 80), 1.5))
            painter.drawPath(path)


class MusicPlayerScreen(QWidget):
    go_back = Signal()

    SOUNDS = [
        ("brown_noise", "Brown Noise",    "Deep calming rumble — best for focus", "#7B6EC4", "🌫️"),
        ("pink_noise",  "Pink Noise",     "Softer rainfall-like static",          "#FF6BC4", "🌸"),
        ("ocean",       "Ocean Waves",    "Rhythmic gentle waves",                "#1A7FA8", "🌊"),
        ("rain",        "Gentle Rain",    "Soft rain with droplet pings",         "#5CE5DC", "🌧️"),
        ("ambient",     "Ambient Pad",    "Slow harmonic chord music",            "#B388FF", "🎵"),
        ("om",          "Humming Tone",   "Deep continuous hum — meditation",     "#00BFA8", "🕉️"),
    ]

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._child_data = db.get_child(child_id) or {}
        self._current_sound = None
        self._volume = 0.5
        self.setStyleSheet(MAIN_STYLE)
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
        title = QLabel("🎵 Sound Garden")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {COLORS['text']};")
        sub = QLabel("Autism-friendly calming sounds — brown noise, ocean, rain")
        sub.setStyleSheet(f"font-size: 13px; color: {COLORS['text_light']};")
        hdr.addWidget(back_btn); hdr.addSpacing(20)
        col = QVBoxLayout(); col.addWidget(title); col.addWidget(sub)
        hdr.addLayout(col); hdr.addStretch()
        main.addLayout(hdr)

        # Now playing card
        np_card = GlassCard(self, radius=22)
        np_layout = QVBoxLayout(np_card)
        np_layout.setContentsMargins(24, 18, 24, 18)
        np_layout.setSpacing(10)

        np_header = QHBoxLayout()
        self._face = ARIAFaceWidget(size=80)
        self._face.set_expression("calm")
        np_text = QVBoxLayout()
        self._np_title = QLabel("Pick a sound below")
        self._np_title.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {COLORS['text']};")
        self._np_desc = QLabel("Tap any card to start playing")
        self._np_desc.setStyleSheet(f"font-size: 12px; color: {COLORS['text_light']};")
        np_text.addWidget(self._np_title)
        np_text.addWidget(self._np_desc)
        np_header.addWidget(self._face)
        np_header.addSpacing(12)
        np_header.addLayout(np_text, 1)
        np_layout.addLayout(np_header)

        # Waveform
        self._waveform = WaveformVisualizer(self)
        np_layout.addWidget(self._waveform)

        # Stop button
        self._stop_btn = QPushButton("⏹  Stop")
        self._stop_btn.setEnabled(False)
        self._stop_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,107,126,0.15); color: #C04055;
                border: 1.5px solid rgba(255,107,126,0.4); border-radius: 12px;
                padding: 10px 22px; font-size: 13px; font-weight: 700;
            }}
            QPushButton:hover {{ background: rgba(255,107,126,0.30); }}
            QPushButton:disabled {{ opacity: 0.4; }}
        """)
        self._stop_btn.clicked.connect(self._stop)

        # Volume slider
        vol_row = QHBoxLayout()
        vol_lbl = QLabel("🔊  Volume")
        vol_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {COLORS['text_light']};")
        self._vol_slider = QSlider(Qt.Horizontal)
        self._vol_slider.setRange(0, 100)
        self._vol_slider.setValue(50)
        self._vol_slider.valueChanged.connect(self._on_volume)
        vol_row.addWidget(vol_lbl)
        vol_row.addWidget(self._vol_slider, 1)
        vol_row.addWidget(self._stop_btn)
        np_layout.addLayout(vol_row)

        main.addWidget(np_card)

        # Sounds grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        grid_w = QWidget()
        grid_w.setStyleSheet("background: transparent;")
        grid = QGridLayout(grid_w)
        grid.setSpacing(14)
        grid.setContentsMargins(0, 0, 8, 0)

        self._cards = {}
        for i, (key, name, desc, color, icon) in enumerate(self.SOUNDS):
            card = SoundCard(key, name, desc, color, icon, self)
            card.play_requested.connect(self._play_sound)
            self._cards[key] = card
            grid.addWidget(card, i // 3, i % 3)

        scroll.setWidget(grid_w)
        main.addWidget(scroll, 1)

    def _play_sound(self, key):
        try:
            from audio.sound_garden import play_sound, GENERATORS
        except Exception as e:
            print(f"[Music import error: {e}]")
            return

        # Update UI
        for k, card in self._cards.items():
            card.set_playing(k == key)

        sound_info = next((s for s in self.SOUNDS if s[0] == key), None)
        if sound_info:
            _, name, desc, color, icon = sound_info
            self._np_title.setText(f"{icon}  {name}")
            self._np_desc.setText(desc)
            self._waveform.set_active(True, color)
            self._face.set_expression("calm")

        try:
            play_sound(key, self._volume / 1.0, loop=True)
        except Exception as e:
            self._np_desc.setText(f"⚠️ Playback error: {e}")
            return

        self._current_sound = key
        self._stop_btn.setEnabled(True)

    def _stop(self):
        try:
            from audio.sound_garden import stop_sound
            stop_sound()
        except Exception:
            pass
        for card in self._cards.values():
            card.set_playing(False)
        self._waveform.set_active(False)
        self._np_title.setText("Stopped")
        self._np_desc.setText("Tap a card to play another sound")
        self._stop_btn.setEnabled(False)
        self._current_sound = None

    def _on_volume(self, val):
        self._volume = val / 100.0
        # Restart with new volume if playing
        if self._current_sound:
            try:
                from audio.sound_garden import play_sound
                play_sound(self._current_sound, self._volume, loop=True)
            except Exception:
                pass

    def _on_back(self):
        self._stop()
        self.go_back.emit()

    def resizeEvent(self, event):
        if hasattr(self, '_bg'):
            self._bg.resize(self.size())
        super().resizeEvent(event)
