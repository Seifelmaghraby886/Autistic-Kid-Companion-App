"""Capture screenshots of every ARIA screen for the presentation."""
import sys, os, time
sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pygame
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtGui import QImage

import database.db_manager as db

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
os.makedirs(OUT, exist_ok=True)

cid = db.get_all_children()[0]['child_id']
pid = db.get_all_parents()[0]['parent_id']

app = QApplication(sys.argv)

def shot(widget, name):
    widget.resize(1400, 850)
    widget.show()
    app.processEvents()
    time.sleep(0.5)
    app.processEvents()
    pix = widget.grab()
    pix.save(os.path.join(OUT, f"{name}.png"))
    print(f"  saved {name}.png")
    widget.hide()

from ui.dashboard import DashboardScreen
from ui.talk_screen import TalkScreen
from ui.live_camera import LiveCameraScreen
from ui.calm_zone import CalmZoneScreen
from ui.sensory_toolkit import SensoryToolkitScreen
from ui.mood_journal import MoodJournalScreen
from ui.feelings_thermometer import FeelingsThermometerScreen
from ui.aac_builder import AACBuilderScreen
from ui.visual_timer import VisualTimerScreen
from ui.transition_helper import TransitionHelperScreen
from ui.games import GamesScreen
from ui.task_tutorials import TaskTutorialsScreen
from ui.music_player import MusicPlayerScreen
from ui.story_generator import StoryGeneratorScreen
from ui.bedtime_story import BedtimeStoryScreen
from ui.ai_coach import AICoachScreen
from ui.ai_insights import AIInsightsScreen
from ui.social_coach import SocialCoachScreen
from ui.reward_system import RewardSystemScreen
from ui.parent_dashboard import ParentDashboardScreen
from ui.settings import SettingsScreen
from ui.visual_schedule import VisualScheduleScreen
from ui.communication_board import CommunicationBoardScreen

shots = [
    (DashboardScreen, (cid,), 'dashboard'),
    (TalkScreen, (cid,), 'talk'),
    (LiveCameraScreen, (cid,), 'camera'),
    (CalmZoneScreen, (cid,), 'calm'),
    (SensoryToolkitScreen, (cid,), 'sensory'),
    (MoodJournalScreen, (cid,), 'journal'),
    (FeelingsThermometerScreen, (cid,), 'thermometer'),
    (AACBuilderScreen, (cid,), 'aac'),
    (VisualTimerScreen, (cid,), 'timer'),
    (TransitionHelperScreen, (cid,), 'transition'),
    (GamesScreen, (cid,), 'games'),
    (TaskTutorialsScreen, (cid,), 'tutorials'),
    (MusicPlayerScreen, (cid,), 'music'),
    (StoryGeneratorScreen, (cid,), 'story'),
    (BedtimeStoryScreen, (cid,), 'bedtime'),
    (AICoachScreen, (cid,), 'coach'),
    (SocialCoachScreen, (cid,), 'social'),
    (RewardSystemScreen, (cid,), 'rewards'),
    (SettingsScreen, (cid, pid), 'settings'),
    (VisualScheduleScreen, (cid,), 'schedule'),
    (CommunicationBoardScreen, (cid,), 'comms'),
]

for cls, args, name in shots:
    try:
        w = cls(*args)
        shot(w, name)
        w.deleteLater()
    except Exception as e:
        print(f"  FAIL {name}: {e}")

print(f"\nTotal: saved to {OUT}")
