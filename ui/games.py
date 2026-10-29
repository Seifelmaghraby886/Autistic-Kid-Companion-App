"""
ARIA Games Screen
Autism-friendly games: Emotion Matching, Color Sort, Shape Match, Social Stories, Routine Order.
"""

import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QStackedWidget, QGridLayout, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QColor, QFont, QPainterPath, QLinearGradient

from ui.components import GlassCard, ARIAFaceWidget, ParticleBackground, ToastNotification
from ui.styles import MAIN_STYLE, COLORS
import database.db_manager as db


# ══════════════════════════════════════════════════════════════
#  Emotion Matching Game
# ══════════════════════════════════════════════════════════════
class EmotionMatchingGame(QWidget):
    game_complete = Signal(int)  # score

    EMOTIONS = [
        ("happy",    "😊", "Happy",    "#4CAF90"),
        ("sad",      "😢", "Sad",      "#6B9FD4"),
        ("upset",    "😤", "Upset",    "#E8956D"),
        ("scared",   "😨", "Scared",   "#9B8EC4"),
        ("calm",     "😌", "Calm",     "#38B8B0"),
        ("surprised","😲", "Surprised","#F0C040"),
    ]

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._child_data = db.get_child(child_id) or {}
        self._score = 0
        self._round = 0
        self._total_rounds = 6
        self._current_emotion = None
        self._build_ui()
        self._next_round()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Score + round
        self._progress_lbl = QLabel("Round 1 of 6")
        self._progress_lbl.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {COLORS['text']};")
        self._score_lbl = QLabel("⭐ Score: 0")
        self._score_lbl.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {COLORS['teal']};")
        top = QHBoxLayout()
        top.addWidget(self._progress_lbl)
        top.addStretch()
        top.addWidget(self._score_lbl)
        layout.addLayout(top)

        # ARIA face showing emotion
        face_card = GlassCard(self, radius=24)
        fc = QVBoxLayout(face_card)
        fc.setContentsMargins(20, 20, 20, 20)
        fc.setAlignment(Qt.AlignCenter)

        self._face = ARIAFaceWidget(size=150)
        fc.addWidget(self._face, alignment=Qt.AlignCenter)

        self._question_lbl = QLabel("How is ARIA feeling?")
        self._question_lbl.setAlignment(Qt.AlignCenter)
        self._question_lbl.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {COLORS['text']}; padding: 8px 0;")
        fc.addWidget(self._question_lbl)
        layout.addWidget(face_card)

        # Emotion choice buttons
        self._choices_grid = QGridLayout()
        self._choices_grid.setSpacing(12)
        self._choice_buttons = []

        for i, (key, icon, label, color) in enumerate(self.EMOTIONS):
            btn = QPushButton(f"{icon}\n{label}")
            btn.setFixedSize(130, 80)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255,255,255,0.85);
                    border: 2px solid rgba(56,184,176,0.25);
                    border-radius: 18px;
                    font-size: 20px;
                    color: {COLORS['text']};
                    padding: 6px;
                }}
                QPushButton:hover {{
                    background: {color}22;
                    border-color: {color};
                }}
            """)
            btn.clicked.connect(lambda checked, k=key: self._check_answer(k))
            self._choice_buttons.append((key, btn))
            self._choices_grid.addWidget(btn, i // 3, i % 3)

        choices_card = GlassCard(self, radius=20)
        cc = QVBoxLayout(choices_card)
        cc.setContentsMargins(20, 16, 20, 16)
        cc.addLayout(self._choices_grid)
        layout.addWidget(choices_card)

        # Feedback label
        self._feedback_lbl = QLabel("")
        self._feedback_lbl.setAlignment(Qt.AlignCenter)
        self._feedback_lbl.setStyleSheet(f"font-size: 18px; font-weight: 700; padding: 8px;")
        layout.addWidget(self._feedback_lbl)

    def _next_round(self):
        if self._round >= self._total_rounds:
            self.game_complete.emit(self._score)
            return

        self._round += 1
        self._progress_lbl.setText(f"Round {self._round} of {self._total_rounds}")
        self._feedback_lbl.setText("")

        # Pick random emotion
        self._current_emotion = random.choice(self.EMOTIONS)
        key, icon, label, color = self._current_emotion
        self._face.set_expression(key)

        lang = self._child_data.get("language", "en")
        questions = {
            "en": "How is ARIA feeling?",
            "ar": "كيف تحس أريا دلوقتي؟",
            "de": "Wie fühlt sich ARIA gerade?",
        }
        self._question_lbl.setText(questions.get(lang, questions["en"]))

        # Enable all buttons
        for _, btn in self._choice_buttons:
            btn.setEnabled(True)
            btn.setStyleSheet(btn.styleSheet().replace("opacity: 0.5;", ""))

    def _check_answer(self, chosen_key):
        correct_key = self._current_emotion[0]
        correct_color = self._current_emotion[3]

        for _, btn in self._choice_buttons:
            btn.setEnabled(False)

        lang = self._child_data.get("language", "en")
        if chosen_key == correct_key:
            self._score += 1
            self._score_lbl.setText(f"⭐ Score: {self._score}")
            msgs = {"en": "✅ That's right! Great job!", "ar": "✅ صح! عظيم!", "de": "✅ Richtig! Gut gemacht!"}
            self._feedback_lbl.setText(msgs.get(lang, msgs["en"]))
            self._feedback_lbl.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {COLORS['success']}; padding: 8px;")
        else:
            msgs = {"en": f"Not quite. It was {self._current_emotion[2]}. That's okay! 💙",
                    "ar": f"مش الصح. كانت {self._current_emotion[2]}. مفيش مشكلة! 💙",
                    "de": f"Nicht ganz. Es war {self._current_emotion[2]}. Das ist okay! 💙"}
            self._feedback_lbl.setText(msgs.get(lang, msgs["en"]))
            self._feedback_lbl.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLORS['teal_deep']}; padding: 8px;")

        QTimer.singleShot(1800, self._next_round)


# ══════════════════════════════════════════════════════════════
#  Color Sorting Game
# ══════════════════════════════════════════════════════════════
class ColorSortGame(QWidget):
    game_complete = Signal(int)

    COLORS_LIST = [
        ("#4CAF90", "Green"), ("#38B8B0", "Teal"), ("#6B9FD4", "Blue"),
        ("#D8A0E8", "Purple"), ("#F0C040", "Yellow"), ("#E8956D", "Orange"),
    ]

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._score = 0
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("🎨 Color Sorting")
        title.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {COLORS['text']};")
        subtitle = QLabel("Tap the ball, then tap the matching box!")
        subtitle.setStyleSheet(f"font-size: 14px; color: {COLORS['text_light']};")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Color balls (items to sort)
        balls_card = GlassCard(self, radius=20)
        bl = QHBoxLayout(balls_card)
        bl.setContentsMargins(20, 16, 20, 16)
        bl.setSpacing(12)

        self._current_ball = None
        self._ball_buttons = []
        shuffled = self.COLORS_LIST.copy()
        random.shuffle(shuffled)

        for hex_color, name in shuffled[:4]:
            btn = QPushButton()
            btn.setFixedSize(60, 60)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {hex_color};
                    border: 3px solid rgba(255,255,255,0.5);
                    border-radius: 30px;
                }}
                QPushButton:hover {{
                    border: 3px solid white;
                    border-radius: 30px;
                }}
            """)
            btn.clicked.connect(lambda checked, c=hex_color, n=name: self._select_ball(c, n))
            self._ball_buttons.append((hex_color, name, btn))
            bl.addWidget(btn)
        bl.addStretch()
        layout.addWidget(balls_card)

        # Target label
        self._target_lbl = QLabel("Tap a ball to start!")
        self._target_lbl.setAlignment(Qt.AlignCenter)
        self._target_lbl.setStyleSheet(f"font-size: 16px; color: {COLORS['text']}; padding: 8px;")
        layout.addWidget(self._target_lbl)

        # Color boxes (targets)
        boxes_card = GlassCard(self, radius=20)
        bx = QHBoxLayout(boxes_card)
        bx.setContentsMargins(20, 16, 20, 16)
        bx.setSpacing(12)

        for hex_color, name in self.COLORS_LIST[:4]:
            box = QPushButton(name)
            box.setFixedSize(80, 80)
            box.setStyleSheet(f"""
                QPushButton {{
                    background: {hex_color}22;
                    border: 3px solid {hex_color}88;
                    border-radius: 16px;
                    color: {COLORS['text']};
                    font-size: 12px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background: {hex_color}44;
                    border-color: {hex_color};
                }}
            """)
            box.clicked.connect(lambda checked, c=hex_color, n=name: self._drop_ball(c, n))
            bx.addWidget(box)
        bx.addStretch()
        layout.addWidget(boxes_card)

        self._score_lbl = QLabel("⭐ Score: 0")
        self._score_lbl.setAlignment(Qt.AlignCenter)
        self._score_lbl.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {COLORS['teal']};")
        layout.addWidget(self._score_lbl)

    def _select_ball(self, color, name):
        self._current_ball = (color, name)
        self._target_lbl.setText(f"Now tap the {name} box! →")
        self._target_lbl.setStyleSheet(f"font-size: 16px; color: {color}; font-weight: 700; padding: 8px;")

    def _drop_ball(self, box_color, box_name):
        if not self._current_ball:
            return
        ball_color, ball_name = self._current_ball
        if ball_color == box_color:
            self._score += 1
            self._score_lbl.setText(f"⭐ Score: {self._score}")
            self._target_lbl.setText("✅ Correct! Great sorting!")
            self._target_lbl.setStyleSheet(f"font-size: 16px; color: {COLORS['success']}; font-weight: 700; padding: 8px;")
        else:
            self._target_lbl.setText(f"💙 Not quite — {ball_name} goes in the {ball_name} box!")
            self._target_lbl.setStyleSheet(f"font-size: 14px; color: {COLORS['teal_deep']}; padding: 8px;")
        self._current_ball = None
        QTimer.singleShot(1500, lambda: self._target_lbl.setText("Tap another ball!"))


