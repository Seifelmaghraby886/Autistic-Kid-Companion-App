"""
ARIA AI Social Story Generator
Generate custom social stories using Gemini for specific situations.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QTextEdit, QScrollArea, QLineEdit
)
from PySide6.QtCore import Qt, Signal, QThread, QObject
from PySide6.QtGui import QFont

from ui.components import GlassCard, ARIAFaceWidget, ParticleBackground, ToastNotification
from ui.styles import MAIN_STYLE, COLORS
import database.db_manager as db


PRESETS = [
    ("🏥", "Going to the doctor",       "doctor_visit"),
    ("✂️", "Getting a haircut",          "haircut"),
    ("🦷", "Visiting the dentist",       "dentist"),
    ("🛒", "Going to the supermarket",   "supermarket"),
    ("🎂", "Going to a birthday party",  "birthday_party"),
    ("📚", "First day of school",         "first_school"),
    ("✈️", "Flying on an airplane",      "airplane"),
    ("🚌", "Riding the bus",             "bus_ride"),
    ("🏊", "Going swimming",             "swimming"),
]


class StoryWorker(QObject):
    story_ready = Signal(str)
    error = Signal(str)

    def __init__(self, situation, child_id):
        super().__init__()
        self._situation = situation
        self._child_id = child_id

    def run(self):
        try:
            child = db.get_child(self._child_id) or {}
            lang = child.get("language", "en")
            name = child.get("name", "the child")
            age = child.get("age", 7)

            lang_names = {
                "en": "English",
                "ar": "Egyptian Arabic عامية مصرية (NEVER MSA, only colloquial)",
                "de": "simple German",
            }
            language_name = lang_names.get(lang, "English")

            prompt = f"""You are a social story author for autistic children.

Write a social story for a {age}-year-old autistic child named {name} about: {self._situation}

Rules:
- Write in {language_name}
- Use 5–8 short sentences
- Use first person ("I will...")
- Be calm, predictable, reassuring
- Describe what to expect step-by-step
- End with a positive coping statement
- NO scary details, NO sarcasm
- Use simple words for the age

