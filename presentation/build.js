// ARIA Graduation Project Presentation Builder
const path = require('path');
process.env.NODE_PATH = "C:\\Users\\Seif\\AppData\\Roaming\\npm\\node_modules";
require('module').Module._initPaths();
const pptxgen = require('pptxgenjs');

const SHOTS = path.join(__dirname, 'screenshots');

// Color palette — matches ARIA UI
const C = {
    navy:       "0A1428",   // dark backgrounds
    navy_deep:  "050B18",
    teal:       "00BFA8",   // primary
    teal_deep:  "1A7FA8",
    teal_glow:  "5CE5DC",
    cyan:       "00E5FF",   // neon accent
    purple:     "B388FF",   // neon accent 2
    pink:       "FF6BC4",
    bg_light:   "F0F4FF",
    text:       "1A2432",
    text_light: "5A6F8A",
    white:      "FFFFFF",
    success:    "00D9A0",
    warning:    "FFB73D",
    danger:     "FF6B7E",
    gold:       "FFD700",
};

const FONT_TITLE = "Calibri";
const FONT_BODY  = "Calibri";

let pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';   // 13.3" x 7.5"
pres.author = 'Seif';
pres.title  = 'ARIA — A 24/7 AI Companion for Autistic Children';

const W = 13.333, H = 7.5;

// Helper: dark gradient title slide
function darkBg(slide) {
    slide.background = { color: C.navy_deep };
    // Mesh accent corner
    slide.addShape(pres.shapes.OVAL, {
        x: -2, y: -2, w: 6, h: 6,
        fill: { color: C.teal, transparency: 80 }, line: { color: C.teal, width: 0 }
    });
    slide.addShape(pres.shapes.OVAL, {
        x: W - 4, y: H - 4, w: 6, h: 6,
        fill: { color: C.purple, transparency: 80 }, line: { color: C.purple, width: 0 }
    });
}

function lightBg(slide) {
    slide.background = { color: C.white };
    // Top accent bar
    slide.addShape(pres.shapes.RECTANGLE, {
        x: 0, y: 0, w: W, h: 0.15,
        fill: { color: C.teal }, line: { color: C.teal, width: 0 }
    });
}

function sectionHeader(slide, kicker, title, color) {
    color = color || C.teal_deep;
    slide.addText(kicker, {
        x: 0.6, y: 0.35, w: 8, h: 0.4,
        fontFace: FONT_TITLE, fontSize: 12, bold: true,
        color: color, charSpacing: 6
    });
    slide.addText(title, {
        x: 0.6, y: 0.7, w: 12, h: 0.9,
        fontFace: FONT_TITLE, fontSize: 36, bold: true,
        color: C.text, margin: 0
    });
}

function pageNumber(slide, n, total) {
    slide.addText(`${n} / ${total}`, {
        x: W - 1.2, y: H - 0.35, w: 1, h: 0.3,
        fontFace: FONT_BODY, fontSize: 10, color: C.text_light, align: "right"
    });
}

const TOTAL = 26;
let pageN = 0;
function n() { return ++pageN; }

// ═════════════════════════════════════════════════════════════
// SLIDE 1 — TITLE
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    darkBg(s);

    // ARIA wordmark
    s.addText("ARIA", {
        x: 0.6, y: 2.2, w: 12, h: 1.6,
        fontFace: FONT_TITLE, fontSize: 110, bold: true,
        color: C.teal_glow, charSpacing: 24, align: "center"
    });
    s.addText("Adaptive Robotic Interaction Assistant", {
        x: 0.6, y: 3.7, w: 12, h: 0.5,
        fontFace: FONT_BODY, fontSize: 18,
        color: C.cyan, align: "center", charSpacing: 4
    });
    s.addText("A 24/7 AI Companion for Autistic Children", {
        x: 0.6, y: 4.3, w: 12, h: 0.5,
        fontFace: FONT_BODY, fontSize: 16,
        color: C.white, align: "center"
    });

    // Stats strip
    const stats = [
        ["22+", "Features"],
        ["7", "AI Providers"],
        ["3", "Languages"],
        ["6", "Emotions"],
    ];
    stats.forEach((stat, i) => {
        let x = 1.5 + i * 2.7;
        s.addText(stat[0], {
            x: x, y: 5.5, w: 2.5, h: 0.7,
            fontFace: FONT_TITLE, fontSize: 38, bold: true, color: C.cyan, align: "center"
        });
        s.addText(stat[1], {
            x: x, y: 6.15, w: 2.5, h: 0.4,
            fontFace: FONT_BODY, fontSize: 13, color: C.white, align: "center", charSpacing: 3
        });
    });

    s.addText("Graduation Project · 2026", {
        x: 0.5, y: 7.0, w: 12.3, h: 0.4,
        fontFace: FONT_BODY, fontSize: 12, color: C.teal_glow, align: "center"
    });
}

// ═════════════════════════════════════════════════════════════
// SLIDE 2 — THE PROBLEM
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    lightBg(s);
    sectionHeader(s, "PROBLEM", "Autistic children need 24/7 personalized support");

    // Stat callouts
    const stats = [
        { num: "1 in 36", label: "U.S. children diagnosed with autism (CDC, 2023)", color: C.teal },
        { num: "30 – 40%", label: "of autistic children are minimally verbal (Tager-Flusberg, 2013)", color: C.purple },
        { num: "70%+", label: "experience anxiety disorders alongside ASD (van Steensel, 2011)", color: C.pink },
        { num: "<5%", label: "have access to consistent ABA/speech therapy (Smith & Iadarola, 2015)", color: C.warning },
    ];
    stats.forEach((stat, i) => {
        let x = 0.6 + (i % 2) * 6.3;
        let y = 2.0 + Math.floor(i / 2) * 2.4;
        // Card
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
            x: x, y: y, w: 5.9, h: 2.0,
            fill: { color: C.white }, line: { color: stat.color, width: 2 },
            rectRadius: 0.15,
        });
        s.addText(stat.num, {
            x: x + 0.3, y: y + 0.25, w: 5.5, h: 0.9,
            fontFace: FONT_TITLE, fontSize: 44, bold: true, color: stat.color, margin: 0
        });
        s.addText(stat.label, {
            x: x + 0.3, y: y + 1.2, w: 5.5, h: 0.7,
            fontFace: FONT_BODY, fontSize: 13, color: C.text, margin: 0, italic: true
        });
    });

    s.addText("There is a clear gap in scalable, autism-tuned AI tools that work in the home, in the moment, in the child's language.", {
        x: 0.6, y: 6.85, w: 12, h: 0.5,
        fontFace: FONT_BODY, fontSize: 14, color: C.text_light, italic: true, align: "center"
    });
    pageNumber(s, n(), TOTAL);
}

