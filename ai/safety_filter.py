"""ARIA Safety Filters — Input and Output."""

import re

BLOCKED_PATTERNS = [
    r'\b(kill|hurt|abuse|weapon|die|suicide|harm)\b',
    r'\b(drug|alcohol|violence)\b',
]

DANGEROUS_TRIGGERS = ["kill", "hurt myself", "want to die", "abuse", "no one loves"]
PARENT_ALERT_TRIGGERS = ["scared of", "hits me", "doesn't want me", "hurts me", "abuse"]


class InputSafetyFilter:
    @staticmethod
    def clean(text: str) -> str:
        text = text.strip()
        text = re.sub(r'[<>{}|\\]', '', text)
        return text[:500]

    @staticmethod
    def is_blocked(text: str) -> bool:
        lower = text.lower()
        for trigger in DANGEROUS_TRIGGERS:
            if trigger in lower:
                return True
        return False


class OutputSafetyFilter:
    @staticmethod
    def check(result: dict, lang: str) -> dict:
        reply = result.get("reply", "")
        lower = reply.lower()

        if any(word in lower for word in ["diagnos", "disorder", "treatment", "medic"]):
            safe_replies = {
                "en": "I'm here with you. Let's talk about something you enjoy.",
                "ar": "أنا معاك. خلينا نتكلم في حاجة تحبها.",
                "de": "Ich bin bei dir. Lass uns über etwas sprechen, das du magst.",
            }
            result["reply"] = safe_replies.get(lang, safe_replies["en"])
            result["face_expression"] = "calm"

        for trigger in PARENT_ALERT_TRIGGERS:
            if trigger in lower:
                result["parent_alert"] = True
                result["comfort_mode"] = True
                break

        return result