# ══════════════════════════════════════════════════════════════
#  Routine Ordering Game
# ══════════════════════════════════════════════════════════════
class RoutineOrderGame(QWidget):
    game_complete = Signal(int)

    ROUTINE = [
        ("🌅", "Wake Up"),
        ("🪥", "Brush Teeth"),
        ("🍳", "Breakfast"),
        ("🎒", "School"),
        ("😴", "Rest"),
        ("🎮", "Play"),
        ("🌙", "Sleep"),
    ]

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._child_data = db.get_child(child_id) or {}
        self._score = 0
        self._selected = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        lang = self._child_data.get("language", "en")
        titles = {"en": "📅 Daily Routine", "ar": "📅 روتين اليوم", "de": "📅 Tagesroutine"}
        subs = {"en": "Put the day in order! Tap each step.", "ar": "رتب اليوم! اضغط على كل خطوة.", "de": "Bringe den Tag in Ordnung!"}

        title = QLabel(titles.get(lang, titles["en"]))
        title.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {COLORS['text']};")
        subtitle = QLabel(subs.get(lang, subs["en"]))
        subtitle.setStyleSheet(f"font-size: 14px; color: {COLORS['text_light']};")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        routine_ar = [("🌅","اصحى"),("🪥","اغسل سنانك"),("🍳","الفطار"),("🎒","المدرسة"),("😴","راحة"),("🎮","لعب"),("🌙","النوم")]
        routine_de = [("🌅","Aufwachen"),("🪥","Zähne putzen"),("🍳","Frühstück"),("🎒","Schule"),("😴","Pause"),("🎮","Spielen"),("🌙","Schlafen")]
        routine = {"ar": routine_ar, "de": routine_de}.get(lang, self.ROUTINE)

        # Shuffled cards
        shuffled = routine.copy()
        random.shuffle(shuffled)

        self._routine_order = routine
        self._buttons = {}

        cards_card = GlassCard(self, radius=20)
        cl = QGridLayout(cards_card)
        cl.setContentsMargins(16, 14, 16, 14)
        cl.setSpacing(10)

        for i, (icon, label) in enumerate(shuffled):
            btn = QPushButton(f"{icon}\n{label}")
            btn.setFixedSize(100, 80)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255,255,255,0.9);
                    border: 2px solid rgba(56,184,176,0.25);
                    border-radius: 16px;
                    font-size: 14px;
                    color: {COLORS['text']};
                    padding: 4px;
                }}
                QPushButton:hover {{
                    background: rgba(56,184,176,0.15);
                    border-color: {COLORS['teal']};
                }}
                QPushButton:checked {{
                    background: rgba(56,184,176,0.25);
                    border-color: {COLORS['teal']};
                    color: {COLORS['teal_deep']};
                }}
            """)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, ic=icon, lb=label: self._select_card(ic, lb))
            self._buttons[(icon, label)] = btn
            cl.addWidget(btn, i // 4, i % 4)

        layout.addWidget(cards_card)

        # Selected order display
        self._order_lbl = QLabel("Tap cards in the correct order →")
        self._order_lbl.setStyleSheet(f"font-size: 13px; color: {COLORS['text_light']}; padding: 4px;")
        layout.addWidget(self._order_lbl)

        self._answer_row = QHBoxLayout()
        self._answer_row.setSpacing(8)
        layout.addLayout(self._answer_row)

        # Check button
        check_btn = QPushButton("✅  Check Order")
        check_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {COLORS['teal']}, stop:1 {COLORS['teal_deep']});
                color: white; border: none; border-radius: 14px;
                padding: 12px 28px; font-size: 14px; font-weight: 700;
            }}
            QPushButton:hover {{ background: {COLORS['teal_glow']}; }}
        """)
        check_btn.clicked.connect(self._check_order)
        layout.addWidget(check_btn, alignment=Qt.AlignHCenter)

        self._result_lbl = QLabel("")
        self._result_lbl.setAlignment(Qt.AlignCenter)
        self._result_lbl.setStyleSheet(f"font-size: 16px; font-weight: 700; padding: 8px;")
        layout.addWidget(self._result_lbl)

    def _select_card(self, icon, label):
        item = (icon, label)
        if item in self._selected:
            self._selected.remove(item)
            self._buttons[item].setChecked(False)
        else:
            self._selected.append(item)
            self._buttons[item].setChecked(True)
        self._update_answer_row()

    def _update_answer_row(self):
        while self._answer_row.count():
            w = self._answer_row.takeAt(0)
            if w.widget():
                w.widget().deleteLater()
        for icon, label in self._selected:
            lbl = QLabel(icon)
            lbl.setStyleSheet("font-size: 22px; background: rgba(56,184,176,0.1); border-radius: 10px; padding: 6px;")
            self._answer_row.addWidget(lbl)
        self._answer_row.addStretch()

    def _check_order(self):
        if len(self._selected) != len(self._routine_order):
            self._result_lbl.setText("Select all the steps first!")
            self._result_lbl.setStyleSheet(f"font-size: 14px; color: {COLORS['warning']}; padding: 8px;")
            return

        correct = all(self._selected[i] == self._routine_order[i]
                      for i in range(len(self._selected)))
        lang = self._child_data.get("language", "en")
        if correct:
            msgs = {"en": "🎉 Perfect! You got it all right!", "ar": "🎉 ممتاز! كلها صح!", "de": "🎉 Perfekt! Alles richtig!"}
            self._result_lbl.setText(msgs.get(lang, msgs["en"]))
            self._result_lbl.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {COLORS['success']}; padding: 8px;")
            self.game_complete.emit(7)
        else:
            msgs = {"en": "💙 Almost! Try again — I believe in you!", "ar": "💙 تقريباً! جرب تاني — أنا واثق فيك!", "de": "💙 Fast! Versuche es noch einmal!"}
            self._result_lbl.setText(msgs.get(lang, msgs["en"]))
            self._result_lbl.setStyleSheet(f"font-size: 16px; color: {COLORS['teal_deep']}; padding: 8px;")


