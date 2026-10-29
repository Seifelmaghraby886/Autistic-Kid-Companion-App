"""
ARIA — Adaptive Robotic Interaction Assistant
A 24/7 AI Companion Platform for Autistic Children
Main Application Entry Point
"""

import sys
import os
import traceback
from pathlib import Path

# Ensure project root is in path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget,
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QFrame, QScrollArea, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Signal
from PySide6.QtGui import QIcon, QFont, QColor

from ui.styles import MAIN_STYLE, COLORS
from ui.splash_screen import SplashScreen
import database.db_manager as db


# Human-readable version stamp shown in the welcome footer.
# Bump when you ship a demo / present to examiners.
APP_VERSION = "1.1"


def _format_last_seen(iso_ts: str) -> str:
    """Return a short, human label for a child's last_active timestamp."""
    if not iso_ts:
        return "Never used yet"
    try:
        from datetime import datetime
        then = datetime.fromisoformat(iso_ts)
        delta = datetime.now() - then
        secs = int(delta.total_seconds())
        if secs < 60:
            return "Last seen just now"
        if secs < 3600:
            return f"Last seen {secs // 60} min ago"
        if secs < 86400:
            return f"Last seen {secs // 3600} h ago"
        days = secs // 86400
        if days == 1:
            return "Last seen yesterday"
        if days < 7:
            return f"Last seen {days} days ago"
        return f"Last seen on {then.strftime('%b %d')}"
    except Exception:
        return ""


def check_first_run() -> bool:
    return db.get_setting("first_run", True)


def get_active_parent_id():
    return db.get_setting("active_parent_id", None)


def get_active_child_id():
    return db.get_setting("active_child_id", None)


def _kiosk_enabled() -> bool:
    """Kiosk mode = frameless fullscreen + on-screen keyboard (no mouse/keyboard)."""
    try:
        import json
        cfg = json.loads((ROOT / "config" / "app_config.json")
                         .read_text(encoding="utf-8"))
        return bool(cfg.get("kiosk_mode", True))
    except Exception:
        return True


def _auto_start_enabled() -> bool:
    """Robot boot: skip the profile picker and open the voice shell directly."""
    try:
        import json
        cfg = json.loads((ROOT / "config" / "app_config.json")
                         .read_text(encoding="utf-8"))
        return bool(cfg.get("auto_start_child", True))
    except Exception:
        return True


def _face_input_enabled() -> bool:
    """Face input = camera presence / look-to-listen / head gestures."""
    try:
        import json
        cfg = json.loads((ROOT / "config" / "app_config.json")
                         .read_text(encoding="utf-8"))
        return bool(cfg.get("face_input_enabled", True))
    except Exception:
        return True


# Global crash handler
def excepthook(exc_type, exc_value, exc_tb):
    err = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(f"\n{'='*60}\nCRASH PREVENTED:\n{err}\n{'='*60}\n")
    try:
        with open(ROOT / "crash.log", "a") as f:
            f.write(err + "\n---\n")
    except Exception:
        pass


sys.excepthook = excepthook


