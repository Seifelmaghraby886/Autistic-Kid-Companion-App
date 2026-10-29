"""
ARIA Visual Schedule
Daily routine cards with child-friendly design and completion tracking.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPainter, QColor, QPainterPath, QFont, QLinearGradient

from ui.components import GlassCard, ARIAFaceWidget, ParticleBackground
from ui.styles import MAIN_STYLE, COLORS
import database.db_manager as db


SCHEDULES = {
    "en": [
        ("🌅", "Wake Up",      "Good morning!",         "#F0C040"),
        ("🚿", "Wash Face",    "Fresh and clean",        "#38B8B0"),
        ("🪥", "Brush Teeth",  "Shiny teeth!",           "#4CAF90"),
        ("🍳", "Breakfast",    "Yummy food",             "#E8956D"),
        ("🎒", "Get Ready",    "School time!",           "#6B9FD4"),
        ("📚", "School",       "Learning new things",    "#9B8EC4"),
        ("🍎", "Lunch",        "Midday meal",            "#E8956D"),
        ("😴", "Rest Time",    "Rest and relax",         "#A8B8D0"),
        ("🎮", "Play Time",    "Fun and games",          "#4CAF90"),
        ("🍽️", "Dinner",       "Family meal",            "#E8956D"),
        ("🛁", "Bath Time",    "Clean and fresh",        "#38B8B0"),
        ("🌙", "Bedtime",      "Sweet dreams",           "#9B8EC4"),
    ],
    "ar": [
        ("🌅", "اصحى",         "صباح الخير!",            "#F0C040"),
        ("🚿", "اغسل وشك",     "نضيف وشاطر",             "#38B8B0"),
        ("🪥", "اغسل سنانك",   "أسنان لامعة!",           "#4CAF90"),
        ("🍳", "الفطار",        "أكل لذيذ",               "#E8956D"),
        ("🎒", "استعد",         "جاهز للمدرسة!",          "#6B9FD4"),
        ("📚", "المدرسة",       "نتعلم حاجات جديدة",      "#9B8EC4"),
        ("🍎", "الغدا",         "وجبة الظهر",              "#E8956D"),
        ("😴", "راحة",          "استرخي وارتاح",           "#A8B8D0"),
        ("🎮", "لعب",           "فرفشة وألعاب",            "#4CAF90"),
        ("🍽️", "العشا",         "وجبة العيلة",             "#E8956D"),
        ("🛁", "الاستحمام",     "نضيف ومنعش",             "#38B8B0"),
        ("🌙", "النوم",         "أحلام حلوة",              "#9B8EC4"),
    ],
    "de": [
        ("🌅", "Aufwachen",     "Guten Morgen!",          "#F0C040"),
        ("🚿", "Gesicht waschen","Sauber und frisch",      "#38B8B0"),
        ("🪥", "Zähne putzen",  "Glänzende Zähne!",       "#4CAF90"),
        ("🍳", "Frühstück",     "Leckeres Essen",         "#E8956D"),
        ("🎒", "Fertig machen", "Schulzeit!",             "#6B9FD4"),
        ("📚", "Schule",        "Neues lernen",           "#9B8EC4"),
        ("🍎", "Mittagessen",   "Mittagsmahlzeit",        "#E8956D"),
        ("😴", "Pause",         "Ausruhen und entspannen","#A8B8D0"),
        ("🎮", "Spielzeit",     "Spaß und Spiele",        "#4CAF90"),
        ("🍽️", "Abendessen",    "Familienessen",          "#E8956D"),
        ("🛁", "Badezeit",      "Sauber und frisch",      "#38B8B0"),
        ("🌙", "Schlafenszeit", "Süße Träume",            "#9B8EC4"),
    ],
}


class ScheduleCard(QWidget):
    completed = Signal(int, bool)

    def __init__(self, index, icon, title, subtitle, color, done=False, parent=None):
        super().__init__(parent)
        self._index = index
        self._color = color
        self._done = done
        self.setFixedHeight(80)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(14)

        # Icon circle
        self._icon_lbl = QLabel(icon)
        self._icon_lbl.setFixedSize(54, 54)
        self._icon_lbl.setAlignment(Qt.AlignCenter)
        self._icon_lbl.setStyleSheet(f"""
            font-size: 26px;
            background: {color}22;
            border: 2px solid {color}66;
            border-radius: 27px;
        """)

        # Text
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self._title_lbl = QLabel(title)
        self._title_lbl.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {COLORS['text']};")
        self._sub_lbl = QLabel(subtitle)
        self._sub_lbl.setStyleSheet(f"font-size: 12px; color: {COLORS['text_light']};")
        text_col.addWidget(self._title_lbl)
        text_col.addWidget(self._sub_lbl)

        # Check button
        self._check_btn = QPushButton()
        self._check_btn.setFixedSize(40, 40)
        self._check_btn.setCheckable(True)
        self._check_btn.setChecked(done)
        self._check_btn.clicked.connect(self._on_check)
        self._update_check_style()

        layout.addWidget(self._icon_lbl)
        layout.addLayout(text_col, 1)
        layout.addWidget(self._check_btn)

        self._update_done_style()

    def _on_check(self, checked):
        self._done = checked
        self._update_check_style()
        self._update_done_style()
        self.completed.emit(self._index, checked)

    def _update_check_style(self):
        if self._check_btn.isChecked():
            self._check_btn.setText("✓")
            self._check_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {self._color};
                    color: white; border: none;
                    border-radius: 20px; font-size: 16px; font-weight: 700;
                }}
            """)
        else:
            self._check_btn.setText("")
            self._check_btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(56,184,176,0.08);
                    border: 2px solid rgba(56,184,176,0.3);
                    border-radius: 20px;
                }}
                QPushButton:hover {{
                    background: rgba(56,184,176,0.18);
                    border-color: {COLORS['teal']};
                }}
            """)

    def _update_done_style(self):
        if self._done:
            self.setStyleSheet(f"""
                background: {self._color}15;
                border: 1.5px solid {self._color}44;
                border-radius: 16px;
            """)
            self._title_lbl.setStyleSheet(
                f"font-size: 15px; font-weight: 700; color: {self._color}; text-decoration: line-through;"
            )
        else:
            self.setStyleSheet("""
                background: rgba(255,255,255,0.8);
                border: 1px solid rgba(56,184,176,0.2);
                border-radius: 16px;
            """)
            self._title_lbl.setStyleSheet(
                f"font-size: 15px; font-weight: 700; color: {COLORS['text']};"
            )


class VisualScheduleScreen(QWidget):
    go_back = Signal()

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._child_data = db.get_child(child_id) or {}
        self._completed = set()
        self.setStyleSheet(MAIN_STYLE)
        self._build_ui()

    def _build_ui(self):
        self._bg = ParticleBackground(self)
        self._bg.lower()

        main = QVBoxLayout(self)
        main.setContentsMargins(36, 28, 36, 28)
        main.setSpacing(16)

        # Header
        hdr = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(56,184,176,0.10); color: {COLORS['teal_deep']};
                border: 1.5px solid {COLORS['teal']}; border-radius: 10px;
                padding: 8px 16px; font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(56,184,176,0.22); }}
        """)
        back_btn.clicked.connect(self.go_back.emit)

        lang = self._child_data.get("language", "en")
        titles = {"en": "📅 My Daily Schedule", "ar": "📅 روتين يومي", "de": "📅 Mein Tagesplan"}
        title = QLabel(titles.get(lang, titles["en"]))
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {COLORS['text']};")
        hdr.addWidget(back_btn)
        hdr.addSpacing(20)
        hdr.addWidget(title)
        hdr.addStretch()
        main.addLayout(hdr)

        body = QHBoxLayout()
        body.setSpacing(20)

        # ── Left: ARIA + progress
        left = QVBoxLayout()
        left.setSpacing(14)

        face_card = GlassCard(self, radius=22)
        fc = QVBoxLayout(face_card)
        fc.setContentsMargins(20, 20, 20, 20)
        fc.setAlignment(Qt.AlignCenter)

        self._aria_face = ARIAFaceWidget(size=130)
        fc.addWidget(self._aria_face, alignment=Qt.AlignCenter)

        self._aria_msg = QLabel("Let's check your day! 📅")
        self._aria_msg.setAlignment(Qt.AlignCenter)
        self._aria_msg.setWordWrap(True)
        self._aria_msg.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {COLORS['teal_deep']}; padding: 8px;")
        fc.addWidget(self._aria_msg)
        left.addWidget(face_card)

        # Progress card
        prog_card = GlassCard(self, radius=20)
        pl = QVBoxLayout(prog_card)
        pl.setContentsMargins(18, 14, 18, 14)

        prog_title = QLabel("TODAY'S PROGRESS")
        prog_title.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {COLORS['teal_deep']}; letter-spacing: 2px;")
        pl.addWidget(prog_title)

        self._prog_lbl = QLabel("0 / 12 completed")
        self._prog_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {COLORS['teal']};")
        pl.addWidget(self._prog_lbl)

        from PySide6.QtWidgets import QProgressBar
        self._prog_bar = QProgressBar()
        self._prog_bar.setRange(0, 12)
        self._prog_bar.setValue(0)
        self._prog_bar.setTextVisible(False)
        self._prog_bar.setFixedHeight(10)
        pl.addWidget(self._prog_bar)

        left.addWidget(prog_card)
        left.addStretch()
        body.addLayout(left)

        # ── Right: Schedule cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        schedule_w = QWidget()
        schedule_w.setStyleSheet("background: transparent;")
        schedule_layout = QVBoxLayout(schedule_w)
        schedule_layout.setContentsMargins(0, 0, 8, 0)
        schedule_layout.setSpacing(8)

        schedule_data = SCHEDULES.get(lang, SCHEDULES["en"])
        self._cards = []
        for i, (icon, title_text, sub, color) in enumerate(schedule_data):
            card = ScheduleCard(i, icon, title_text, sub, color, parent=self)
            card.completed.connect(self._on_completed)
            schedule_layout.addWidget(card)
            self._cards.append(card)

        schedule_layout.addStretch()
        scroll.setWidget(schedule_w)
        body.addWidget(scroll, 1)
        main.addLayout(body, 1)

    def _on_completed(self, index, done):
        if done:
            self._completed.add(index)
        else:
            self._completed.discard(index)

        count = len(self._completed)
        total = len(self._cards)
        self._prog_lbl.setText(f"{count} / {total} completed")
        self._prog_bar.setValue(count)

        lang = self._child_data.get("language", "en")
        if count == total:
            msgs = {"en": "🎉 You finished everything! Amazing work!", "ar": "🎉 أنهيت كل حاجة! رائع!", "de": "🎉 Du hast alles geschafft! Fantastisch!"}
            self._aria_msg.setText(msgs.get(lang, msgs["en"]))
            self._aria_face.set_expression("happy")
        elif count > 0:
            msgs = {"en": f"Great! {count} down, keep going! 💪", "ar": f"رائع! {count} خلصت، كمل! 💪", "de": f"Super! {count} erledigt, weiter so! 💪"}
            self._aria_msg.setText(msgs.get(lang, msgs["en"]))
            self._aria_face.set_expression("calm")

    def resizeEvent(self, event):
        if hasattr(self, '_bg'):
            self._bg.resize(self.size())
        super().resizeEvent(event)
