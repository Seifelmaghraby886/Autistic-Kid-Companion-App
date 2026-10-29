"""
ARIA Parent Profile Setup
Beautiful first-time setup with animated steps.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QStackedWidget, QScrollArea,
    QFrame, QApplication, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QPainter, QColor, QLinearGradient, QPainterPath, QFont

from ui.components import GlassCard, ParticleBackground, ToastNotification
from ui.styles import MAIN_STYLE, COLORS
import database.db_manager as db


class StepIndicator(QWidget):
    def __init__(self, total_steps, parent=None):
        super().__init__(parent)
        self._total = total_steps
        self._current = 0
        self.setFixedHeight(50)

    def set_step(self, step):
        self._current = step
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        step_w = w // self._total
        cy = h // 2

        for i in range(self._total):
            cx = step_w * i + step_w // 2
            r = 14

            if i < self._current:
                # Done step
                painter.setBrush(QColor(COLORS["teal"]))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)
                painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
                painter.setPen(QColor("white"))
                painter.drawText(cx - r, cy - r, r * 2, r * 2, Qt.AlignCenter, "✓")
            elif i == self._current:
                # Current step
                painter.setBrush(QColor(COLORS["teal"]))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(cx - r - 3, cy - r - 3, (r + 3) * 2, (r + 3) * 2)
                painter.setBrush(QColor("white"))
                painter.drawEllipse(cx - r + 2, cy - r + 2, (r - 2) * 2, (r - 2) * 2)
                painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
                painter.setPen(QColor(COLORS["teal"]))
                painter.drawText(cx - r, cy - r, r * 2, r * 2, Qt.AlignCenter, str(i + 1))
            else:
                # Future step
                painter.setBrush(QColor(200, 215, 225))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)
                painter.setFont(QFont("Segoe UI", 9))
                painter.setPen(QColor(150, 165, 175))
                painter.drawText(cx - r, cy - r, r * 2, r * 2, Qt.AlignCenter, str(i + 1))

            # Connector line
            if i < self._total - 1:
                next_cx = step_w * (i + 1) + step_w // 2
                if i < self._current:
                    pen_color = QColor(COLORS["teal"])
                else:
                    pen_color = QColor(200, 215, 225)
                from PySide6.QtGui import QPen
                painter.setPen(QPen(pen_color, 2))
                painter.drawLine(cx + r + 2, cy, next_cx - r - 2, cy)


class FieldRow(QWidget):
    def __init__(self, label, placeholder="", is_password=False, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 12)
        layout.setSpacing(6)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {COLORS['text_light']}; letter-spacing: 1px;")
        layout.addWidget(lbl)

        self.field = QLineEdit()
        self.field.setPlaceholderText(placeholder)
        if is_password:
            self.field.setEchoMode(QLineEdit.Password)
        self.field.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(255,255,255,0.9);
                border: 2px solid rgba(56,184,176,0.2);
                border-radius: 12px;
                padding: 12px 16px;
                font-size: 14px;
                color: {COLORS['text']};
            }}
            QLineEdit:focus {{
                border-color: {COLORS['teal']};
                background: white;
            }}
        """)
        layout.addWidget(self.field)

    def value(self):
        return self.field.text().strip()

    def set_value(self, v):
        self.field.setText(v)


