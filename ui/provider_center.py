"""
ARIA OS — Provider Control Center
=================================
One screen, one switch per service. A parent or developer flips any AI brain,
voice (TTS) or listening (STT) provider on or off; ARIA picks the change up on
the very next request. Built for kiosk mode — big touch toggles, no typing.
"""

import json
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QFrame, QLineEdit
)
from PySide6.QtCore import Qt, Signal

from ui.components import GlassCard, ParticleBackground, ToggleSwitch
from ui.styles import MAIN_STYLE, COLORS
from core.provider_control import all_states, set_enabled, set_api_key


# (provider key, display name, config key holding its API key — or None if keyless)
_AI = [
    ("ai_groq",        "Groq · Llama 3.3 70B",  "groq_api_key"),
    ("ai_cerebras",    "Cerebras · Llama 3.3",  "cerebras_api_key"),
    ("ai_gemini",      "Google Gemini",         "gemini_api_key"),
    ("ai_openrouter",  "OpenRouter",            "openrouter_api_key"),
    ("ai_anthropic",   "Anthropic · Claude",    "anthropic_api_key"),
    ("ai_openai",      "OpenAI · GPT",          "openai_api_key"),
    ("ai_ollama",      "Ollama · local model",  None),
]
_TTS = [
    ("tts_elevenlabs", "ElevenLabs · premium voice", "elevenlabs_api_key"),
    ("tts_edge",       "Edge-TTS · free neural",     None),
    ("tts_pyttsx3",    "Windows SAPI · offline",     None),
]
_STT = [
    ("stt_elevenlabs", "ElevenLabs Scribe · best Arabic", "elevenlabs_api_key"),
    ("stt_whisper",    "Whisper · offline fallback",      None),
    ("stt_google",     "Google Speech · online",          None),
]


