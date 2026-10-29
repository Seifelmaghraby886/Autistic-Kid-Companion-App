"""
ARIA AI Coping Coach
Gemini-powered personalized coping strategy generator based on real-time emotion + child profile.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QTextEdit
)
from PySide6.QtCore import Qt, Signal, QThread, QObject

from ui.components import GlassCard, ARIAFaceWidget
from ui.animated_bg import MeshBackground
from ui.styles import MAIN_STYLE, COLORS
import database.db_manager as db


class CoachWorker(QObject):
    suggestions_ready = Signal(list)
    error = Signal(str)

    def __init__(self, child_id, current_feeling):
        super().__init__()
        self._child_id = child_id
        self._feeling = current_feeling

    def run(self):
        try:
            import json
            from pathlib import Path
            cfg_path = Path(__file__).parent.parent / "config" / "app_config.json"
            with open(cfg_path) as f:
                cfg = json.load(f)
            api_key = cfg.get("gemini_api_key", "").strip()
            model_name = cfg.get("gemini_model", "gemini-2.0-flash")
            if not api_key:
                self._fallback()
                return

            child = db.get_child(self._child_id) or {}
            prefs = db.get_child_preferences(self._child_id)
            lang = child.get("language", "en")
            name = child.get("name", "the child")
            age = child.get("age", 7)

            lang_names = {"en": "English", "ar": "Egyptian Arabic", "de": "German"}

            import google.generativeai as genai
            genai.configure(api_key=api_key)

            prompt = f"""You are an autism support coach.

Child profile:
- Name: {name}
- Age: {age}
- Language: {lang_names.get(lang, 'English')}
- Known triggers: {', '.join(prefs.get('known_triggers', []))}
- Calming methods that work: {', '.join(prefs.get('calming_methods', []))}
- Favorite topics: {', '.join(prefs.get('favorite_topics', []))}

Current feeling: {self._feeling}

Suggest 3 personalized, actionable, immediate coping strategies for this autistic child right now.
Each suggestion should be:
- Concrete (something to DO right now)
- Sensory-aware
- Aligned with the child's known triggers/calming methods
- 1-2 short sentences in {lang_names.get(lang, 'English')}

Return ONLY a JSON array with 3 objects, each having "title" and "description" fields.
Example: [{{"title": "Deep breaths", "description": "Take 5 slow breaths counting in your head"}}, ...]
NO markdown, NO explanation, JUST the JSON array."""

            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            raw = response.text.strip()
            import re
            raw = re.sub(r'```(?:json)?', '', raw).strip()
            match = re.search(r'\[.*\]', raw, re.DOTALL)
            if match:
                suggestions = json.loads(match.group())
                self.suggestions_ready.emit(suggestions[:3])
            else:
                self._fallback()
        except Exception as e:
            print(f"[Coach error: {e}]")
            self._fallback()

    def _fallback(self):
        self.suggestions_ready.emit([
            {"title": "Slow breathing", "description": "Breathe in for 4, hold for 4, out for 4. Repeat 5 times."},
            {"title": "Quiet space", "description": "Find a calm, low-stimulation spot for a few minutes."},
            {"title": "Favorite topic", "description": "Think about your favorite topic to help your mind feel safe."},
        ])


class SuggestionCard(QWidget):
    def __init__(self, num, title, desc, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(110)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        num_lbl = QLabel(str(num))
        num_lbl.setFixedSize(50, 50)
        num_lbl.setAlignment(Qt.AlignCenter)
        num_lbl.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 #00BFA8, stop:1 #00E5FF);
            color: white;
            border-radius: 25px;
            font-size: 22px; font-weight: 900;
        """)

        col = QVBoxLayout()
        col.setSpacing(4)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {COLORS['text']};")
        title_lbl.setWordWrap(True)
        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet(f"font-size: 13px; color: {COLORS['text_light']}; line-height: 1.5;")
        desc_lbl.setWordWrap(True)
        col.addWidget(title_lbl)
        col.addWidget(desc_lbl)

        layout.addWidget(num_lbl)
        layout.addLayout(col, 1)

        self.setStyleSheet(f"""
            QWidget {{
                background: rgba(255,255,255,0.92);
                border: 1.5px solid rgba(0,191,168,0.25);
                border-radius: 18px;
            }}
        """)