# ══════════════════════════════════════════════════════════════
#  Welcome Back Screen
# ══════════════════════════════════════════════════════════════
class WelcomeBackScreen(QWidget):
    child_selected = Signal(int)
    setup_new = Signal()
    parent_mode = Signal()

    def __init__(self, parent_id, parent=None):
        super().__init__(parent)
        self._parent_id = parent_id
        self.setStyleSheet(MAIN_STYLE)
        self._build_ui()

    def _build_ui(self):
        from ui.components import ParticleBackground, GlassCard, ARIAFaceWidget

        self._bg = ParticleBackground(self)
        self._bg.lower()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 30, 60, 40)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignTop)

        aria_lbl = QLabel("ARIA")
        aria_lbl.setAlignment(Qt.AlignCenter)
        aria_lbl.setStyleSheet(f"""
            font-size: 48px; font-weight: 900;
            color: {COLORS['teal']}; letter-spacing: 16px;
        """)
        sub_lbl = QLabel("Adaptive Robotic Interaction Assistant")
        sub_lbl.setAlignment(Qt.AlignCenter)
        sub_lbl.setStyleSheet(f"font-size: 14px; color: {COLORS['text_light']}; letter-spacing: 2px;")
        layout.addWidget(aria_lbl)
        layout.addWidget(sub_lbl)

        face = ARIAFaceWidget(size=140)
        face.set_expression("happy")
        layout.addWidget(face, alignment=Qt.AlignCenter)

        parent_data = db.get_parent(self._parent_id)
        name = parent_data.get("name", "").split()[0] if parent_data else ""
        greet = QLabel(f"Welcome back{', ' + name if name else ''}! 👋")
        greet.setAlignment(Qt.AlignCenter)
        greet.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {COLORS['text']};")
        layout.addWidget(greet)

        children = db.get_children_for_parent(self._parent_id)
        if children:
            children_lbl = QLabel("WHO IS USING ARIA TODAY?")
            children_lbl.setAlignment(Qt.AlignCenter)
            children_lbl.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {COLORS['teal_deep']}; letter-spacing: 2px; padding-top: 12px;")
            layout.addWidget(children_lbl)

            cards_row = QHBoxLayout()
            cards_row.setAlignment(Qt.AlignCenter)
            cards_row.setSpacing(16)

            for child in children:
                card = GlassCard(self, radius=20, hover_lift=True)
                card.setFixedSize(170, 158)
                cl = QVBoxLayout(card)
                cl.setContentsMargins(16, 14, 16, 14)
                cl.setAlignment(Qt.AlignCenter)
                cl.setSpacing(2)

                icon_lbl = QLabel("👦" if child.get("age", 10) <= 12 else "👩")
                icon_lbl.setAlignment(Qt.AlignCenter)
                icon_lbl.setStyleSheet("font-size: 32px; background: transparent;")

                name_lbl = QLabel(child["name"])
                name_lbl.setAlignment(Qt.AlignCenter)
                name_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLORS['text']}; background: transparent;")

                age_lbl = QLabel(f"Age {child.get('age', '?')}")
                age_lbl.setAlignment(Qt.AlignCenter)
                age_lbl.setStyleSheet(f"font-size: 11px; color: {COLORS['text_light']}; background: transparent;")

                seen_lbl = QLabel(_format_last_seen(child.get("last_active")))
                seen_lbl.setAlignment(Qt.AlignCenter)
                seen_lbl.setStyleSheet(
                    f"font-size: 10px; color: {COLORS['text_light']};"
                    f"font-style: italic; background: transparent;"
                )

                select_btn = QPushButton("Start →")
                select_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {COLORS['teal']}; color: white;
                        border: none; border-radius: 10px;
                        padding: 6px 14px; font-size: 12px; font-weight: 700;
                    }}
                    QPushButton:hover {{ background: {COLORS['teal_glow']}; }}
                """)
                select_btn.clicked.connect(lambda checked, cid=child["child_id"]: self._select_child(cid))

                cl.addWidget(icon_lbl)
                cl.addWidget(name_lbl)
                cl.addWidget(age_lbl)
                cl.addWidget(seen_lbl)
                cl.addSpacing(2)
                cl.addWidget(select_btn)
                cards_row.addWidget(card)

            layout.addLayout(cards_row)
        else:
            # Empty state — much friendlier than a blank gap.
            empty = QLabel(
                "No child profiles yet.\n"
                "Tap “+ Add Child Profile” below to create the first one."
            )
            empty.setAlignment(Qt.AlignCenter)
            empty.setWordWrap(True)
            empty.setStyleSheet(
                f"font-size: 14px; color: {COLORS['text_light']};"
                f"font-style: italic; padding: 24px;"
                f"background: rgba(0,191,168,0.06); border-radius: 16px;"
            )
            layout.addSpacing(8)
            layout.addWidget(empty)

        bottom = QHBoxLayout()
        bottom.setAlignment(Qt.AlignCenter)
        bottom.setSpacing(12)

        add_btn = QPushButton("+ Add Child Profile")
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(56,184,176,0.10); color: {COLORS['teal_deep']};
                border: 1.5px solid {COLORS['teal']}; border-radius: 14px;
                padding: 12px 24px; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(56,184,176,0.22); }}
        """)
        add_btn.clicked.connect(self.setup_new.emit)

        parent_btn = QPushButton("🔐 Parent Dashboard")
        parent_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(217,107,107,0.12); color: #C05050;
                border: 1.5px solid rgba(217,107,107,0.3); border-radius: 14px;
                padding: 12px 24px; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(217,107,107,0.22); }}
        """)
        parent_btn.clicked.connect(self.parent_mode.emit)

        bottom.addWidget(add_btn)
        bottom.addWidget(parent_btn)
        layout.addSpacing(12)
        layout.addLayout(bottom)
        layout.addStretch()

        # Small version footer — gives examiners a build stamp at a glance.
        footer = QLabel(f"ARIA OS  ·  v{APP_VERSION}")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet(
            f"font-size: 10px; color: {COLORS['text_light']};"
            f"letter-spacing: 2px; padding-top: 12px; opacity: 0.7;"
        )
        layout.addWidget(footer)

    def _select_child(self, child_id):
        db.set_setting("active_child_id", child_id)
        self.child_selected.emit(child_id)

    def resizeEvent(self, event):
        if hasattr(self, '_bg'):
            self._bg.resize(self.size())
        super().resizeEvent(event)


# ══════════════════════════════════════════════════════════════
#  Main Window
# ══════════════════════════════════════════════════════════════
class ARIAMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ARIA — AI Companion for Autistic Children")
        self.setMinimumSize(1200, 750)
        self.resize(1400, 900)
        self.setStyleSheet(MAIN_STYLE)

        # Kiosk mode: frameless — ARIA OS owns the whole screen like an OS.
        self._kiosk = _kiosk_enabled()
        if self._kiosk:
            self.setWindowFlag(Qt.FramelessWindowHint, True)

        icon_path = ROOT / "assets" / "icons" / "aria_icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Restore active IDs from DB at startup
        self._parent_id = db.get_setting("active_parent_id")
        self._child_id = db.get_setting("active_child_id")

        # If still none but children exist, pick the first one
        if not self._child_id:
            children = db.get_all_children()
            if children:
                self._child_id = children[0]["child_id"]
                db.set_setting("active_child_id", self._child_id)
        if not self._parent_id:
            parents = db.get_all_parents()
            if parents:
                self._parent_id = parents[0]["parent_id"]
                db.set_setting("active_parent_id", self._parent_id)

        # Intelligence bus follows the restored child from the very start.
        try:
            from core.child_context import get_context
            get_context().set_child(self._child_id)
        except Exception:
            pass

        self._current_emotion = "calm"
        self._current_screen = None
        self._conversation = None     # ARIA OS voice engine — persists across screens
        self._emotion_monitor = None  # ambient camera emotion watcher
        self._face_input = None       # camera presence / look-to-listen / gestures
        self._shell = None

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._show_splash()

    def _show_splash(self):
        self._splash = SplashScreen()
        self._splash.finished.connect(self._on_splash_done)
        self._splash.show()

    def _present(self):
        """Show the window — fullscreen in kiosk mode, a normal window otherwise."""
        if self._kiosk:
            self.showFullScreen()
        else:
            self.show()

    def _on_splash_done(self):
        try:
            if check_first_run():
                self._show_parent_setup()
            else:
                parent_id = get_active_parent_id()
                if parent_id:
                    self._parent_id = parent_id
                    # Robot mode: the device boots straight into ARIA.
                    # A pre-reading child can't work a profile picker — go
                    # directly to the voice shell; ARIA greets and listens.
                    if self._child_id and _auto_start_enabled():
                        self._on_child_selected(self._child_id)
                    else:
                        self._show_welcome_back()
                else:
                    self._show_parent_setup()
            self._present()
        except Exception as e:
            traceback.print_exc()
            self._show_parent_setup()
            self._present()

    def _safe_navigate(self, factory_fn):
        """Wrap navigation in try/except to prevent crashes."""
        try:
            screen = factory_fn()
            self._switch_to(screen)
        except Exception as e:
            traceback.print_exc()
            QMessageBox.warning(
                self, "Navigation Error",
                f"Couldn't open that screen.\n\n{type(e).__name__}: {e}"
            )

    def _show_parent_setup(self):
        def make():
            from ui.parent_profile import ParentProfileSetup
            screen = ParentProfileSetup()
            screen.setup_complete.connect(self._on_parent_setup_done)
            return screen
        self._safe_navigate(make)

    def _on_parent_setup_done(self, parent_id):
        self._parent_id = parent_id
        db.set_setting("active_parent_id", parent_id)
        db.set_setting("first_run", False)
        self._show_child_setup()

    def _show_child_setup(self):
        def make():
            from ui.child_profile import ChildProfileSetup
            screen = ChildProfileSetup(self._parent_id)
            screen.setup_complete.connect(self._on_child_setup_done)
            return screen
        self._safe_navigate(make)

    def _on_child_setup_done(self, child_id):
        self._child_id = child_id
        db.set_setting("active_child_id", child_id)
        self._show_shell()

    def _show_welcome_back(self):
        def make():
            screen = WelcomeBackScreen(self._parent_id)
            screen.child_selected.connect(self._on_child_selected)
            screen.setup_new.connect(self._show_child_setup)
            screen.parent_mode.connect(self._show_parent_dashboard)
            return screen
        self._safe_navigate(make)

    def _on_child_selected(self, child_id):
        self._child_id = child_id
        try:
            from core.child_context import get_context
            get_context().set_child(child_id)
        except Exception:
            pass
        self._show_shell()

    def _ensure_conversation(self):
        """Create the persistent ARIA OS voice engine once a child is active."""
        if self._conversation is None and self._child_id:
            try:
                from core.conversation import ConversationEngine
                self._conversation = ConversationEngine(self._child_id)
                self._conversation.navigate_requested.connect(self._navigate)
                self._conversation.comfort_triggered.connect(self._show_calm_auto)
            except Exception:
                traceback.print_exc()
                self._conversation = None
        return self._conversation

    def _ensure_emotion_monitor(self):
        """Create the ambient camera emotion monitor (parent can disable it)."""
        if _face_input_enabled():
            return None   # face input owns the shell camera instead
        if self._emotion_monitor is None and self._child_id:
            try:
                import json
                cfg = json.loads((ROOT / "config" / "app_config.json")
                                  .read_text(encoding="utf-8"))
                if not cfg.get("ambient_emotion_enabled", True):
                    return None
            except Exception:
                pass
            try:
                from core.emotion_monitor import EmotionMonitor
                self._emotion_monitor = EmotionMonitor(self._child_id)
                self._emotion_monitor.emotion_detected.connect(self._on_ambient_emotion)
                self._emotion_monitor.distress_detected.connect(self._on_camera_distress)
                self._emotion_monitor.monitor_error.connect(
                    lambda m: print(f"[ARIA-OS] camera monitor: {m}", flush=True))
            except Exception:
                traceback.print_exc()
                self._emotion_monitor = None
        return self._emotion_monitor

    def _ensure_face_input(self):
        """Create the camera face-input engine — presence / look / gestures."""
        if self._face_input is None and self._child_id and _face_input_enabled():
            try:
                from core.face_input import FaceInputEngine
                self._face_input = FaceInputEngine(self._child_id)
                self._face_input.presence_changed.connect(self._on_presence)
                self._face_input.gesture_detected.connect(self._on_gesture)
                self._face_input.monitor_error.connect(self._on_face_error)
            except Exception:
                traceback.print_exc()
                self._face_input = None
        return self._face_input

    def _on_presence(self, present):
        """A child appeared in / left the camera view."""
        if self._conversation is not None:
            try:
                self._conversation.notify_presence(bool(present))
            except Exception:
                pass
        # let the shell show "I see you" / "Looking for you" feedback
        scr = self._current_screen
        if scr is not None and hasattr(scr, "set_presence"):
            try:
                scr.set_presence(bool(present))
            except Exception:
                pass

    def _on_gesture(self, gesture):
        """A head nod / shake — hand it to the current screen if it uses it."""
        scr = self._current_screen
        if scr is not None and hasattr(scr, "on_gesture"):
            try:
                scr.on_gesture(gesture)
            except Exception:
                pass

    def _on_face_error(self, msg):
        print(f"[ARIA-OS] face input: {msg}", flush=True)

    def _show_shell(self):
        """ARIA OS home — voice-first, hands-free. The default screen."""
        engine = self._ensure_conversation()
        self._ensure_emotion_monitor()
        self._ensure_face_input()
        # Listening is continuous when the child is present; face_input
        # provides only presence wake/idle and head-nod/shake gestures.

        def make():
            from ui.shell import ARIAShell
            self._shell = ARIAShell(self._child_id, engine)
            self._shell.navigate.connect(self._navigate)
            return self._shell

        # The shell self-starts the engine once it is on screen and settled,
        # so ARIA never begins greeting/listening on top of another screen.
        self._safe_navigate(make)

    def _show_dashboard(self):
        def make():
            from ui.dashboard import DashboardScreen
            self._dashboard = DashboardScreen(self._child_id)
            self._dashboard.navigate.connect(self._navigate)
            if hasattr(self._dashboard, "go_back"):
                self._dashboard.go_back.connect(self._show_shell)
            return self._dashboard
        self._safe_navigate(make)

    def _navigate(self, destination: str):
        nav_map = {
            "talk":       self._show_talk,
            "camera":     self._show_camera,
            "photo":      self._show_photo,
            "games":      self._show_games,
            "calm":       self._show_calm,
            "schedule":   self._show_schedule,
            "comms":      self._show_comms,
            "parent":     self._show_parent_dashboard,
            "settings":   self._show_settings,
            "sensory":    self._show_sensory,
            "journal":    self._show_journal,
            "story":      self._show_story,
            "rewards":    self._show_rewards,
            "timer":      self._show_timer,
            "aac":        self._show_aac,
            "transition": self._show_transition,
            "coach":      self._show_coach,
            "bedtime":    self._show_bedtime,
            "insights":   self._show_insights,
            "music":      self._show_music,
            "tutorials":  self._show_tutorials,
            "thermometer":self._show_thermometer,
            "firstthen":  self._show_first_then,
            "social":     self._show_social,
            "biometric":  self._show_biometric,
            "home":       self._show_shell,
            "shell":      self._show_shell,
            "dashboard":  self._show_dashboard,
            "providers":  self._show_provider_center,
        }
        fn = nav_map.get(destination)
        if fn:
            fn()

    def _show_talk(self):
        def make():
            from ui.talk_screen import TalkScreen
            screen = TalkScreen(self._child_id)
            screen.go_back.connect(self._show_shell)
            screen.comfort_mode_triggered.connect(self._show_calm_auto)
            screen.emotion_updated.connect(self._on_emotion_update)
            return screen
        self._safe_navigate(make)

    def _show_camera(self):
        def make():
            from ui.live_camera import LiveCameraScreen
            screen = LiveCameraScreen(self._child_id)
            screen.go_back.connect(self._show_shell)
            screen.comfort_triggered.connect(self._show_calm_auto)
            screen.emotion_updated.connect(self._on_emotion_update)
            return screen
        self._safe_navigate(make)

    def _show_photo(self):
        def make():
            from ui.photo_emotion_test import PhotoEmotionTestScreen
            screen = PhotoEmotionTestScreen(self._child_id)
            screen.go_back.connect(self._show_shell)
            return screen
        self._safe_navigate(make)

    def _show_games(self):
        def make():
            from ui.games import GamesScreen
            screen = GamesScreen(self._child_id)
            screen.go_back.connect(self._show_shell)
            return screen
        self._safe_navigate(make)

    def _show_calm(self):
        self._show_calm_zone(auto_start=False)

    def _show_calm_auto(self):
        self._show_calm_zone(auto_start=True)

    def _show_calm_zone(self, auto_start=False):
        def make():
            from ui.calm_zone import CalmZoneScreen
            screen = CalmZoneScreen(self._child_id, auto_start=auto_start)
            screen.go_back.connect(self._show_shell)
            return screen
        self._safe_navigate(make)

    def _show_schedule(self):
        def make():
            from ui.visual_schedule import VisualScheduleScreen
            screen = VisualScheduleScreen(self._child_id)
            screen.go_back.connect(self._show_shell)
            return screen
        self._safe_navigate(make)

    def _show_comms(self):
        def make():
            from ui.communication_board import CommunicationBoardScreen
            screen = CommunicationBoardScreen(self._child_id)
            screen.go_back.connect(self._show_shell)
            return screen
        self._safe_navigate(make)

    def _show_parent_dashboard(self):
        if not self._parent_id:
            return
        def make():
            from ui.parent_dashboard import ParentDashboardScreen
            screen = ParentDashboardScreen(self._child_id, self._parent_id)
            screen.go_back.connect(self._show_shell)
            return screen
        self._safe_navigate(make)

    def _show_settings(self):
        def make():
            from ui.settings import SettingsScreen
            screen = SettingsScreen(self._child_id, self._parent_id)
            screen.go_back.connect(self._show_shell)
            return screen
        self._safe_navigate(make)

    def _show_provider_center(self):
        def make():
            from ui.provider_center import ProviderCenterScreen
            screen = ProviderCenterScreen(self._child_id)
            screen.go_back.connect(self._show_shell)
            return screen
        self._safe_navigate(make)

    # ── New impressive features
    def _show_sensory(self):
        def make():
            from ui.sensory_toolkit import SensoryToolkitScreen
            screen = SensoryToolkitScreen(self._child_id)
            screen.go_back.connect(self._show_shell)
            return screen
        self._safe_navigate(make)

    def _show_journal(self):
        def make():
            from ui.mood_journal import MoodJournalScreen
            screen = MoodJournalScreen(self._child_id)
            screen.go_back.connect(self._show_shell)
            return screen
        self._safe_navigate(make)

    def _show_story(self):
        def make():
            from ui.story_generator import StoryGeneratorScreen
            screen = StoryGeneratorScreen(self._child_id)
            screen.go_back.connect(self._show_shell)
            return screen
        self._safe_navigate(make)

    def _show_rewards(self):
        def make():
            from ui.reward_system import RewardSystemScreen
            screen = RewardSystemScreen(self._child_id)
            screen.go_back.connect(self._show_shell)
            return screen
        self._safe_navigate(make)

    def _show_timer(self):
        def make():
            from ui.visual_timer import VisualTimerScreen
            screen = VisualTimerScreen(self._child_id)
            screen.go_back.connect(self._show_shell)
            return screen
        self._safe_navigate(make)

    def _show_aac(self):
        def make():
            from ui.aac_builder import AACBuilderScreen
            screen = AACBuilderScreen(self._child_id)
            screen.go_back.connect(self._show_shell)
            return screen
        self._safe_navigate(make)

    def _show_transition(self):
        def make():
            from ui.transition_helper import TransitionHelperScreen
            screen = TransitionHelperScreen(self._child_id)
            screen.go_back.connect(self._show_shell)
            return screen
        self._safe_navigate(make)

    def _show_coach(self):
        def make():
            from ui.ai_coach import AICoachScreen
            screen = AICoachScreen(self._child_id)
            screen.go_back.connect(self._show_shell)
            return screen
        self._safe_navigate(make)

    def _show_bedtime(self):
        def make():
            from ui.bedtime_story import BedtimeStoryScreen
            screen = BedtimeStoryScreen(self._child_id)
            screen.go_back.connect(self._show_shell)
            return screen
        self._safe_navigate(make)

    def _show_insights(self):
        def make():
            from ui.ai_insights import AIInsightsScreen
            screen = AIInsightsScreen(self._child_id)
            screen.go_back.connect(self._show_shell)
            return screen
        self._safe_navigate(make)

    def _show_music(self):
        def make():
            from ui.music_player import MusicPlayerScreen
            s = MusicPlayerScreen(self._child_id); s.go_back.connect(self._show_shell)
            return s
        self._safe_navigate(make)

    def _show_tutorials(self):
        def make():
            from ui.task_tutorials import TaskTutorialsScreen
            s = TaskTutorialsScreen(self._child_id); s.go_back.connect(self._show_shell)
            return s
        self._safe_navigate(make)

    def _show_thermometer(self):
        def make():
            from ui.feelings_thermometer import FeelingsThermometerScreen
            s = FeelingsThermometerScreen(self._child_id); s.go_back.connect(self._show_shell)
            return s
        self._safe_navigate(make)

    def _show_first_then(self):
        def make():
            from ui.first_then import FirstThenScreen
            s = FirstThenScreen(self._child_id); s.go_back.connect(self._show_shell)
            return s
        self._safe_navigate(make)

    def _show_social(self):
        def make():
            from ui.social_coach import SocialCoachScreen
            s = SocialCoachScreen(self._child_id); s.go_back.connect(self._show_shell)
            return s
        self._safe_navigate(make)

    def _show_biometric(self):
        def make():
            from ui.biometric_screen import BiometricScreen
            s = BiometricScreen(self._child_id); s.go_back.connect(self._show_shell)
            return s
        self._safe_navigate(make)

    def _on_emotion_update(self, emotion: str):
        self._current_emotion = emotion
        try:
            from core.child_context import get_context
            get_context().record_emotion(emotion, source="app")
        except Exception:
            pass
        scr = self._current_screen
        if scr is not None and hasattr(scr, "set_emotion"):
            try:
                scr.set_emotion(emotion)
            except Exception:
                pass
        # Let the always-on voice companion adapt its tone to the camera.
        if self._conversation is not None:
            try:
                self._conversation.set_emotion(emotion)
            except Exception:
                pass

    def _on_ambient_emotion(self, emotion: str, confidence: float):
        """Ambient camera emotion — feed it through the normal emotion path."""
        self._on_emotion_update(emotion)

    def _on_camera_distress(self, emotion: str):
        """Camera saw sustained distress — gently offer the Calm Zone, never forced."""
        print(f"[ARIA-OS] camera distress '{emotion}' — offering a calm moment",
              flush=True)
        scr = self._current_screen
        if type(scr).__name__ == "ARIAShell":
            try:
                scr.show_comfort_offer(emotion)
            except Exception:
                traceback.print_exc()
        if self._conversation is not None:
            try:
                self._conversation.announce_comfort()
            except Exception:
                pass

    def _switch_to(self, widget: QWidget):
        """Switch screens with a short fade-in.

        The opacity effect is installed only for the animation and removed on
        finish — a permanent effect flattens child drop-shadows (learned the
        hard way), a 180 ms temporary one is invisible.
        """
        old = self._current_screen
        self._current_screen = widget

        self._stack.addWidget(widget)
        self._stack.setCurrentWidget(widget)
        self._fade_in(widget)

        # Intelligence bus: remember where the child went.
        try:
            from core.child_context import get_context
            get_context().record_visit(type(widget).__name__)
        except Exception:
            pass

        # ARIA OS voice — three modes depending on the screen:
        #   home shell / tool grid -> full conversation
        #   a tool that owns the mic -> paused (it listens for itself)
        #   every other tool        -> tool-voice (spoken commands click buttons)
        if self._conversation is not None:
            cls = type(widget).__name__
            try:
                if cls in ("ARIAShell", "DashboardScreen"):
                    self._conversation.detach_tool()
                    self._conversation.resume_listening()
                elif cls in ("TalkScreen",):
                    self._conversation.detach_tool()
                    self._conversation.pause_listening()
                else:
                    self._conversation.attach_tool(widget)
            except Exception:
                pass

        # ARIA OS ambient camera: watch the child's mood only on the home
        # shell; release the camera everywhere else so camera tools can use it.
        if self._emotion_monitor is not None:
            try:
                if type(widget).__name__ == "ARIAShell":
                    self._emotion_monitor.start()
                else:
                    self._emotion_monitor.stop()
            except Exception:
                pass

        # ARIA OS face input: presence / look-to-listen / head gestures run
        # only on the home shell; the camera is released for every other screen.
        if self._face_input is not None:
            try:
                if type(widget).__name__ == "ARIAShell":
                    self._face_input.start()
                else:
                    self._face_input.stop()
            except Exception:
                pass

        # Cleanup old screen
        if old and old is not widget:
            QTimer.singleShot(50, lambda o=old: self._cleanup_widget(o))

    def _fade_in(self, widget: QWidget, ms: int = 180):
        """Animate widget opacity 0 -> 1, then drop the effect entirely."""
        try:
            from PySide6.QtWidgets import QGraphicsOpacityEffect
            eff = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(eff)
            anim = QPropertyAnimation(eff, b"opacity", widget)
            anim.setDuration(ms)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.OutCubic)

            def _done():
                try:
                    widget.setGraphicsEffect(None)  # restore native shadows
                except Exception:
                    pass
            anim.finished.connect(_done)
            anim.start(QPropertyAnimation.DeleteWhenStopped)
        except Exception:
            pass  # transition is decoration — never let it break navigation

    def _cleanup_widget(self, old):
        try:
            self._stack.removeWidget(old)
            for child in old.findChildren(QTimer):
                try:
                    child.stop()
                except Exception:
                    pass
            old.setParent(None)
            old.deleteLater()
        except Exception as e:
            print(f"Cleanup warning: {e}")

    def keyPressEvent(self, event):
        # Esc is always a guaranteed way out of fullscreen kiosk mode.
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        # Persist today's session into ARIA's long-term memory first —
        # after this line the child's day survives the restart.
        try:
            from core.child_context import get_context
            get_context().consolidate_to_memory()
        except Exception:
            pass
        # Stop everything before close
        try:
            if self._conversation is not None:
                self._conversation.shutdown()
        except Exception:
            pass
        try:
            if self._emotion_monitor is not None:
                self._emotion_monitor.shutdown()
        except Exception:
            pass
        try:
            if self._face_input is not None:
                self._face_input.shutdown()
        except Exception:
            pass
        try:
            if self._current_screen:
                for child in self._current_screen.findChildren(QTimer):
                    try:
                        child.stop()
                    except Exception:
                        pass
        except Exception:
            pass
        super().closeEvent(event)


def main():
    # Pre-initialize pygame mixer ON MAIN THREAD before Qt starts
    try:
        import pygame
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        print("[pygame mixer pre-initialized OK]")
    except Exception as e:
        print(f"[pygame mixer pre-init: {e}]")

    # Preload Whisper in background so first Arabic recording is fast
    try:
        import threading
        from speech.stt_engine import preload_whisper
        # Get active child language to preload right model
        import database.db_manager as db
        children = db.get_all_children()
        lang = "ar"  # Default to Arabic since user is Egyptian
        if children:
            active_id = db.get_setting("active_child_id")
            if active_id:
                child = db.get_child(active_id)
                if child:
                    lang = child.get("language", "ar")
        threading.Thread(target=preload_whisper, args=(lang,), daemon=True).start()
        print(f"[Preloading Whisper for '{lang}' in background...]")
    except Exception as e:
        print(f"[Whisper preload skipped: {e}]")

    app = QApplication(sys.argv)
    app.setApplicationName("ARIA")
    app.setOrganizationName("ARIA AI")
    app.setApplicationVersion("1.0.0")

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = ARIAMainWindow()

    # Kiosk mode: install the app-wide on-screen keyboard so ARIA OS can be
    # operated with no physical keyboard.
    try:
        if _kiosk_enabled():
            from ui.virtual_keyboard import install as install_keyboard
            install_keyboard(app, window)
            print("[on-screen keyboard installed — kiosk mode]")
    except Exception as e:
        print(f"[Virtual keyboard skipped: {e}]")

    rc = app.exec()

    # Stop background engines, then exit hard. Daemon threads — Whisper STT,
    # edge-tts's asyncio loop, the camera monitor — crash the process if they
    # are left running into Python's interpreter shutdown. os._exit skips that
    # teardown entirely, so closing ARIA OS is always clean.
    try:
        if window._conversation is not None:
            window._conversation.shutdown()
    except Exception:
        pass
    try:
        if window._emotion_monitor is not None:
            window._emotion_monitor.shutdown()
    except Exception:
        pass
    try:
        if window._face_input is not None:
            window._face_input.shutdown()
    except Exception:
        pass
    try:
        from speech.tts_engine import stop_speaking
        stop_speaking()
    except Exception:
        pass
    os._exit(rc if isinstance(rc, int) else 0)


if __name__ == "__main__":
    main()
