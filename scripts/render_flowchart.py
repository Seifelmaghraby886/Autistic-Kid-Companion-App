"""Render a single-image detailed flowchart of ARIA OS to FLOWCHART.png.

Run: py -3.11 scripts/render_flowchart.py
"""
from __future__ import annotations

import os
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from matplotlib.lines import Line2D

# --------------------------------------------------------------------------- #
# Canvas
# --------------------------------------------------------------------------- #
FIG_W, FIG_H = 30, 22  # inches
DPI = 150

fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=DPI)
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis("off")
ax.set_facecolor("#0f1115")
fig.patch.set_facecolor("#0f1115")

# Title
ax.text(
    50, 98.4,
    "ARIA OS — Full System Flowchart",
    ha="center", va="center",
    color="#ffffff", fontsize=26, fontweight="bold",
)
ax.text(
    50, 96.6,
    "Voice-first, camera-aware AI companion kiosk for autistic children · PySide6 · Python 3.11",
    ha="center", va="center",
    color="#9aa4b2", fontsize=12, style="italic",
)

# --------------------------------------------------------------------------- #
# Color palette per subsystem
# --------------------------------------------------------------------------- #
C = {
    "hw":      ("#1e293b", "#38bdf8", "#e0f2fe"),  # bg, edge, text
    "boot":    ("#1e1b4b", "#a78bfa", "#ede9fe"),
    "vision":  ("#064e3b", "#34d399", "#d1fae5"),
    "voice":   ("#7c2d12", "#fb923c", "#ffedd5"),
    "ai":      ("#581c87", "#c084fc", "#f3e8ff"),
    "tts":     ("#831843", "#f472b6", "#fce7f3"),
    "screens": ("#0c4a6e", "#38bdf8", "#e0f2fe"),
    "parent":  ("#713f12", "#facc15", "#fef9c3"),
    "storage": ("#3f3f46", "#a1a1aa", "#f4f4f5"),
    "decision":("#422006", "#fb7185", "#fee2e2"),
}


def box(ax, x, y, w, h, label, kind, fs=10, fw="normal"):
    bg, edge, txt = C[kind]
    patch = FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.6",
        linewidth=1.6, edgecolor=edge, facecolor=bg,
    )
    ax.add_patch(patch)
    ax.text(x, y, label, ha="center", va="center",
            color=txt, fontsize=fs, fontweight=fw, wrap=True)
    return patch


def diamond(ax, x, y, w, h, label, fs=9):
    bg, edge, txt = C["decision"]
    pts = [(x, y + h / 2), (x + w / 2, y), (x, y - h / 2), (x - w / 2, y)]
    poly = plt.Polygon(pts, closed=True, edgecolor=edge,
                       facecolor=bg, linewidth=1.6)
    ax.add_patch(poly)
    ax.text(x, y, label, ha="center", va="center",
            color=txt, fontsize=fs, fontweight="bold")


def arrow(ax, x1, y1, x2, y2, color="#94a3b8", lw=1.4, style="-|>", label=None,
          label_color="#cbd5e1", curve=0.0, ls="solid"):
    a = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle=style, mutation_scale=14,
        color=color, linewidth=lw,
        connectionstyle=f"arc3,rad={curve}",
        linestyle=ls,
    )
    ax.add_patch(a)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my + 0.6, label, ha="center", va="center",
                color=label_color, fontsize=8, style="italic",
                bbox=dict(facecolor="#0f1115", edgecolor="none", pad=1.5))


def section_header(ax, x, y, w, title, color):
    ax.add_patch(Rectangle((x - w / 2, y - 0.6), w, 1.2,
                           facecolor=color, edgecolor="none", alpha=0.18))
    ax.text(x, y, title, ha="center", va="center",
            color=color, fontsize=12, fontweight="bold")


# --------------------------------------------------------------------------- #
# ROW 1 — HARDWARE INPUTS (y ~ 91)
# --------------------------------------------------------------------------- #
section_header(ax, 50, 93.5, 92, "[ HARDWARE INPUTS ]", "#38bdf8")

