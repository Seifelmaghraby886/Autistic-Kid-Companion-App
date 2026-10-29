"""ShellWindow — child-facing auto-listening interface. NO talk button.

This is the default screen ARIA OS launches into. Voice-first.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QLineEdit, QFrame, QMainWindow
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont

from ui.components import ARIAFace, WaveformBar, GlassCard, MAIN_STYLE, C


class ShellWindow(QMainWindow):
    """Top-level window. Owns the AppController and routes between modules."""

    request_parent_pin = Signal()

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("ARIA OS — AI Companion")
        self.setMinimumSize(1280, 800)
        self.setStyleSheet(MAIN_STYLE)

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        # Build the talk shell
        self.shell = self._build_shell()
        self._stack.addWidget(self.shell)

        # Wire controller → UI signals
        self.controller.aria_replied.connect(self._on_aria_reply)
        self.controller.state_changed.connect(self._on_state)
        self.controller.transcript.connect(self._on_transcript)
        self.controller.listening_started.connect(self._on_listening_started)
        self.controller.error.connect(self._on_error)

        # Wire ToolLauncher → screens
        self.controller.tools.open_calm_zone.connect(self._open_calm_zone)
        self.controller.tools.open_aac.connect(self._open_aac)
        self.controller.tools.open_schedule.connect(self._open_schedule)
        self.controller.tools.open_tutorial.connect(self._open_tutorial)
        self.controller.tools.open_story.connect(self._open_story)
        self.controller.tools.open_game.connect(self._open_game)
        self.controller.tools.open_parent_pin.connect(self._open_parent_pin)
        self.controller.tools.open_safety.connect(self._open_safety)
        self.controller.tools.close_all_tools.connect(self._return_to_shell)

        # Start the auto flow
        QTimer.singleShot(300, self.controller.start)

    # ── Shell layout ─────────────────────────────────────────
    def _build_shell(self):
        w = QWidget()
        root = QVBoxLayout(w)
        root.setContentsMargins(40, 24, 40, 24)
        root.setSpacing(16)

        # Top strip
        top = QHBoxLayout()
        title = QLabel("ARIA OS")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; "
                           f"color: {C['cyan']}; letter-spacing: 4px;")
        self._mode_lbl = QLabel("• Companion Mode")
        self._mode_lbl.setStyleSheet(f"font-size: 12px; color: {C['text_dim']};")
        top.addWidget(title)
        top.addSpacing(16)
        top.addWidget(self._mode_lbl)
        top.addStretch()
        parent_btn = QPushButton("👤  Parent")
        parent_btn.setMaximumWidth(140)
        parent_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0,229,255,0.12); color: {C['cyan']};
                border: 1.5px solid rgba(0,229,255,0.4); border-radius: 12px;
                padding: 8px 16px; font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(0,229,255,0.25); }}
        """)
        parent_btn.clicked.connect(self._open_parent_pin)
        top.addWidget(parent_btn)
        root.addLayout(top)

        # Center — face + status
        face_row = QHBoxLayout()
        face_row.addStretch()
        face_col = QVBoxLayout()
        face_col.setAlignment(Qt.AlignCenter)
        self._face = ARIAFace(size=260)
        face_col.addWidget(self._face, alignment=Qt.AlignCenter)
        self._state_lbl = QLabel("ARIA is waking up…")
        self._state_lbl.setAlignment(Qt.AlignCenter)
        self._state_lbl.setStyleSheet(
            f"font-size: 16px; font-weight: 600; color: {C['soft']}; padding-top: 10px;"
        )
        face_col.addWidget(self._state_lbl)
        face_row.addLayout(face_col)
        face_row.addStretch()
        root.addLayout(face_row)

        # Waveform
        self._wave = WaveformBar()
        root.addWidget(self._wave)

        # Conversation card
        bubble_card = GlassCard(self, radius=20, dark=True)
        bcl = QVBoxLayout(bubble_card)
        bcl.setContentsMargins(24, 18, 24, 18)
        self._aria_bubble = QLabel("…")
        self._aria_bubble.setWordWrap(True)
        self._aria_bubble.setStyleSheet(
            f"font-size: 18px; color: {C['text']}; line-height: 1.6;"
        )
        self._aria_bubble.setAlignment(Qt.AlignCenter)
        self._aria_bubble.setMinimumHeight(80)
        bcl.addWidget(self._aria_bubble)
        self._heard_lbl = QLabel("")
        self._heard_lbl.setAlignment(Qt.AlignCenter)
        self._heard_lbl.setStyleSheet(
            f"font-size: 12px; color: {C['text_dim']}; font-style: italic;"
        )
        bcl.addWidget(self._heard_lbl)
        root.addWidget(bubble_card)

        # Tiny developer text input (collapsed look — for testing only)
        dev_row = QHBoxLayout()
        self._dev_input = QLineEdit()
        self._dev_input.setPlaceholderText("dev test input (press Enter)  …")
        self._dev_input.setMaximumHeight(36)
        self._dev_input.setStyleSheet(
            f"background: rgba(255,255,255,0.05); border: 1px solid rgba(0,191,168,0.25);"
            f"border-radius: 10px; padding: 6px 12px; color: {C['text_dim']}; font-size: 12px;"
        )
        self._dev_input.returnPressed.connect(self._send_dev_input)
        dev_row.addWidget(self._dev_input)
        root.addLayout(dev_row)

        return w

    # ── Controller event handlers ───────────────────────────
    def _on_aria_reply(self, response):
        reply = response.get("reply", "")
        emotion = response.get("emotion", "calm")
        self._aria_bubble.setText(reply)
        self._face.set_emotion(emotion)
        self._face.set_speaking(True)
        # Drop speaking flag after a moment
        QTimer.singleShot(max(1200, min(6000, len(reply) * 60)),
                          lambda: self._face.set_speaking(False))

    def _on_state(self, state_name):
        labels = {
            "IDLE_STARTUP":       "Starting…",
            "GREETING":           "Saying hi…",
            "LISTENING":          "ARIA is listening… 🎙",
            "SPEECH_DETECTED":    "I hear you…",
            "TRANSCRIBING":       "Understanding…",
            "THINKING":           "Thinking…",
            "SPEAKING":           "ARIA is talking…",
            "OPENING_TOOL":       "Opening…",
            "TOOL_ACTIVE":        "Open",
            "RETURNING_TO_LISTEN":"Coming back…",
            "PARENT_MODE":        "Parent mode",
            "SAFETY_MODE":        "Calm & safe space",
            "ERROR_RECOVERY":     "One moment…",
        }
        self._state_lbl.setText(labels.get(state_name, state_name))
        if state_name == "LISTENING":
            self._wave.set_active(True)
            self._face.set_listening(True)
        elif state_name in ("SPEAKING", "THINKING"):
            self._wave.set_active(False)
            self._face.set_listening(False)
        else:
            self._wave.set_active(False)

    def _on_transcript(self, text):
        if text:
            self._heard_lbl.setText(f"you said: {text}")

    def _on_listening_started(self):
        self._wave.set_active(True)
        self._face.set_listening(True)

    def _on_error(self, msg):
        # Soft error — don't show to child; log to dev
        print(f"[ShellWindow error] {msg}")

    def _send_dev_input(self):
        text = self._dev_input.text().strip()
        if not text:
            return
        self._dev_input.clear()
        self.controller.process_input(text)

    # ── Tool routing ─────────────────────────────────────────
    def _open_tool(self, factory_fn):
        """Push a tool screen onto stack. Returns to shell when closed."""
        try:
            screen = factory_fn()
            screen.close_requested.connect(self._return_to_shell)
            self._stack.addWidget(screen)
            self._stack.setCurrentWidget(screen)
        except Exception as e:
            print(f"[Open tool error: {e}]")

    def _return_to_shell(self):
        if self._stack.currentWidget() is not self.shell:
            old = self._stack.currentWidget()
            self._stack.setCurrentWidget(self.shell)
            QTimer.singleShot(300, lambda: self._stack.removeWidget(old) if old else None)

    def _open_calm_zone(self):
        from ui.calm_zone import CalmZone
        self._open_tool(lambda: CalmZone(self.controller))

    def _open_aac(self, category):
        from ui.aac_board import AACBoard
        self._open_tool(lambda: AACBoard(self.controller, category))

    def _open_schedule(self):
        from ui.visual_schedule import VisualSchedule
        self._open_tool(lambda: VisualSchedule(self.controller))

    def _open_tutorial(self, key):
        from ui.task_tutorials import TaskTutorial
        self._open_tool(lambda: TaskTutorial(self.controller, key))

    def _open_story(self, theme):
        from ui.story_mode import StoryMode
        self._open_tool(lambda: StoryMode(self.controller, theme))

    def _open_game(self):
        from ui.games import GamesScreen
        self._open_tool(lambda: GamesScreen(self.controller))

    def _open_parent_pin(self):
        from ui.parent_pin import ParentPIN
        self._open_tool(lambda: ParentPIN(self.controller))

    def _open_safety(self, payload):
        from ui.calm_zone import CalmZone
        # Safety opens calm zone with parent alert visible
        self._open_tool(lambda: CalmZone(self.controller, safety_payload=payload))

    def closeEvent(self, event):
        try:
            self.controller.shutdown()
        except Exception:
            pass
        super().closeEvent(event)