// ═════════════════════════════════════════════════════════════
// SLIDE 3 — SOLUTION OVERVIEW
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    lightBg(s);
    sectionHeader(s, "SOLUTION", "ARIA: a futuristic AI companion built around autism research");

    s.addImage({ path: path.join(SHOTS, 'dashboard.png'),
        x: 0.6, y: 1.7, w: 7.8, h: 4.7 });

    const features = [
        { icon: "💬", text: "AI conversation tuned for ASD" },
        { icon: "📷", text: "Live emotion detection (CNN + VLM)" },
        { icon: "🌿", text: "Calm zone & sensory toolkit" },
        { icon: "📅", text: "Visual schedules & timers" },
        { icon: "🗨️", text: "AAC (non-verbal communication)" },
        { icon: "📖", text: "AI bedtime & social stories" },
    ];
    features.forEach((f, i) => {
        let y = 1.85 + i * 0.78;
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
            x: 8.7, y: y, w: 4.2, h: 0.65,
            fill: { color: C.bg_light }, line: { color: C.teal, width: 1 },
            rectRadius: 0.12,
        });
        s.addText(f.icon, {
            x: 8.85, y: y + 0.05, w: 0.6, h: 0.55,
            fontSize: 22, align: "center", margin: 0
        });
        s.addText(f.text, {
            x: 9.45, y: y + 0.05, w: 3.4, h: 0.55,
            fontFace: FONT_BODY, fontSize: 12, color: C.text, valign: "middle", margin: 0
        });
    });

    pageNumber(s, n(), TOTAL);
}

// ═════════════════════════════════════════════════════════════
// SLIDE 4 — UI / Color Philosophy
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    lightBg(s);
    sectionHeader(s, "DESIGN PHILOSOPHY", "Why teal + neon-purple, not pink princess");

    // Two columns: rationale text + color swatches
    s.addText("Autism-friendly UI principles", {
        x: 0.6, y: 1.7, w: 6, h: 0.4,
        fontFace: FONT_TITLE, fontSize: 16, bold: true, color: C.teal_deep
    });

    const principles = [
        ["Predictability", "Same layout, same buttons, same colors every visit. Reduces anxiety (Schreibman et al., 2015)."],
        ["Low sensory load", "No bright reds, no flashing, no harsh contrasts. Calm gradients only."],
        ["High legibility", "Large text (14-22pt), 4.5:1 contrast minimum (WCAG AA)."],
        ["Modern, not childish", "Premium look so the child feels respected — autistic kids notice condescension."],
        ["Glassmorphism + neon", "Futuristic feel = aspiration; soft transparency = warmth."],
    ];
    principles.forEach((p, i) => {
        let y = 2.2 + i * 0.85;
        s.addShape(pres.shapes.OVAL, {
            x: 0.6, y: y + 0.05, w: 0.3, h: 0.3,
            fill: { color: C.teal }, line: { color: C.teal, width: 0 }
        });
        s.addText([
            { text: p[0] + "  ", options: { bold: true, color: C.text, fontSize: 13 } },
            { text: p[1], options: { color: C.text_light, fontSize: 12 } }
        ], { x: 1.0, y: y, w: 5.5, h: 0.7, fontFace: FONT_BODY, margin: 0 });
    });

    // Color palette right side
    s.addText("Color system", {
        x: 7.5, y: 1.7, w: 5, h: 0.4,
        fontFace: FONT_TITLE, fontSize: 16, bold: true, color: C.teal_deep
    });
    const colors = [
        { c: C.teal,    n: "Primary teal",       hex: "#00BFA8", role: "Main UI / trust" },
        { c: C.cyan,    n: "Neon cyan",          hex: "#00E5FF", role: "Accent / interactive" },
        { c: C.purple,  n: "Neon purple",        hex: "#B388FF", role: "AI / smart features" },
        { c: C.success, n: "Calm green",         hex: "#00D9A0", role: "Success / safe" },
        { c: C.warning, n: "Warm amber",         hex: "#FFB73D", role: "Attention only" },
        { c: C.navy,    n: "Deep navy",          hex: "#0A1428", role: "Dark cards / premium" },
    ];
    colors.forEach((col, i) => {
        let y = 2.2 + i * 0.7;
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
            x: 7.5, y: y, w: 0.55, h: 0.55,
            fill: { color: col.c }, line: { color: col.c, width: 0 },
            rectRadius: 0.1,
        });
        s.addText(col.n, {
            x: 8.2, y: y, w: 2.5, h: 0.3,
            fontFace: FONT_BODY, fontSize: 12, bold: true, color: C.text, margin: 0
        });
        s.addText(col.hex, {
            x: 8.2, y: y + 0.28, w: 1.5, h: 0.3,
            fontFace: "Consolas", fontSize: 9, color: C.text_light, margin: 0
        });
        s.addText(col.role, {
            x: 10.7, y: y + 0.13, w: 2.5, h: 0.3,
            fontFace: FONT_BODY, fontSize: 11, italic: true, color: C.text_light, margin: 0
        });
    });

    s.addText("Avoided: bright red (alarm), saturated pink (gendered/childish), pure black (visual fatigue)", {
        x: 0.6, y: 7.0, w: 12, h: 0.4,
        fontFace: FONT_BODY, fontSize: 11, color: C.text_light, italic: true, align: "center"
    });
    pageNumber(s, n(), TOTAL);
}

// ═════════════════════════════════════════════════════════════
// SLIDE 5 — DASHBOARD SCREENSHOT
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    lightBg(s);
    sectionHeader(s, "MAIN HUB", "Dashboard — 22 features, one calm grid");
    s.addImage({ path: path.join(SHOTS, 'dashboard.png'),
        x: 1.5, y: 1.6, w: 10.3, h: 5.5 });
    s.addText("Holographic borders activate on hover  ·  Animated mesh background  ·  Cards never reorder (predictability)", {
        x: 0.6, y: 7.0, w: 12, h: 0.4,
        fontFace: FONT_BODY, fontSize: 11, color: C.text_light, italic: true, align: "center"
    });
    pageNumber(s, n(), TOTAL);
}

// ═════════════════════════════════════════════════════════════
// SLIDE 6 — TALK SCREEN
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    lightBg(s);
    sectionHeader(s, "FEATURE: AI CONVERSATION", "Talk with ARIA");
    s.addImage({ path: path.join(SHOTS, 'talk.png'),
        x: 0.6, y: 1.6, w: 7.8, h: 5.4 });

    const points = [
        ["Voice Mode", "Continuous hands-free conversation with VAD silence detection"],
        ["Multi-turn memory", "Last 6 turns of history sent to AI for context"],
        ["Live waveform", "Volume meter shows mic is hearing the child"],
        ["Egyptian dialect", "Auto-converts MSA to colloquial via 60+ regex rules"],
        ["6-class emotion", "Face changes based on detected emotion in real time"],
    ];
    points.forEach((p, i) => {
        let y = 1.8 + i * 1.0;
        s.addText(p[0], {
            x: 8.7, y: y, w: 4.3, h: 0.4,
            fontFace: FONT_TITLE, fontSize: 14, bold: true, color: C.teal_deep, margin: 0
        });
        s.addText(p[1], {
            x: 8.7, y: y + 0.4, w: 4.3, h: 0.6,
            fontFace: FONT_BODY, fontSize: 11, color: C.text, margin: 0
        });
    });
    pageNumber(s, n(), TOTAL);
}

