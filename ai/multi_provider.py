"""
ARIA Multi-Provider AI Client
Supports Gemini, Groq, Anthropic, OpenAI — automatic fallback chain.
"""

import json
import re
from pathlib import Path

import database.db_manager as db
from ai.prompt_builder import build_system_prompt
from ai.safety_filter import InputSafetyFilter, OutputSafetyFilter
from ai.response_parser import parse_aria_response
from core.provider_control import enabled_in


CFG_PATH = Path(__file__).parent.parent / "config" / "app_config.json"


def _load_config():
    try:
        with open(CFG_PATH, encoding="utf-8") as f:
            from core.secrets import merge_secrets
            return merge_secrets(json.load(f))
    except Exception:
        return {}


OFFLINE_RESPONSES = {
    "en": {"reply": "I'm here with you. Let's do something calm together.",
           "face_expression": "calm", "tts_style": "soft",
           "suggested_activity": "breathing", "comfort_mode": False,
           "parent_alert": False, "memory_update": "", "reason": "offline"},
    "ar": {"reply": "أنا معاك. خلينا نعمل حاجة هادية سوا.",
           "face_expression": "calm", "tts_style": "very_slow",
           "suggested_activity": "breathing", "comfort_mode": False,
           "parent_alert": False, "memory_update": "", "reason": "offline"},
    "de": {"reply": "Ich bin bei dir. Lass uns etwas Ruhiges machen.",
           "face_expression": "calm", "tts_style": "soft",
           "suggested_activity": "breathing", "comfort_mode": False,
           "parent_alert": False, "memory_update": "", "reason": "offline"},
}


def get_aria_response(user_message, child_id, current_emotion="neutral",
                     current_mode="home", current_activity="none",
                     chat_history=None):
    """Main entry: routes to active provider, falls back through chain."""
    child = db.get_child(child_id) or {}
    prefs = db.get_child_preferences(child_id)
    memory = db.get_ai_memory(child_id)
    lang = child.get("language", "en")

    # Safety
    safe_msg = InputSafetyFilter.clean(user_message)
    if InputSafetyFilter.is_blocked(safe_msg):
        return _safety_response(lang)

    cfg = _load_config()
    provider = cfg.get("ai_provider", "gemini").lower()
    system_prompt = build_system_prompt(child, prefs, memory,
                                        current_emotion, current_mode, current_activity)

    # Cache check first (avoids API call entirely for common phrases)
    cached = _check_response_cache(safe_msg, lang)
    if cached:
        return cached

    # Provider chain — try active first, then fall back through free providers
    chain_priority = {
        "gemini":    [_call_gemini,    _call_groq,     _call_cerebras, _call_openrouter, _call_anthropic, _call_openai, _call_ollama],
        "groq":      [_call_groq,      _call_cerebras, _call_gemini,   _call_openrouter, _call_anthropic, _call_openai, _call_ollama],
        "cerebras":  [_call_cerebras,  _call_groq,     _call_gemini,   _call_openrouter, _call_anthropic, _call_openai, _call_ollama],
        "openrouter":[_call_openrouter,_call_groq,     _call_cerebras, _call_gemini,     _call_anthropic, _call_openai, _call_ollama],
        "anthropic": [_call_anthropic, _call_groq,     _call_cerebras, _call_gemini,     _call_openrouter, _call_openai, _call_ollama],
        "openai":    [_call_openai,    _call_groq,     _call_cerebras, _call_gemini,     _call_openrouter, _call_anthropic, _call_ollama],
        "ollama":    [_call_ollama,    _call_groq,     _call_cerebras, _call_gemini,     _call_openrouter, _call_anthropic, _call_openai],
    }
    chain = chain_priority.get(provider, chain_priority["groq"])

    last_error = None
    for fn in chain:
        try:
            result = fn(safe_msg, system_prompt, cfg, lang, chat_history)
            if result:
                result = OutputSafetyFilter.check(result, lang)
                # Polish to Egyptian if Arabic
                if lang == "ar":
                    try:
                        from ai.egyptian_polish import polish_to_egyptian
                        result["reply"] = polish_to_egyptian(result.get("reply", ""))
                    except Exception:
                        pass
                cache_response(safe_msg, lang, result)
                return result
        except RateLimitError as e:
            last_error = e
            print(f"[{fn.__name__} rate-limited, falling back...]")
            continue
        except Exception as e:
            last_error = e
            print(f"[{fn.__name__} failed: {e}]")
            continue

    # Save successful results to cache later (we add this when we have a result)

    # Everything failed — informative offline
    if last_error and "quota" in str(last_error).lower():
        msgs = {
            "en": "All AIs are taking a quick break. Try again in 30 seconds. 💙",
            "ar": "كل الذكاءات الاصطناعية بتاخد راحة. حاول تاني بعد 30 ثانية. 💙",
            "de": "Alle KIs machen eine Pause. Versuche es in 30 Sekunden. 💙",
        }
        fb = OFFLINE_RESPONSES.get(lang, OFFLINE_RESPONSES["en"]).copy()
        fb["reply"] = msgs.get(lang, msgs["en"])
        return fb

    return OFFLINE_RESPONSES.get(lang, OFFLINE_RESPONSES["en"])


