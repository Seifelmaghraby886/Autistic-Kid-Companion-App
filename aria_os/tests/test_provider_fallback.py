import unittest
import os
from tests import _setup_path  # noqa

from core.claude_provider import ClaudeProvider
from core.mock_ai import MockAIProvider
from core.voice_provider import (
    Pyttsx3Provider, EdgeTTSProvider, ElevenLabsProvider, MockTTSProvider
)
from core.tts_engine import TTSEngine
from core.ai_provider import VALID_INTENTS


class TestProviderFallback(unittest.TestCase):
    def test_claude_without_key_is_unavailable(self):
        os.environ["ANTHROPIC_API_KEY"] = ""
        c = ClaudeProvider()
        s = c.status()
        self.assertFalse(s["available"])
        self.assertEqual(s.get("reason"), "missing_api_key")

    def test_claude_falls_back_to_mock(self):
        """When Claude has no key, generate_response delegates to MockAI."""
        os.environ["ANTHROPIC_API_KEY"] = ""
        c = ClaudeProvider()
        r = c.generate_response("أنا جعان", {"language": "ar", "name": "Mazy"}, {}, [])
        self.assertIn(r["intent"], VALID_INTENTS)
        self.assertEqual(r["intent"], "need_food")

    def test_elevenlabs_without_key_is_unavailable(self):
        os.environ["ELEVENLABS_API_KEY"] = ""
        v = ElevenLabsProvider()
        self.assertFalse(v.available)

    def test_tts_engine_picks_an_available_provider(self):
        eng = TTSEngine()
        self.assertTrue(eng.active is not None)
        # active provider must be available
        self.assertTrue(eng.active.available)

    def test_tts_engine_status_lists_chain(self):
        eng = TTSEngine()
        status = eng.status()
        names = {s["name"] for s in status}
        # At minimum MockTTS is always present
        self.assertIn("MockTTS", names)

    def test_tts_speak_does_not_crash_with_empty_text(self):
        eng = TTSEngine()
        try:
            eng.speak("", language="en")
            eng.speak(None, language="en")
            ok = True
        except Exception:
            ok = False
        self.assertTrue(ok)

    def test_mock_ai_always_returns_valid_schema(self):
        ai = MockAIProvider()
        for text in ["hi", "ana ga3an", "أنا زعلان", "بعد كده ايه", "garbage xx"]:
            r = ai.generate_response(text, {"language": "ar"}, {}, [])
            self.assertIn("reply", r)
            self.assertIn("intent", r)
            self.assertIn(r["intent"], VALID_INTENTS)
            self.assertIn("robot_command", r)


if __name__ == "__main__":
    unittest.main()
