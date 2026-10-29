"""
ARIA Token Reward System
Visual progress with collectible stars and animated rewards.
"""

import math
import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QTimer, QPointF
from PySide6.QtGui import QPainter, QColor, QFont, QPainterPath, QPen, QLinearGradient, QRadialGradient

from ui.components import GlassCard, ARIAFaceWidget, ParticleBackground
from ui.styles import MAIN_STYLE, COLORS
import database.db_manager as db


class StarBurst(QWidget):
    """Animated star earned celebration."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 200)
        self._t = 0.0
        self._stars = []
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)

    def burst(self):
        self._t = 0.0
        self._stars = []
        for _ in range(15):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 5)
            self._stars.append({
                "x": 0, "y": 0,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "rot": random.uniform(0, math.pi * 2),
                "size": random.uniform(8, 16),
                "life": 1.0,
            })
        self._timer.start(20)

    def _update(self):
        self._t += 0.04
        for s in self._stars:
            s["x"] += s["vx"]
            s["y"] += s["vy"]
            s["vy"] += 0.15
            s["rot"] += 0.1
            s["life"] -= 0.02
        self._stars = [s for s in self._stars if s["life"] > 0]
        if not self._stars:
            self._timer.stop()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2

        # Center star
        center_size = 50 + 10 * math.sin(self._t * 3)
        self._draw_star(painter, cx, cy, center_size, QColor("#FFD700"), 1.0)

        for s in self._stars:
            x = cx + s["x"]
            y = cy + s["y"]
            color = QColor.fromHsl(int(50 + s["rot"] * 30) % 360, 255, 200)
            self._draw_star(painter, x, y, s["size"], color, s["life"])

    def _draw_star(self, painter, cx, cy, size, color, alpha):
        path = QPainterPath()
        for i in range(10):
            angle = math.pi / 5 * i - math.pi / 2
            r = size if i % 2 == 0 else size * 0.45
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        path.closeSubpath()

        c = QColor(color)
        c.setAlpha(int(255 * alpha))
        painter.setBrush(c)
        painter.setPen(QPen(QColor(255, 215, 0, int(255 * alpha)), 1))
        painter.drawPath(path)


class TokenJar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(250, 320)
        self._tokens = 0
        self._target = 0
        self._t = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self._timer.start(30)

    def set_tokens(self, n):
        self._target = n

    def _update(self):
        if self._tokens < self._target:
            self._tokens += 0.2
        elif self._tokens > self._target:
            self._tokens -= 0.2
        self._t += 0.02
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        jar_w = 180
        jar_h = 240
        jar_x = (w - jar_w) / 2
        jar_y = 40

        # Jar outline
        path = QPainterPath()
        path.addRoundedRect(jar_x, jar_y, jar_w, jar_h, 18, 18)

        # Jar fill (transparent glass)
        painter.setBrush(QColor(255, 255, 255, 80))
        painter.setPen(QPen(QColor(56, 184, 176, 200), 3))
        painter.drawPath(path)

        # Token fill level
        max_tokens = 50
        fill_pct = min(self._tokens / max_tokens, 1.0)
        fill_h = jar_h * fill_pct - 4
        if fill_h > 0:
            fill_path = QPainterPath()
            fill_path.addRoundedRect(jar_x + 4, jar_y + jar_h - fill_h - 2,
                                     jar_w - 8, fill_h, 14, 14)
            grad = QLinearGradient(0, jar_y, 0, jar_y + jar_h)
            grad.setColorAt(0, QColor(255, 215, 0, 200))
            grad.setColorAt(0.5, QColor(255, 180, 50, 220))
            grad.setColorAt(1, QColor(255, 140, 0, 240))
            painter.fillPath(fill_path, grad)

            # Animated stars inside jar
            for i in range(min(int(self._tokens), 20)):
                angle = i * 0.5 + self._t
                px = jar_x + jar_w / 2 + math.cos(angle) * (jar_w / 4)
                py = jar_y + jar_h - fill_h * 0.5 + math.sin(angle * 2) * 20
                self._draw_mini_star(painter, px, py, 7, QColor(255, 240, 100))

        # Lid
        lid_path = QPainterPath()
        lid_path.addRoundedRect(jar_x - 6, jar_y - 20, jar_w + 12, 22, 6, 6)
        painter.setBrush(QColor(120, 80, 30))
        painter.setPen(QPen(QColor(80, 50, 20), 2))
        painter.drawPath(lid_path)

        # Count
        painter.setFont(QFont("Segoe UI", 28, QFont.Black))
        painter.setPen(QColor(COLORS["text"]))
        painter.drawText(0, jar_y + jar_h + 12, w, 40, Qt.AlignCenter,
                         f"{int(self._tokens)} ⭐")

    def _draw_mini_star(self, painter, cx, cy, size, color):
        path = QPainterPath()
        for i in range(10):
            angle = math.pi / 5 * i - math.pi / 2
            r = size if i % 2 == 0 else size * 0.45
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        path.closeSubpath()
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)


class RewardCard(QWidget):
    earned = Signal(str)

    def __init__(self, key, icon, title, desc, cost, parent=None):
        super().__init__(parent)
        self._key = key
        self._cost = cost
        self.setFixedHeight(110)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        icon_lbl = QLabel(icon)
        icon_lbl.setFixedSize(60, 60)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(f"""
            font-size: 32px;
            background: rgba(255,215,0,0.15);
            border: 2px solid rgba(255,215,0,0.4);
            border-radius: 14px;
        """)

        col = QVBoxLayout()
        col.setSpacing(2)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLORS['text']};")
        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet(f"font-size: 11px; color: {COLORS['text_light']};")
        cost_lbl = QLabel(f"⭐ {cost} stars")
        cost_lbl.setStyleSheet("font-size: 12px; color: #D4A024; font-weight: 700;")
        col.addWidget(title_lbl)
        col.addWidget(desc_lbl)
        col.addWidget(cost_lbl)

        layout.addWidget(icon_lbl)
        layout.addLayout(col, 1)

        self.setStyleSheet(f"""
            QWidget {{
                background: rgba(255,255,255,0.85);
                border: 1.5px solid rgba(255,215,0,0.3);
                border-radius: 14px;
            }}
        """)


class RewardSystemScreen(QWidget):
    go_back = Signal()

    REWARDS = [
        ("extra_play",  "🎮", "Extra Play Time",   "5 min more games",     5),
        ("story",       "📖", "Pick Bedtime Story",  "Choose tonight's story", 8),
        ("treat",       "🍪", "Healthy Treat",       "A favorite snack",    10),
        ("movie",       "🎬", "Movie Night",         "Pick a family movie",  15),
        ("trip",        "🌳", "Park Trip",           "Special outing",       25),
    ]

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._child_data = db.get_child(child_id) or {}
        self.setStyleSheet(MAIN_STYLE)
        self._tokens = self._load_tokens()
        self._build_ui()

    def _load_tokens(self):
        return db.get_setting(f"tokens_{self._child_id}", 0)

    def _save_tokens(self):
        db.set_setting(f"tokens_{self._child_id}", self._tokens)

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
        title = QLabel("⭐ My Star Jar")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {COLORS['text']};")
        hdr.addWidget(back_btn)
        hdr.addSpacing(20)
        hdr.addWidget(title)
        hdr.addStretch()
        main.addLayout(hdr)

        body = QHBoxLayout()
        body.setSpacing(20)

        # ── LEFT: Token jar
        left = QVBoxLayout()
        left.setSpacing(12)

        jar_card = GlassCard(self, radius=22)
        jl = QVBoxLayout(jar_card)
        jl.setContentsMargins(16, 12, 16, 12)
        self._jar = TokenJar(self)
        self._jar.set_tokens(self._tokens)
        jl.addWidget(self._jar)
        left.addWidget(jar_card)

        # Earn button
        earn_card = GlassCard(self, radius=20)
        el = QVBoxLayout(earn_card)
        el.setContentsMargins(20, 14, 20, 14)

        el.addWidget(self._section("EARN STARS"))
        actions = [
            ("🎯 Completed an activity",  1),
            ("🌟 Used calm zone",          1),
            ("📅 Finished schedule task",  1),
            ("💬 Had a good conversation", 1),
        ]
        for label, amount in actions:
            btn = QPushButton(f"{label}  +{amount}⭐")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255,215,0,0.12); color: {COLORS['text']};
                    border: 1.5px solid rgba(255,215,0,0.4); border-radius: 12px;
                    padding: 9px 14px; font-size: 12px; font-weight: 600;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background: rgba(255,215,0,0.25);
                }}
            """)
            btn.clicked.connect(lambda checked, a=amount: self._add_tokens(a))
            el.addWidget(btn)
        left.addWidget(earn_card)
        left.addStretch()
        body.addLayout(left, 1)

        # ── RIGHT: rewards list
        right = QVBoxLayout()
        right.setSpacing(10)

        rew_card = GlassCard(self, radius=22)
        rl = QVBoxLayout(rew_card)
        rl.setContentsMargins(20, 14, 20, 14)
        rl.setSpacing(8)
        rl.addWidget(self._section("REWARDS YOU CAN EARN"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        rew_w = QWidget()
        rew_w.setStyleSheet("background: transparent;")
        rw_layout = QVBoxLayout(rew_w)
        rw_layout.setSpacing(10)
        rw_layout.setContentsMargins(0, 0, 8, 0)

        for key, icon, title, desc, cost in self.REWARDS:
            row = QHBoxLayout()
            card = RewardCard(key, icon, title, desc, cost)
            redeem_btn = QPushButton("Redeem!" if self._tokens >= cost else "Need more ⭐")
            redeem_btn.setEnabled(self._tokens >= cost)
            redeem_btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 #FFD700, stop:1 #FFA500);
                    color: white; border: none; border-radius: 12px;
                    padding: 10px 18px; font-size: 12px; font-weight: 700;
                }}
                QPushButton:hover {{ background: #FFCB00; }}
                QPushButton:disabled {{
                    background: #D0D5DA; color: #888;
                }}
            """)
            redeem_btn.clicked.connect(lambda checked, c=cost, k=key: self._redeem(c, k))
            row.addWidget(card, 1)
            row.addWidget(redeem_btn)
            rw_layout.addLayout(row)

        scroll.setWidget(rew_w)
        rl.addWidget(scroll)
        right.addWidget(rew_card, 1)
        body.addLayout(right, 2)
        main.addLayout(body, 1)

        self._refresh_buttons()

    def _section(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {COLORS['teal_deep']}; letter-spacing: 2px;")
        return lbl

    def _add_tokens(self, n):
        self._tokens += n
        self._jar.set_tokens(self._tokens)
        self._save_tokens()
        self._refresh_buttons()

    def _redeem(self, cost, key):
        if self._tokens >= cost:
            self._tokens -= cost
            self._jar.set_tokens(self._tokens)
            self._save_tokens()
            self._refresh_buttons()
            try:
                from ui.components import ToastNotification
                t = ToastNotification(self, f"🎉 Redeemed! Show this to your parent.", kind="success")
                t.move(self.width() // 2 - t.width() // 2, 30)
                t.show()
            except Exception:
                pass

    def _refresh_buttons(self):
        # Just rebuild the right list
        pass

    def resizeEvent(self, event):
        if hasattr(self, '_bg'):
            self._bg.resize(self.size())
        super().resizeEvent(event)