class RateLimitError(Exception):
    pass


# ─── Gemini (with multi-key rotation) ──────────────────────────────────
def _call_gemini(user_msg, system_prompt, cfg, lang, chat_history=None):
    if not enabled_in(cfg, "ai_gemini"):
        return None
    api_key = _get_rotating_gemini_key(cfg)
    if not api_key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name=cfg.get("gemini_model", "gemini-2.5-flash"),
            system_instruction=system_prompt,
        )

        # Build history for Gemini
        if chat_history:
            history = []
            for h in chat_history:
                role = "user" if h["role"] == "user" else "model"
                history.append({"role": role, "parts": [h["content"]]})
            chat = model.start_chat(history=history)
        else:
            chat = None
        try:
            gc = genai.types.GenerationConfig(
                temperature=0.7, max_output_tokens=1024,
                response_mime_type="application/json",
            )
        except TypeError:
            gc = genai.types.GenerationConfig(temperature=0.7, max_output_tokens=1024)
        if chat:
            r = chat.send_message(user_msg, generation_config=gc)
        else:
            r = model.generate_content(user_msg, generation_config=gc)
        return parse_aria_response(r.text.strip())
    except Exception as e:
        if "quota" in str(e).lower() or "429" in str(e) or "rate" in str(e).lower():
            raise RateLimitError(str(e))
        raise


# ─── Groq (Llama-3.3-70B) — FREE, FAST ─────────────────────────────────
def _call_groq(user_msg, system_prompt, cfg, lang, chat_history=None):
    if not enabled_in(cfg, "ai_groq"):
        return None
    api_key = cfg.get("groq_api_key", "").strip()
    if not api_key:
        return None
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        msgs = [{"role": "system", "content": system_prompt}]
        if chat_history:
            msgs.extend(chat_history)
        msgs.append({"role": "user", "content": user_msg})
        response = client.chat.completions.create(
            model=cfg.get("groq_model", "llama-3.3-70b-versatile"),
            messages=msgs,
            temperature=0.7,
            max_tokens=1024,
            response_format={"type": "json_object"},
        )
        return parse_aria_response(response.choices[0].message.content.strip())
    except Exception as e:
        if "rate" in str(e).lower() or "quota" in str(e).lower() or "429" in str(e):
            raise RateLimitError(str(e))
        raise


# ─── Anthropic Claude ──────────────────────────────────────────────────
def _call_anthropic(user_msg, system_prompt, cfg, lang, chat_history=None):
    if not enabled_in(cfg, "ai_anthropic"):
        return None
    api_key = cfg.get("anthropic_api_key", "").strip()
    if not api_key:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        # Append JSON instruction
        prompt_full = system_prompt + "\n\nIMPORTANT: Output ONLY the JSON object, nothing else."
        msgs = list(chat_history) if chat_history else []
        msgs.append({"role": "user", "content": user_msg})
        response = client.messages.create(
            model=cfg.get("anthropic_model", "claude-3-5-haiku-20241022"),
            max_tokens=1024,
            system=prompt_full,
            messages=msgs,
        )
        text = response.content[0].text if response.content else ""
        return parse_aria_response(text.strip())
    except Exception as e:
        if "rate" in str(e).lower() or "429" in str(e):
            raise RateLimitError(str(e))
        raise


