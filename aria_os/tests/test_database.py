import unittest
from tests import _setup_path  # noqa
from data import database as db


class TestDatabase(unittest.TestCase):
    def test_init_schema(self):
        # init_db is called at import; check tables exist by querying
        c = db._conn()
        names = {r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        c.close()
        for required in ["children","parents","sessions","messages","child_state",
                         "memories","emotion_logs","schedule_items","alerts","goals",
                         "app_settings","robot_commands","test_results"]:
            self.assertIn(required, names, f"Missing table: {required}")

    def test_create_child(self):
        cid = db.create_child("TestKid", age=6, language="en")
        self.assertTrue(cid >= 1)
        c = db.get_child(cid)
        self.assertEqual(c["name"], "TestKid")

    def test_log_message_roundtrip(self):
        cid = db.get_or_create_default_child()
        sid = db.start_session(cid)
        db.log_message(sid, "child", "hello", emotion="happy", intent="talk")
        msgs = db.session_messages(sid)
        self.assertTrue(any(m["text"] == "hello" for m in msgs))

    def test_settings_roundtrip(self):
        db.set_setting("auto_listening_enabled", True)
        self.assertEqual(db.get_setting("auto_listening_enabled"), True)

    def test_alerts(self):
        cid = db.get_or_create_default_child()
        db.add_alert(cid, "test_alert", "low", "test message")
        rows = db.list_alerts(cid, 5)
        self.assertTrue(any(a["type"] == "test_alert" for a in rows))


if __name__ == "__main__":
    unittest.main()
