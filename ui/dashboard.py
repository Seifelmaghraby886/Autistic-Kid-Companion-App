"""
ARIA Main Dashboard
Central hub with animated ARIA face, status cards, and navigation grid.
"""

import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QFrame, QScrollArea, QSizePolicy, QStackedWidget
)
from PySide6.QtCore import Qt, QTimer, Signal, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import (
    QPainter, QColor, QLinearGradient, QRadialGradient,
    QFont, QPainterPath, QPen, QPixmap
)

from ui.components import (
    GlassCard, ARIAFaceWidget, StatusDot, ParticleBackground, ToastNotification
)
from ui.styles import MAIN_STYLE, COLORS, get_emotion_color
import database.db_manager as db


# ══════════════════════════════════════════════════════════════
#  Animated Nav Card
# ══════════════════════════════════════════════════════════════
class NavCard(QWidget):
    clicked = Signal(str)

    def __init__(self, key, icon, title, subtitle, color, parent=None):
        super().__init__(parent)
        self._key = key
        self._color = QColor(color)
        self._hover = False
        self._press_scale = 1.0
        self._scan_pos = 0.0
        self._glow_t = 0.0
        self.setMinimumSize(120, 105)
        self.setMaximumSize(165, 135)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)

        # Hover scan animation
        self._scan_timer = QTimer(self)
        self._scan_timer.timeout.connect(self._update_scan)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(4)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 34px; background: transparent;")
        icon_lbl.setAlignment(Qt.AlignLeft)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"""
            font-size: 15px; font-weight: 700;
            color: {COLORS['text']}; background: transparent;
        """)
        title_lbl.setWordWrap(True)

        sub_lbl = QLabel(subtitle)
        sub_lbl.setStyleSheet(f"""
            font-size: 10px; color: {COLORS['text_light']};
            background: transparent;
        """)
        sub_lbl.setWordWrap(True)

        layout.addWidget(icon_lbl)
        layout.addWidget(title_lbl)
        layout.addWidget(sub_lbl)
        layout.addStretch()

        # Accent bar at bottom
        bar = QFrame()
        bar.setFixedHeight(3)
        bar.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {color}, stop:1 transparent); border-radius: 2px;"
        )
        layout.addWidget(bar)

    def enterEvent(self, event):
        self._hover = True
        self._scan_pos = 0.0
        self._scan_timer.start(20)
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self._scan_timer.stop()
        self.update()
        super().leaveEvent(event)

    def _update_scan(self):
        self._scan_pos = (self._scan_pos + 0.025) % 1.0
        self._glow_t += 0.06
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._key)
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, 20, 20)

        if self._hover:
            # Glowing card
            bg = QColor(255, 255, 255, 230)
            painter.fillPath(path, bg)

            # Glow border
            glow = QColor(self._color)
            glow.setAlpha(120)
            pen = QPen(glow, 2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)

            # Top color band
            band_path = QPainterPath()
            band_path.addRoundedRect(0, 0, w, 5, 3, 3)
            painter.fillPath(band_path, self._color)

        else:
            bg = QColor(255, 255, 255, 190)
            painter.fillPath(path, bg)
            border = QColor(56, 184, 176, 40)
            painter.setPen(QPen(border, 1.5))
            painter.drawPath(path)

        # Draw children on top
        for child in self.children():
            if hasattr(child, 'render'):
                pass

    def paintEvent(self, event):
        import math
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, 20, 20)

        if self._hover:
            # Elevated holographic glass
            bg_grad = QLinearGradient(0, 0, w, h)
            bg_grad.setColorAt(0, QColor(255, 255, 255, 245))
            bg_grad.setColorAt(0.5, QColor(self._color.red(),
                                            self._color.green(),
                                            self._color.blue(), 30))
            bg_grad.setColorAt(1, QColor(255, 255, 255, 230))
            painter.fillPath(path, bg_grad)

            # Animated rainbow border (teal-cyan-purple flow)
            border_grad = QLinearGradient(0, 0, w, h)
            offset = self._glow_t % 1.0
            border_grad.setColorAt(max(0, offset - 0.3), QColor(0, 191, 168, 220))
            border_grad.setColorAt(offset, QColor(0, 229, 255, 255))
            border_grad.setColorAt(min(1, offset + 0.3), QColor(179, 136, 255, 220))
            from PySide6.QtGui import QBrush
            painter.setPen(QPen(QBrush(border_grad), 2.5))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)

            # Top shine
            shine = QLinearGradient(0, 0, 0, 60)
            shine.setColorAt(0, QColor(255, 255, 255, 100))
            shine.setColorAt(1, QColor(255, 255, 255, 0))
            painter.fillPath(path, shine)

            # Scanning line (futuristic effect)
            painter.setClipPath(path)
            scan_y = self._scan_pos * h
            scan_grad = QLinearGradient(0, scan_y - 10, 0, scan_y + 10)
            scan_grad.setColorAt(0, QColor(0, 229, 255, 0))
            scan_grad.setColorAt(0.5, QColor(0, 229, 255, 90))
            scan_grad.setColorAt(1, QColor(0, 229, 255, 0))
            painter.fillRect(0, int(scan_y - 10), w, 20, scan_grad)

            # Pulse glow corners
            corner_color = QColor(self._color)
            corner_color.setAlpha(int(80 + 60 * abs(math.sin(self._glow_t * 2))))
            painter.setBrush(corner_color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(w - 12, 4, 6, 6)
            painter.drawEllipse(4, h - 12, 6, 6)
        else:
            bg = QColor(255, 255, 255, 195)
            painter.fillPath(path, bg)
            painter.setPen(QPen(QColor(0, 191, 168, 55), 1.5))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)


