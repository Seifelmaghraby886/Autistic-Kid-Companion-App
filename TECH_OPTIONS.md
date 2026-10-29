# ARIA OS — Tech Options Considered (long list)

For each layer we surveyed the credible alternatives, then committed.
This is the "why we picked X, and what we knowingly rejected" reference
for the defence.

---

## TTS — text-to-speech

ARIA must speak in **natural Egyptian Arabic**, handle **English words
mixed inside Arabic sentences** (Arabic media is full of "okay", "online",
"yalla habibi"), carry warm **emotional inflection** for an autistic child,
and degrade gracefully when there's no internet.

### 1. Microsoft **edge-tts** (Azure Neural voices via the Bing endpoint)
* **Pros:** completely free, no API key, ships an Egyptian voice
  (`ar-EG-SalmaNeural`), simple HTTPS.
* **Cons:** robotic prosody; stumbles on English words inside Arabic; no
  emotional control.

### 2. **Google Cloud Text-to-Speech** (WaveNet / Neural2)
* **Pros:** generous free tier, world-class English voices.
* **Cons:** Google's Arabic voices are **MSA "news anchor"** dialect, not
  Egyptian colloquial — reads as foreign and cold for an Egyptian child.

### 3. **Amazon Polly** (Neural and Generative engines)
* **Pros:** mature API, decent Arabic ("Hala", "Zeina"), pay-as-you-go.
* **Cons:** Arabic voices are *Gulf*-flavoured, not Egyptian; emotional
  range is limited compared to ElevenLabs.

### 4. **OpenAI TTS** (`tts-1`, `tts-1-hd`, `gpt-4o-mini-tts`)
* **Pros:** smooth English, easy SDK already in the project.
* **Cons:** **doesn't speak Arabic naturally** — it phonetically renders
  Arabic in an English-sounding accent. Disqualified for our main language.

### 5. **Azure Speech** (proper paid Cognitive Services SDK)
* **Pros:** SSML control, neural styles ("cheerful", "calm"), corporate SLA.
* **Cons:** same underlying Egyptian voice as edge-tts but paid; the
  emotional styles are only available for a few languages, not Arabic.

### 6. **Coqui XTTS-v2** (self-hosted, open-source)
* **Pros:** runs offline, supports voice cloning, no API limits.
* **Cons:** **6 GB model**, GPU recommended, Arabic quality much worse
  than ElevenLabs, install pain on Windows.

### 7. **Piper TTS** (open-source, offline, very fast)
* **Pros:** small, CPU-only, no API, perfect for a Raspberry Pi.
* **Cons:** voices are clear but monotone; emotional warmth is absent.

### 8. **pyttsx3 / Windows SAPI** (offline last-resort)
* **Pros:** offline, no install, no key.
* **Cons:** the voice is *the* stereotype of a robot reading. Acceptable
  only as a safety net.

### ✓ **9. ElevenLabs `eleven_multilingual_v2`** — chosen
* **Pros:** Egyptian Arabic sounds **warm and human**, real emotional
  inflection, **code-switching just works** ("بحبك habibi 💙" is one
  sentence), free-tier voice IDs (Sarah, Laura, Matilda…) cover the demo.
* **Cons:** paid for the best voices; free-tier API has voice
  restrictions we route around in the code.

### Why ElevenLabs

The other eight are *fine* but **none of them are kind**. ARIA's whole
identity is a warm older-sibling voice speaking Egyptian Arabic, and
ElevenLabs is the only engine that does that today. We keep edge-tts as
the free fallback and pyttsx3 as the offline last resort, all toggleable
live in the Provider Control Center.

---

## Frontend — UI framework

The app must be a **fullscreen, frameless kiosk** with custom-painted faces
and particles, a **camera preview, mic-volume bar and AI thinking spinner**
all running together at 60 fps, native **Arabic right-to-left** support,
and a single window hosting 25+ tool screens by stack-swapping.

### 1. **Tkinter** (Python's standard-library GUI)
* **Pros:** ships with Python, no extra install.
* **Cons:** UI looks like Windows 95; custom paint is painful; no built-in
  animation system; Arabic RTL technically works but fights you; threading
  model is brittle when STT / camera / AI all update the UI.

### 2. **CustomTkinter** (modern look-and-feel wrapper)
* **Pros:** modern flat styling, dark mode, easy to start.
* **Cons:** still Tkinter underneath — same custom-paint limits, same
  thread issues, the styling is a thin coat.

