# ARIA OS — Tech Choices

A short reference for the graduation defence: every piece of the stack and **why** we picked it.

---

## What ARIA is

A Windows desktop "operating app" — voice-first, hands-free, camera-aware — for autistic children.
The whole experience runs in one fullscreen window the child never has to leave.

---

## Language: Python 3.11

We use **Python** because everything ARIA needs lives in Python: the strongest AI / machine-learning ecosystem in the world (TensorFlow, OpenCV, Whisper, Anthropic/OpenAI/Google SDKs), Qt bindings (PySide6) that match C++ Qt feature-for-feature, and rapid iteration on a single codebase that mixes UI, vision, speech and AI.

Specifically **Python 3.11** because all the heavy libraries we depend on (TensorFlow, faster-whisper, PySide6, opencv-contrib) have stable, well-tested wheels for it on Windows.

---

## Frontend: PySide6 (Qt 6 for Python)

We use **PySide6** for every screen in the app. Why:

* **Native desktop performance.** Qt is a real GUI toolkit — animations stay 60 fps even with the particle background, the animated ARIA face, the camera preview and the live mic-volume bar all running.
* **Custom drawing.** ARIA's holographic face, the breathing circle in the Calm Zone and the glassmorphic cards are all painted with `QPainter` — no images, no web view, perfectly crisp at any size.
* **Touch / kiosk first.** Frameless fullscreen, on-screen keyboard for text fields, big touch tiles — all stock Qt features. The same code runs as a normal windowed dev app or a locked-down kiosk just by flipping `kiosk_mode` in the config.
* **Signals + threads.** Voice, camera and AI all run in background threads but talk to the UI safely through Qt's signal/slot system. No race conditions, no UI freezes.

A web stack (React / Electron) would have given us a smaller community for accessibility patterns, much higher RAM, no real way to ship the camera + STT in one process, and worse Arabic RTL handling.

---

## Storage: SQLite (one file)

Per-child memory, chat logs, emotion logs, sessions, parent PINs and device settings all live in **`database/aria.db`** through Python's stdlib `sqlite3`.

Why:

* **Zero install** — SQLite is part of the standard library.
* **One file** — easy to back up, easy to inspect with any DB browser.
* **ACID** — a power-cut mid-session never corrupts a profile.
* **Plenty fast** for one family's worth of conversations.

A real server (Postgres, Mongo, Firebase) would add deployment complexity, a network dependency, and privacy headaches for a child-facing offline-capable app.

---

## App architecture: a custom "OS" in `core/`

The `core/` package is the operating-app shell:

| Module | Job |
|---|---|
| `conversation.py` | The brain — orchestrates STT → AI → TTS, owns multi-turn memory |
| `auto_listening_engine.py` | Continuous hands-free microphone with a state machine |
| `intent_router.py` | Turns a spoken line into navigation / command / talk |
| `screen_voice.py` | Voice-controls every tool screen generically by matching spoken words to visible buttons |
| `face_input.py` | Camera presence, look-to-listen and head-nod / shake gestures |
| `scan_mode.py` | Choice scanning for non-verbal children — ARIA reads each option, child nods to pick |
| `emotion_monitor.py` | Quietly notices the child's mood from the camera |
| `provider_control.py` | On/off toggles + API keys for every AI / TTS / STT provider |
| `log.py` | One shared diagnostic log (`aria_os.log`) every module writes to |

This separation means we can swap any provider, any model or any input modality without touching the screens.

---

## AI: a multi-provider fallback chain

ARIA's conversation engine never depends on a single AI vendor. Each spoken line is tried against this chain, in order, until one succeeds:

```
Groq  →  Cerebras  →  Google Gemini  →  OpenRouter  →
Anthropic Claude  →  OpenAI GPT  →  local Ollama
```

The chain is configurable in the **Provider Control Center** screen — every provider has an on/off toggle and an editable API-key field, so a parent can flip providers live without restarting the app.

### Why each is in the chain

* **Groq (Llama 3.3 70B)** — currently the *primary* during development. Free tier, blistering speed (~300 tok/s), works very well in Egyptian Arabic. Perfect for iterating on prompts.
* **Cerebras (Llama 3.3)** — secondary free fallback. Even faster than Groq, smaller daily quota.
* **Google Gemini 2.5 Flash** — free, generous quota, strong vision model — useful for the camera-based emotion descriptions.
* **OpenRouter** — gateway to a huge catalogue of free models, including community fine-tunes if Llama ever stops working for us.
* **Anthropic Claude** — **the target "main" provider for the final version.** Best instruction-following for our strict JSON output contract, best safety alignment for a child-facing companion, the warmest emotional tone in our blind tests of Egyptian Arabic replies, and the strongest at following long structured prompts (the per-child memory + safety + dialect rules).
* **OpenAI GPT-4o-mini** — credible alternative if Anthropic is unavailable.
* **Ollama (local)** — offline emergency mode. Privacy-preserving, no internet needed, runs `llama3.2:3b` on the parent's machine.

