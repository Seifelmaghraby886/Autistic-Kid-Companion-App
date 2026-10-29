"""ARIA intelligence bus — the shared context every feature reads and feeds.

One ChildContext per app run (module-level singleton via get_context()).
Screens report what happened (emotions, visits, activity outcomes); the bus
turns that into:

  * a compact natural-language summary injected into AI prompts
  * an AI-generated "what should we do next?" suggestion for the home shell
    (rule-based fallback when no provider is reachable)
  * automatic reward tokens for completed activities

Qt signals let any screen react live (e.g. the shell's suggestion card).
"""
from __future__ import annotations

import time
import threading
from collections import deque
from datetime import datetime

from PySide6.QtCore import QObject, Signal

import database.db_manager as db
from core.log import log as _log


# Destinations the suggestion engine may propose — must be real nav routes.
_SUGGESTABLE = {
    "talk", "games", "calm", "story", "music", "aac", "comms",
    "journal", "rewards", "bedtime", "sensory", "thermometer", "firstthen",
}

_FRIENDLY = {
    "talk": ("Let's talk", "💬"),
    "games": ("Play a game", "🎮"),
    "calm": ("Calm Zone", "🌿"),
    "story": ("Make a story", "📖"),
    "music": ("Listen to music", "🎵"),
    "aac": ("Picture talk", "🗣"),
    "comms": ("Picture board", "🃏"),
    "journal": ("Mood journal", "📓"),
    "rewards": ("See your stars", "⭐"),
    "bedtime": ("Bedtime story", "🌙"),
    "sensory": ("Sensory play", "🫧"),
    "thermometer": ("How do I feel?", "🌡"),
    "firstthen": ("First … Then", "🧩"),
}

_NEGATIVE = {"sad", "sadness", "fear", "anger", "angry", "disgust"}

# Egyptian-Arabic reasons for the rule-based fallback (AI path localizes itself).
_RULE_REASONS_AR = {
    "calm": "شكلك متضايق شوية — تعالى ناخد نفس مع بعض.",
    "bedtime": "الوقت اتأخر — إيه رأيك في حدوتة قبل النوم؟",
    "games": "لسه ملعبناش النهارده — يلا نلعب!",
    "story": "تعالى نتخيل حكاية حلوة مع بعض.",
    "talk": "نفسي أسمع منك عن يومك.",
}