box(ax, 12, 91, 14, 2.6, "MICROPHONE\n(continuous audio)", "hw")
box(ax, 32, 91, 14, 2.6, "WEBCAM\n(640x480 · ~10-12 fps)", "hw")
box(ax, 52, 91, 14, 2.6, "TOUCHSCREEN\n(kiosk gestures)", "hw")
box(ax, 72, 91, 14, 2.6, "KEYBOARD\n(parent · virtual KB)", "hw")
box(ax, 90, 91, 14, 2.6, "SPEAKERS\n(TTS output)", "hw")

# --------------------------------------------------------------------------- #
# ROW 2 — BOOT (y ~ 86)
# --------------------------------------------------------------------------- #
section_header(ax, 50, 88, 92, "[ BOOT & KIOSK ]", "#a78bfa")
box(ax, 10, 86, 14, 2.4, "main.py\nentry point", "boot", fw="bold")
box(ax, 26, 86, 14, 2.4, "ARIAMainWindow\nfullscreen · frameless", "boot")
box(ax, 42, 86, 14, 2.4, "DB init\naria.db (SQLite)", "boot")
box(ax, 58, 86, 14, 2.4, "load app_config.json\n+ providers state", "boot")
box(ax, 74, 86, 14, 2.4, "Engine bootstrap\nConv · Face · Emotion", "boot")
box(ax, 90, 86, 14, 2.4, "Show ARIAShell\n(home tiles)", "boot")
for x1, x2 in [(17, 19), (33, 35), (49, 51), (65, 67), (81, 83)]:
    arrow(ax, x1, 86, x2, 86)

# Hardware → Boot
arrow(ax, 12, 89.7, 10, 87.2, curve=-0.1)
arrow(ax, 90, 89.7, 90, 87.2)

# --------------------------------------------------------------------------- #
# ROW 3 — TWO PARALLEL ALWAYS-ON LOOPS (y ~ 73–82)
# --------------------------------------------------------------------------- #
section_header(ax, 26, 83, 46, "[ CAMERA / VISION LOOP ]", "#34d399")
section_header(ax, 75, 83, 46, "[ VOICE LOOP ]", "#fb923c")

# Vision pipeline (left)
box(ax, 14, 80, 18, 2.6, "FaceInputEngine\n(QThread · CAP_DSHOW)", "vision", fw="bold")
box(ax, 38, 80, 18, 2.6, "vision/face_detector\nHaar cascade · largest face", "vision")
arrow(ax, 23, 80, 29, 80, label="frame")

box(ax, 14, 76, 18, 2.6, "Presence (≥ 0.8 s)\n→ absent (≥ 4 s)", "vision")
box(ax, 38, 76, 18, 2.6, "Gesture math\nΔx / Δy zero-crossings", "vision")
arrow(ax, 14, 78.6, 14, 77.3)
arrow(ax, 38, 78.6, 38, 77.3)

box(ax, 26, 72, 22, 2.6, "EmotionMonitor (gated)\nKeras CNN · TFLite fallback", "vision")
arrow(ax, 14, 74.6, 22, 73.3, curve=0.1)
arrow(ax, 38, 74.6, 30, 73.3, curve=-0.1)

diamond(ax, 14, 68.5, 7, 2.6, "Face\npresent?")
diamond(ax, 38, 68.5, 7, 2.6, "Gesture\ndetected?")
arrow(ax, 14, 74.6, 14, 69.8)
arrow(ax, 38, 74.6, 38, 69.8)

# Voice pipeline (right)
box(ax, 63, 80, 18, 2.6, "AutoListeningEngine\n(VAD · 3.5 s silence)", "voice", fw="bold")
box(ax, 87, 80, 18, 2.6, "STTEngine\nfaster-whisper · Google", "voice")
arrow(ax, 72, 80, 78, 80, label="PCM")

box(ax, 63, 76, 18, 2.6, "intent_router\nyes/no · open · scan", "voice")
box(ax, 87, 76, 18, 2.6, "ConversationEngine\n(orchestrator)", "voice", fw="bold")
arrow(ax, 87, 78.6, 87, 77.3)
arrow(ax, 78, 76, 78, 76, style="-")  # placeholder
arrow(ax, 96, 76, 72, 76, curve=0.15, label="transcript")

