"""
ARIA Mood Journal
Daily mood tracking with calendar heatmap visualization.
"""

import math
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QTextEdit, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QTimer, QPointF
from PySide6.QtGui import QPainter, QColor, QFont, QPainterPath, QPen, QLinearGradient

from ui.components import GlassCard, ARIAFaceWidget, ParticleBackground
from ui.styles import MAIN_STYLE, COLORS, get_emotion_color
import database.db_manager as db


class MoodHeatmap(QWidget):
    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self.setMinimumHeight(180)
        self._data = self._load_data()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update)
        self._timer.start(60)
        self._t = 0.0

    def _load_data(self):
        """Returns dict of {date_str: dominant_emotion} for last 30 days."""
        try:
            logs = db.get_emotion_logs(self._child_id, 1000)
        except Exception:
            return {}
        by_day = {}
        for log in logs:
            date_str = log.get("timestamp", "")[:10]
            em = log.get("emotion", "neutral")
            if date_str not in by_day:
                by_day[date_str] = {}
            by_day[date_str][em] = by_day[date_str].get(em, 0) + 1
        result = {}
        for date_str, ems in by_day.items():
            result[date_str] = max(ems, key=ems.get)
        return result

    def refresh(self):
        self._data = self._load_data()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Last 30 days
        today = datetime.now().date()
        days = [today - timedelta(days=i) for i in range(29, -1, -1)]

        cell_size = min((w - 60) / 30, h - 60)
        cell_size = max(cell_size, 16)
        gap = 4
        actual_w = (cell_size + gap) * 30 - gap
        x_start = (w - actual_w) / 2
        y_start = 30

        # Title
        painter.setPen(QColor(COLORS["teal_deep"]))
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.drawText(int(x_start), 22, "LAST 30 DAYS — MOOD HEATMAP")

        for i, day in enumerate(days):
            x = x_start + i * (cell_size + gap)
            y = y_start
            date_str = day.isoformat()
            emotion = self._data.get(date_str, None)

            if emotion:
                color = QColor(get_emotion_color(emotion))
                # Pulse on today
                if day == today:
                    pulse = 0.7 + 0.3 * math.sin(self._t)
                    color.setAlpha(int(255 * pulse))
            else:
                color = QColor(220, 230, 240, 80)

            path = QPainterPath()
            path.addRoundedRect(x, y, cell_size, cell_size, 4, 4)
            painter.fillPath(path, color)

            if day == today:
                painter.setPen(QPen(QColor(COLORS["teal"]), 2))
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(path)

        self._t += 0.04

        # Day labels
        painter.setPen(QColor(COLORS["text_light"]))
        painter.setFont(QFont("Segoe UI", 8))
        labels_y = int(y_start + cell_size + 10)
        for i in [0, 7, 14, 21, 29]:
            day = days[i]
            x = x_start + i * (cell_size + gap)
            painter.drawText(int(x - 8), labels_y + 14, day.strftime("%b %d"))

        # Legend
        legend_y = y_start + cell_size + 38
        legend_items = [
            ("Happy", "#4CAF90"), ("Calm", "#38B8B0"),
            ("Sad", "#6B9FD4"), ("Scared", "#9B8EC4"),
            ("Upset", "#E8956D"), ("Surprised", "#F0C040"),
        ]
        lx = x_start
        for label, c in legend_items:
            painter.setBrush(QColor(c))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(int(lx), int(legend_y), 12, 12, 3, 3)
            painter.setPen(QColor(COLORS["text"]))
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(int(lx + 16), int(legend_y + 10), label)
            lx += 70


