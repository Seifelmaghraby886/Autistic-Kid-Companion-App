import unittest
from tests import _setup_path  # noqa

# Headless Qt for tests
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from core.tool_launcher import ToolLauncher


class TestToolLauncher(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tl = ToolLauncher()
        self.signals = {"calm":0, "aac":None, "schedule":0, "tutorial":None,
                        "story":None, "game":0, "parent_pin":0, "safety":None}
        self.tl.open_calm_zone.connect(lambda: self.signals.__setitem__("calm",
                                       self.signals["calm"]+1))
        self.tl.open_aac.connect(lambda c: self.signals.__setitem__("aac", c))
        self.tl.open_schedule.connect(lambda: self.signals.__setitem__("schedule",
                                       self.signals["schedule"]+1))
        self.tl.open_tutorial.connect(lambda k: self.signals.__setitem__("tutorial", k))
        self.tl.open_story.connect(lambda t: self.signals.__setitem__("story", t))
        self.tl.open_game.connect(lambda: self.signals.__setitem__("game",
                                       self.signals["game"]+1))
        self.tl.open_parent_pin.connect(lambda: self.signals.__setitem__("parent_pin",
                                       self.signals["parent_pin"]+1))
        self.tl.open_safety.connect(lambda p: self.signals.__setitem__("safety", p))

    def test_calm(self):
        self.tl.dispatch({"open_tool": "calm_zone", "intent": "sad"}, "أنا زعلان")
        self.assertEqual(self.signals["calm"], 1)

    def test_aac_food_category(self):
        self.tl.dispatch({"open_tool": "aac", "intent": "need_food"}, "أنا جعان")
        self.assertEqual(self.signals["aac"], "food")

    def test_schedule(self):
        self.tl.dispatch({"open_tool": "schedule", "intent": "open_schedule"}, "what now")
        self.assertEqual(self.signals["schedule"], 1)

    def test_tutorial_brush(self):
        self.tl.dispatch({"open_tool": "tutorial", "intent": "open_tutorial"},
                         "wash my teeth")
        self.assertEqual(self.signals["tutorial"], "brush_teeth")

    def test_story(self):
        self.tl.dispatch({"open_tool": "story", "intent": "open_story"}, "احكيلي قصة")
        self.assertEqual(self.signals["story"], "calm_night")

    def test_game(self):
        self.tl.dispatch({"open_tool": "game"}, "play")
        self.assertEqual(self.signals["game"], 1)

    def test_parent_pin(self):
        self.tl.dispatch({"open_tool": "parent_pin"}, "open parent mode")
        self.assertEqual(self.signals["parent_pin"], 1)

    def test_safety(self):
        self.tl.dispatch({"open_tool": "safety", "alert_type": "bullying"}, "ضربوني")
        self.assertIsNotNone(self.signals["safety"])
        self.assertEqual(self.signals["safety"]["alert_type"], "bullying")


if __name__ == "__main__":
    unittest.main()
