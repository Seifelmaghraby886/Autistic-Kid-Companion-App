# ARIA OS — Adaptive Robotic Interaction Assistant Operating System

A voice-first, AI-controlled companion OS interface for autistic children. Built as a graduation project at AASTMT (2026-2027).

> ARIA is a **companion**, not therapy, not a diagnostic tool, not a medical device.
> Every feature is built around evidence-based support strategies under parent supervision.

---

## Quick start

```powershell
# 1. Python 3.11+
# 2. Install deps
pip install -r requirements.txt

# 3. (Optional) add API keys to enable premium providers
copy .env.example .env
# edit .env, fill in ANTHROPIC_API_KEY / ELEVENLABS_API_KEY etc.

# 4. Run the app
python main.py
```

App opens directly into the **child Shell** — auto-listening, no buttons.
Press the small "👤 Parent" button (top-right) and enter PIN **`1234`** to access the Parent Dashboard.

---

## Run tests

```powershell
python run_tests.py
```

Every feature listed in the spec has at least one passing test in `tests/`.

---

## Offline-first design

| Component | Default (no keys) | Premium (with keys) |
|-----------|-------------------|---------------------|
| AI brain  | MockAI (rule-based, all demo scenarios) | Anthropic Claude 3.5 |
| Voice     | edge-tts → pyttsx3 → silent mock | ElevenLabs Multilingual v2 |
| STT       | Google Web Speech (free) + faster-whisper | same |
| Emotion vision | MobileNetV2 CNN local | + Llama-4-Scout VLM via Groq |

The app **always** works without any API key. Adding keys to `.env` unlocks higher quality transparently.

---

## Folder map

```
main.py                 → entry, opens straight into voice shell
run_tests.py            → unittest discover
.env.example            → copy → .env

core/                   → all business logic (no Qt)
  app_controller.py     → top-level coordinator
  ai_shell.py           → input → provider → JSON → action loop
  auto_listening_engine → 13-state FSM (no talk button)
  speech_engine.py      → STT (Whisper for Arabic, Google for en/de)
  tts_engine.py         → fallback chain (ElevenLabs → edge → pyttsx3 → mock)
  intent / safety / language / emotion / memory / tool_launcher engines
  mock_ai.py            → offline rule-based AI for all demo scenarios
  claude_provider.py    → premium AI brain, API-ready
  voice_provider.py     → ElevenLabsProvider + EdgeTTSProvider + Pyttsx3Provider
  robot_bridge.py       → simulated robot commands (logs to DB)

data/database.py        → 13-table SQLite, auto-created on first run
config/*.json           → app, prompts, safety rules, language rules

ui/shell_window.py      → child-facing auto-listening shell (DEFAULT screen)
ui/parent_dashboard.py  → PIN-locked parent tabs (overview, command center, alerts, sessions, schedule, AI & voice, test center)
ui/calm_zone.py         → breathing bubble + comfort
ui/aac_board.py         → 48-pictogram sentence builder
ui/visual_schedule.py   → NOW / NEXT / THEN cards
ui/task_tutorials.py    → brush_teeth, wash_hands step-by-step
ui/story_mode.py        → bedtime / social stories
ui/games.py             → emotion match
ui/parent_pin.py        → PIN gate
ui/components.py        → ARIA face, waveform, glass card, theme tokens

tests/                  → unittest suite covering every required path
```

---

## Demo scenarios (all automated in `tests/test_full_demo_flows.py`)

| Child says | ARIA does |
|------------|----------|
| "أنا جعان" / "ana ga3an" | Opens AAC food, sets state.current_need = hungry |
| "أنا زعلان ومش عايز أتكلم" | Comforts, opens Calm Zone, robot face = sad_soft |
| "بعد كده ايه؟" | Opens Visual Schedule (NOW/NEXT/THEN) |
| "الولد ضربني في المدرسة" | Safe reply + parent alert (bullying) + Calm Zone |
| "open parent mode" | Parent PIN screen, auto-listening pauses |
| "مش عارف اغسل سناني" | Brushing-teeth tutorial |
| "احكيلي قصة" | Story Mode |
| "عايز ألعب" | Games |
| "I want to hurt myself" | Safety reply, parent_alert + critical |

---

## State machine (AutoListeningEngine)

```
IDLE_STARTUP → GREETING → LISTENING ⇄ SPEECH_DETECTED
                                       ↓
                              TRANSCRIBING → THINKING → SPEAKING
                                                          ↓
                                       OPENING_TOOL → TOOL_ACTIVE
                                                          ↓
                                                   RETURNING_TO_LISTEN
                                                          ↓
                                                       LISTENING (again)

PARENT_MODE / SAFETY_MODE / ERROR_RECOVERY override as needed.
```

---

## JSON schema every AI provider must return

See `config/prompts.json` for full description.

```json
{
  "reply": "...",
  "language": "english | egyptian_arabic | german",
  "emotion": "happy | calm | sad | angry | scared | tired | neutral",
  "emotion_confidence": 0.0-1.0,
  "need": "food | water | bathroom | parent | pain | null",
  "intent": "talk | need_food | sad | open_calm_zone | parent_mode | emergency | ...",
  "open_tool": "none | calm_zone | aac | schedule | tutorial | story | game | parent_pin | safety",
  "parent_alert": true|false,
  "alert_type": "normal | distress | pain | bullying | abuse_risk | self_harm | medical_emergency | null",
  "robot_command": { "face":"...", "voice":"...", "led":"...", "movement":"...", "mode":"..." },
  "voice_style": "soft | cheerful | calm | neutral | parent",
  "listening_after_reply": true|false,
  "memory_update": { "current_emotion":"...", "current_need":"...|null", "stress_level":"low|medium|high", "last_topic":"..." },
  "log_summary": "..."
}
```

The validator in `core/ai_provider.py` coerces / repairs malformed JSON and never raises.

---

## Provider status (visible in Parent Dashboard → Overview)

| State | Meaning |
|-------|---------|
| `MockMode · Offline` | No API keys, fully offline |
| `Claude AI · Fallback voice` | Claude active, edge-tts/pyttsx3 voice |
| `MockAI · ElevenLabs voice` | Mock AI, premium voice |
| `Premium (Claude + ElevenLabs)` | All premium |

---

## Troubleshooting

- **No audio:** Parent Dashboard → AI & Voice tab → "Test voice provider".
- **Mic not detected:** App still works — type in the small dev input at the bottom of the shell.
- **First word lost:** STT now uses 50 ms warmup + 250 RMS fixed threshold; should not happen.
- **Arabic transcript is wrong:** install `faster-whisper`; first use downloads the medium model (~1.5 GB).
- **App crash:** check `crash.log` next to `main.py`.

---

## Safety positioning (must always say)

> ARIA OS is a **support and companion system**. It does not diagnose, treat, or cure autism. It does not replace parents, therapists, or doctors. All features are built around evidence-based autism-support strategies (visual schedules, social stories, AAC, ABA-style token economy, sensory regulation tools) — used under parent guidance.

---

## License

For graduation project demonstration. Not for clinical or medical use.
