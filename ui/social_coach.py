"""
ARIA Social Skills Coach
AI-powered scenario practice for friendship, asking for help, and social situations.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QTextEdit, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QThread, QObject

from ui.components import GlassCard, ARIAFaceWidget
from ui.animated_bg import MeshBackground
from ui.styles import MAIN_STYLE, COLORS
import database.db_manager as db


SCENARIOS = [
    ("🤝", "Make a friend",          "I want to make a new friend at school"),
    ("🆘", "Ask for help",            "I'm stuck on something and need help"),
    ("🎁", "Share a toy",             "Someone wants to play with my toy"),
    ("😢", "Comfort someone",         "My friend is sad and I want to help"),
    ("🚫", "Say no politely",         "Someone wants me to do something I don't want"),
    ("💬", "Start a conversation",    "I want to talk to someone new"),
    ("🎂", "Go to a birthday party",  "I'm invited to a party"),
    ("🙋", "Raise my hand in class",  "I have a question in class"),
    ("🤐", "What if I'm bullied",     "Someone is being mean to me"),
    ("👋", "Say hi and bye",          "How to greet people"),
]


class CoachWorker(QObject):
    response_ready = Signal(dict)
    error = Signal(str)

    def __init__(self, scenario_text, child_id, user_input=""):
        super().__init__()
        self._scenario = scenario_text
        self._child_id = child_id
        self._user_input = user_input

    def run(self):
        try:
            import json
            from pathlib import Path
            cfg_path = Path(__file__).parent.parent / "config" / "app_config.json"
            with open(cfg_path) as f:
                cfg = json.load(f)

            child = db.get_child(self._child_id) or {}
            lang = child.get("language", "en")
            name = child.get("name", "the child")
            age = child.get("age", 7)
            lang_names = {"en": "English", "ar": "Egyptian Arabic عامية مصرية", "de": "simple German"}

            prompt = f"""You are a kind social skills coach for an autistic child named {name}, age {age}.

Scenario: {self._scenario}
{f"Child's input: {self._user_input}" if self._user_input else ""}

In {lang_names.get(lang, 'English')}, write a short JSON response with:
- "story": 2-3 sentence relatable scenario setup (in 1st person — "I am at school...")
- "options": array of 3-4 things they could say or do, each as object {{"text": "...", "emoji": "..."}}
- "best_choice_idx": index (0-based) of the best option
- "explanation": short kind explanation of why that option works
- "key_phrase": one short phrase the child can practice saying

