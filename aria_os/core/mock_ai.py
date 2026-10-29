"""MockAIProvider — offline-first. Pattern-matches input to all demo scenarios."""

import re
from core.ai_provider import AIProvider, validate_json_response, fallback_response
from core.intent_engine import detect_intent
from core.language_engine import normalize_franco, detect_language
from core.emotion_engine import quick_emotion
from core.safety_engine import classify_safety


def _reply_for(intent, lang, name):
    name = name or ""
    yh = (" يا " + name) if (name and lang == "ar") else ""
    R = {
        "ar": {
            "need_food":     f"تمام{yh}، تحب أقول لماما إنك جعان؟",
            "need_water":    f"تمام{yh}، تحب اشرب مية؟",
            "need_bathroom": f"ماشي{yh}، نروح الحمام بهدوء.",
            "need_parent":   f"أنا هاناديلك ماما دلوقتي.",
            "pain":          f"أنا فاهماك{yh}. هاقولّ لماما تشوفك.",
            "sad":           f"تمام{yh}، أنا معاك. نفتح الوضع الهادي؟",
            "angry":         f"عادي تتضايق{yh}. نهدى سوا؟",
            "scared":        f"إنت في أمان معايا{yh}. ناخد نفس صغير سوا؟",
            "overstimulated":f"خلينا نفتح الوضع الهادي{yh}.",
            "open_calm_zone":f"تمام{yh}، هافتحلك الوضع الهادي.",
            "open_aac":      f"هافتحلك لوحة الصور{yh}.",
            "open_schedule": f"دي الجدول{yh}.",
            "open_tutorial": f"خلينا نعمل الخطوات سوا{yh}.",
            "open_story":    f"تمام{yh}، هاحكيلك قصة هادية.",
            "open_game":     f"يلا نلعب{yh}!",
            "parent_mode":   "وضع الأهل. محتاجين الرقم السري.",
            "emergency":     "أنا معاك. هاناديلك حد كبير دلوقتي.",
            "unknown":       f"أنا معاك{yh}. تحب نعمل ايه؟",
            "talk":          f"أنا سامعاك{yh}.",
        },
        "en": {
            "need_food":     "Okay sweetie, want me to tell mom you're hungry?",
            "need_water":    "Okay, would you like some water?",
            "need_bathroom": "Sure, let's calmly go to the bathroom.",
            "need_parent":   "I'll call mom for you right now.",
            "pain":          "I hear you. I'll tell mom to check on you.",
            "sad":           "I'm here with you. Want to open the calm zone?",
            "angry":         "It's okay to feel upset. Want to calm down together?",
            "scared":        "You're safe with me. Want to take a small breath together?",
            "overstimulated":"Let's open the quiet mode.",
            "open_calm_zone":"Sure, opening the calm zone.",
            "open_aac":      "Opening your picture board.",
            "open_schedule": "Here's your schedule.",
            "open_tutorial": "Let's do the steps together.",
            "open_story":    "Sure, I'll tell you a gentle story.",
            "open_game":     "Yay, let's play!",
            "parent_mode":   "Parent mode. I need the PIN.",
            "emergency":     "I'm with you. I'll call a trusted adult right now.",
            "unknown":       "I'm here. What would you like to do?",
            "talk":          "I'm listening.",
        },
        "de": {
            "need_food":     "Okay, soll ich Mama sagen, dass du hungrig bist?",
            "need_water":    "Okay, möchtest du Wasser trinken?",
            "need_bathroom": "Klar, gehen wir ruhig zur Toilette.",
            "need_parent":   "Ich rufe Mama für dich.",
            "pain":          "Ich verstehe dich. Ich sag Mama Bescheid.",
            "sad":           "Ich bin bei dir. Sollen wir die Ruhezone öffnen?",
            "angry":         "Es ist okay, wütend zu sein. Atmen wir zusammen?",
            "scared":        "Du bist sicher bei mir. Atmen wir kurz zusammen?",
            "overstimulated":"Lass uns den Ruhe-Modus öffnen.",
            "open_calm_zone":"Klar, ich öffne die Ruhezone.",
            "open_aac":      "Ich öffne dein Bildbrett.",
            "open_schedule": "Hier ist dein Tagesplan.",
            "open_tutorial": "Machen wir die Schritte zusammen.",
            "open_story":    "Ich erzähle dir eine ruhige Geschichte.",
            "open_game":     "Lass uns spielen!",
            "parent_mode":   "Eltern-Modus. Ich brauche die PIN.",
            "emergency":     "Ich bin bei dir. Ich rufe einen Erwachsenen.",
            "unknown":       "Ich bin hier. Was möchtest du machen?",
            "talk":          "Ich höre zu.",
        },
    }
    return R.get(lang, R["en"]).get(intent, R.get(lang, R["en"])["talk"])


