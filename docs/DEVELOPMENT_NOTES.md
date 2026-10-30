# Wanees — development notes

Read this first when picking the project up on a new machine (e.g. the
Raspberry Pi inside the robot).

## What the app is

Wanees (code name ARIA) is a voice-first companion for autistic children,
built in Python 3.11 + PySide6. On the robot it boots straight into the
voice home screen (`ui/shell.py`): ARIA greets the child by name and
listens. Children are assumed to be pre-readers, so everything is reachable
by voice, by big emoji tiles, or (for non-verbal children) by a scan menu
where ARIA reads options aloud and the child nods.

Key modules:

| Area | Files |
|---|---|
| Entry, navigation, boot flow | `main.py` (`_navigate`, `_switch_to`, `_on_splash_done`) |
| Voice loop | `core/conversation.py`, `core/auto_listening_engine.py`, `core/intent_router.py` |
| Session "brain" (context, suggestions, stars, memory) | `core/child_context.py` |
| Camera presence + nod/shake | `core/face_input.py`, `vision/camera.py` |
| AI providers (fallback chain) | `ai/multi_provider.py`, `ai/prompt_builder.py`, `ai/safety_filter.py` |
| Speech | `speech/stt_engine.py` (Whisper / Google), `speech/tts_engine.py` (ElevenLabs / edge-tts / pyttsx3) |
| API keys | `core/secrets.py` — keys live in `.env`, never in `config/app_config.json` |
| Data | `database/db_manager.py` → `database/aria.db` (SQLite, not in git) |

## API keys

`config/app_config.json` is committed to a public repo, so its key fields
are always empty. Real keys go in a git-ignored `.env` in the project root,
one per line:

```
gemini_api_key=...
groq_api_key=...
cerebras_api_key=...
elevenlabs_api_key=...
anthropic_api_key=...
```

`core/secrets.py` merges `.env` into the config on every load, and moves
any key typed into Settings / the Control Center into `.env` on save.
Without a `.env` the app still runs, but with rule-based replies and the
robotic offline voice.

## Raspberry Pi setup

Target: Raspberry Pi 5 (8 GB), Raspberry Pi OS **64-bit**, USB webcam,
USB microphone, speaker.

1. `bash deploy/setup_pi.sh` — installs system packages (emoji + Arabic
   fonts, audio libs, espeak-ng), creates `.venv`, installs requirements,
   turns on reduce-motion / kiosk / auto-start, registers autostart on boot.
2. Create `.env` (see above).
3. Optional: copy `database/aria.db` from the PC to keep existing child
   profiles. Without it, first launch runs the parent setup screens.
4. `./run_aria.sh` to test, then `sudo reboot` — the app opens by itself.

Pi-specific behaviour already in the code:
- `vision/camera.py` uses V4L2 on Linux (DirectShow only on Windows).
- `speech/stt_engine.py` picks Whisper `small` (Arabic) / `base` (others)
  on ARM instead of `medium`/`small`; override with `"whisper_model"` in
  `config/app_config.json`.
- First launch downloads the Whisper model (~500 MB) — needs internet.

## Not yet verified on real Pi hardware

Everything above was written and tested on Windows only. Things to check
on the first Pi run:
- Camera opens (`v4l2-ctl --list-devices`). The ribbon-cable Pi Camera
  Module goes through libcamera and is NOT supported by this code — use a
  USB webcam.
- Microphone is picked up (`arecord -l`) and STT latency is acceptable.
- Emoji tiles render (needs `fonts-noto-color-emoji`).
- TensorFlow installed (only the camera emotion screens need it).
- UI is smooth enough with `reduce_motion` on.

## Checking the app

```
python scripts/qa_import_sweep.py        # every module imports
python scripts/qa_core_engines.py        # router, gestures, scan mode, context, memory
python scripts/qa_screen_construction.py # all 27 screens build
python scripts/qa_boot_test.py           # full boot, crash.log must not grow
```

All four pass on Windows as of these notes. Uncaught exceptions land in
`crash.log`; the voice loop logs to `aria_os.log`.
