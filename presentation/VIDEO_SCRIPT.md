# ARIA — Demo Video Script
**Total runtime: ~4 minutes** · Aim for clear narration over screen recording.

Recording tool: **OBS Studio** (free) or **Windows Game Bar** (Win+G).
Resolution: 1920×1080 @ 30 fps. Mic: same one set up in Settings.

---

## SCENE 1 — INTRO (0:00 – 0:20)
**[Show ARIA splash screen → Welcome Back]**

> "Hi, I'm Seif. This is ARIA — Adaptive Robotic Interaction Assistant.
> A 24/7 AI companion built specifically for autistic children.
> ARIA combines real-time emotion detection, multi-language AI conversation,
> and over twenty research-backed features into one calm, futuristic Windows app."

**[Click child profile → Dashboard fades in]**

---

## SCENE 2 — UI TOUR (0:20 – 0:40)
**[Show dashboard with all 22 cards]**

> "The dashboard shows 22 features — from AI conversation to sensory tools,
> games, communication boards, and parent dashboards. Each card uses a holographic
> hover effect with a scanning cyan line — futuristic, but never overstimulating.
> The teal-and-purple palette was chosen to avoid the harsh reds and bright pinks
> that overwhelm autistic children."

**[Hover over a few cards to show animation]**

---

## SCENE 3 — TALK WITH ARIA (0:40 – 1:20)
**[Click "Talk with ARIA"]**

> "Let me show you the conversation feature. ARIA speaks Egyptian Arabic,
> English, or German — based on the child's profile."

**[Click big rainbow "Start Voice Chat" button]**
**[Wait for green LISTENING badge]**

> *(Speak in Arabic):* "أنا تعبان النهاردة"

**[ARIA replies aloud in Egyptian dialect with Salma neural voice. Wait for response.]**

> "Notice ARIA replied in real Egyptian colloquial — 'يا حبيبي' — not formal
> Modern Standard Arabic. This is achieved with a 60+ phrase regex polisher
> plus aggressive prompt engineering. The AI also tracks the last 6 turns of
> conversation for context."

---

## SCENE 4 — LIVE CAMERA + VLM (1:20 – 2:00)
**[Click "Live Camera"]**

> "ARIA's hybrid emotion detection runs two systems in parallel."

**[Click Start Camera]**

> "First, a custom MobileNetV2 CNN trained on three autism datasets.
> It runs locally at 30 frames per second, identifying six emotions with
> probability bars on the right."

**[Wait for face detection]**
**[Click 🧠 Smart Analysis button]**

> "Now I trigger Smart Analysis — this sends the frame to a Vision-Language
> Model, Llama-4 Scout via Groq. Instead of just a label, it returns rich
> clinical-grade descriptions like 'looking pensive, slight forward lean.'
> The CNN gives speed and privacy. The VLM gives depth."

---

## SCENE 5 — CALMING + SENSORY (2:00 – 2:30)
**[Back → Sound Garden]**

> "ARIA includes procedural calming audio — brown noise, ocean, rain —
> all generated in real time with numpy. No license fees, no audio files."

**[Click Brown Noise → live waveform animates]**
**[Stop → back → Feelings Thermometer]**

> "The feelings thermometer is autism-critical. It scales from 1 to 10.
> Above 7, ARIA automatically suggests calming actions and pulses red."

**[Tap level 8]**

> "ARIA detects the spike and switches into comfort mode."

---

## SCENE 6 — AI FEATURES (2:30 – 3:10)
**[Back → AI Coping Coach]**

> "AI Coping Coach generates personalized strategies based on the child's
> profile, triggers, and what calms them."

**[Tap "Anxious"]**

> "In about a second, ARIA returns 3 actionable strategies in Arabic."

**[Wait briefly]**
**[Back → Bedtime Story → tap "Cozy Night"]**

> "Bedtime Story creates a personalized story with the child as the hero."

**[Wait for story → click Narrate]**

> "And reads it aloud in the soft Egyptian neural voice."

---

## SCENE 7 — PARENT DASHBOARD (3:10 – 3:40)
**[Back → Parent Dashboard]**
**[Enter PIN]**

> "Parents have a PIN-locked dashboard with five tabs.
> Today's mood, full emotion logs, all chat history, sessions,
> and a data export tab with JSON and PDF report generation.
> The donut chart shows emotion distribution. AI Insights uses
> Gemini to spot patterns the parent should know about."

---

## SCENE 8 — TECHNICAL HIGHLIGHTS (3:40 – 4:00)
**[Switch to slide-style overlay or stay on dashboard]**

> "Behind the scenes: 11,000+ lines of Python with PySide6.
> Seven AI providers in an automatic fallback chain — Groq, Cerebras,
> Gemini, OpenRouter, Anthropic, OpenAI, and local Ollama.
> The free tier alone covers virtually unlimited usage.
> Whisper Medium for Arabic STT, edge-tts for warm neural voices.
> Every feature is grounded in autism research papers from CDC,
> ASHA, and peer-reviewed journals."

---

## SCENE 9 — CLOSING (4:00 – 4:15)
**[Back to dashboard or splash]**

> "ARIA isn't a chatbot — it's a complete autism companion platform.
> Built with care, every decision evidence-based.
> Thank you for watching."

**[Fade out to ARIA logo]**

---

# 🎬 RECORDING TIPS

1. **Practice once silent**, then once with narration before recording final.
2. **Pause 2 sec** after every click — give viewer time to see the screen.
3. **Don't read this script** — paraphrase naturally.
4. **Mouse cursor** — set Windows cursor size to large (Settings > Accessibility).
5. **Background music** — Optional. If using, free tracks at pixabay.com/music.
6. **Subtitles** — Auto-generate with capcut.com after recording.

---

# 📁 FILES PRODUCED
- `ARIA_Presentation.pptx` — full slide deck (this folder)
- `screenshots/*.png` — 20 screenshots ready to use anywhere
- `VIDEO_SCRIPT.md` — this document

---

# 📚 KEY QUOTES FOR Q&A

**Q: Why teal not blue?**
A: Teal sits between blue (calm) and green (safety). Avoids the corporate-blue feel and the "medical" institutional feel. Saturation kept moderate to prevent sensory overload.

**Q: Why MobileNetV2 not a bigger model?**
A: Real-time inference on CPU at 30fps. Bigger models would force GPU which limits deployment. MobileNetV2 hits the speed-accuracy sweet spot for emotion classification.

**Q: Why not OpenAI as primary?**
A: OpenAI has no free tier and the free $5 trial expires fast. Groq's free tier (30 req/min Llama-3.3-70B) genuinely meets autism support needs. Claude is the premium answer for empathy when budget allows.

**Q: How is this different from existing autism apps?**
A: Three things — (1) hybrid CNN+VLM emotion detection in one app, (2) genuine Egyptian Arabic dialect support not just MSA, (3) seven-provider AI fallback chain that makes the free tier actually viable.

**Q: Privacy?**
A: Face data stays local for the CNN. VLM analysis is opt-in per click. Database is SQLite on the user's machine. No telemetry. Full export and delete controls in parent dashboard.
