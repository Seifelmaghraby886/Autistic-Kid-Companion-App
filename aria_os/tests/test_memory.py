import unittest
from tests import _setup_path  # noqa
from core.memory_engine import MemoryEngine
from data import database as db


class TestMemory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cid = db.get_or_create_default_child()
        cls.sid = db.start_session(cls.cid)

    def test_update_state(self):
        m = MemoryEngine(self.cid, self.sid)
        m.update_state(current_emotion="sad", stress_level="medium", last_topic="school")
        s = m.state()
        self.assertEqual(s["current_emotion"], "sad")
        self.assertEqual(s["stress_level"], "medium")

    def test_ai_memory_update(self):
        m = MemoryEngine(self.cid, self.sid)
        m.apply_ai_memory_update({"current_emotion": "happy", "current_need": "food"})
        s = m.state()
        self.assertEqual(s["current_emotion"], "happy")
        self.assertEqual(s["current_need"], "food")

    def test_log_turn(self):
        m = MemoryEngine(self.cid, self.sid)
        m.log_turn("child", "hello", intent="talk")
        h = m.session_history()
        self.assertTrue(any(t["text"] == "hello" for t in h))


if __name__ == "__main__":
    unittest.main()
