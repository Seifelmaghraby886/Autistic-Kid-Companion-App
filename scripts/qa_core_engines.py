"""QA: functional tests for the core non-UI engines.

Covers: intent_router routing, face_input gesture math, ScanController
selection flow, TTS text cleaning, provider gating. No network, no camera.

Run: py -3.11 scripts/qa_core_engines.py
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from PySide6.QtWidgets import QApplication  # noqa: E402
app = QApplication.instance() or QApplication([])

PASS, FAIL = 0, 0


def check(label, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"OK    {label}")
    else:
        FAIL += 1
        print(f"FAIL  {label}  {detail}")


# ── 1. intent_router ──────────────────────────────────────────────────
from core.intent_router import route, normalize, detect_navigation  # noqa: E402

r = route("open games")
check("router: 'open games' → nav", r and r[0] == "navigate" and r[1] == "games",
      f"got {r!r}")
r = route("go back")
check("router: 'go back' → back", r and r[0] in ("back", "navigate"), f"got {r!r}")
r = route("what's the weather like")
check("router: chit-chat → talk", r and r[0] == "talk", f"got {r!r}")
check("router: normalize strips punctuation",
      normalize("Hello,   WORLD!!") == normalize("hello world"))

# ── 2. face_input gesture math ───────────────────────────────────────
from core.face_input import analyze_gesture  # noqa: E402

now = time.time()
BOX_W = 100.0

# Pure nod: strong vertical oscillation, tiny horizontal noise
nod = [(now + i * 0.08, 200 + (1 if i % 4 < 2 else -1) * 1.0,
        200 + (12 if i % 4 < 2 else -12)) for i in range(18)]
g, dbg = analyze_gesture(nod, BOX_W)
check("gesture: vertical oscillation → nod", g == "nod", f"got {g!r} {dbg}")

# Pure shake: strong horizontal oscillation
shake = [(now + i * 0.08, 200 + (14 if i % 4 < 2 else -14),
          200 + (1 if i % 4 < 2 else -1) * 1.0) for i in range(18)]
g, dbg = analyze_gesture(shake, BOX_W)
check("gesture: horizontal oscillation → shake", g == "shake", f"got {g!r} {dbg}")

# Jitter: tiny random-ish motion → no gesture
jit = [(now + i * 0.08, 200 + (i % 3 - 1) * 1.5, 200 + (i % 2) * 1.5)
       for i in range(18)]
g, dbg = analyze_gesture(jit, BOX_W)
check("gesture: jitter → none", g is None, f"got {g!r} {dbg}")

# ── 3. ScanController ────────────────────────────────────────────────
from core.scan_mode import ScanController  # noqa: E402

spoken, selected = [], []
sc = ScanController(child_id=3, speak_fn=lambda t: spoken.append(t))
sc.start([("Talk", "talk"), ("Games", "games"), ("Calm", "calm")],
         on_select=lambda v: selected.append(v), window_ms=60000)
check("scan: starts active + speaks first option",
      sc.is_active() and len(spoken) >= 1, f"spoken={spoken}")
sc.on_gesture("shake")          # advance to option 2
sc.on_gesture("nod")            # select option 2
check("scan: shake advances, nod selects", selected == ["games"],
      f"selected={selected}")
check("scan: stops after selection", not sc.is_active())

# voice yes path
spoken.clear(); selected.clear()
sc2 = ScanController(child_id=3, speak_fn=lambda t: spoken.append(t))
sc2.start([("A", "a"), ("B", "b")], on_select=lambda v: selected.append(v),
          window_ms=60000)
sc2.on_voice("yes")
check("scan: spoken 'yes' selects current", selected == ["a"],
      f"selected={selected}")

# ── 4. TTS text cleaning ─────────────────────────────────────────────
from speech.tts_engine import _clean_speech_text  # noqa: E402

cleaned = _clean_speech_text("**Hello!** 😀🎉 How are _you_? ## Title")
check("tts: strips emoji", "😀" not in cleaned and "🎉" not in cleaned,
      f"got {cleaned!r}")
check("tts: strips markdown", "**" not in cleaned and "##" not in cleaned,
      f"got {cleaned!r}")
check("tts: keeps words", "Hello" in cleaned and "How are" in cleaned,
      f"got {cleaned!r}")

# ── 5. provider gating ───────────────────────────────────────────────
from core.provider_control import all_states, is_enabled  # noqa: E402

states = all_states()
check("providers: 12 states exposed", len(states) >= 12, f"got {len(states)}")
check("providers: is_enabled returns bool",
      isinstance(is_enabled("ai_gemini"), bool))

# ── 6. intelligence bus (core/child_context.py) ─────────────────────
from core.child_context import ChildContext  # noqa: E402
import database.db_manager as db  # noqa: E402

ctx = ChildContext()
ctx.set_child(3)

ctx.record_emotion("sad", source="test")
ctx.record_emotion("sad", source="test")
ctx.record_emotion("happy", source="test")
check("context: dominant emotion", ctx.dominant_recent_emotion() == "sad")

ctx.record_visit("GamesScreen")
ctx.record_activity("game:memory", "won")
s = ctx.summary()
check("context: summary mentions visit + activity",
      "GamesScreen" in s and "game:memory" in s, f"got {s!r}")

# token round-trip (restore afterwards)
tok_before = ctx.tokens()
ctx.award_tokens(2, "qa test")
check("context: tokens awarded", ctx.tokens() == tok_before + 2)
db.set_setting("tokens_3", tok_before)  # restore

# rule fallback: sad session must suggest calm
dest, _t, _r = ctx._rule_suggestion()
check("context: sad session → calm suggestion", dest == "calm", f"got {dest!r}")

# request_suggestion with AI forced to fail → rule fallback still emits
import ai.multi_provider as mp  # noqa: E402
_orig_gen = mp.generate_text
mp.generate_text = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("offline"))
got = []
ctx.suggestion_ready.connect(lambda d, t, r: got.append((d, t, r)))
ctx.request_suggestion("ar")
deadline = time.time() + 5
while not got and time.time() < deadline:
    app.processEvents()
    time.sleep(0.02)
mp.generate_text = _orig_gen
check("context: suggestion emitted offline", bool(got), f"got {got!r}")
if got:
    check("context: offline suggestion is calm (sad session)",
          got[0][0] == "calm", f"got {got[0]!r}")

# prompt builder embeds the session context
from ai.prompt_builder import build_system_prompt  # noqa: E402
from core.child_context import get_context  # noqa: E402
get_context().set_child(3)
get_context().record_activity("game:memory", "won")
p = build_system_prompt({"name": "T", "age": 7, "language": "en"},
                        {}, {}, "happy", "chat", None)
check("prompt: session context injected", "THIS SESSION" in p and "game:memory" in p)

# ── 7. cross-session memory consolidation ───────────────────────────
mem_before = (db.get_ai_memory(3) or {}).get("memory_summary") or ""
ctx2 = ChildContext()
ctx2.set_child(3)
ctx2.record_activity("game:memory", "won")
ctx2.record_emotion("happy", "test")
ctx2.consolidate_to_memory()
mem_after = (db.get_ai_memory(3) or {}).get("memory_summary") or ""
check("memory: session digest persisted",
      "game:memory" in mem_after and "mood mostly" in mem_after,
      f"got {mem_after!r}")
# prompt builder should surface it after restart-simulation
p2 = build_system_prompt(db.get_child(3) or {"name": "x", "age": 7},
                         {}, db.get_ai_memory(3) or {}, "calm", "chat", None)
check("memory: digest reaches the prompt", "game:memory" in p2)
db.update_ai_memory(3, memory_summary=mem_before)  # restore

# ── 8. reduce-motion flag ────────────────────────────────────────────
import ui.styles as styles
styles._REDUCE_MOTION = None            # reset cache
check("motion: default off", styles.reduce_motion() is False)
styles._REDUCE_MOTION = True            # simulate enabled
from ui.animated_bg import MeshBackground
mb = MeshBackground(None)
check("motion: mesh timer idle when reduced", not mb._timer.isActive())
styles._REDUCE_MOTION = None            # reset for other tests

# ── summary ──────────────────────────────────────────────────────────
print(f"\nPASS {PASS}  FAIL {FAIL}")
raise SystemExit(1 if FAIL else 0)