class FeelingButton(QPushButton):
    def __init__(self, icon, label, key, color, parent=None):
        super().__init__(f"{icon}\n{label}", parent)
        self._color = color
        self._key = key
        self.setFixedSize(110, 90)
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.85);
                border: 2px solid {color}55;
                border-radius: 16px;
                font-size: 13px; font-weight: 600;
                color: {COLORS['text']};
                padding: 4px;
            }}
            QPushButton:hover {{
                background: {color}22;
                border-color: {color};
            }}
            QPushButton:checked {{
                background: {color};
                color: white;
                border-color: {color};
            }}
        """)


class MoodJournalScreen(QWidget):
    go_back = Signal()

    FEELINGS = [
        ("😊", "Great",     "great",    "#4CAF90"),
        ("🙂", "Good",      "good",     "#38B8B0"),
        ("😐", "Okay",      "okay",     "#90A8C0"),
        ("😢", "Sad",       "sad",      "#6B9FD4"),
        ("😨", "Worried",   "worried",  "#9B8EC4"),
        ("😤", "Frustrated","upset",    "#E8956D"),
    ]

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._child_data = db.get_child(child_id) or {}
        self._selected_feeling = None
        self.setStyleSheet(MAIN_STYLE)
        self._build_ui()

    def _build_ui(self):
        self._bg = ParticleBackground(self)
        self._bg.lower()

        main = QVBoxLayout(self)
        main.setContentsMargins(32, 24, 32, 24)
        main.setSpacing(14)

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
        title = QLabel("📔 Mood Journal")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {COLORS['text']};")
        hdr.addWidget(back_btn)
        hdr.addSpacing(20)
        hdr.addWidget(title)
        hdr.addStretch()
        main.addLayout(hdr)

        body = QHBoxLayout()
        body.setSpacing(16)

        # ── LEFT: Today's check-in
        left = QVBoxLayout()
        left.setSpacing(14)

        checkin_card = GlassCard(self, radius=22)
        cl = QVBoxLayout(checkin_card)
        cl.setContentsMargins(24, 20, 24, 20)
        cl.setSpacing(12)

        cl.addWidget(self._section("HOW DO YOU FEEL TODAY?"))

        face_row = QHBoxLayout()
        self._face = ARIAFaceWidget(size=100)
        face_row.addWidget(self._face)
        face_row.addStretch()
        self._aria_msg = QLabel("Tap a feeling 💙")
        self._aria_msg.setWordWrap(True)
        self._aria_msg.setStyleSheet(f"font-size: 14px; color: {COLORS['teal_deep']}; font-weight: 600;")
        face_row.addWidget(self._aria_msg, 1)
        cl.addLayout(face_row)

        # Feeling buttons
        feels_grid = QGridLayout()
        feels_grid.setSpacing(8)
        self._feeling_buttons = []
        for i, (icon, label, key, color) in enumerate(self.FEELINGS):
            btn = FeelingButton(icon, label, key, color, self)
            btn.clicked.connect(lambda checked, k=key, c=color, l=label: self._select_feeling(k, c, l))
            self._feeling_buttons.append(btn)
            feels_grid.addWidget(btn, i // 3, i % 3)
        cl.addLayout(feels_grid)

        cl.addWidget(self._section("WHAT HAPPENED? (OPTIONAL)"))
        self._note = QTextEdit()
        self._note.setPlaceholderText("You can write or just tap a feeling...")
        self._note.setMaximumHeight(80)
        cl.addWidget(self._note)

        save_btn = QPushButton("💾  Save Today's Entry")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {COLORS['teal']}, stop:1 #B388FF);
                color: white; border: none; border-radius: 14px;
                padding: 12px 28px; font-size: 14px; font-weight: 700;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {COLORS['teal_glow']}, stop:1 #C39BFF);
            }}
        """)
        save_btn.clicked.connect(self._save_entry)
        cl.addWidget(save_btn)
        left.addWidget(checkin_card)
        body.addLayout(left, 1)

        # ── RIGHT: Heatmap & insights
        right = QVBoxLayout()
        right.setSpacing(14)

        heat_card = GlassCard(self, radius=22)
        hl = QVBoxLayout(heat_card)
        hl.setContentsMargins(20, 14, 20, 14)
        self._heatmap = MoodHeatmap(self._child_id, self)
        hl.addWidget(self._heatmap)
        right.addWidget(heat_card)

        # Insights
        insight_card = GlassCard(self, radius=20)
        il = QVBoxLayout(insight_card)
        il.setContentsMargins(20, 14, 20, 14)
        il.addWidget(self._section("INSIGHTS"))
        insights = self._compute_insights()
        for insight in insights:
            lbl = QLabel(f"• {insight}")
            lbl.setStyleSheet(f"font-size: 13px; color: {COLORS['text']}; padding: 4px 0;")
            lbl.setWordWrap(True)
            il.addWidget(lbl)
        right.addWidget(insight_card)
        right.addStretch()

        body.addLayout(right, 1)
        main.addLayout(body, 1)

    def _section(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"""
            font-size: 10px; font-weight: 700;
            color: {COLORS['teal_deep']}; letter-spacing: 2px;
        """)
        return lbl

    def _select_feeling(self, key, color, label):
        for btn in self._feeling_buttons:
            btn.setChecked(btn._key == key)
        self._selected_feeling = key

        # ARIA reaction
        emotion_map = {
            "great": "happy", "good": "happy", "okay": "calm",
            "sad": "sad", "worried": "fear", "upset": "anger",
        }
        self._face.set_expression(emotion_map.get(key, "calm"))

        lang = self._child_data.get("language", "en")
        msgs = {
            "en": {
                "great":  "I'm so glad you feel great today! ☀️",
                "good":   "That's wonderful! 😊",
                "okay":   "It's okay to feel just okay. 💙",
                "sad":    "I'm here with you. It's okay to feel sad. 💙",
                "worried":"It's okay to feel worried. Let's breathe together. 🌬️",
                "upset":  "It's okay to feel upset. I'm with you. 💙",
            },
            "ar": {
                "great":  "أنا مبسوط إنك حاسس كويس النهاردة! ☀️",
                "good":   "ده رائع! 😊",
                "okay":   "عادي تحس عادي. 💙",
                "sad":    "أنا معاك. عادي تحس بزعل. 💙",
                "worried":"عادي تحس بقلق. خلينا نتنفس سوا. 🌬️",
                "upset":  "عادي تحس بضيق. أنا معاك. 💙",
            },
            "de": {
                "great":  "Ich freue mich, dass du dich super fühlst! ☀️",
                "good":   "Das ist wunderbar! 😊",
                "okay":   "Es ist okay, sich nur okay zu fühlen. 💙",
                "sad":    "Ich bin bei dir. Es ist okay, traurig zu sein. 💙",
                "worried":"Es ist okay, besorgt zu sein. Atmen wir zusammen. 🌬️",
                "upset":  "Es ist okay, verärgert zu sein. Ich bin bei dir. 💙",
            },
        }
        self._aria_msg.setText(msgs.get(lang, msgs["en"]).get(key, "I hear you 💙"))

    def _save_entry(self):
        if not self._selected_feeling:
            self._aria_msg.setText("Please tap a feeling first! 💙")
            return

        emotion_map = {
            "great": "happy", "good": "happy", "okay": "neutral",
            "sad": "sadness", "worried": "fear", "upset": "anger",
        }
        em = emotion_map.get(self._selected_feeling, "neutral")
        try:
            db.log_emotion(
                self._child_id, em, 1.0,
                source="mood_journal",
                action_taken=self._note.toPlainText()[:200] or "no_note"
            )
        except Exception:
            pass

        # Intelligence bus: a self-reported feeling is gold — feed it to the
        # suggestion engine and reward the act of sharing.
        try:
            from core.child_context import get_context
            get_context().record_emotion(em, source="self_report")
            get_context().record_activity("journal", "entry", award=1,
                                          reason="mood journal entry")
        except Exception:
            pass

        self._aria_msg.setText("✅ Saved! Thank you for sharing. 💙")
        self._note.clear()
        self._heatmap.refresh()

    def _compute_insights(self):
        try:
            logs = db.get_emotion_logs(self._child_id, 100)
        except Exception:
            return ["Start tracking your mood today to see insights!"]
        if not logs:
            return ["Tap a feeling above to start your journal!"]

        emotions = [l.get("emotion", "neutral") for l in logs[:30]]
        from collections import Counter
        counts = Counter(emotions)
        most_common = counts.most_common(1)[0][0] if counts else "neutral"
        positive = sum(counts.get(e, 0) for e in ["happy", "joy", "calm", "neutral"])
        negative = sum(counts.get(e, 0) for e in ["sadness", "fear", "anger"])
        total = positive + negative

        insights = []
        if total > 0:
            ratio = positive / total
            if ratio > 0.7:
                insights.append(f"🌟 Mostly positive moods recently ({int(ratio*100)}% positive)")
            elif ratio > 0.4:
                insights.append(f"😊 Mixed but balanced moods ({int(ratio*100)}% positive)")
            else:
                insights.append(f"💙 Lots of tough feelings lately. ARIA is here.")
        insights.append(f"Most common feeling: {most_common.title()}")
        insights.append(f"Total entries tracked: {len(logs)}")
        return insights

    def resizeEvent(self, event):
        if hasattr(self, '_bg'):
            self._bg.resize(self.size())
        super().resizeEvent(event)