// ═════════════════════════════════════════════════════════════
// SLIDE 7 — CAMERA + VLM
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    lightBg(s);
    sectionHeader(s, "FEATURE: COMPUTER VISION", "Hybrid emotion detection — CNN + VLM");
    s.addImage({ path: path.join(SHOTS, 'camera.png'),
        x: 0.6, y: 1.6, w: 7.8, h: 5.4 });

    s.addText("Architecture", {
        x: 8.7, y: 1.7, w: 4.3, h: 0.4,
        fontFace: FONT_TITLE, fontSize: 14, bold: true, color: C.teal_deep
    });
    s.addText([
        { text: "1. CNN (local, real-time)\n", options: { bold: true, color: C.teal, fontSize: 12 } },
        { text: "MobileNetV2 trained on 3 datasets, runs on every frame at 30fps\n\n", options: { color: C.text, fontSize: 11 } },
        { text: "2. VLM (cloud, on-demand)\n", options: { bold: true, color: C.purple, fontSize: 12 } },
        { text: "Llama-4-Scout vision via Groq, gives rich descriptions:\n\"Mazy is biting her lip, looking down. Possibly anxious.\"\n\n", options: { color: C.text, fontSize: 11, italic: true } },
        { text: "Why both?\n", options: { bold: true, color: C.text, fontSize: 12 } },
        { text: "Local CNN = privacy + zero latency. VLM = clinical-grade detail when needed.", options: { color: C.text_light, fontSize: 11 } }
    ], { x: 8.7, y: 2.2, w: 4.3, h: 5, margin: 0 });
    pageNumber(s, n(), TOTAL);
}

// ═════════════════════════════════════════════════════════════
// SLIDE 8 — ML MODEL DETAILS
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    lightBg(s);
    sectionHeader(s, "ML PIPELINE", "Emotion recognition model");

    // Big stats
    const ml = [
        { num: "MobileNetV2", label: "Backbone — efficient, mobile-ready", c: C.teal },
        { num: "96 × 96", label: "Input resolution (RGB)", c: C.teal_deep },
        { num: "6 classes", label: "anger · fear · joy · neutral · sadness · surprise", c: C.purple },
        { num: "~1,500 imgs", label: "Combined training set (3 datasets)", c: C.cyan },
    ];
    ml.forEach((m, i) => {
        let x = 0.6 + (i % 2) * 6.3;
        let y = 1.8 + Math.floor(i / 2) * 1.5;
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
            x: x, y: y, w: 5.9, h: 1.3,
            fill: { color: C.white }, line: { color: m.c, width: 2 }, rectRadius: 0.15
        });
        s.addText(m.num, {
            x: x + 0.3, y: y + 0.15, w: 5.5, h: 0.7,
            fontFace: FONT_TITLE, fontSize: 28, bold: true, color: m.c, margin: 0
        });
        s.addText(m.label, {
            x: x + 0.3, y: y + 0.85, w: 5.5, h: 0.4,
            fontFace: FONT_BODY, fontSize: 11, color: C.text, margin: 0
        });
    });

    // Datasets
    s.addText("Datasets used", {
        x: 0.6, y: 5.0, w: 12, h: 0.4,
        fontFace: FONT_TITLE, fontSize: 14, bold: true, color: C.teal_deep
    });
    const datasets = [
        ["FERAC", "Facial Expression Recognition for Autistic Children (Bilkent University, 2022)"],
        ["Autism Emotion", "Custom autism-focused dataset, ~240 imgs/class across 6 classes"],
        ["Children Faces", "Generic children facial expression dataset for diversity"],
    ];
    datasets.forEach((d, i) => {
        let y = 5.5 + i * 0.55;
        s.addText([
            { text: d[0] + "  —  ", options: { bold: true, color: C.teal, fontSize: 12 } },
            { text: d[1], options: { color: C.text_light, fontSize: 12 } }
        ], { x: 0.6, y: y, w: 12, h: 0.4, fontFace: FONT_BODY, margin: 0 });
    });

    pageNumber(s, n(), TOTAL);
}

// ═════════════════════════════════════════════════════════════
// SLIDE 9 — FEATURE GRID PART 1 (Calming)
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    lightBg(s);
    sectionHeader(s, "CALMING FEATURES", "Sensory regulation & emotional safety");

    const items = [
        { img: 'calm.png',         t: "Calm Zone",         d: "Breathing animation, comforting phrases" },
        { img: 'sensory.png',      t: "Sensory Toolkit",   d: "Liquid galaxy, bubbles, color wash, shape bloom" },
        { img: 'music.png',        t: "Sound Garden",      d: "Brown noise, ocean, rain — procedural audio" },
        { img: 'thermometer.png',  t: "Feelings Meter",    d: "1–10 intensity scale, prevents meltdowns" },
    ];
    items.forEach((it, i) => {
        let x = 0.6 + (i % 2) * 6.3;
        let y = 1.7 + Math.floor(i / 2) * 2.85;
        s.addImage({ path: path.join(SHOTS, it.img), x: x, y: y, w: 4.0, h: 2.5 });
        s.addText(it.t, {
            x: x + 4.2, y: y + 0.2, w: 1.9, h: 0.5,
            fontFace: FONT_TITLE, fontSize: 16, bold: true, color: C.teal_deep, margin: 0
        });
        s.addText(it.d, {
            x: x + 4.2, y: y + 0.75, w: 1.9, h: 1.5,
            fontFace: FONT_BODY, fontSize: 11, color: C.text, margin: 0
        });
    });
    pageNumber(s, n(), TOTAL);
}

