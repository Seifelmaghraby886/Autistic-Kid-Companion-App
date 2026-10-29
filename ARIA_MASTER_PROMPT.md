# ARIA — Master Build Prompt (combined: full feature app + OS shell)

You are a senior full-stack software architect, AI product engineer, autism-assistive-technology UX designer, Windows desktop developer, QA engineer, AI safety engineer, ML engineer, and test automation engineer.

Build the complete production version of **ARIA — Adaptive Robotic Interaction Assistant**.

---

## 1. PRODUCT POSITIONING (read carefully — wording matters)

ARIA is a **24/7 AI companion** for autistic children. It is:
- A **voice-first companion OS shell** that opens directly into hands-free conversation.
- A **rich support platform** with 25+ research-grounded tools (calm zone, AAC, schedule, tutorials, games, biometric monitoring, etc.).
- A **parent-supervised, evidence-grounded support system**.

ARIA is **NOT**:
- a therapy robot, therapy replacement, ABA delivery system, or diagnostic tool;
- a medical device;
- a "clinically validated" product (unless future clinical trial work is explicitly marked as future work).

Always use the words **support / assist / suggest / estimate / companion / parent-guided**.
Never claim **diagnose / cure / treat / clinically proven**.

---

## 2. TARGET PLATFORM & STACK

- **OS:** Windows desktop (Python 3.11+).
- **UI:** PySide6 (Qt 6.6+). Custom `QPainter` rendering for the ARIA face. `QtWebEngine` for embedded videos.
- **DB:** SQLite (stdlib only).
- **Audio:** `pygame.mixer` for playback; `pyaudio` + `SpeechRecognition` + `faster-whisper` for STT.
- **Provider abstraction:** all AI/voice services hidden behind base classes so swaps are 1-line config.
- **No CUDA required.** Must run on CPU.
- **Offline by default.** App MUST run fully (MockAI + offline TTS) with zero API keys.
- **Crash-safe:** global `excepthook` writes to `crash.log`, never propagates to Qt event loop.

---

## 3. PROJECT STRUCTURE (final)