Be warm, never preachy. Use child-level words. NO judgment.
Output ONLY valid JSON, no markdown."""

            # Try Groq first (free), then Gemini
            result = None
            try:
                if cfg.get("groq_api_key"):
                    from groq import Groq
                    client = Groq(api_key=cfg["groq_api_key"])
                    response = client.chat.completions.create(
                        model=cfg.get("groq_model", "llama-3.3-70b-versatile"),
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7, max_tokens=800,
                        response_format={"type": "json_object"},
                    )
                    raw = response.choices[0].message.content
                    result = json.loads(raw)
            except Exception as e:
                print(f"[Groq social: {e}]")

            if not result and cfg.get("gemini_api_key"):
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=cfg["gemini_api_key"])
                    model = genai.GenerativeModel(cfg.get("gemini_model", "gemini-2.5-flash"))
                    gc = genai.types.GenerationConfig(
                        temperature=0.7, max_output_tokens=1024,
                        response_mime_type="application/json",
                    )
                    r = model.generate_content(prompt, generation_config=gc)
                    import re
                    raw = re.sub(r'```(?:json)?', '', r.text).strip()
                    result = json.loads(raw)
                except Exception as e:
                    print(f"[Gemini social: {e}]")

            if result:
                self.response_ready.emit(result)
            else:
                self._fallback()
        except Exception as e:
            print(f"[Coach error: {e}]")
            self._fallback()

    def _fallback(self):
        self.response_ready.emit({
            "story": "Imagine you are in this situation...",
            "options": [
                {"text": "Take a deep breath first", "emoji": "🌬️"},
                {"text": "Ask a parent or teacher for help", "emoji": "🆘"},
                {"text": "Be kind to yourself — it's okay", "emoji": "💙"},
            ],
            "best_choice_idx": 1,
            "explanation": "Asking a trusted adult is always a good choice when unsure.",
            "key_phrase": "Can you help me, please?",
        })


class ScenarioCard(QWidget):
    selected = Signal(str, str)
    def __init__(self, icon, title, scenario, parent=None):
        super().__init__(parent)
        self._scenario = scenario
        self._title = title
        self.setMinimumHeight(80)
        self.setCursor(Qt.PointingHandCursor)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 28px; background: transparent;")
        icon_lbl.setFixedWidth(40)

        text_lbl = QLabel(title)
        text_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLORS['text']}; background: transparent;")

        layout.addWidget(icon_lbl)
        layout.addWidget(text_lbl, 1)
        self.setStyleSheet(f"""
            QWidget {{
                background: rgba(255,255,255,0.85);
                border: 1.5px solid rgba(0,191,168,0.25);
                border-radius: 14px;
            }}
            QWidget:hover {{
                background: rgba(0,191,168,0.10);
                border-color: {COLORS['teal']};
            }}
        """)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.selected.emit(self._title, self._scenario)


class SocialCoachScreen(QWidget):
    go_back = Signal()

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._child = db.get_child(child_id) or {}
        self.setStyleSheet(MAIN_STYLE)
        self._build_ui()

    def _build_ui(self):
        self._bg = MeshBackground(self, intensity=0.5)
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
        title = QLabel("🤝 Social Skills Coach")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {COLORS['text']};")
        sub = QLabel("Practice tricky social situations with AI")
        sub.setStyleSheet(f"font-size: 13px; color: {COLORS['text_light']};")
        hdr.addWidget(back_btn); hdr.addSpacing(20)
        col = QVBoxLayout(); col.addWidget(title); col.addWidget(sub)
        hdr.addLayout(col); hdr.addStretch()
        main.addLayout(hdr)

        body = QHBoxLayout()
        body.setSpacing(16)

        # LEFT: scenario list
        left_card = GlassCard(self, radius=22)
        left_card.setMaximumWidth(280)
        ll = QVBoxLayout(left_card)
        ll.setContentsMargins(18, 14, 18, 14)
        ll.setSpacing(8)
        ll.addWidget(self._section("CHOOSE A SCENARIO"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        sw = QWidget()
        sw.setStyleSheet("background: transparent;")
        sl = QVBoxLayout(sw)
        sl.setSpacing(8)
        sl.setContentsMargins(0, 0, 8, 0)
        for icon, title, scenario in SCENARIOS:
            card = ScenarioCard(icon, title, scenario)
            card.selected.connect(self._handle_scenario)
            sl.addWidget(card)
        sl.addStretch()
        scroll.setWidget(sw)
        ll.addWidget(scroll)
        body.addWidget(left_card)

        # RIGHT: AI response
        right_card = GlassCard(self, radius=22)
        rl = QVBoxLayout(right_card)
        rl.setContentsMargins(24, 20, 24, 20)
        rl.setSpacing(12)

        top = QHBoxLayout()
        self._face = ARIAFaceWidget(size=80)
        self._face.set_expression("happy")
        self._scenario_title = QLabel("Pick a scenario to practice")
        self._scenario_title.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {COLORS['text']};")
        self._scenario_title.setWordWrap(True)
        top.addWidget(self._face)
        top.addSpacing(10)
        top.addWidget(self._scenario_title, 1)
        rl.addLayout(top)

        # Story
        self._story_lbl = QLabel("ARIA will help you practice tricky social moments. Pick one from the left! 💚")
        self._story_lbl.setWordWrap(True)
        self._story_lbl.setStyleSheet(f"""
            background: rgba(0,191,168,0.10);
            border-left: 4px solid {COLORS['teal']};
            border-radius: 10px;
            padding: 14px 18px;
            font-size: 14px; color: {COLORS['text']};
            line-height: 1.7;
        """)
        rl.addWidget(self._story_lbl)

        # Options container
        self._options_widget = QWidget()
        self._options_widget.setStyleSheet("background: transparent;")
        self._options_layout = QVBoxLayout(self._options_widget)
        self._options_layout.setSpacing(8)
        self._options_layout.setContentsMargins(0, 0, 0, 0)
        rl.addWidget(self._options_widget)

        # Explanation
        self._explanation_lbl = QLabel("")
        self._explanation_lbl.setWordWrap(True)
        self._explanation_lbl.setStyleSheet(f"""
            font-size: 13px; color: {COLORS['text_light']};
            font-style: italic; padding: 8px 0;
        """)
        rl.addWidget(self._explanation_lbl)

        # Key phrase
        self._phrase_card = QLabel("")
        self._phrase_card.setWordWrap(True)
        self._phrase_card.setAlignment(Qt.AlignCenter)
        self._phrase_card.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 rgba(0,191,168,0.15), stop:1 rgba(179,136,255,0.15));
            border: 1.5px solid rgba(0,191,168,0.3);
            border-radius: 14px;
            padding: 14px;
            font-size: 16px; font-weight: 700;
            color: {COLORS['teal_deep']};
        """)
        self._phrase_card.setVisible(False)
        rl.addWidget(self._phrase_card)

        rl.addStretch()
        body.addWidget(right_card, 1)
        main.addLayout(body, 1)

    def _section(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {COLORS['teal_deep']}; letter-spacing: 2px;")
        return lbl

    def _handle_scenario(self, title, scenario):
        self._scenario_title.setText(f"📚  {title}")
        self._story_lbl.setText("✨ ARIA is preparing your practice...")
        self._face.set_expression("thinking")
        # Clear options
        while self._options_layout.count():
            item = self._options_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._explanation_lbl.setText("")
        self._phrase_card.setVisible(False)

        self._thread = QThread()
        self._worker = CoachWorker(scenario, self._child_id)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.response_ready.connect(self._on_response)
        self._thread.start()

    def _on_response(self, data):
        story = data.get("story", "")
        options = data.get("options", [])
        best = data.get("best_choice_idx", -1)
        explanation = data.get("explanation", "")
        phrase = data.get("key_phrase", "")

        self._story_lbl.setText(story)
        self._face.set_expression("happy")

        for i, opt in enumerate(options):
            text = opt.get("text", "")
            emoji = opt.get("emoji", "•")
            btn = QPushButton(f"{emoji}  {text}")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255,255,255,0.85);
                    color: {COLORS['text']};
                    border: 1.5px solid rgba(0,191,168,0.25);
                    border-radius: 12px;
                    padding: 12px 18px;
                    font-size: 13px; font-weight: 600;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background: rgba(0,191,168,0.15);
                    border-color: {COLORS['teal']};
                }}
            """)
            btn.clicked.connect(lambda checked, idx=i, b=best, ex=explanation, ph=phrase:
                                self._reveal(idx, b, ex, ph))
            self._options_layout.addWidget(btn)

        try:
            self._thread.quit()
        except Exception:
            pass

    def _reveal(self, chosen_idx, best_idx, explanation, phrase):
        if chosen_idx == best_idx:
            self._explanation_lbl.setText(f"✅ Great choice! {explanation}")
            self._explanation_lbl.setStyleSheet(f"font-size: 13px; color: #00BFA8; font-weight: 600; padding: 8px 0;")
            self._face.set_expression("happy")
        else:
            self._explanation_lbl.setText(f"💙 That's okay. The best choice would be #{best_idx + 1}. {explanation}")
            self._explanation_lbl.setStyleSheet(f"font-size: 13px; color: {COLORS['teal_deep']}; padding: 8px 0;")
            self._face.set_expression("calm")

        if phrase:
            self._phrase_card.setText(f"💬  Practice saying:  \"{phrase}\"")
            self._phrase_card.setVisible(True)
            try:
                from speech.tts_engine import speak
                speak(phrase, self._child_id, style="very_slow")
            except Exception:
                pass

    def resizeEvent(self, event):
        if hasattr(self, '_bg'):
            self._bg.resize(self.size())
        super().resizeEvent(event)
