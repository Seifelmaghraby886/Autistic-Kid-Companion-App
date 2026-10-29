# ARIA OS
**Adaptive Robotic Interaction Assistant — a voice-first AI companion for autistic children.**

A Windows desktop "operating app" that opens straight into ARIA's animated face. The child talks; ARIA listens, understands, replies, and opens any of 25+ tools by voice. The camera quietly notices the child's mood, and for non-verbal children ARIA reads the choices aloud and the child nods to pick. No mouse or keyboard required.

---

## What's in here

| Layer | Files |
|---|---|
| Entry / window | `main.py` — `ARIAMainWindow`, navigation, kiosk mode |
| **OS engines** | `core/conversation.py`, `core/auto_listening_engine.py`, `core/intent_router.py`, `core/screen_voice.py`, `core/face_input.py`, `core/scan_mode.py`, `core/emotion_monitor.py`, `core/provider_control.py`, `core/log.py` |
| Home shell | `ui/shell.py` — voice-first, hands-free home |
| 25+ tool screens | `ui/dashboard.py`, `ui/talk_screen.py`, `ui/calm_zone.py`, `ui/communication_board.py`, `ui/games.py`, etc. |
| Provider control | `ui/provider_center.py` — on/off toggles + API keys |
| Virtual keyboard | `ui/virtual_keyboard.py` — pops up on any text field in kiosk mode |
| AI / providers | `ai/multi_provider.py`, `ai/prompt_builder.py`, `ai/safety_filter.py`, `ai/response_parser.py` |
| Speech | `speech/stt_engine.py` (faster-whisper + Google), `speech/tts_engine.py` (ElevenLabs + edge-tts + pyttsx3) |
| Vision | `vision/face_detector.py`, `vision/emotion_predictor.py`, `vision/emotion_smoothing.py`, `vision/face_id.py` |
| DB | `database/db_manager.py` — SQLite (`aria.db`) |
| Config | `config/app_config.json` |
| Diagnostics | `aria_os.log` (rolling), `crash.log` (uncaught Python exceptions) |

The `aria_os/` folder is the older single-screen prototype; it's superseded by everything in `core/` and `ui/shell.py`. It can be removed; nothing in the live app imports from it.

## Run

```bat
run_aria.bat                       :: launches with the bundled Python 3.11
:: or
py -3.11 main.py
```

First run walks the parent through profile setup. After that, ARIA boots straight into the home shell.

### Kiosk vs. development mode

`config/app_config.json` -> `"kiosk_mode": true` (default) is frameless + fullscreen and pops the on-screen keyboard for any text field. Press **Esc** to exit, or use the **✕ Exit** button in the Provider Control Center.

Set `"kiosk_mode": false` for a normal resizable dev window.

## The voice loop

1. The home shell creates one **ConversationEngine** that survives screen changes.
2. The engine runs an **AutoListeningEngine** state machine (`IDLE -> LISTENING -> THINKING -> SPEAKING -> ...`) and pipes one `STTWorker` per turn.
3. Transcribed lines go to the **intent router** — explicit nav ("open games"), global commands ("go back", "stop") or conversation.
4. Conversation is multi-provider (Groq → Cerebras → Gemini → OpenRouter → Anthropic → OpenAI → Ollama), with per-child memory seeded from `chat_logs` and a 6-turn rolling history.
5. **TTS** prefers ElevenLabs when a key is present, else edge-tts (Egyptian Salma for Arabic, Jenny for English), else Windows SAPI. Emojis and markdown are stripped before speech.
6. A **TTS watchdog** prevents a stuck audio call from freezing the loop.
7. Inside a tool, the engine switches to **tool-voice mode**: `ScreenVoiceController` either fires `screen.go_back` or matches the spoken word to a visible button / clickable tile and activates it. This voice-enables all 25 screens generically.

## Camera

When `"face_input_enabled": true`, the home shell runs a lightweight camera thread:

- **Presence** — face seen for 0.8 s ⇒ ARIA wakes (resume listening). Face gone for 4 s ⇒ ARIA idles.
- **Head gestures** — nod / shake routed to whatever screen is open (used by the scan menu and the comfort offer card).

When a child profile's `communication_level == "non_verbal"`, the shell auto-starts a **scan menu** after the greeting: ARIA reads each home tile aloud, the child nods at the one they want. The picture/communication board is surfaced first because for a non-verbal child it *is* their voice.

`"ambient_emotion_enabled"` is off by default (TF inference in a background thread proved fragile). The on-demand Emotion Room screen still works for the live emotion demo.

## Provider Control Center

The **⚙ Setup** button on the home shell, or saying "ARIA, open the control center", opens a screen with an on/off switch *and* an editable API-key field for every provider — Groq, Cerebras, Gemini, OpenRouter, Anthropic, OpenAI, ElevenLabs — plus toggles for the TTS engines (ElevenLabs / Edge-TTS / Windows SAPI) and STT engines (Whisper / Google Speech). Changes take effect on the very next request, no restart.

State persists in `config/app_config.json` -> `"providers_enabled"`.

## ElevenLabs (free tier)

The default voice ID is **`EXAVITQu4vr4xnSDxMaL` (Sarah)** — one of the few ElevenLabs default voices a free plan may use via the API. Other free-tier-allowed voices: Laura, Alice, Matilda, Lily, Jessica. Library voices and most premium voices return HTTP 402 on free plans — ARIA falls back to edge-tts automatically when that happens.

Audio samples for each voice are in `voice_samples/`.

## Demo flow

The grad-review demo this app was built for:

1. Launch — ARIA boots into the home shell, greets the active child by name.
2. The child says **"I'm hungry"** — ARIA replies kindly and remembers.
3. Later the child asks **"What should I do?"** — ARIA recalls the hunger and suggests asking a parent or checking the snack routine.
4. The camera notices sustained sadness — a gentle Calm Zone card appears; the child nods or taps.
5. The Calm Zone runs a breathing exercise. The parent dashboard shows the emotion log, the chat history and ARIA's memory.

Every step is logged to `aria_os.log` with timestamps, so the demo is self-narrating.

## See also

- **`TESTING.md`** — full testing checklist matching the master spec.
- **`crash.log`** — Python tracebacks from past runs (rotated by appending).
- **`aria_os.log`** — `[ARIA-OS]` diagnostic stream from every session.