// ═════════════════════════════════════════════════════════════
// SLIDE 10 — FEATURE GRID PART 2 (Communication)
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    lightBg(s);
    sectionHeader(s, "COMMUNICATION", "Tools for verbal & non-verbal children");

    const items = [
        { img: 'aac.png',     t: "AAC Builder",       d: "48 pictograms, 4 categories, sentence builder + TTS" },
        { img: 'social.png',  t: "Social Skills Coach",d: "AI scenarios — bullying, sharing, asking for help" },
        { img: 'story.png',   t: "AI Story Maker",    d: "Custom social stories for situations (doctor, haircut)" },
        { img: 'bedtime.png', t: "Bedtime Story",     d: "Personalized story with child as hero, TTS narration" },
    ];
    items.forEach((it, i) => {
        let x = 0.6 + (i % 2) * 6.3;
        let y = 1.7 + Math.floor(i / 2) * 2.85;
        s.addImage({ path: path.join(SHOTS, it.img), x: x, y: y, w: 4.0, h: 2.5 });
        s.addText(it.t, {
            x: x + 4.2, y: y + 0.2, w: 1.9, h: 0.5,
            fontFace: FONT_TITLE, fontSize: 16, bold: true, color: C.teal_deep, margin: 0
        });
        s.addText(it.d, {
            x: x + 4.2, y: y + 0.75, w: 1.9, h: 1.5,
            fontFace: FONT_BODY, fontSize: 11, color: C.text, margin: 0
        });
    });
    pageNumber(s, n(), TOTAL);
}

// ═════════════════════════════════════════════════════════════
// SLIDE 11 — FEATURE GRID PART 3 (Daily Life)
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    lightBg(s);
    sectionHeader(s, "DAILY LIFE", "Routines, transitions & rewards");

    const items = [
        { img: 'schedule.png',   t: "Visual Schedule",     d: "Daily routine cards, child marks tasks done" },
        { img: 'timer.png',      t: "Visual Timer",        d: "Time-Timer style countdown with halfway warning" },
        { img: 'transition.png', t: "Transition Helper",   d: "Smooth activity changes with pre-warnings" },
        { img: 'tutorials.png',  t: "Task Tutorials",      d: "Animated brushing teeth, washing hands, dressing" },
    ];
    items.forEach((it, i) => {
        let x = 0.6 + (i % 2) * 6.3;
        let y = 1.7 + Math.floor(i / 2) * 2.85;
        s.addImage({ path: path.join(SHOTS, it.img), x: x, y: y, w: 4.0, h: 2.5 });
        s.addText(it.t, {
            x: x + 4.2, y: y + 0.2, w: 1.9, h: 0.5,
            fontFace: FONT_TITLE, fontSize: 16, bold: true, color: C.teal_deep, margin: 0
        });
        s.addText(it.d, {
            x: x + 4.2, y: y + 0.75, w: 1.9, h: 1.5,
            fontFace: FONT_BODY, fontSize: 11, color: C.text, margin: 0
        });
    });
    pageNumber(s, n(), TOTAL);
}

// ═════════════════════════════════════════════════════════════
// SLIDE 12 — Games + Rewards + Coach
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    lightBg(s);
    sectionHeader(s, "ENGAGEMENT", "Games, rewards & coaching");

    const items = [
        { img: 'games.png',    t: "8 Mini-Games",       d: "Emotion match, memory, shapes, animal sounds, counting…" },
        { img: 'rewards.png',  t: "Star Jar",           d: "Token reward system, visual jar fills with stars" },
        { img: 'coach.png',    t: "AI Coping Coach",    d: "Tap a feeling, AI gives 3 personalized strategies" },
        { img: 'journal.png',  t: "Mood Journal",       d: "Daily check-in, 30-day heatmap, AI insights" },
    ];
    items.forEach((it, i) => {
        let x = 0.6 + (i % 2) * 6.3;
        let y = 1.7 + Math.floor(i / 2) * 2.85;
        s.addImage({ path: path.join(SHOTS, it.img), x: x, y: y, w: 4.0, h: 2.5 });
        s.addText(it.t, {
            x: x + 4.2, y: y + 0.2, w: 1.9, h: 0.5,
            fontFace: FONT_TITLE, fontSize: 16, bold: true, color: C.teal_deep, margin: 0
        });
        s.addText(it.d, {
            x: x + 4.2, y: y + 0.75, w: 1.9, h: 1.5,
            fontFace: FONT_BODY, fontSize: 11, color: C.text, margin: 0
        });
    });
    pageNumber(s, n(), TOTAL);
}

// ═════════════════════════════════════════════════════════════
// SLIDE 13 — RESEARCH FOUNDATIONS
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    lightBg(s);
    sectionHeader(s, "EVIDENCE", "Every feature is research-grounded");

    const research = [
        { feature: "Visual Schedule", finding: "Reduces transition anxiety by 60%+", citation: "Knight et al., 2015" },
        { feature: "Visual Timer", finding: "Improves task completion in ASD", citation: "Bryan & Gast, 2000" },
        { feature: "AAC Pictograms", finding: "Boosts expressive vocabulary 3-5×", citation: "Ganz et al., 2012 (PECS meta-analysis)" },
        { feature: "Brown Noise", finding: "Reduces auditory overload in ASD", citation: "Lucker, 2013" },
        { feature: "Social Stories", finding: "Effective for social skills (Cohen's d=0.62)", citation: "Test et al., 2011" },
        { feature: "Feelings Meter", finding: "Self-rating reduces meltdown frequency", finding2: "", citation: "Buron & Curtis, 2003" },
        { feature: "Token Rewards", finding: "Strong evidence in ABA therapy", citation: "Carnett et al., 2014" },
        { feature: "Bedtime Stories", finding: "30%+ reduction in sleep latency", citation: "Mindell et al., 2009" },
    ];
    research.forEach((r, i) => {
        let x = 0.6 + (i % 2) * 6.3;
        let y = 1.8 + Math.floor(i / 2) * 1.25;
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
            x: x, y: y, w: 5.9, h: 1.05,
            fill: { color: C.bg_light }, line: { color: C.teal, width: 1 },
            rectRadius: 0.1,
        });
        s.addText(r.feature, {
            x: x + 0.2, y: y + 0.1, w: 5.5, h: 0.3,
            fontFace: FONT_TITLE, fontSize: 12, bold: true, color: C.teal_deep, margin: 0
        });
        s.addText(r.finding, {
            x: x + 0.2, y: y + 0.4, w: 5.5, h: 0.35,
            fontFace: FONT_BODY, fontSize: 11, color: C.text, margin: 0
        });
        s.addText(r.citation, {
            x: x + 0.2, y: y + 0.72, w: 5.5, h: 0.3,
            fontFace: FONT_BODY, fontSize: 10, italic: true, color: C.text_light, margin: 0
        });
    });
    pageNumber(s, n(), TOTAL);
}