### Why Claude is the chosen main provider

* The system prompt is ~3 KB of Egyptian-Arabic dialect rules, child profile, memory, safety constraints, and a JSON output schema. **Claude is measurably the best at following all of that simultaneously.**
* Anthropic's safety alignment is the most appropriate for a tool used by autistic children — the refusals and tone match the use case.
* It handles Egyptian Arabic + endearments + emojis + JSON-strict-output better than the alternatives.
* Long-context: the per-child memory plus 6-turn rolling history fits with room to spare.

---

## Voice out (TTS): ElevenLabs → edge-tts → Windows SAPI

We try ElevenLabs first when an API key is present, then fall back automatically. Why each:

* **ElevenLabs `eleven_multilingual_v2`** — *the* answer for the question "make her sound human in Egyptian Arabic". It:
  * speaks Egyptian Arabic naturally (not the robotic MSA most TTS engines fall back to);
  * handles **code-switching** — English words mid-Arabic sentence sound right;
  * carries emotional inflection (warm, calm, gentle), which matters enormously for an autistic child;
  * has voice IDs that work on the free tier (Sarah, Laura, Matilda, etc.) so the demo doesn't require a paid plan.
* **edge-tts (Microsoft Azure Neural voices via Bing)** — free, no key needed, decent quality. The Egyptian voice (`ar-EG-SalmaNeural`) is the best free option for Arabic. We use it whenever ElevenLabs isn't configured or rejects a request (the free tier has voice restrictions).
* **pyttsx3 (Windows SAPI)** — last-resort offline fallback so ARIA still has a voice even with no internet.

All emojis and markdown are stripped *before* the text reaches TTS, so the voice never spells "💙" out as "blue heart".

---

## Voice in (STT): Whisper + Google Speech

* **`faster-whisper` (medium model for Arabic, base for English)** — runs *offline* on the CPU, uses Egyptian-Arabic vocabulary as an initial prompt, and is dramatically better than online STT at dialect. This is what gives ARIA real Egyptian-Arabic understanding.
* **`SpeechRecognition` (Google Speech)** — used as a fast first-pass for English / German. Faster than Whisper for clean English speech, free at this volume.

The conversation engine wraps both in an `STTWorker` with **voice-activity detection** so it knows when the child has finished speaking — no "press to talk", no stuck-listening.

---

## Vision: OpenCV + a custom Keras emotion CNN