diamond(ax, 75, 68.5, 9, 2.6, "Listen?\n(presence /\ntap-to-talk)")
arrow(ax, 63, 74.6, 71, 69.8, curve=-0.1)
arrow(ax, 87, 74.6, 79, 69.8, curve=0.1)

# Vision → Conversation bridges
arrow(ax, 17, 68.5, 70, 68.5, color="#a78bfa", lw=1.2, ls="dashed",
      label="presence → notify_presence(bool)")
arrow(ax, 41, 68.5, 70, 67, color="#a78bfa", lw=1.2, ls="dashed",
      label="gesture → on_gesture(nod/shake)")

# --------------------------------------------------------------------------- #
# ROW 4 — AI MULTI-PROVIDER CHAIN (y ~ 60)
# --------------------------------------------------------------------------- #
section_header(ax, 50, 64.5, 92, "[ AI REASONING - ai/multi_provider.py (fallback ladder, provider_control gated) ]", "#c084fc")

providers = [
    ("Groq\nLlama-3", 10),
    ("Cerebras\nLlama-3", 22),
    ("Gemini\n2.5-flash\n(primary)", 34),
    ("OpenRouter\nClaude/GPT", 46),
    ("Anthropic\nClaude API", 58),
    ("OpenAI\nGPT-4o", 70),
    ("Ollama\nlocal", 82),
    ("Safety\nFilter", 94),
]
for i, (name, x) in enumerate(providers):
    bold = "bold" if "primary" in name else "normal"
    box(ax, x, 61, 10, 3, name, "ai", fs=9, fw=bold)
    if i < len(providers) - 1:
        arrow(ax, x + 5, 61, providers[i + 1][1] - 5, 61,
              label="429/err" if 0 < i < 6 else None)

# Voice loop → AI
arrow(ax, 87, 74.6, 94, 63.4, curve=0.15, color="#c084fc",
      label="user_text + child profile + emotion")

# AI → TTS
arrow(ax, 50, 59.4, 50, 56.2, color="#f472b6", label="reply_text")

# --------------------------------------------------------------------------- #
# ROW 5 — TTS CHAIN (y ~ 53)
# --------------------------------------------------------------------------- #
section_header(ax, 50, 56.5, 92, "[ TTS - speech/tts_engine.py ]", "#f472b6")
box(ax, 18, 53, 18, 3, "ElevenLabs\nmultilingual_v2\n(Sarah voice)", "tts", fw="bold")
box(ax, 42, 53, 18, 3, "edge-tts\nar-EG-SalmaNeural\n(asyncio)", "tts")
box(ax, 66, 53, 18, 3, "pyttsx3\nSAPI offline\n(final fallback)", "tts")
box(ax, 90, 53, 14, 3, "_clean_speech_text\n(strip emoji / md)", "tts")
arrow(ax, 27, 53, 33, 53, label="HTTP 402/key off")
arrow(ax, 51, 53, 57, 53, label="net err")
arrow(ax, 75, 53, 83, 53, label="post")

# TTS → Speaker
arrow(ax, 50, 51.4, 90, 89.7, color="#f472b6", lw=1.2, ls="dashed",
      curve=0.25, label="audio out")

# --------------------------------------------------------------------------- #
# ROW 6 — SCREEN-VOICE BUS + SCAN MODE (y ~ 45)
# --------------------------------------------------------------------------- #
section_header(ax, 25, 48, 46, "[ SCREEN-VOICE BUS - core/screen_voice.py ]", "#38bdf8")
section_header(ax, 75, 48, 46, "[ SCAN MODE - core/scan_mode.py ]", "#fb7185")

box(ax, 14, 45, 18, 3, "attach_tool(screen)\non navigation", "screens", fw="bold")
box(ax, 38, 45, 18, 3, "_match_button(text)\nsynonyms EN/AR/DE", "screens")
arrow(ax, 23, 45, 29, 45)

