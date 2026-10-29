# ARIA OS — System Flowchart

The complete data-flow of the running app, end-to-end. Hardware on the
outside, the conversation loop in the middle, storage and UI on the sides.

> 💡 **For a high-resolution slide/poster image:** copy the `mermaid` block
> below into <https://mermaid.live> and export as SVG or PNG.
> The whole diagram renders in GitHub and VSCode (with the Mermaid
> extension) as-is.

---

```mermaid
graph TD
    %% ─── HARDWARE (outside the app) ────────────────────────────────────
    MIC([🎙 Microphone<br/>PyAudio 16 kHz mono])
    CAM([📷 Camera<br/>cv2.VideoCapture])
    TOUCH([👆 Touch / Mouse])
    SPK([🔊 Speakers<br/>pygame.mixer])
    DISP([🖥 Screen<br/>fullscreen kiosk])

    %% ─── BOOT FLOW ────────────────────────────────────────────────────
    subgraph BOOT["BOOT — main.py"]
        direction TB
        MAIN[main is run]
        SPLASH[Splash · 5s]
        CHECK{first_run?}
        SETUP[Parent + Child<br/>profile wizard]
        WELCOME[WelcomeBackScreen<br/>pick a child]
        OPEN[Open ARIAShell · home]
    end
    MAIN --> SPLASH --> CHECK
    CHECK -- yes --> SETUP --> OPEN
    CHECK -- no  --> WELCOME --> OPEN

    %% ─── CAMERA PIPELINE (background thread on the shell) ─────────────
    subgraph CAMP["CAMERA PIPELINE — face_input + emotion_monitor"]
        direction TB
        FD[FaceDetector<br/>Haar cascade]
        PR{Face held<br/>≥ 0.8 s?}
        GA[analyze_gesture<br/>amp + osc]
        GS{Nod or<br/>shake?}
        EP[EmotionPredictor<br/>Keras CNN]
        ES[EmotionSmoother<br/>6 s window]
        DS{Sustained<br/>sad / fear /<br/>anger?}
    end
    CAM --> FD
    FD --> PR
    FD --> GA --> GS
    FD --> EP --> ES --> DS

    %% ─── VOICE LOOP (when present) ────────────────────────────────────
    subgraph VL["VOICE LOOP — conversation + auto_listening + intent_router"]
        direction TB
        STT[AutoListeningEngine<br/>STTWorker · VAD]
        WSP[faster-whisper<br/>medium · Arabic]
        GSR[Google Speech<br/>English / German]
        TX[Transcript text]
        IR[IntentRouter.route]
        DEC{navigate?<br/>command?<br/>talk?}
    end
    STT --> MIC
    MIC --> WSP
    MIC --> GSR
    WSP --> TX
    GSR --> TX
    TX --> IR --> DEC

    %% ─── AI PROVIDER CHAIN ────────────────────────────────────────────
    THINK[ConversationEngine<br/>_think text · memory + emotion + history]
    subgraph AICHAIN["AI MULTI-PROVIDER CHAIN — multi_provider.py"]
        direction TB
        G[Groq · Llama 3.3 70B<br/>FREE primary]
        CB[Cerebras · Llama 3.3]
        GM[Google Gemini 2.5 Flash]
        ORT[OpenRouter]
        CL[Anthropic Claude<br/>★ TARGET MAIN]
        GP[OpenAI GPT-4o-mini]
        OL[Ollama · local 3 B]
        G   -- fail --> CB
        CB  -- fail --> GM
        GM  -- fail --> ORT
        ORT -- fail --> CL
        CL  -- fail --> GP
        GP  -- fail --> OL
    end
    THINK --> G
    G   --> JSON
    CB  --> JSON
    GM  --> JSON
    ORT --> JSON
    CL  --> JSON
    GP  --> JSON
    OL  --> JSON

    JSON[Response JSON<br/>reply · face_expression<br/>suggested_activity<br/>comfort_mode · parent_alert<br/>memory_update]

    %% ─── TTS CHAIN ────────────────────────────────────────────────────
    CLEAN[strip emoji + markdown]
    subgraph TC["TTS CHAIN — tts_engine.py + watchdog"]
        direction TB
        EL[ElevenLabs<br/>multilingual_v2<br/>★ MAIN voice]
        ET[edge-tts · Salma EG<br/>FREE]
        PT[pyttsx3<br/>offline last resort]
        EL -- fail --> ET
        ET -- fail --> PT
    end
    MP3[mp3 file]
    PYG[pygame.mixer · play]
    AF[_after_speech<br/>+ TTS watchdog]

    JSON --> CLEAN --> EL
    EL --> MP3
    ET --> MP3
    MP3 --> PYG --> SPK
    PT --> SPK
    PYG -- speech finished --> AF
    AF -- active --> STT

    %% ─── ROUTING DECISIONS ────────────────────────────────────────────
    DEC -- "I am hungry…"               --> THINK
    DEC -- "ARIA, open games"           --> NAV[main._navigate]
    DEC -- "go back" / "stop"           --> CMD[global command]
    CMD -- stop  --> STOPTTS[stop TTS] --> STT
    CMD -- back  --> NAV

    %% ─── 25 TOOL SCREENS ──────────────────────────────────────────────
    subgraph TOOLBOX["25 TOOL SCREENS (one window, stack-swapped)"]
        direction LR
        GAMES[Games]
        CALM[Calm Zone]
        SCHED[Visual Schedule]
        AACS[Communication Board]
        STORY[Stories]
        COACH[Coach]
        OTHER[· · · 19 more]
    end
    NAV --> TOOLBOX
    TOUCH --> NAV

    %% ─── TOOL-VOICE (works on every screen) ───────────────────────────
    SVC[ScreenVoiceController<br/>word → button match]
    TX -. while a tool is open .-> SVC
    SVC -- click --> TOOLBOX

    %% ─── CAMERA OUTPUTS WIRE BACK INTO THE LOOP ───────────────────────
    PR -- present       --> RES[ConvEngine.resume_listening]
    PR -- gone 4 s      --> PAU[ConvEngine.pause_listening]
    RES --> STT
    PAU -. mute .-> STT
    GS -- nod / shake --> SG[current_screen.on_gesture]
    SG --> SHELL
    DS -- yes           --> COMF[Comfort Card<br/>+ ARIA speaks gently]
    COMF -- tap Calm Zone --> NAV
    COMF -- tap I'm okay  --> SHELL

    %% ─── HOME SHELL (the home screen) ─────────────────────────────────
    SHELL[ARIAShell<br/>face · status · mic bar<br/>presence badge · tap-to-talk<br/>6 home tiles · ⚙ Setup · 👤 Parent]
    OPEN --> SHELL
    JSON -- aria_replied      --> SHELL
    ES   -- emotion_updated   --> SHELL
    PR   -- presence_changed  --> SHELL
    SHELL --> DISP
    TOOLBOX --> DISP

    %% ─── PARENT + DEV PATH ────────────────────────────────────────────
    SHELL -- tap 👤 Parent --> PIN[Parent PIN<br/>on-screen numpad]
    PIN -- correct --> PD[Parent Dashboard<br/>chat logs · emotion logs<br/>sessions · memory · alerts]
    SHELL -- tap ⚙ Setup --> PROV[Provider Control Center<br/>on/off toggle + editable API key<br/>per AI / TTS / STT]

    %% ─── STORAGE ──────────────────────────────────────────────────────
    subgraph STORE["STORAGE"]
        direction TB
        DB[(SQLite<br/>database/aria.db)]
        CFG[(config/app_config.json)]
        LOG[(aria_os.log)]
    end
    JSON --> MEM[update_ai_memory] --> DB
    JSON --> CHAT[log_chat] --> DB
    ES   --> EM[log_emotion]  --> DB
    PROV --> CFG
    AICHAIN -. reads .-> CFG
    TC      -. reads .-> CFG
    PD      -. reads .-> DB

    %% Every module writes to one shared diagnostic file
    STT      -. log .-> LOG
    AICHAIN  -. log .-> LOG
    TC       -. log .-> LOG
    CAMP     -. log .-> LOG
    SHELL    -. log .-> LOG

    %% ─── STYLE ────────────────────────────────────────────────────────
    classDef hw    fill:#fce4ec,stroke:#c2185b,color:#000;
    classDef ai    fill:#e1f5fe,stroke:#0277bd,color:#000;
    classDef tts   fill:#fff3e0,stroke:#ef6c00,color:#000;
    classDef store fill:#f3e5f5,stroke:#6a1b9a,color:#000;
    classDef ui    fill:#e8f5e9,stroke:#2e7d32,color:#000;
    classDef cam   fill:#fffde7,stroke:#f9a825,color:#000;
    classDef key   fill:#ffe0b2,stroke:#bf360c,color:#000,stroke-width:3px;

    class MIC,CAM,TOUCH,SPK,DISP hw
    class THINK,JSON,G,CB,GM,ORT,GP,OL ai
    class CL key
    class EL key
    class ET,PT,MP3,PYG,CLEAN,AF tts
    class DB,CFG,LOG,MEM,CHAT,EM store
    class SHELL,TOOLBOX,GAMES,CALM,SCHED,AACS,STORY,COACH,OTHER,PROV,PD,PIN,SVC,NAV,SG,COMF ui
    class FD,PR,GA,GS,EP,ES,DS,RES,PAU cam
```

