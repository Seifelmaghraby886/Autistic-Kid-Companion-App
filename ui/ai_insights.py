"""
ARIA AI Insights — analyzes child's emotion + behavior history with Gemini.
Generates patterns, trends, and recommendations for parents.
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


class InsightWorker(QObject):
    insights_ready = Signal(dict)
    error = Signal(str)

    def __init__(self, child_id):
        super().__init__()
        self._child_id = child_id

    def run(self):
        try:
            import json
            from pathlib import Path
            from collections import Counter

            cfg_path = Path(__file__).parent.parent / "config" / "app_config.json"
            with open(cfg_path) as f:
                cfg = json.load(f)
            api_key = cfg.get("gemini_api_key", "").strip()
            model_name = cfg.get("gemini_model", "gemini-2.0-flash")

            child = db.get_child(self._child_id) or {}
            prefs = db.get_child_preferences(self._child_id)
            emotions = db.get_emotion_logs(self._child_id, 200)
            chats = db.get_chat_logs(self._child_id, 50)
            sessions = db.get_sessions_for_child(self._child_id, 30)

            # Build summary
            em_counts = Counter(e.get("emotion", "neutral") for e in emotions)
            em_summary = ", ".join(f"{k}: {v}" for k, v in em_counts.most_common(6))

            sources = Counter(e.get("source", "unknown") for e in emotions)
            source_summary = ", ".join(f"{k}: {v}" for k, v in sources.most_common(5))

            if not api_key:
                self._fallback(em_counts, len(sessions))
                return

            import google.generativeai as genai
            genai.configure(api_key=api_key)

            prompt = f"""You are an autism support analytics expert reviewing a child's recent behavior data.

Child profile:
- Name: {child.get('name', 'Child')}
- Age: {child.get('age', '?')}
- Communication level: {child.get('communication_level', '?')}
- Sensory mode: {child.get('sensory_mode', '?')}
- Known triggers: {', '.join(prefs.get('known_triggers', []))}
- Calming methods: {', '.join(prefs.get('calming_methods', []))}

Recent data (last ~200 events):
- Emotion frequency: {em_summary}
- Detection sources: {source_summary}
- Total chat messages: {len(chats)}
- Total sessions: {len(sessions)}

Generate parent-facing insights as JSON:
{{
  "summary": "2-3 sentence overall picture",
  "patterns": ["pattern 1", "pattern 2", "pattern 3"],
  "concerns": ["concern 1 if any, or empty list"],
  "wins": ["positive observation 1", "positive observation 2"],
  "recommendations": ["actionable suggestion 1", "actionable suggestion 2", "actionable suggestion 3"]
}}

