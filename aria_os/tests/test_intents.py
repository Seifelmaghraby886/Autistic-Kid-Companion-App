import unittest
from tests import _setup_path  # noqa
from core.intent_engine import detect_intent
from core.language_engine import normalize_franco


class TestIntents(unittest.TestCase):
    def _check(self, text, expected, msg=""):
        norm = normalize_franco(text)
        got = detect_intent(norm)
        self.assertEqual(got, expected, f"{msg or text} → got {got} expected {expected}")

    def test_food_arabic(self):
        self._check("أنا جعان", "need_food")

    def test_food_franco(self):
        self._check("ana ga3an", "need_food")

    def test_water(self):
        self._check("عايز اشرب مية", "need_water")

    def test_bathroom(self):
        self._check("عايز الحمام", "need_bathroom")

    def test_sad(self):
        self._check("أنا زعلان", "sad")

    def test_scared(self):
        self._check("أنا خايف", "scared")

    def test_angry(self):
        self._check("متضايق", "angry")

    def test_schedule_question(self):
        self._check("بعد كده ايه؟", "open_schedule")

    def test_brush_teeth(self):
        self._check("مش عارف اغسل سناني", "open_tutorial")

    def test_story(self):
        self._check("احكيلي قصة", "open_story")

    def test_game(self):
        self._check("عايز ألعب", "open_game")

    def test_parent_mode(self):
        self._check("Open parent mode", "parent_mode")

    def test_unknown(self):
        self._check("xkjsdf zzz", "unknown")


if __name__ == "__main__":
    unittest.main()
