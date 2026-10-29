import unittest
from tests import _setup_path  # noqa
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from core.robot_bridge import RobotBridge
from data import database as db


class TestRobotBridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.cid = db.get_or_create_default_child()

    def test_send_logs_and_emits(self):
        rb = RobotBridge(self.cid)
        received = []
        rb.command_sent.connect(lambda d: received.append(d))
        cmd = {"face": "sad_soft", "voice": "comfort",
               "led": "calm_blue", "movement": "stay_still", "mode": "comfort"}
        rb.send(cmd)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["face"], "sad_soft")
        # DB log
        rows = db.recent_robot_commands(self.cid, 5)
        self.assertTrue(any("sad_soft" in r["command_json"] for r in rows))

    def test_empty_command_ignored(self):
        rb = RobotBridge(self.cid)
        received = []
        rb.command_sent.connect(lambda d: received.append(d))
        rb.send({})
        rb.send(None)
        self.assertEqual(len(received), 0)


if __name__ == "__main__":
    unittest.main()
