import unittest
from tests import _setup_path  # noqa
from core.ai_provider import validate_json_response, fallback_response, VALID_INTENTS
from core.mock_ai import MockAIProvider


class TestAIShellValidation(unittest.TestCase):
    def test_validates_complete(self):
        r = validate_json_response({
            "reply": "Hi", "language": "english", "emotion": "happy",
            "emotion_confidence": 0.8, "intent": "talk", "open_tool": "none",
        })
        self.assertEqual(r["reply"], "Hi")
        self.assertEqual(r["emotion"], "happy")
        self.assertEqual(r["intent"], "talk")

    def test_rejects_invalid(self):
        r = validate_json_response("not json")
        self.assertEqual(r["intent"], "talk")  # fallback
        self.assertTrue(isinstance(r["reply"], str))

    def test_mock_arabic_sad(self):
        r = MockAIProvider().generate_response("أنا زعلان", {"language": "ar", "name": "Mazy"}, {}, [])
        self.assertEqual(r["intent"], "sad")
        self.assertEqual(r["open_tool"], "calm_zone")
        self.assertIn(r["intent"], VALID_INTENTS)

    def test_mock_food_franco(self):
        r = MockAIProvider().generate_response("ana ga3an", {"language": "ar", "name": "Mazy"}, {}, [])
        self.assertEqual(r["intent"], "need_food")
        self.assertEqual(r["open_tool"], "aac")

    def test_mock_schedule(self):
        r = MockAIProvider().generate_response("بعد كده ايه؟", {"language": "ar"}, {}, [])
        self.assertEqual(r["intent"], "open_schedule")
        self.assertEqual(r["open_tool"], "schedule")

    def test_mock_brush(self):
        r = MockAIProvider().generate_response("مش عارف اغسل سناني", {"language": "ar"}, {}, [])
        self.assertEqual(r["open_tool"], "tutorial")

    def test_mock_story(self):
        r = MockAIProvider().generate_response("احكيلي قصة", {"language": "ar"}, {}, [])
        self.assertEqual(r["open_tool"], "story")

    def test_mock_game(self):
        r = MockAIProvider().generate_response("عايز ألعب", {"language": "ar"}, {}, [])
        self.assertEqual(r["open_tool"], "game")

    def test_mock_parent_mode(self):
        r = MockAIProvider().generate_response("open parent mode", {"language": "en"}, {}, [])
        self.assertEqual(r["open_tool"], "parent_pin")

    def test_mock_bullying_alerts(self):
        r = MockAIProvider().generate_response("الولد ضربني في المدرسة", {"language": "ar"}, {}, [])
        self.assertTrue(r["parent_alert"])
        self.assertEqual(r["alert_type"], "bullying")
        self.assertEqual(r["open_tool"], "calm_zone")


if __name__ == "__main__":
    unittest.main()
