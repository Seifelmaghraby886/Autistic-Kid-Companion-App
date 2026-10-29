"""
ARIA Live Camera Screen
Real-time face detection, emotion classification, and ARIA response.
"""

import cv2
import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, QObject
from PySide6.QtGui import QImage, QPixmap, QPainter, QColor, QFont, QPen, QPainterPath

from ui.components import GlassCard, ARIAFaceWidget, EmotionBar, ParticleBackground
from ui.styles import MAIN_STYLE, COLORS, get_emotion_color
import database.db_manager as db


# ══════════════════════════════════════════════════════════════
#  Camera Worker
# ══════════════════════════════════════════════════════════════
class CameraWorker(QObject):
    frame_ready = Signal(np.ndarray)
    emotion_detected = Signal(str, float, dict)
    error = Signal(str)

    def __init__(self, camera_id=0):
        super().__init__()
        self._camera_id = camera_id
        self._running = False
        self._cap = None
        self._predictor = None

    def start(self):
        self._running = True
        try:
            from vision.emotion_predictor import EmotionPredictor
            self._predictor = EmotionPredictor()
        except Exception as e:
            self.error.emit(f"Model error: {e}")

        self._cap = cv2.VideoCapture(self._camera_id)
        if not self._cap.isOpened():
            self.error.emit("Camera not accessible")
            return

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        from vision.face_detector import FaceDetector
        from vision.emotion_smoothing import EmotionSmoother
        detector = FaceDetector()
        smoother = EmotionSmoother(window_seconds=5)

        frame_count = 0
        while self._running:
            ret, frame = self._cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            frame_count += 1

            if frame_count % 3 == 0:  # Process every 3rd frame
                faces = detector.detect(frame)
                for (x, y, w, h) in faces:
                    # Draw face box
                    cv2.rectangle(frame, (x, y), (x + w, y + h),
                                  (56, 184, 176), 2)
                    # Round corners effect
                    corner_len = min(w, h) // 6
                    for cx, cy in [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]:
                        cv2.circle(frame, (cx, cy), 5, (92, 207, 202), -1)

                    if self._predictor:
                        face_crop = frame[y:y + h, x:x + w]
                        try:
                            emotion, conf, probs = self._predictor.predict(face_crop)
                            smoothed = smoother.update(emotion, conf)
                            if smoothed:
                                self.emotion_detected.emit(smoothed, conf, probs)
                            # Label on frame
                            label = f"{emotion} {conf*100:.0f}%"
                            cv2.putText(frame, label, (x, y - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                                        (56, 184, 176), 2)
                        except Exception:
                            pass

            self.frame_ready.emit(frame)

    def stop(self):
        self._running = False
        if self._cap:
            self._cap.release()


# ══════════════════════════════════════════════════════════════
#  Camera View Label
# ══════════════════════════════════════════════════════════════
class CameraView(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(400, 320)
        self.setStyleSheet("""
            background: #0A1220;
            border-radius: 16px;
            color: rgba(56,184,176,0.5);
            font-size: 16px;
        """)
        self.setText("Camera loading...")
        self._overlay_text = ""

    def set_frame(self, frame: np.ndarray):
        h, w, c = frame.shape
        img = QImage(frame.data, w, h, w * c, QImage.Format_BGR888)
        pix = QPixmap.fromImage(img).scaled(
            self.width(), self.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.setPixmap(pix)

    def set_no_camera_text(self, text):
        self.setText(text)
        self.setPixmap(QPixmap())


# ══════════════════════════════════════════════════════════════
#  Live Camera Screen
# ══════════════════════════════════════════════════════════════
class LiveCameraScreen(QWidget):
    go_back = Signal()
    comfort_triggered = Signal()
    emotion_updated = Signal(str)

    COMFORT_EMOTIONS = {"sadness", "sad", "fear", "scared", "anger", "upset"}

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._child_data = db.get_child(child_id) or {}
        self._current_emotion = "neutral"
        self._camera_active = False
        self._cam_thread = None
        self._cam_worker = None
        self._comfort_count = 0
        self.setStyleSheet(MAIN_STYLE)
        self._build_ui()

    def _build_ui(self):
        self._bg = ParticleBackground(self)
        self._bg.lower()

        main = QHBoxLayout(self)
        main.setContentsMargins(28, 28, 28, 28)
        main.setSpacing(20)

        # ── Left: Camera + controls
        left = QVBoxLayout()
        left.setSpacing(14)

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
        back_btn.clicked.connect(self._on_back)
        title = QLabel("📷 Live Emotion Camera")
        title.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {COLORS['text']};")
        hdr.addWidget(back_btn)
        hdr.addSpacing(16)
        hdr.addWidget(title)
        hdr.addStretch()
        left.addLayout(hdr)

        # Camera view
        cam_card = GlassCard(self, radius=20)
        cam_card_layout = QVBoxLayout(cam_card)
        cam_card_layout.setContentsMargins(8, 8, 8, 8)
        self._cam_view = CameraView(self)
        cam_card_layout.addWidget(self._cam_view)
        left.addWidget(cam_card, 1)

        # Camera controls
        controls = QHBoxLayout()
        self._start_btn = QPushButton("▶  Start Camera")
        self._start_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {COLORS['teal']}, stop:1 {COLORS['teal_deep']});
                color: white; border: none; border-radius: 12px;
                padding: 11px 28px; font-size: 14px; font-weight: 700;
            }}
            QPushButton:hover {{ background: {COLORS['teal_glow']}; }}
        """)
        self._start_btn.clicked.connect(self._toggle_camera)

        self._snapshot_btn = QPushButton("📸  Snapshot")
        self._snapshot_btn.setEnabled(False)
        self._snapshot_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(56,184,176,0.10); color: {COLORS['teal_deep']};
                border: 1.5px solid {COLORS['teal']}; border-radius: 12px;
                padding: 10px 22px; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(56,184,176,0.22); }}
            QPushButton:disabled {{ opacity: 0.5; }}
        """)

        # VLM Smart Analysis button
        self._vlm_btn = QPushButton("🧠  Smart Analysis")
        self._vlm_btn.setEnabled(False)
        self._vlm_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #B388FF, stop:1 #00E5FF);
                color: white; border: none; border-radius: 12px;
                padding: 10px 22px; font-size: 13px; font-weight: 700;
            }}
            QPushButton:hover {{ background: #C39BFF; }}
            QPushButton:disabled {{ background: #C0C8D4; color: #8A9CB8; }}
        """)
        self._vlm_btn.clicked.connect(self._run_vlm_analysis)

        self._status_lbl = QLabel("Camera is off")
        self._status_lbl.setStyleSheet(f"font-size: 12px; color: {COLORS['text_light']};")

        controls.addWidget(self._start_btn)
        controls.addWidget(self._snapshot_btn)
        controls.addWidget(self._vlm_btn)
        controls.addStretch()
        controls.addWidget(self._status_lbl)
        left.addLayout(controls)

        main.addLayout(left, 1)

        # ── Right: ARIA + emotion bars
        right = QVBoxLayout()
        right.setSpacing(14)
        right.setContentsMargins(0, 0, 0, 0)

        # ARIA face
        face_card = GlassCard(self, radius=22)
        face_layout = QVBoxLayout(face_card)
        face_layout.setContentsMargins(20, 20, 20, 20)
        face_layout.setAlignment(Qt.AlignCenter)

        self._aria_face = ARIAFaceWidget(size=160)
        face_layout.addWidget(self._aria_face, alignment=Qt.AlignCenter)

        self._emotion_name_lbl = QLabel("Detecting...")
        self._emotion_name_lbl.setAlignment(Qt.AlignCenter)
        self._emotion_name_lbl.setStyleSheet(f"""
            font-size: 18px; font-weight: 700;
            color: {COLORS['teal']}; padding: 4px 0;
        """)
        face_layout.addWidget(self._emotion_name_lbl)

        self._confidence_lbl = QLabel("Confidence: —")
        self._confidence_lbl.setAlignment(Qt.AlignCenter)
        self._confidence_lbl.setStyleSheet(f"font-size: 12px; color: {COLORS['text_light']};")
        face_layout.addWidget(self._confidence_lbl)
        right.addWidget(face_card)

        # Emotion probability bars
        bars_card = GlassCard(self, radius=20)
        bars_layout = QVBoxLayout(bars_card)
        bars_layout.setContentsMargins(16, 14, 16, 14)
        bars_layout.setSpacing(6)

        bars_title = QLabel("EMOTION PROBABILITIES")
        bars_title.setStyleSheet(f"""
            font-size: 10px; font-weight: 700;
            color: {COLORS['teal_deep']}; letter-spacing: 2px;
        """)
        bars_layout.addWidget(bars_title)

        self._bars = {}
        emotions = ["happy", "calm", "sad", "scared", "upset", "surprised"]
        for em in emotions:
            bar = EmotionBar(em, bars_card)
            bars_layout.addWidget(bar)
            self._bars[em] = bar

        right.addWidget(bars_card)

        # ARIA reaction card
        react_card = GlassCard(self, radius=20)
        react_layout = QVBoxLayout(react_card)
        react_layout.setContentsMargins(16, 14, 16, 14)

        react_title = QLabel("ARIA SAYS")
        react_title.setStyleSheet(f"""
            font-size: 10px; font-weight: 700;
            color: {COLORS['teal_deep']}; letter-spacing: 2px;
        """)
        self._aria_says_lbl = QLabel("Start camera to begin detection.")
        self._aria_says_lbl.setWordWrap(True)
        self._aria_says_lbl.setStyleSheet(f"""
            font-size: 13px; color: {COLORS['text']};
            line-height: 1.6; padding: 4px 0;
        """)
        react_layout.addWidget(react_title)
        react_layout.addWidget(self._aria_says_lbl)

        comfort_btn = QPushButton("🌿 Start Calm Zone")
        comfort_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(107,159,212,0.15); color: #2A6090;
                border: 1.5px solid #6B9FD4; border-radius: 12px;
                padding: 10px 18px; font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(107,159,212,0.28); }}
        """)
        comfort_btn.clicked.connect(self.comfort_triggered.emit)
        react_layout.addWidget(comfort_btn)
        right.addWidget(react_card)

        # VLM Smart Analysis card
        vlm_card = GlassCard(self, radius=20)
        vlm_layout = QVBoxLayout(vlm_card)
        vlm_layout.setContentsMargins(16, 14, 16, 14)
        vlm_layout.setSpacing(8)
        vlm_title = QLabel("🧠  AI VISION ANALYSIS")
        vlm_title.setStyleSheet(f"""
            font-size: 10px; font-weight: 700;
            color: #6B4EBF; letter-spacing: 2px;
        """)
        vlm_layout.addWidget(vlm_title)
        self._vlm_emotion_lbl = QLabel("Click Smart Analysis ↑")
        self._vlm_emotion_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: #B388FF;")
        vlm_layout.addWidget(self._vlm_emotion_lbl)
        self._vlm_desc_lbl = QLabel("VLM gives rich emotion descriptions beyond labels.")
        self._vlm_desc_lbl.setWordWrap(True)
        self._vlm_desc_lbl.setStyleSheet(f"font-size: 12px; color: {COLORS['text']}; line-height: 1.5;")
        vlm_layout.addWidget(self._vlm_desc_lbl)
        self._vlm_body_lbl = QLabel("")
        self._vlm_body_lbl.setWordWrap(True)
        self._vlm_body_lbl.setStyleSheet(f"font-size: 11px; color: {COLORS['text_light']}; font-style: italic;")
        vlm_layout.addWidget(self._vlm_body_lbl)
        self._vlm_action_lbl = QLabel("")
        self._vlm_action_lbl.setWordWrap(True)
        self._vlm_action_lbl.setStyleSheet(f"font-size: 11px; color: #00BFA8; font-weight: 600;")
        vlm_layout.addWidget(self._vlm_action_lbl)
        right.addWidget(vlm_card)

        right.addStretch()
        main.addLayout(right)

    def _toggle_camera(self):
        if self._camera_active:
            self._stop_camera()
        else:
            self._start_camera()

    def _start_camera(self):
        self._camera_active = True
        self._start_btn.setText("⏹  Stop Camera")
        self._start_btn.setStyleSheet(f"""
            QPushButton {{
                background: #D96B6B; color: white;
                border: none; border-radius: 12px;
                padding: 11px 28px; font-size: 14px; font-weight: 700;
            }}
            QPushButton:hover {{ background: #E07070; }}
        """)
        self._snapshot_btn.setEnabled(True)
        self._vlm_btn.setEnabled(True)
        self._status_lbl.setText("🟢 Camera active")

        dev_settings = db.get_device_settings(self._child_id)
        cam_id = dev_settings.get("camera_id", 0)

        self._cam_thread = QThread()
        self._cam_worker = CameraWorker(cam_id)
        self._cam_worker.moveToThread(self._cam_thread)
        self._cam_thread.started.connect(self._cam_worker.start)
        self._cam_worker.frame_ready.connect(self._on_frame)
        self._cam_worker.emotion_detected.connect(self._on_emotion)
        self._cam_worker.error.connect(self._on_cam_error)
        self._cam_thread.start()

    def _stop_camera(self):
        self._camera_active = False
        if self._cam_worker:
            self._cam_worker.stop()
        if self._cam_thread:
            self._cam_thread.quit()
            self._cam_thread.wait(2000)
        self._start_btn.setText("▶  Start Camera")
        self._start_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {COLORS['teal']}, stop:1 {COLORS['teal_deep']});
                color: white; border: none; border-radius: 12px;
                padding: 11px 28px; font-size: 14px; font-weight: 700;
            }}
            QPushButton:hover {{ background: {COLORS['teal_glow']}; }}
        """)
        self._snapshot_btn.setEnabled(False)
        self._vlm_btn.setEnabled(False)
        self._status_lbl.setText("Camera is off")
        self._cam_view.set_no_camera_text("Camera stopped")

    def _on_frame(self, frame):
        self._cam_view.set_frame(frame)
        self._latest_frame = frame  # Cache for VLM

    def _run_vlm_analysis(self):
        """Trigger VLM analysis on the most recent frame."""
        if not hasattr(self, '_latest_frame') or self._latest_frame is None:
            self._vlm_emotion_lbl.setText("No frame yet — wait a moment")
            return

        self._vlm_btn.setEnabled(False)
        self._vlm_btn.setText("🧠  Analyzing...")
        self._vlm_emotion_lbl.setText("✨ AI analyzing...")
        self._vlm_desc_lbl.setText("Sending frame to vision AI...")
        self._vlm_body_lbl.setText("")
        self._vlm_action_lbl.setText("")

        from vision.vlm_emotion import VLMEmotionWorker
        self._vlm_thread = QThread()
        self._vlm_worker = VLMEmotionWorker(self._latest_frame, self._child_data)
        self._vlm_worker.moveToThread(self._vlm_thread)
        self._vlm_thread.started.connect(self._vlm_worker.run)
        self._vlm_worker.result_ready.connect(self._on_vlm_result)
        self._vlm_worker.error_occurred.connect(self._on_vlm_error)
        self._vlm_thread.start()

    def _on_vlm_result(self, data):
        emotion = data.get("emotion", "neutral").title()
        secondary = data.get("secondary_emotion", "")
        conf = data.get("confidence", 0)
        desc = data.get("description", "")
        body = data.get("body_language", "")
        action = data.get("suggested_action", "")

        label = f"{emotion} ({int(conf*100)}%)"
        if secondary:
            label += f" · {secondary}"
        self._vlm_emotion_lbl.setText(label)
        self._vlm_desc_lbl.setText(f"📝  {desc}")
        if body:
            self._vlm_body_lbl.setText(f"🧍  {body}")
        if action:
            self._vlm_action_lbl.setText(f"💡  {action}")

        self._vlm_btn.setEnabled(True)
        self._vlm_btn.setText("🧠  Smart Analysis")

        # Log to DB
        try:
            db.log_emotion(
                self._child_id,
                emotion.lower(),
                conf,
                source="vlm",
                action_taken=desc[:200],
            )
        except Exception:
            pass

        try:
            self._vlm_thread.quit()
        except Exception:
            pass

    def _on_vlm_error(self, msg):
        self._vlm_emotion_lbl.setText("⚠️ VLM unavailable")
        self._vlm_desc_lbl.setText(f"Error: {msg[:100]}")
        self._vlm_btn.setEnabled(True)
        self._vlm_btn.setText("🧠  Smart Analysis")
        try:
            self._vlm_thread.quit()
        except Exception:
            pass

    def _on_emotion(self, emotion: str, confidence: float, probs: dict):
        self._current_emotion = emotion
        self._aria_face.set_expression(emotion)
        self.emotion_updated.emit(emotion)

        color = get_emotion_color(emotion)
        ui_labels = {
            "happy": "Happy 😊", "joy": "Happy 😊",
            "neutral": "Calm 😌", "calm": "Calm 😌",
            "sadness": "Sad 😢", "sad": "Sad 😢",
            "fear": "Scared 😨", "scared": "Scared 😨",
            "anger": "Upset 😤", "upset": "Upset 😤",
            "surprise": "Surprised 😲", "surprised": "Surprised 😲",
        }
        label = ui_labels.get(emotion, emotion.title())
        self._emotion_name_lbl.setText(label)
        self._emotion_name_lbl.setStyleSheet(
            f"font-size: 18px; font-weight: 700; color: {color}; padding: 4px 0;"
        )
        self._confidence_lbl.setText(f"Confidence: {confidence * 100:.1f}%")

        # Update bars
        bar_map = {
            "happy": "happy", "joy": "happy",
            "neutral": "calm", "calm": "calm",
            "sadness": "sad", "sad": "sad",
            "fear": "scared", "scared": "scared",
            "anger": "upset", "upset": "upset",
            "surprise": "surprised", "surprised": "surprised",
        }
        for orig_em, prob in probs.items():
            bar_key = bar_map.get(orig_em, orig_em)
            if bar_key in self._bars:
                self._bars[bar_key].set_value(prob)

        # ARIA reaction
        self._set_aria_reaction(emotion, confidence)

        # Log and comfort check
        if confidence > 0.65:
            db.log_emotion(self._child_id, emotion, confidence,
                           source="live_camera", action="auto_detect")

            if emotion in self.COMFORT_EMOTIONS:
                self._comfort_count += 1
                if self._comfort_count >= 3:
                    self._comfort_count = 0
                    self.comfort_triggered.emit()
            else:
                self._comfort_count = 0

    def _set_aria_reaction(self, emotion, conf):
        lang = self._child_data.get("language", "en")
        child_name = self._child_data.get("name", "")

        reactions = {
            "en": {
                "happy": f"You look so happy{', ' + child_name if child_name else ''}! That's wonderful! 😊",
                "joy": f"You look so happy{', ' + child_name if child_name else ''}! That's wonderful! 😊",
                "neutral": "You look calm and relaxed. That's great! 😌",
                "calm": "You look calm and relaxed. That's great! 😌",
                "sad": "I see you might be feeling sad. I'm right here with you. 💙",
                "sadness": "I see you might be feeling sad. I'm right here with you. 💙",
                "fear": "It's okay to feel scared. I'm here. Let's breathe together. 🌬️",
                "scared": "It's okay to feel scared. I'm here. Let's breathe together. 🌬️",
                "anger": "It's okay to feel upset. Let's take a slow breath. 🌿",
                "upset": "It's okay to feel upset. Let's take a slow breath. 🌿",
                "surprise": "Oh! Something surprised you? Are you okay? 😲",
                "surprised": "Oh! Something surprised you? Are you okay? 😲",
            },
            "ar": {
                "happy": f"أنت شايف مبسوط{' يا ' + child_name if child_name else ''}! ده جميل! 😊",
                "joy": f"أنت شايف مبسوط{' يا ' + child_name if child_name else ''}! ده جميل! 😊",
                "neutral": "شايفك هادي ومرتاح. كويس! 😌",
                "calm": "شايفك هادي ومرتاح. كويس! 😌",
                "sad": "شايفك زعلان شوية. أنا معاك. 💙",
                "sadness": "شايفك زعلان شوية. أنا معاك. 💙",
                "fear": "مفيش مشكلة. أنا جنبك. خلينا ناخد نفس سوا. 🌬️",
                "scared": "مفيش مشكلة. أنا جنبك. خلينا ناخد نفس سوا. 🌬️",
                "anger": "طبيعي تحس بغضب أحياناً. خد نفس معايا. 🌿",
                "upset": "طبيعي تحس بغضب أحياناً. خد نفس معايا. 🌿",
                "surprise": "اتفاجأت بحاجة؟ أنت كويس؟ 😲",
                "surprised": "اتفاجأت بحاجة؟ أنت كويس؟ 😲",
            },
            "de": {
                "happy": f"Du siehst so glücklich aus{', ' + child_name if child_name else ''}! Das ist wunderbar! 😊",
                "sad": "Ich sehe, du bist vielleicht traurig. Ich bin bei dir. 💙",
                "sadness": "Ich sehe, du bist vielleicht traurig. Ich bin bei dir. 💙",
                "fear": "Es ist okay, Angst zu haben. Ich bin hier. Lass uns zusammen atmen. 🌬️",
                "scared": "Es ist okay, Angst zu haben. Ich bin hier. Lass uns zusammen atmen. 🌬️",
                "anger": "Es ist okay, wütend zu sein. Lass uns langsam atmen. 🌿",
                "neutral": "Du siehst ruhig aus. Gut! 😌",
            }
        }

        lang_reactions = reactions.get(lang, reactions["en"])
        msg = lang_reactions.get(emotion, f"I see you. You're doing great!")
        if conf < 0.60:
            msg = "I can see your face but I'm not sure of the emotion yet..."
        self._aria_says_lbl.setText(msg)

    def _on_cam_error(self, msg: str):
        self._cam_view.set_no_camera_text(f"⚠️ {msg}")
        self._camera_active = False

    def _on_back(self):
        if self._camera_active:
            self._stop_camera()
        self.go_back.emit()

    def resizeEvent(self, event):
        if hasattr(self, '_bg'):
            self._bg.resize(self.size())
        super().resizeEvent(event)

    def closeEvent(self, event):
        if self._camera_active:
            self._stop_camera()
        super().closeEvent(event)