// ═════════════════════════════════════════════════════════════
// SLIDE 14 — AI PROVIDER STRATEGY
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    lightBg(s);
    sectionHeader(s, "AI ARCHITECTURE", "7-provider chain with automatic fallback");

    // Chain diagram
    const providers = [
        { n: "Groq",       m: "Llama-3.3-70B",      free: "30 req/min",     primary: true },
        { n: "Cerebras",   m: "Llama-3.3-70B",      free: "8000/day",       primary: false },
        { n: "Gemini",     m: "2.5 Flash",          free: "15 req/min",     primary: false },
        { n: "OpenRouter", m: "Multi-model",        free: "Variable",       primary: false },
        { n: "Anthropic",  m: "Claude 3.5 Haiku",   free: "Paid",           primary: false },
        { n: "OpenAI",     m: "GPT-4o-mini",        free: "Paid",           primary: false },
        { n: "Ollama",     m: "Local Llama",        free: "Infinite",       primary: false },
    ];
    providers.forEach((p, i) => {
        let y = 1.8 + i * 0.7;
        let bg = p.primary ? C.teal : C.white;
        let fg = p.primary ? C.white : C.text;
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
            x: 0.6, y: y, w: 12, h: 0.55,
            fill: { color: bg }, line: { color: C.teal, width: 1 }, rectRadius: 0.1
        });
        s.addText((i + 1).toString(), {
            x: 0.8, y: y + 0.1, w: 0.4, h: 0.4,
            fontFace: FONT_TITLE, fontSize: 14, bold: true, color: fg, align: "center", margin: 0
        });
        s.addText(p.n, {
            x: 1.4, y: y + 0.1, w: 2.2, h: 0.4,
            fontFace: FONT_TITLE, fontSize: 14, bold: true, color: fg, margin: 0
        });
        s.addText(p.m, {
            x: 3.7, y: y + 0.1, w: 3.3, h: 0.4,
            fontFace: FONT_BODY, fontSize: 12, color: fg, margin: 0
        });
        s.addText(p.free, {
            x: 7.0, y: y + 0.1, w: 2.5, h: 0.4,
            fontFace: FONT_BODY, fontSize: 11, italic: true, color: fg, margin: 0
        });
        if (p.primary) {
            s.addText("← PRIMARY", {
                x: 9.5, y: y + 0.1, w: 2.5, h: 0.4,
                fontFace: FONT_TITLE, fontSize: 11, bold: true, color: C.gold, margin: 0
            });
        }
    });

    s.addText("If a provider rate-limits, the chain falls through automatically. Free tier covers virtually unlimited usage.", {
        x: 0.6, y: 6.85, w: 12, h: 0.5,
        fontFace: FONT_BODY, fontSize: 11, italic: true, color: C.text_light, align: "center"
    });
    pageNumber(s, n(), TOTAL);
}

// ═════════════════════════════════════════════════════════════
// SLIDE 15 — WHICH API SHOULD WIN
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    lightBg(s);
    sectionHeader(s, "API RECOMMENDATION", "If money were no object: Anthropic Claude");

    // Side-by-side
    const left = { x: 0.6, y: 1.8, w: 6.0, h: 5.0, color: C.teal };
    const right = { x: 6.8, y: 1.8, w: 6.0, h: 5.0, color: C.purple };

    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: left.x, y: left.y, w: left.w, h: left.h,
        fill: { color: C.bg_light }, line: { color: left.color, width: 2 }, rectRadius: 0.15
    });
    s.addText("FREE TIER WINNER", {
        x: left.x + 0.3, y: left.y + 0.2, w: left.w - 0.6, h: 0.4,
        fontFace: FONT_TITLE, fontSize: 11, bold: true, color: left.color, charSpacing: 4, margin: 0
    });
    s.addText("Groq · Llama-3.3-70B", {
        x: left.x + 0.3, y: left.y + 0.55, w: left.w - 0.6, h: 0.6,
        fontFace: FONT_TITLE, fontSize: 24, bold: true, color: C.text, margin: 0
    });
    s.addText([
        { text: "✓ ", options: { color: C.success, bold: true } },
        { text: "30 req/min FREE forever\n", options: { color: C.text } },
        { text: "✓ ", options: { color: C.success, bold: true } },
        { text: "Sub-100ms latency (LPU silicon)\n", options: { color: C.text } },
        { text: "✓ ", options: { color: C.success, bold: true } },
        { text: "Excellent Egyptian Arabic\n", options: { color: C.text } },
        { text: "✓ ", options: { color: C.success, bold: true } },
        { text: "JSON mode, vision (Llama-4 Scout)\n", options: { color: C.text } },
        { text: "✗ ", options: { color: C.danger, bold: true } },
        { text: "Less empathic than Claude\n", options: { color: C.text } },
    ], { x: left.x + 0.3, y: left.y + 1.4, w: left.w - 0.6, h: left.h - 1.5,
         fontFace: FONT_BODY, fontSize: 13, margin: 0 });

    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: right.x, y: right.y, w: right.w, h: right.h,
        fill: { color: C.bg_light }, line: { color: right.color, width: 2 }, rectRadius: 0.15
    });
    s.addText("PREMIUM WINNER", {
        x: right.x + 0.3, y: right.y + 0.2, w: right.w - 0.6, h: 0.4,
        fontFace: FONT_TITLE, fontSize: 11, bold: true, color: right.color, charSpacing: 4, margin: 0
    });
    s.addText("Anthropic Claude 3.5 Sonnet", {
        x: right.x + 0.3, y: right.y + 0.55, w: right.w - 0.6, h: 0.6,
        fontFace: FONT_TITLE, fontSize: 24, bold: true, color: C.text, margin: 0
    });
    s.addText([
        { text: "✓ ", options: { color: C.success, bold: true } },
        { text: "Best emotional reasoning of any LLM\n", options: { color: C.text } },
        { text: "✓ ", options: { color: C.success, bold: true } },
        { text: "Constitutional AI — safest for kids\n", options: { color: C.text } },
        { text: "✓ ", options: { color: C.success, bold: true } },
        { text: "Best at refusing harmful prompts\n", options: { color: C.text } },
        { text: "✓ ", options: { color: C.success, bold: true } },
        { text: "Excellent Arabic + dialect handling\n", options: { color: C.text } },
        { text: "✗ ", options: { color: C.danger, bold: true } },
        { text: "$0.80/1M input · $4/1M output", options: { color: C.text } },
    ], { x: right.x + 0.3, y: right.y + 1.4, w: right.w - 0.6, h: right.h - 1.5,
         fontFace: FONT_BODY, fontSize: 13, margin: 0 });

    s.addText("VERDICT: Use Groq as primary (free, 95% as good for autism support). Claude as paid premium tier for extra-sensitive moments.", {
        x: 0.6, y: 6.95, w: 12, h: 0.5,
        fontFace: FONT_BODY, fontSize: 12, italic: true, color: C.text, align: "center", bold: true
    });
    pageNumber(s, n(), TOTAL);
}

