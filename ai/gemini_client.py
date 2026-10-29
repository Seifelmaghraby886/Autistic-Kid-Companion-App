"""
ARIA Gemini AI Client
Structured AI responses with safety filtering and child profile adaptation.
"""

import json
import re
import os
from pathlib import Path

import database.db_manager as db
from ai.prompt_builder import build_system_prompt, build_user_message
from ai.safety_filter import InputSafetyFilter, OutputSafetyFilter
from ai.response_parser import parse_aria_response


OFFLINE_RESPONSES = {
    "en": {
        "reply": "I'm here with you. We can do a calm activity together.",
        "face_expression": "calm",
        "tts_style": "soft",
        "suggested_activity": "breathing",
        "comfort_mode": False,
        "parent_alert": False,
        "memory_update": "",
        "reason": "Offline fallback"
    },
    "ar": {
        "reply": "أنا موجودة معاك. نقدر نعمل نشاط هادي.",
        "face_expression": "calm",
        "tts_style": "very_slow",
        "suggested_activity": "breathing",
        "comfort_mode": False,
        "parent_alert": False,
        "memory_update": "",
        "reason": "Offline fallback"
    },
    "de": {
        "reply": "Ich bin bei dir. Wir können eine ruhige Aktivität machen.",
        "face_expression": "calm",
        "tts_style": "soft",
        "suggested_activity": "breathing",
        "comfort_mode": False,
        "parent_alert": False,
        "memory_update": "",
        "reason": "Offline fallback"
    },
}


def _load_api_key():
    try:
        cfg_path = Path(__file__).parent.parent / "config" / "app_config.json"
        with open(cfg_path) as f:
            cfg = json.load(f)
        return cfg.get("gemini_api_key", "").strip()
    except Exception:
        return ""


def get_aria_response(
    user_message: str,
    child_id: int,
    current_emotion: str = "neutral",
    current_mode: str = "home",
    current_activity: str = "none",
    chat_history: list = None,
) -> dict:
    """Route through multi-provider chain (Gemini → Groq → Claude → GPT)."""
    from ai.multi_provider import get_aria_response as _multi
    return _multi(user_message, child_id, current_emotion, current_mode,
                  current_activity, chat_history=chat_history)


def _legacy_get_aria_response(
    user_message: str,
    child_id: int,
    current_emotion: str = "neutral",
    current_mode: str = "home",
    current_activity: str = "none"
) -> dict:
    """Legacy single-provider path (Gemini only)."""

    # Load child context
    child = db.get_child(child_id) or {}
    prefs = db.get_child_preferences(child_id)
    memory = db.get_ai_memory(child_id)

    lang = child.get("language", "en")

    # Input safety filter
    safe_msg = InputSafetyFilter.clean(user_message)
    if InputSafetyFilter.is_blocked(safe_msg):
        return _safety_response(lang)

    api_key = _load_api_key()
    if not api_key:
        return OFFLINE_RESPONSES.get(lang, OFFLINE_RESPONSES["en"])

    # Load model name from config
    try:
        cfg_path = Path(__file__).parent.parent / "config" / "app_config.json"
        with open(cfg_path) as f:
            cfg = json.load(f)
        model_name = cfg.get("gemini_model", "gemini-2.5-flash")
    except Exception:
        model_name = "gemini-2.5-flash"

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)

        system_prompt = build_system_prompt(
            child=child,
            prefs=prefs,
            memory=memory,
            current_emotion=current_emotion,
            current_mode=current_mode,
            current_activity=current_activity,
        )

        user_msg = build_user_message(safe_msg, lang)

        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_prompt,
        )

        # Force JSON output via response_mime_type
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=512,
                candidate_count=1,
                response_mime_type="application/json",
            )
        except TypeError:
            generation_config = genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=512,
                candidate_count=1,
            )

        response = model.generate_content(
            user_msg,
            generation_config=generation_config,
        )

        try:
            raw_text = response.text.strip()
        except Exception as e:
            print(f"[Response.text failed: {e}, candidates: {response.candidates}]")
            raw_text = ""

        result = parse_aria_response(raw_text)
        # Debug
        if result.get("reason") == "parse_fallback":
            print(f"[Parse fallback hit. Raw response: {raw_text[:300]}]")

        # Output safety check
        result = OutputSafetyFilter.check(result, lang)

        return result

    except ImportError:
        return _no_library_response(lang)

    except Exception as e:
        err_str = str(e).lower()
        print(f"[ARIA AI Error] {e}")

        # Rate limit / quota
        if "quota" in err_str or "429" in err_str or "rate" in err_str:
            msgs = {
                "en": "The AI is taking a quick break (rate limit). Wait 30 seconds and try again. 💙",
                "ar": "الذكاء الاصطناعي بياخد راحة صغيرة. استنى 30 ثانية وحاول تاني. 💙",
                "de": "Die KI macht eine kurze Pause. Warte 30 Sekunden. 💙",
            }
            return {
                "reply": msgs.get(lang, msgs["en"]),
                "face_expression": "thinking",
                "tts_style": "soft",
                "suggested_activity": "breathing",
                "comfort_mode": False,
                "parent_alert": False,
                "memory_update": "",
                "reason": f"Rate limit: {str(e)[:200]}"
            }

        # Auth / API key
        if "api key" in err_str or "401" in err_str or "permission" in err_str or "auth" in err_str:
            msgs = {
                "en": "The AI key needs to be set up. Ask a parent to check Settings. 🔑",
                "ar": "محتاجين نظبط الكود. اطلب من الأهل يفتحوا الإعدادات. 🔑",
                "de": "Der KI-Schlüssel muss eingerichtet werden. Bitte einen Erwachsenen. 🔑",
            }
            return {
                "reply": msgs.get(lang, msgs["en"]),
                "face_expression": "thinking",
                "tts_style": "soft",
                "suggested_activity": "none",
                "comfort_mode": False,
                "parent_alert": False,
                "memory_update": "",
                "reason": f"Auth error: {str(e)[:200]}"
            }

        # Generic offline fallback
        return OFFLINE_RESPONSES.get(lang, OFFLINE_RESPONSES["en"])


def _safety_response(lang: str) -> dict:
    msgs = {
        "en": "I hear you. I'm here to keep you safe. Let's talk about something gentle.",
        "ar": "أنا سامعك. أنا هنا عشان أبقى معاك بأمان. خلينا نتكلم في حاجة هادية.",
        "de": "Ich höre dich. Ich bin hier, um dir zu helfen. Lass uns über etwas Ruhiges sprechen.",
    }
    return {
        "reply": msgs.get(lang, msgs["en"]),
        "face_expression": "calm",
        "tts_style": "soft",
        "suggested_activity": "breathing",
        "comfort_mode": True,
        "parent_alert": True,
        "memory_update": "",
        "reason": "Input safety filter triggered"
    }


def _no_library_response(lang: str) -> dict:
    return OFFLINE_RESPONSES.get(lang, OFFLINE_RESPONSES["en"])