# ══════════════════════════════════════════════════════════════
#  Memory Match Game
# ══════════════════════════════════════════════════════════════
class MemoryMatchGame(QWidget):
    game_complete = Signal(int)

    EMOJI_PAIRS = ["🐶", "🐱", "🐰", "🦊", "🐻", "🐼"]

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._first = None
        self._matches = 0
        self._tries = 0
        self._can_click = True
        cards = (self.EMOJI_PAIRS * 2).copy()
        random.shuffle(cards)
        self._cards = cards
        self._revealed = [False] * len(cards)
        self._matched = [False] * len(cards)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("🧠 Memory Match")
        title.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {COLORS['text']};")
        sub = QLabel("Find matching pairs by tapping cards")
        sub.setStyleSheet(f"font-size: 13px; color: {COLORS['text_light']};")
        layout.addWidget(title)
        layout.addWidget(sub)

        self._stats = QLabel("Pairs found: 0  ·  Tries: 0")
        self._stats.setStyleSheet(f"font-size: 14px; color: {COLORS['teal_deep']}; font-weight: 600;")
        layout.addWidget(self._stats)

        grid_card = GlassCard(self, radius=20)
        grid = QGridLayout(grid_card)
        grid.setContentsMargins(20, 16, 20, 16)
        grid.setSpacing(10)

        self._buttons = []
        for i, emoji in enumerate(self._cards):
            btn = QPushButton("?")
            btn.setFixedSize(80, 80)
            btn.setStyleSheet(self._hidden_style())
            btn.clicked.connect(lambda checked, idx=i: self._flip(idx))
            self._buttons.append(btn)
            grid.addWidget(btn, i // 4, i % 4)
        layout.addWidget(grid_card)

        self._msg = QLabel("")
        self._msg.setAlignment(Qt.AlignCenter)
        self._msg.setStyleSheet(f"font-size: 14px; font-weight: 600; padding: 6px;")
        layout.addWidget(self._msg)
        layout.addStretch()

    def _hidden_style(self):
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #00BFA8, stop:1 #1A7FA8);
                color: white; border: 2px solid #00E5FF; border-radius: 14px;
                font-size: 30px; font-weight: 900;
            }}
            QPushButton:hover {{ background: #5CE5DC; }}
            QPushButton:disabled {{ opacity: 0.5; }}
        """

    def _shown_style(self):
        return f"""
            QPushButton {{
                background: rgba(255,255,255,0.95); color: {COLORS['text']};
                border: 2px solid {COLORS['teal']}; border-radius: 14px;
                font-size: 36px;
            }}
        """

    def _matched_style(self):
        return f"""
            QPushButton {{
                background: rgba(0,217,160,0.30); color: {COLORS['text']};
                border: 2px solid #00D9A0; border-radius: 14px;
                font-size: 36px;
            }}
        """

    def _flip(self, idx):
        if not self._can_click or self._matched[idx] or self._revealed[idx]:
            return
        self._revealed[idx] = True
        self._buttons[idx].setText(self._cards[idx])
        self._buttons[idx].setStyleSheet(self._shown_style())

        if self._first is None:
            self._first = idx
        else:
            self._tries += 1
            self._stats.setText(f"Pairs found: {self._matches}  ·  Tries: {self._tries}")
            if self._cards[self._first] == self._cards[idx]:
                # Match!
                self._matched[self._first] = True
                self._matched[idx] = True
                self._buttons[self._first].setStyleSheet(self._matched_style())
                self._buttons[idx].setStyleSheet(self._matched_style())
                self._matches += 1
                self._first = None
                if self._matches == len(self.EMOJI_PAIRS):
                    self._msg.setText(f"🎉 You found all {self._matches} pairs in {self._tries} tries!")
                    self._msg.setStyleSheet(f"font-size: 16px; color: {COLORS['success']}; font-weight: 700; padding: 6px;")
                    self.game_complete.emit(self._matches)
            else:
                self._can_click = False
                first_idx = self._first
                self._first = None
                QTimer.singleShot(900, lambda: self._unflip(first_idx, idx))

    def _unflip(self, i1, i2):
        self._revealed[i1] = False
        self._revealed[i2] = False
        self._buttons[i1].setText("?")
        self._buttons[i2].setText("?")
        self._buttons[i1].setStyleSheet(self._hidden_style())
        self._buttons[i2].setStyleSheet(self._hidden_style())
        self._can_click = True


# ══════════════════════════════════════════════════════════════
#  Shape Match Game
# ══════════════════════════════════════════════════════════════
class ShapeMatchGame(QWidget):
    game_complete = Signal(int)

    SHAPES = [
        ("circle",   "⭕", "Circle",   "#00BFA8"),
        ("square",   "🟦", "Square",   "#6B9FE8"),
        ("triangle", "🔺", "Triangle", "#FF8B5C"),
        ("star",     "⭐", "Star",     "#FFD700"),
        ("heart",    "❤️", "Heart",    "#FF6BC4"),
        ("diamond",  "💎", "Diamond",  "#A695FF"),
    ]

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._score = 0
        self._round = 0
        self._total = 5
        self._build_ui()
        self._next_round()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("🔷 Shape Matching")
        title.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {COLORS['text']};")
        layout.addWidget(title)

        self._round_lbl = QLabel("")
        self._round_lbl.setStyleSheet(f"font-size: 13px; color: {COLORS['teal_deep']}; font-weight: 600;")
        layout.addWidget(self._round_lbl)

        self._target_card = GlassCard(self, radius=22)
        tl = QVBoxLayout(self._target_card)
        tl.setContentsMargins(20, 24, 20, 24)
        tl.setAlignment(Qt.AlignCenter)
        self._target_lbl = QLabel("?")
        self._target_lbl.setAlignment(Qt.AlignCenter)
        self._target_lbl.setStyleSheet("font-size: 80px;")
        tl.addWidget(self._target_lbl)
        self._question = QLabel("")
        self._question.setAlignment(Qt.AlignCenter)
        self._question.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {COLORS['text']};")
        tl.addWidget(self._question)
        layout.addWidget(self._target_card)

        self._choices_grid = QGridLayout()
        self._choices_grid.setSpacing(10)
        self._choice_btns = []
        for i in range(6):
            btn = QPushButton()
            btn.setFixedSize(120, 80)
            self._choice_btns.append(btn)
            self._choices_grid.addWidget(btn, i // 3, i % 3)

        choices_card = GlassCard(self, radius=20)
        cl = QVBoxLayout(choices_card)
        cl.setContentsMargins(16, 14, 16, 14)
        cl.addLayout(self._choices_grid)
        layout.addWidget(choices_card)

        self._feedback = QLabel("")
        self._feedback.setAlignment(Qt.AlignCenter)
        self._feedback.setStyleSheet(f"font-size: 16px; font-weight: 700; padding: 8px;")
        layout.addWidget(self._feedback)

    def _next_round(self):
        if self._round >= self._total:
            self._feedback.setText(f"🎉 You scored {self._score}/{self._total}!")
            self._feedback.setStyleSheet(f"font-size: 18px; color: {COLORS['success']}; font-weight: 800; padding: 8px;")
            self.game_complete.emit(self._score)
            return
        self._round += 1
        self._round_lbl.setText(f"Round {self._round} of {self._total}  ·  Score: {self._score}")
        self._feedback.setText("")
        target = random.choice(self.SHAPES)
        self._target_key = target[0]
        self._target_lbl.setText(target[1])
        self._question.setText(f"Find the {target[2]}")

        # Pick 6 shapes including the target
        choices = self.SHAPES.copy()
        random.shuffle(choices)
        if target not in choices[:6]:
            choices[0] = target
            random.shuffle(choices)

        for i, btn in enumerate(self._choice_btns):
            shape = choices[i]
            btn.setText(f"{shape[1]}\n{shape[2]}")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255,255,255,0.92);
                    border: 2px solid {shape[3]}55; border-radius: 14px;
                    font-size: 16px; color: {COLORS['text']};
                }}
                QPushButton:hover {{ background: {shape[3]}33; border-color: {shape[3]}; }}
            """)
            try:
                btn.clicked.disconnect()
            except Exception:
                pass
            btn.clicked.connect(lambda checked, k=shape[0], lbl=shape[2]: self._check(k, lbl))

    def _check(self, key, label):
        if key == self._target_key:
            self._score += 1
            self._feedback.setText(f"✅ Correct!")
            self._feedback.setStyleSheet(f"font-size: 16px; color: {COLORS['success']}; font-weight: 700; padding: 8px;")
        else:
            self._feedback.setText(f"💙 That was {label}. Try again next time!")
            self._feedback.setStyleSheet(f"font-size: 14px; color: {COLORS['teal_deep']}; padding: 8px;")
        QTimer.singleShot(1300, self._next_round)


# ══════════════════════════════════════════════════════════════
#  Animal Sounds Game
# ══════════════════════════════════════════════════════════════
class AnimalSoundsGame(QWidget):
    game_complete = Signal(int)

    ANIMALS = [
        ("dog",   "🐶", "Dog",   "Woof Woof!"),
        ("cat",   "🐱", "Cat",   "Meow Meow!"),
        ("cow",   "🐄", "Cow",   "Mooo!"),
        ("sheep", "🐑", "Sheep", "Baa Baa!"),
        ("duck",  "🦆", "Duck",  "Quack Quack!"),
        ("lion",  "🦁", "Lion",  "Roar!"),
        ("bird",  "🐦", "Bird",  "Tweet Tweet!"),
        ("frog",  "🐸", "Frog",  "Ribbit!"),
    ]

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._score = 0
        self._round = 0
        self._total = 5
        self._build_ui()
        self._next_round()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)
        title = QLabel("🐶 Animal Sounds")
        title.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {COLORS['text']};")
        layout.addWidget(title)

        self._round_lbl = QLabel("")
        self._round_lbl.setStyleSheet(f"font-size: 13px; color: {COLORS['teal_deep']}; font-weight: 600;")
        layout.addWidget(self._round_lbl)

        sound_card = GlassCard(self, radius=22)
        sl = QVBoxLayout(sound_card)
        sl.setContentsMargins(20, 22, 20, 22)
        sl.setAlignment(Qt.AlignCenter)
        self._sound_lbl = QLabel("")
        self._sound_lbl.setAlignment(Qt.AlignCenter)
        self._sound_lbl.setStyleSheet(f"font-size: 30px; font-weight: 800; color: {COLORS['teal_deep']}; padding: 16px;")
        sl.addWidget(self._sound_lbl)
        speak_btn = QPushButton("🔊  Hear Sound")
        speak_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0,191,168,0.15); color: {COLORS['teal_deep']};
                border: 1.5px solid {COLORS['teal']}; border-radius: 12px;
                padding: 8px 22px; font-size: 13px; font-weight: 600;
            }}
        """)
        speak_btn.clicked.connect(self._speak_sound)
        sl.addWidget(speak_btn, alignment=Qt.AlignCenter)
        question = QLabel("Which animal makes this sound?")
        question.setAlignment(Qt.AlignCenter)
        question.setStyleSheet(f"font-size: 14px; color: {COLORS['text']}; padding: 6px;")
        sl.addWidget(question)
        layout.addWidget(sound_card)

        self._choices_grid = QGridLayout()
        self._choices_grid.setSpacing(10)
        self._choice_btns = []
        for i in range(4):
            btn = QPushButton()
            btn.setFixedSize(140, 90)
            self._choice_btns.append(btn)
            self._choices_grid.addWidget(btn, i // 2, i % 2)

        choices_card = GlassCard(self, radius=20)
        cl = QVBoxLayout(choices_card)
        cl.setContentsMargins(16, 14, 16, 14)
        cl.addLayout(self._choices_grid)
        layout.addWidget(choices_card)

        self._feedback = QLabel("")
        self._feedback.setAlignment(Qt.AlignCenter)
        self._feedback.setStyleSheet(f"font-size: 16px; font-weight: 700; padding: 8px;")
        layout.addWidget(self._feedback)

    def _speak_sound(self):
        try:
            from speech.tts_engine import speak
            speak(self._sound_lbl.text(), self._child_id, force_lang="en")
        except Exception:
            pass

    def _next_round(self):
        if self._round >= self._total:
            self._feedback.setText(f"🎉 You scored {self._score}/{self._total}!")
            self.game_complete.emit(self._score)
            return
        self._round += 1
        self._round_lbl.setText(f"Round {self._round} of {self._total}  ·  Score: {self._score}")
        self._feedback.setText("")
        target = random.choice(self.ANIMALS)
        self._target = target
        self._sound_lbl.setText(target[3])
        self._speak_sound()

        choices = random.sample(self.ANIMALS, 4)
        if target not in choices:
            choices[0] = target
            random.shuffle(choices)
        for i, btn in enumerate(self._choice_btns):
            a = choices[i]
            btn.setText(f"{a[1]}\n{a[2]}")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255,255,255,0.92);
                    border: 2px solid rgba(0,191,168,0.3); border-radius: 14px;
                    font-size: 22px; font-weight: 700; color: {COLORS['text']};
                }}
                QPushButton:hover {{ background: rgba(0,191,168,0.15); border-color: {COLORS['teal']}; }}
            """)
            try:
                btn.clicked.disconnect()
            except Exception:
                pass
            btn.clicked.connect(lambda checked, k=a[0], n=a[2]: self._check(k, n))

    def _check(self, key, name):
        if key == self._target[0]:
            self._score += 1
            self._feedback.setText(f"✅ Yes! It's a {self._target[2]}!")
            self._feedback.setStyleSheet(f"font-size: 16px; color: {COLORS['success']}; font-weight: 700; padding: 8px;")
        else:
            self._feedback.setText(f"💙 It was a {self._target[2]}. Good try!")
            self._feedback.setStyleSheet(f"font-size: 14px; color: {COLORS['teal_deep']}; padding: 8px;")
        QTimer.singleShot(1500, self._next_round)