Return ONLY the story text, no explanations, no markdown."""

            from ai.multi_provider import generate_text
            story = generate_text(prompt, max_tokens=800)
            if story:
                if lang == "ar":
                    try:
                        from ai.egyptian_polish import polish_to_egyptian
                        story = polish_to_egyptian(story)
                    except Exception:
                        pass
                self.story_ready.emit(story)
            else:
                self._fallback_story()
        except Exception as e:
            print(f"[Story error: {e}]")
            self._fallback_story()

    def _fallback_story(self):
        fallbacks = {
            "doctor_visit": "Today I will go to the doctor.\nThe doctor wears a white coat.\nThe doctor will look at me.\nThis helps keep me healthy.\nI can hold a toy if I feel scared.\nMy parent will be with me.\nGoing to the doctor is okay.",
            "haircut": "Today I will get a haircut.\nThe hair stylist will use scissors.\nThe scissors might make a small sound.\nMy hair does not feel anything.\nI will sit very still.\nWhen we're done, my hair will look nice.\nGetting a haircut is okay.",
        }
        self.story_ready.emit(fallbacks.get(
            self._situation,
            "I will try something new today.\nNew things can feel different.\nIt's okay to feel unsure.\nI can take slow breaths.\nMy parent will be with me.\nI am brave and capable.\nEverything will be okay."
        ))


class StoryGeneratorScreen(QWidget):
    go_back = Signal()

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._child_data = db.get_child(child_id) or {}
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
        title = QLabel("📖 Social Story Generator")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {COLORS['text']};")
        sub = QLabel("AI-powered stories for new situations")
        sub.setStyleSheet(f"font-size: 13px; color: {COLORS['text_light']};")
        hdr.addWidget(back_btn)
        hdr.addSpacing(20)
        col = QVBoxLayout()
        col.addWidget(title)
        col.addWidget(sub)
        hdr.addLayout(col)
        hdr.addStretch()
        main.addLayout(hdr)

        body = QHBoxLayout()
        body.setSpacing(16)

        # ── LEFT: Presets + custom input
        left = QVBoxLayout()
        left.setSpacing(14)

        preset_card = GlassCard(self, radius=20)
        pl = QVBoxLayout(preset_card)
        pl.setContentsMargins(20, 16, 20, 16)
        pl.addWidget(self._section("CHOOSE A SITUATION"))

        grid = QGridLayout()
        grid.setSpacing(8)
        for i, (icon, label, key) in enumerate(PRESETS):
            btn = QPushButton(f"{icon}  {label}")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255,255,255,0.85);
                    color: {COLORS['text']};
                    border: 1.5px solid rgba(56,184,176,0.25);
                    border-radius: 12px; padding: 10px 14px;
                    font-size: 12px; font-weight: 600;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background: rgba(56,184,176,0.15);
                    border-color: {COLORS['teal']};
                }}
            """)
            btn.clicked.connect(lambda checked, l=label: self._generate(l))
            grid.addWidget(btn, i // 2, i % 2)
        pl.addLayout(grid)

        pl.addSpacing(8)
        pl.addWidget(self._section("OR DESCRIBE A CUSTOM SITUATION"))
        self._custom_input = QLineEdit()
        self._custom_input.setPlaceholderText("e.g. Going to grandma's house...")
        pl.addWidget(self._custom_input)

        gen_btn = QPushButton("✨  Generate Story")
        gen_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #38B8B0, stop:0.5 #00E5FF, stop:1 #B388FF);
                color: white; border: none; border-radius: 14px;
                padding: 12px 28px; font-size: 14px; font-weight: 700;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #5CCFCA, stop:0.5 #4DECFF, stop:1 #C39BFF);
            }}
        """)
        gen_btn.clicked.connect(self._generate_custom)
        pl.addWidget(gen_btn)
        left.addWidget(preset_card)
        left.addStretch()
        body.addLayout(left, 1)

        # ── RIGHT: Story display
        story_card = GlassCard(self, radius=22)
        sl = QVBoxLayout(story_card)
        sl.setContentsMargins(24, 20, 24, 20)
        sl.setSpacing(10)

        story_top = QHBoxLayout()
        self._face = ARIAFaceWidget(size=80)
        self._face.set_expression("calm")
        self._story_title = QLabel("Your Story Will Appear Here")
        self._story_title.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {COLORS['text']};")
        story_top.addWidget(self._face)
        story_top.addSpacing(10)
        story_top.addWidget(self._story_title, 1)
        sl.addLayout(story_top)

        self._story_text = QTextEdit()
        self._story_text.setReadOnly(True)
        self._story_text.setPlaceholderText("Choose a situation to generate a personalized social story...")
        self._story_text.setStyleSheet(f"""
            QTextEdit {{
                background: rgba(255,255,255,0.95);
                border: 1px solid rgba(56,184,176,0.2);
                border-radius: 14px;
                padding: 18px;
                font-size: 16px;
                color: {COLORS['text']};
                line-height: 1.8;
            }}
        """)
        sl.addWidget(self._story_text, 1)

        # Read aloud button
        self._read_btn = QPushButton("🔊  Read Aloud")
        self._read_btn.setEnabled(False)
        self._read_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(56,184,176,0.15); color: {COLORS['teal_deep']};
                border: 1.5px solid {COLORS['teal']}; border-radius: 12px;
                padding: 10px 20px; font-size: 13px; font-weight: 700;
            }}
            QPushButton:hover {{ background: rgba(56,184,176,0.25); }}
            QPushButton:disabled {{ opacity: 0.5; }}
        """)
        self._read_btn.clicked.connect(self._read_aloud)
        sl.addWidget(self._read_btn, alignment=Qt.AlignLeft)
        body.addWidget(story_card, 2)
        main.addLayout(body, 1)

        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet(f"font-size: 12px; color: {COLORS['text_light']}; padding: 4px;")
        main.addWidget(self._status_lbl)

    def _section(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {COLORS['teal_deep']}; letter-spacing: 2px;")
        return lbl

    def _generate_custom(self):
        text = self._custom_input.text().strip()
        if not text:
            return
        self._generate(text)

    def _generate(self, situation):
        self._story_title.setText(f"📖 {situation}")
        self._story_text.setPlainText("✨ Generating your story...")
        self._face.set_expression("thinking")
        self._read_btn.setEnabled(False)
        self._status_lbl.setText("ARIA is writing a personalized story...")

        self._thread = QThread()
        self._worker = StoryWorker(situation, self._child_id)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.story_ready.connect(self._on_story)
        self._worker.error.connect(self._on_error)
        self._thread.start()

    def _on_story(self, story):
        self._story_text.setPlainText(story)
        self._face.set_expression("happy")
        self._read_btn.setEnabled(True)
        self._status_lbl.setText("✅ Story ready!")
        self._thread.quit()
        try:
            from core.child_context import get_context
            get_context().record_activity("story", "generated", award=1,
                                          reason="social story created")
        except Exception:
            pass

    def _on_error(self, msg):
        self._story_text.setPlainText(f"Couldn't generate story: {msg}\n\nMake sure you've added your Gemini API key in Settings.")
        self._face.set_expression("calm")
        self._status_lbl.setText("❌ Error — check API key in Settings")
        self._thread.quit()

    def _read_aloud(self):
        text = self._story_text.toPlainText()
        if text:
            try:
                from speech.tts_engine import speak
                speak(text, self._child_id, style="soft")
            except Exception:
                pass

    def resizeEvent(self, event):
        if hasattr(self, '_bg'):
            self._bg.resize(self.size())
        super().resizeEvent(event)
