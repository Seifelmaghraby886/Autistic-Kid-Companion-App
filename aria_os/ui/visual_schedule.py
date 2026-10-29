"""Visual Schedule — NOW / NEXT / THEN."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal

from ui.components import C, GlassCard, MAIN_STYLE
from data import database as db


class VisualSchedule(QWidget):
    close_requested = Signal()

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setStyleSheet(MAIN_STYLE)
        self._build()

    def _build(self):
        L = QVBoxLayout(self); L.setContentsMargins(40, 22, 40, 22); L.setSpacing(16)

        top = QHBoxLayout()
        back = QPushButton("← Back"); back.setMaximumWidth(120)
        back.setStyleSheet(f"""
            QPushButton {{ background: rgba(0,191,168,0.12); color: {C['cyan']};
                border: 1.5px solid {C['teal']}; border-radius: 10px;
                padding: 9px 14px; font-size: 12px; }}
        """)
        back.clicked.connect(self.close_requested.emit)
        t = QLabel("📅  Today")
        t.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {C['cyan']};")
        top.addWidget(back); top.addSpacing(16); top.addWidget(t); top.addStretch()
        L.addLayout(top)

        items = db.list_schedule(self.controller.child_id)
        # Identify NOW / NEXT / THEN by first pending statuses
        pending = [i for i in items if i.get("status", "pending") != "done"]
        now_i  = pending[0] if len(pending) > 0 else None
        next_i = pending[1] if len(pending) > 1 else None
        then_i = pending[2] if len(pending) > 2 else None

        cards = QHBoxLayout(); cards.setSpacing(16)
        for label, item, color in [("NOW", now_i, C["cyan"]),
                                   ("NEXT", next_i, C["soft"]),
                                   ("THEN", then_i, C["purple"])]:
            card = GlassCard(self, dark=True)
            cl = QVBoxLayout(card); cl.setContentsMargins(20, 18, 20, 18)
            head = QLabel(label)
            head.setStyleSheet(
                f"font-size: 12px; font-weight: 800; color: {color}; letter-spacing: 3px;"
            )
            cl.addWidget(head)
            if item:
                icon = QLabel(item.get("icon", "📅"))
                icon.setStyleSheet("font-size: 56px;")
                icon.setAlignment(Qt.AlignCenter)
                title = QLabel(item.get("title", ""))
                title.setStyleSheet(
                    f"font-size: 20px; font-weight: 700; color: {C['text']}; padding-top: 8px;"
                )
                title.setAlignment(Qt.AlignCenter)
                time_lbl = QLabel(item.get("time", ""))
                time_lbl.setStyleSheet(f"font-size: 13px; color: {C['text_dim']};")
                time_lbl.setAlignment(Qt.AlignCenter)
                cl.addWidget(icon); cl.addWidget(title); cl.addWidget(time_lbl)
                if label == "NOW":
                    btn = QPushButton("✓ Mark done")
                    btn.clicked.connect(lambda checked, iid=item["id"]: self._mark_done(iid))
                    cl.addWidget(btn)
            else:
                empty = QLabel("—")
                empty.setStyleSheet(f"font-size: 36px; color: {C['text_dim']};")
                empty.setAlignment(Qt.AlignCenter)
                cl.addWidget(empty)
            cards.addWidget(card)
        L.addLayout(cards)
        L.addStretch()

    def _mark_done(self, item_id):
        db.update_schedule_status(item_id, "done")
        # Refresh
        for i in reversed(range(self.layout().count())):
            w = self.layout().itemAt(i).widget()
            if w: w.setParent(None)
        self._build_inner = True
        self._build()
