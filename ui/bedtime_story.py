"""
ARIA AI Bedtime Story Generator
Personalized calming stories with the child as the hero — TTS narration.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QTextEdit, QComboBox
)
from PySide6.QtCore import Qt, Signal, QThread, QObject, QTimer

from ui.components import GlassCard, ARIAFaceWidget
from ui.animated_bg import MeshBackground
from ui.styles import MAIN_STYLE, COLORS
import database.db_manager as db


class BedtimeStoryWorker(QObject):
    story_ready = Signal(str, str)  # title, body
    error = Signal(str)

    def __init__(self, child_id, theme):
        super().__init__()
        self._child_id = child_id
        self._theme = theme

    def run(self):
        try:
            child = db.get_child(self._child_id) or {}
            prefs = db.get_child_preferences(self._child_id)
            lang = child.get("language", "en")
            name = child.get("name", "the child")
            age = child.get("age", 7)
            topics = ", ".join(prefs.get("favorite_topics", []) or ["adventure"])

            lang_names = {
                "en": "English",
                "ar": "Egyptian Arabic عامية مصرية (NEVER MSA)",
                "de": "simple German",
            }

            prompt = f"""Write a calming bedtime story for {name}, age {age}, an autistic child.

Theme: {self._theme}
Child's favorite topics: {topics}
Language: {lang_names.get(lang, 'English')}

Rules:
- Write in {lang_names.get(lang, 'English')} ONLY
- Make {name} the hero of the story
- 8-12 short, calming sentences
- Include sensory descriptions (soft sounds, gentle colors, warm feelings)
- Predictable, reassuring narrative
- End with {name} feeling safe, calm, and ready to sleep
- NO scary elements, NO conflict, NO surprises
- Use child's favorite topics naturally

