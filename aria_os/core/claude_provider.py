"""ClaudeProvider — API-ready Anthropic Claude wrapper. Falls back to MockAI."""

import os
import json
from pathlib import Path

from core.ai_provider import AIProvider, validate_json_response, fallback_response


def _load_env_key():
    """Load ANTHROPIC_API_KEY from .env or environment."""
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if key:
        return key
    env = Path(__file__).parent.parent / ".env"
    if env.exists():
        try:
            for line in env.read_text().splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
        except Exception:
            pass
    return ""


def _load_prompt_config():
    p = Path(__file__).parent.parent / "config" / "prompts.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"system_prompt": "You are ARIA, a child companion.", "json_schema_description": ""}


class ClaudeProvider(AIProvider):
    name = "Claude"

    def __init__(self):
        self._key = _load_env_key()
        self._cfg = _load_prompt_config()
        self.model = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        self.available = bool(self._key)
        self._client = None
        if self.available:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self._key)
            except Exception as e:
                print(f"[Claude init error: {e}]")
                self.available = False

    def refresh_key(self):
        """Re-check env after user sets the key from Settings."""
        self.__init__()

    def status(self):
        if not self._key:
            return {"name": self.name, "available": False, "reason": "missing_api_key"}
        if not self._client:
            return {"name": self.name, "available": False, "reason": "client_init_failed"}
        return {"name": self.name, "available": True}

    def _build_system_prompt(self, profile, state):
        base = self._cfg.get("system_prompt", "")
        schema = self._cfg.get("json_schema_description", "")
        name = (profile or {}).get("name", "the child")
        age = (profile or {}).get("age", 8)
        lang = (profile or {}).get("language", "en")
        interests = ", ".join((profile or {}).get("interests_json", []) or []) or "none"
        triggers = ", ".join((profile or {}).get("triggers_json", []) or []) or "none"
        cur_em = (state or {}).get("current_emotion", "neutral")
        cur_need = (state or {}).get("current_need", "")
        stress = (state or {}).get("stress_level", "low")

        ctx = (
            f"\n\nCHILD PROFILE:\n"
            f"- Name: {name}, age: {age}\n"
            f"- Language: {lang} (use Egyptian colloquial if ar)\n"
            f"- Interests: {interests}\n"
            f"- Triggers (avoid): {triggers}\n"
            f"\nCURRENT STATE:\n"
            f"- Emotion: {cur_em}\n"
            f"- Open need: {cur_need or 'none'}\n"
            f"- Stress: {stress}\n"
        )
        return base + ctx + "\n\nOUTPUT SCHEMA:\n" + schema

    def generate_response(self, child_input, child_profile=None, child_state=None,
                          session_history=None):
        if not self.available or not self._client:
            from core.mock_ai import MockAIProvider
            return MockAIProvider().generate_response(child_input, child_profile,
                                                     child_state, session_history)
        try:
            sys_prompt = self._build_system_prompt(child_profile, child_state)
            msgs = []
            for h in (session_history or [])[-6:]:
                role = "user" if h.get("speaker") == "child" else "assistant"
                msgs.append({"role": role, "content": h.get("text", "")})
            msgs.append({"role": "user", "content": child_input or ""})

            resp = self._client.messages.create(
                model=self.model,
                max_tokens=600,
                system=sys_prompt,
                messages=msgs,
            )
            text = resp.content[0].text if resp.content else ""
            # Try to parse JSON out of the response
            import re
            m = re.search(r"\{[\s\S]*\}", text)
            raw = m.group(0) if m else text
            return validate_json_response(raw, (child_profile or {}).get("language", "en"))
        except Exception as e:
            print(f"[ClaudeProvider error → fallback: {e}]")
            from core.mock_ai import MockAIProvider
            r = MockAIProvider().generate_response(child_input, child_profile,
                                                  child_state, session_history)
            r["log_summary"] = f"claude_fallback:{e}"
            return r
