"""AIShell — the heart. Takes raw child input → runs the pipeline → emits actions.

Pipeline:
   text → language norm → safety → AI provider → JSON validate → memory update
        → log → emit reply → fire tool launcher → emit robot command → return to listen
"""

from PySide6.QtCore import QObject, Signal

from core.ai_provider import validate_json_response, fallback_response
from core.language_engine import normalize_franco, detect_language
from core.safety_engine import classify_safety
from core.memory_engine import MemoryEngine
from data import database as db


class AIShell(QObject):
    # UI bindings
    reply_ready = Signal(dict)         # full JSON response
    state_update = Signal(str)         # e.g. 'thinking', 'speaking'
    error = Signal(str)

    def __init__(self, child_id, session_id, ai_provider, tool_launcher,
                 robot_bridge, parent=None):
        super().__init__(parent)
        self.child_id = child_id
        self.session_id = session_id
        self.ai = ai_provider
        self.tools = tool_launcher
        self.robot = robot_bridge
        self.memory = MemoryEngine(child_id, session_id)

    def set_ai_provider(self, provider):
        self.ai = provider

    def process(self, child_input: str) -> dict:
        """Main entry. Returns the validated JSON response."""
        if not child_input or not child_input.strip():
            return fallback_response("en")
        text_norm = normalize_franco(child_input.strip())
        profile = db.get_child(self.child_id) or {}
        lang = profile.get("language") or detect_language(text_norm)

        # Persist incoming
        self.memory.log_turn("child", child_input, intent="")

        # Quick safety pre-screen (we still call AI for nuance, but flag now)
        safety = classify_safety(text_norm, lang=lang)

        self.state_update.emit("thinking")
        try:
            response = self.ai.generate_response(
                text_norm, profile, self.memory.state(),
                self.memory.session_history(),
            )
        except Exception as e:
            self.error.emit(f"ai_error:{e}")
            response = fallback_response(lang)

        # Force-validate (provider might have skipped it)
        response = validate_json_response(response, lang)

        # If safety pre-screen flagged something the AI missed, override.
        if safety["category"] in ("SELF_HARM", "ABUSE_RISK", "MEDICAL_EMERGENCY"):
            response["parent_alert"] = True
            response["alert_type"] = safety["category"].lower()
            response["open_tool"] = "safety"
            response["listening_after_reply"] = False
            if safety["safe_reply"]:
                response["reply"] = safety["safe_reply"]

        # Memory update
        self.memory.apply_ai_memory_update(response.get("memory_update", {}))
        self.memory.log_turn("aria", response.get("reply", ""),
                             emotion=response.get("emotion", ""),
                             intent=response.get("intent", ""))

        # Log emotion + alert if any
        try:
            db.log_emotion(self.child_id, response.get("emotion", "neutral"),
                           response.get("emotion_confidence", 0.5), source="ai")
        except Exception:
            pass
        if response.get("parent_alert"):
            try:
                db.add_alert(self.child_id,
                             response.get("alert_type") or "distress",
                             "high" if response.get("alert_type") in
                                 ("self_harm","abuse_risk","medical_emergency") else "medium",
                             response.get("log_summary") or response.get("reply", ""))
            except Exception:
                pass

        # Robot command
        try:
            rc = response.get("robot_command") or {}
            if rc:
                self.robot.send(rc)
        except Exception:
            pass

        # Emit + dispatch tool
        self.reply_ready.emit(response)
        try:
            self.tools.dispatch(response, child_input)
        except Exception as e:
            self.error.emit(f"tool_dispatch:{e}")

        return response