class AICoachScreen(QWidget):
    go_back = Signal()

    FEELINGS = [
        ("😊", "Happy",     "happy",     "#00D9A0"),
        ("😢", "Sad",       "sad",       "#6B9FE8"),
        ("😨", "Anxious",   "anxious",   "#A695FF"),
        ("😤", "Frustrated","frustrated","#FF8B5C"),
        ("😴", "Tired",     "tired",     "#A8B8D0"),
        ("🤯", "Overwhelmed","overwhelmed","#FF6B7E"),
    ]

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._child_data = db.get_child(child_id) or {}
        self.setStyleSheet(MAIN_STYLE)
        self._build_ui()

    def _build_ui(self):
        self._bg = MeshBackground(self)
        self._bg.lower()

        main = QVBoxLayout(self)
        main.setContentsMargins(32, 24, 32, 24)
        main.setSpacing(14)

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
        title = QLabel("🧠 AI Coping Coach")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {COLORS['text']};")
        sub = QLabel("Personalized strategies powered by AI")
        sub.setStyleSheet(f"font-size: 13px; color: {COLORS['text_light']};")
        hdr.addWidget(back_btn)
        hdr.addSpacing(20)
        col = QVBoxLayout()
        col.addWidget(title)
        col.addWidget(sub)
        hdr.addLayout(col)
        hdr.addStretch()
        main.addLayout(hdr)

        # Feeling buttons
        feel_card = GlassCard(self, radius=22)
        fl = QVBoxLayout(feel_card)
        fl.setContentsMargins(24, 18, 24, 18)
        fl.setSpacing(10)
        prompt_lbl = QLabel("How are you feeling right now?")
        prompt_lbl.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {COLORS['text']};")
        fl.addWidget(prompt_lbl)

        feel_row = QHBoxLayout()
        feel_row.setSpacing(10)
        for icon, label, key, color in self.FEELINGS:
            btn = QPushButton(f"{icon}\n{label}")
            btn.setFixedSize(110, 90)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255,255,255,0.85);
                    border: 2px solid {color}55;
                    border-radius: 18px;
                    color: {COLORS['text']};
                    font-size: 13px; font-weight: 700;
                    padding: 4px;
                }}
                QPushButton:hover {{
                    background: {color}22;
                    border-color: {color};
                }}
            """)
            btn.clicked.connect(lambda checked, k=key, l=label: self._get_suggestions(k, l))
            feel_row.addWidget(btn)
        feel_row.addStretch()
        fl.addLayout(feel_row)
        main.addWidget(feel_card)

        # Results
        self._results_card = GlassCard(self, radius=22)
        self._rl = QVBoxLayout(self._results_card)
        self._rl.setContentsMargins(20, 16, 20, 16)
        self._rl.setSpacing(10)

        self._aria_row = QHBoxLayout()
        self._face = ARIAFaceWidget(size=80)
        self._aria_msg = QLabel("Pick a feeling above and I'll give you 3 personalized strategies. ✨")
        self._aria_msg.setWordWrap(True)
        self._aria_msg.setStyleSheet(f"font-size: 14px; color: {COLORS['teal_deep']}; font-weight: 600;")
        self._aria_row.addWidget(self._face)
        self._aria_row.addWidget(self._aria_msg, 1)
        self._rl.addLayout(self._aria_row)

        self._suggestions_widget = QWidget()
        self._suggestions_widget.setStyleSheet("background: transparent;")
        self._sl = QVBoxLayout(self._suggestions_widget)
        self._sl.setSpacing(10)
        self._sl.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.setWidget(self._suggestions_widget)
        self._rl.addWidget(scroll, 1)
        main.addWidget(self._results_card, 1)

    def _get_suggestions(self, feeling_key, feeling_label):
        self._face.set_expression("thinking")
        self._aria_msg.setText(f"Thinking about how to help with {feeling_label.lower()}...")

        # Clear previous suggestions
        while self._sl.count():
            item = self._sl.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        loading = QLabel("✨ AI is generating strategies...")
        loading.setAlignment(Qt.AlignCenter)
        loading.setStyleSheet(f"font-size: 14px; color: {COLORS['text_light']}; padding: 30px;")
        self._sl.addWidget(loading)

        self._thread = QThread()
        self._worker = CoachWorker(self._child_id, feeling_key)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.suggestions_ready.connect(self._on_suggestions)
        self._thread.start()

    def _on_suggestions(self, suggestions):
        # Clear loading
        while self._sl.count():
            item = self._sl.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, s in enumerate(suggestions, 1):
            card = SuggestionCard(i, s.get("title", ""), s.get("description", ""))
            self._sl.addWidget(card)
        self._sl.addStretch()

        self._face.set_expression("happy")
        self._aria_msg.setText("Here are 3 strategies just for you. Try one! ✨")
        self._thread.quit()
