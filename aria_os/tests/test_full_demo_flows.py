"""End-to-end demo flows — pipe text through MockAI + ToolLauncher + DB,
verify the expected screen would open and DB was updated."""

import unittest
import os
from tests import _setup_path  # noqa
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from core.mock_ai import MockAIProvider
from core.tool_launcher import ToolLauncher
from data import database as db


class TestFullDemoFlows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.ai = MockAIProvider()
        cls.cid = db.get_or_create_default_child()
        # Reset child language to Arabic for the Arabic demos
        c = db._conn()
        c.execute("UPDATE children SET language='ar' WHERE id=?", (cls.cid,))
        c.commit(); c.close()

    def setUp(self):
        self.opened = {"calm":0,"aac":None,"schedule":0,"tutorial":None,
                       "story":None,"game":0,"parent_pin":0,"safety":None}
        self.tl = ToolLauncher()
        self.tl.open_calm_zone.connect(lambda: self.opened.__setitem__("calm",
                                       self.opened["calm"]+1))
        self.tl.open_aac.connect(lambda c: self.opened.__setitem__("aac", c))
        self.tl.open_schedule.connect(lambda: self.opened.__setitem__("schedule",
                                       self.opened["schedule"]+1))
        self.tl.open_tutorial.connect(lambda k: self.opened.__setitem__("tutorial", k))
        self.tl.open_story.connect(lambda t: self.opened.__setitem__("story", t))
        self.tl.open_game.connect(lambda: self.opened.__setitem__("game",
                                       self.opened["game"]+1))
        self.tl.open_parent_pin.connect(lambda: self.opened.__setitem__("parent_pin",
                                       self.opened["parent_pin"]+1))
        self.tl.open_safety.connect(lambda p: self.opened.__setitem__("safety", p))

    def _flow(self, text):
        prof = db.get_child(self.cid)
        r = self.ai.generate_response(text, prof, {}, [])
        self.tl.dispatch(r, text)
        return r

    # Scenario 1
    def test_arabic_hunger_opens_aac_food(self):
        r = self._flow("أنا جعان")
        self.assertEqual(r["intent"], "need_food")
        self.assertEqual(self.opened["aac"], "food")

    # Scenario 1b (Franco)
    def test_franco_hunger_opens_aac_food(self):
        r = self._flow("ana ga3an")
        self.assertEqual(r["intent"], "need_food")
        self.assertEqual(self.opened["aac"], "food")

    # Scenario 2
    def test_sad_opens_calm_zone(self):
        r = self._flow("أنا زعلان ومش عايز أتكلم")
        self.assertEqual(r["intent"], "sad")
        self.assertEqual(self.opened["calm"], 1)
        self.assertEqual(r["robot_command"]["face"], "sad_soft")

    # Scenario 3
    def test_what_now_opens_schedule(self):
        r = self._flow("بعد كده ايه؟")
        self.assertEqual(r["intent"], "open_schedule")
        self.assertEqual(self.opened["schedule"], 1)

    # Scenario 4
    def test_bullying_creates_alert(self):
        r = self._flow("الولد ضربني في المدرسة")
        self.assertTrue(r["parent_alert"])
        self.assertEqual(r["alert_type"], "bullying")
        self.assertEqual(self.opened["calm"], 1)

    # Scenario 5
    def test_parent_mode_opens_pin(self):
        r = self._flow("open parent mode")
        self.assertEqual(r["intent"], "parent_mode")
        self.assertEqual(self.opened["parent_pin"], 1)

    # Scenario 6
    def test_brushing_opens_tutorial(self):
        r = self._flow("مش عارف اغسل سناني")
        self.assertEqual(self.opened["tutorial"], "brush_teeth")

    # Scenario 7
    def test_story_opens_story(self):
        r = self._flow("احكيلي قصة")
        self.assertEqual(r["intent"], "open_story")
        self.assertEqual(self.opened["story"], "calm_night")

    # Scenario 8
    def test_play_opens_games(self):
        r = self._flow("عايز ألعب")
        self.assertEqual(r["intent"], "open_game")
        self.assertEqual(self.opened["game"], 1)

    # Scenario 11 (self harm — critical safety)
    def test_self_harm_triggers_safety(self):
        r = self._flow("I want to hurt myself")
        self.assertTrue(r["parent_alert"])
        self.assertEqual(r["alert_type"], "self_harm")
        self.assertIsNotNone(self.opened["safety"])

    # English happy
    def test_english_unknown_falls_to_talk(self):
        prof = db.get_child(self.cid)
        c = db._conn(); c.execute("UPDATE children SET language='en' WHERE id=?", (self.cid,))
        c.commit(); c.close()
        try:
            r = self._flow("hi friend")
        finally:
            c = db._conn(); c.execute("UPDATE children SET language='ar' WHERE id=?", (self.cid,))
            c.commit(); c.close()
        self.assertIn(r["intent"], ("talk", "unknown"))


if __name__ == "__main__":
    unittest.main()