```
aria/
├── main.py                     ← entry, opens directly into shell
├── run_tests.py                ← `python run_tests.py`
├── requirements.txt
├── README.md
├── .env.example
├── crash.log                   ← auto-created
│
├── config/
│   ├── app_config.json
│   ├── prompts.json            ← system prompt + JSON schema description
│   ├── safety_rules.json       ← multilingual keyword categories
│   └── language_rules.json     ← Franco-Arabic + intent patterns
│
├── core/                       ← pure logic, NO Qt imports
│   ├── app_controller.py       ← top-level coordinator
│   ├── ai_shell.py             ← input→provider→JSON→action loop
│   ├── ai_provider.py          ← AIProvider ABC + JSON validator
│   ├── mock_ai.py              ← MockAIProvider (offline rule-based)
│   ├── claude_provider.py      ← ClaudeProvider (Anthropic, premium)
│   ├── groq_provider.py        ← GroqProvider (Llama-3.3-70B, FREE primary)
│   ├── gemini_provider.py      ← GeminiProvider (vision-capable)
│   ├── cerebras_provider.py    ← CerebrasProvider (FREE, fast)
│   ├── openai_provider.py      ← OpenAIProvider (GPT-4o-mini)
│   ├── openrouter_provider.py  ← OpenRouterProvider (free model rotation)
│   ├── ollama_provider.py      ← OllamaProvider (local, infinite)
│   ├── multi_provider.py       ← fallback chain orchestrator
│   ├── voice_provider.py       ← VoiceProvider ABC + Mock + pyttsx3 + edge-tts + ElevenLabs
│   ├── tts_engine.py           ← TTSEngine coordinator
│   ├── speech_engine.py        ← STT (Whisper Medium for Arabic, Google for en/de)
│   ├── voice_activity_detector.py
│   ├── auto_listening_engine.py← 13-state FSM
│   ├── intent_engine.py        ← rule-based intent detection
│   ├── safety_engine.py        ← 7-category multilingual safety classifier
│   ├── language_engine.py      ← Franco-Arabic normalize + lang detect
│   ├── egyptian_polish.py      ← 60+ MSA→Egyptian regex
│   ├── emotion_engine.py       ← text-based emotion estimate
│   ├── memory_engine.py        ← 3-layer (live/session/long-term)
│   ├── tool_launcher.py        ← maps open_tool → Qt Signal
│   ├── robot_bridge.py         ← simulated/real robot commands
│   └── provider_status.py      ← aggregates availability
│
├── vision/
│   ├── camera_manager.py
│   ├── face_detector.py        ← Haar cascade
│   ├── emotion_predictor.py    ← MobileNetV2 wrapper
│   ├── image_preprocessor.py
│   ├── emotion_smoothing.py    ← deque-based VAD-style smoothing
│   ├── vlm_emotion.py          ← Llama-4-Scout vision via Groq, on-demand
│   └── multimodal_fusion.py    ← face + BPM/HRV fusion
│
├── biometric/
│   └── heart_rate.py           ← Apple Watch CSV + mock + RMSSD HRV + classify_stress
│
├── audio/
│   └── sound_garden.py         ← procedural brown noise, ocean, rain, ambient pad
│
├── ml_training/                ← optional, for retraining the CNN
│   ├── prepare_datasets.py
│   ├── train_emotion_model.py
│   ├── evaluate_model.py
│   ├── export_model.py
│   └── training_report.py
│
├── ui/
│   ├── shell_window.py         ← main child-facing AUTO-LISTENING shell (no buttons)
│   ├── aria_face_v2.py         ← holographic robot head with neural net + eye tracking
│   ├── components.py           ← GlassCard, WaveformBar, MeshBackground
│   ├── animated_bg.py          ← futuristic mesh gradient
│   ├── styles.py               ← global QSS + color tokens
│   ├── splash_screen.py
│   ├── parent_profile.py
│   ├── child_profile.py
│   ├── welcome_back.py
│   ├── dashboard.py            ← optional rich grid of all 25 tools (parent toggle)
│   ├── talk_screen.py          ← legacy chat fallback
│   ├── live_camera.py          ← CNN + on-demand VLM smart analysis
│   ├── photo_emotion_test.py
│   ├── games.py                ← 5+ autism-friendly mini-games
│   ├── calm_zone.py            ← breathing bubble + comfort phrases
│   ├── sensory_toolkit.py      ← liquid galaxy / bubbles / wash / shape bloom
│   ├── music_player.py         ← Sound Garden UI
│   ├── feelings_thermometer.py ← 1-10 mercury thermometer
│   ├── mood_journal.py         ← 30-day heatmap
│   ├── visual_schedule.py      ← NOW/NEXT/THEN
│   ├── visual_timer.py         ← Time-Timer-style countdown
│   ├── transition_helper.py    ← activity-change warnings
│   ├── task_tutorials.py       ← 9 animated ADL tutorials + YouTube embed
│   ├── video_player.py         ← QtWebEngine YouTube embed
│   ├── communication_board.py  ← quick non-verbal buttons
│   ├── aac_builder.py          ← 48-pictogram sentence builder
│   ├── reward_system.py        ← Star Jar token economy
│   ├── ai_coach.py             ← AI Coping Coach
│   ├── bedtime_story.py        ← AI personalized bedtime story
│   ├── story_generator.py      ← AI custom social stories
│   ├── social_coach.py         ← 10-scenario social skill practice
│   ├── biometric_screen.py     ← live BPM + HRV + multimodal fusion
│   ├── ai_insights.py          ← AI pattern analysis for parents
│   ├── parent_pin.py           ← PIN gate
│   ├── parent_dashboard.py     ← reports, alerts, schedule editor, command center, test center
│   ├── settings.py             ← devices, voices, providers, language
│   └── test_center.py          ← in-app test runner
│
├── data/
│   ├── database.py             ← SQLite schema + helpers (auto-init)
│   ├── aria.db                 ← auto-created
│   └── seed_data.py            ← default child, parent, schedule
│
├── tests/
│   ├── _setup_path.py
│   ├── test_intents.py
│   ├── test_safety.py
│   ├── test_memory.py
│   ├── test_ai_shell.py
│   ├── test_tool_launcher.py
│   ├── test_database.py
│   ├── test_robot_bridge.py
│   ├── test_provider_fallback.py
│   ├── test_auto_listening.py
│   ├── test_egyptian_polish.py
│   ├── test_multimodal_fusion.py
│   ├── test_safety_engine_arabic.py
│   ├── test_emotion_smoothing.py
│   └── test_full_demo_flows.py
│
├── models/
│   ├── emotion_model.h5
│   ├── emotion_model.tflite
│   └── labels.json
│
├── assets/
│   ├── icons/aria_icon.ico     ← multi-res, generated by assets/make_icon.py
│   ├── faces/, sounds/, pictograms/, animations/
│   └── make_icon.py
│
└── presentation/
    ├── ARIA_Presentation.pptx
    ├── TECH_DOCUMENTATION.md
    ├── VIDEO_SCRIPT.md
    └── screenshots/
```

---

## 4. CHILD-FACING APP FLOW (voice-first)

**Default launch flow:**
1. `main.py` → pre-init pygame mixer on main thread.
2. SplashScreen (≤2 s).
3. If first run → ParentProfile → ChildProfile → DeviceSetup wizard.
4. If returning → WelcomeBack → child picks profile.
5. Open **ShellWindow** (the OS-style talk screen) — NOT the dashboard.

**ShellWindow** is the default child interface:
- Holographic ARIA face (240px) center, animated with neural network "thinking" mode, eye tracking, blink.
- Status line under face: "ARIA is waking up…" → "ARIA is listening… 🎙" → "Thinking…" → "ARIA is talking…"
- Waveform bar (animated when listening).
- Conversation bubble showing ARIA's last reply.
- Tiny dev text input at the bottom (collapsed appearance) — for testing only.
- Small top-right "👤 Parent" button.