---

## How to read it

The chart has **six colour-coded swim lanes**:

| Colour | What it is |
|---|---|
| 🟪 Pink  | **Hardware** — mic, camera, touch, speakers, screen |
| 🟦 Blue  | **AI** — the multi-provider chain + ConversationEngine |
| 🟧 Orange| **TTS** — ElevenLabs → edge-tts → pyttsx3 + the pygame player |
| 🟪 Purple| **Storage** — SQLite, JSON config, the diagnostic log |
| 🟩 Green | **UI** — the home shell, the 25 tool screens, parent dashboard, provider centre |
| 🟨 Yellow| **Camera pipeline** — face detection, presence, gestures, emotion |
| 🟫 **Thick orange border** | the two **chosen "main" engines** — Claude and ElevenLabs |

---

## The two main loops (read the chart along these)

### 1. The conversation loop (when the child is present)

```
camera sees face (0.8 s)
   ↓
resume listening  ──►  STTWorker opens mic
                              ↓
                        Whisper / Google → transcript
                              ↓
                        IntentRouter decides:
                          • "ARIA, open games" → navigate
                          • "go back" / "stop"  → command
                          • everything else      → talk
                              ↓ (talk)
                        ConversationEngine._think
                              ↓
                        AI chain: Groq → Cerebras → Gemini → OpenRouter
                                  → Claude → GPT → Ollama  (first success wins)
                              ↓
                        JSON response (reply + emotion + activity + memory)
                              ↓
                        log_chat + update_ai_memory → SQLite
                              ↓
                        strip emoji/markdown → ElevenLabs → mp3 → pygame
                              ↓ speech finished (watchdog covers hangs)
                        _after_speech → open mic again ⤴
```

