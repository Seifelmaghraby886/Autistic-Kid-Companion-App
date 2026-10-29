"""
ARIA Talk Screen
Full AI conversation interface with animated face, STT, TTS, and emotion-aware responses.
"""

import asyncio
import threading
import math
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QFrame, QSizePolicy, QTextEdit
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, QObject
from PySide6.QtGui import QPainter, QColor, QLinearGradient, QFont, QPainterPath, QPen

from ui.components import GlassCard, ARIAFaceWidget, ParticleBackground, ToastNotification
from ui.styles import MAIN_STYLE, COLORS, get_emotion_color
import database.db_manager as db


# ══════════════════════════════════════════════════════════════
#  Chat Bubble
# ══════════════════════════════════════════════════════════════
class ChatBubble(QWidget):
    def __init__(self, text, sender="aria", emotion="calm", parent=None):
        super().__init__(parent)
        self._sender = sender
        self._color = QColor(get_emotion_color(emotion))
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)

        bubble = QFrame()
        bubble.setMaximumWidth(500)
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(14, 10, 14, 10)
        bubble_layout.setSpacing(4)

        msg = QLabel(text)
        msg.setWordWrap(True)
        msg.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        if sender == "aria":
            msg.setStyleSheet(f"font-size: 14px; color: {COLORS['text']}; line-height: 1.5;")
            bubble.setStyleSheet(f"""
                QFrame {{
                    background: rgba(255,255,255,0.92);
                    border: 1.5px solid rgba(56,184,176,0.3);
                    border-radius: 18px;
                    border-top-left-radius: 4px;
                }}
            """)
            time_lbl = QLabel(f"ARIA · {datetime.now().strftime('%H:%M')}")
            time_lbl.setStyleSheet(f"font-size: 10px; color: {COLORS['text_light']};")
            bubble_layout.addWidget(msg)
            bubble_layout.addWidget(time_lbl)
            layout.addWidget(bubble)
            layout.addStretch()
        else:
            msg.setStyleSheet("font-size: 14px; color: white;")
            bubble.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 {COLORS['teal']}, stop:1 {COLORS['teal_deep']});
                    border-radius: 18px;
                    border-top-right-radius: 4px;
                }}
            """)
            time_lbl = QLabel(datetime.now().strftime('%H:%M'))
            time_lbl.setStyleSheet("font-size: 10px; color: rgba(255,255,255,0.7);")
            bubble_layout.addWidget(msg)
            bubble_layout.addWidget(time_lbl, alignment=Qt.AlignRight)
            layout.addStretch()
            layout.addWidget(bubble)


# ══════════════════════════════════════════════════════════════
#  Typing Indicator
# ══════════════════════════════════════════════════════════════
class TypingIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(80, 40)
        self._t = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self._timer.start(60)

    def _update(self):
        self._t += 0.15
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(0, 0, 70, 36, 14, 14)
        painter.fillPath(path, QColor(255, 255, 255, 220))
        painter.setPen(QPen(QColor(56, 184, 176, 80), 1.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        for i in range(3):
            phase = self._t + i * 0.8
            y_offset = 4 * math.sin(phase)
            x = 15 + i * 20
            y = 18 + y_offset
            c = QColor(56, 184, 176, 200)
            painter.setBrush(c)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(x - 4), int(y - 4), 8, 8)


# ══════════════════════════════════════════════════════════════
#  AI Worker Thread
# ══════════════════════════════════════════════════════════════
class AIWorker(QObject):
    response_ready = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, message, child_id, emotion):
        super().__init__()
        self._message = message
        self._child_id = child_id
        self._emotion = emotion

    def run(self):
        try:
            # Get last 6 chat turns for context
            recent = db.get_chat_logs(self._child_id, 6)
            history = []
            for c in reversed(recent):  # oldest first
                if c.get("user_message"):
                    history.append({"role": "user", "content": c["user_message"]})
                if c.get("aria_reply"):
                    history.append({"role": "assistant", "content": c["aria_reply"]})
            from ai.gemini_client import get_aria_response
            result = get_aria_response(self._message, self._child_id, self._emotion,
                                       chat_history=history)
            self.response_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))


# ══════════════════════════════════════════════════════════════
#  TTS Worker
# ══════════════════════════════════════════════════════════════
class TTSWorker(QObject):
    finished = Signal()

    def __init__(self, text, child_id):
        super().__init__()
        self._text = text
        self._child_id = child_id

    def run(self):
        try:
            from speech.tts_engine import speak
            speak(self._text, self._child_id)
        except Exception:
            pass
        self.finished.emit()


# ══════════════════════════════════════════════════════════════
#  Talk Screen
# ══════════════════════════════════════════════════════════════
class TalkScreen(QWidget):
    go_back = Signal()
    comfort_mode_triggered = Signal()
    emotion_updated = Signal(str)

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._child_data = db.get_child(child_id) or {}
        self._current_emotion = "calm"
        self._is_listening = False
        self._ai_busy = False
        self._comfort_mode = False
        self._voice_mode = False
        self._voice_conversation_active = False
        self.setStyleSheet(MAIN_STYLE)
        self._build_ui()
        self._add_welcome_message()

    def _build_ui(self):
        from ui.animated_bg import MeshBackground

        # Background as separate underlay
        self._bg = MeshBackground(self, intensity=0.5)
        self._bg.lower()

        # Main horizontal layout
        main = QHBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # ── Left: ARIA face panel
        left = self._build_face_panel()
        main.addWidget(left)

        # ── Right: Chat
        right = self._build_chat_panel()
        main.addWidget(right, 1)

        # Make sure background is behind layout content
        self._bg.lower()

    def _build_face_panel(self):
        panel = GlassCard(self, dark=True, radius=0)
        panel.setFixedWidth(300)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 28, 24, 28)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignTop)

        # Back button
        back_btn = QPushButton("← Back")
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(56,184,176,0.15); color: {COLORS['teal_glow']};
                border: 1px solid rgba(56,184,176,0.4); border-radius: 10px;
                padding: 8px 16px; font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(56,184,176,0.3); }}
        """)
        back_btn.clicked.connect(self.go_back.emit)
        layout.addWidget(back_btn, alignment=Qt.AlignLeft)

        layout.addSpacing(16)

        # ARIA face
        self._face = ARIAFaceWidget(size=180)
        layout.addWidget(self._face, alignment=Qt.AlignHCenter)

        # ARIA name
        name_lbl = QLabel("ARIA")
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setStyleSheet(f"""
            font-size: 22px; font-weight: 900; color: {COLORS['teal']};
            letter-spacing: 6px;
        """)
        layout.addWidget(name_lbl)

        # State label
        self._state_lbl = QLabel("Ready to chat")
        self._state_lbl.setAlignment(Qt.AlignCenter)
        self._state_lbl.setStyleSheet("color: rgba(200,220,230,0.8); font-size: 12px;")
        layout.addWidget(self._state_lbl)

        layout.addSpacing(10)

        # Emotion badge
        self._emotion_badge = QLabel("● Calm")
        self._emotion_badge.setAlignment(Qt.AlignCenter)
        self._emotion_badge.setStyleSheet(f"""
            color: {COLORS['teal_glow']}; font-size: 13px;
            font-weight: 600; padding: 6px 14px;
            background: rgba(56,184,176,0.12);
            border: 1px solid rgba(56,184,176,0.3);
            border-radius: 20px;
        """)
        layout.addWidget(self._emotion_badge, alignment=Qt.AlignHCenter)

        layout.addSpacing(16)

        # Controls
        # Voice conversation mode toggle (BIG, prominent)
        self._voice_mode_btn = QPushButton("🎤  Start Voice Chat")
        self._voice_mode_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #00BFA8, stop:0.5 #00E5FF, stop:1 #B388FF);
                color: white;
                border: none;
                border-radius: 16px; padding: 14px 22px;
                font-size: 14px; font-weight: 800;
                text-align: center;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #5CE5DC, stop:0.5 #4DECFF, stop:1 #C39BFF);
            }}
        """)
        self._voice_mode_btn.clicked.connect(self._toggle_voice_mode)
        layout.addWidget(self._voice_mode_btn)

        # Hold-to-speak (single message mode)
        self._mic_btn = QPushButton("🎙️  Hold to Speak Once")
        self._mic_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(56,184,176,0.18);
                color: {COLORS['teal_glow']};
                border: 1.5px solid {COLORS['teal']};
                border-radius: 14px; padding: 10px 16px;
                font-size: 12px; font-weight: 600;
                text-align: center;
            }}
            QPushButton:hover {{ background: rgba(56,184,176,0.30); }}
        """)
        self._mic_btn.pressed.connect(self._start_listening)
        self._mic_btn.released.connect(self._stop_listening)
        layout.addWidget(self._mic_btn)

        # Listening indicator
        self._listen_lbl = QLabel("")
        self._listen_lbl.setAlignment(Qt.AlignCenter)
        self._listen_lbl.setStyleSheet(f"color: {COLORS['teal_glow']}; font-size: 12px;")
        layout.addWidget(self._listen_lbl)

        # Volume meter
        from PySide6.QtWidgets import QProgressBar
        self._volume_meter = QProgressBar()
        self._volume_meter.setRange(0, 100)
        self._volume_meter.setValue(0)
        self._volume_meter.setTextVisible(False)
        self._volume_meter.setFixedHeight(8)
        self._volume_meter.setVisible(False)
        self._volume_meter.setStyleSheet(f"""
            QProgressBar {{
                background: rgba(255,255,255,0.10);
                border-radius: 4px; border: none;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #00BFA8, stop:0.5 #00E5FF, stop:1 #B388FF);
                border-radius: 4px;
            }}
        """)
        layout.addWidget(self._volume_meter)

        layout.addStretch()

        # Comfort mode button
        comfort_btn = QPushButton("🌿  Calm Zone")
        comfort_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(107,159,212,0.15);
                color: #90C0E8; border: 1px solid rgba(107,159,212,0.3);
                border-radius: 12px; padding: 10px 18px;
                font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(107,159,212,0.28); }}
        """)
        comfort_btn.clicked.connect(self.comfort_mode_triggered.emit)
        layout.addWidget(comfort_btn)

        return panel

    def _build_chat_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(12)

        # Title
        title_row = QHBoxLayout()
        title = QLabel("Conversation")
        title.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {COLORS['text']};")
        child_name = self._child_data.get("name", "")
        if child_name:
            title.setText(f"Talking with ARIA · {child_name}")
        title_row.addWidget(title)
        title_row.addStretch()

        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {COLORS['text_light']};
                border: 1px solid rgba(56,184,176,0.2); border-radius: 8px;
                padding: 6px 14px; font-size: 12px;
            }}
            QPushButton:hover {{ border-color: {COLORS['teal']}; color: {COLORS['teal']}; }}
        """)
        clear_btn.clicked.connect(self._clear_chat)
        title_row.addWidget(clear_btn)
        layout.addLayout(title_row)

        # Chat area
        chat_card = GlassCard(panel, radius=20)
        chat_layout = QVBoxLayout(chat_card)
        chat_layout.setContentsMargins(8, 8, 8, 8)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._chat_container = QWidget()
        self._chat_container.setStyleSheet("background: transparent;")
        self._chat_inner = QVBoxLayout(self._chat_container)
        self._chat_inner.setContentsMargins(8, 8, 8, 8)
        self._chat_inner.setSpacing(6)
        self._chat_inner.addStretch()

        self._scroll.setWidget(self._chat_container)
        chat_layout.addWidget(self._scroll)

        # Typing indicator
        self._typing = TypingIndicator(panel)
        self._typing.setVisible(False)
        chat_layout.addWidget(self._typing)

        layout.addWidget(chat_card, 1)

        # Input area
        input_card = GlassCard(panel, radius=18)
        input_layout = QHBoxLayout(input_card)
        input_layout.setContentsMargins(14, 10, 14, 10)
        input_layout.setSpacing(10)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Type a message... or hold the microphone button")
        self._input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent; border: none;
                font-size: 14px; color: {COLORS['text']};
                padding: 8px 0;
            }}
        """)
        self._input.returnPressed.connect(self._send_text)

        send_btn = QPushButton("Send →")
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {COLORS['teal']}, stop:1 {COLORS['teal_deep']});
                color: white; border: none; border-radius: 12px;
                padding: 10px 22px; font-size: 13px; font-weight: 700;
            }}
            QPushButton:hover {{ background: {COLORS['teal_glow']}; }}
        """)
        send_btn.clicked.connect(self._send_text)

        input_layout.addWidget(self._input, 1)
        input_layout.addWidget(send_btn)
        layout.addWidget(input_card)

        # Offline note
        self._offline_lbl = QLabel("")
        self._offline_lbl.setStyleSheet(f"font-size: 11px; color: {COLORS['warning']}; padding: 4px 8px;")
        layout.addWidget(self._offline_lbl)

        return panel

    def _add_welcome_message(self):
        name = self._child_data.get("name", "friend")
        lang = self._child_data.get("language", "en")
        greetings = {
            "en": f"Hi {name}! I'm ARIA. I'm really happy to see you today! 😊 What would you like to talk about?",
            "ar": f"أهلاً {name}! أنا أريا. سعيدة جداً بلقاءك النهاردة! 😊 عايز تتكلم في إيه؟",
            "de": f"Hallo {name}! Ich bin ARIA. Ich freue mich sehr, dich heute zu sehen! 😊 Worüber möchtest du reden?",
        }
        msg = greetings.get(lang, greetings["en"])
        self._add_bubble(msg, sender="aria", emotion="happy")
        self._face.set_expression("happy")

    def _add_bubble(self, text, sender="aria", emotion="calm"):
        bubble = ChatBubble(text, sender, emotion, self._chat_container)
        # Insert before the stretch
        count = self._chat_inner.count()
        self._chat_inner.insertWidget(count - 1, bubble)
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        )

    def _send_text(self):
        text = self._input.text().strip()
        if not text or self._ai_busy:
            return
        self._input.clear()
        self._add_bubble(text, sender="user")
        self._request_ai(text)

    def _request_ai(self, text):
        if self._ai_busy:
            return
        self._ai_busy = True
        try:
            self._typing.setVisible(True)
        except Exception:
            pass
        self._state_lbl.setText("Thinking...")
        self._face.set_expression("thinking")
        self._scroll_to_bottom()

        # Log user message
        try:
            db.log_chat(self._child_id, text, "", "neutral", "none", False)
        except Exception:
            pass

        try:
            self._ai_thread = QThread()
            self._ai_worker = AIWorker(text, self._child_id, self._current_emotion)
            self._ai_worker.moveToThread(self._ai_thread)
            self._ai_thread.started.connect(self._ai_worker.run)
            self._ai_worker.response_ready.connect(self._on_ai_response)
            self._ai_worker.error_occurred.connect(self._on_ai_error)
            self._ai_thread.start()
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._on_ai_error(str(e))

    def _on_ai_response(self, data: dict):
        try:
            self._ai_busy = False
            self._typing.setVisible(False)
            try:
                self._ai_thread.quit()
            except Exception:
                pass

            reply = data.get("reply", "I'm here with you.")
            face_expr = data.get("face_expression", "calm")
            comfort = data.get("comfort_mode", False)
            activity = data.get("suggested_activity", "none")
            parent_alert = data.get("parent_alert", False)
            memory = data.get("memory_update", "")

            self._add_bubble(reply, sender="aria", emotion=face_expr)
            self._face.set_expression(face_expr)
            self._state_lbl.setText("Ready to chat")

            color = get_emotion_color(face_expr)
            self._emotion_badge.setText(f"● {face_expr.title()}")
            self._emotion_badge.setStyleSheet(f"""
                color: {color}; font-size: 13px; font-weight: 600;
                padding: 6px 14px; background: {color}22;
                border: 1px solid {color}44; border-radius: 20px;
            """)
            self.emotion_updated.emit(face_expr)

            if comfort:
                self.comfort_mode_triggered.emit()

            try:
                if parent_alert:
                    db.log_emotion(self._child_id, "distress", 0.9,
                                   source="chat", action="parent_alert")
                if memory:
                    db.update_ai_memory(self._child_id, memory_summary=memory)
                db.log_chat(self._child_id, "", reply,
                            detected_emotion=face_expr,
                            suggested_activity=activity,
                            comfort_mode=bool(comfort))
            except Exception as e:
                print(f"[DB log error] {e}")

            # TTS in plain thread (avoid QThread cleanup issues)
            try:
                from speech.tts_engine import speak
                speak(reply, self._child_id)
            except Exception as e:
                print(f"[TTS error] {e}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._state_lbl.setText("Error — see console")

    def _on_ai_error(self, error: str):
        self._ai_busy = False
        self._typing.setVisible(False)
        lang = self._child_data.get("language", "en")
        offline_msgs = {
            "en": "I'm here with you. We can do a calm activity.",
            "ar": "أنا موجودة معاك. نقدر نعمل نشاط هادي.",
            "de": "Ich bin bei dir. Wir können eine ruhige Aktivität machen.",
        }
        self._add_bubble(offline_msgs.get(lang, offline_msgs["en"]), sender="aria")
        self._face.set_expression("calm")
        self._offline_lbl.setText("⚠️ Offline mode — using basic responses")
        self._state_lbl.setText("Offline mode")

    def _start_listening(self):
        if self._is_listening:
            return
        self._is_listening = True
        # Show "preparing" until listening_started fires
        self._mic_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,180,60,0.30);
                color: #C08020; border: 2px solid #FFB73D;
                border-radius: 14px; padding: 10px 16px;
                font-size: 12px; font-weight: 700;
            }}
        """)
        self._state_lbl.setText("🎙 Get ready...")
        self._face.set_expression("listening")
        self._listen_lbl.setText("⏳ Mic warming up...")
        if hasattr(self, '_volume_meter'):
            self._volume_meter.setValue(0)
            self._volume_meter.setVisible(True)

        try:
            from speech.stt_engine import STTWorker
            # Hold-to-speak mode: NO auto-stop. Voice mode: auto-stop with longer pause-tolerance.
            auto_stop = self._voice_mode  # Only auto-stop when in voice mode
            self._stt_worker = STTWorker(
                self._child_id,
                auto_stop_on_silence=auto_stop,
                silence_seconds=2.8,  # Longer pause-tolerance
                min_speech_seconds=1.5,
                max_record_seconds=30,
            )
            self._stt_worker.transcription_ready.connect(self._on_transcription)
            self._stt_worker.error_occurred.connect(self._on_stt_error)
            self._stt_worker.volume_level.connect(self._on_volume)
            self._stt_worker.listening_started.connect(self._on_listening_started)
            self._stt_worker.auto_stopped.connect(self._on_auto_stopped)
            self._stt_worker.start_recording()
        except Exception as e:
            self._on_stt_error(str(e))

    def _on_auto_stopped(self):
        """STT detected silence and stopped automatically."""
        self._is_listening = False
        self._listen_lbl.setText("⏳ Got it — transcribing...")
        if hasattr(self, '_volume_meter'):
            self._volume_meter.setVisible(False)
        # Reset mic button
        self._mic_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(56,184,176,0.18);
                color: {COLORS['teal_glow']};
                border: 1.5px solid {COLORS['teal']};
                border-radius: 14px; padding: 10px 16px;
                font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(56,184,176,0.30); }}
        """)

    def _on_volume(self, level: float):
        if hasattr(self, '_volume_meter'):
            self._volume_meter.setValue(int(level * 100))
        # Update input field with live waveform indication
        if level > 0.05:
            self._listen_lbl.setText(f"● Hearing you... 🔊")
        else:
            self._listen_lbl.setText("● Recording (silence)")

    def _on_listening_started(self):
        self._listen_lbl.setText("🎤 LISTENING — speak now!")
        # Highlight the mic button to show it's ready
        self._mic_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #00D9A0, stop:1 #00E5FF);
                color: white; border: 2px solid #00E5FF;
                border-radius: 14px; padding: 10px 16px;
                font-size: 12px; font-weight: 800;
            }}
        """)

    def _toggle_voice_mode(self):
        if self._voice_mode:
            # Stop voice conversation
            self._voice_mode = False
            self._voice_conversation_active = False
            self._voice_mode_btn.setText("🎤  Start Voice Chat")
            self._voice_mode_btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 #00BFA8, stop:0.5 #00E5FF, stop:1 #B388FF);
                    color: white; border: none;
                    border-radius: 16px; padding: 14px 22px;
                    font-size: 14px; font-weight: 800;
                }}
            """)
            try:
                if hasattr(self, '_stt_worker') and self._stt_worker:
                    self._stt_worker.stop_recording()
            except Exception:
                pass
            self._state_lbl.setText("Voice chat ended. Tap to restart.")
            try:
                from speech.tts_engine import clear_finished_callbacks
                clear_finished_callbacks()
            except Exception:
                pass
        else:
            # Start voice conversation
            self._voice_mode = True
            self._voice_conversation_active = True
            self._voice_mode_btn.setText("⏹  Stop Voice Chat")
            self._voice_mode_btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 #FF6B7E, stop:1 #C04055);
                    color: white; border: none;
                    border-radius: 16px; padding: 14px 22px;
                    font-size: 14px; font-weight: 800;
                }}
            """)
            self._state_lbl.setText("🎤 Voice mode ON — listening...")

            # Register TTS-finished hook → auto-listen again
            try:
                from speech.tts_engine import on_speech_finished, clear_finished_callbacks
                clear_finished_callbacks()
                on_speech_finished(self._on_tts_finished_voice_mode)
            except Exception:
                pass

            # Start listening immediately
            QTimer.singleShot(300, self._start_listening)

    def _on_tts_finished_voice_mode(self):
        """Called when ARIA finishes speaking — auto-listen if in voice mode."""
        if self._voice_mode and self._voice_conversation_active:
            # Schedule on Qt main thread via signal
            QTimer.singleShot(800, self._auto_listen)

    def _auto_listen(self):
        if self._voice_mode and not self._is_listening and not self._ai_busy:
            self._start_listening()
            # Auto-stop after 8 seconds if no input
            QTimer.singleShot(8000, self._auto_stop_if_silent)

    def _auto_stop_if_silent(self):
        if self._voice_mode and self._is_listening:
            self._stop_listening()

    def _stop_listening(self):
        if not self._is_listening:
            return
        self._is_listening = False
        self._mic_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(56,184,176,0.18);
                color: {COLORS['teal_glow']};
                border: 1.5px solid {COLORS['teal']};
                border-radius: 14px; padding: 12px 20px;
                font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(56,184,176,0.30); }}
        """)
        self._state_lbl.setText("Processing...")
        self._listen_lbl.setText("⏳ Transcribing...")
        if hasattr(self, '_volume_meter'):
            self._volume_meter.setVisible(False)

        try:
            if hasattr(self, '_stt_worker') and self._stt_worker:
                self._stt_worker.stop_recording()
        except Exception as e:
            print(f"[Stop STT error] {e}")
            self._on_stt_error(str(e))

    def _on_stt_error(self, msg: str):
        self._is_listening = False
        self._listen_lbl.setText("")
        self._state_lbl.setText("Voice input not available — please type")
        self._face.set_expression("calm")
        # Reset mic button style
        self._mic_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(56,184,176,0.18);
                color: {COLORS['teal_glow']};
                border: 1.5px solid {COLORS['teal']};
                border-radius: 14px; padding: 12px 20px;
                font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(56,184,176,0.30); }}
        """)
        QTimer.singleShot(3000, lambda: self._state_lbl.setText("Ready to chat"))

    def _on_transcription(self, text: str):
        self._listen_lbl.setText("")
        if hasattr(self, '_volume_meter'):
            self._volume_meter.setVisible(False)
        if text and text.strip():
            self._input.setText(text)
            self._send_text()
        else:
            self._state_lbl.setText("Didn't catch that. Try again or type.")
            QTimer.singleShot(2500, lambda: self._state_lbl.setText("Ready to chat"))

    def _clear_chat(self):
        while self._chat_inner.count() > 1:
            item = self._chat_inner.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._add_welcome_message()

    def resizeEvent(self, event):
        if hasattr(self, '_bg'):
            self._bg.resize(self.size())
        super().resizeEvent(event)