INTENT_TO_TOOL = {
    "need_food": "aac", "need_water": "aac", "need_bathroom": "aac",
    "need_parent": "safety", "pain": "safety",
    "sad": "calm_zone", "angry": "calm_zone", "scared": "calm_zone",
    "overstimulated": "calm_zone",
    "open_calm_zone": "calm_zone", "open_aac": "aac",
    "open_schedule": "schedule", "open_tutorial": "tutorial",
    "open_story": "story", "open_game": "game",
    "parent_mode": "parent_pin", "emergency": "safety",
    "talk": "none", "unknown": "none",
}

INTENT_TO_EMOTION = {
    "sad": "sad", "angry": "angry", "scared": "scared",
    "pain": "sad", "overstimulated": "scared",
    "open_game": "happy", "open_story": "calm",
}


def _robot_for(intent):
    base = {"face": "calm", "voice": "soft", "led": "calm_blue",
            "movement": "stay_still", "mode": "idle"}
    if intent in ("sad", "scared", "open_calm_zone", "overstimulated"):
        base.update({"face": "sad_soft", "voice": "comfort", "led": "calm_blue", "mode": "comfort"})
    elif intent == "angry":
        base.update({"face": "neutral", "voice": "comfort", "led": "warm_amber", "mode": "comfort"})
    elif intent in ("open_game",):
        base.update({"face": "happy", "voice": "cheerful", "led": "cheerful_teal", "mode": "play"})
    elif intent == "emergency":
        base.update({"face": "concern", "voice": "soft", "led": "alert_pulse", "mode": "alert"})
    return base


class MockAIProvider(AIProvider):
    """Pure-Python rule-based AI. Works offline, supports all demo scenarios."""
    name = "MockAI"
    available = True

    def generate_response(self, child_input, child_profile=None, child_state=None,
                          session_history=None):
        try:
            text = child_input or ""
            text_norm = normalize_franco(text)
            lang = (child_profile or {}).get("language") or detect_language(text_norm)
            name = (child_profile or {}).get("name", "")

            # Safety check first
            safety = classify_safety(text_norm)
            if safety["category"] in ("SELF_HARM","ABUSE_RISK","MEDICAL_EMERGENCY"):
                return validate_json_response({
                    "reply": safety["safe_reply"],
                    "language": {"en":"english","ar":"egyptian_arabic","de":"german"}.get(lang,"english"),
                    "emotion": "scared", "emotion_confidence": 0.85,
                    "need": "parent", "intent": "emergency",
                    "open_tool": "safety", "parent_alert": True,
                    "alert_type": safety["category"].lower(),
                    "robot_command": _robot_for("emergency"),
                    "voice_style": "soft", "listening_after_reply": False,
                    "memory_update": {"current_emotion":"scared","stress_level":"high",
                                      "last_topic": safety["category"].lower()},
                    "log_summary": f"safety:{safety['category']}",
                }, lang)

            if safety["category"] == "BULLYING":
                return validate_json_response({
                    "reply": _reply_for("scared", lang, name),
                    "language": {"en":"english","ar":"egyptian_arabic","de":"german"}.get(lang,"english"),
                    "emotion": "scared", "emotion_confidence": 0.75,
                    "intent": "scared", "open_tool": "calm_zone",
                    "parent_alert": True, "alert_type": "bullying",
                    "robot_command": _robot_for("sad"),
                    "voice_style": "soft", "listening_after_reply": True,
                    "memory_update": {"current_emotion":"scared","stress_level":"high",
                                      "last_topic":"bullying"},
                    "log_summary": "bullying_reported",
                }, lang)

            # Intent detection
            intent = detect_intent(text_norm)
            tool = INTENT_TO_TOOL.get(intent, "none")
            emotion = INTENT_TO_EMOTION.get(intent, quick_emotion(text_norm))
            need = {"need_food":"food","need_water":"water","need_bathroom":"bathroom",
                    "need_parent":"parent","pain":"pain"}.get(intent)

            return validate_json_response({
                "reply": _reply_for(intent, lang, name),
                "language": {"en":"english","ar":"egyptian_arabic","de":"german"}.get(lang,"english"),
                "emotion": emotion, "emotion_confidence": 0.65,
                "need": need, "intent": intent, "open_tool": tool,
                "parent_alert": intent in ("emergency","need_parent","pain"),
                "alert_type": "distress" if intent in ("sad","scared","angry") else None,
                "robot_command": _robot_for(intent),
                "voice_style": "soft" if intent in ("sad","scared","overstimulated") else "neutral",
                "listening_after_reply": True,
                "memory_update": {
                    "current_emotion": emotion,
                    "current_need": need,
                    "stress_level": "medium" if intent in ("sad","angry","scared") else "low",
                    "last_topic": intent,
                },
                "log_summary": f"intent:{intent} tool:{tool}",
            }, lang)
        except Exception as e:
            r = fallback_response((child_profile or {}).get("language","en"))
            r["log_summary"] = f"mock_error:{e}"
            return r