### 2. The camera loop (every frame on the shell)

```
camera frame
   ↓
FaceDetector (Haar)
   ├── face held ≥ 0.8 s   → presence True  → resume listening
   ├── face gone 4 s       → presence False → pause listening
   ├── analyze_gesture     → nod / shake    → current screen.on_gesture
   └── Keras emotion CNN   → smoother (6 s) → if sad/fear/anger
                                              → log_emotion → comfort card
                                              → ARIA gently offers Calm Zone
```

The two loops run in parallel — the camera supplies wake/idle signals and
mood data, the voice loop handles the actual dialogue.

---

## Where every important file lives in the diagram

| Module | What part of the chart |
|---|---|
| `main.py` | the BOOT box + `_navigate` + the `_on_…` handlers |
| `ui/shell.py` | the SHELL node (presence badge, tap-to-talk, tiles) |
| `core/conversation.py` | the THINK / `_after_speech` / TTS watchdog plumbing |
| `core/auto_listening_engine.py` | STT inside the VOICE LOOP subgraph |
| `core/intent_router.py` | `IntentRouter.route` + the DEC diamond |
| `core/screen_voice.py` | the `ScreenVoiceController` node |
| `core/face_input.py` | FaceDetector, presence, analyze_gesture inside CAMERA PIPELINE |
| `core/emotion_monitor.py` | EmotionPredictor + EmotionSmoother in CAMERA PIPELINE |
| `core/scan_mode.py` | feeds `on_gesture` for non-verbal scanning |
| `core/provider_control.py` | the lock between `Provider Control Center` and `app_config.json` |
| `core/log.py` | the `aria_os.log` cylinder |
| `ai/multi_provider.py` | the entire AI CHAIN subgraph |
| `speech/stt_engine.py` | STTWorker + Whisper + Google nodes |
| `speech/tts_engine.py` | the TTS CHAIN subgraph + pygame |
| `vision/face_detector.py` | the FaceDetector node |
| `vision/emotion_predictor.py` | the EmotionPredictor node |
| `database/db_manager.py` | every arrow that reaches `aria.db` |
| `ui/provider_center.py` | the Provider Control Center node |
| `ui/communication_board.py`, `ui/games.py`, `ui/calm_zone.py`, … | the TOOLBOX subgraph |

---

## Defending the diagram in one sentence

> *"A single PySide6 window hosts everything; the camera continuously
> supplies presence/mood/gesture signals, the microphone drives an
> always-listening STT cycle, every spoken line is classified by the
> intent router and either navigates the app or is sent through a
> fault-tolerant AI provider chain to Claude (with fallbacks to Groq,
> Cerebras, Gemini, OpenRouter, GPT and Ollama); the JSON reply is
> persisted to SQLite, narrated by ElevenLabs, and the loop closes — and
> the parent can flip any of those providers on or off live."*