class ParentProfileSetup(QWidget):
    setup_complete = Signal(int)  # parent_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(MAIN_STYLE)
        self._parent_id = None
        self._build_ui()

    def _build_ui(self):
        # Background
        self._bg = ParticleBackground(self)
        self._bg.resize(self.size())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 40, 60, 40)
        layout.setSpacing(0)

        # Header
        header = QHBoxLayout()
        aria_lbl = QLabel("ARIA")
        aria_lbl.setStyleSheet(f"""
            font-size: 26px; font-weight: 900;
            color: {COLORS['teal']}; letter-spacing: 6px;
        """)
        header.addWidget(aria_lbl)
        header.addStretch()
        setup_lbl = QLabel("Parent Setup")
        setup_lbl.setStyleSheet(f"font-size: 14px; color: {COLORS['text_light']};")
        header.addWidget(setup_lbl)
        layout.addLayout(header)
        layout.addSpacing(20)

        # Step indicator
        self._step_indicator = StepIndicator(3, self)
        layout.addWidget(self._step_indicator)
        layout.addSpacing(24)

        # Main card
        card = GlassCard(self, radius=24)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(50, 40, 50, 40)

        # Stacked pages
        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_page1())
        self._stack.addWidget(self._build_page2())
        self._stack.addWidget(self._build_page3())
        card_layout.addWidget(self._stack)

        layout.addWidget(card)
        layout.addSpacing(20)

        # Navigation buttons
        nav = QHBoxLayout()
        self._back_btn = QPushButton("← Back")
        self._back_btn.setObjectName("SoftButton")
        self._back_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(56,184,176,0.10);
                color: {COLORS['teal_deep']};
                border: 1.5px solid {COLORS['teal']};
                border-radius: 14px; padding: 12px 28px;
                font-size: 14px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(56,184,176,0.20); }}
        """)
        self._back_btn.clicked.connect(self._go_back)
        self._back_btn.setVisible(False)

        self._next_btn = QPushButton("Continue →")
        self._next_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['teal']}, stop:1 {COLORS['teal_deep']});
                color: white; border: none; border-radius: 14px;
                padding: 12px 36px; font-size: 14px; font-weight: 700;
            }}
            QPushButton:hover {{ background: {COLORS['teal_glow']}; }}
        """)
        self._next_btn.clicked.connect(self._go_next)

        nav.addWidget(self._back_btn)
        nav.addStretch()
        nav.addWidget(self._next_btn)
        layout.addLayout(nav)

    def _build_page1(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(0)

        title = QLabel("Welcome to ARIA 👋")
        title.setStyleSheet(f"font-size: 26px; font-weight: 800; color: {COLORS['text']};")
        subtitle = QLabel("Let's set up your parent account to get started.")
        subtitle.setStyleSheet(f"font-size: 14px; color: {COLORS['text_light']}; margin-bottom: 28px;")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)

        self._name = FieldRow("Your Full Name", "e.g. Sarah Johnson")
        self._relationship = QWidget()
        rel_layout = QVBoxLayout(self._relationship)
        rel_layout.setContentsMargins(0, 0, 0, 12)
        rel_lbl = QLabel("Your Role")
        rel_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {COLORS['text_light']}; letter-spacing: 1px;")
        rel_layout.addWidget(rel_lbl)
        self._rel_combo = QComboBox()
        self._rel_combo.addItems(["Mother", "Father", "Therapist", "Caregiver", "Guardian"])
        rel_layout.addWidget(self._rel_combo)
        self._email = FieldRow("Email (optional)", "your@email.com")
        self._phone = FieldRow("Phone (optional)", "+1 555 0000")

        layout.addWidget(self._name)
        layout.addWidget(self._relationship)
        layout.addWidget(self._email)
        layout.addWidget(self._phone)
        layout.addStretch()
        return w

    def _build_page2(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        title = QLabel("Set Your PIN 🔐")
        title.setStyleSheet(f"font-size: 26px; font-weight: 800; color: {COLORS['text']};")
        subtitle = QLabel("Your PIN protects parent controls and settings.")
        subtitle.setStyleSheet(f"font-size: 14px; color: {COLORS['text_light']}; margin-bottom: 28px;")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)

        self._pin = FieldRow("Create PIN (4-6 digits)", "••••", is_password=True)
        self._pin.field.setMaxLength(6)
        self._pin_confirm = FieldRow("Confirm PIN", "••••", is_password=True)
        self._pin_confirm.field.setMaxLength(6)

        # Language
        lang_w = QWidget()
        lang_layout = QVBoxLayout(lang_w)
        lang_layout.setContentsMargins(0, 0, 0, 12)
        lang_lbl = QLabel("Preferred Report Language")
        lang_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {COLORS['text_light']}; letter-spacing: 1px;")
        lang_layout.addWidget(lang_lbl)
        self._report_lang = QComboBox()
        self._report_lang.addItems(["English", "العربية", "Deutsch"])
        lang_layout.addWidget(self._report_lang)

        layout.addWidget(self._pin)
        layout.addWidget(self._pin_confirm)
        layout.addWidget(lang_w)
        layout.addStretch()
        return w

    def _build_page3(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        title = QLabel("All Set! ✨")
        title.setStyleSheet(f"font-size: 26px; font-weight: 800; color: {COLORS['text']};")
        subtitle = QLabel("Your parent account is ready.\nNext, let's set up your child's profile.")
        subtitle.setStyleSheet(f"font-size: 14px; color: {COLORS['text_light']}; margin-bottom: 28px; line-height: 1.6;")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Summary card
        self._summary_card = GlassCard(w)
        sc_layout = QVBoxLayout(self._summary_card)
        self._summary_lbl = QLabel("")
        self._summary_lbl.setStyleSheet(f"font-size: 14px; color: {COLORS['text']}; line-height: 1.8;")
        self._summary_lbl.setWordWrap(True)
        sc_layout.addWidget(self._summary_lbl)
        layout.addWidget(self._summary_card)
        layout.addStretch()
        return w

    def resizeEvent(self, event):
        if hasattr(self, '_bg'):
            self._bg.resize(self.size())
        super().resizeEvent(event)

    def _go_next(self):
        current = self._stack.currentIndex()

        if current == 0:
            if not self._name.value():
                self._show_error("Please enter your name.")
                return
            self._stack.setCurrentIndex(1)
            self._step_indicator.set_step(1)
            self._back_btn.setVisible(True)

        elif current == 1:
            pin = self._pin.value()
            confirm = self._pin_confirm.value()
            if len(pin) < 4:
                self._show_error("PIN must be at least 4 digits.")
                return
            if pin != confirm:
                self._show_error("PINs don't match. Try again.")
                return
            if not pin.isdigit():
                self._show_error("PIN must contain only numbers.")
                return

            lang_map = {"English": "en", "العربية": "ar", "Deutsch": "de"}
            lang = lang_map.get(self._report_lang.currentText(), "en")

            # Save parent
            self._parent_id = db.create_parent(
                name=self._name.value(),
                relationship=self._rel_combo.currentText().lower(),
                pin=pin,
                email=self._email.value(),
                phone=self._phone.value(),
                report_lang=lang,
            )
            db.set_setting("active_parent_id", self._parent_id)

            # Update summary
            self._summary_lbl.setText(
                f"<b>Name:</b> {self._name.value()}<br>"
                f"<b>Role:</b> {self._rel_combo.currentText()}<br>"
                f"<b>Language:</b> {self._report_lang.currentText()}<br>"
                f"<b>Account ID:</b> #{self._parent_id}"
            )

            self._stack.setCurrentIndex(2)
            self._step_indicator.set_step(2)
            self._next_btn.setText("Add Child Profile →")

        elif current == 2:
            self.setup_complete.emit(self._parent_id)

    def _go_back(self):
        current = self._stack.currentIndex()
        if current > 0:
            self._stack.setCurrentIndex(current - 1)
            self._step_indicator.set_step(current - 1)
            if current == 1:
                self._back_btn.setVisible(False)
                self._next_btn.setText("Continue →")

    def _show_error(self, msg):
        toast = ToastNotification(self, msg, kind="error")
        toast.move(self.width() // 2 - toast.width() // 2, 30)
        toast.show()
