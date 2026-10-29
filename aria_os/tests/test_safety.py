import unittest
from tests import _setup_path  # noqa
from core.safety_engine import classify_safety


class TestSafety(unittest.TestCase):
    def test_normal(self):
        self.assertEqual(classify_safety("hi there")["category"], "NORMAL")

    def test_bullying(self):
        self.assertEqual(classify_safety("الولد ضربني في المدرسة")["category"], "BULLYING")

    def test_self_harm(self):
        r = classify_safety("I want to hurt myself")
        self.assertEqual(r["category"], "SELF_HARM")
        self.assertEqual(r["severity"], "critical")

    def test_abuse(self):
        r = classify_safety("لمسني حد بصورة وحشة")
        self.assertEqual(r["category"], "ABUSE_RISK")

    def test_medical(self):
        r = classify_safety("I can't breathe")
        self.assertEqual(r["category"], "MEDICAL_EMERGENCY")


if __name__ == "__main__":
    unittest.main()