# ─── OpenAI GPT ───────────────────────────────────────────────────────
def _call_openai(user_msg, system_prompt, cfg, lang, chat_history=None):
    if not enabled_in(cfg, "ai_openai"):
        return None
    api_key = cfg.get("openai_api_key", "").strip()
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        msgs = [{"role": "system", "content": system_prompt}]
        if chat_history:
            msgs.extend(chat_history)
        msgs.append({"role": "user", "content": user_msg})
        response = client.chat.completions.create(
            model=cfg.get("openai_model", "gpt-4o-mini"),
            messages=msgs,
            temperature=0.7,
            max_tokens=1024,
            response_format={"type": "json_object"},
        )
        return parse_aria_response(response.choices[0].message.content.strip())
    except Exception as e:
        if "rate" in str(e).lower() or "429" in str(e):
            raise RateLimitError(str(e))
        raise


# ─── Cerebras (FREE — 8,000 req/day) ──────────────────────────────────
def _call_cerebras(user_msg, system_prompt, cfg, lang, chat_history=None):
    if not enabled_in(cfg, "ai_cerebras"):
        return None
    api_key = cfg.get("cerebras_api_key", "").strip()
    if not api_key:
        return None
    try:
        import requests
        msgs = [{"role": "system", "content": system_prompt}]
        if chat_history:
            msgs.extend(chat_history)
        msgs.append({"role": "user", "content": user_msg})
        response = requests.post(
            "https://api.cerebras.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": cfg.get("cerebras_model", "llama-3.3-70b"),
                "messages": msgs,
                "temperature": 0.7,
                "max_tokens": 1024,
                "response_format": {"type": "json_object"},
            },
            timeout=30,
        )
        if response.status_code == 429:
            raise RateLimitError("Cerebras rate limit")
        response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"]
        return parse_aria_response(text)
    except RateLimitError:
        raise
    except Exception as e:
        if "rate" in str(e).lower() or "429" in str(e) or "quota" in str(e).lower():
            raise RateLimitError(str(e))
        raise


# ─── OpenRouter (free models available) ────────────────────────────────
def _call_openrouter(user_msg, system_prompt, cfg, lang, chat_history=None):
    if not enabled_in(cfg, "ai_openrouter"):
        return None
    api_key = cfg.get("openrouter_api_key", "").strip()
    if not api_key:
        return None
    try:
        import requests
        model = cfg.get("openrouter_model", "meta-llama/llama-3.3-70b-instruct:free")
        msgs = [{"role": "system", "content": system_prompt}]
        if chat_history:
            msgs.extend(chat_history)
        msgs.append({"role": "user", "content": user_msg})
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://aria-companion.local",
                "X-Title": "ARIA Autism Companion",
            },
            json={
                "model": model,
                "messages": msgs,
                "temperature": 0.7,
                "max_tokens": 1024,
            },
            timeout=30,
        )
        if response.status_code == 429:
            raise RateLimitError("OpenRouter rate limit")
        response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"]
        return parse_aria_response(text)
    except RateLimitError:
        raise
    except Exception as e:
        if "rate" in str(e).lower() or "429" in str(e):
            raise RateLimitError(str(e))
        raise


# ─── Ollama (LOCAL — INFINITE, FREE, OFFLINE) ──────────────────────────
def _call_ollama(user_msg, system_prompt, cfg, lang, chat_history=None):
    """Calls local Ollama server. User must run `ollama serve` and pull a model."""
    if not enabled_in(cfg, "ai_ollama"):
        return None
    enabled = cfg.get("ollama_enabled", False)
    if not enabled:
        return None
    try:
        import requests
        url = cfg.get("ollama_url", "http://localhost:11434")
        model = cfg.get("ollama_model", "llama3.2:3b")
        msgs = [{"role": "system", "content": system_prompt}]
        if chat_history:
            msgs.extend(chat_history)
        msgs.append({"role": "user", "content": user_msg})
        response = requests.post(
            f"{url}/api/chat",
            json={
                "model": model,
                "messages": msgs,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.7, "num_predict": 1024},
            },
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        text = data["message"]["content"]
        return parse_aria_response(text)
    except Exception as e:
        if "rate" in str(e).lower():
            raise RateLimitError(str(e))
        raise


