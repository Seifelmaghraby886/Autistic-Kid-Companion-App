"""
ARIA Settings Screen
API key, device config, voice, model training launcher.
"""

import json
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QScrollArea, QFrame, QTabWidget,
    QSlider, QCheckBox, QProgressBar, QTextEdit, QSizePolicy, QDialog
)
from PySide6.QtCore import Qt, Signal, QThread, QObject, QTimer
from PySide6.QtGui import QFont

from ui.components import GlassCard, ParticleBackground, ToastNotification
from ui.styles import MAIN_STYLE, COLORS
import database.db_manager as db

ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "config" / "app_config.json"


def load_config():
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print(f"[Config save error] {e}")


# ══════════════════════════════════════════════════════════════
#  ML Training Worker
# ══════════════════════════════════════════════════════════════
class TrainingWorker(QObject):
    progress = Signal(int)
    log_msg = Signal(str)
    finished = Signal(bool)  # success

    def run(self):
        try:
            from ml_training.prepare_datasets import prepare_combined_dataset
            from ml_training.train_emotion_model import train
            from ml_training.evaluate_model import evaluate_and_plot

            self.log_msg.emit("━━ Step 1: Preparing datasets ━━")
            prepare_combined_dataset(
                progress_callback=lambda p: self.progress.emit(int(p * 0.3)),
            )
            self.log_msg.emit("\n━━ Step 2: Training model ━━")
            train(
                progress_callback=lambda p: self.progress.emit(30 + int(p * 0.6)),
                log_callback=self.log_msg.emit,
            )
            self.log_msg.emit("\n━━ Step 3: Evaluating ━━")
            evaluate_and_plot(
                progress_callback=lambda p: self.progress.emit(90 + int(p * 0.10)),
                log_callback=self.log_msg.emit,
            )
            self.progress.emit(100)
            self.finished.emit(True)
        except Exception as e:
            self.log_msg.emit(f"\n❌ Error: {e}")
            self.finished.emit(False)