### 3. **Kivy** (touch-first cross-platform Python)
* **Pros:** designed for touch and kiosk, OpenGL accelerated, good
  Android / iOS story for a later port.
* **Cons:** non-native widgets (everything is custom), the `kv` markup
  language is a second tool to learn, RTL has rough edges, integrating
  the standard PyAudio/cv2 windows is fiddly.

### 4. **wxPython**
* **Pros:** native widgets per OS, mature.
* **Cons:** weak custom-paint story compared to Qt; the API feels dated;
  smaller community than Qt for kiosk patterns.

### 5. **Dear PyGui** (immediate-mode GUI)
* **Pros:** very fast for dashboards / data visualisation, simple API.
* **Cons:** game-style immediate-mode rendering is a mismatch for an
  autistic-child app — every frame is redrawn, harder to keep calm and
  predictable; weak RTL.

### 6. **Electron + React / Next.js**
* **Pros:** the entire JavaScript / web ecosystem (charts, animations,
  every AAC template ever made).
* **Cons:** ships a private Chrome + Node → **200–400 MB RAM minimum**;
  local Python (Whisper, TensorFlow, OpenCV) must run as a sidecar over
  IPC. Three runtimes, double the failure modes.

### 7. **Tauri + Rust + web frontend**
* **Pros:** lighter than Electron (~10 MB binary, system webview).
* **Cons:** still requires a JS frontend + Rust bindings to Python for AI;
  immature ecosystem for camera and STT.

### 8. **Flutter / Dart**
* **Pros:** beautiful animations, single codebase for desktop + mobile.
* **Cons:** Dart, not Python — would require **rewriting every ML / AI
  / vision call** through native bindings. Massive scope blow-out for this
  project.

### 9. **.NET MAUI / WPF**
* **Pros:** native Windows, polished tooling.
* **Cons:** C#, not Python — same rewrite problem as Flutter, plus the
  AI/ML ecosystem in .NET is years behind Python.

### ✓ **10. PySide6 / Qt 6 (for Python)** — chosen
* **Pros:** native desktop performance, animations at 60 fps with
  particles + face + mic-bar + camera; **`QPainter` custom drawing** (the
  ARIA face, breathing circle, glassmorphic cards are *painted*, not
  images); **signals + threads** so STT / AI / camera talk to the UI
  safely; kiosk + RTL are stock Qt features.