Be evidence-based, kind, and specific. Reference the actual data.
DO NOT diagnose. DO NOT recommend medical treatment. ONLY parent-actionable suggestions.
Return ONLY JSON, no markdown."""

            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            raw = response.text.strip()
            import re
            raw = re.sub(r'```(?:json)?', '', raw).strip()
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                data = json.loads(match.group())
                self.insights_ready.emit(data)
            else:
                self._fallback(em_counts, len(sessions))
        except Exception as e:
            print(f"[Insights error: {e}]")
            try:
                self._fallback(Counter(), 0)
            except Exception:
                self.insights_ready.emit({})

    def _fallback(self, em_counts, n_sessions):
        positive = sum(em_counts.get(k, 0) for k in ["happy", "joy", "calm", "neutral"])
        negative = sum(em_counts.get(k, 0) for k in ["sadness", "fear", "anger"])
        total = positive + negative

        self.insights_ready.emit({
            "summary": (
                f"Recorded {sum(em_counts.values())} emotion events across {n_sessions} sessions. "
                f"{positive} positive vs {negative} challenging."
            ),
            "patterns": [
                f"Most common emotion: {em_counts.most_common(1)[0][0] if em_counts else 'neutral'}",
                f"Total interactions: {n_sessions} sessions",
                "Add API key in Settings for full AI analysis",
            ],
            "concerns": [],
            "wins": [
                f"Consistent engagement across {n_sessions} sessions",
                "Child is using ARIA regularly",
            ],
            "recommendations": [
                "Continue regular check-ins",
                "Add Gemini API key for personalized AI insights",
                "Review the emotion timeline weekly",
            ],
        })


class AIInsightsScreen(QWidget):
    go_back = Signal()

    def __init__(self, child_id, parent=None):
        super().__init__(parent)
        self._child_id = child_id
        self._child_data = db.get_child(child_id) or {}
        self.setStyleSheet(MAIN_STYLE)
        self._build_ui()
        self._start_analysis()

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
        title = QLabel(f"💡 AI Insights for {self._child_data.get('name', 'Child')}")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {COLORS['text']};")
        sub = QLabel("Patterns, wins, and recommendations from real data")
        sub.setStyleSheet(f"font-size: 13px; color: {COLORS['text_light']};")
        hdr.addWidget(back_btn); hdr.addSpacing(20)
        col = QVBoxLayout(); col.addWidget(title); col.addWidget(sub)
        hdr.addLayout(col); hdr.addStretch()
        main.addLayout(hdr)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        self._content = QWidget()
        self._content.setStyleSheet("background: transparent;")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setSpacing(16)
        self._content_layout.setContentsMargins(0, 0, 8, 0)

        self._loading_lbl = QLabel("✨ Analyzing data with AI...")
        self._loading_lbl.setAlignment(Qt.AlignCenter)
        self._loading_lbl.setStyleSheet(f"font-size: 16px; color: {COLORS['teal_deep']}; padding: 60px;")
        self._content_layout.addWidget(self._loading_lbl)

        scroll.setWidget(self._content)
        main.addWidget(scroll, 1)

    def _start_analysis(self):
        self._thread = QThread()
        self._worker = InsightWorker(self._child_id)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.insights_ready.connect(self._on_insights)
        self._thread.start()

    def _on_insights(self, data: dict):
        # Clear loading
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not data:
            err = QLabel("Could not generate insights. Add API key in Settings.")
            err.setStyleSheet(f"font-size: 14px; color: {COLORS['danger']}; padding: 30px;")
            self._content_layout.addWidget(err)
            return

        # Summary
        if data.get("summary"):
            self._content_layout.addWidget(self._make_card(
                "📊 SUMMARY", data["summary"], COLORS["teal"]
            ))

        # Patterns
        if data.get("patterns"):
            self._content_layout.addWidget(self._make_list_card(
                "🔍 PATTERNS DETECTED", data["patterns"], "#00E5FF"
            ))

        # Wins
        if data.get("wins"):
            self._content_layout.addWidget(self._make_list_card(
                "🌟 WINS", data["wins"], "#00D9A0"
            ))

        # Concerns
        if data.get("concerns"):
            self._content_layout.addWidget(self._make_list_card(
                "⚠️ AREAS TO WATCH", data["concerns"], "#FFB73D"
            ))

        # Recommendations
        if data.get("recommendations"):
            self._content_layout.addWidget(self._make_list_card(
                "💡 RECOMMENDATIONS", data["recommendations"], "#B388FF"
            ))

        self._content_layout.addStretch()
        try:
            self._thread.quit()
        except Exception:
            pass

    def _make_card(self, title, content, color):
        card = GlassCard(self._content, radius=18)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 14, 20, 14)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {color}; letter-spacing: 2px;")
        body = QLabel(content)
        body.setWordWrap(True)
        body.setStyleSheet(f"font-size: 14px; color: {COLORS['text']}; line-height: 1.7; padding-top: 4px;")
        layout.addWidget(title_lbl)
        layout.addWidget(body)
        return card

    def _make_list_card(self, title, items, color):
        card = GlassCard(self._content, radius=18)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(8)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {color}; letter-spacing: 2px;")
        layout.addWidget(title_lbl)
        for item in items:
            row = QHBoxLayout()
            bullet = QLabel("●")
            bullet.setStyleSheet(f"color: {color}; font-size: 14px; padding-right: 6px;")
            text_lbl = QLabel(str(item))
            text_lbl.setWordWrap(True)
            text_lbl.setStyleSheet(f"font-size: 13px; color: {COLORS['text']}; line-height: 1.6;")
            row.addWidget(bullet, 0, Qt.AlignTop)
            row.addWidget(text_lbl, 1)
            layout.addLayout(row)
        return card
