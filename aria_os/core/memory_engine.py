"""Three-layer memory: live state, session, long-term."""

from data import database as db


class MemoryEngine:
    def __init__(self, child_id, session_id):
        self.child_id = child_id
        self.session_id = session_id
        # In-memory copies for the current turn
        self._state = db.get_child_state(child_id)
        self._session_history = db.session_messages(session_id, limit=20)

    # ── Live state ──────────────────────────────────────────
    def state(self):
        return dict(self._state)

    def update_state(self, **kw):
        """Persist state changes for downstream turns."""
        # Filter to keys that exist on the table
        allowed = {"current_emotion","current_need","stress_level",
                   "energy_level","last_topic","risk_level"}
        clean = {k: v for k, v in kw.items() if k in allowed and v is not None}
        if not clean:
            return
        db.update_child_state(self.child_id, **clean)
        self._state.update(clean)

    # ── Session history ─────────────────────────────────────
    def session_history(self):
        return list(self._session_history)

    def log_turn(self, speaker, text, emotion="", intent=""):
        db.log_message(self.session_id, speaker, text, emotion, intent)
        self._session_history.append({
            "speaker": speaker, "text": text,
            "emotion_estimate": emotion, "intent": intent,
        })
        if len(self._session_history) > 30:
            self._session_history = self._session_history[-30:]

    # ── Long-term memories ──────────────────────────────────
    def remember(self, memory_type, content, importance=1):
        db.add_memory(self.child_id, memory_type, content, importance)

    def recall(self, limit=10):
        return db.get_memories(self.child_id, limit)

    def apply_ai_memory_update(self, mu: dict):
        """Apply the AI's memory_update payload."""
        if not isinstance(mu, dict):
            return
        self.update_state(
            current_emotion=mu.get("current_emotion"),
            current_need=mu.get("current_need"),
            stress_level=mu.get("stress_level"),
            last_topic=mu.get("last_topic"),
        )