# ══════════════════════════════════════════════════════════════
#  Status Widget (top right panel)
# ══════════════════════════════════════════════════════════════
class SystemStatusWidget(GlassCard):
    def __init__(self, parent=None):
        super().__init__(parent, radius=18)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        title = QLabel("SYSTEM STATUS")
        title.setStyleSheet(f"""
            font-size: 10px; font-weight: 700;
            color: {COLORS['teal_deep']}; letter-spacing: 2px;
        """)
        layout.addWidget(title)

        self._items = {}
        for key, label in [
            ("camera",   "📷 Camera"),
            ("mic",      "🎙️ Microphone"),
            ("model",    "🧠 Emotion Model"),
            ("api",      "🤖 Gemini AI"),
            ("tts",      "🔊 Voice Engine"),
            ("database", "💾 Database"),
            ("internet", "🌐 Internet"),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet(f"font-size: 12px; color: {COLORS['text']};")
            dot = StatusDot(self)
            dot.set_status(False)
            status_lbl = QLabel("Checking...")
            status_lbl.setStyleSheet(f"font-size: 11px; color: {COLORS['text_light']};")
            row.addWidget(dot)
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(status_lbl)
            layout.addLayout(row)
            self._items[key] = (dot, status_lbl)

    def update_status(self, key, ok, text):
        if key in self._items:
            dot, lbl = self._items[key]
            dot.set_status(ok)
            lbl.setText(text)
            lbl.setStyleSheet(
                f"font-size: 11px; color: {'#4CAF90' if ok else '#D96B6B'};"
            )


# ══════════════════════════════════════════════════════════════
#  Emotion Timeline (mini graph)
# ══════════════════════════════════════════════════════════════
class EmotionTimeline(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self._emotions = []

    def add_emotion(self, emotion):
        self._emotions.append(emotion)
        if len(self._emotions) > 60:
            self._emotions.pop(0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        if not self._emotions:
            painter.setPen(QColor(COLORS["text_light"]))
            painter.setFont(QFont("Segoe UI", 10))
            painter.drawText(self.rect(), Qt.AlignCenter, "No emotion data yet")
            return

        step = w / max(len(self._emotions), 1)
        for i, em in enumerate(self._emotions):
            x = i * step
            bar_h = h * 0.6
            c = QColor(get_emotion_color(em))
            c.setAlpha(180)
            painter.setBrush(c)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(x + 1, h - bar_h, max(step - 2, 2), bar_h, 2, 2)


# ══════════════════════════════════════════════════════════════
#  Main Dashboard
# ══════════════════════════════════════════════════════════════
class DashboardScreen(QWidget):
    navigate = Signal(str)

    NAV_CARDS = [
        # Row 1: AI Conversation
        ("talk",        "💬", "Talk with ARIA",      "AI conversation",             "#00BFA8"),
        ("camera",      "📷", "Live Camera",          "Emotion detection",           "#1A7FA8"),
        ("photo",       "🖼️", "Photo Test",           "Import an image",             "#7B6EC4"),
        ("coach",       "🧠", "AI Coping Coach",      "Personal strategies",         "#00E5FF"),
        ("social",      "🤝", "Social Coach",         "Practice scenarios",          "#FF6BC4"),
        ("bedtime",     "🌙", "Bedtime Story",        "AI calming story",            "#A695FF"),
        ("story",       "📖", "Social Story",         "AI custom situations",        "#FFB347"),
        # Row 2: Calming + sensory
        ("calm",        "🌿", "Calm Zone",            "Breathing & comfort",         "#6B9FE8"),
        ("sensory",     "✨", "Sensory Toolkit",      "Soothing visuals",            "#B388FF"),
        ("music",       "🎵", "Sound Garden",         "Brown noise, ocean, rain",    "#5CE5DC"),
        ("thermometer", "🌡", "Feelings Meter",       "How big is your feeling?",    "#FF8B5C"),
        ("games",       "🎮", "Games & Play",         "Autism-friendly games",       "#00D9A0"),
        ("aac",         "🗨️", "AAC Builder",          "Build sentences",             "#7FFFD4"),
        # Row 3: Daily life
        ("comms",       "🔤", "Quick Buttons",        "Non-verbal board",            "#D8A0E8"),
        ("journal",     "📔", "Mood Journal",         "Track feelings",              "#00BFA8"),
        ("schedule",    "📅", "Visual Schedule",      "Daily routine",               "#FFB73D"),
        ("tutorials",   "📺", "Task Tutorials",       "Animated daily skills",       "#00E5FF"),
        ("timer",       "⏱", "Visual Timer",          "See time pass",               "#FF8B5C"),
        ("transition",  "🔄", "Transition Helper",    "Activity changes",            "#B388FF"),
        # Row 4: Rewards + parent
        ("rewards",     "⭐", "Star Jar",             "Earn rewards",                "#FFD700"),
        ("insights",    "💡", "AI Insights",          "Patterns & wins",             "#00BFA8"),
        ("biometric",   "❤️", "Biometric Monitor",    "HR + HRV + fusion",           "#FF6BC4"),
        ("settings",    "⚙️", "Settings",             "Configure ARIA",              "#90A8C0"),
    ]

    def __init__(self, child_id=None, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._child_data = {}
        self._current_emotion = "calm"
        self._session_id = None
        self.setStyleSheet(MAIN_STYLE)
        self._build_ui()
        self._load_child()
        self._start_status_checks()

    def set_child(self, child_id):
        self._child_id = child_id
        self._load_child()

    def _load_child(self):
        if not self._child_id:
            return
        data = db.get_child(self._child_id)
        if data:
            self._child_data = data
            db.update_child_last_active(self._child_id)
            self._session_id = db.start_session(self._child_id)
            self._refresh_child_panel()

    def _build_ui(self):
        from ui.animated_bg import MeshBackground
        self._bg = MeshBackground(self, intensity=0.6)
        self._bg.lower()

        main = QHBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # ── Left Sidebar
        sidebar = self._build_sidebar()
        main.addWidget(sidebar)

        # ── Center
        center = QVBoxLayout()
        center.setContentsMargins(28, 28, 20, 28)
        center.setSpacing(16)

        # Top bar
        top_bar = self._build_top_bar()
        center.addLayout(top_bar)

        # Navigation grid
        center.addWidget(self._build_nav_grid(), 1)

        main.addLayout(center, 1)

        # ── Right Panel
        right_panel = self._build_right_panel()
        main.addWidget(right_panel)

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 rgba(26,35,50,0.95),
                    stop:1 rgba(15,22,38,0.98));
                border-right: 1px solid rgba(56,184,176,0.15);
            }
        """)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 28, 12, 24)
        layout.setSpacing(6)

        # ARIA logo
        logo_lbl = QLabel("ARIA")
        logo_lbl.setStyleSheet(f"""
            font-size: 28px; font-weight: 900;
            color: {COLORS['teal']}; letter-spacing: 8px;
            padding: 0 8px 16px 8px;
        """)
        layout.addWidget(logo_lbl)

        # ARIA face (small)
        self._face_sidebar = ARIAFaceWidget(size=90)
        layout.addWidget(self._face_sidebar, alignment=Qt.AlignHCenter)

        # Child name
        self._child_name_lbl = QLabel("Loading...")
        self._child_name_lbl.setAlignment(Qt.AlignCenter)
        self._child_name_lbl.setStyleSheet("""
            color: white; font-size: 14px;
            font-weight: 600; padding: 8px 4px 0 4px;
        """)
        layout.addWidget(self._child_name_lbl)

        # Emotion label
        self._emotion_lbl = QLabel("● Calm")
        self._emotion_lbl.setAlignment(Qt.AlignCenter)
        self._emotion_lbl.setStyleSheet(f"color: {COLORS['teal']}; font-size: 12px; padding-bottom: 14px;")
        layout.addWidget(self._emotion_lbl)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background: rgba(56,184,176,0.2); max-height: 1px;")
        layout.addWidget(line)
        layout.addSpacing(8)

        # Mode buttons
        from ui.components import SidebarButton
        modes = [
            ("🏠", "Home Mode"),
            ("📚", "School Mode"),
            ("🧘", "Therapy Mode"),
            ("🎮", "Play Mode"),
            ("🌙", "Sleep Mode"),
        ]
        self._mode_buttons = []
        for icon, label in modes:
            btn = SidebarButton(icon, label, sidebar)
            btn.clicked.connect(lambda checked, l=label: self._set_mode(l))
            layout.addWidget(btn)
            self._mode_buttons.append(btn)

        if self._mode_buttons:
            self._mode_buttons[0].set_active(True)

        layout.addStretch()

        # Bottom
        parent_btn = QPushButton("🔐  Parent Dashboard")
        parent_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(217,107,107,0.15);
                color: #E8A0A0; border: 1px solid rgba(217,107,107,0.3);
                border-radius: 12px; padding: 10px 14px;
                font-size: 12px; text-align: left;
            }}
            QPushButton:hover {{ background: rgba(217,107,107,0.25); }}
        """)
        parent_btn.clicked.connect(lambda: self.navigate.emit("parent"))
        layout.addWidget(parent_btn)
        return sidebar

    def _build_top_bar(self):
        layout = QHBoxLayout()

        # Greeting
        self._greeting_lbl = QLabel("Good morning! ☀️")
        self._greeting_lbl.setStyleSheet(f"""
            font-size: 22px; font-weight: 800; color: {COLORS['text']};
        """)

        self._date_lbl = QLabel()
        self._date_lbl.setStyleSheet(f"font-size: 13px; color: {COLORS['text_light']};")
        self._update_greeting()

        greet_col = QVBoxLayout()
        greet_col.setSpacing(2)
        greet_col.addWidget(self._greeting_lbl)
        greet_col.addWidget(self._date_lbl)
        layout.addLayout(greet_col)
        layout.addStretch()

        # Quick controls
        cam_btn = QPushButton("📷 Camera")
        cam_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(56,184,176,0.10); color: {COLORS['teal_deep']};
                border: 1.5px solid {COLORS['teal']}; border-radius: 12px;
                padding: 8px 16px; font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(56,184,176,0.22); }}
        """)
        cam_btn.clicked.connect(lambda: self.navigate.emit("camera"))

        calm_btn = QPushButton("🌿 Calm Zone")
        calm_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(107,159,212,0.15); color: #2A6090;
                border: 1.5px solid #6B9FD4; border-radius: 12px;
                padding: 8px 16px; font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(107,159,212,0.28); }}
        """)
        calm_btn.clicked.connect(lambda: self.navigate.emit("calm"))

        layout.addWidget(cam_btn)
        layout.addSpacing(8)
        layout.addWidget(calm_btn)
        return layout

    def _build_nav_grid(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        grid = QGridLayout(container)
        grid.setSpacing(14)
        grid.setContentsMargins(0, 0, 0, 0)

        for i, (key, icon, title, sub, color) in enumerate(self.NAV_CARDS):
            card = NavCard(key, icon, title, sub, color, container)
            card.clicked.connect(self.navigate.emit)
            grid.addWidget(card, i // 7, i % 7)

        scroll.setWidget(container)
        return scroll

    def _build_right_panel(self):
        panel = QFrame()
        panel.setFixedWidth(270)
        panel.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 28, 24, 28)
        layout.setSpacing(14)

        # ── ARIA Face (big)
        face_card = GlassCard(panel, radius=22)
        face_layout = QVBoxLayout(face_card)
        face_layout.setContentsMargins(16, 16, 16, 16)
        face_layout.setAlignment(Qt.AlignCenter)

        self._aria_face = ARIAFaceWidget(size=150)
        face_layout.addWidget(self._aria_face, alignment=Qt.AlignCenter)

        self._aria_status_lbl = QLabel("ARIA is ready")
        self._aria_status_lbl.setAlignment(Qt.AlignCenter)
        self._aria_status_lbl.setStyleSheet(f"""
            font-size: 13px; font-weight: 600; color: {COLORS['teal']};
        """)
        face_layout.addWidget(self._aria_status_lbl)
        layout.addWidget(face_card)

        # ── Status
        self._status_widget = SystemStatusWidget(panel)
        layout.addWidget(self._status_widget)

        # ── Emotion timeline
        timeline_card = GlassCard(panel, radius=18)
        tl_layout = QVBoxLayout(timeline_card)
        tl_layout.setContentsMargins(14, 12, 14, 12)
        tl_title = QLabel("TODAY'S EMOTIONS")
        tl_title.setStyleSheet(f"""
            font-size: 10px; font-weight: 700;
            color: {COLORS['teal_deep']}; letter-spacing: 2px;
        """)
        tl_layout.addWidget(tl_title)
        self._timeline = EmotionTimeline(panel)
        tl_layout.addWidget(self._timeline)
        layout.addWidget(timeline_card)

        layout.addStretch()
        return panel

    def _build_child_panel(self):
        pass

    def _refresh_child_panel(self):
        name = self._child_data.get("name", "Child")
        lang_map = {"en": "🇬🇧 English", "ar": "🇪🇬 Arabic", "de": "🇩🇪 Deutsch"}
        lang = lang_map.get(self._child_data.get("language", "en"), "English")
        hour = __import__("datetime").datetime.now().hour
        greeting = ("Good morning" if hour < 12
                    else "Good afternoon" if hour < 17
                    else "Good evening")

        self._greeting_lbl.setText(f"{greeting}, {name}! ☀️")
        self._child_name_lbl.setText(name)
        self._date_lbl.setText(
            f"{lang}  ·  {self._child_data.get('sensory_mode', 'calm').title()} Mode"
        )

    def _update_greeting(self):
        from datetime import datetime
        now = datetime.now()
        self._date_lbl.setText(now.strftime("%A, %d %B %Y"))

    def _set_mode(self, mode):
        for btn in self._mode_buttons:
            btn.set_active(btn._label == mode)
        self._aria_status_lbl.setText(f"ARIA in {mode}")

    def set_emotion(self, emotion: str):
        self._current_emotion = emotion
        self._aria_face.set_expression(emotion)
        self._face_sidebar.set_expression(emotion)
        color = get_emotion_color(emotion)
        ui_labels = {
            "happy": "Happy 😊", "joy": "Happy 😊",
            "calm": "Calm 😌", "neutral": "Calm 😌",
            "sad": "Sad 😢", "sadness": "Sad 😢",
            "scared": "Scared 😨", "fear": "Scared 😨",
            "upset": "Upset 😤", "anger": "Upset 😤",
            "surprised": "Surprised 😲", "surprise": "Surprised 😲",
        }
        label = ui_labels.get(emotion, emotion.title())
        self._emotion_lbl.setText(f"● {label}")
        self._emotion_lbl.setStyleSheet(f"color: {color}; font-size: 12px; padding-bottom: 14px;")
        self._timeline.add_emotion(emotion)

    def _start_status_checks(self):
        QTimer.singleShot(500, self._check_statuses)

    def _check_statuses(self):
        import os
        # Database
        try:
            db.get_all_parents()
            self._status_widget.update_status("database", True, "Ready")
        except Exception:
            self._status_widget.update_status("database", False, "Error")

        # Emotion model
        model_path = "models/emotion_model.h5"
        model_exists = os.path.exists(model_path)
        if model_exists:
            self._status_widget.update_status("model", True, "Loaded")
        else:
            self._status_widget.update_status("model", False, "Not trained yet")

        # API key
        import json
        try:
            with open("config/app_config.json") as f:
                cfg = json.load(f)
            has_key = bool(cfg.get("gemini_api_key", "").strip())
            if has_key:
                self._status_widget.update_status("api", True, "Key configured")
            else:
                self._status_widget.update_status("api", False, "No API key")
        except Exception:
            self._status_widget.update_status("api", False, "Config error")

        # TTS
        try:
            import edge_tts
            self._status_widget.update_status("tts", True, "edge-tts ready")
        except ImportError:
            try:
                import pyttsx3
                self._status_widget.update_status("tts", True, "pyttsx3 ready")
            except ImportError:
                self._status_widget.update_status("tts", False, "Not installed")

        # Internet
        try:
            import urllib.request
            urllib.request.urlopen("https://www.google.com", timeout=3)
            self._status_widget.update_status("internet", True, "Connected")
        except Exception:
            self._status_widget.update_status("internet", False, "Offline")

        # Camera
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            ok = cap.isOpened()
            cap.release()
            self._status_widget.update_status("camera", ok, "Ready" if ok else "Not found")
        except Exception:
            self._status_widget.update_status("camera", False, "Error")

        # Mic
        try:
            import sounddevice as sd
            devs = sd.query_devices()
            self._status_widget.update_status("mic", True, "Ready")
        except Exception:
            self._status_widget.update_status("mic", False, "Error")

    def resizeEvent(self, event):
        if hasattr(self, '_bg'):
            self._bg.resize(self.size())
        super().resizeEvent(event)

    def closeEvent(self, event):
        if self._session_id:
            db.end_session(
                self._session_id,
                dominant_emotion=self._current_emotion,
                summary="Session ended normally"
            )
        super().closeEvent(event)