box(ax, 14, 41, 18, 3, "QAbstractButton\n+ clickable QWidget", "screens")
box(ax, 38, 41, 18, 3, "synthesize click\nmousePressEvent", "screens")
arrow(ax, 14, 43.4, 14, 42.2)
arrow(ax, 38, 43.4, 38, 42.2)
arrow(ax, 23, 41, 29, 41)

box(ax, 63, 45, 18, 3, "ScanController\nspeak option → wait", "screens", fw="bold")
box(ax, 87, 45, 18, 3, "non-verbal home tiles\n+ AAC choices", "screens")
arrow(ax, 72, 45, 78, 45)

diamond(ax, 63, 41, 9, 2.6, "Nod / yes?")
diamond(ax, 87, 41, 9, 2.6, "Shake / no /\ntimeout 6 s?")
arrow(ax, 63, 43.4, 63, 42.2)
arrow(ax, 87, 43.4, 87, 42.2)
arrow(ax, 87, 39.7, 78, 46.5, color="#fb7185", lw=1.2, ls="dashed", curve=-0.2,
      label="next option")
arrow(ax, 63, 39.7, 72, 39.7, color="#34d399", lw=1.2, label="select()")

# Conversation ↔ Screen-voice + Scan
arrow(ax, 87, 74.6, 14, 46.5, color="#38bdf8", lw=1.2, ls="dashed", curve=-0.25,
      label="open <tool> / route command")

# --------------------------------------------------------------------------- #
# ROW 7 — TOOL SCREENS GRID (y ~ 30–38)
# --------------------------------------------------------------------------- #
section_header(ax, 50, 38.5, 92, "[ 25 TOOL SCREENS - ui/* (each: QWidget + go_back signal) ]", "#38bdf8")

tools_row1 = [
    "Talk", "Calm Zone", "Picture Cards", "Comm Board",
    "Games", "Schedule", "Stories", "Routines",
]
tools_row2 = [
    "Live Camera", "Photo Test", "Art", "Music",
    "Numbers", "Letters", "Emotions", "Timer",
]
tools_row3 = [
    "Family", "Animals", "Food", "Vehicles",
    "Home", "Memory", "Mirror", "Rewards",
    "Reports (parent)",
]

def render_tools(row, y):
    n = len(row)
    span = 88.0
    start = 50 - span / 2
    w = span / n - 0.6
    for i, name in enumerate(row):
        x = start + (i + 0.5) * (span / n)
        box(ax, x, y, w, 2.0, name, "screens", fs=9)

render_tools(tools_row1, 35.5)
render_tools(tools_row2, 33.0)
render_tools(tools_row3, 30.5)

# Conv → tool screens bus
arrow(ax, 50, 40, 50, 39.5, color="#38bdf8")

# --------------------------------------------------------------------------- #
# ROW 8 — PARENT PATH (y ~ 23)
# --------------------------------------------------------------------------- #
section_header(ax, 25, 26.5, 46, "[ PARENT PATH (touch-only) ]", "#facc15")
section_header(ax, 75, 26.5, 46, "[ STORAGE ]", "#a1a1aa")

box(ax, 10, 23, 14, 3, "Setup\n(home gear)", "parent")
box(ax, 26, 23, 14, 3, "PIN gate\nvirtual keypad", "parent")
box(ax, 42, 23, 14, 3, "Parent Dashboard\nchildren · settings", "parent", fw="bold")
arrow(ax, 17, 23, 19, 23)
arrow(ax, 33, 23, 35, 23)

box(ax, 10, 19, 14, 3, "Provider Center\n12 toggles · 7 keys", "parent")
box(ax, 26, 19, 14, 3, "Child Profile\nname · age · level", "parent")
box(ax, 42, 19, 14, 3, "Reports & Logs\nemotion · sessions", "parent")
arrow(ax, 10, 21.4, 10, 20.2)
arrow(ax, 26, 21.4, 26, 20.2)
arrow(ax, 42, 21.4, 42, 20.2)