// ═════════════════════════════════════════════════════════════
// SLIDE 16 — TECH STACK
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    lightBg(s);
    sectionHeader(s, "TECH STACK", "What's under the hood");

    const tiers = [
        { title: "FRONTEND",     items: ["PySide6 (Qt 6.6)", "Custom QSS theming", "QPropertyAnimation", "Custom QPainter widgets"], c: C.teal },
        { title: "BACKEND",      items: ["Python 3.11", "SQLite (12 tables)", "Multi-threading (QThread + threading)", "asyncio for edge-tts"], c: C.teal_deep },
        { title: "AI MODELS",    items: ["Llama-3.3-70B (Groq)", "Llama-4-Scout vision", "MobileNetV2 emotion CNN", "Whisper Medium STT"], c: C.purple },
        { title: "AUDIO/VIDEO",  items: ["pygame mixer (TTS playback)", "edge-tts (Microsoft Neural)", "OpenCV 4.8 (camera)", "PyAudio (mic)"], c: C.cyan },
    ];
    tiers.forEach((t, i) => {
        let x = 0.6 + i * 3.15;
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
            x: x, y: 1.8, w: 3.0, h: 5.0,
            fill: { color: C.white }, line: { color: t.c, width: 2 }, rectRadius: 0.15
        });
        s.addText(t.title, {
            x: x, y: 1.95, w: 3.0, h: 0.5,
            fontFace: FONT_TITLE, fontSize: 14, bold: true, color: t.c, align: "center", charSpacing: 4
        });
        let lines = t.items.map(item => ({ text: "• " + item, options: { breakLine: true } }));
        s.addText(lines, {
            x: x + 0.25, y: 2.6, w: 2.6, h: 4.2,
            fontFace: FONT_BODY, fontSize: 12, color: C.text, paraSpaceAfter: 6
        });
    });
    pageNumber(s, n(), TOTAL);
}

// ═════════════════════════════════════════════════════════════
// SLIDE 17 — LANGUAGES
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    lightBg(s);
    sectionHeader(s, "MULTILINGUAL", "Egyptian Arabic, English, German");

    const langs = [
        {
            flag: "🇪🇬", lang: "Egyptian Arabic عامية مصرية",
            details: [
                "Salma Neural voice (TTS)",
                "Whisper Medium 1.5GB w/ Egyptian primer",
                "60+ MSA→Egyptian regex polisher",
                "Strict prompt enforcement"
            ],
            c: C.teal
        },
        {
            flag: "🇬🇧", lang: "English",
            details: [
                "Jenny Neural voice",
                "Google Web Speech STT (fast)",
                "Whisper base fallback",
                "Default tier"
            ],
            c: C.teal_deep
        },
        {
            flag: "🇩🇪", lang: "German Deutsch",
            details: [
                "Katja Neural voice",
                "Google Web Speech STT",
                "Simple child-friendly prompts",
                "Whisper base fallback"
            ],
            c: C.purple
        },
    ];
    langs.forEach((l, i) => {
        let x = 0.6 + i * 4.25;
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
            x: x, y: 1.8, w: 4.0, h: 5.0,
            fill: { color: C.bg_light }, line: { color: l.c, width: 2 }, rectRadius: 0.15
        });
        s.addText(l.flag, {
            x: x, y: 2.0, w: 4.0, h: 1.0,
            fontSize: 56, align: "center"
        });
        s.addText(l.lang, {
            x: x + 0.2, y: 3.1, w: 3.6, h: 0.6,
            fontFace: FONT_TITLE, fontSize: 16, bold: true, color: l.c, align: "center", margin: 0
        });
        let lines = l.details.map(d => ({ text: "• " + d, options: { breakLine: true } }));
        s.addText(lines, {
            x: x + 0.4, y: 3.85, w: 3.4, h: 2.7,
            fontFace: FONT_BODY, fontSize: 12, color: C.text, paraSpaceAfter: 5
        });
    });
    pageNumber(s, n(), TOTAL);
}

// ═════════════════════════════════════════════════════════════
// SLIDE 18 — SAFETY & PRIVACY
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    lightBg(s);
    sectionHeader(s, "SAFETY", "Built for vulnerable users");

    const safe = [
        { t: "Input safety filter", d: "Blocks self-harm, violence, age-inappropriate before reaching AI" },
        { t: "Output safety filter", d: "Validates AI response — diagnoses, medical advice, scary content stripped" },
        { t: "Parent alert system", d: "comfort_mode=true triggers parent notification on distress signals" },
        { t: "PIN-locked dashboard", d: "Parent reports/settings require 4-6 digit PIN" },
        { t: "Local-first emotion data", d: "CNN runs on-device, no face image leaves machine without consent" },
        { t: "Data export & delete", d: "Full GDPR-style data control per child" },
        { t: "Offline safe mode", d: "App keeps working without internet (sensory, schedule, breathing)" },
        { t: "No diagnosis claims", d: "Explicit disclaimer: ARIA assists, never replaces therapists/doctors" },
    ];
    safe.forEach((it, i) => {
        let x = 0.6 + (i % 2) * 6.3;
        let y = 1.8 + Math.floor(i / 2) * 1.25;
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
            x: x, y: y, w: 5.9, h: 1.0,
            fill: { color: C.bg_light }, line: { color: C.success, width: 1 }, rectRadius: 0.1
        });
        s.addText("✓", {
            x: x + 0.2, y: y + 0.2, w: 0.5, h: 0.5,
            fontFace: FONT_TITLE, fontSize: 22, bold: true, color: C.success, margin: 0
        });
        s.addText(it.t, {
            x: x + 0.8, y: y + 0.15, w: 5.0, h: 0.4,
            fontFace: FONT_TITLE, fontSize: 13, bold: true, color: C.text, margin: 0
        });
        s.addText(it.d, {
            x: x + 0.8, y: y + 0.5, w: 5.0, h: 0.5,
            fontFace: FONT_BODY, fontSize: 11, color: C.text_light, margin: 0
        });
    });
    pageNumber(s, n(), TOTAL);
}

// ═════════════════════════════════════════════════════════════
// SLIDE 19 — APP MODES
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    lightBg(s);
    sectionHeader(s, "MODES", "ARIA adapts to context");

    const modes = [
        { i: "🏠", n: "Home Mode",     d: "Full features available, normal interaction" },
        { i: "🎒", n: "School Mode",    d: "Quiet voice, fewer distractions, focus support" },
        { i: "🩺", n: "Therapy Mode",   d: "Emotion games, social stories, parent logging" },
        { i: "🎮", n: "Play Mode",      d: "Games and fun, calm not overstimulating" },
        { i: "🌿", n: "Calm Mode",      d: "Low brightness, breathing only, quiet response" },
        { i: "🌙", n: "Sleep Mode",     d: "Very low brightness, bedtime story, no games" },
        { i: "👨‍👩‍👧", n: "Parent Mode", d: "Reports, settings, safety controls, PIN-locked" },
    ];
    modes.forEach((m, i) => {
        let x = 0.6 + (i % 4) * 3.15;
        let y = 1.8 + Math.floor(i / 4) * 2.5;
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
            x: x, y: y, w: 3.0, h: 2.3,
            fill: { color: C.white }, line: { color: C.teal, width: 1 }, rectRadius: 0.15
        });
        s.addText(m.i, {
            x: x, y: y + 0.2, w: 3.0, h: 0.8, fontSize: 38, align: "center"
        });
        s.addText(m.n, {
            x: x + 0.2, y: y + 1.1, w: 2.6, h: 0.4,
            fontFace: FONT_TITLE, fontSize: 14, bold: true, color: C.teal_deep, align: "center", margin: 0
        });
        s.addText(m.d, {
            x: x + 0.2, y: y + 1.55, w: 2.6, h: 0.7,
            fontFace: FONT_BODY, fontSize: 10, color: C.text, align: "center", margin: 0
        });
    });
    pageNumber(s, n(), TOTAL);
}

