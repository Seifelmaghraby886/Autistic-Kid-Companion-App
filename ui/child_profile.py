"""
ARIA Child Profile Setup
Multi-step child profile creation with autism-specific fields.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QScrollArea, QCheckBox,
    QSpinBox, QFrame, QButtonGroup, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPainter, QColor, QFont, QPainterPath

from ui.components import GlassCard, ParticleBackground, ToastNotification
from ui.styles import MAIN_STYLE, COLORS
import database.db_manager as db


class TagButton(QPushButton):
    """Toggle button for topic/trigger tags."""
    def __init__(self, text, color=None, parent=None):
        super().__init__(text, parent)
        self._color = color or COLORS["teal"]
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background: rgba(56,184,176,0.08);
                color: {COLORS['text_light']};
                border: 1.5px solid rgba(56,184,176,0.25);
                border-radius: 20px;
                padding: 7px 16px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:checked {{
                background: {self._color};
                color: white;
                border-color: {self._color};
                font-weight: 600;
            }}
            QPushButton:hover:!checked {{
                background: rgba(56,184,176,0.15);
                border-color: {COLORS['teal']};
            }}
        """)


class TagSelector(QWidget):
    def __init__(self, items, color=None, parent=None):
        super().__init__(parent)
        self._buttons = {}
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignLeft)

        wrap = QWidget()
        wrap_layout = QGridLayout(wrap)
        wrap_layout.setContentsMargins(0, 0, 0, 0)
        wrap_layout.setSpacing(8)

        for i, item in enumerate(items):
            btn = TagButton(item, color)
            self._buttons[item] = btn
            wrap_layout.addWidget(btn, i // 5, i % 5)

        layout.addWidget(wrap)
        layout.addStretch()

    def selected(self):
        return [k for k, v in self._buttons.items() if v.isChecked()]

    def set_selected(self, items):
        for item in items:
            if item in self._buttons:
                self._buttons[item].setChecked(True)


class OptionCard(QWidget):
    selected = Signal(str)

    def __init__(self, options, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self._buttons = {}
        self._current = None

        for key, label, icon in options:
            btn = QPushButton(f"{icon}\n{label}")
            btn.setCheckable(True)
            btn.setFixedSize(120, 70)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(56,184,176,0.08);
                    border: 1.5px solid rgba(56,184,176,0.25);
                    border-radius: 14px;
                    font-size: 11px;
                    color: {COLORS['text_light']};
                    padding: 4px;
                }}
                QPushButton:checked {{
                    background: rgba(56,184,176,0.20);
                    border-color: {COLORS['teal']};
                    color: {COLORS['teal_deep']};
                    font-weight: 600;
                }}
                QPushButton:hover:!checked {{
                    background: rgba(56,184,176,0.12);
                }}
            """)
            btn.clicked.connect(lambda checked, k=key: self._on_select(k))
            self._buttons[key] = btn
            layout.addWidget(btn)
        layout.addStretch()

    def _on_select(self, key):
        for k, b in self._buttons.items():
            b.setChecked(k == key)
        self._current = key
        self.selected.emit(key)

    def value(self):
        return self._current

    def set_value(self, key):
        if key in self._buttons:
            self._on_select(key)


class ChildProfileSetup(QWidget):
    setup_complete = Signal(int)  # child_id

    def __init__(self, parent_id, parent=None):
        super().__init__(parent)
        self._parent_id = parent_id
        self._child_id = None
        self.setStyleSheet(MAIN_STYLE)
        self._build_ui()

    def _build_ui(self):
        self._bg = ParticleBackground(self)
        self._bg.resize(self.size())

        outer = QVBoxLayout(self)
        outer.setContentsMargins(60, 30, 60, 30)
        outer.setSpacing(0)

        # Header
        hdr = QHBoxLayout()
        aria_lbl = QLabel("ARIA")
        aria_lbl.setStyleSheet(f"font-size: 26px; font-weight: 900; color: {COLORS['teal']}; letter-spacing: 6px;")
        hdr.addWidget(aria_lbl)
        hdr.addStretch()
        lbl = QLabel("Child Profile Setup")
        lbl.setStyleSheet(f"font-size: 14px; color: {COLORS['text_light']};")
        hdr.addWidget(lbl)
        outer.addLayout(hdr)
        outer.addSpacing(16)

        # Scrollable main card
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content = QWidget()
        self._form_layout = QVBoxLayout(content)
        self._form_layout.setContentsMargins(0, 0, 20, 0)
        self._form_layout.setSpacing(16)
        self._build_form()
        scroll.setWidget(content)

        card = GlassCard(self, radius=24)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(50, 36, 50, 36)
        card_layout.addWidget(scroll)
        outer.addWidget(card)
        outer.addSpacing(16)

        # Save button
        save_btn = QPushButton("Save Child Profile & Continue →")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {COLORS['teal']}, stop:1 {COLORS['teal_deep']});
                color: white; border: none; border-radius: 16px;
                padding: 14px 40px; font-size: 15px; font-weight: 700;
            }}
            QPushButton:hover {{ background: {COLORS['teal_glow']}; }}
        """)
        save_btn.clicked.connect(self._save)
        outer.addWidget(save_btn, alignment=Qt.AlignRight)

    def _section(self, text):
        lbl = QLabel(text.upper())
        lbl.setStyleSheet(f"""
            font-size: 11px; font-weight: 700;
            color: {COLORS['teal_deep']}; letter-spacing: 2px;
            padding: 8px 0 4px 0;
        """)
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"color: {COLORS['border']}; background: {COLORS['border']};")
        line.setFixedHeight(1)
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(2)
        v.addWidget(lbl)
        v.addWidget(line)
        return w

    def _field_lbl(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {COLORS['text_light']}; letter-spacing: 0.8px;")
        return lbl

    def _build_form(self):
        fl = self._form_layout

        title = QLabel("Tell us about the child 🧒")
        title.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {COLORS['text']}; margin-bottom: 6px;")
        subtitle = QLabel("This helps ARIA personalize every interaction.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {COLORS['text_light']}; margin-bottom: 12px;")
        fl.addWidget(title)
        fl.addWidget(subtitle)

        # ── Basic Info
        fl.addWidget(self._section("Basic Information"))

        row1 = QHBoxLayout()
        name_w = QWidget()
        nv = QVBoxLayout(name_w)
        nv.setContentsMargins(0, 0, 0, 0)
        nv.addWidget(self._field_lbl("Child's First Name"))
        self._child_name = QLineEdit()
        self._child_name.setPlaceholderText("e.g. Ahmed")
        nv.addWidget(self._child_name)
        row1.addWidget(name_w)

        age_w = QWidget()
        age_w.setFixedWidth(120)
        av = QVBoxLayout(age_w)
        av.setContentsMargins(0, 0, 0, 0)
        av.addWidget(self._field_lbl("Age"))
        self._child_age = QSpinBox()
        self._child_age.setRange(2, 18)
        self._child_age.setValue(7)
        av.addWidget(self._child_age)
        row1.addWidget(age_w)
        fl.addLayout(row1)

        # ── Language
        fl.addWidget(self._section("Language & Communication"))
        fl.addWidget(self._field_lbl("Preferred Language"))
        self._lang_opt = OptionCard([
            ("en",  "English",        "🇬🇧"),
            ("ar",  "عربي\nMisry",   "🇪🇬"),
            ("de",  "Deutsch",        "🇩🇪"),
        ])
        self._lang_opt.set_value("en")
        fl.addWidget(self._lang_opt)

        fl.addWidget(self._field_lbl("Communication Level"))
        self._comm_opt = OptionCard([
            ("non_verbal",      "Non-Verbal\n(Buttons)",     "🖼️"),
            ("simple_words",    "Simple\nWords",             "💬"),
            ("short_sentences", "Short\nSentences",          "📝"),
            ("normal",          "Normal\nConversation",      "🗣️"),
        ])
        self._comm_opt.set_value("short_sentences")
        fl.addWidget(self._comm_opt)

        # ── Sensory Mode
        fl.addWidget(self._section("Sensory Preferences"))
        fl.addWidget(self._field_lbl("Sensory Mode"))
        self._sensory_opt = OptionCard([
            ("extra_low", "Extra Low\nStimulation",  "🌿"),
            ("calm",      "Calm Mode",               "😌"),
            ("normal",    "Normal Mode",             "🌟"),
        ])
        self._sensory_opt.set_value("calm")
        fl.addWidget(self._sensory_opt)

        # ── Favorite Topics
        fl.addWidget(self._section("Favorite Topics"))
        fl.addWidget(self._field_lbl("Select what the child loves (multiple OK)"))
        self._topics = TagSelector(
            ["Animals 🐾", "Space 🚀", "Cartoons 📺", "Cars 🚗",
             "Music 🎵", "Colors 🎨", "Numbers 🔢", "Nature 🌳"],
            color=COLORS["teal"]
        )
        fl.addWidget(self._topics)

        # ── Known Triggers
        fl.addWidget(self._section("Known Triggers"))
        fl.addWidget(self._field_lbl("Things that may upset the child"))
        self._triggers = TagSelector(
            ["Loud sounds 🔊", "Bright lights 💡", "Crowds 👥",
             "Sudden movement ⚡", "Certain words 🚫", "Waiting ⏳"],
            color="#D96B6B"
        )
        fl.addWidget(self._triggers)

        # ── Calming Methods
        fl.addWidget(self._section("Calming Methods"))
        fl.addWidget(self._field_lbl("What helps the child calm down?"))
        self._calming = TagSelector(
            ["Breathing 🌬️", "Counting 🔢", "Quiet time 🤫",
             "Parent hug 🤗", "Favorite story 📖", "Music off 🔇"],
            color=COLORS["lavender_mid"]
        )
        fl.addWidget(self._calming)

        fl.addSpacing(10)

    def resizeEvent(self, event):
        if hasattr(self, '_bg'):
            self._bg.resize(self.size())
        super().resizeEvent(event)

    def _save(self):
        name = self._child_name.text().strip()
        if not name:
            toast = ToastNotification(self, "Please enter the child's name.", kind="error")
            toast.move(self.width() // 2 - toast.width() // 2, 30)
            toast.show()
            return

        lang = self._lang_opt.value() or "en"
        comm = self._comm_opt.value() or "short_sentences"
        sensory = self._sensory_opt.value() or "calm"

        child_id = db.create_child(
            parent_id=self._parent_id,
            name=name,
            age=self._child_age.value(),
            language=lang,
            communication_level=comm,
            sensory_mode=sensory,
        )

        db.update_child_preferences(
            child_id,
            favorite_topics=[t.split(" ")[0] for t in self._topics.selected()],
            known_triggers=[t.split(" ")[0] for t in self._triggers.selected()],
            calming_methods=[t.split(" ")[0] for t in self._calming.selected()],
        )

        db.set_setting("active_child_id", child_id)
        self._child_id = child_id
        self.setup_complete.emit(child_id)