Return JSON: {{"title": "story title", "body": "the full story text"}}
NO markdown, NO explanation, JUST JSON."""

            from ai.multi_provider import generate_text
            raw = generate_text(prompt, json_mode=True, max_tokens=1024)

            if raw:
                import json, re
                raw = re.sub(r'```(?:json)?', '', raw).strip()
                match = re.search(r'\{.*\}', raw, re.DOTALL)
                if match:
                    try:
                        data = json.loads(match.group())
                        title = data.get("title", "A Bedtime Story")
                        body = data.get("body", "")
                        if lang == "ar":
                            try:
                                from ai.egyptian_polish import polish_to_egyptian
                                title = polish_to_egyptian(title)
                                body = polish_to_egyptian(body)
                            except Exception:
                                pass
                        self.story_ready.emit(title, body)
                        return
                    except json.JSONDecodeError:
                        pass
            self._fallback()
        except Exception as e:
            print(f"[Bedtime story error: {e}]")
            self._fallback()

    def _fallback(self):
        self.story_ready.emit(
            "A Quiet Night",
            "Once upon a time, in a soft cozy room, a brave child closed their eyes.\n"
            "Outside the window, the moon shone gently like a silver lamp.\n"
            "The world was quiet and safe.\n"
            "Soft pillows surrounded the child like clouds.\n"
            "Warm blankets felt like a hug.\n"
            "Slowly, slowly, breathing in and out, the child felt peaceful.\n"
            "Stars twinkled hello, then waved goodnight.\n"
            "Everything was calm.\n"
            "The end. Sweet dreams. 🌙"
        )


class BedtimeStoryScreen(QWidget):
    go_back = Signal()

    THEMES = [
        ("🌙", "Cozy Night",       "a quiet peaceful night"),
        ("🚀", "Space Adventure",  "a calm trip to the stars"),
        ("🌳", "Forest Walk",      "a gentle walk in a friendly forest"),
        ("🏰", "Castle Dream",     "visiting a friendly magical castle"),
        ("🐠", "Ocean Sleep",      "swimming gently with friendly fish"),
        ("☁️", "Cloud Journey",    "floating softly on a cloud"),
    ]

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._child_data = db.get_child(child_id) or {}
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
        title = QLabel("🌙 AI Bedtime Story")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {COLORS['text']};")
        sub = QLabel("Personalized calming stories with you as the hero")
        sub.setStyleSheet(f"font-size: 13px; color: {COLORS['text_light']};")
        hdr.addWidget(back_btn); hdr.addSpacing(20)
        col = QVBoxLayout(); col.addWidget(title); col.addWidget(sub)
        hdr.addLayout(col); hdr.addStretch()
        main.addLayout(hdr)

        body = QHBoxLayout()
        body.setSpacing(18)

        # LEFT: themes
        left_card = GlassCard(self, radius=22)
        left_card.setMaximumWidth(290)
        ll = QVBoxLayout(left_card)
        ll.setContentsMargins(20, 16, 20, 16)
        ll.setSpacing(10)
        ll.addWidget(self._section("PICK A THEME"))
        for icon, name, theme in self.THEMES:
            btn = QPushButton(f"{icon}  {name}")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255,255,255,0.85);
                    color: {COLORS['text']};
                    border: 1.5px solid rgba(0,191,168,0.25);
                    border-radius: 14px; padding: 12px 16px;
                    font-size: 13px; font-weight: 600;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 rgba(0,191,168,0.20), stop:1 rgba(179,136,255,0.20));
                    border-color: {COLORS['teal']};
                }}
            """)
            btn.clicked.connect(lambda checked, t=theme, n=name: self._generate(t, n))
            ll.addWidget(btn)
        ll.addStretch()
        body.addWidget(left_card)

        # RIGHT: story display
        story_card = GlassCard(self, radius=22)
        sl = QVBoxLayout(story_card)
        sl.setContentsMargins(28, 22, 28, 22)
        sl.setSpacing(14)

        top = QHBoxLayout()
        self._face = ARIAFaceWidget(size=90)
        self._face.set_expression("comfort")
        title_col = QVBoxLayout()
        self._story_title = QLabel("Choose a theme to begin...")
        self._story_title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {COLORS['text']};")
        self._story_title.setWordWrap(True)
        self._aria_status = QLabel("ARIA will write a personal story for you 💙")
        self._aria_status.setStyleSheet(f"font-size: 13px; color: {COLORS['teal_deep']}; font-weight: 600;")
        self._aria_status.setWordWrap(True)
        title_col.addWidget(self._story_title)
        title_col.addWidget(self._aria_status)
        top.addWidget(self._face)
        top.addLayout(title_col, 1)
        sl.addLayout(top)

        self._story_text = QTextEdit()
        self._story_text.setReadOnly(True)
        self._story_text.setPlaceholderText("Your personalized story will appear here...")
        self._story_text.setStyleSheet(f"""
            QTextEdit {{
                background: rgba(255,255,255,0.95);
                border: 1px solid rgba(0,191,168,0.2);
                border-radius: 16px;
                padding: 22px;
                font-size: 18px;
                color: {COLORS['text']};
                line-height: 2.0;
                font-family: 'Georgia', serif;
            }}
        """)
        sl.addWidget(self._story_text, 1)

        ctrl_row = QHBoxLayout()
        self._read_btn = QPushButton("🔊  Narrate Story")
        self._read_btn.setEnabled(False)
        self._read_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #00BFA8, stop:0.5 #00E5FF, stop:1 #B388FF);
                color: white; border: none; border-radius: 14px;
                padding: 11px 28px; font-size: 13px; font-weight: 700;
            }}
            QPushButton:disabled {{ background: #C0C8D4; color: #8A9CB8; }}
        """)
        self._read_btn.clicked.connect(self._narrate)
        stop_btn = QPushButton("⏹  Stop")
        stop_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,107,126,0.12); color: #C04055;
                border: 1.5px solid rgba(255,107,126,0.4); border-radius: 12px;
                padding: 10px 20px; font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(255,107,126,0.25); }}
        """)
        stop_btn.clicked.connect(self._stop_narration)
        ctrl_row.addWidget(self._read_btn)
        ctrl_row.addWidget(stop_btn)
        ctrl_row.addStretch()
        sl.addLayout(ctrl_row)

        body.addWidget(story_card, 1)
        main.addLayout(body, 1)

    def _section(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {COLORS['teal_deep']}; letter-spacing: 2px;")
        return lbl

    def _generate(self, theme, name):
        self._story_title.setText(f"✨ Writing your story...")
        self._story_text.setPlainText("")
        self._aria_status.setText("ARIA is thinking of a special story just for you...")
        self._face.set_expression("thinking")
        self._read_btn.setEnabled(False)

        self._thread = QThread()
        self._worker = BedtimeStoryWorker(self._child_id, theme)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.story_ready.connect(self._on_story)
        self._thread.start()

    def _on_story(self, title, body):
        self._story_title.setText(f"📖 {title}")
        self._story_text.setPlainText(body)
        self._aria_status.setText("Your story is ready. Tap Narrate to hear it. 🌙")
        self._face.set_expression("comfort")
        self._read_btn.setEnabled(True)
        try:
            self._thread.quit()
        except Exception:
            pass
        try:
            from core.child_context import get_context
            get_context().record_activity("bedtime", "story", award=1,
                                          reason="bedtime story")
        except Exception:
            pass

    def _narrate(self):
        text = self._story_text.toPlainText()
        if text:
            try:
                from speech.tts_engine import speak
                speak(text, self._child_id, style="very_slow")
                self._aria_status.setText("🔊 Reading your story softly...")
            except Exception:
                pass

    def _stop_narration(self):
        try:
            from speech.tts_engine import stop_speaking
            stop_speaking()
            self._aria_status.setText("Stopped.")
        except Exception:
            pass