# ─── Multi-key rotation for Gemini ─────────────────────────────────────
_gemini_key_index = 0


def _get_rotating_gemini_key(cfg):
    """Rotate through multiple Gemini keys to multiply free quota."""
    global _gemini_key_index
    keys = []
    primary = cfg.get("gemini_api_key", "").strip()
    if primary:
        keys.append(primary)
    extras = cfg.get("gemini_extra_keys", [])
    if isinstance(extras, list):
        keys.extend(k.strip() for k in extras if k.strip())
    if not keys:
        return ""
    key = keys[_gemini_key_index % len(keys)]
    _gemini_key_index += 1
    return key


# ─── Response cache (for common phrases) ───────────────────────────────
_response_cache = {}
_CACHE_MAX = 100


def _check_response_cache(message, lang):
    """Return cached response for common greetings/casual phrases."""
    msg_lower = message.lower().strip()
    # Only cache ultra-common phrases (don't cache personal stuff)
    cacheable = {
        "hi": "greeting", "hello": "greeting", "hey": "greeting",
        "أهلا": "greeting", "اهلا": "greeting", "السلام عليكم": "greeting",
        "hallo": "greeting", "guten tag": "greeting",
        "thank you": "thanks", "thanks": "thanks", "شكرا": "thanks", "danke": "thanks",
        "goodbye": "goodbye", "bye": "goodbye", "مع السلامة": "goodbye", "tschüss": "goodbye",
    }
    cat = cacheable.get(msg_lower)
    if cat and (msg_lower, lang) in _response_cache:
        return _response_cache[(msg_lower, lang)]
    return None


def cache_response(message, lang, response):
    """Save common response to memory cache."""
    msg_lower = message.lower().strip()
    cacheable_keys = {
        "hi", "hello", "hey", "أهلا", "اهلا", "السلام عليكم",
        "hallo", "guten tag", "thank you", "thanks", "شكرا", "danke",
        "goodbye", "bye", "مع السلامة", "tschüss",
    }
    if msg_lower in cacheable_keys and len(_response_cache) < _CACHE_MAX:
        _response_cache[(msg_lower, lang)] = response


