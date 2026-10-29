"""QA: construct every navigable screen offscreen against the real DB.

Mirrors the exact constructor calls in main.py's _show_* factories.
LiveCamera / Biometric may briefly open the webcam; each screen is
destroyed immediately after construction.

Run: py -3.11 scripts/qa_screen_construction.py
"""
from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

app = QApplication.instance() or QApplication([])

import database.db_manager as db  # noqa: E402

CHILD_ID = db.get_setting("active_child_id") or 3
PARENT_ID = db.get_setting("active_parent_id") or 1


def build_specs():
    """(name, factory) — one per nav route, mirroring main.py."""
    def spec(name):
        def deco(fn):
            return (name, fn)
        return deco

    specs = []

    def add(name, fn):
        specs.append((name, fn))

    add("talk",        lambda: __import__("ui.talk_screen", fromlist=["x"]).TalkScreen(CHILD_ID))
    add("camera",      lambda: __import__("ui.live_camera", fromlist=["x"]).LiveCameraScreen(CHILD_ID))
    add("photo",       lambda: __import__("ui.photo_emotion_test", fromlist=["x"]).PhotoEmotionTestScreen(CHILD_ID))
    add("games",       lambda: __import__("ui.games", fromlist=["x"]).GamesScreen(CHILD_ID))
    add("calm",        lambda: __import__("ui.calm_zone", fromlist=["x"]).CalmZoneScreen(CHILD_ID, auto_start=False))
    add("schedule",    lambda: __import__("ui.visual_schedule", fromlist=["x"]).VisualScheduleScreen(CHILD_ID))
    add("comms",       lambda: __import__("ui.communication_board", fromlist=["x"]).CommunicationBoardScreen(CHILD_ID))
    add("parent",      lambda: __import__("ui.parent_dashboard", fromlist=["x"]).ParentDashboardScreen(CHILD_ID, PARENT_ID))
    add("settings",    lambda: __import__("ui.settings", fromlist=["x"]).SettingsScreen(CHILD_ID, PARENT_ID))
    add("providers",   lambda: __import__("ui.provider_center", fromlist=["x"]).ProviderCenterScreen(CHILD_ID))
    add("sensory",     lambda: __import__("ui.sensory_toolkit", fromlist=["x"]).SensoryToolkitScreen(CHILD_ID))
    add("journal",     lambda: __import__("ui.mood_journal", fromlist=["x"]).MoodJournalScreen(CHILD_ID))
    add("story",       lambda: __import__("ui.story_generator", fromlist=["x"]).StoryGeneratorScreen(CHILD_ID))
    add("rewards",     lambda: __import__("ui.reward_system", fromlist=["x"]).RewardSystemScreen(CHILD_ID))
    add("timer",       lambda: __import__("ui.visual_timer", fromlist=["x"]).VisualTimerScreen(CHILD_ID))
    add("aac",         lambda: __import__("ui.aac_builder", fromlist=["x"]).AACBuilderScreen(CHILD_ID))
    add("transition",  lambda: __import__("ui.transition_helper", fromlist=["x"]).TransitionHelperScreen(CHILD_ID))
    add("coach",       lambda: __import__("ui.ai_coach", fromlist=["x"]).AICoachScreen(CHILD_ID))
    add("bedtime",     lambda: __import__("ui.bedtime_story", fromlist=["x"]).BedtimeStoryScreen(CHILD_ID))
    add("insights",    lambda: __import__("ui.ai_insights", fromlist=["x"]).AIInsightsScreen(CHILD_ID))
    add("music",       lambda: __import__("ui.music_player", fromlist=["x"]).MusicPlayerScreen(CHILD_ID))
    add("tutorials",   lambda: __import__("ui.task_tutorials", fromlist=["x"]).TaskTutorialsScreen(CHILD_ID))
    add("thermometer", lambda: __import__("ui.feelings_thermometer", fromlist=["x"]).FeelingsThermometerScreen(CHILD_ID))
    add("social",      lambda: __import__("ui.social_coach", fromlist=["x"]).SocialCoachScreen(CHILD_ID))
    add("biometric",   lambda: __import__("ui.biometric_screen", fromlist=["x"]).BiometricScreen(CHILD_ID))
    add("dashboard",   lambda: __import__("ui.dashboard", fromlist=["x"]).DashboardScreen(CHILD_ID))
    add("firstthen",   lambda: __import__("ui.first_then", fromlist=["x"]).FirstThenScreen(CHILD_ID))
    return specs


def main() -> int:
    failures = []
    for name, factory in build_specs():
        try:
            w = factory()
            # tear down promptly (releases camera/threads if any grabbed)
            if hasattr(w, "cleanup"):
                try:
                    w.cleanup()
                except Exception:
                    pass
            w.deleteLater()
            app.processEvents()
            print(f"OK    {name}")
        except Exception:
            failures.append(name)
            print(f"FAIL  {name}")
            traceback.print_exc(limit=4)
    print(f"\n{len(build_specs()) - len(failures)}/{len(build_specs())} screens construct cleanly")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
