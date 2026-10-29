import unittest
from tests import _setup_path  # noqa
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from core.auto_listening_engine import AutoListeningEngine, State


class TestAutoListening(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_initial_state(self):
        e = AutoListeningEngine(speech_engine=None)
        self.assertEqual(e.get_state(), State.IDLE_STARTUP.value)

    def test_start_goes_to_greeting(self):
        e = AutoListeningEngine(speech_engine=None)
        e.start()
        self.assertEqual(e.get_state(), State.GREETING.value)

    def test_set_state_string(self):
        e = AutoListeningEngine(speech_engine=None)
        e.set_state("LISTENING")
        self.assertEqual(e.get_state(), State.LISTENING.value)

    def test_set_state_invalid_string_ignored(self):
        e = AutoListeningEngine(speech_engine=None)
        original = e.get_state()
        ok = e.set_state("BOGUS_STATE")
        self.assertFalse(ok)
        self.assertEqual(e.get_state(), original)

    def test_parent_mode_stops_speech(self):
        e = AutoListeningEngine(speech_engine=None)
        e.start()
        e.enter_parent_mode()
        self.assertEqual(e.get_state(), State.PARENT_MODE.value)

    def test_pause_for_speaking_transitions_to_speaking(self):
        e = AutoListeningEngine(speech_engine=None)
        e.pause_for_speaking()
        self.assertEqual(e.get_state(), State.SPEAKING.value)

    def test_state_changed_signal_emits(self):
        e = AutoListeningEngine(speech_engine=None)
        received = []
        e.state_changed.connect(lambda s: received.append(s))
        e.set_state(State.LISTENING)
        e.set_state(State.SPEAKING)
        self.assertEqual(received, ["LISTENING", "SPEAKING"])

    def test_stop_resets(self):
        e = AutoListeningEngine(speech_engine=None)
        e.start()
        e.stop()
        self.assertEqual(e.get_state(), State.IDLE_STARTUP.value)


if __name__ == "__main__":
    unittest.main()