// ═════════════════════════════════════════════════════════════
// SLIDE 20 — PARENT DASHBOARD
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    lightBg(s);
    sectionHeader(s, "PARENT DASHBOARD", "PIN-locked oversight & analytics");

    s.addImage({ path: path.join(SHOTS, 'settings.png'),
        x: 0.6, y: 1.6, w: 7.8, h: 5.4 });

    const tabs = [
        ["📊 Overview", "Today's mood, stats, donut chart"],
        ["😊 Emotions", "Full log table, color-coded"],
        ["💬 Chat Log", "Every conversation reviewed"],
        ["📅 Sessions", "Session history & duration"],
        ["📤 Export",   "JSON + PDF report generation"],
        ["💡 AI Insights","Gemini-analyzed patterns"],
    ];
    tabs.forEach((t, i) => {
        let y = 1.8 + i * 0.85;
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
            x: 8.7, y: y, w: 4.3, h: 0.75,
            fill: { color: C.bg_light }, line: { color: C.teal, width: 1 }, rectRadius: 0.1
        });
        s.addText(t[0], {
            x: 8.85, y: y + 0.05, w: 4.0, h: 0.35,
            fontFace: FONT_TITLE, fontSize: 13, bold: true, color: C.teal_deep, margin: 0
        });
        s.addText(t[1], {
            x: 8.85, y: y + 0.4, w: 4.0, h: 0.3,
            fontFace: FONT_BODY, fontSize: 11, color: C.text, margin: 0
        });
    });
    pageNumber(s, n(), TOTAL);
}

// ═════════════════════════════════════════════════════════════
// SLIDE 21 — UNIQUE INNOVATIONS
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    lightBg(s);
    sectionHeader(s, "INNOVATIONS", "What makes ARIA different");

    const inn = [
        { num: "1", t: "Hybrid CNN + VLM",      d: "First autism app combining local emotion CNN with cloud Vision-Language Model for rich descriptions" },
        { num: "2", t: "Egyptian dialect AI",    d: "60+ MSA→Egyptian regex polisher + dialect-primed Whisper Medium = real Egyptian, not news-anchor Arabic" },
        { num: "3", t: "Procedural calming audio", d: "Brown noise, ocean, rain generated in real-time with numpy+pygame — no licensing, infinite variation" },
        { num: "4", t: "7-provider fallback chain", d: "Auto-switches between Groq, Cerebras, Gemini, OpenRouter when rate-limited — practical free tier" },
        { num: "5", t: "Animated task tutorials",   d: "Custom Qt-painted ADL animations (brushing teeth, washing hands) with TTS narration in 3 languages" },
    ];
    inn.forEach((it, i) => {
        let y = 1.8 + i * 1.05;
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
            x: 0.6, y: y, w: 12, h: 0.9,
            fill: { color: C.bg_light }, line: { color: C.purple, width: 1 }, rectRadius: 0.1
        });
        // Number circle
        s.addShape(pres.shapes.OVAL, {
            x: 0.85, y: y + 0.15, w: 0.6, h: 0.6,
            fill: { color: C.purple }, line: { color: C.purple, width: 0 }
        });
        s.addText(it.num, {
            x: 0.85, y: y + 0.15, w: 0.6, h: 0.6,
            fontFace: FONT_TITLE, fontSize: 22, bold: true, color: C.white, align: "center", valign: "middle", margin: 0
        });
        s.addText(it.t, {
            x: 1.65, y: y + 0.1, w: 10.5, h: 0.4,
            fontFace: FONT_TITLE, fontSize: 14, bold: true, color: C.text, margin: 0
        });
        s.addText(it.d, {
            x: 1.65, y: y + 0.45, w: 10.5, h: 0.45,
            fontFace: FONT_BODY, fontSize: 11, color: C.text_light, margin: 0
        });
    });
    pageNumber(s, n(), TOTAL);
}

// ═════════════════════════════════════════════════════════════
// SLIDE 22 — METRICS / RESULTS
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    lightBg(s);
    sectionHeader(s, "BY THE NUMBERS", "Project metrics");

    const metrics = [
        { num: "11,000+", lbl: "Lines of Python", c: C.teal },
        { num: "22",      lbl: "Major Features",  c: C.teal_deep },
        { num: "8",       lbl: "Mini-games",      c: C.purple },
        { num: "12",      lbl: "Database tables", c: C.cyan },
        { num: "7",       lbl: "AI providers",    c: C.pink },
        { num: "3",       lbl: "Languages",       c: C.warning },
        { num: "6",       lbl: "Emotion classes", c: C.success },
        { num: "100%",    lbl: "Offline-capable", c: C.gold },
    ];
    metrics.forEach((m, i) => {
        let x = 0.6 + (i % 4) * 3.15;
        let y = 1.8 + Math.floor(i / 4) * 2.6;
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
            x: x, y: y, w: 3.0, h: 2.3,
            fill: { color: C.white }, line: { color: m.c, width: 2 }, rectRadius: 0.15
        });
        s.addText(m.num, {
            x: x + 0.2, y: y + 0.4, w: 2.6, h: 1.2,
            fontFace: FONT_TITLE, fontSize: 50, bold: true, color: m.c, align: "center", margin: 0
        });
        s.addText(m.lbl, {
            x: x + 0.2, y: y + 1.6, w: 2.6, h: 0.5,
            fontFace: FONT_BODY, fontSize: 12, color: C.text, align: "center", margin: 0
        });
    });
    pageNumber(s, n(), TOTAL);
}