# ══════════════════════════════════════════════════════════════
#  Settings Screen
# ══════════════════════════════════════════════════════════════
class SettingsScreen(QWidget):
    go_back = Signal()
    settings_saved = Signal()

    def __init__(self, child_id=None, parent_id=None, parent=None):
        super().__init__(parent)
        # Resolve active child if not explicitly passed
        if not child_id:
            child_id = db.get_setting("active_child_id")
        if not child_id:
            children = db.get_all_children()
            if children:
                child_id = children[0]["child_id"]
                db.set_setting("active_child_id", child_id)
        self._child_id = child_id

        if not parent_id:
            parent_id = db.get_setting("active_parent_id")
        if not parent_id:
            parents = db.get_all_parents()
            if parents:
                parent_id = parents[0]["parent_id"]
        self._parent_id = parent_id

        self._cfg = load_config()
        self.setStyleSheet(MAIN_STYLE)
        self._build_ui()

    def _build_ui(self):
        self._bg = ParticleBackground(self)
        self._bg.lower()

        main = QVBoxLayout(self)
        main.setContentsMargins(32, 24, 32, 24)
        main.setSpacing(16)

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
        title = QLabel("⚙️ Settings")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {COLORS['text']};")
        hdr.addWidget(back_btn)
        hdr.addSpacing(20)
        hdr.addWidget(title)
        hdr.addStretch()
        main.addLayout(hdr)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self._build_api_tab(),       "🤖 AI & API")
        tabs.addTab(self._build_training_tab(),  "🧠 Train Model")
        tabs.addTab(self._build_device_tab(),    "🎙️ Devices")
        tabs.addTab(self._build_voice_tab(),     "🔊 Voice")
        tabs.addTab(self._build_privacy_tab(),   "🔒 Privacy")
        main.addWidget(tabs, 1)

    def _section_label(self, text):
        lbl = QLabel(text.upper())
        lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {COLORS['teal_deep']}; letter-spacing: 2px; padding: 8px 0 4px 0;")
        return lbl

    def _build_api_tab(self):
        w = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # ── Active provider selector
        prov_card = GlassCard(w, radius=20)
        pcl = QVBoxLayout(prov_card)
        pcl.setContentsMargins(24, 18, 24, 18)
        pcl.addWidget(self._section_label("Active AI Provider"))
        info = QLabel(
            "Choose your primary AI. ARIA will automatically fall back to others if rate-limited.\n"
            "🌟 Recommendation: Add Groq for FREE high-volume backup."
        )
        info.setStyleSheet(f"font-size: 12px; color: {COLORS['text_light']}; line-height: 1.6;")
        info.setWordWrap(True)
        pcl.addWidget(info)
        self._provider_combo = QComboBox()
        self._provider_combo.addItems([
            "groq       — Llama 3.3 ★ FREE 30 req/min, fastest",
            "cerebras   — Llama 3.3 ★ FREE 8000 req/day",
            "openrouter — Multi-model FREE",
            "gemini     — Google (FREE 15 req/min)",
            "ollama     — LOCAL (offline, infinite)",
            "anthropic  — Claude (paid, best empathy)",
            "openai     — GPT-4o (paid)",
        ])
        cur = self._cfg.get("ai_provider", "gemini")
        for i in range(self._provider_combo.count()):
            if self._provider_combo.itemText(i).startswith(cur):
                self._provider_combo.setCurrentIndex(i); break
        pcl.addWidget(self._provider_combo)
        layout.addWidget(prov_card)

        # ── Gemini
        layout.addWidget(self._provider_card(
            "🟦 Gemini (Google)",
            "gemini_api_key",
            "https://aistudio.google.com/app/apikey",
            "FREE — 15 req/min on flash",
            "gemini_model",
            ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-pro",
             "gemini-2.0-flash", "gemini-flash-latest"],
        ))

        # ── Groq
        layout.addWidget(self._provider_card(
            "⚡ Groq (Llama-3.3 — FREE & FAST)",
            "groq_api_key",
            "https://console.groq.com/keys",
            "FREE — 30 req/min, instant speed",
            "groq_model",
            ["llama-3.3-70b-versatile", "llama-3.1-8b-instant",
             "mixtral-8x7b-32768", "gemma2-9b-it"],
        ))

        # ── Cerebras (NEW — also free, super fast)
        layout.addWidget(self._provider_card(
            "🚀 Cerebras (Llama-3.3 — FREE 8000 req/day)",
            "cerebras_api_key",
            "https://cloud.cerebras.ai/platform/",
            "FREE — 8,000 req/day, fastest hosted",
            "cerebras_model",
            ["llama-3.3-70b", "llama3.1-8b", "llama3.1-70b"],
        ))

        # ── OpenRouter (NEW — aggregator with free models)
        layout.addWidget(self._provider_card(
            "🌐 OpenRouter (multi-model aggregator)",
            "openrouter_api_key",
            "https://openrouter.ai/keys",
            "FREE tier on selected models",
            "openrouter_model",
            ["meta-llama/llama-3.3-70b-instruct:free",
             "google/gemini-2.0-flash-exp:free",
             "deepseek/deepseek-r1:free",
             "qwen/qwen-2.5-72b-instruct:free"],
        ))

        # ── Anthropic
        layout.addWidget(self._provider_card(
            "🧡 Anthropic Claude (most empathetic)",
            "anthropic_api_key",
            "https://console.anthropic.com/settings/keys",
            "$5 free trial then paid · best for kindness",
            "anthropic_model",
            ["claude-3-5-haiku-20241022", "claude-3-5-sonnet-20241022",
             "claude-3-opus-20240229"],
        ))

        # ── OpenAI
        layout.addWidget(self._provider_card(
            "🟢 OpenAI GPT (NOT ChatGPT Plus — separate billing)",
            "openai_api_key",
            "https://platform.openai.com/api-keys",
            "Paid · $0.15/1M tokens for gpt-4o-mini",
            "openai_model",
            ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
        ))

        save_api_btn = QPushButton("💾  Save All AI Settings")
        save_api_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {COLORS['teal']}, stop:0.5 #00E5FF, stop:1 #B388FF);
                color: white; border: none; border-radius: 14px;
                padding: 13px 32px; font-size: 14px; font-weight: 700;
            }}
        """)
        save_api_btn.clicked.connect(self._save_api)
        layout.addWidget(save_api_btn, alignment=Qt.AlignLeft)
        layout.addStretch()

        scroll.setWidget(content)
        main = QVBoxLayout(w)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(scroll)
        return w

    def _provider_card(self, title, key_name, url, note, model_key, models):
        card = GlassCard(self, radius=18)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(22, 16, 22, 16)
        cl.setSpacing(8)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {COLORS['text']};")
        cl.addWidget(title_lbl)

        note_lbl = QLabel(note)
        note_lbl.setStyleSheet(f"font-size: 11px; color: {COLORS['text_light']};")
        cl.addWidget(note_lbl)

        key_field = QLineEdit()
        key_field.setPlaceholderText("Paste API key here...")
        key_field.setEchoMode(QLineEdit.Password)
        key_field.setText(self._cfg.get(key_name, ""))
        if not hasattr(self, '_api_fields'):
            self._api_fields = {}
        self._api_fields[key_name] = key_field
        cl.addWidget(key_field)

        # Model selector
        row = QHBoxLayout()
        model_combo = QComboBox()
        model_combo.addItems(models)
        cur_model = self._cfg.get(model_key, models[0])
        if cur_model in models:
            model_combo.setCurrentText(cur_model)
        if not hasattr(self, '_model_combos'):
            self._model_combos = {}
        self._model_combos[model_key] = model_combo
        row.addWidget(QLabel("Model:"))
        row.addWidget(model_combo)
        row.addStretch()
        cl.addLayout(row)

        link_lbl = QLabel(f"Get key at: <a href='{url}' style='color:#00BFA8;'>{url[:50]}...</a>")
        link_lbl.setOpenExternalLinks(True)
        link_lbl.setStyleSheet(f"font-size: 11px; color: {COLORS['text_light']};")
        cl.addWidget(link_lbl)
        return card

    def _build_training_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        info_card = GlassCard(w, radius=20)
        ic = QVBoxLayout(info_card)
        ic.setContentsMargins(24, 18, 24, 18)
        ic.setSpacing(8)

        ic.addWidget(self._section_label("Emotion Model Training"))
        info = QLabel(
            "This will:\n"
            "1. Extract and prepare your 3 datasets\n"
            "2. Train a MobileNetV2 emotion classifier\n"
            "3. Save emotion_model.h5 + emotion_model.tflite\n"
            "4. Generate evaluation reports\n\n"
            "⚠️ This may take 30–90 minutes on CPU."
        )
        info.setStyleSheet(f"font-size: 13px; color: {COLORS['text']}; line-height: 1.7;")
        ic.addWidget(info)

        self._train_btn = QPushButton("🚀  Start Training")
        self._train_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #4CAF90, stop:1 #38B8B0);
                color: white; border: none; border-radius: 14px;
                padding: 13px 30px; font-size: 15px; font-weight: 700;
            }}
            QPushButton:hover {{ background: #5CCFCA; }}
            QPushButton:disabled {{ background: #B0C4C4; }}
        """)
        self._train_btn.clicked.connect(self._start_training)
        ic.addWidget(self._train_btn)

        layout.addWidget(info_card)

        # Progress
        prog_card = GlassCard(w, radius=18)
        pc = QVBoxLayout(prog_card)
        pc.setContentsMargins(20, 14, 20, 14)
        pc.setSpacing(8)

        self._prog_bar = QProgressBar()
        self._prog_bar.setRange(0, 100)
        self._prog_bar.setValue(0)
        self._prog_bar.setFixedHeight(14)
        self._prog_bar.setTextVisible(True)
        self._prog_lbl = QLabel("Not started")
        self._prog_lbl.setStyleSheet(f"font-size: 12px; color: {COLORS['text_light']};")
        pc.addWidget(QLabel("Training Progress:"))
        pc.addWidget(self._prog_bar)
        pc.addWidget(self._prog_lbl)
        layout.addWidget(prog_card)

        # Log
        log_card = GlassCard(w, radius=18)
        lc = QVBoxLayout(log_card)
        lc.setContentsMargins(16, 12, 16, 12)
        lc.addWidget(QLabel("Training Log:"))
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setStyleSheet(f"""
            QTextEdit {{
                background: #0A1220; color: #5CCFCA;
                border: none; border-radius: 10px;
                font-family: Consolas, monospace; font-size: 11px;
                padding: 10px;
            }}
        """)
        self._log_text.setMinimumHeight(200)
        lc.addWidget(self._log_text)
        layout.addWidget(log_card, 1)
        return w

    def _build_device_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)

        card = GlassCard(w, radius=20)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(24, 20, 24, 20)
        cl.setSpacing(10)
        cl.addWidget(self._section_label("Microphone"))

        self._mic_combo = QComboBox()
        try:
            from speech.stt_engine import get_available_microphones
            mics = get_available_microphones()
            for mic_id, mic_name in mics:
                self._mic_combo.addItem(mic_name[:60], mic_id)
        except Exception:
            self._mic_combo.addItem("Default", 0)

        # Restore current mic
        if self._child_id:
            try:
                ds = db.get_device_settings(self._child_id) or {}
                cur = ds.get("microphone_id")
                if cur is not None:
                    for i in range(self._mic_combo.count()):
                        if self._mic_combo.itemData(i) == cur:
                            self._mic_combo.setCurrentIndex(i)
                            break
            except Exception:
                pass

        cl.addWidget(QLabel("Select Microphone:"))
        cl.addWidget(self._mic_combo)

        # Mic test
        test_mic_btn = QPushButton("🎙 Test Microphone (3 sec)")
        test_mic_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0,191,168,0.10); color: {COLORS['teal_deep']};
                border: 1.5px solid {COLORS['teal']}; border-radius: 10px;
                padding: 8px 16px; font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(0,191,168,0.22); }}
        """)
        test_mic_btn.clicked.connect(self._test_mic)
        self._mic_test_lbl = QLabel("")
        self._mic_test_lbl.setStyleSheet(f"font-size: 12px; color: {COLORS['text_light']};")
        cl.addWidget(test_mic_btn, alignment=Qt.AlignLeft)
        cl.addWidget(self._mic_test_lbl)

        cl.addSpacing(10)
        cl.addWidget(self._section_label("Camera"))
        self._cam_combo = QComboBox()
        try:
            from speech.stt_engine import get_available_cameras
            cams = get_available_cameras()
            for cam_id, cam_name in cams:
                self._cam_combo.addItem(cam_name, cam_id)
        except Exception:
            for i in range(4):
                self._cam_combo.addItem(f"Camera {i}", i)

        if self._child_id:
            try:
                ds = db.get_device_settings(self._child_id) or {}
                cur = ds.get("camera_id")
                if cur is not None:
                    for i in range(self._cam_combo.count()):
                        if self._cam_combo.itemData(i) == cur:
                            self._cam_combo.setCurrentIndex(i)
                            break
            except Exception:
                pass

        cl.addWidget(QLabel("Select Camera:"))
        cl.addWidget(self._cam_combo)

        test_cam_btn = QPushButton("📷 Test Camera")
        test_cam_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0,191,168,0.10); color: {COLORS['teal_deep']};
                border: 1.5px solid {COLORS['teal']}; border-radius: 10px;
                padding: 8px 16px; font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(0,191,168,0.22); }}
        """)
        test_cam_btn.clicked.connect(self._test_camera)
        self._cam_test_lbl = QLabel("")
        self._cam_test_lbl.setStyleSheet(f"font-size: 12px; color: {COLORS['text_light']};")
        cl.addWidget(test_cam_btn, alignment=Qt.AlignLeft)
        cl.addWidget(self._cam_test_lbl)

        save_dev_btn = QPushButton("💾  Save Device Settings")
        save_dev_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {COLORS['teal']}, stop:1 {COLORS['teal_deep']});
                color: white; border: none; border-radius: 12px;
                padding: 11px 24px; font-size: 13px; font-weight: 700;
            }}
        """)
        save_dev_btn.clicked.connect(self._save_devices)
        cl.addSpacing(10)
        cl.addWidget(save_dev_btn, alignment=Qt.AlignLeft)
        layout.addWidget(card)
        layout.addStretch()
        return w

    def _build_voice_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)

        card = GlassCard(w, radius=20)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(24, 20, 24, 20)
        cl.setSpacing(10)
        cl.addWidget(self._section_label("Voice Settings"))

        voice_settings = {}
        if self._child_id:
            voice_settings = db.get_voice_settings(self._child_id)

        speed_lbl = QLabel("Speech Speed")
        speed_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {COLORS['text_light']};")
        self._speed_slider = QSlider(Qt.Horizontal)
        self._speed_slider.setRange(-50, 10)
        self._speed_slider.setValue(voice_settings.get("speed", -20))
        cl.addWidget(speed_lbl)
        cl.addWidget(self._speed_slider)

        vol_lbl = QLabel("Volume")
        vol_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {COLORS['text_light']};")
        self._vol_slider = QSlider(Qt.Horizontal)
        self._vol_slider.setRange(0, 100)
        self._vol_slider.setValue(int(voice_settings.get("volume", 0.8) * 100))
        cl.addWidget(vol_lbl)
        cl.addWidget(self._vol_slider)

        save_voice_btn = QPushButton("💾  Save Voice Settings")
        save_voice_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {COLORS['teal']}, stop:1 {COLORS['teal_deep']});
                color: white; border: none; border-radius: 12px;
                padding: 11px 24px; font-size: 13px; font-weight: 700;
            }}
        """)
        save_voice_btn.clicked.connect(self._save_voice)
        cl.addSpacing(10)
        cl.addWidget(save_voice_btn, alignment=Qt.AlignLeft)
        layout.addWidget(card)
        layout.addStretch()
        return w

    def _build_privacy_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)

        card = GlassCard(w, radius=20)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(24, 20, 24, 20)
        cl.setSpacing(12)
        cl.addWidget(self._section_label("Privacy Controls"))

        notice = QLabel(
            "ARIA is an assistive companion system. It does not diagnose or treat autism.\n"
            "It supports communication, emotional regulation, routine, and parent-supervised interaction.\n\n"
            "Audio/video are NOT saved by default.\n"
            "Emotion predictions and session summaries can be saved locally."
        )
        notice.setStyleSheet(f"font-size: 13px; color: {COLORS['text']}; line-height: 1.7;")
        notice.setWordWrap(True)
        cl.addWidget(notice)

        self._save_emotion_cb = QCheckBox("Save emotion logs")
        self._save_emotion_cb.setChecked(True)
        self._save_chat_cb = QCheckBox("Save chat logs")
        self._save_chat_cb.setChecked(True)
        cl.addWidget(self._save_emotion_cb)
        cl.addWidget(self._save_chat_cb)

        # Sensory accommodation — persists straight to app_config.json.
        # Backgrounds pick it up on the next app start.
        self._reduce_motion_cb = QCheckBox(
            "🫧 Reduce motion (sensory-friendly, applies after restart)")
        self._reduce_motion_cb.setChecked(bool(self._cfg.get("reduce_motion", False)))
        def _save_motion(state):
            self._cfg["reduce_motion"] = bool(state)
            save_config(self._cfg)
        self._reduce_motion_cb.stateChanged.connect(_save_motion)
        cl.addWidget(self._reduce_motion_cb)

        cl.addSpacing(8)
        danger_lbl = QLabel("⚠️ DANGER ZONE")
        danger_lbl.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {COLORS['danger']}; letter-spacing: 2px;")
        cl.addWidget(danger_lbl)

        if self._child_id:
            del_btn = QPushButton("🗑️  Delete All Child Data")
            del_btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(217,107,107,0.15); color: {COLORS['danger']};
                    border: 1.5px solid {COLORS['danger']}; border-radius: 12px;
                    padding: 10px 20px; font-size: 13px; font-weight: 600;
                }}
                QPushButton:hover {{ background: rgba(217,107,107,0.28); }}
            """)
            del_btn.clicked.connect(self._confirm_delete)
            cl.addWidget(del_btn, alignment=Qt.AlignLeft)

        layout.addWidget(card)
        layout.addStretch()
        return w

    def _save_api(self):
        # Save active provider
        prov_text = self._provider_combo.currentText().split()[0]
        self._cfg["ai_provider"] = prov_text

        # Save all keys
        for key_name, field in (self._api_fields or {}).items():
            self._cfg[key_name] = field.text().strip()

        # Save all models
        for model_key, combo in (self._model_combos or {}).items():
            self._cfg[model_key] = combo.currentText()

        save_config(self._cfg)
        toast = ToastNotification(
            self, f"✅ Saved! Active provider: {prov_text}", kind="success"
        )
        toast.move(self.width() // 2 - toast.width() // 2, 30)
        toast.show()

    def _save_devices(self):
        if self._child_id:
            try:
                mic_data = self._mic_combo.currentData()
                mic_id = int(mic_data) if mic_data is not None else 0
                mic_name = self._mic_combo.currentText()
                cam_data = self._cam_combo.currentData()
                cam_id = int(cam_data) if cam_data is not None else 0
                cam_name = self._cam_combo.currentText()

                db.update_device_settings(
                    self._child_id,
                    microphone_id=mic_id,
                    microphone_name=mic_name,
                    camera_id=cam_id,
                    camera_name=cam_name,
                )
                toast = ToastNotification(
                    self,
                    f"✅ Saved! Mic: {mic_name[:25]} · Cam: {cam_name}",
                    kind="success"
                )
            except Exception as e:
                toast = ToastNotification(self, f"❌ Save error: {e}", kind="error")
        else:
            toast = ToastNotification(self, "No active child profile", kind="warning")

        toast.move(self.width() // 2 - toast.width() // 2, 30)
        toast.show()

    def _test_mic(self):
        """Quick 3-second mic test."""
        self._mic_test_lbl.setText("🔴 Recording for 3 seconds...")
        try:
            import pyaudio, threading, time
            mic_id = self._mic_combo.currentData()
            mic_id = int(mic_id) if mic_id is not None else 0
            from speech.stt_engine import STTWorker

            def do_test():
                try:
                    pa = pyaudio.PyAudio()
                    stream = pa.open(
                        format=pyaudio.paInt16, channels=1, rate=16000,
                        input=True, input_device_index=mic_id,
                        frames_per_buffer=1024
                    )
                    max_vol = 0
                    for _ in range(48):  # ~3 seconds
                        data = stream.read(1024, exception_on_overflow=False)
                        import struct, math
                        shorts = struct.unpack(f"{len(data)//2}h", data)
                        rms = math.sqrt(sum(s*s for s in shorts) / len(shorts))
                        max_vol = max(max_vol, rms)
                        time.sleep(0.01)
                    stream.stop_stream(); stream.close(); pa.terminate()
                    if max_vol > 200:
                        self._mic_test_lbl.setText(f"✅ Mic working! Peak: {int(max_vol)}")
                    else:
                        self._mic_test_lbl.setText(f"⚠️ Very quiet (peak: {int(max_vol)}). Speak louder?")
                except Exception as e:
                    self._mic_test_lbl.setText(f"❌ Mic error: {e}")

            threading.Thread(target=do_test, daemon=True).start()
        except Exception as e:
            self._mic_test_lbl.setText(f"❌ {e}")

    def _test_camera(self):
        self._cam_test_lbl.setText("📷 Opening camera...")
        try:
            import cv2
            cam_id = self._cam_combo.currentData()
            cam_id = int(cam_id) if cam_id is not None else 0
            from vision.camera import open_camera
            cap = open_camera(cam_id)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                if ret:
                    self._cam_test_lbl.setText(f"✅ Camera {cam_id} works! ({frame.shape[1]}x{frame.shape[0]})")
                else:
                    self._cam_test_lbl.setText(f"⚠️ Camera {cam_id} opened but no frame")
            else:
                self._cam_test_lbl.setText(f"❌ Camera {cam_id} not accessible")
        except Exception as e:
            self._cam_test_lbl.setText(f"❌ {e}")

    def _save_voice(self):
        if self._child_id:
            db.update_voice_settings(
                self._child_id,
                speed=self._speed_slider.value(),
                volume=self._vol_slider.value() / 100.0,
            )
        toast = ToastNotification(self, "Voice settings saved!", kind="success")
        toast.move(self.width() // 2 - toast.width() // 2, 30)
        toast.show()

    def _start_training(self):
        self._train_btn.setEnabled(False)
        self._train_btn.setText("⏳ Training in progress...")
        self._log_text.clear()
        self._prog_bar.setValue(0)
        self._prog_lbl.setText("Starting...")

        self._train_thread = QThread()
        self._train_worker = TrainingWorker()
        self._train_worker.moveToThread(self._train_thread)
        self._train_thread.started.connect(self._train_worker.run)
        self._train_worker.progress.connect(self._on_train_progress)
        self._train_worker.log_msg.connect(self._on_train_log)
        self._train_worker.finished.connect(self._on_train_done)
        self._train_thread.start()

    def _on_train_progress(self, pct):
        self._prog_bar.setValue(pct)
        self._prog_lbl.setText(f"{pct}% complete")

    def _on_train_log(self, msg):
        self._log_text.append(msg)
        self._log_text.verticalScrollBar().setValue(
            self._log_text.verticalScrollBar().maximum()
        )

    def _on_train_done(self, success):
        self._train_thread.quit()
        self._train_btn.setEnabled(True)
        if success:
            self._train_btn.setText("✅ Training Complete! Retrain?")
            self._prog_lbl.setText("Training successful!")
        else:
            self._train_btn.setText("❌ Failed — Try Again")
            self._prog_lbl.setText("Training failed. See log above.")

    def _confirm_delete(self):
        from PySide6.QtWidgets import QMessageBox
        if not self._child_id:
            return
        msg = QMessageBox(self)
        msg.setWindowTitle("Clear activity history")
        msg.setText(
            "Erase this child's chats, emotion logs, and sessions?\n\n"
            "The profile, preferences, and device settings will be kept.\n"
            "For full profile removal, use Parent Dashboard → Export tab."
        )
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        msg.setDefaultButton(QMessageBox.Cancel)
        if msg.exec() != QMessageBox.Yes:
            return
        try:
            db.clear_child_history(self._child_id)
            toast = ToastNotification(
                self, "✅ Activity history cleared.", kind="success"
            )
        except Exception as e:
            toast = ToastNotification(
                self, f"Couldn't clear history: {e}", kind="error"
            )
        toast.move(self.width() // 2 - toast.width() // 2, 30)
        toast.show()

    def resizeEvent(self, event):
        if hasattr(self, '_bg'):
            self._bg.resize(self.size())
        super().resizeEvent(event)
