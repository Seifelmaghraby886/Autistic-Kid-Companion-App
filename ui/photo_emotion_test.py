"""ARIA Photo Emotion Test — Import image and classify emotion."""

import numpy as np
import cv2
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage

from ui.components import GlassCard, ARIAFaceWidget, EmotionBar, ParticleBackground
from ui.styles import MAIN_STYLE, COLORS, get_emotion_color
import database.db_manager as db


class PhotoEmotionTestScreen(QWidget):
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

        main = QHBoxLayout(self)
        main.setContentsMargins(32, 28, 32, 28)
        main.setSpacing(20)

        # ── Left: image display
        left = QVBoxLayout()
        left.setSpacing(14)

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
        title = QLabel("🖼️ Photo Emotion Test")
        title.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {COLORS['text']};")
        hdr.addWidget(back_btn)
        hdr.addSpacing(16)
        hdr.addWidget(title)
        hdr.addStretch()
        left.addLayout(hdr)

        # Image card
        img_card = GlassCard(self, radius=20)
        img_layout = QVBoxLayout(img_card)
        img_layout.setContentsMargins(10, 10, 10, 10)
        self._img_lbl = QLabel("Click 'Import Image' to begin")
        self._img_lbl.setAlignment(Qt.AlignCenter)
        self._img_lbl.setMinimumSize(400, 300)
        self._img_lbl.setStyleSheet("background: #0A1220; border-radius: 14px; color: rgba(56,184,176,0.6); font-size: 14px;")
        img_layout.addWidget(self._img_lbl)
        left.addWidget(img_card, 1)

        import_btn = QPushButton("📂  Import Image")
        import_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {COLORS['teal']}, stop:1 {COLORS['teal_deep']});
                color: white; border: none; border-radius: 14px;
                padding: 12px 30px; font-size: 14px; font-weight: 700;
            }}
            QPushButton:hover {{ background: {COLORS['teal_glow']}; }}
        """)
        import_btn.clicked.connect(self._import_image)
        left.addWidget(import_btn, alignment=Qt.AlignLeft)
        main.addLayout(left, 1)

        # ── Right: results
        right = QVBoxLayout()
        right.setSpacing(14)

        face_card = GlassCard(self, radius=22)
        fc = QVBoxLayout(face_card)
        fc.setContentsMargins(20, 20, 20, 20)
        fc.setAlignment(Qt.AlignCenter)
        self._aria_face = ARIAFaceWidget(size=140)
        fc.addWidget(self._aria_face, alignment=Qt.AlignCenter)
        self._result_lbl = QLabel("No result yet")
        self._result_lbl.setAlignment(Qt.AlignCenter)
        self._result_lbl.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {COLORS['teal']};")
        fc.addWidget(self._result_lbl)
        self._conf_lbl = QLabel("")
        self._conf_lbl.setAlignment(Qt.AlignCenter)
        self._conf_lbl.setStyleSheet(f"font-size: 12px; color: {COLORS['text_light']};")
        fc.addWidget(self._conf_lbl)
        right.addWidget(face_card)

        # Bars card
        bars_card = GlassCard(self, radius=20)
        bl = QVBoxLayout(bars_card)
        bl.setContentsMargins(16, 14, 16, 14)
        bl.setSpacing(6)
        bars_title = QLabel("EMOTION PROBABILITIES")
        bars_title.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {COLORS['teal_deep']}; letter-spacing: 2px;")
        bl.addWidget(bars_title)
        self._bars = {}
        for em in ["happy", "calm", "sad", "scared", "upset", "surprised"]:
            bar = EmotionBar(em, bars_card)
            bl.addWidget(bar)
            self._bars[em] = bar
        right.addWidget(bars_card)

        # ARIA says
        say_card = GlassCard(self, radius=20)
        sl = QVBoxLayout(say_card)
        sl.setContentsMargins(16, 14, 16, 14)
        sl.addWidget(QLabel("ARIA SAYS"))
        self._aria_says = QLabel("Import a photo to see ARIA's response!")
        self._aria_says.setWordWrap(True)
        self._aria_says.setStyleSheet(f"font-size: 13px; color: {COLORS['text']}; line-height: 1.6; padding: 4px 0;")
        sl.addWidget(self._aria_says)
        right.addWidget(say_card)
        right.addStretch()
        main.addLayout(right)

    def _import_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "",
            "Images (*.jpg *.jpeg *.png *.bmp *.webp)"
        )
        if not path:
            return
        self._analyze(path)

    def _analyze(self, path: str):
        try:
            frame = cv2.imread(path)
            if frame is None:
                self._result_lbl.setText("Could not load image")
                return

            # Show image
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = QImage(rgb.data, w, h, w * 3, QImage.Format_RGB888)
            pix = QPixmap.fromImage(img).scaled(
                self._img_lbl.width(), self._img_lbl.height(),
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self._img_lbl.setPixmap(pix)

            # Detect face
            from vision.face_detector import FaceDetector
            detector = FaceDetector()
            face = detector.get_largest_face(frame)

            if face is None:
                self._result_lbl.setText("No face detected")
                self._aria_says.setText("No clear face found. Try another image. 😊")
                return

            x, y, fw, fh = face
            face_crop = frame[y:y + fh, x:x + fw]

            # Predict
            from vision.emotion_predictor import EmotionPredictor
            predictor = EmotionPredictor()
            emotion, conf, probs = predictor.predict(face_crop)

            # Show
            color = get_emotion_color(emotion)
            labels = {
                "happy": "Happy 😊", "joy": "Happy 😊",
                "neutral": "Calm 😌", "calm": "Calm 😌",
                "sadness": "Sad 😢", "sad": "Sad 😢",
                "fear": "Scared 😨", "anger": "Upset 😤",
                "surprise": "Surprised 😲",
            }
            self._result_lbl.setText(labels.get(emotion, emotion.title()))
            self._result_lbl.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {color};")
            self._conf_lbl.setText(f"Confidence: {conf*100:.1f}%")
            self._aria_face.set_expression(emotion)

            bar_map = {"happy": "happy", "joy": "happy", "neutral": "calm",
                       "calm": "calm", "sadness": "sad", "fear": "scared",
                       "anger": "upset", "surprise": "surprised"}
            for em, prob in probs.items():
                bk = bar_map.get(em, em)
                if bk in self._bars:
                    self._bars[bk].set_value(prob)

            lang = self._child_data.get("language", "en")
            msgs = {
                "en": f"I can see this face looks {labels.get(emotion, emotion)}! That's okay — all feelings are valid. 💙",
                "ar": f"شايف إن الوش ده بيبان {labels.get(emotion, emotion)}! كل الإحساسات طبيعية. 💙",
                "de": f"Ich sehe, dieses Gesicht sieht {labels.get(emotion, emotion)} aus! Alle Gefühle sind okay. 💙",
            }
            self._aria_says.setText(msgs.get(lang, msgs["en"]))

            db.log_emotion(self._child_id, emotion, conf, source="photo_import")

        except Exception as e:
            self._result_lbl.setText("Analysis error")
            self._aria_says.setText(f"Something went wrong: {e}")

    def resizeEvent(self, event):
        if hasattr(self, '_bg'):
            self._bg.resize(self.size())
        super().resizeEvent(event)