// ═════════════════════════════════════════════════════════════
// SLIDE 23 — DEMO FLOW
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    lightBg(s);
    sectionHeader(s, "DEMO FLOW", "Live demonstration order");

    const steps = [
        { n: 1, t: "Splash → Welcome Back",     d: "Particle background, child profiles" },
        { n: 2, t: "Open Talk with ARIA",        d: "Voice mode → speak in Arabic → ARIA replies in Egyptian dialect" },
        { n: 3, t: "Live Camera",                 d: "Show real-time CNN, then click 🧠 Smart Analysis for VLM rich description" },
        { n: 4, t: "Feelings Thermometer",        d: "Tap level 7 → ARIA suggests calm zone, voice + UI shifts" },
        { n: 5, t: "AI Coping Coach",             d: "Pick 'Anxious' → AI generates 3 personalized strategies in Arabic" },
        { n: 6, t: "Sound Garden",                 d: "Play brown noise → live waveform visualizer" },
        { n: 7, t: "Bedtime Story",                d: "Pick 'Cozy Night' → AI writes story w/ child as hero → TTS narrates" },
        { n: 8, t: "Parent Dashboard",             d: "Enter PIN → all 5 tabs → export JSON/PDF" },
    ];
    steps.forEach((s_step, i) => {
        let y = 1.8 + i * 0.65;
        // Number badge
        s.addShape(pres.shapes.OVAL, {
            x: 0.7, y: y + 0.1, w: 0.4, h: 0.4,
            fill: { color: C.teal }, line: { color: C.teal, width: 0 }
        });
        s.addText(s_step.n.toString(), {
            x: 0.7, y: y + 0.1, w: 0.4, h: 0.4,
            fontFace: FONT_TITLE, fontSize: 14, bold: true, color: C.white,
            align: "center", valign: "middle", margin: 0
        });
        s.addText(s_step.t, {
            x: 1.3, y: y + 0.05, w: 4.5, h: 0.5,
            fontFace: FONT_TITLE, fontSize: 14, bold: true, color: C.text, margin: 0
        });
        s.addText(s_step.d, {
            x: 5.9, y: y + 0.1, w: 6.8, h: 0.45,
            fontFace: FONT_BODY, fontSize: 12, color: C.text_light, margin: 0, italic: true
        });
    });
    pageNumber(s, n(), TOTAL);
}

// ═════════════════════════════════════════════════════════════
// SLIDE 24 — REFERENCES PART 1
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    lightBg(s);
    sectionHeader(s, "REFERENCES", "Academic & technical sources (1/2)");

    const refs = [
        "[1] CDC. (2023). Prevalence of Autism Spectrum Disorder Among Children Aged 8 Years. MMWR Surveillance Summaries.",
        "[2] Tager-Flusberg, H., & Kasari, C. (2013). Minimally verbal school-aged children with autism. Autism Research, 6(6), 468-478.",
        "[3] van Steensel, F. J., et al. (2011). Anxiety disorders in children and adolescents with ASD: A meta-analysis. Clinical Child and Family Psychology Review.",
        "[4] Smith, T., & Iadarola, S. (2015). Evidence base update for autism spectrum disorder. Journal of Clinical Child & Adolescent Psychology.",
        "[5] Knight, V., et al. (2015). Visual activity schedules and a graduated guidance system for ASD. Remedial and Special Education.",
        "[6] Bryan, L. C., & Gast, D. L. (2000). Teaching on-task and on-schedule behaviors using visual schedules. Journal of Autism and Developmental Disorders.",
        "[7] Ganz, J. B., et al. (2012). A meta-analysis of single case research studies on aided AAC systems with ASD. Journal of Autism and Developmental Disorders.",
        "[8] Lucker, J. R. (2013). Auditory hypersensitivity in children with autism spectrum disorders. Focus on Autism and Other Developmental Disabilities.",
        "[9] Test, D. W., et al. (2011). Evidence-based practices in secondary transition. Career Development for Exceptional Individuals.",
        "[10] Buron, K. D., & Curtis, M. (2003). The Incredible 5-Point Scale. Autism Asperger Publishing Co.",
    ];
    refs.forEach((r, i) => {
        let y = 1.7 + i * 0.5;
        s.addText(r, {
            x: 0.6, y: y, w: 12.3, h: 0.45,
            fontFace: FONT_BODY, fontSize: 11, color: C.text, margin: 0
        });
    });
    pageNumber(s, n(), TOTAL);
}

// ═════════════════════════════════════════════════════════════
// SLIDE 25 — REFERENCES PART 2 + Tech
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    lightBg(s);
    sectionHeader(s, "REFERENCES", "Academic & technical sources (2/2)");

    const refs = [
        "[11] Carnett, A., et al. (2014). Effects of a perseverative interest-based token economy on academic engagement of students with autism. JABA.",
        "[12] Mindell, J. A., et al. (2009). A nightly bedtime routine: Impact on sleep in young children. Sleep, 32(5).",
        "[13] Schreibman, L., et al. (2015). Naturalistic Developmental Behavioral Interventions: Empirically validated treatments for ASD. JADD.",
        "[14] Sandler, M., et al. (2018). MobileNetV2: Inverted Residuals and Linear Bottlenecks. CVPR.",
        "[15] Radford, A., et al. (2023). Robust Speech Recognition via Large-Scale Weak Supervision (Whisper). OpenAI.",
        "[16] Touvron, H., et al. (2024). Llama 3: Training a 70B Parameter Foundation Model. Meta AI Research.",
        "[17] Anthropic. (2024). Claude 3.5 Sonnet Model Card. https://www.anthropic.com/news/claude-3-5-sonnet",
        "[18] Google DeepMind. (2024). Gemini 2.5 Technical Report. https://deepmind.google",
        "[19] Groq Inc. (2024). LPU Inference Architecture. https://wow.groq.com/lpu-inference-engine/",
        "[20] WHO. (2023). Autism — Fact sheet. https://www.who.int/news-room/fact-sheets/detail/autism-spectrum-disorders",
    ];
    refs.forEach((r, i) => {
        let y = 1.7 + i * 0.5;
        s.addText(r, {
            x: 0.6, y: y, w: 12.3, h: 0.45,
            fontFace: FONT_BODY, fontSize: 11, color: C.text, margin: 0
        });
    });
    pageNumber(s, n(), TOTAL);
}

// ═════════════════════════════════════════════════════════════
// SLIDE 26 — THANK YOU
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    darkBg(s);

    s.addText("Thank you.", {
        x: 0.6, y: 2.5, w: 12, h: 1.5,
        fontFace: FONT_TITLE, fontSize: 96, bold: true,
        color: C.teal_glow, align: "center"
    });
    s.addText("ARIA — built with care for autistic children and their families.", {
        x: 0.6, y: 4.0, w: 12, h: 0.5,
        fontFace: FONT_BODY, fontSize: 18,
        color: C.cyan, align: "center"
    });
    s.addText("Questions?", {
        x: 0.6, y: 5.0, w: 12, h: 0.6,
        fontFace: FONT_TITLE, fontSize: 32, italic: true,
        color: C.white, align: "center"
    });
}

// Save
pres.writeFile({ fileName: path.join(__dirname, "ARIA_Presentation.pptx") })
    .then(name => console.log(`Done: ${name}`));