class ProviderCenterScreen(QWidget):
    """Live on/off control for every AI / TTS / STT provider."""

    go_back = Signal()

    def __init__(self, child_id=None, parent=None):
        super().__init__(parent)
        self.child_id = child_id
        self.setStyleSheet(MAIN_STYLE)
        self._states = all_states()
        self._cfg = self._load_cfg()
        self._build_ui()

    # ── helpers ──────────────────────────────────────────────────────
    @staticmethod
    def _load_cfg():
        try:
            path = Path(__file__).parent.parent / "config" / "app_config.json"
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    # ── construction ─────────────────────────────────────────────────
    def _build_ui(self):
        self._bg = ParticleBackground(self)
        self._bg.lower()

        root = QVBoxLayout(self)
        root.setContentsMargins(44, 24, 44, 28)
        root.setSpacing(14)

        # header: back button + title
        header = QHBoxLayout()
        back = QPushButton("←  Back")
        back.setCursor(Qt.PointingHandCursor)
        back.setFixedHeight(46)
        back.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0,191,168,0.12); color: {COLORS['teal_deep']};
                border: 1.5px solid {COLORS['teal']}; border-radius: 15px;
                padding: 8px 22px; font-size: 13px; font-weight: 700;
            }}
            QPushButton:hover {{ background: rgba(0,191,168,0.24); }}
        """)
        back.clicked.connect(self.go_back.emit)
        header.addWidget(back)
        header.addStretch()
        title = QLabel("⚙   Provider Control Center")
        title.setStyleSheet(
            f"font-size: 23px; font-weight: 900; color: {COLORS['teal_deep']};"
        )
        header.addWidget(title)
        header.addStretch()
        exit_btn = QPushButton("✕  Exit")
        exit_btn.setCursor(Qt.PointingHandCursor)
        exit_btn.setFixedHeight(46)
        exit_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,107,126,0.14); color: #C0504F;
                border: 1.5px solid rgba(255,107,126,0.5); border-radius: 15px;
                padding: 8px 22px; font-size: 13px; font-weight: 700;
            }
            QPushButton:hover { background: rgba(255,107,126,0.26); }
        """)
        exit_btn.clicked.connect(self._exit_app)
        header.addWidget(exit_btn)
        root.addLayout(header)

        sub = QLabel("Turn any service on or off — ARIA uses it on the next "
                     "request, no restart needed.")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(f"font-size: 12px; color: {COLORS['text_light']};")
        root.addWidget(sub)

        # scrollable list of sections
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(2, 4, 2, 4)
        cl.setSpacing(16)
        cl.addWidget(self._section(
            "🧠   AI Brain",
            "Tried top-to-bottom — ARIA uses the first one that is ON and reachable.",
            _AI))
        cl.addWidget(self._section(
            "🔊   ARIA's Voice (TTS)",
            "ElevenLabs first (if ON), then Edge-TTS, then the offline Windows voice.",
            _TTS))
        cl.addWidget(self._section(
            "🎙   Listening (STT)",
            "Whisper is best for Egyptian Arabic; Google is faster for English.",
            _STT))
        cl.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

    def _section(self, title, hint, providers):
        card = GlassCard(self, radius=20)
        v = QVBoxLayout(card)
        v.setContentsMargins(24, 18, 24, 20)
        v.setSpacing(6)

        t = QLabel(title)
        t.setStyleSheet(f"font-size: 16px; font-weight: 800; "
                        f"color: {COLORS['text']}; background: transparent;")
        v.addWidget(t)
        h = QLabel(hint)
        h.setWordWrap(True)
        h.setStyleSheet(f"font-size: 11px; color: {COLORS['text_light']}; "
                        f"background: transparent;")
        v.addWidget(h)
        v.addSpacing(8)
        for key, name, cfg_key in providers:
            v.addWidget(self._row(key, name, cfg_key))
        return card

    @staticmethod
    def _chip_style(ok):
        col = COLORS["success"] if ok else COLORS["warning"]
        return (f"font-size: 10px; font-weight: 700; color: white; "
                f"background: {col}; border-radius: 9px; padding: 3px 11px;")

    @staticmethod
    def _mini_btn_style(primary=False):
        if primary:
            return ("QPushButton { background: #00BFA8; color: white; border: none;"
                    " border-radius: 10px; font-size: 12px; font-weight: 700; }"
                    "QPushButton:hover { background: #00D9A0; }")
        return ("QPushButton { background: rgba(122,140,170,0.16); color: #5A6F8A;"
                " border: 1px solid rgba(122,140,170,0.40); border-radius: 10px;"
                " font-size: 11px; font-weight: 700; }"
                "QPushButton:checked { background: rgba(0,191,168,0.22); color: #1A7FA8; }"
                "QPushButton:hover { background: rgba(122,140,170,0.30); }")

    def _row(self, key, name, cfg_key):
        card = QFrame()
        card.setStyleSheet("background: rgba(255,255,255,0.58); border-radius: 14px;")
        v = QVBoxLayout(card)
        v.setContentsMargins(16, 11, 16, 13)
        v.setSpacing(9)

        # ── top line: name · status chip · on/off toggle
        top = QHBoxLayout()
        top.setSpacing(10)
        nm = QLabel(name)
        nm.setStyleSheet(f"font-size: 14px; font-weight: 600; "
                         f"color: {COLORS['text']}; background: transparent;")
        top.addWidget(nm)
        top.addStretch()

        has_key = bool((self._cfg.get(cfg_key) or "").strip()) if cfg_key else True
        chip = QLabel("key set" if (cfg_key and has_key)
                      else ("needs key" if cfg_key else "ready"))
        chip.setStyleSheet(self._chip_style(has_key))
        top.addWidget(chip)

        toggle = ToggleSwitch(self._states.get(key, True))
        toggle.toggled.connect(lambda val, k=key: self._on_toggle(k, val))
        top.addWidget(toggle)
        v.addLayout(top)

        # ── second line: editable API key (only providers that need one)
        if cfg_key:
            kr = QHBoxLayout()
            kr.setSpacing(8)
            field = QLineEdit(self._cfg.get(cfg_key) or "")
            field.setEchoMode(QLineEdit.EchoMode.Password)
            field.setPlaceholderText(f"paste your {cfg_key} here…")

            eye = QPushButton("show")
            eye.setCheckable(True)
            eye.setFixedSize(60, 40)
            eye.setCursor(Qt.PointingHandCursor)
            eye.setStyleSheet(self._mini_btn_style())
            eye.toggled.connect(
                lambda shown, f=field, b=eye: self._toggle_echo(shown, f, b))

            save = QPushButton("Save")
            save.setFixedSize(76, 40)
            save.setCursor(Qt.PointingHandCursor)
            save.setStyleSheet(self._mini_btn_style(primary=True))
            save.clicked.connect(
                lambda _, ck=cfg_key, f=field, c=chip: self._save_key(ck, f, c))
            field.returnPressed.connect(
                lambda ck=cfg_key, f=field, c=chip: self._save_key(ck, f, c))

            kr.addWidget(field, 1)
            kr.addWidget(eye)
            kr.addWidget(save)
            v.addLayout(kr)

        return card

    def _toggle_echo(self, shown, field, button):
        field.setEchoMode(QLineEdit.EchoMode.Normal if shown
                          else QLineEdit.EchoMode.Password)
        button.setText("hide" if shown else "show")

    def _save_key(self, cfg_key, field, chip):
        value = field.text().strip()
        set_api_key(cfg_key, value)
        self._cfg[cfg_key] = value
        chip.setText("key set" if value else "needs key")
        chip.setStyleSheet(self._chip_style(bool(value)))
        print(f"[ARIA-OS] saved {cfg_key} ({len(value)} chars)", flush=True)

    def _on_toggle(self, key, value):
        set_enabled(key, value)
        self._states[key] = value
        print(f"[ARIA-OS] provider '{key}' -> {'ON' if value else 'OFF'}", flush=True)

    def _exit_app(self):
        """Touch-friendly way to quit ARIA OS from kiosk mode (with confirm)."""
        from PySide6.QtWidgets import QMessageBox
        win = self.window()
        answer = QMessageBox.question(
            self, "Exit ARIA OS", "Close ARIA OS now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes and win is not None:
            win.close()

    def resizeEvent(self, event):
        if hasattr(self, "_bg"):
            self._bg.resize(self.size())
        super().resizeEvent(event)