* **Cons:** larger learning curve than Tkinter; LGPL licensing (we link,
  we don't statically embed — compliant).

### Why PySide6

It's the only framework in this list that lets us run **UI + AI + vision +
camera in a single Python process** with no IPC bridges, native
performance, real custom paint and true kiosk + RTL. One config flag
(`kiosk_mode`) switches between dev window and locked fullscreen.

---

## Backend — language, storage and architecture

"Backend" here = **runtime + data layer + business logic**. ARIA needs to
run ML workloads (Whisper STT, TensorFlow emotion CNN, OpenCV face
detection) on a normal laptop CPU; call seven AI vendor SDKs; persist
per-child memory, chat history, emotion logs, sessions safely across power
cuts; and keep working **offline** as much as physically possible.

### 1. **Node.js + JSON files**
* **Pros:** popular runtime; easy serialisation; same language as a web
  admin panel.
* **Cons:** **ML ecosystem on Node is poor** (no first-class
  faster-whisper, weak TF binding, OpenCV is a thin wrapper with constant
  build issues); JSON files have **no ACID**, a power-cut mid-write
  corrupts the profile; file-locking races.

### 2. **C# / .NET + SQL Server LocalDB**
* **Pros:** native Windows performance, mature toolchain.
* **Cons:** heavy install (.NET runtime + LocalDB); **AI/ML on C# is years
  behind Python** — you'd end up calling Python anyway. Cross-platform to
  Raspberry Pi / Jetson would be painful.

### 3. **Go + BoltDB / Badger**
* **Pros:** small binary, blazing fast, easy concurrency.
* **Cons:** Go's **AI / ML library scene is sparse**; no good Whisper or
  TensorFlow binding; UI bindings to Qt are clunky.

### 4. **Rust + `sled` / `rusqlite`**
* **Pros:** very fast, memory-safe, embedded DB excellent.
* **Cons:** same AI / ML problem — minimal mature bindings; building a
  desktop GUI in Rust still hurts; massive learning curve.

### 5. **Java / Kotlin + H2 / SQLite (JDBC)**
* **Pros:** mature, JVM is fast, decent ML libraries.
* **Cons:** ships an enormous JRE; awkward integration with Qt or the
  Python-only ML libraries we'd still need.

### 6. **Python + PostgreSQL** (proper relational server)
* **Pros:** rock-solid DB, SQL goodness, scales to many users.
* **Cons:** **massive overkill** for one family on one PC — needs a
  service running, port, install. Privacy headaches: a network DB on a
  child's device.

### 7. **Python + MongoDB**
* **Pros:** flexible JSON-native storage, popular.
* **Cons:** Mongo is a server too — same install / port problem as
  Postgres, plus weaker ACID guarantees.

### 8. **Firebase / Supabase (cloud BaaS)**
* **Pros:** zero server admin, auth + DB + storage out of the box.
* **Cons:** **cloud dependency for child data is the wrong tradeoff** —
  needs internet, raises privacy / GDPR / parental-consent issues,
  vendor-locked.

### 9. **Python + DuckDB**
* **Pros:** SQLite-style embedded database, blazing fast for analytics,
  excellent Python integration.
* **Cons:** designed for OLAP / column-store workloads (analytics) not the
  OLTP / row-store reads-writes we do per-conversation; ACID still
  evolving in 2025.

### 10. **Pure file system (per-profile folder of `.json` / `.txt`)**
* **Pros:** no DB at all, trivial to inspect.
* **Cons:** no transactions, no foreign keys, no queries — every list
  ("today's emotion logs") becomes a hand-written file walk. Doesn't scale
  past a toy.

### ✓ **11. Python 3.11 + SQLite + custom `core/` engine** — chosen
* **Pros:**
  * Python has the **strongest AI / ML ecosystem in the world** —
    `faster-whisper`, `tensorflow`, `opencv-python`, `anthropic`,
    `google-generativeai`, `groq`, `pygame`, `edge-tts` — all first-class.
  * **SQLite** ships in the standard library — zero install, **one file**
    (`database/aria.db`), **ACID-safe**, fast enough for one family, easy
    to back up by copying a file.
  * Our `core/` package is a small **custom OS engine** —
    `conversation.py`, `auto_listening_engine.py`, `intent_router.py`,
    `screen_voice.py`, `face_input.py`, `scan_mode.py`,
    `emotion_monitor.py`, `provider_control.py`, `log.py` — every layer is
    swappable in isolation.
* **Cons:** Python is not the fastest language and we ship a Python 3.11
  install; both irrelevant because the heavy lifting (cv2, ctranslate2 for
  Whisper, Qt) is native code under the hood.

### Why Python + SQLite + `core/`

**One language end-to-end** for UI, voice, vision, AI and DB — no IPC
bridges, no sidecars, no second runtime. SQLite gives us real database
guarantees in a single file the parent can back up. And the `core/`
engine lets us swap any AI provider, any TTS, any STT or any input
modality without touching the screens.

---

## Long-form summary table

| Layer | Options surveyed | Chosen | Deciding constraint |
|---|---|---|---|
| **TTS** | edge-tts · Google Cloud TTS · Amazon Polly · OpenAI TTS · Azure Speech · Coqui XTTS-v2 · Piper · pyttsx3 · **ElevenLabs** | **ElevenLabs `eleven_multilingual_v2`** | Only engine that delivers Egyptian Arabic that is *warm*, with English-in-Arabic code-switching and emotional inflection |
| **Frontend** | Tkinter · CustomTkinter · Kivy · wxPython · Dear PyGui · Electron+React · Tauri+Rust+web · Flutter · .NET MAUI · **PySide6** | **PySide6 / Qt 6** | Only framework letting us run UI + AI + vision + camera in **one Python process** at 60 fps with real kiosk + RTL |
| **Backend** | Node.js+JSON · C#/.NET+SQL Server · Go+BoltDB · Rust+sled · Java+H2 · Python+PostgreSQL · Python+MongoDB · Firebase/Supabase · Python+DuckDB · pure files · **Python+SQLite+`core/`** | **Python 3.11 + SQLite + custom `core/`** | Best AI ecosystem on Earth + zero-install ACID DB in one file + one language end-to-end + offline-first |