# Storage (right)
box(ax, 62, 23, 14, 3, "SQLite\naria.db", "storage", fw="bold")
box(ax, 78, 23, 14, 3, "parents · children\nsettings · sessions", "storage")
box(ax, 94, 23, 12, 3, "device_config\napp_config.json", "storage")
arrow(ax, 69, 23, 71, 23)
arrow(ax, 85, 23, 88, 23)

box(ax, 62, 19, 14, 3, "aria_os.log\nstructured ts log", "storage")
box(ax, 78, 19, 14, 3, "crash.log\nuncaught excs", "storage")
box(ax, 94, 19, 12, 3, "models/\nemotion .h5/.tflite", "storage")

# Parent → storage
arrow(ax, 49, 23, 55, 23, color="#a1a1aa", lw=1.2, ls="dashed",
      label="r/w")

# AI / TTS / Conv → log
arrow(ax, 50, 51.4, 62, 20.4, color="#a1a1aa", lw=1.0, ls="dotted", curve=0.2,
      label="logs")

# --------------------------------------------------------------------------- #
# ROW 9 — CROSS-CUTTING / SAFETY (y ~ 12)
# --------------------------------------------------------------------------- #
section_header(ax, 50, 15.5, 92, "[ CROSS-CUTTING CONCERNS ]", "#fb7185")

box(ax, 12, 13, 16, 3, "ai/safety_filter\nchild-safe content", "ai")
box(ax, 30, 13, 16, 3, "TTS watchdog\nprevent loop freeze", "tts")
box(ax, 48, 13, 16, 3, "Kiosk lock\nfullscreen · no exit", "boot")
box(ax, 66, 13, 16, 3, "os._exit(0)\nclean shutdown", "boot")
box(ax, 84, 13, 16, 3, "core/log.py\nshared logger", "storage")

box(ax, 12, 9, 16, 3, "Egyptian Arabic\nprimary dialect", "voice")
box(ax, 30, 9, 16, 3, "Multi-provider\nfallback chain", "ai")
box(ax, 48, 9, 16, 3, "Provider toggles\nprovider_control.py", "parent")
box(ax, 66, 9, 16, 3, "Virtual Keyboard\nKeyboardManager", "screens")
box(ax, 84, 9, 16, 3, "Emotion smoothing\ndeque + threshold", "vision")

# --------------------------------------------------------------------------- #
# Legend
# --------------------------------------------------------------------------- #
legend_items = [
    ("Hardware", "#38bdf8"),
    ("Boot / Kiosk", "#a78bfa"),
    ("Vision", "#34d399"),
    ("Voice / STT", "#fb923c"),
    ("AI Providers", "#c084fc"),
    ("TTS", "#f472b6"),
    ("Screens / Bus", "#38bdf8"),
    ("Parent", "#facc15"),
    ("Storage", "#a1a1aa"),
    ("Decision", "#fb7185"),
]
ax.add_patch(Rectangle((1, 1), 98, 4, facecolor="#1e293b",
                       edgecolor="#334155", linewidth=1.0, alpha=0.6))
ax.text(2.5, 4, "LEGEND", color="#cbd5e1", fontsize=10, fontweight="bold",
        va="center")

for i, (name, color) in enumerate(legend_items):
    x = 12 + i * 8.7
    ax.add_patch(Rectangle((x, 2.2), 1.6, 1.6, facecolor=color,
                           edgecolor="none"))
    ax.text(x + 2.2, 3.0, name, color="#e2e8f0", fontsize=9, va="center")

ax.text(50, 0.5,
        "data flow: solid arrow  ·  control / event: dashed  ·  log / telemetry: dotted  ·  decision: red diamond",
        ha="center", va="center", color="#64748b", fontsize=8, style="italic")

# --------------------------------------------------------------------------- #
# Save
# --------------------------------------------------------------------------- #
out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "FLOWCHART.png")
plt.savefig(out_path, dpi=DPI, bbox_inches="tight",
            facecolor=fig.get_facecolor(), pad_inches=0.1)
plt.close(fig)
print(f"Wrote {out_path}")