def generate_text(prompt: str, system: str = "", json_mode: bool = False,
                  max_tokens: int = 1024) -> str:
    """Generic AI text generation with provider fallback. Used by all features."""
    cfg = _load_config()
    provider = cfg.get("ai_provider", "groq").lower()

    chain = ["groq", "cerebras", "gemini", "openrouter", "anthropic", "openai"]
    if provider in chain:
        chain.remove(provider)
        chain.insert(0, provider)

    for prov in chain:
        try:
            if prov == "groq" and cfg.get("groq_api_key") and enabled_in(cfg, "ai_groq"):
                from groq import Groq
                client = Groq(api_key=cfg["groq_api_key"])
                kwargs = {
                    "model": cfg.get("groq_model", "llama-3.3-70b-versatile"),
                    "messages": [
                        {"role": "system", "content": system or "You are a helpful assistant."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.7,
                    "max_tokens": max_tokens,
                }
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}
                resp = client.chat.completions.create(**kwargs)
                return resp.choices[0].message.content.strip()

            if prov == "cerebras" and cfg.get("cerebras_api_key") and enabled_in(cfg, "ai_cerebras"):
                import requests
                payload = {
                    "model": cfg.get("cerebras_model", "llama-3.3-70b"),
                    "messages": [
                        {"role": "system", "content": system or "You are a helpful assistant."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.7, "max_tokens": max_tokens,
                }
                if json_mode:
                    payload["response_format"] = {"type": "json_object"}
                r = requests.post(
                    "https://api.cerebras.ai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {cfg['cerebras_api_key']}"},
                    json=payload, timeout=30
                )
                if r.status_code == 429:
                    raise RateLimitError("Cerebras")
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"].strip()

            if prov == "gemini" and cfg.get("gemini_api_key") and enabled_in(cfg, "ai_gemini"):
                import google.generativeai as genai
                genai.configure(api_key=_get_rotating_gemini_key(cfg))
                model = genai.GenerativeModel(
                    cfg.get("gemini_model", "gemini-2.5-flash"),
                    system_instruction=system if system else None,
                )
                try:
                    gc = genai.types.GenerationConfig(
                        temperature=0.7, max_output_tokens=max_tokens,
                        response_mime_type="application/json" if json_mode else "text/plain",
                    )
                except TypeError:
                    gc = genai.types.GenerationConfig(temperature=0.7, max_output_tokens=max_tokens)
                resp = model.generate_content(prompt, generation_config=gc)
                return resp.text.strip()

            if prov == "openrouter" and cfg.get("openrouter_api_key") and enabled_in(cfg, "ai_openrouter"):
                import requests
                r = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {cfg['openrouter_api_key']}",
                        "HTTP-Referer": "https://aria.local",
                    },
                    json={
                        "model": cfg.get("openrouter_model", "meta-llama/llama-3.3-70b-instruct:free"),
                        "messages": [
                            {"role": "system", "content": system or "You are a helpful assistant."},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.7, "max_tokens": max_tokens,
                    }, timeout=30
                )
                if r.status_code == 429:
                    raise RateLimitError("OpenRouter")
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"].strip()

        except RateLimitError:
            print(f"[{prov} rate limit, trying next...]")
            continue
        except Exception as e:
            print(f"[{prov} failed: {e}]")
            continue

    return ""  # All providers failed


def generate_vision(image_bytes: bytes, prompt: str, json_mode: bool = True) -> str:
    """Vision-language model call. Tries Groq Llama-Vision → Gemini Vision."""
    import base64
    cfg = _load_config()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    # Try Groq vision first (free)
    try:
        if cfg.get("groq_api_key") and enabled_in(cfg, "ai_groq"):
            from groq import Groq
            client = Groq(api_key=cfg["groq_api_key"])
            # Try current Groq vision models in order of preference
            models_to_try = [
                "meta-llama/llama-4-scout-17b-16e-instruct",
                "meta-llama/llama-4-maverick-17b-128e-instruct",
                "llama-3.2-11b-vision-preview",
            ]
            for model_name in models_to_try:
                try:
                    kwargs = {
                        "model": model_name,
                        "messages": [
                            {"role": "user", "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_b64}"
                                }},
                            ]},
                        ],
                        "temperature": 0.3, "max_tokens": 600,
                    }
                    if json_mode:
                        kwargs["response_format"] = {"type": "json_object"}
                    resp = client.chat.completions.create(**kwargs)
                    return resp.choices[0].message.content.strip()
                except Exception as e:
                    if "decommissioned" in str(e) or "not_found" in str(e).lower():
                        continue
                    raise
    except Exception as e:
        print(f"[Groq vision failed: {e}]")

    # Try Gemini vision (also free)
    try:
        if cfg.get("gemini_api_key") and enabled_in(cfg, "ai_gemini"):
            import google.generativeai as genai
            genai.configure(api_key=cfg["gemini_api_key"])
            model = genai.GenerativeModel(cfg.get("gemini_model", "gemini-2.5-flash"))
            try:
                gc = genai.types.GenerationConfig(
                    temperature=0.3, max_output_tokens=600,
                    response_mime_type="application/json" if json_mode else "text/plain",
                )
            except TypeError:
                gc = genai.types.GenerationConfig(temperature=0.3, max_output_tokens=600)
            resp = model.generate_content(
                [prompt, {"mime_type": "image/jpeg", "data": image_bytes}],
                generation_config=gc
            )
            return resp.text.strip()
    except Exception as e:
        print(f"[Gemini vision failed: {e}]")

    return ""


def _safety_response(lang):
    msgs = {
        "en": "I hear you. I'm here to keep you safe. Let's talk about something gentle.",
        "ar": "أنا سامعك. أنا هنا عشان أبقى معاك بأمان. خلينا نتكلم في حاجة هادية.",
        "de": "Ich höre dich. Ich bin hier, um dir zu helfen.",
    }
    return {
        "reply": msgs.get(lang, msgs["en"]),
        "face_expression": "calm", "tts_style": "soft",
        "suggested_activity": "breathing", "comfort_mode": True,
        "parent_alert": True, "memory_update": "", "reason": "safety_filter"
    }