* **OpenCV (`opencv-python`)** — face detection (Haar cascade), camera frame capture, image preprocessing. It's the standard, it's free, it doesn't need a GPU, and Haar runs at 30 fps on any laptop.
* **Custom CNN (`models/emotion_model.h5`)** — a small Keras model trained on a combined emotion dataset (six emotions: anger, fear, joy, neutral, sadness, surprise). The `.tflite` export is what we'd ship to a Raspberry Pi or Jetson.
* **`EmotionSmoother`** — a 5-second sliding-window majority vote on top, so the system reacts to *settled* moods, not single-frame jitter (an autistic child blinking once mustn't be misread as "scared").

For the future "face login" feature we wrote `vision/face_id.py` to be **dependency-free** (ORB feature matching), with an automatic upgrade to OpenCV LBPH if `opencv-contrib-python` is ever installed. That avoids the heavy `dlib` dependency entirely.

---

## Audio plumbing: pygame.mixer + PyAudio

* **pygame.mixer** — plays the mp3 files generated by ElevenLabs / edge-tts. We chose pygame over `playsound` or `sounddevice` because `mixer.music.get_busy()` gives us a perfectly reliable "is it still talking?" signal we need to keep the conversation loop synchronous.
* **PyAudio** — direct microphone access for the STT input loop. Low-latency, can address a specific input device (so a parent can pick a USB mic if the laptop one is bad), and provides the raw 16 kHz mono int16 stream Whisper expects.

---

## Games: built directly in PySide6, by design

`ui/games.py` is ~1200 lines of pure PySide6 — every game (emotion matching, social story choices, daily routine ordering, calm puzzle, colour & shape, etc.) is a `QWidget` with custom paint and Qt animations.

Why not Pygame / a game engine:

* **Visual coherence.** The games share the exact same glassmorphic card style, fonts, colours and animations as the rest of ARIA. A child can't tell where the app ends and a game begins. That continuity matters for an autistic child.
* **No context switch.** Same window, same input, same back-out by voice. Pygame would mean a separate window with its own event loop.
* **The games are *deliberately calm*.** No timers, no flashing, no twitch reflexes — none of the things a game engine optimises for. PySide6 is perfect.
* **One language, one toolchain.** No SDL, no game-engine learning curve, no extra dependency.

---

## Kiosk mode

When `kiosk_mode: true` (the default):

* The main window is **frameless and fullscreen** — ARIA owns the whole screen like an OS.
* An **on-screen keyboard** (`ui/virtual_keyboard.py`) pops up for every text field — QWERTY for English/Arabic, big number pad for the parent PIN, all touch.
* **Esc** still exits. A discreet **✕ Exit** button lives inside the Provider Control Center.

Why a custom virtual keyboard instead of the built-in Windows on-screen one: ours uses `Qt.WA_ShowWithoutActivating` + `Qt.NoFocus` keys so the focused text field never loses the caret — typing always goes into the right widget.

---

## Head gestures and look-to-listen — *why this matters*

Many autistic children are non-verbal, or speak only with effort. They still have things to say.

* The camera detects **presence** (face seen ≥ 0.8 s → ARIA wakes), **looking** (face centred ≥ 0.5 s → start a listening turn), and **nod / shake** gestures (with a pure, unit-testable `analyze_gesture()` that measures axis-dominant oscillation in the face-box centre).
* A **`ScanController`** reads choices aloud one at a time, and the child nods on the one they want. Standard switch-access pattern — the camera *is* the switch.
* For a non-verbal child the home screen surfaces the **Picture / Communication board first**, because for them that board *is* their voice.

This is the part of ARIA the grad demo really pivots on: the same app is voice-first for a verbal child and gesture-first for a non-verbal child, with no setting to flip — it just adapts to the child's profile.

---

## Diagnostics: one log file

Every module of `core/` and the UI uses `core.log.log()`, which writes to **`aria_os.log`** alongside the existing `crash.log`. The log narrates the entire pipeline:

```
[ARIA-OS] ConversationEngine.start() — ARIA will greet, then listen
[ARIA-OS] greeting (ar)
[ARIA-OS] speaking (59 chars, style=soft)
[ARIA-OS] face input: camera on (presence + look + gestures)
[ARIA-OS] presence: a child is here
[ARIA-OS] auto-listen: heard -> 'انا جعان'
[ARIA-OS] routed 'انا جعان' -> (talk, انا جعان)
[ARIA-OS] thinking… (asking the AI companion)
[ARIA-OS] AI replied: 'يا قلبي إنت جعان؟ تحب نقول لماما؟ ✨'
[ARIA-OS] speaking (38 chars, style=soft)
[ARIA-OS] speech finished
```

If anything goes wrong, the answer is in there.

---

## Summary table

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.11 | Best AI ecosystem, one codebase for UI + vision + speech |
| UI | PySide6 / Qt 6 | Native perf, custom paint, kiosk-ready, threading-safe |
| Storage | SQLite | Zero install, one file, ACID, fast enough |
| AI (main) | **Anthropic Claude** | Best at structured prompts + dialect + safety |
| AI (fallback) | Groq, Cerebras, Gemini, OpenRouter, OpenAI, Ollama | Free dev tiers, redundancy, offline mode |
| TTS (main) | **ElevenLabs multilingual v2** | Natural Egyptian Arabic + code-switching + emotion |
| TTS (fallback) | edge-tts → pyttsx3 | Free Arabic voice → offline last resort |
| STT (Arabic) | faster-whisper (medium) | Offline, dialect-aware via Egyptian prompt |
| STT (English) | Google Speech Recognition | Fast, free, fine for clean English |
| Vision | OpenCV + Keras CNN | Free, CPU-only, Haar at 30 fps, custom emotion model |
| Camera input | `face_input.py` (presence / look / gestures) | Hands-free access for non-verbal children |
| Audio out | pygame.mixer | Reliable "is it still talking?" signal |
| Audio in | PyAudio | Direct device access, 16 kHz mono for Whisper |
| Games | Pure PySide6 | Visual continuity, calm/no-twitch, one toolchain |
| Kiosk | Frameless + virtual keyboard | True OS feel, no mouse/keyboard needed |
| Logging | one `aria_os.log` | The whole pipeline narrates itself |