# ══════════════════════════════════════════════════════════════
#  Counting Game
# ══════════════════════════════════════════════════════════════
class CountingGame(QWidget):
    game_complete = Signal(int)

    OBJECTS = ["🍎", "🌟", "🐱", "🚗", "🎈", "🦋", "🌸", "🍪"]

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._score = 0
        self._round = 0
        self._total = 5
        self._build_ui()
        self._next_round()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)
        title = QLabel("🔢 Number Counting")
        title.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {COLORS['text']};")
        layout.addWidget(title)

        self._round_lbl = QLabel("")
        self._round_lbl.setStyleSheet(f"font-size: 13px; color: {COLORS['teal_deep']}; font-weight: 600;")
        layout.addWidget(self._round_lbl)

        objects_card = GlassCard(self, radius=22)
        ol = QVBoxLayout(objects_card)
        ol.setContentsMargins(20, 24, 20, 24)
        ol.setAlignment(Qt.AlignCenter)
        self._objects_lbl = QLabel("")
        self._objects_lbl.setAlignment(Qt.AlignCenter)
        self._objects_lbl.setWordWrap(True)
        self._objects_lbl.setStyleSheet("font-size: 48px; padding: 20px;")
        ol.addWidget(self._objects_lbl)
        question = QLabel("How many do you see?")
        question.setAlignment(Qt.AlignCenter)
        question.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {COLORS['text']};")
        ol.addWidget(question)
        layout.addWidget(objects_card)

        nums_grid = QGridLayout()
        nums_grid.setSpacing(8)
        self._num_btns = []
        for i, n in enumerate([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]):
            btn = QPushButton(str(n))
            btn.setFixedSize(70, 70)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #00BFA8, stop:1 #00E5FF);
                    color: white; border: none; border-radius: 35px;
                    font-size: 24px; font-weight: 900;
                }}
                QPushButton:hover {{ background: #5CE5DC; }}
            """)
            btn.clicked.connect(lambda checked, num=n: self._check(num))
            self._num_btns.append(btn)
            nums_grid.addWidget(btn, i // 5, i % 5)

        nums_card = GlassCard(self, radius=20)
        nl = QVBoxLayout(nums_card)
        nl.setContentsMargins(16, 14, 16, 14)
        nl.addLayout(nums_grid)
        layout.addWidget(nums_card)

        self._feedback = QLabel("")
        self._feedback.setAlignment(Qt.AlignCenter)
        self._feedback.setStyleSheet(f"font-size: 16px; font-weight: 700; padding: 8px;")
        layout.addWidget(self._feedback)

    def _next_round(self):
        if self._round >= self._total:
            self._feedback.setText(f"🎉 You scored {self._score}/{self._total}!")
            self.game_complete.emit(self._score)
            return
        self._round += 1
        self._round_lbl.setText(f"Round {self._round} of {self._total}  ·  Score: {self._score}")
        self._feedback.setText("")
        self._target_count = random.randint(1, 8)
        emoji = random.choice(self.OBJECTS)
        self._objects_lbl.setText(emoji * self._target_count)

    def _check(self, n):
        if n == self._target_count:
            self._score += 1
            self._feedback.setText(f"✅ Correct! There were {n}!")
            self._feedback.setStyleSheet(f"font-size: 16px; color: {COLORS['success']}; font-weight: 700; padding: 8px;")
        else:
            self._feedback.setText(f"💙 There were {self._target_count}. Try again!")
            self._feedback.setStyleSheet(f"font-size: 14px; color: {COLORS['teal_deep']}; padding: 8px;")
        QTimer.singleShot(1500, self._next_round)


# ══════════════════════════════════════════════════════════════
#  Opposites Game
# ══════════════════════════════════════════════════════════════
class OppositesGame(QWidget):
    game_complete = Signal(int)

    PAIRS = [
        ("🌞", "Hot",   "🥶", "Cold"),
        ("⬆️", "Up",    "⬇️", "Down"),
        ("📏", "Big",   "🐜", "Small"),
        ("🌅", "Day",   "🌃", "Night"),
        ("😊", "Happy", "😢", "Sad"),
        ("🐢", "Slow",  "🐇", "Fast"),
        ("🌟", "Light", "🌑", "Dark"),
    ]

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._score = 0
        self._round = 0
        self._total = 5
        self._build_ui()
        self._next_round()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)
        title = QLabel("↔️ Opposites")
        title.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {COLORS['text']};")
        layout.addWidget(title)
        self._round_lbl = QLabel("")
        self._round_lbl.setStyleSheet(f"font-size: 13px; color: {COLORS['teal_deep']}; font-weight: 600;")
        layout.addWidget(self._round_lbl)

        target_card = GlassCard(self, radius=22)
        tl = QVBoxLayout(target_card)
        tl.setContentsMargins(20, 22, 20, 22)
        tl.setAlignment(Qt.AlignCenter)
        self._target_lbl = QLabel("")
        self._target_lbl.setAlignment(Qt.AlignCenter)
        self._target_lbl.setStyleSheet("font-size: 64px;")
        tl.addWidget(self._target_lbl)
        self._target_word = QLabel("")
        self._target_word.setAlignment(Qt.AlignCenter)
        self._target_word.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {COLORS['text']};")
        tl.addWidget(self._target_word)
        question = QLabel("What is the opposite?")
        question.setAlignment(Qt.AlignCenter)
        question.setStyleSheet(f"font-size: 14px; color: {COLORS['text_light']};")
        tl.addWidget(question)
        layout.addWidget(target_card)

        self._choices_grid = QGridLayout()
        self._choices_grid.setSpacing(10)
        self._choice_btns = []
        for i in range(4):
            btn = QPushButton()
            btn.setFixedSize(140, 80)
            self._choice_btns.append(btn)
            self._choices_grid.addWidget(btn, i // 2, i % 2)
        choices_card = GlassCard(self, radius=20)
        cl = QVBoxLayout(choices_card)
        cl.setContentsMargins(16, 14, 16, 14)
        cl.addLayout(self._choices_grid)
        layout.addWidget(choices_card)

        self._feedback = QLabel("")
        self._feedback.setAlignment(Qt.AlignCenter)
        self._feedback.setStyleSheet(f"font-size: 16px; font-weight: 700; padding: 8px;")
        layout.addWidget(self._feedback)

    def _next_round(self):
        if self._round >= self._total:
            self._feedback.setText(f"🎉 You scored {self._score}/{self._total}!")
            self.game_complete.emit(self._score)
            return
        self._round += 1
        self._round_lbl.setText(f"Round {self._round} of {self._total}  ·  Score: {self._score}")
        self._feedback.setText("")

        pair = random.choice(self.PAIRS)
        # Show first item, ask for second
        if random.random() > 0.5:
            self._target_lbl.setText(pair[0]); self._target_word.setText(pair[1])
            correct = (pair[2], pair[3])
        else:
            self._target_lbl.setText(pair[2]); self._target_word.setText(pair[3])
            correct = (pair[0], pair[1])
        self._correct_word = correct[1]

        # 4 choices including correct
        choices = []
        choices.append(correct)
        wrong_pool = [(p[0], p[1]) for p in self.PAIRS if p[0] != correct[0]] + \
                     [(p[2], p[3]) for p in self.PAIRS if p[2] != correct[0]]
        random.shuffle(wrong_pool)
        choices.extend(wrong_pool[:3])
        random.shuffle(choices)

        for i, btn in enumerate(self._choice_btns):
            emoji, word = choices[i]
            btn.setText(f"{emoji}  {word}")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255,255,255,0.92);
                    border: 2px solid rgba(0,191,168,0.3); border-radius: 14px;
                    font-size: 18px; font-weight: 700; color: {COLORS['text']};
                }}
                QPushButton:hover {{ background: rgba(0,191,168,0.15); border-color: {COLORS['teal']}; }}
            """)
            try:
                btn.clicked.disconnect()
            except Exception:
                pass
            btn.clicked.connect(lambda checked, w=word: self._check(w))

    def _check(self, word):
        if word == self._correct_word:
            self._score += 1
            self._feedback.setText(f"✅ Yes! {word} is the opposite!")
            self._feedback.setStyleSheet(f"font-size: 16px; color: {COLORS['success']}; font-weight: 700; padding: 8px;")
        else:
            self._feedback.setText(f"💙 The opposite was {self._correct_word}.")
            self._feedback.setStyleSheet(f"font-size: 14px; color: {COLORS['teal_deep']}; padding: 8px;")
        QTimer.singleShot(1500, self._next_round)


# ══════════════════════════════════════════════════════════════
#  Games Lobby
# ══════════════════════════════════════════════════════════════
class GamesScreen(QWidget):
    go_back = Signal()

    GAMES = [
        ("emotion_match", "😊", "Emotion Matching",   "Match ARIA's feeling",    "#4CAF90", "All ages"),
        ("color_sort",    "🎨", "Color Sorting",       "Sort colorful balls",     "#38B8B0", "Age 3+"),
        ("routine_order", "📅", "Routine Ordering",    "Order the daily routine", "#6B9FD4", "Age 5+"),
        ("memory",        "🧠", "Memory Match",        "Find matching pairs",     "#D8A0E8", "Age 4+"),
        ("shape_match",   "🔷", "Shape Matching",      "Match shapes to outlines","#F0C040", "Age 3+"),
        ("animals",       "🐶", "Animal Sounds",       "Match animals to sounds", "#FFB347", "Age 3+"),
        ("counting",      "🔢", "Number Counting",     "Count objects",           "#7FFFD4", "Age 4+"),
        ("opposite",      "↔️", "Opposites",            "Find opposite pairs",     "#A695FF", "Age 5+"),
    ]

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._child_data = db.get_child(child_id) or {}
        self.setStyleSheet(MAIN_STYLE)
        self._stack = QStackedWidget(self)
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(self._stack)
        self._stack.addWidget(self._build_lobby())
        # Game screens added on demand

    def _build_lobby(self):
        w = QWidget()
        self._bg = ParticleBackground(w)
        layout = QVBoxLayout(w)
        layout.setContentsMargins(36, 28, 36, 28)
        layout.setSpacing(16)

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
        title = QLabel("🎮 Games & Activities")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {COLORS['text']};")
        hdr.addWidget(back_btn)
        hdr.addSpacing(20)
        hdr.addWidget(title)
        hdr.addStretch()
        layout.addLayout(hdr)

        lang = self._child_data.get("language", "en")
        subs = {
            "en": "Choose a fun game to play with ARIA! 🌟",
            "ar": "اختار لعبة تلعبها مع أريا! 🌟",
            "de": "Wähle ein Spiel mit ARIA! 🌟",
        }
        sub = QLabel(subs.get(lang, subs["en"]))
        sub.setStyleSheet(f"font-size: 14px; color: {COLORS['text_light']};")
        layout.addWidget(sub)

        # Game cards grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        grid_w = QWidget()
        grid_w.setStyleSheet("background: transparent;")
        grid = QGridLayout(grid_w)
        grid.setSpacing(16)
        grid.setContentsMargins(0, 0, 0, 0)

        for i, (key, icon, title, desc, color, age) in enumerate(self.GAMES):
            card = self._game_card(key, icon, title, desc, color, age)
            grid.addWidget(card, i // 4, i % 4)

        scroll.setWidget(grid_w)
        layout.addWidget(scroll, 1)
        return w

    def _game_card(self, key, icon, title, desc, color, age):
        card = GlassCard(self, radius=22, hover_lift=True)
        card.setFixedHeight(160)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 16)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 36px; background: transparent;")
        age_lbl = QLabel(age)
        age_lbl.setStyleSheet(f"""
            font-size: 10px; color: white; background: {color};
            border-radius: 10px; padding: 3px 10px; font-weight: 600;
        """)
        top_row.addWidget(icon_lbl)
        top_row.addStretch()
        top_row.addWidget(age_lbl)
        layout.addLayout(top_row)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {COLORS['text']}; background: transparent;")
        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet(f"font-size: 12px; color: {COLORS['text_light']}; background: transparent;")

        layout.addWidget(title_lbl)
        layout.addWidget(desc_lbl)
        layout.addStretch()

        play_btn = QPushButton("Play →")
        play_btn.setStyleSheet(f"""
            QPushButton {{
                background: {color}22; color: {color};
                border: 1.5px solid {color}66; border-radius: 10px;
                padding: 6px 16px; font-size: 12px; font-weight: 700;
            }}
            QPushButton:hover {{ background: {color}44; }}
        """)
        play_btn.clicked.connect(lambda checked, k=key: self._launch_game(k))
        layout.addWidget(play_btn, alignment=Qt.AlignRight)
        return card

    def _launch_game(self, key):
        try:
            if key == "emotion_match":
                game_w = EmotionMatchingGame(self._child_id, self)
            elif key == "color_sort":
                game_w = ColorSortGame(self._child_id, self)
            elif key == "routine_order":
                game_w = RoutineOrderGame(self._child_id, self)
            elif key == "memory":
                game_w = MemoryMatchGame(self._child_id, self)
            elif key == "shape_match":
                game_w = ShapeMatchGame(self._child_id, self)
            elif key == "animals":
                game_w = AnimalSoundsGame(self._child_id, self)
            elif key == "counting":
                game_w = CountingGame(self._child_id, self)
            elif key == "opposite":
                game_w = OppositesGame(self._child_id, self)
            else:
                return
        except Exception as e:
            import traceback; traceback.print_exc()
            return

        # Intelligence bus: every finished game earns a star and feeds the
        # session context (the shell's AI suggestion card reads this).
        if hasattr(game_w, "game_complete"):
            def _won(score, k=key):
                try:
                    from core.child_context import get_context
                    get_context().record_activity(
                        f"game:{k}", "won", award=1,
                        reason=f"{k} score {score}")
                except Exception:
                    pass
            game_w.game_complete.connect(_won)

        # Wrap with back button
        wrapper = QWidget()
        vl = QVBoxLayout(wrapper)
        vl.setContentsMargins(24, 16, 24, 16)

        back_btn = QPushButton("← Back to Games")
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(56,184,176,0.10); color: {COLORS['teal_deep']};
                border: 1.5px solid {COLORS['teal']}; border-radius: 10px;
                padding: 8px 16px; font-size: 12px; font-weight: 600;
                max-width: 160px;
            }}
            QPushButton:hover {{ background: rgba(56,184,176,0.22); }}
        """)
        back_btn.clicked.connect(lambda: self._stack.setCurrentIndex(0))
        vl.addWidget(back_btn)
        vl.addWidget(game_w, 1)

        self._stack.addWidget(wrapper)
        self._stack.setCurrentWidget(wrapper)

    def resizeEvent(self, event):
        if hasattr(self, '_bg'):
            self._bg.resize(self.size())
        super().resizeEvent(event)
