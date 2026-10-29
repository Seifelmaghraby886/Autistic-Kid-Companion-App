"""
ARIA Parent Dashboard
PIN-protected dashboard with emotion logs, session reports, charts, AI insights.
"""

from collections import Counter
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QLineEdit, QDialog, QGridLayout,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QStackedLayout
)
from PySide6.QtCore import Qt, Signal, QTimer, QRectF
from PySide6.QtGui import QPainter, QColor, QFont, QPainterPath, QLinearGradient, QPen

from ui.components import GlassCard
from ui.animated_bg import MeshBackground
from ui.styles import MAIN_STYLE, COLORS, get_emotion_color
import database.db_manager as db


# ══════════════════════════════════════════════════════════════
#  PIN Dialog
# ══════════════════════════════════════════════════════════════
class PINDialog(QDialog):
    def __init__(self, parent_id, parent=None):
        super().__init__(parent)
        self._parent_id = parent_id
        self._verified = False
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(380, 300)
        self._build_ui()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)

        card = GlassCard(self, radius=24)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(36, 28, 36, 28)
        layout.setSpacing(14)

        title = QLabel("🔐 Parent Access")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {COLORS['text']};")
        layout.addWidget(title)

        sub = QLabel("Enter your PIN")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(f"font-size: 13px; color: {COLORS['text_light']};")
        layout.addWidget(sub)

        self._pin_input = QLineEdit()
        self._pin_input.setEchoMode(QLineEdit.Password)
        self._pin_input.setMaxLength(6)
        self._pin_input.setPlaceholderText("••••")
        self._pin_input.setAlignment(Qt.AlignCenter)
        self._pin_input.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(255,255,255,0.95);
                border: 2px solid rgba(0,191,168,0.3);
                border-radius: 14px; padding: 14px;
                font-size: 22px; color: {COLORS['text']};
                letter-spacing: 8px;
            }}
            QLineEdit:focus {{ border-color: {COLORS['teal']}; }}
        """)
        self._pin_input.returnPressed.connect(self._check_pin)
        layout.addWidget(self._pin_input)

        self._error_lbl = QLabel("")
        self._error_lbl.setAlignment(Qt.AlignCenter)
        self._error_lbl.setStyleSheet(f"font-size: 12px; color: {COLORS['danger']};")
        layout.addWidget(self._error_lbl)

        btn_row = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0,191,168,0.10); color: {COLORS['text_light']};
                border: 1px solid rgba(0,191,168,0.25); border-radius: 12px;
                padding: 10px 18px;
            }}
            QPushButton:hover {{ background: rgba(0,191,168,0.22); }}
        """)
        cancel.clicked.connect(self.reject)

        unlock_btn = QPushButton("🔓  Unlock")
        unlock_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {COLORS['teal']}, stop:1 {COLORS['teal_deep']});
                color: white; border: none; border-radius: 12px;
                padding: 10px 22px; font-weight: 700;
            }}
        """)
        unlock_btn.clicked.connect(self._check_pin)

        btn_row.addWidget(cancel)
        btn_row.addStretch()
        btn_row.addWidget(unlock_btn)
        layout.addLayout(btn_row)

        main.addWidget(card)
        self._pin_input.setFocus()

    def _check_pin(self):
        pin = self._pin_input.text().strip()
        if not pin:
            self._error_lbl.setText("Enter a PIN.")
            return
        if db.verify_parent_pin(self._parent_id, pin):
            self._verified = True
            self.accept()
        else:
            self._error_lbl.setText("❌ Wrong PIN. Try again.")
            self._pin_input.clear()
            self._pin_input.setFocus()

    def is_verified(self):
        return self._verified


# ══════════════════════════════════════════════════════════════
#  Donut chart for emotion distribution
# ══════════════════════════════════════════════════════════════
class EmotionDonutChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 220)
        self._data = {}

    def set_data(self, data: dict):
        self._data = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        size = min(w, h) - 30
        x = (w - size) / 2
        y = (h - size) / 2

        if not self._data or sum(self._data.values()) == 0:
            painter.setPen(QColor(COLORS["text_light"]))
            painter.setFont(QFont("Segoe UI", 11))
            painter.drawText(self.rect(), Qt.AlignCenter, "No data yet")
            return

        total = sum(self._data.values())
        start_angle = 90 * 16
        for emotion, count in sorted(self._data.items(), key=lambda x: -x[1]):
            span = int((count / total) * 360 * 16)
            color = QColor(get_emotion_color(emotion))
            painter.setBrush(color)
            painter.setPen(QPen(QColor("white"), 3))
            painter.drawPie(QRectF(x, y, size, size), start_angle, span)
            start_angle += span

        # Center hole
        hole_size = size * 0.55
        hx = (w - hole_size) / 2
        hy = (h - hole_size) / 2
        painter.setBrush(QColor("white"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(hx, hy, hole_size, hole_size))

        # Center text
        dominant = max(self._data, key=self._data.get)
        painter.setPen(QColor(get_emotion_color(dominant)))
        painter.setFont(QFont("Segoe UI", 14, QFont.Bold))
        painter.drawText(self.rect(), Qt.AlignCenter, dominant.title())
        painter.setFont(QFont("Segoe UI", 10))
        painter.setPen(QColor(COLORS["text_light"]))
        painter.drawText(QRectF(0, h / 2 + 18, w, 20), Qt.AlignCenter,
                         f"{total} events")


# ══════════════════════════════════════════════════════════════
#  Parent Dashboard Screen
# ══════════════════════════════════════════════════════════════
class ParentDashboardScreen(QWidget):
    go_back = Signal()

    def __init__(self, child_id, parent_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._parent_id = parent_id
        self._child_data = db.get_child(child_id) or {}
        self._authenticated = False
        self.setStyleSheet(MAIN_STYLE)
        self._build_ui()

    def _build_ui(self):
        # Background
        self._bg = MeshBackground(self, intensity=0.5)
        self._bg.lower()

        # Use stacked layout: lock screen → dashboard
        self._stack = QStackedLayout(self)
        self._stack.setContentsMargins(0, 0, 0, 0)

        self._lock_widget = self._build_lock_screen()
        self._dashboard_widget = QWidget()  # Built lazily after auth
        self._dashboard_built = False

        self._stack.addWidget(self._lock_widget)
        self._stack.addWidget(self._dashboard_widget)
        self._stack.setCurrentWidget(self._lock_widget)

        # Try unlock immediately
        QTimer.singleShot(100, self._try_unlock)

    def _build_lock_screen(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(14)

        icon = QLabel("🔐")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 80px; padding: 20px;")
        title = QLabel("Parent Dashboard")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"font-size: 30px; font-weight: 800; color: {COLORS['text']};")
        sub = QLabel("Protected with your PIN")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(f"font-size: 16px; color: {COLORS['text_light']};")

        unlock_btn = QPushButton("🔑  Enter PIN")
        unlock_btn.setFixedWidth(280)
        unlock_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {COLORS['teal']}, stop:1 {COLORS['teal_deep']});
                color: white; border: none; border-radius: 18px;
                padding: 16px 32px; font-size: 16px; font-weight: 700;
            }}
            QPushButton:hover {{ background: {COLORS['teal_glow']}; }}
        """)
        unlock_btn.clicked.connect(self._try_unlock)

        back_btn = QPushButton("← Back")
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {COLORS['text_light']};
                border: 1px solid rgba(0,0,0,0.1); border-radius: 12px;
                padding: 8px 18px; font-size: 13px;
            }}
            QPushButton:hover {{ color: {COLORS['teal']}; }}
        """)
        back_btn.clicked.connect(self.go_back.emit)

        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addWidget(sub)
        layout.addSpacing(16)
        layout.addWidget(unlock_btn, alignment=Qt.AlignCenter)
        layout.addWidget(back_btn, alignment=Qt.AlignCenter)
        return w

    def _try_unlock(self):
        dialog = PINDialog(self._parent_id, self)
        if dialog.exec() == QDialog.Accepted and dialog.is_verified():
            self._authenticated = True
            self._build_dashboard()
            self._stack.setCurrentWidget(self._dashboard_widget)

    def _build_dashboard(self):
        if self._dashboard_built:
            return

        layout = QVBoxLayout(self._dashboard_widget)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(14)

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
        title = QLabel(f"👨‍👩‍👧 Dashboard — {self._child_data.get('name', 'Child')}")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {COLORS['text']};")
        hdr.addWidget(back_btn)
        hdr.addSpacing(20)
        hdr.addWidget(title)
        hdr.addStretch()
        layout.addLayout(hdr)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self._build_overview_tab(), "📊 Overview")
        tabs.addTab(self._build_emotions_tab(), "😊 Emotions")
        tabs.addTab(self._build_chat_tab(), "💬 Chat Log")
        tabs.addTab(self._build_sessions_tab(), "📅 Sessions")
        tabs.addTab(self._build_export_tab(), "📤 Export")
        layout.addWidget(tabs, 1)

        self._dashboard_built = True

    # ─── Tabs ─────────────────────────────────────────────────
    def _build_overview_tab(self):
        w = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # Today summary
        today_summary = db.get_today_emotion_summary(self._child_id)
        all_logs = db.get_emotion_logs(self._child_id, 1000)
        all_summary = Counter(l.get("emotion", "neutral") for l in all_logs)

        dominant = max(today_summary, key=today_summary.get) if today_summary else "calm"
        chats = db.get_chat_logs(self._child_id, 1000)
        sessions = db.get_sessions_for_child(self._child_id, 100)

        # Stats grid
        stats = [
            ("😊", "Today's Mood",       dominant.title(),
             get_emotion_color(dominant)),
            ("📊", "Today Events",       str(sum(today_summary.values())),
             COLORS["teal"]),
            ("💬", "Chat Messages",      str(len(chats)),
             COLORS["teal_deep"]),
            ("📅", "Total Sessions",     str(len(sessions)),
             "#B388FF"),
            ("🌿", "Comfort Events",     str(sum(today_summary.get(k, 0)
                                                 for k in ["sadness", "fear", "anger"])),
             "#6B9FE8"),
            ("⭐", "Activities",         str(len(all_logs)),
             "#FFD700"),
        ]
        grid = QGridLayout()
        grid.setSpacing(12)
        for i, (icon, label, value, color) in enumerate(stats):
            card = self._stat_card(icon, label, value, color)
            grid.addWidget(card, i // 3, i % 3)
        layout.addLayout(grid)

        # Donut chart
        chart_card = GlassCard(content, radius=20)
        cl = QVBoxLayout(chart_card)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.addWidget(self._section_label("EMOTION DISTRIBUTION (ALL TIME)"))
        donut = EmotionDonutChart()
        donut.set_data(dict(all_summary))
        cl.addWidget(donut, alignment=Qt.AlignCenter)
        layout.addWidget(chart_card)

        # AI Insights button
        insights_btn = QPushButton("💡  Generate AI Insights")
        insights_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #00BFA8, stop:0.5 #00E5FF, stop:1 #B388FF);
                color: white; border: none; border-radius: 14px;
                padding: 13px 28px; font-size: 14px; font-weight: 700;
            }}
        """)
        insights_btn.clicked.connect(self._open_insights)
        layout.addWidget(insights_btn, alignment=Qt.AlignCenter)
        layout.addStretch()

        scroll.setWidget(content)
        wl = QVBoxLayout(w)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.addWidget(scroll)
        return w

    def _build_emotions_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        layout.addWidget(self._section_label("RECENT EMOTION LOGS"))

        table = QTableWidget()
        logs = db.get_emotion_logs(self._child_id, 100)
        table.setRowCount(len(logs))
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Time", "Emotion", "Confidence", "Source", "Action"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)

        for i, log in enumerate(logs):
            t = log.get("timestamp", "")[:19]
            em = log.get("emotion", "")
            conf = f"{log.get('confidence', 0)*100:.0f}%"
            src = log.get("source", "")
            act = log.get("action_taken", "")
            for j, val in enumerate([t, em, conf, src, act]):
                item = QTableWidgetItem(str(val))
                if j == 1:  # color the emotion cell
                    item.setForeground(QColor(get_emotion_color(em)))
                table.setItem(i, j, item)

        layout.addWidget(table, 1)
        return w

    def _build_chat_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        layout.addWidget(self._section_label("RECENT CONVERSATIONS"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        cl = QVBoxLayout(content)
        cl.setSpacing(8)

        chats = db.get_chat_logs(self._child_id, 50)
        if not chats:
            empty = QLabel("No chat history yet.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(f"font-size: 14px; color: {COLORS['text_light']}; padding: 40px;")
            cl.addWidget(empty)
        else:
            for chat in chats:
                card = self._chat_log_card(chat)
                cl.addWidget(card)
        cl.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)
        return w

    def _build_sessions_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        layout.addWidget(self._section_label("PAST SESSIONS"))

        sessions = db.get_sessions_for_child(self._child_id, 50)
        if not sessions:
            empty = QLabel("No sessions recorded yet.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(f"font-size: 14px; color: {COLORS['text_light']}; padding: 40px;")
            layout.addWidget(empty)
            return w

        table = QTableWidget()
        table.setRowCount(len(sessions))
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Start", "End", "Dominant", "Comfort"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)

        for i, s in enumerate(sessions):
            for j, val in enumerate([
                s.get("start_time", "")[:19],
                s.get("end_time", "")[:19] if s.get("end_time") else "(active)",
                s.get("dominant_emotion", "—"),
                str(s.get("comfort_mode_count", 0)),
            ]):
                table.setItem(i, j, QTableWidgetItem(str(val)))
        layout.addWidget(table, 1)
        return w

    def _build_export_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        layout.addWidget(self._section_label("DATA MANAGEMENT"))

        export_btn = QPushButton("📤  Export All Data (JSON)")
        export_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0,191,168,0.15); color: {COLORS['teal_deep']};
                border: 1.5px solid {COLORS['teal']}; border-radius: 12px;
                padding: 12px 24px; font-size: 14px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(0,191,168,0.30); }}
        """)
        export_btn.clicked.connect(self._export_data)
        layout.addWidget(export_btn, alignment=Qt.AlignLeft)

        report_btn = QPushButton("📊  Generate Weekly Report (PDF)")
        report_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(179,136,255,0.15); color: #6B4EBF;
                border: 1.5px solid #B388FF; border-radius: 12px;
                padding: 12px 24px; font-size: 14px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(179,136,255,0.30); }}
        """)
        report_btn.clicked.connect(self._generate_report)
        layout.addWidget(report_btn, alignment=Qt.AlignLeft)

        # ─── Danger zone ────────────────────────────────────────
        danger_label = QLabel("DANGER ZONE")
        danger_label.setStyleSheet(
            f"font-size: 11px; font-weight: 800; letter-spacing: 2px;"
            f"color: #C04055; padding-top: 14px;"
        )
        layout.addWidget(danger_label)

        clear_btn = QPushButton("🧹  Clear Activity History")
        clear_btn.setToolTip(
            "Erases chats, emotion logs, and sessions. "
            "Keeps the profile, preferences, and device settings."
        )
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,170,90,0.14); color: #B36A1A;
                border: 1.5px solid rgba(255,170,90,0.5); border-radius: 12px;
                padding: 12px 24px; font-size: 14px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(255,170,90,0.28); }}
        """)
        clear_btn.clicked.connect(self._clear_history)
        layout.addWidget(clear_btn, alignment=Qt.AlignLeft)

        delete_btn = QPushButton("❌  Delete Entire Child Profile")
        delete_btn.setToolTip(
            "Removes the child and ALL of their data. "
            "Requires re-entering the parent PIN. Cannot be undone."
        )
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(220,60,80,0.14); color: #C04055;
                border: 1.5px solid rgba(220,60,80,0.55); border-radius: 12px;
                padding: 12px 24px; font-size: 14px; font-weight: 700;
            }}
            QPushButton:hover {{ background: rgba(220,60,80,0.28); }}
        """)
        delete_btn.clicked.connect(self._delete_profile)
        layout.addWidget(delete_btn, alignment=Qt.AlignLeft)
        layout.addStretch()
        return w

    # ─── Helpers ──────────────────────────────────────────────
    def _stat_card(self, icon, label, value, color):
        card = GlassCard(self, radius=18)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(4)

        top = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"font-size: 26px; background: transparent;")
        top.addWidget(icon_lbl)
        top.addStretch()
        layout.addLayout(top)

        value_lbl = QLabel(value)
        value_lbl.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {color}; background: transparent;")
        layout.addWidget(value_lbl)

        label_lbl = QLabel(label)
        label_lbl.setStyleSheet(f"font-size: 11px; color: {COLORS['text_light']}; font-weight: 600; letter-spacing: 1px; background: transparent;")
        layout.addWidget(label_lbl)
        return card

    def _section_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {COLORS['teal_deep']}; letter-spacing: 2px;")
        return lbl

    def _chat_log_card(self, chat):
        card = GlassCard(self, radius=14)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(16, 12, 16, 12)
        cl.setSpacing(4)

        ts = chat.get("timestamp", "")[:19]
        ts_lbl = QLabel(ts)
        ts_lbl.setStyleSheet(f"font-size: 10px; color: {COLORS['text_light']}; font-weight: 600;")
        cl.addWidget(ts_lbl)

        if chat.get("user_message"):
            user_lbl = QLabel(f"👤 {chat['user_message']}")
            user_lbl.setWordWrap(True)
            user_lbl.setStyleSheet(f"font-size: 13px; color: {COLORS['text']}; padding: 4px 0;")
            cl.addWidget(user_lbl)

        if chat.get("aria_reply"):
            aria_lbl = QLabel(f"🤖 {chat['aria_reply']}")
            aria_lbl.setWordWrap(True)
            aria_lbl.setStyleSheet(f"font-size: 13px; color: {COLORS['teal_deep']}; padding: 4px 0;")
            cl.addWidget(aria_lbl)

        meta = []
        em = chat.get("detected_emotion")
        if em and em != "neutral":
            meta.append(f"emotion: {em}")
        if chat.get("comfort_mode"):
            meta.append("🌿 comfort mode")
        if meta:
            meta_lbl = QLabel(" · ".join(meta))
            meta_lbl.setStyleSheet(f"font-size: 10px; color: {COLORS['text_light']};")
            cl.addWidget(meta_lbl)
        return card

    def _open_insights(self):
        # Open AI insights dialog
        try:
            from ui.ai_insights import AIInsightsScreen
            dlg = QDialog(self)
            dlg.setWindowTitle(f"AI Insights — {self._child_data.get('name', '')}")
            dlg.resize(900, 700)
            screen = AIInsightsScreen(self._child_id, dlg)
            screen.go_back.connect(dlg.close)
            l = QVBoxLayout(dlg)
            l.setContentsMargins(0, 0, 0, 0)
            l.addWidget(screen)
            dlg.exec()
        except Exception as e:
            QMessageBox.warning(self, "Insights", f"Couldn't open: {e}")

    def _export_data(self):
        try:
            import json, time
            from PySide6.QtWidgets import QFileDialog
            data = {
                "child": db.get_child(self._child_id),
                "preferences": db.get_child_preferences(self._child_id),
                "emotion_logs": db.get_emotion_logs(self._child_id, 1000),
                "chat_logs": db.get_chat_logs(self._child_id, 1000),
                "sessions": db.get_sessions_for_child(self._child_id, 100),
                "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            default_name = f"aria_export_{self._child_data.get('name','child')}_{time.strftime('%Y%m%d')}.json"
            path, _ = QFileDialog.getSaveFileName(
                self, "Export Data", default_name, "JSON Files (*.json)"
            )
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                QMessageBox.information(self, "Exported", f"Saved to:\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "Export error", str(e))

    def _generate_report(self):
        try:
            from PySide6.QtWidgets import QFileDialog
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            import time

            default_name = f"aria_report_{self._child_data.get('name','child')}_{time.strftime('%Y%m%d')}.pdf"
            path, _ = QFileDialog.getSaveFileName(
                self, "Save Report", default_name, "PDF Files (*.pdf)"
            )
            if not path:
                return

            c = canvas.Canvas(path, pagesize=letter)
            w, h = letter
            y = h - 50
            c.setFont("Helvetica-Bold", 20)
            c.drawString(50, y, f"ARIA Weekly Report — {self._child_data.get('name', '')}")
            y -= 30
            c.setFont("Helvetica", 12)
            c.drawString(50, y, time.strftime("%Y-%m-%d %H:%M"))
            y -= 40

            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, y, "Summary")
            y -= 20
            c.setFont("Helvetica", 11)
            logs = db.get_emotion_logs(self._child_id, 500)
            chats = db.get_chat_logs(self._child_id, 200)
            sessions = db.get_sessions_for_child(self._child_id, 50)
            for line in [
                f"Total emotion events: {len(logs)}",
                f"Chat messages: {len(chats)}",
                f"Sessions: {len(sessions)}",
            ]:
                c.drawString(70, y, line); y -= 18
            y -= 10

            counts = Counter(l.get("emotion", "neutral") for l in logs)
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, y, "Emotion Frequency"); y -= 20
            c.setFont("Helvetica", 11)
            for em, ct in counts.most_common():
                c.drawString(70, y, f"  {em.title()}: {ct}"); y -= 16

            c.save()
            QMessageBox.information(self, "Report saved", f"PDF saved to:\n{path}")
        except ImportError:
            QMessageBox.warning(self, "PDF", "reportlab not installed.\nRun: pip install reportlab")
        except Exception as e:
            QMessageBox.warning(self, "Report error", str(e))

    # ─── Danger-zone actions ──────────────────────────────────
    def _clear_history(self):
        name = self._child_data.get("name", "this child")
        ret = QMessageBox.question(
            self, "Clear activity history",
            f"This will erase chats, emotion logs, and sessions for {name}.\n\n"
            "The profile, preferences, and device settings will be kept.\n\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if ret != QMessageBox.Yes:
            return
        try:
            db.clear_child_history(self._child_id)
            self._toast(f"History cleared for {name}.", kind="success")
        except Exception as e:
            self._toast(f"Couldn't clear: {e}", kind="error")

    def _delete_profile(self):
        name = self._child_data.get("name", "this child")
        # 1) Plain "are you sure?" gate
        ret = QMessageBox.warning(
            self, "Delete entire profile",
            f"This will permanently delete {name} and ALL of their data:\n\n"
            "  • profile (name, age, language, communication level)\n"
            "  • preferences and AI memory\n"
            "  • device and voice settings\n"
            "  • chat logs, emotion logs, and session history\n\n"
            "This cannot be undone.\n\nContinue?",
            QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel
        )
        if ret != QMessageBox.Yes:
            return

        # 2) PIN re-prompt — same gate that protected dashboard entry
        pin_dialog = PINDialog(self._parent_id, self)
        if pin_dialog.exec() != QDialog.Accepted or not pin_dialog.is_verified():
            self._toast("PIN cancelled — profile NOT deleted.", kind="warning")
            return

        # 3) Do the delete
        ok = db.delete_child(self._child_id)
        if not ok:
            self._toast("Delete failed. See crash.log.", kind="error")
            return
        self._toast(f"{name}'s profile has been deleted.", kind="success")
        # Bounce back to the welcome screen so the parent can pick another child.
        QTimer.singleShot(900, self.go_back.emit)

    def _toast(self, message: str, kind: str = "info"):
        """Show a transient feedback bubble. Falls back to QMessageBox on failure."""
        try:
            from ui.components import ToastNotification
            t = ToastNotification(self, message, kind=kind)
            t.move(self.width() // 2 - t.width() // 2, 60)
            t.show()
        except Exception:
            QMessageBox.information(self, "ARIA", message)

    def resizeEvent(self, event):
        if hasattr(self, '_bg'):
            self._bg.resize(self.size())
        super().resizeEvent(event)