**The child NEVER presses a button to talk.** AutoListeningEngine handles everything.

**Parent can still reach the rich 25-tool dashboard** via the Parent Dashboard → Command Center, OR by enabling "Tools Drawer" in settings, which adds a swipe-up panel on the shell.

---

## 5. AUTOMATIC LISTENING — STATE MACHINE

`core/auto_listening_engine.py` implements `AutoListeningEngine` with these states:

```
IDLE_STARTUP → GREETING → LISTENING → SPEECH_DETECTED → TRANSCRIBING
→ THINKING → SPEAKING → OPENING_TOOL → TOOL_ACTIVE → RETURNING_TO_LISTEN
→ LISTENING …  or PARENT_MODE / SAFETY_MODE / ERROR_RECOVERY
```

Rules:
- App boots → `GREETING` (TTS plays greeting in child's language).
- After greeting → `LISTENING` automatically.
- Speech detected → `SPEECH_DETECTED` → `TRANSCRIBING` → `THINKING`.
- `THINKING` runs through AIShell pipeline (see §6).
- `SPEAKING` (TTS) → if tool needed `OPENING_TOOL` → `TOOL_ACTIVE` → back to `RETURNING_TO_LISTEN` → `LISTENING`.
- Parent mode pauses auto-listening unless parent re-enables.
- Safety mode prioritizes parent alert; does not return to casual chat.
- Errors fall back to `ERROR_RECOVERY` with 1.5 s cooldown then resume.

**STT engine** (`SpeechEngine`):
- For `ar`: faster-whisper "medium" with Egyptian dialect primer (≥200 dialect words injected as `initial_prompt`).
- For `en` / `de`: Google Web Speech via `SpeechRecognition` (lower latency).
- VAD-based silence stop: 2.8 sec silence + min 1.5 sec speech + min 0.5 sec accumulated speech.
- 50 ms hardware warmup BEFORE the listening-started signal, so first words are never lost.
- Fixed RMS threshold (250) — NO calibration delay that eats first words.

---

## 6. AISHELL PIPELINE (every input flows here)

```
raw text
   ↓
language detect + Franco-Arabic normalize
   ↓
safety pre-screen  →  if SELF_HARM/ABUSE/MEDICAL → force safe response + parent_alert=true
   ↓
AI provider (chain in §8) returns structured JSON
   ↓
validate JSON against schema; coerce missing fields; never raise
   ↓
post-process: Egyptian polish if lang=ar
   ↓
memory.apply_update + log emotion + log alert + log chat
   ↓
robot_bridge.send(robot_command)
   ↓
emit reply_ready → UI bubble + TTS speaks
   ↓
tool_launcher.dispatch(response) → UI opens calm_zone / aac / schedule / …
   ↓
when TTS finishes → auto-listening resumes (unless tool blocks)
```

---

## 7. AI RESPONSE — STRUCTURED JSON SCHEMA

The AI MUST always return valid JSON in this exact shape. The validator coerces/repairs anything missing:

```json
{
  "reply": "تمام يا حبيبي، أنا معاك. نفتح الوضع الهادي؟",
  "language": "english|egyptian_arabic|german",
  "emotion": "happy|calm|sad|angry|scared|tired|neutral",
  "emotion_confidence": 0.68,
  "need": "food|water|bathroom|parent|pain|null",
  "intent": "talk|need_food|need_water|need_bathroom|need_parent|pain|sad|angry|scared|overstimulated|open_calm_zone|open_aac|open_schedule|open_tutorial|open_story|open_game|parent_mode|emergency|unknown",
  "open_tool": "none|calm_zone|aac|schedule|tutorial|story|game|parent_pin|safety|sensory|music|thermometer|coach|biometric",
  "parent_alert": false,
  "alert_type": "normal|distress|pain|bullying|abuse_risk|self_harm|medical_emergency|null",
  "robot_command": {
    "face": "calm|sad_soft|happy|neutral|concern",
    "voice": "soft|comfort|cheerful|neutral",
    "led": "calm_blue|cheerful_teal|warm_amber|alert_pulse",
    "movement": "stay_still|gentle_nod|wave",
    "mode": "idle|comfort|play|alert"
  },
  "voice_style": "soft|cheerful|calm|neutral|parent",
  "listening_after_reply": true,
  "memory_update": {
    "current_emotion": "sad",
    "current_need": null,
    "stress_level": "low|medium|high",
    "last_topic": "school"
  },
  "log_summary": "child appeared sad and calm zone was suggested"
}
```

The schema definition lives in `config/prompts.json` and is included in every system prompt.

---

## 8. AI PROVIDER CHAIN (free-first, fallback)

```
1. Groq           (Llama-3.3-70B)              ← PRIMARY (FREE, 30 RPM, 80 ms latency)
2. Cerebras       (Llama-3.3-70B)              ← FREE 8000/day
3. Gemini         (2.5-flash)                  ← FREE 15 RPM (vision)
4. OpenRouter     (llama-3.3-70b:free etc.)    ← FREE variable
5. Anthropic      (claude-3-5-sonnet/haiku)    ← PAID — best empathy
6. OpenAI         (gpt-4o-mini)                ← PAID
7. Ollama         (local llama3.2:3b)          ← ∞ FREE OFFLINE
8. MockAI         (rule-based, no network)     ← FINAL FALLBACK
```

- A 429 / quota error on a provider triggers automatic fallback to the next.
- Multi-key Gemini rotation: parent can paste an array of keys; chain rotates per request.
- Response cache for common phrases ("hi", "thanks", "bye") in 3 languages — zero API call on hit.
- ClaudeProvider for the **premium AI brain** (safety-aware, ASD-empathetic, JSON-strict).
- ElevenLabsProvider for the **premium voice** (multilingual_v2 model, 4.78 MOS vs Azure 4.21).
- Provider keys live ONLY in `.env`. App refuses to embed them in code.

Provider status surface in Parent Dashboard:
- `MockMode` / `Claude Connected` / `ElevenLabs Connected` / `Missing API Key` / `Fallback Active` / `Premium (Claude + ElevenLabs)`.

---

## 9. VOICE PROVIDER CHAIN

```
1. ElevenLabsProvider  (premium, multilingual_v2)   — if API key present
2. EdgeTTSProvider     (Microsoft neural — FREE)    — Salma/Jenny/Katja voices
3. Pyttsx3Provider     (Windows SAPI offline)
4. MockTTSProvider     (print-only — silent fallback)
```

Voice style maps to `rate` / `pitch` per provider:
- `soft` → rate −15 %
- `very_slow` → rate −30 %
- `cheerful` → rate +0 %, pitch +1 st
- `comfort` → rate −20 %, pitch −1 st

Egyptian Arabic default voice: **`ar-EG-SalmaNeural`**.
Text-language auto-detect overrides the stored voice if the AI replies in a different language than expected (e.g. AI fell back to English; we still want Salma if config says Arabic).

---

## 10. LANGUAGES SUPPORTED

- **English** — default.
- **Egyptian Arabic عامية مصرية** — primary target. Must NEVER be MSA.
- **German Deutsch**.

**Egyptian dialect enforcement (3 layers):**
1. Prompt-side: hard rules ("NEVER use MSA"), 30+ replacement pairs, warm-style examples.
2. Whisper-side: 200-word Egyptian primer in `initial_prompt`.
3. Post-process: `egyptian_polish.py` regex converts 60+ common MSA tokens (ماذا→ايه, كيف→ازاي, الآن→دلوقتي, أريد→عايز, نعم→آه, شيء→حاجة, etc.).

**Franco-Arabic input** is normalized to Arabic before intent detection:
`ana ga3an` → `أنا جعان`, `msh 3ayz` → `مش عايز`, etc.

---

## 11. SAFETY ENGINE

7 categories with multilingual keyword lists (en + ar + Franco):

| Category | Severity | Action |
|----------|----------|--------|
| `SELF_HARM` | critical | safe reply, parent_alert=true, no casual chat, open safety screen |
| `ABUSE_RISK` | critical | same |
| `MEDICAL_EMERGENCY` | critical | same |
| `BULLYING` | high | open calm zone + parent alert |
| `PAIN` | medium | open AAC pain board + parent alert |
| `HUNGER_THIRST` | low | open AAC food/water board |
| `NORMAL` | none | normal pipeline |

Safe-reply templates in 3 languages live in `config/safety_rules.json`.

---

## 12. CORE FEATURES — every screen below MUST work and be tested

### Conversation / AI
- **Talk with ARIA / Shell** — voice-first auto-listening, multi-turn memory (last 6 turns).
- **AI Coping Coach** — pick feeling → AI generates 3 personalized strategies in child's language.
- **AI Bedtime Story** — 6 themes, child becomes the hero, TTS narration in selected voice.
- **AI Social Story Generator** — 9 preset situations + custom input, generated stories grounded in social-story method.
- **AI Insights** — Gemini analyzes child's logs and outputs `{summary, patterns, concerns, wins, recommendations}` for parents.
- **Social Skills Coach** — 10 scenarios (bullying, asking for help, sharing, birthday party…); AI returns story + 3-4 options + best choice + practice phrase with TTS.

### Vision / Emotion
- **Live Camera** — MobileNetV2 CNN @ 30 fps (6 classes: anger/fear/joy/neutral/sadness/surprise) + on-demand **Smart Analysis** that sends frame to Llama-4-Scout vision (Groq) for rich description.
- **Photo Emotion Test** — import image → CNN inference + probability bars.
- **Emotion smoothing** — deque-based, only emits when one emotion is dominant ≥3 frames AND not within 3 sec of last emit.

### Biometric (NEW)
- **Biometric Monitor** — live BPM, HRV (RMSSD), 60-sec scrolling chart, beating-heart visual.
- Sources: Apple Watch Health-export CSV import, mock generator, future Bluetooth bracelet.
- `classify_stress(bpm, age, hrv_rmssd)` returns `{score 0–100, label calm/alert/stressed/high_stress}` with age-aware resting ranges.
- `fuse_face_and_biometric()` detects **masking** (calm face + high biometric stress) — flags parent alert, suggests calm zone.

### Calming & Sensory
- **Calm Zone** — animated breathing bubble (4 s in / 4 s out), comfort phrases in 3 languages, "I feel better" button, parent help button, automatic return-to-listening.
- **Sensory Toolkit** — 4 procedural visualizations: Liquid Galaxy, Slow Bubbles, Color Wash, Shape Bloom. All Qt-painted, no assets.
- **Sound Garden** — 6 procedural sounds (numpy + pygame): brown noise, pink noise, ocean waves, gentle rain, ambient pad (C-major), humming tone (110 Hz). Live waveform visualizer.
- **Feelings Thermometer** — vertical mercury thermometer, 10 levels with emoji, color shifts green→yellow→red, pulses red ≥7, AI suggestion + TTS speaks it.

### Communication
- **AAC Builder** — 48 pictograms across 4 categories (I want / I feel / Help / Yes-No), multi-tap sentence builder, "Speak" reads sentence via TTS.
- **Quick Buttons / Communication Board** — large single-tap buttons for "I need a break", "Too loud", "I want mom", etc.

### Daily Life
- **Visual Schedule** — NOW / NEXT / THEN; parent edits, child marks task done; child can ask "بعد كده ايه؟" and ARIA opens it automatically.
- **Visual Timer** — Time-Timer-style countdown with halfway warning at 50 %, 30-sec warning at end, color shifts green→yellow→red.
- **Transition Helper** — picks "🎮 → 🍽️ Game → Dinner" presets, 5/2/1/30s/done warnings spoken in child's language.
- **Task Tutorials** — 9 animated ADL tutorials (brush teeth, wash hands, dress, tie shoes, bathroom, eat, bedtime, school morning, cross street) with custom Qt animations + TTS narration + embedded YouTube video button (QtWebEngine).
- **Star Jar** — token reward system; visual jar fills, 5 redeemable rewards configured by parent.
- **Mood Journal** — daily check-in (6 feelings), 30-day calendar heatmap, AI insight summary.

### Games
- 5+ autism-friendly mini-games: Emotion Match, Color Sorting, Shape Matching, Memory Cards, Routine Ordering.
- No flashing, calm colors, positive reinforcement only.

### Parent
- **Parent Dashboard** — PIN-locked tabs: Overview / Emotions / Chat Log / Sessions / AI Insights / Settings / Test Center / Export.
- **Command Center** — buttons to manually open any tool, trigger robot comfort mode, run all tests.
- **Settings** — child profile, mic select + test, camera select + test, voice select + test, AI provider selector, API key inputs (Claude/ElevenLabs/Groq/Cerebras/OpenRouter/Gemini), language, sensory mode, safety sensitivity, allowed tools toggles, auto-listening toggle, robot simulator toggle, privacy (export/delete data).
- **Test Center** — visible "Run All Tests" button, shows pass/fail counts, saves results to `test_results` table.

### Robot Bridge
- `RobotBridge` emits structured commands `{face, voice, led, movement, mode}` after every AI turn.
- Logs to `robot_commands` table.
- Future hardware integration is a 1-method swap (replace `_send`).
- Parent Dashboard shows last 20 commands.

---

## 13. UI / VISUAL DESIGN

- **Dark navy** main background (`#0A1428`) with cyan/teal/purple accents.
- **Holographic ARIA face** (`ui/aria_face_v2.py`):
  - Custom QPainter rendering, no static art.
  - Layers: orbiting particle aura, 3 pulsing halos, rotating arc segments when listening, glassmorphic head sphere, neural-network nodes inside head when in `thinking` state, glowing iris with cursor tracking, blink scheduler, phoneme-style mouth when speaking, eyebrow shape per emotion, tech accent dots.
- **MeshBackground** for tools — 6 flowing colored blobs (teal/cyan/purple) + 25 twinkling stars + subtle grid pattern.
- **GlassCard** widget with shadow, dark + light variants, hover lift, hover holographic border (teal→cyan→purple gradient).
- **WaveformBar** that animates while LISTENING.
- **Slow animations only** (≥300 ms easing curves). No flashing. No harsh red except parent emergency alerts.
- **WCAG AA contrast** (≥4.5 : 1) on all text.
- Fonts: Segoe UI / Inter, 14-22 pt body, 36 pt+ titles.
- App icon: multi-resolution `.ico` generated by `assets/make_icon.py` (holographic teal-purple "A" with neural ring + gold accent dot).

---

## 14. APP MODES

ARIA adapts behavior to context:

| Mode | Trigger | Behavior |
|------|---------|----------|
| **Home** | default | Full features |
| **School** | parent toggle | Quiet voice, minimal animations, focus support |
| **Therapy** | parent toggle | Emotion games + social stories surfaced; richer logging |
| **Play** | child requests game | Cheerful voice, games available |
| **Calm** | sad/scared/anger detected sustained, or thermometer ≥7 | Low brightness, breathing only, very soft voice |
| **Sleep** | bedtime hour OR child asks for story at night | Very low brightness, bedtime story, no games |
| **Parent** | PIN unlock | Auto-listening paused, full dashboard |
| **Safety** | self-harm/abuse/medical keyword | Safe response, parent alert, no casual chat |

---

## 15. DATABASE SCHEMA (SQLite)

13 tables. Auto-created on first run by `data/database.py`:

```
children            id name age language communication_level sensory_profile_json
                    interests_json triggers_json created_at
parents             id name pin_hash email phone
sessions            id child_id start_time end_time mode summary risk_level
messages            id session_id speaker text emotion_estimate intent created_at
child_state         child_id current_emotion current_need stress_level
                    energy_level last_topic risk_level last_updated
memories            id child_id memory_type content importance created_at last_used
emotion_logs        id child_id emotion confidence source timestamp
schedule_items      id child_id title icon time status repeat_rule
alerts              id child_id type severity message resolved timestamp
goals               id child_id goal_name target_behavior progress created_at
app_settings        key value
robot_commands      id child_id command_json timestamp status
test_results       id test_name status details timestamp
```

PIN hashed via SHA-256. JSON columns deserialized in helpers.

---

## 16. MEMORY — 3 LAYERS

| Layer | Storage | Lifetime |
|-------|---------|----------|
| Live state | `child_state` row | persists across sessions |
| Session | `messages` table for current `session_id` | until session ends |
| Long-term | `memories` table tagged by `memory_type` + importance | forever |

`MemoryEngine.apply_ai_memory_update(mu)` writes `current_emotion`, `current_need`, `stress_level`, `last_topic` to `child_state` every AI turn.

Example: child says "أنا جعان" → state.current_need='hungry'. Later child says "مش عايز اتكلم" → ARIA references the hunger in its reply.

---

## 17. INTENTS → TOOL MAPPING

| Intent | Tool opened |
|--------|------------|
| `need_food` | aac (food category) |
| `need_water` | aac (water category) |
| `need_bathroom` | aac (bathroom category) |
| `need_parent` | safety + parent alert |
| `pain` | safety + AAC pain board |
| `sad`, `angry`, `scared` | calm_zone |
| `overstimulated` | calm_zone (quiet sub-mode) |
| `open_calm_zone` | calm_zone |
| `open_aac` | aac |
| `open_schedule` | schedule |
| `open_tutorial` | tutorial (brush/wash decided from keywords) |
| `open_story` | story |
| `open_game` | game |
| `parent_mode` | parent_pin |
| `emergency` | safety + parent alert |
| `talk`, `unknown` | no tool, just reply |

---

## 18. DEMO SCENARIOS (must all pass automated tests)

1. **Child says "أنا جعان"** → "تمام، تحب أقول لماما إنك جعان؟", AAC food opens, state.current_need='hungry', auto-listening resumes.
2. **Child says "أنا زعلان ومش عايز أتكلم"** → calm reply, Calm Zone opens, robot face = sad_soft, listening resumes after safe.
3. **Child says "بعد كده إيه؟"** → Visual Schedule opens with NOW / NEXT / THEN cards.
4. **Child says "الولد ضربني في المدرسة"** → safe reply, parent_alert=true (bullying), Calm Zone opens, alert logged.
5. **Parent says "Open parent mode"** → PIN screen, on success Parent Dashboard opens, auto-listening paused.
6. **Child says "مش عارف أغسل سناني"** → Brushing tutorial opens.
7. **Child says "احكيلي قصة"** → Bedtime/social story screen opens with TTS narration.
8. **Child says "عايز ألعب"** → Games screen opens.
9. **No Claude API key** → ChainSelector skips Claude; MockAI or Groq serves; UI shows "Mock Mode" status.
10. **No ElevenLabs API key** → edge-tts serves; UI shows "edge-tts active".
11. **Camera face shows calm + Apple Watch BPM 145 + HRV 12 ms** → MultimodalFusion flags **masking**, suggests calm zone, parent alert.
12. **Franco-Arabic "ana ga3an"** → normalized to "أنا جعان" → need_food intent → AAC food.
13. **Hits 30 RPM Groq limit** → automatic fallback to Cerebras transparently.
14. **AI returns malformed JSON** → response_parser repairs / falls back to safe response, no crash, logs `parse_fallback`.

---

## 19. AUTOMATED TESTING

`python run_tests.py` runs all of `tests/` via `unittest`.

Coverage MUST include:
- **test_intents.py** — every intent listed above, in 3 languages + Franco-Arabic.
- **test_safety.py** — every category (NORMAL, SELF_HARM, ABUSE_RISK, MEDICAL_EMERGENCY, BULLYING, PAIN, HUNGER_THIRST).
- **test_memory.py** — state updates, AI memory apply, turn logging.
- **test_ai_shell.py** — JSON validation, MockAI scenarios for all demo cases.
- **test_tool_launcher.py** — every signal fires for the right input.
- **test_database.py** — schema exists, CRUD round-trips, settings round-trip.
- **test_robot_bridge.py** — command logged + emitted.
- **test_provider_fallback.py** — Claude missing → MockAI activates; ElevenLabs missing → edge-tts; invalid response caught.
- **test_auto_listening.py** — all state transitions reachable; safety/parent modes pause listening.
- **test_egyptian_polish.py** — MSA inputs produce Egyptian outputs.
- **test_multimodal_fusion.py** — masking detection, confirmed calm, confirmed distress.
- **test_safety_engine_arabic.py** — Arabic + Franco safety keywords match.
- **test_emotion_smoothing.py** — single frame doesn't trigger; sustained ≥3 frames does.
- **test_full_demo_flows.py** — end-to-end demos 1-14 above.

Parent Dashboard → Test Center surfaces results, saves to `test_results` table.

---

## 20. ENVIRONMENT (.env.example)

```
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=
ELEVENLABS_MODEL=eleven_multilingual_v2
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile
CEREBRAS_API_KEY=
CEREBRAS_MODEL=llama-3.3-70b
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
OPENROUTER_API_KEY=
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free
OLLAMA_ENABLED=false
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

**The app MUST start with zero keys** and run on MockAI + edge-tts/pyttsx3.

---

## 21. AI PROMPT — system prompt template

Stored in `config/prompts.json`. The provider builds it per turn with child profile + state injected.

Required directives:
- Speak the child's language. For `ar`, use warm Egyptian colloquial — NEVER MSA.
- 1-2 short sentences. Validate feelings first. Max ONE question.
- Use child's name and a soft endearment naturally ("يا حبيبي"/"sweetie") often.
- Match child's energy. Excited→excited, quiet→gentle.
- Use child's favorite topics from profile.
- NEVER sarcasm, lecture, shame, diagnose, recommend medical treatment.
- ONLY trigger `comfort_mode`/`open_tool="calm_zone"` for real distress (kid says "I want to cry", "everything is bad", repeated distress). Casual mention of a feeling → just curious follow-up.
- ONLY `parent_alert=true` for: self-harm, abuse, medical emergency, sustained crisis.
- Output ONLY JSON matching the schema. No markdown. No prose.

---

## 22. RESEARCH GROUNDING (every feature must cite a paper)

| Feature | Reference |
|---------|-----------|
| Visual Schedule | Knight et al., 2015; Bryan & Gast, 2000 |
| Visual Timer / Transitions | Dettmer et al., 2000; Waters et al., 2009 |
| AAC Builder | Ganz et al., 2012 (PECS meta-analysis); ASHA Practice Portal |
| Brown Noise / Sound Garden | Lucker, 2013 |
| Social Stories | Zhou et al., 2024; Como et al., 2023 |
| Feelings Thermometer | Buron & Curtis, 2012 (Incredible 5-Point Scale); Vanderbilt TRIAD, 2023 |
| Token Rewards / Star Jar | Kim et al., 2022; Fernandez et al., 2023 |
| Bedtime Story | Mindell et al., 2009 |
| Task Tutorials | Piccin et al., 2017 (video modeling); Davis (oral hygiene VM) |
| Calm Zone / Sensory Toolkit | Marco et al., 2011 (sensory processing in ASD) |
| Parent Dashboard | Cheng et al., 2022 (parent-implemented interventions meta-analysis); AFIRM 2025 |
| Mood Journal | NCAEP evidence-based practices (self-management) |
| Emotion CNN architecture | Sandler et al., 2018 (MobileNetV2) |
| STT | Radford et al., 2023 (Whisper) |
| Emotion-recognition caveats | Johnson et al., 2025 |
| Robot companion framing | Pennisi et al., 2016; Bartl-Pokorny et al., 2021; Pigureddu et al., 2025 |
| Egypt prevalence | Metwally et al., 2025 (1.1 % overall; 1.5 % ages 3-6) |
| Global prevalence | WHO 2025 (≈1 in 127 globally); CDC ADDM 2025 (1 in 31 U.S. 8-year-olds) |
| AI-robot autism learning gains | Tang et al., CHI 2024 — EmoEden +50 % emotion recognition over 22 days |
| NCAEP evidence base | Steinbrenner et al., 2020; Hume et al., 2021 |

**Safe wording rule** from the references map: "ARIA is built around evidence-based support strategies — not every feature is clinically proven by itself."

**Do NOT use:** the figure "250 million autistic people". Use **WHO 2025: ~1 in 127 globally** (~62 million) instead.

---

## 23. NUMBERS THAT MUST APPEAR (for the presentation slides + tech doc)

| Metric | Value |
|--------|-------|
| Egypt ASD prevalence (1-12 years) | **1.1 %** (Metwally 2025) |
| Egypt peak age group (3-6 years) | **1.5 %** |
| Egypt peak single year (6-7 years) | **1.69 %** |
| Egypt boys vs girls | **1.7 % vs 0.4 %** |
| Estimated Egyptian autistic children | **~437 K** (39.7 M × 1.1 %) |
| Therapy access in MENA | **< 1 %** |
| Global prevalence (WHO 2025) | **~1 in 127** |
| U.S. 8-year-olds (CDC 2025) | **1 in 31** |
| Groq latency | **~80 ms** median |
| Whisper Medium Arabic WER | **15.7 %** (vs Whisper base 31.5 %) |
| Egyptian dialect WER with primer | **~10-15 %** (informal user testing) |
| ElevenLabs MOS | **4.78 / 5** (Azure 4.21) |
| MobileNetV2 CPU latency | **~30 ms / frame** |
| RMSSD calm threshold | **>40 ms** healthy parasympathetic |
| RMSSD high stress | **<15 ms** sympathetic dominance |
| EmoEden study (Tang 2024) | **+50 % emotion recognition** after 22 days, p=0.0003 |

---

## 24. INSTALLATION & RUN

```
1. Install Python 3.11 from python.org (NOT Microsoft Store), check "Add to PATH"
2. Install FFmpeg, add C:\ffmpeg\bin to PATH
3. Install Visual Studio Build Tools → Desktop development with C++
4. pip install -r requirements.txt
5. (Optional) copy .env.example to .env and paste API keys
6. python main.py
```

**Tests:** `python run_tests.py`

**Troubleshooting:**
- App crashes on launch → check `crash.log`.
- No audio → Settings → AI & Voice → click "Test Voice".
- Mic not heard → Settings → Devices → click "Test Microphone" (3-sec recording shows peak RMS).
- Arabic STT poor → first run downloads Whisper Medium (1.5 GB), wait for "Whisper medium loaded ✓".
- AI keeps falling back to MockAI → check `crash.log` for HTTP 429 (quota) or auth errors; rotate keys in Settings.

---

## 25. QUALITY GATES (CI-style mental checklist before declaring done)

- [ ] `python main.py` launches the Shell directly (no dashboard first).
- [ ] App starts with NO `.env` and NO internet (MockAI + pyttsx3).
- [ ] Child never sees a button to start talking.
- [ ] First word of recorded speech is never lost.
- [ ] STT recognizes Egyptian phrases (e.g. "ضربوني", "بعد كده ايه؟", "ana ga3an").
- [ ] AI returns valid JSON for every demo input; validator never raises.
- [ ] Calm Zone, AAC, Schedule, Tutorials, Story, Games, Parent PIN, Settings each open and close cleanly.
- [ ] Multi-turn memory works ("I'm hungry" then "I'm angry" → ARIA references hunger).
- [ ] Robot command is logged + printed for every reply.
- [ ] Parent Dashboard PIN gate works (default 1234, hashed in DB).
- [ ] Test Center "Run All Tests" produces ≥95 % pass.
- [ ] No crashes when API key is wrong / network is down / Whisper model missing.
- [ ] No medical claims ("diagnose", "cure", "treat", "clinically proven") in any UI string.
- [ ] Egyptian Arabic outputs contain Egyptian markers (ايه/ازاي/دلوقتي/عايز/مش/يا حبيبي) and NO MSA markers (ماذا/كيف/الآن/أريد/ليس).
- [ ] Tech doc updated; presentation references include all citations above.
- [ ] App icon set generated for 16/32/48/64/128/256/512 px and `.ico`.

---

## 26. DELIVERABLES CHECKLIST

1. Full runnable project under `aria/` matching the structure in §3.
2. `requirements.txt` with pinned-ish versions.
3. `README.md` with install + run + troubleshooting.
4. `.env.example` with every supported key.
5. `run_tests.py` that runs all 14 test files.
6. In-app Test Center page (Parent Dashboard tab).
7. `presentation/ARIA_Presentation.pptx` matching the dark-navy + colored-circle design language.
8. `presentation/TECH_DOCUMENTATION.md` with all numbers + 30+ references.
9. `presentation/VIDEO_SCRIPT.md` for a 4-minute demo recording.
10. 20+ in-app screenshots in `presentation/screenshots/`.
11. Multi-resolution app icon under `assets/icons/`.
12. Demo scenarios 1-14 all working end-to-end.
13. Manual QA checklist printed as Markdown.

---

## 27. NON-NEGOTIABLES (do not ship without these)

- **Child experience is hands-free.** Period.
- **Egyptian Arabic feels native** — never news-anchor MSA.
- **No medical/diagnostic/therapy claims** anywhere in UI or docs.
- **Offline-first.** Works with zero API keys, zero internet.
- **Safety overrides everything.** A self-harm or abuse trigger silences casual chat and produces a parent alert.
- **Every feature has at least one passing automated test.**
- **Every screen returns cleanly** to the Shell without leaking timers/threads.
- **No untested dead buttons.** No fake navigation.

---

START NOW. First produce the file tree (already given above — confirm it). Then generate every file in §3, fully runnable, file by file, no placeholders or `# TODO` for the items in §12. Tests in §19 must actually pass.

ARIA OS is the shell. ARIA App is everything else inside it. The combined product is just **ARIA — Adaptive Robotic Interaction Assistant**.
