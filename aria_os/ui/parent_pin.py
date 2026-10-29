"""Parent PIN screen — gates the Parent Dashboard."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QFrame
)
from PySide6.QtCore import Qt, Signal

from ui.components import C, GlassCard, MAIN_STYLE
from data import database as db


class ParentPIN(QWidget):
    close_requested = Signal()
    unlocked = Signal()

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.controller.enter_parent_mode()
        self.setStyleSheet(MAIN_STYLE)
        self._build()

    def _build(self):
        L = QVBoxLayout(self); L.setContentsMargins(60, 40, 60, 40); L.setSpacing(20)
        top = QHBoxLayout()
        back = QPushButton("← Cancel"); back.setMaximumWidth(140)
        back.setStyleSheet(f"""
            QPushButton {{ background: rgba(255,107,126,0.15); color: {C['alert']};
                border: 1.5px solid {C['alert']}; border-radius: 10px;
                padding: 9px 14px; font-size: 12px; }}
        """)
        back.clicked.connect(self._cancel)
        top.addWidget(back); top.addStretch()
        L.addLayout(top)

        L.addStretch()

        card = GlassCard(self, dark=True)
        cl = QVBoxLayout(card); cl.setContentsMargins(40, 36, 40, 36); cl.setSpacing(16)
        icon = QLabel("🔐"); icon.setAlignment(Qt.AlignCenter); icon.setStyleSheet("font-size: 64px;")
        title = QLabel("Parent Mode"); title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {C['cyan']};")
        sub = QLabel("Enter PIN to continue"); sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(f"font-size: 13px; color: {C['text_dim']};")

        self._pin_input = QLineEdit()
        self._pin_input.setEchoMode(QLineEdit.Password)
        self._pin_input.setMaxLength(8)
        self._pin_input.setAlignment(Qt.AlignCenter)
        self._pin_input.setMaximumWidth(220)
        self._pin_input.setStyleSheet(f"""
            font-size: 22px; letter-spacing: 6px;
            background: rgba(255,255,255,0.08);
            border: 2px solid rgba(0,229,255,0.4);
            border-radius: 14px; padding: 12px;
        """)
        self._pin_input.returnPressed.connect(self._check)
        self._error = QLabel("")
        self._error.setAlignment(Qt.AlignCenter)
        self._error.setStyleSheet(f"color: {C['alert']}; font-size: 12px;")

        unlock = QPushButton("Unlock")
        unlock.clicked.connect(self._check)

        cl.addWidget(icon); cl.addWidget(title); cl.addWidget(sub)
        cl.addWidget(self._pin_input, alignment=Qt.AlignCenter)
        cl.addWidget(self._error)
        cl.addWidget(unlock, alignment=Qt.AlignCenter)

        hint = QLabel("Default PIN: 1234")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet(f"color: {C['text_dim']}; font-size: 11px; padding-top: 6px;")
        cl.addWidget(hint)

        L.addWidget(card, alignment=Qt.AlignCenter)
        L.addStretch()

    def _check(self):
        pin = self._pin_input.text().strip()
        if db.verify_pin(pin):
            from ui.parent_dashboard import ParentDashboard
            dash = ParentDashboard(self.controller)
            dash.close_requested.connect(self._exit_dashboard)
            # Swap content in the same window
            self.parent().addWidget(dash)
            self.parent().setCurrentWidget(dash)
        else:
            self._error.setText("Wrong PIN. Try again.")
            self._pin_input.clear()

    def _exit_dashboard(self):
        self.controller.exit_parent_mode()
        self.close_requested.emit()

    def _cancel(self):
        self.controller.exit_parent_mode()
        self.close_requested.emit()