class ChildContext(QObject):
    """Rolling, in-memory picture of the child's session."""

    suggestion_ready = Signal(str, str, str)   # dest, title, reason
    tokens_changed = Signal(int)               # new total

    def __init__(self, parent=None):
        super().__init__(parent)
        self._child_id = None
        self._emotions = deque(maxlen=40)      # (ts, emotion, source)
        self._visits = deque(maxlen=40)        # (ts, screen)
        self._activities = deque(maxlen=40)    # (ts, activity, outcome)
        self._lock = threading.Lock()

    # ── identity ─────────────────────────────────────────────────────
    def set_child(self, child_id):
        if child_id != self._child_id:
            self._child_id = child_id
            with self._lock:
                self._emotions.clear()
                self._visits.clear()
                self._activities.clear()

    @property
    def child_id(self):
        return self._child_id

    # ── reporting (called from anywhere) ─────────────────────────────
    def record_emotion(self, emotion: str, source: str = "camera"):
        if not emotion:
            return
        with self._lock:
            self._emotions.append((time.time(), str(emotion).lower(), source))

    def record_visit(self, screen: str):
        if not screen:
            return
        with self._lock:
            self._visits.append((time.time(), screen))

    def record_activity(self, activity: str, outcome: str = "completed",
                        award: int = 0, reason: str = ""):
        """Log a finished activity; optionally award reward tokens."""
        with self._lock:
            self._activities.append((time.time(), activity, outcome))
        if award > 0:
            self.award_tokens(award, reason or f"{activity} {outcome}")

    # ── rewards (shared token pool with ui/reward_system.py) ────────
    def award_tokens(self, n: int, reason: str = ""):
        if not self._child_id or n <= 0:
            return
        try:
            total = int(db.get_setting(f"tokens_{self._child_id}", 0)) + int(n)
            db.set_setting(f"tokens_{self._child_id}", total)
            _log(f"context: +{n} tokens ({reason}) -> {total}")
            self.tokens_changed.emit(total)
        except Exception as e:
            _log(f"context: token award failed: {e}")

    def tokens(self) -> int:
        if not self._child_id:
            return 0
        try:
            return int(db.get_setting(f"tokens_{self._child_id}", 0))
        except Exception:
            return 0

    # ── context summary for AI prompts ───────────────────────────────
    def dominant_recent_emotion(self, window_s: float = 600.0):
        cutoff = time.time() - window_s
        with self._lock:
            recent = [e for (ts, e, _s) in self._emotions if ts >= cutoff]
        if not recent:
            return None
        return max(set(recent), key=recent.count)

    def summary(self) -> str:
        """Compact English summary of the session — safe to embed in prompts."""
        parts = []
        hour = datetime.now().hour
        daypart = ("morning" if hour < 12 else
                   "afternoon" if hour < 18 else "evening")
        parts.append(f"time: {daypart}")

        dom = self.dominant_recent_emotion()
        if dom:
            parts.append(f"recent mood: {dom}")

        with self._lock:
            visited = [s for (_t, s) in list(self._visits)[-6:]]
            acts = [f"{a}:{o}" for (_t, a, o) in list(self._activities)[-4:]]
        if visited:
            parts.append("visited: " + ", ".join(visited))
        if acts:
            parts.append("activities: " + ", ".join(acts))
        parts.append(f"stars: {self.tokens()}")
        return " | ".join(parts)

    # ── suggestion engine ─────────────────────────────────────────────
    def _rule_suggestion(self):
        """Deterministic fallback — always returns something sensible."""
        hour = datetime.now().hour
        dom = self.dominant_recent_emotion()
        with self._lock:
            visited = {s for (_t, s) in self._visits}

        if dom in _NEGATIVE:
            return ("calm", "a calming break",
                    "You seemed a little upset — let's breathe together.")
        if hour >= 19:
            return ("bedtime", "a bedtime story",
                    "It's getting late — how about a cozy story?")
        if "games" not in visited:
            return ("games", "a fun game",
                    "We haven't played yet today!")
        if "story" not in visited:
            return ("story", "making a story",
                    "Let's imagine something together.")
        return ("talk", "a little chat",
                "I'd love to hear about your day.")

    def request_suggestion(self, lang: str = "en"):
        """Compute a suggestion in the background; emits suggestion_ready.

        Tries the AI provider chain with a strict two-line contract, falls
        back to rules on any failure so the shell card always fills in.
        The reason sentence is written in the child's language.
        """
        summary = self.summary()
        lang_name = {"ar": "Egyptian Arabic", "de": "German"}.get(lang, "English")

        def work():
            dest = title = reason = None
            try:
                from ai.multi_provider import generate_text
                prompt = (
                    "You help pick the next activity for an autistic child "
                    "using a companion app. Session context: " + summary +
                    ". Choose ONE destination from this exact list: " +
                    ", ".join(sorted(_SUGGESTABLE)) +
                    ". Reply with exactly two lines:\n"
                    "line 1: the destination word only, in English\n"
                    f"line 2: one short, warm sentence in {lang_name} "
                    "(max 12 words) telling the child why, no emojis."
                )
                raw = generate_text(prompt, system="", json_mode=False) or ""
                lines = [l.strip() for l in raw.strip().splitlines() if l.strip()]
                if len(lines) >= 2 and lines[0].lower() in _SUGGESTABLE:
                    dest = lines[0].lower()
                    reason = lines[1][:120]
                    title = _FRIENDLY.get(dest, (dest.title(),))[0]
            except Exception as e:
                _log(f"context: AI suggestion failed ({e}); using rules")

            if dest is None:
                dest, title, reason = self._rule_suggestion()
                title = _FRIENDLY.get(dest, (title,))[0]
                reason = _RULE_REASONS_AR.get(dest, reason) if lang == "ar" else reason
            icon = _FRIENDLY.get(dest, ("", "✨"))[1]
            self.suggestion_ready.emit(dest, f"{icon}  {title}", reason)

        threading.Thread(target=work, daemon=True).start()


    # ── cross-session memory ──────────────────────────────────────────
    def consolidate_to_memory(self):
        """Persist a one-line session digest into ai_memory.memory_summary.

        prompt_builder already injects memory_summary into every system
        prompt, so after a restart ARIA can say "yesterday you loved the
        memory game". Called on app shutdown and safe to call repeatedly —
        it overwrites today's digest rather than appending forever.
        """
        if not self._child_id:
            return
        with self._lock:
            has_data = bool(self._activities or self._emotions or self._visits)
            acts = [f"{a}({o})" for (_t, a, o) in list(self._activities)[-6:]]
        if not has_data:
            return  # nothing worth remembering
        try:
            dom = self.dominant_recent_emotion(window_s=86400) or "calm"
            today = datetime.now().strftime("%b %d")
            digest = (f"[{today}] mood mostly {dom}; "
                      f"did: {', '.join(acts) if acts else 'chatting'}; "
                      f"stars total {self.tokens()}.")
            prev = (db.get_ai_memory(self._child_id) or {}).get("memory_summary") or ""
            # keep at most one previous day's digest for continuity
            prev_lines = [l for l in prev.splitlines()
                          if l.strip() and not l.startswith(f"[{today}]")]
            summary = "\n".join((prev_lines[-1:] + [digest]))[:400]
            db.update_ai_memory(self._child_id, memory_summary=summary)
            _log(f"context: consolidated session -> ai_memory ({digest})")
        except Exception as e:
            _log(f"context: consolidation failed: {e}")


# ── module-level singleton ────────────────────────────────────────────
_instance: ChildContext | None = None


def get_context() -> ChildContext:
    global _instance
    if _instance is None:
        _instance = ChildContext()
    return _instance
