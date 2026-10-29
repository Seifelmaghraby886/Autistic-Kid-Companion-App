/*
 * Build "ARIA — Tech & Features Cheat Sheet" (DOCX).
 *
 *   npm install -g docx     (one-time)
 *   node scripts/build_tech_doc.js
 *
 * Writes to:  docs/ARIA_Tech_and_Features.docx
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, BorderStyle, WidthType, ShadingType, HeadingLevel,
  LevelFormat, PageBreak,
} = require("docx");

// ─── style tokens ────────────────────────────────────────────── //
const NAVY  = "0E2D4A";
const TEAL  = "1A6A7E";
const GREY  = "4A5568";
const HEADERBG = "E2F1F6";
const ALTBG = "F4F8FB";
const BODER_COLOR = "CFDEE4";

const PAGE_W = 12240;            // US Letter
const PAGE_H = 15840;
const MARGIN = 1440;             // 1 inch
const CONTENT_W = PAGE_W - 2 * MARGIN; // 9360 DXA

// border preset
const thinBorder = { style: BorderStyle.SINGLE, size: 4, color: BODER_COLOR };
const allBorders = { top: thinBorder, bottom: thinBorder, left: thinBorder, right: thinBorder };

// ─── helpers ─────────────────────────────────────────────────── //
const P = (text, opts = {}) =>
  new Paragraph({
    spacing: { before: 60, after: 60, line: 300 },
    ...opts,
    children: opts.children || [new TextRun({ text, ...(opts.run || {}) })],
  });

const H1 = (text) =>
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 180 },
    children: [new TextRun({ text, bold: true, size: 36, color: NAVY })],
  });

const H2 = (text) =>
  new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 140 },
    children: [new TextRun({ text, bold: true, size: 30, color: NAVY })],
  });

const H3 = (text) =>
  new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 220, after: 100 },
    children: [new TextRun({ text, bold: true, size: 26, color: TEAL })],
  });

const bullet = (text) =>
  new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { before: 40, after: 40, line: 280 },
    children: [new TextRun({ text, size: 22 })],
  });

const intro = (text) =>
  new Paragraph({
    spacing: { before: 80, after: 120, line: 320 },
    children: [new TextRun({ text, italics: true, size: 22, color: GREY })],
  });

const body = (text) =>
  new Paragraph({
    spacing: { before: 60, after: 80, line: 300 },
    children: [new TextRun({ text, size: 22 })],
  });

// inline "label: body" line with bold label
const labelLine = (label, body) =>
  new Paragraph({
    spacing: { before: 60, after: 60, line: 300 },
    children: [
      new TextRun({ text: label + " ", bold: true, size: 22, color: NAVY }),
      new TextRun({ text: body, size: 22 }),
    ],
  });

// ─── tables ──────────────────────────────────────────────────── //
function cell(text, opts = {}) {
  return new TableCell({
    borders: allBorders,
    width: { size: opts.width, type: WidthType.DXA },
    shading: opts.fill
      ? { fill: opts.fill, type: ShadingType.CLEAR }
      : undefined,
    margins: { top: 100, bottom: 100, left: 140, right: 140 },
    children: [
      new Paragraph({
        spacing: { before: 0, after: 0, line: 280 },
        children: [new TextRun({ text, size: 21, bold: !!opts.bold,
                                  color: opts.color || "000000" })],
      }),
    ],
  });
}

// Two-column "Why we picked X" table
function whyTable(rows) {
  const COL_L = 2400, COL_R = 6960;
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [COL_L, COL_R],
    rows: rows.map(([label, value], i) =>
      new TableRow({
        children: [
          cell(label, { width: COL_L, bold: true, color: NAVY,
                        fill: i % 2 === 0 ? HEADERBG : ALTBG }),
          cell(value, { width: COL_R,
                        fill: i % 2 === 0 ? "FFFFFF" : ALTBG }),
        ],
      })
    ),
  });
}

// Final 3-column summary table
function summaryTable() {
  const COL_A = 1800, COL_B = 2160, COL_C = 5400;
  const header = new TableRow({
    tableHeader: true,
    children: [
      cell("Area",   { width: COL_A, bold: true, color: NAVY, fill: HEADERBG }),
      cell("Choice", { width: COL_B, bold: true, color: NAVY, fill: HEADERBG }),
      cell("One-line reason", { width: COL_C, bold: true, color: NAVY, fill: HEADERBG }),
    ],
  });
  const data = [
    ["UI",            "PySide6 (Qt)",         "Same Python ecosystem as the AI / vision / speech."],
    ["Language",      "Python 3.11",          "Every ML library we need is Python-first."],
    ["Database",      "SQLite",               "Single file, no server, all data stays local."],
    ["STT",           "faster-whisper + Google Speech",  "Best free Arabic + free EN/DE coverage."],
    ["TTS",           "ElevenLabs + edge-tts + pyttsx3", "Warmest Arabic voice + graceful fallbacks."],
    ["AI primary",    "Anthropic Claude",     "Safest refusal behaviour for a child-facing app."],
    ["AI fallback",   "Groq / Gemini / OpenAI / Ollama", "No single point of failure."],
    ["Face detect",   "OpenCV Haar cascade",  "Fast on CPU; frontal-face is enough."],
    ["Emotion model", "Custom Keras CNN",     "Trained on FER-2013 in-house — we own it."],
    ["Audio",         "pygame.mixer",         "Reliable “still talking?” signal for the loop."],
    ["Packaging",     "run_aria.bat",         "Easy to launch and debug during development."],
  ];
  const dataRows = data.map(([a, b, c], i) =>
    new TableRow({
      children: [
        cell(a, { width: COL_A, bold: true, color: NAVY,
                  fill: i % 2 === 0 ? "FFFFFF" : ALTBG }),
        cell(b, { width: COL_B,
                  fill: i % 2 === 0 ? "FFFFFF" : ALTBG }),
        cell(c, { width: COL_C,
                  fill: i % 2 === 0 ? "FFFFFF" : ALTBG }),
      ],
    })
  );
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [COL_A, COL_B, COL_C],
    rows: [header, ...dataRows],
  });
}

// ─── content ─────────────────────────────────────────────────── //
const children = [];

// ── Title block ──
children.push(new Paragraph({
  spacing: { before: 120, after: 80 },
  children: [new TextRun({
    text: "ARIA — Tech & Features Cheat Sheet",
    bold: true, size: 44, color: NAVY,
  })],
}));
children.push(intro(
  "A short, defensible walkthrough of how each feature is built and why the tools were chosen. " +
  "Numbers and module names trace back to the actual source tree (ai/, core/, ui/, vision/, speech/)."
));

children.push(new Paragraph({
  spacing: { before: 80, after: 200 },
  children: [new TextRun({
    text: "Project: ARIA  ·  Stack: Python 3.11 + PySide6 + SQLite  ·  Author: Seif Elmaghraby",
    size: 20, italics: true, color: GREY,
  })],
}));

// ───────────────────────────────────────────────────────────────
// SECTION A — HOW EACH FEATURE IS BUILT
// ───────────────────────────────────────────────────────────────
children.push(H1("Section A — How each feature is built"));
children.push(intro(
  "Each feature below: what it does · how it works (file + library) · the trade-off."
));

// 1. Voice
children.push(H3("1.  Voice conversation"));
children.push(labelLine("What it does:",
  "The child speaks; ARIA understands, replies out loud in Arabic, English, or German, " +
  "and remembers what was said."));
children.push(labelLine("How it is built:", ""));
children.push(bullet("Mic is opened by core/auto_listening_engine.py — a state machine: IDLE → LISTENING → THINKING → SPEAKING."));
children.push(bullet("speech/stt_engine.py runs faster-whisper for Arabic, and Google Speech for English / German."));
children.push(bullet("core/intent_router.py catches nav commands first (\"go back\", \"open games\"); everything else goes to ai/multi_provider.py."));
children.push(bullet("ai/safety_filter.py strips anything inappropriate from the reply."));
children.push(bullet("speech/tts_engine.py speaks the reply: ElevenLabs → edge-tts → pyttsx3 fallback chain."));
children.push(labelLine("Why this way:",
  "Continuous, hands-free, always-listening — tap-to-talk does not work for small autistic children " +
  "who often can not aim a touch precisely."));

// 2. Face + emotion
children.push(H3("2.  Face presence and emotion detection"));
children.push(labelLine("What it does:",
  "Sees whether the child is in front of the camera, and (when enabled) what mood they are in."));
children.push(bullet("core/face_input.py runs a background camera thread (cv2.VideoCapture at 10-12 fps)."));
children.push(bullet("vision/face_detector.py uses an OpenCV Haar cascade to find the largest face per frame."));
children.push(bullet("core/emotion_monitor.py feeds the face crop to a Keras CNN trained on FER-2013, with smoothing across frames."));
children.push(labelLine("Why two engines:",
  "Presence is light (always on); emotion is heavy and off by default — toggled on for the on-demand Emotion Room screen."));

// 3. Hands-free gestures
children.push(H3("3.  Hands-free interaction (nod / shake)"));
children.push(labelLine("What it does:",
  "Child says “yes” by nodding and “no” by shaking — useful when they can not reliably speak."));
children.push(bullet("core/face_input.py keeps a 1.5-second deque of face-box centre points."));
children.push(bullet("Counts zero-crossings of the smoothed Δx / Δy series; vertical → nod, horizontal → shake."));
children.push(bullet("A 1.2-second cooldown between detections prevents double-counting."));
children.push(labelLine("Why this approach:",
  "Pure math on OpenCV's face box — no extra ML library, runs on any laptop with a webcam."));

// 4. Scan mode
children.push(H3("4.  Scan mode for non-verbal children"));
children.push(labelLine("What it does:",
  "ARIA reads each tile out loud (“Talk… Calm Zone… Games…”) and the child nods at the one they want."));
children.push(bullet("core/scan_mode.py walks through the visible tiles one at a time."));
children.push(bullet("Each label is spoken via speech/tts_engine.py."));
children.push(bullet("Subscribes to face_input.gesture_detected — nod selects, shake or 6-second timeout advances."));
children.push(labelLine("Why it matters:",
  "Many autistic children are non-verbal. Without this path the whole voice-first design would exclude them."));

// 5. Multilang
children.push(H3("5.  Multi-language support"));
children.push(labelLine("What it does:",
  "ARIA replies in Egyptian Arabic by default; the parent can switch to English or German per child."));
children.push(bullet("Child profile stores a language code (ar / en / de) in SQLite."));
children.push(bullet("speech/stt_engine.py loads the matching Whisper / Google model on the fly."));
children.push(bullet("speech/tts_engine.py picks the matching voice (Salma for Arabic, Jenny for English)."));
children.push(bullet("ai/prompt_builder.py injects “reply in language X” into every prompt."));

// 6. Parent dashboard
children.push(H3("6.  Parent dashboard"));
children.push(labelLine("What it does:",
  "A PIN-protected screen showing every conversation, every emotion log, and trend graphs."));
children.push(bullet("ui/parent_dashboard.py reads from database/db_manager.py."));
children.push(bullet("Tabs for Overview, Emotions, Chat Log, Sessions, and Export."));
children.push(bullet("Export → JSON; weekly report → PDF (via reportlab)."));
children.push(bullet("Deleting a full child profile is gated behind a second PIN re-entry."));

// 7. Provider control
children.push(H3("7.  Provider Control Center"));
children.push(labelLine("What it does:",
  "The parent can turn ON / OFF each AI provider, each STT engine, each TTS engine, and edit API keys live."));
children.push(bullet("ui/provider_center.py — 12 toggles and 7 editable API-key fields."));
children.push(bullet("core/provider_control.py reads / writes config/app_config.json."));
children.push(bullet("Every AI call checks is_enabled(provider) first — disabled providers are skipped."));
children.push(labelLine("Why this exists:",
  "During the demo, if one API is down or out of credit, the parent flips a toggle and the next provider takes over automatically."));

// 8. Per-child memory
children.push(H3("8.  Per-child memory"));
children.push(labelLine("What it does:",
  "ARIA remembers things the child said earlier in the day, or earlier this week."));
children.push(bullet("Every turn is logged to database/aria.db → chat_logs table."));
children.push(bullet("ai/prompt_builder.py injects the last few turns into every prompt as context."));
children.push(bullet("Memory is per-child — each profile has its own history, never mixed."));

// 9. Kiosk + virtual keyboard
children.push(H3("9.  Kiosk mode and virtual keyboard"));
children.push(labelLine("What it does:",
  "ARIA boots fullscreen with no window chrome. Any text field opens a touch-screen keyboard."));
children.push(bullet("config/app_config.json → \"kiosk_mode\": true → main.py sets the frameless fullscreen flag."));
children.push(bullet("ui/virtual_keyboard.py pops a top-level QWERTY for normal fields; a numpad for short password fields."));
children.push(bullet("Keys use Qt::NoFocus so the field never loses focus."));

// ── page break to start Section B ──
children.push(new Paragraph({ children: [new PageBreak()] }));

// ───────────────────────────────────────────────────────────────
// SECTION B — WHY EACH TOOL WAS CHOSEN
// ───────────────────────────────────────────────────────────────
children.push(H1("Section B — Why each tool was chosen"));
children.push(intro(
  "For each piece of the stack: what we picked, what we considered, and the one or two reasons that decided it."
));

// B1
children.push(H3("B1.  UI framework — PySide6 (not Flutter)"));
children.push(whyTable([
  ["What we picked",        "PySide6 (official Python bindings for Qt 6)."],
  ["Alternatives",          "Flutter desktop, Electron, React Native desktop, Tkinter."],
  ["Why PySide6",           "Same Python ecosystem as the AI, vision, and speech code. " +
                            "No language bridge needed between UI and ML. " +
                            "Qt is a 25-year-old, very mature desktop framework on Windows. " +
                            "Qt's signal / slot system maps cleanly onto the camera-thread → UI handoff."],
  ["Why not Flutter",       "Flutter is Dart, not Python. Every AI call, every DB read, every camera frame " +
                            "would need a Dart ↔ Python bridge — the single biggest source of bugs in " +
                            "cross-language desktop apps. Flutter desktop is also younger than Qt; the kiosk-mode " +
                            "and on-screen-keyboard story is much thinner."],
  ["Why not Electron",      "Ships a 150 MB Chromium runtime per install. We do not need a web layout engine for " +
                            "a single-user kiosk; that is pure overhead."],
]));

// B2
children.push(H3("B2.  Backend language — Python (not C++ / Node.js)"));
children.push(whyTable([
  ["What we picked",  "Python 3.11."],
  ["Alternatives",    "C++, Node.js, Java."],
  ["Why Python",      "Every AI / ML / vision / speech library we need is Python-first: TensorFlow, OpenCV, " +
                      "faster-whisper, the Anthropic SDK, the Google Speech SDK. Graduation projects move fast, " +
                      "and Python lets us change a feature in minutes. One language across UI, AI, vision, DB, " +
                      "and speech — no mental context switching."],
  ["Why not C++",     "We would save some CPU but lose every AI library and lose months of development time. " +
                      "Our bottleneck is the camera and the network calls to the TTS server — Python is fast enough."],
]));

// B3
children.push(H3("B3.  Database — SQLite (not Postgres / MongoDB / Firebase)"));
children.push(whyTable([
  ["What we picked",     "SQLite (one file: database/aria.db)."],
  ["Alternatives",       "PostgreSQL, MongoDB, Firebase, MySQL."],
  ["Why SQLite",         "Single file — no server, no “did you forget to start the DB?” failure mode. " +
                         "Built into Python's standard library (zero install). Plenty fast for a few thousand " +
                         "chat rows. Backup is one file copy."],
  ["Why not Postgres",   "Postgres needs a server process. For a single-user home kiosk that is pure overhead — " +
                         "we would also need a service to keep it running on the parent's laptop."],
  ["Why not Firebase",   "We do not want a child's emotion logs flowing into a third-party cloud by default. " +
                         "Privacy is part of the design — everything stays local unless the parent explicitly exports."],
]));

// B4
children.push(H3("B4.  Speech-to-text — faster-whisper + Google Speech"));
children.push(whyTable([
  ["What we picked",  "faster-whisper (Arabic) + Google Speech (English / German)."],
  ["Alternatives",    "Whisper-only, Azure Speech, Vosk, AWS Transcribe."],
  ["Why this split",  "Egyptian Arabic is hard for free engines — Whisper's medium model is the best free option " +
                      "we tested for dialectal Arabic. For EN / DE, Google Speech is faster and free up to 60 " +
                      "minutes per month, so Whisper would be overkill. faster-whisper is ~4× faster than vanilla " +
                      "Whisper and runs fully offline."],
]));

// B5
children.push(H3("B5.  Text-to-speech — ElevenLabs + edge-tts + pyttsx3"));
children.push(whyTable([
  ["What we picked",   "ElevenLabs multilingual_v2 primary, edge-tts fallback, pyttsx3 last-resort."],
  ["Alternatives",     "Google TTS, Azure TTS, Amazon Polly."],
  ["Why ElevenLabs",   "The most natural, warmest Arabic delivery we tested. Google and Azure Arabic both " +
                       "sound noticeably robotic to a native speaker. A single voice (Sarah) covers Arabic, " +
                       "English, and German — no awkward voice-switching when the language changes."],
  ["Why the fallbacks","ElevenLabs free tier occasionally returns HTTP 402 mid-conversation. edge-tts (Microsoft " +
                       "Edge's built-in TTS, free) catches that gracefully. pyttsx3 (Windows SAPI, fully offline) " +
                       "catches network failures too."],
]));

// B6
children.push(H3("B6.  AI — Anthropic Claude (primary) + multi-provider chain"));
children.push(whyTable([
  ["What we picked",   "Anthropic Claude as primary; Gemini, Groq, Cerebras, OpenAI, Ollama as fallbacks."],
  ["Why Claude",       "Highest refusal rate on dual-use prompts (73 % vs GPT-3.5's 10 %) — the safest default " +
                       "behaviour for a child-facing app. Competitive on accuracy benchmarks (88.7 % MMLU, " +
                       "92 % HumanEval). Trained with the published Constitutional AI method — peer-reviewable, " +
                       "not just a marketing claim."],
  ["Why a fallback chain", "If one provider rate-limits, the next takes over — no single point of failure during a demo."],
  ["See also",         "docs/AI_API_DEFENSE.md — full numbers, charts, and research citations."],
]));

// B7
children.push(H3("B7.  Face detection — OpenCV Haar"));
children.push(whyTable([
  ["What we picked",     "OpenCV Haar cascade."],
  ["Alternatives",       "MediaPipe Face Detector, dlib HOG, modern CNN detectors."],
  ["Why Haar",           "Built into OpenCV — no extra dependency. Fast on CPU (~15 ms per frame). " +
                         "Frontal-face only is fine — the child is sitting in front of a screen; we do not need " +
                         "profile detection."],
  ["Why not MediaPipe",  "Bigger install, GPU-friendly but overkill for our use. Adds a TensorFlow dependency we " +
                         "already pay for elsewhere."],
]));

// B8
children.push(H3("B8.  Emotion model — custom Keras CNN on FER-2013"));
children.push(whyTable([
  ["What we picked",      "A custom CNN trained in ml_training/ on the FER-2013 dataset."],
  ["Alternatives",        "DeepFace, FER+ pretrained, EmoNet."],
  ["Why custom",          "We know exactly what is inside the model — we trained it. That is defensible in the " +
                          "thesis. Smaller artefact (~5 MB .h5) than DeepFace's download bundle. Returns the seven " +
                          "standard emotions we mapped to ARIA's response logic."],
]));

// B9
children.push(H3("B9.  Audio playback — pygame.mixer"));
children.push(whyTable([
  ["What we picked",      "pygame.mixer.music."],
  ["Alternatives",        "playsound, sounddevice, vlc."],
  ["Why pygame.mixer",    "mixer.music.get_busy() gives a perfectly reliable “is it still talking?” signal — " +
                          "critical for the conversation loop to know when to start listening again. Plays mp3 " +
                          "directly with no decoding step. Cross-platform if we ever leave Windows."],
]));

// B10
children.push(H3("B10.  Packaging — run_aria.bat (a launcher)"));
children.push(whyTable([
  ["What we picked",  "run_aria.bat → calls the bundled Python 3.11 with main.py."],
  ["Alternatives",    "PyInstaller .exe, MSI installer, py2exe."],
  ["Why .bat",        "No 300 MB single-file exe to ship during development. Easy to debug — examiner or parent " +
                      "can see Python output if something goes wrong. Faster iteration cycle."],
  ["Caveat for v2",   "Once ARIA ships to families post-graduation, we would switch to PyInstaller or MSIX for a " +
                      "proper installer."],
]));

// ── page break for summary ──
children.push(new Paragraph({ children: [new PageBreak()] }));

// ───────────────────────────────────────────────────────────────
// SECTION C — SUMMARY TABLE
// ───────────────────────────────────────────────────────────────
children.push(H1("Section C — 30-second summary"));
children.push(intro(
  "If you only have a minute, this single table is the whole defense."
));
children.push(summaryTable());

children.push(new Paragraph({
  spacing: { before: 280, after: 0 },
  children: [new TextRun({
    text: "Companion docs in the repository:",
    bold: true, size: 22, color: NAVY,
  })],
}));
children.push(bullet("docs/AI_API_DEFENSE.md — research + charts proving why Anthropic Claude is the safest LLM choice for a child-facing app."));
children.push(bullet("TECH_CHOICES.md — the original choice log written during development."));
children.push(bullet("TECH_OPTIONS.md — alternatives table with deeper rationale."));
children.push(bullet("SYSTEM_FLOW.md — Mermaid system flowchart of the full pipeline."));
children.push(bullet("README.md — repository layout and run instructions."));

// ─── document ────────────────────────────────────────────────── //
const doc = new Document({
  creator: "Seif Elmaghraby",
  title: "ARIA — Tech & Features Cheat Sheet",
  description: "Defensible walkthrough of feature builds and tech choices.",
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: 36, bold: true, font: "Arial", color: NAVY },
        paragraph: { spacing: { before: 360, after: 180 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: 30, bold: true, font: "Arial", color: NAVY },
        paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: 26, bold: true, font: "Arial", color: TEAL },
        paragraph: { spacing: { before: 220, after: 100 }, outlineLevel: 2 } },
    ],
  },
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{
        level: 0, format: LevelFormat.BULLET, text: "•",
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } },
      }],
    }],
  },
  sections: [{
    properties: {
      page: {
        size: { width: PAGE_W, height: PAGE_H },
        margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN },
      },
    },
    children,
  }],
});

const outDir = path.join(__dirname, "..", "docs");
fs.mkdirSync(outDir, { recursive: true });
const outFile = path.join(outDir, "ARIA_Tech_and_Features.docx");

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(outFile, buf);
  console.log("Wrote " + outFile + " (" + buf.length + " bytes)");
});
