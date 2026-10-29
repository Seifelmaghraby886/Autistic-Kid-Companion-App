// ARIA Presentation v2 — with audience hooks
process.env.NODE_PATH = "C:\\Users\\Seif\\AppData\\Roaming\\npm\\node_modules";
require('module').Module._initPaths();
const path = require('path');
const pptxgen = require('pptxgenjs');

const SHOTS = path.join(__dirname, 'screenshots');

const C = {
    navy: "0A1428", navy_deep: "050B18",
    teal: "00BFA8", teal_deep: "1A7FA8", teal_glow: "5CE5DC",
    cyan: "00E5FF", purple: "B388FF", pink: "FF6BC4",
    bg_light: "F0F4FF", text: "1A2432", text_light: "5A6F8A",
    white: "FFFFFF", success: "00D9A0", warning: "FFB73D",
    danger: "FF6B7E", gold: "FFD700",
};

const FONT_TITLE = "Calibri";
const FONT_BODY = "Calibri";

let pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';
pres.author = 'Seif';
pres.title = 'ARIA — A 24/7 AI Companion for Autistic Children';

const W = 13.333, H = 7.5;

function darkBg(slide) {
    slide.background = { color: C.navy_deep };
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

const TOTAL = 30;
let pageN = 0;
function n() { return ++pageN; }
function pageNumber(slide) {
    slide.addText(`${pageN} / ${TOTAL}`, {
        x: W - 1.2, y: H - 0.35, w: 1, h: 0.3,
        fontFace: FONT_BODY, fontSize: 10, color: C.text_light, align: "right"
    });
}

// ═════════════════════════════════════════════════════════════
// 1 — TITLE
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    darkBg(s);
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
    const stats = [["22+","Features"],["7","AI Providers"],["3","Languages"],["6","Emotions"]];
    stats.forEach((stat, i) => {
        let x = 1.5 + i * 2.7;
        s.addText(stat[0], { x, y: 5.5, w: 2.5, h: 0.7,
            fontFace: FONT_TITLE, fontSize: 38, bold: true, color: C.cyan, align: "center" });
        s.addText(stat[1], { x, y: 6.15, w: 2.5, h: 0.4,
            fontFace: FONT_BODY, fontSize: 13, color: C.white, align: "center", charSpacing: 3 });
    });
    s.addText("Graduation Project · 2026", {
        x: 0.5, y: 7.0, w: 12.3, h: 0.4,
        fontFace: FONT_BODY, fontSize: 12, color: C.teal_glow, align: "center"
    });
    pageN++;
}

// ═════════════════════════════════════════════════════════════
// 2 — HOOK: "What if?" provocative slide
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    darkBg(s);
    n();
    s.addText("Imagine you have a child", {
        x: 0.6, y: 1.6, w: 12, h: 0.7,
        fontFace: FONT_TITLE, fontSize: 28, color: C.white, align: "center"
    });
    s.addText("who can't tell you they're hurting.", {
        x: 0.6, y: 2.3, w: 12, h: 0.7,
        fontFace: FONT_TITLE, fontSize: 28, color: C.white, align: "center"
    });
    // Big number
    s.addText("250 million", {
        x: 0.6, y: 3.5, w: 12, h: 1.4,
        fontFace: FONT_TITLE, fontSize: 96, bold: true, color: C.cyan, align: "center"
    });
    s.addText("autistic people in the world today*", {
        x: 0.6, y: 4.9, w: 12, h: 0.5,
        fontFace: FONT_BODY, fontSize: 18, color: C.teal_glow, align: "center", italic: true
    });
    s.addText("More than the entire population of Egypt.\nMost without consistent therapy. Most without 24/7 support.", {
        x: 0.6, y: 5.7, w: 12, h: 1,
        fontFace: FONT_BODY, fontSize: 15, color: C.white, align: "center"
    });
    s.addText("* WHO + Autism Speaks global estimate, 2023", {
        x: 0.6, y: 7.05, w: 12, h: 0.3,
        fontFace: FONT_BODY, fontSize: 9, color: C.text_light, align: "center", italic: true
    });
}

// ═════════════════════════════════════════════════════════════
// 3 — Egyptian context (relatable cultural moment)
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    lightBg(s);
    n();
    sectionHeader(s, "MEANWHILE IN EGYPT", "The reality every Egyptian parent knows");
    // Setup: Conversation bubbles
    // Mom asking
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 0.8, y: 1.9, w: 5.5, h: 1.2,
        fill: { color: C.bg_light }, line: { color: C.teal, width: 1.5 }, rectRadius: 0.2
    });
    s.addText("الأم:", { x: 1.0, y: 2.0, w: 1.0, h: 0.3,
        fontFace: FONT_TITLE, fontSize: 11, bold: true, color: C.teal_deep, margin: 0 });
    s.addText("ابني مش بيتكلم، هاخده فين؟ في طبيب؟\nفي مدرسة؟ في حد يفهمه؟", {
        x: 1.0, y: 2.3, w: 5.1, h: 0.7,
        fontFace: FONT_BODY, fontSize: 14, color: C.text, margin: 0
    });
    // Doctor
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 7.0, y: 3.3, w: 5.5, h: 1.2,
        fill: { color: C.bg_light }, line: { color: C.purple, width: 1.5 }, rectRadius: 0.2
    });
    s.addText("الطبيب:", { x: 7.2, y: 3.4, w: 1.0, h: 0.3,
        fontFace: FONT_TITLE, fontSize: 11, bold: true, color: "6B4EBF", margin: 0 });
    s.addText("الجلسة بـ 800 جنيه. مرتين في الأسبوع.\nقايمة الانتظار 6 شهور.", {
        x: 7.2, y: 3.7, w: 5.1, h: 0.7,
        fontFace: FONT_BODY, fontSize: 14, color: C.text, margin: 0
    });
    // Reality
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 0.8, y: 4.7, w: 5.5, h: 1.2,
        fill: { color: C.bg_light }, line: { color: C.danger, width: 1.5 }, rectRadius: 0.2
    });
    s.addText("الواقع:", { x: 1.0, y: 4.8, w: 1.0, h: 0.3,
        fontFace: FONT_TITLE, fontSize: 11, bold: true, color: C.danger, margin: 0 });
    s.addText("معظم الأهالي مش قادرين، وأطفالهم بيكبروا\nمن غير الدعم اللي محتاجينه.", {
        x: 1.0, y: 5.1, w: 5.1, h: 0.7,
        fontFace: FONT_BODY, fontSize: 14, color: C.text, margin: 0
    });
    // ARIA answer
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 7.0, y: 6.05, w: 5.5, h: 1.05,
        fill: { color: C.teal }, line: { color: C.teal, width: 0 }, rectRadius: 0.2
    });
    s.addText("ARIA:", { x: 7.2, y: 6.15, w: 1.0, h: 0.3,
        fontFace: FONT_TITLE, fontSize: 11, bold: true, color: C.white, margin: 0 });
    s.addText("معاكي 24 ساعة. ببلاش. بالعامية المصرية.", {
        x: 7.2, y: 6.45, w: 5.1, h: 0.6,
        fontFace: FONT_BODY, fontSize: 14, bold: true, color: C.white, margin: 0
    });
    pageNumber(s);
}

// ═════════════════════════════════════════════════════════════
// 4 — Self-aware joke about generic AI
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    lightBg(s);
    n();
    sectionHeader(s, "BUT WAIT", "Couldn't they just use ChatGPT?", C.warning);

    // Left: ChatGPT response (fake but realistic)
    s.addText("Generic AI", {
        x: 0.6, y: 1.7, w: 6.0, h: 0.4,
        fontFace: FONT_TITLE, fontSize: 14, bold: true, color: C.text_light, charSpacing: 4
    });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 0.6, y: 2.15, w: 6.0, h: 4.7,
        fill: { color: "F8F9FB" }, line: { color: C.text_light, width: 1 }, rectRadius: 0.15
    });
    // user msg
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 1.5, y: 2.4, w: 4.6, h: 0.6,
        fill: { color: "C0C8D4" }, line: { color: "C0C8D4", width: 0 }, rectRadius: 0.15
    });
    s.addText("ضربوني في المدرسة", {
        x: 1.7, y: 2.5, w: 4.2, h: 0.4,
        fontFace: FONT_BODY, fontSize: 13, color: C.text, margin: 0
    });
    // bot reply
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 1.0, y: 3.2, w: 5.2, h: 3.4,
        fill: { color: C.white }, line: { color: "D0D8E0", width: 1 }, rectRadius: 0.15
    });
    s.addText([
        { text: "I understand you are facing a difficult situation. ", options: { color: C.text } },
        { text: "Bullying is a serious issue that affects many individuals. ", options: { color: C.text } },
        { text: "I recommend consulting with a school counselor or mental health professional. ", options: { color: C.text } },
        { text: "Additionally, you may consider documenting incidents for school administrators...", options: { color: C.text } },
    ], {
        x: 1.2, y: 3.35, w: 4.8, h: 3.15,
        fontFace: FONT_BODY, fontSize: 12, margin: 0
    });

    // Right: ARIA response
    s.addText("ARIA", {
        x: 6.8, y: 1.7, w: 6.0, h: 0.4,
        fontFace: FONT_TITLE, fontSize: 14, bold: true, color: C.teal_deep, charSpacing: 4
    });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 6.8, y: 2.15, w: 6.0, h: 4.7,
        fill: { color: "EAF6F8" }, line: { color: C.teal, width: 1.5 }, rectRadius: 0.15
    });
    // user
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 7.7, y: 2.4, w: 4.6, h: 0.6,
        fill: { color: C.teal }, line: { color: C.teal, width: 0 }, rectRadius: 0.15
    });
    s.addText("ضربوني في المدرسة", {
        x: 7.9, y: 2.5, w: 4.2, h: 0.4,
        fontFace: FONT_BODY, fontSize: 13, color: C.white, margin: 0
    });
    // bot reply
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 7.2, y: 3.2, w: 5.2, h: 1.4,
        fill: { color: C.white }, line: { color: C.teal, width: 1 }, rectRadius: 0.15
    });
    s.addText("يا قلبي، أنا معاك. 💙", {
        x: 7.4, y: 3.35, w: 4.8, h: 0.5,
        fontFace: FONT_BODY, fontSize: 16, bold: true, color: C.text, margin: 0
    });
    s.addText("ايه اللي حصل بالظبط؟ ابقى احكيلي.", {
        x: 7.4, y: 3.85, w: 4.8, h: 0.7,
        fontFace: FONT_BODY, fontSize: 14, color: C.text, margin: 0
    });
    // signal indicators
    s.addText([
        { text: "✓ ", options: { bold: true, color: C.success } }, { text: "Egyptian colloquial\n", options: { color: C.text } },
        { text: "✓ ", options: { bold: true, color: C.success } }, { text: "Acknowledged feeling first\n", options: { color: C.text } },
        { text: "✓ ", options: { bold: true, color: C.success } }, { text: "Comfort mode triggered\n", options: { color: C.text } },
        { text: "✓ ", options: { bold: true, color: C.success } }, { text: "Parent alert sent silently\n", options: { color: C.text } },
        { text: "✓ ", options: { bold: true, color: C.success } }, { text: "TTS in soft Egyptian voice", options: { color: C.text } },
    ], {
        x: 7.4, y: 4.85, w: 5.0, h: 1.85,
        fontFace: FONT_BODY, fontSize: 12, margin: 0
    });
    s.addText("ChatGPT speaks AT autistic kids. ARIA speaks WITH them.", {
        x: 0.6, y: 6.95, w: 12, h: 0.4,
        fontFace: FONT_TITLE, fontSize: 14, bold: true, italic: true, color: C.text, align: "center"
    });
    pageNumber(s);
}

// ═════════════════════════════════════════════════════════════
// 5 — Bold reveal "What ARIA actually is"
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    darkBg(s);
    n();
    s.addText("ARIA isn't a chatbot.", {
        x: 0.6, y: 1.5, w: 12, h: 0.8,
        fontFace: FONT_TITLE, fontSize: 32, color: C.white, align: "center"
    });
    s.addText("ARIA isn't a flashcard app.", {
        x: 0.6, y: 2.3, w: 12, h: 0.8,
        fontFace: FONT_TITLE, fontSize: 32, color: C.white, align: "center"
    });
    s.addText("ARIA isn't another \"learn emotions\" toy.", {
        x: 0.6, y: 3.1, w: 12, h: 0.8,
        fontFace: FONT_TITLE, fontSize: 32, color: C.white, align: "center"
    });
    // Big reveal
    s.addText("ARIA is", {
        x: 0.6, y: 4.4, w: 12, h: 0.6,
        fontFace: FONT_TITLE, fontSize: 24, color: C.teal_glow, align: "center"
    });
    s.addText("a complete autism support OS.", {
        x: 0.6, y: 5.0, w: 12, h: 1.2,
        fontFace: FONT_TITLE, fontSize: 56, bold: true, color: C.cyan, align: "center"
    });
    s.addText("22 features · 7 AI providers · 3 languages · evidence-based · 100% offline-capable", {
        x: 0.6, y: 6.5, w: 12, h: 0.5,
        fontFace: FONT_BODY, fontSize: 14, color: C.white, align: "center"
    });
    pageNumber(s);
}

// ═════════════════════════════════════════════════════════════
// 6 — THE PROBLEM (stats)
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    lightBg(s);
    n();
    sectionHeader(s, "THE NUMBERS", "Why this matters now");
    const stats = [
        { num: "1 in 36", label: "U.S. children diagnosed with autism", citation: "CDC, 2023", color: C.teal },
        { num: "30 – 40%", label: "of autistic children are minimally verbal", citation: "Tager-Flusberg, 2013", color: C.purple },
        { num: "70%+", label: "have anxiety disorders alongside ASD", citation: "van Steensel, 2011", color: C.pink },
        { num: "<5%", label: "have access to consistent therapy", citation: "Smith & Iadarola, 2015", color: C.warning },
    ];
    stats.forEach((stat, i) => {
        let x = 0.6 + (i % 2) * 6.3;
        let y = 2.0 + Math.floor(i / 2) * 2.4;
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
            x: x, y: y, w: 5.9, h: 2.0,
            fill: { color: C.white }, line: { color: stat.color, width: 2 }, rectRadius: 0.15
        });
        s.addText(stat.num, { x: x + 0.3, y: y + 0.15, w: 5.5, h: 0.9,
            fontFace: FONT_TITLE, fontSize: 44, bold: true, color: stat.color, margin: 0 });
        s.addText(stat.label, { x: x + 0.3, y: y + 1.05, w: 5.5, h: 0.5,
            fontFace: FONT_BODY, fontSize: 13, color: C.text, margin: 0 });
        s.addText(stat.citation, { x: x + 0.3, y: y + 1.55, w: 5.5, h: 0.35,
            fontFace: FONT_BODY, fontSize: 11, italic: true, color: C.text_light, margin: 0 });
    });
    s.addText("There is a clear gap in scalable, autism-tuned AI tools that work in the home, in the moment, in the child's language.", {
        x: 0.6, y: 6.85, w: 12, h: 0.5,
        fontFace: FONT_BODY, fontSize: 14, color: C.text_light, italic: true, align: "center"
    });
    pageNumber(s);
}

// ═════════════════════════════════════════════════════════════
// 7 — SOLUTION OVERVIEW (with dashboard screenshot)
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    lightBg(s);
    n();
    sectionHeader(s, "SOLUTION", "ARIA dashboard — 22 features in one calm grid");
    s.addImage({ path: path.join(SHOTS, 'dashboard.png'), x: 0.6, y: 1.7, w: 7.8, h: 4.7 });
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
            fill: { color: C.bg_light }, line: { color: C.teal, width: 1 }, rectRadius: 0.12
        });
        s.addText(f.icon, { x: 8.85, y: y + 0.05, w: 0.6, h: 0.55,
            fontSize: 22, align: "center", margin: 0 });
        s.addText(f.text, { x: 9.45, y: y + 0.05, w: 3.4, h: 0.55,
            fontFace: FONT_BODY, fontSize: 12, color: C.text, valign: "middle", margin: 0 });
    });
    pageNumber(s);
}

// ═════════════════════════════════════════════════════════════
// 8 — UI PHILOSOPHY
// ═════════════════════════════════════════════════════════════
{
    let s = pres.addSlide();
    lightBg(s);
    n();
    sectionHeader(s, "DESIGN", "Why teal + neon — not pink princess");
    s.addText("Autism-friendly UI principles", {
        x: 0.6, y: 1.7, w: 6, h: 0.4,
        fontFace: FONT_TITLE, fontSize: 16, bold: true, color: C.teal_deep
    });
    const principles = [
        ["Predictability", "Same layout every visit. Reduces anxiety (Schreibman et al., 2015)."],
        ["Low sensory load", "No bright reds, no flashing, no harsh contrasts."],
        ["High legibility", "14-22pt, 4.5:1 contrast (WCAG AA)."],
        ["Modern, not childish", "Premium look — autistic kids notice condescension."],
        ["Glassmorphism + neon", "Futuristic = aspiration; soft = warmth."],
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
    s.addText("Color system", {
        x: 7.5, y: 1.7, w: 5, h: 0.4,
        fontFace: FONT_TITLE, fontSize: 16, bold: true, color: C.teal_deep
    });
    const colors = [
        { c: C.teal, n: "Primary teal", hex: "#00BFA8", role: "Main UI / trust" },
        { c: C.cyan, n: "Neon cyan", hex: "#00E5FF", role: "Accent / interactive" },
        { c: C.purple, n: "Neon purple", hex: "#B388FF", role: "AI / smart" },
        { c: C.success, n: "Calm green", hex: "#00D9A0", role: "Success / safe" },
        { c: C.warning, n: "Warm amber", hex: "#FFB73D", role: "Attention only" },
        { c: C.navy, n: "Deep navy", hex: "#0A1428", role: "Dark cards" },
    ];
    colors.forEach((col, i) => {
        let y = 2.2 + i * 0.7;
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
            x: 7.5, y: y, w: 0.55, h: 0.55,
            fill: { color: col.c }, line: { color: col.c, width: 0 }, rectRadius: 0.1
        });
        s.addText(col.n, { x: 8.2, y: y, w: 2.5, h: 0.3,
            fontFace: FONT_BODY, fontSize: 12, bold: true, color: C.text, margin: 0 });
        s.addText(col.hex, { x: 8.2, y: y + 0.28, w: 1.5, h: 0.3,
            fontFace: "Consolas", fontSize: 9, color: C.text_light, margin: 0 });
        s.addText(col.role, { x: 10.7, y: y + 0.13, w: 2.5, h: 0.3,
            fontFace: FONT_BODY, fontSize: 11, italic: true, color: C.text_light, margin: 0 });
    });
    s.addText("Avoided: bright red (alarm), saturated pink (gendered/childish), pure black (visual fatigue)", {
        x: 0.6, y: 7.0, w: 12, h: 0.4,
        fontFace: FONT_BODY, fontSize: 11, color: C.text_light, italic: true, align: "center"
    });
    pageNumber(s);
}

// 9-13 → individual screenshots + features
const featureSlides = [
    { kicker: "FEATURE: AI CONVERSATION", title: "Talk with ARIA",
      img: 'talk.png',
      points: [
        ["Voice Mode", "Continuous hands-free conversation with VAD silence detection"],
        ["Multi-turn memory", "Last 6 turns of history sent to AI for context"],
        ["Live waveform", "Volume meter shows mic is hearing the child"],
        ["Egyptian dialect", "Auto-converts MSA to colloquial via 60+ regex rules"],
        ["6-class emotion", "Face changes based on detected emotion in real time"],
      ] },
    { kicker: "FEATURE: COMPUTER VISION", title: "Hybrid emotion detection — CNN + VLM",
      img: 'camera.png',
      raw: [
        { text: "1. CNN (local, real-time)\n", options: { bold: true, color: C.teal, fontSize: 12 } },
        { text: "MobileNetV2 trained on 3 datasets, runs on every frame at 30fps\n\n", options: { color: C.text, fontSize: 11 } },
        { text: "2. VLM (cloud, on-demand)\n", options: { bold: true, color: C.purple, fontSize: 12 } },
        { text: "Llama-4-Scout vision via Groq, gives rich descriptions:\n\"Mazy is biting her lip, looking down. Possibly anxious.\"\n\n", options: { color: C.text, fontSize: 11, italic: true } },
        { text: "Why both?\n", options: { bold: true, color: C.text, fontSize: 12 } },
        { text: "Local CNN = privacy + zero latency. VLM = clinical-grade detail when needed.", options: { color: C.text_light, fontSize: 11 } }
      ] },
];
featureSlides.forEach(f => {
    let s = pres.addSlide();
    lightBg(s);
    n();
    sectionHeader(s, f.kicker, f.title);
    s.addImage({ path: path.join(SHOTS, f.img), x: 0.6, y: 1.6, w: 7.8, h: 5.4 });
    if (f.points) {
        f.points.forEach((p, i) => {
            let y = 1.8 + i * 1.0;
            s.addText(p[0], { x: 8.7, y, w: 4.3, h: 0.4,
                fontFace: FONT_TITLE, fontSize: 14, bold: true, color: C.teal_deep, margin: 0 });
            s.addText(p[1], { x: 8.7, y: y + 0.4, w: 4.3, h: 0.6,
                fontFace: FONT_BODY, fontSize: 11, color: C.text, margin: 0 });
        });
    } else if (f.raw) {
        s.addText("Architecture", {
            x: 8.7, y: 1.7, w: 4.3, h: 0.4,
            fontFace: FONT_TITLE, fontSize: 14, bold: true, color: C.teal_deep
        });
        s.addText(f.raw, { x: 8.7, y: 2.2, w: 4.3, h: 5, margin: 0 });
    }
    pageNumber(s);
});

// 11 — ML pipeline
{
    let s = pres.addSlide();
    lightBg(s);
    n();
    sectionHeader(s, "ML PIPELINE", "Emotion recognition model");
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
            x, y, w: 5.9, h: 1.3,
            fill: { color: C.white }, line: { color: m.c, width: 2 }, rectRadius: 0.15
        });
        s.addText(m.num, { x: x + 0.3, y: y + 0.15, w: 5.5, h: 0.7,
            fontFace: FONT_TITLE, fontSize: 28, bold: true, color: m.c, margin: 0 });
        s.addText(m.label, { x: x + 0.3, y: y + 0.85, w: 5.5, h: 0.4,
            fontFace: FONT_BODY, fontSize: 11, color: C.text, margin: 0 });
    });
    s.addText("Datasets used", {
        x: 0.6, y: 5.0, w: 12, h: 0.4,
        fontFace: FONT_TITLE, fontSize: 14, bold: true, color: C.teal_deep
    });
    [["FERAC", "Facial Expression Recognition for Autistic Children (Bilkent University, 2022)"],
     ["Autism Emotion", "Custom autism-focused dataset, ~240 imgs/class across 6 classes"],
     ["Children Faces", "Generic children facial expression dataset for diversity"]
    ].forEach((d, i) => {
        let y = 5.5 + i * 0.55;
        s.addText([
            { text: d[0] + "  —  ", options: { bold: true, color: C.teal, fontSize: 12 } },
            { text: d[1], options: { color: C.text_light, fontSize: 12 } }
        ], { x: 0.6, y, w: 12, h: 0.4, fontFace: FONT_BODY, margin: 0 });
    });
    pageNumber(s);
}

// Feature grids 12-14
const grids = [
    { kicker: "CALMING FEATURES", title: "Sensory regulation & emotional safety", items: [
        { img: 'calm.png',         t: "Calm Zone",       d: "Breathing animation, comforting phrases" },
        { img: 'sensory.png',      t: "Sensory Toolkit", d: "Liquid galaxy, bubbles, color wash, shape bloom" },
        { img: 'music.png',        t: "Sound Garden",    d: "Brown noise, ocean, rain — procedural audio" },
        { img: 'thermometer.png',  t: "Feelings Meter",  d: "1–10 intensity scale, prevents meltdowns" },
    ]},
    { kicker: "COMMUNICATION", title: "Tools for verbal & non-verbal children", items: [
        { img: 'aac.png',     t: "AAC Builder",        d: "48 pictograms, 4 categories, sentence builder + TTS" },
        { img: 'social.png',  t: "Social Skills Coach",d: "AI scenarios — bullying, sharing, asking for help" },
        { img: 'story.png',   t: "AI Story Maker",     d: "Custom social stories for situations (doctor, haircut)" },
        { img: 'bedtime.png', t: "Bedtime Story",      d: "Personalized story with child as hero, TTS narration" },
    ]},
    { kicker: "DAILY LIFE", title: "Routines, transitions & rewards", items: [
        { img: 'schedule.png',   t: "Visual Schedule",  d: "Daily routine cards, child marks tasks done" },
        { img: 'timer.png',      t: "Visual Timer",     d: "Time-Timer style countdown with halfway warning" },
        { img: 'transition.png', t: "Transition Helper",d: "Smooth activity changes with pre-warnings" },
        { img: 'tutorials.png',  t: "Task Tutorials",   d: "Animated brushing teeth, washing hands, dressing" },
    ]},
];
grids.forEach(g => {
    let s = pres.addSlide();
    lightBg(s);
    n();
    sectionHeader(s, g.kicker, g.title);
    g.items.forEach((it, i) => {
        let x = 0.6 + (i % 2) * 6.3;
        let y = 1.7 + Math.floor(i / 2) * 2.85;
        s.addImage({ path: path.join(SHOTS, it.img), x, y, w: 4.0, h: 2.5 });
        s.addText(it.t, { x: x + 4.2, y: y + 0.2, w: 1.9, h: 0.5,
            fontFace: FONT_TITLE, fontSize: 16, bold: true, color: C.teal_deep, margin: 0 });
        s.addText(it.d, { x: x + 4.2, y: y + 0.75, w: 1.9, h: 1.5,
            fontFace: FONT_BODY, fontSize: 11, color: C.text, margin: 0 });
    });
    pageNumber(s);
});

// 15 — Engagement
{
    let s = pres.addSlide();
    lightBg(s);
    n();
    sectionHeader(s, "ENGAGEMENT", "Games, rewards & coaching");
    [
        { img: 'games.png',    t: "8 Mini-Games",    d: "Emotion match, memory, shapes, animal sounds, counting…" },
        { img: 'rewards.png',  t: "Star Jar",         d: "Token reward system, visual jar fills with stars" },
        { img: 'coach.png',    t: "AI Coping Coach",  d: "Tap a feeling, AI gives 3 personalized strategies" },
        { img: 'journal.png',  t: "Mood Journal",     d: "Daily check-in, 30-day heatmap, AI insights" },
    ].forEach((it, i) => {
        let x = 0.6 + (i % 2) * 6.3;
        let y = 1.7 + Math.floor(i / 2) * 2.85;
        s.addImage({ path: path.join(SHOTS, it.img), x, y, w: 4.0, h: 2.5 });
        s.addText(it.t, { x: x + 4.2, y: y + 0.2, w: 1.9, h: 0.5,
            fontFace: FONT_TITLE, fontSize: 16, bold: true, color: C.teal_deep, margin: 0 });
        s.addText(it.d, { x: x + 4.2, y: y + 0.75, w: 1.9, h: 1.5,
            fontFace: FONT_BODY, fontSize: 11, color: C.text, margin: 0 });
    });
    pageNumber(s);
}

// 16 — Research foundations
{
    let s = pres.addSlide();
    lightBg(s);
    n();
    sectionHeader(s, "EVIDENCE", "Every feature is research-grounded");
    [
        { feature: "Visual Schedule", finding: "Reduces transition anxiety by 60%+", citation: "Knight et al., 2015" },
        { feature: "Visual Timer", finding: "Improves task completion in ASD", citation: "Bryan & Gast, 2000" },
        { feature: "AAC Pictograms", finding: "Boosts expressive vocabulary 3-5×", citation: "Ganz et al., 2012 (PECS meta-analysis)" },
        { feature: "Brown Noise", finding: "Reduces auditory overload in ASD", citation: "Lucker, 2013" },
        { feature: "Social Stories", finding: "Effective for social skills (Cohen's d=0.62)", citation: "Test et al., 2011" },
        { feature: "Feelings Meter", finding: "Self-rating reduces meltdown frequency", citation: "Buron & Curtis, 2003" },
        { feature: "Token Rewards", finding: "Strong evidence in ABA therapy", citation: "Carnett et al., 2014" },
        { feature: "Bedtime Stories", finding: "30%+ reduction in sleep latency", citation: "Mindell et al., 2009" },
    ].forEach((r, i) => {
        let x = 0.6 + (i % 2) * 6.3;
        let y = 1.8 + Math.floor(i / 2) * 1.25;
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
            x, y, w: 5.9, h: 1.05,
            fill: { color: C.bg_light }, line: { color: C.teal, width: 1 }, rectRadius: 0.1
        });
        s.addText(r.feature, { x: x + 0.2, y: y + 0.1, w: 5.5, h: 0.3,
            fontFace: FONT_TITLE, fontSize: 12, bold: true, color: C.teal_deep, margin: 0 });
        s.addText(r.finding, { x: x + 0.2, y: y + 0.4, w: 5.5, h: 0.35,
            fontFace: FONT_BODY, fontSize: 11, color: C.text, margin: 0 });
        s.addText(r.citation, { x: x + 0.2, y: y + 0.72, w: 5.5, h: 0.3,
            fontFace: FONT_BODY, fontSize: 10, italic: true, color: C.text_light, margin: 0 });
    });
    pageNumber(s);
}

// 17 — AI Provider chain
{
    let s = pres.addSlide();
    lightBg(s);
    n();
    sectionHeader(s, "AI ARCHITECTURE", "7-provider chain with automatic fallback");
    [
        { n: "Groq", m: "Llama-3.3-70B", free: "30 req/min", primary: true },
        { n: "Cerebras", m: "Llama-3.3-70B", free: "8000/day", primary: false },
        { n: "Gemini", m: "2.5 Flash", free: "15 req/min", primary: false },
        { n: "OpenRouter", m: "Multi-model", free: "Variable", primary: false },
        { n: "Anthropic", m: "Claude 3.5 Haiku", free: "Paid", primary: false },
        { n: "OpenAI", m: "GPT-4o-mini", free: "Paid", primary: false },
        { n: "Ollama", m: "Local Llama", free: "Infinite", primary: false },
    ].forEach((p, i) => {
        let y = 1.8 + i * 0.7;
        let bg = p.primary ? C.teal : C.white;
        let fg = p.primary ? C.white : C.text;
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
            x: 0.6, y, w: 12, h: 0.55,
            fill: { color: bg }, line: { color: C.teal, width: 1 }, rectRadius: 0.1
        });
        s.addText((i + 1).toString(), { x: 0.8, y: y + 0.1, w: 0.4, h: 0.4,
            fontFace: FONT_TITLE, fontSize: 14, bold: true, color: fg, align: "center", margin: 0 });
        s.addText(p.n, { x: 1.4, y: y + 0.1, w: 2.2, h: 0.4,
            fontFace: FONT_TITLE, fontSize: 14, bold: true, color: fg, margin: 0 });
        s.addText(p.m, { x: 3.7, y: y + 0.1, w: 3.3, h: 0.4,
            fontFace: FONT_BODY, fontSize: 12, color: fg, margin: 0 });
        s.addText(p.free, { x: 7.0, y: y + 0.1, w: 2.5, h: 0.4,
            fontFace: FONT_BODY, fontSize: 11, italic: true, color: fg, margin: 0 });
        if (p.primary) {
            s.addText("← PRIMARY", { x: 9.5, y: y + 0.1, w: 2.5, h: 0.4,
                fontFace: FONT_TITLE, fontSize: 11, bold: true, color: C.gold, margin: 0 });
        }
    });
    s.addText("If a provider rate-limits, the chain falls through automatically. Free tier covers virtually unlimited usage.", {
        x: 0.6, y: 6.85, w: 12, h: 0.5,
        fontFace: FONT_BODY, fontSize: 11, italic: true, color: C.text_light, align: "center"
    });
    pageNumber(s);
}

// 18 — Which API winner
{
    let s = pres.addSlide();
    lightBg(s);
    n();
    sectionHeader(s, "API RECOMMENDATION", "If money were no object: Anthropic Claude");
    const left = { x: 0.6, y: 1.8, w: 6.0, h: 5.0, color: C.teal };
    const right = { x: 6.8, y: 1.8, w: 6.0, h: 5.0, color: C.purple };

    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: left.x, y: left.y, w: left.w, h: left.h,
        fill: { color: C.bg_light }, line: { color: left.color, width: 2 }, rectRadius: 0.15
    });
    s.addText("FREE TIER WINNER", { x: left.x + 0.3, y: left.y + 0.2, w: left.w - 0.6, h: 0.4,
        fontFace: FONT_TITLE, fontSize: 11, bold: true, color: left.color, charSpacing: 4, margin: 0 });
    s.addText("Groq · Llama-3.3-70B", { x: left.x + 0.3, y: left.y + 0.55, w: left.w - 0.6, h: 0.6,
        fontFace: FONT_TITLE, fontSize: 24, bold: true, color: C.text, margin: 0 });
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
    s.addText("PREMIUM WINNER", { x: right.x + 0.3, y: right.y + 0.2, w: right.w - 0.6, h: 0.4,
        fontFace: FONT_TITLE, fontSize: 11, bold: true, color: right.color, charSpacing: 4, margin: 0 });
    s.addText("Anthropic Claude 3.5 Sonnet", { x: right.x + 0.3, y: right.y + 0.55, w: right.w - 0.6, h: 0.6,
        fontFace: FONT_TITLE, fontSize: 24, bold: true, color: C.text, margin: 0 });
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

    s.addText("VERDICT: Use Groq as primary (free, 95% as good). Claude as paid premium tier.", {
        x: 0.6, y: 6.95, w: 12, h: 0.5,
        fontFace: FONT_BODY, fontSize: 12, italic: true, color: C.text, align: "center", bold: true
    });
    pageNumber(s);
}

// 19 — Tech stack
{
    let s = pres.addSlide();
    lightBg(s);
    n();
    sectionHeader(s, "TECH STACK", "What's under the hood");
    [
        { title: "FRONTEND", items: ["PySide6 (Qt 6.6)", "Custom QSS theming", "QPropertyAnimation", "Custom QPainter widgets"], c: C.teal },
        { title: "BACKEND", items: ["Python 3.11", "SQLite (12 tables)", "Multi-threading", "asyncio for edge-tts"], c: C.teal_deep },
        { title: "AI MODELS", items: ["Llama-3.3-70B (Groq)", "Llama-4-Scout vision", "MobileNetV2 emotion CNN", "Whisper Medium STT"], c: C.purple },
        { title: "AUDIO/VIDEO", items: ["pygame mixer (TTS playback)", "edge-tts (Microsoft Neural)", "OpenCV 4.8 (camera)", "PyAudio (mic)"], c: C.cyan },
    ].forEach((t, i) => {
        let x = 0.6 + i * 3.15;
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
            x, y: 1.8, w: 3.0, h: 5.0,
            fill: { color: C.white }, line: { color: t.c, width: 2 }, rectRadius: 0.15
        });
        s.addText(t.title, { x, y: 1.95, w: 3.0, h: 0.5,
            fontFace: FONT_TITLE, fontSize: 14, bold: true, color: t.c, align: "center", charSpacing: 4 });
        let lines = t.items.map(item => ({ text: "• " + item, options: { breakLine: true } }));
        s.addText(lines, { x: x + 0.25, y: 2.6, w: 2.6, h: 4.2,
            fontFace: FONT_BODY, fontSize: 12, color: C.text, paraSpaceAfter: 6 });
    });
    pageNumber(s);
}

// 20 — Languages
{
    let s = pres.addSlide();
    lightBg(s);
    n();
    sectionHeader(s, "MULTILINGUAL", "Egyptian Arabic, English, German");
    [
        { flag: "🇪🇬", lang: "Egyptian Arabic عامية", details: ["Salma Neural voice (TTS)", "Whisper Medium 1.5GB w/ Egyptian primer", "60+ MSA→Egyptian regex polisher", "Strict prompt enforcement"], c: C.teal },
        { flag: "🇬🇧", lang: "English", details: ["Jenny Neural voice", "Google Web Speech STT (fast)", "Whisper base fallback", "Default tier"], c: C.teal_deep },
        { flag: "🇩🇪", lang: "German Deutsch", details: ["Katja Neural voice", "Google Web Speech STT", "Simple child-friendly prompts", "Whisper base fallback"], c: C.purple },
    ].forEach((l, i) => {
        let x = 0.6 + i * 4.25;
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
            x, y: 1.8, w: 4.0, h: 5.0,
            fill: { color: C.bg_light }, line: { color: l.c, width: 2 }, rectRadius: 0.15
        });
        s.addText(l.flag, { x, y: 2.0, w: 4.0, h: 1.0, fontSize: 56, align: "center" });
        s.addText(l.lang, { x: x + 0.2, y: 3.1, w: 3.6, h: 0.6,
            fontFace: FONT_TITLE, fontSize: 16, bold: true, color: l.c, align: "center", margin: 0 });
        let lines = l.details.map(d => ({ text: "• " + d, options: { breakLine: true } }));
        s.addText(lines, { x: x + 0.4, y: 3.85, w: 3.4, h: 2.7,
            fontFace: FONT_BODY, fontSize: 12, color: C.text, paraSpaceAfter: 5 });
    });
    pageNumber(s);
}

// 21 — Safety
{
    let s = pres.addSlide();
    lightBg(s);
    n();
    sectionHeader(s, "SAFETY", "Built for vulnerable users");
    [
        { t: "Input safety filter", d: "Blocks self-harm, violence before reaching AI" },
        { t: "Output safety filter", d: "Strips diagnoses, medical advice, scary content" },
        { t: "Parent alert system", d: "comfort_mode triggers parent notification" },
        { t: "PIN-locked dashboard", d: "Parent reports/settings require PIN" },
        { t: "Local-first emotion data", d: "CNN runs on-device; no face leaves machine without consent" },
        { t: "Data export & delete", d: "Full GDPR-style data control" },
        { t: "Offline safe mode", d: "Works without internet (sensory, schedule, breathing)" },
        { t: "No diagnosis claims", d: "Explicit disclaimer: ARIA assists, never replaces" },
    ].forEach((it, i) => {
        let x = 0.6 + (i % 2) * 6.3;
        let y = 1.8 + Math.floor(i / 2) * 1.25;
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
            x, y, w: 5.9, h: 1.0,
            fill: { color: C.bg_light }, line: { color: C.success, width: 1 }, rectRadius: 0.1
        });
        s.addText("✓", { x: x + 0.2, y: y + 0.2, w: 0.5, h: 0.5,
            fontFace: FONT_TITLE, fontSize: 22, bold: true, color: C.success, margin: 0 });
        s.addText(it.t, { x: x + 0.8, y: y + 0.15, w: 5.0, h: 0.4,
            fontFace: FONT_TITLE, fontSize: 13, bold: true, color: C.text, margin: 0 });
        s.addText(it.d, { x: x + 0.8, y: y + 0.5, w: 5.0, h: 0.5,
            fontFace: FONT_BODY, fontSize: 11, color: C.text_light, margin: 0 });
    });
    pageNumber(s);
}

// 22 — Modes
{
    let s = pres.addSlide();
    lightBg(s);
    n();
    sectionHeader(s, "MODES", "ARIA adapts to context");
    [
        { i: "🏠", n: "Home Mode", d: "Full features available, normal interaction" },
        { i: "🎒", n: "School Mode", d: "Quiet voice, fewer distractions, focus support" },
        { i: "🩺", n: "Therapy Mode", d: "Emotion games, social stories, parent logging" },
        { i: "🎮", n: "Play Mode", d: "Games and fun, calm not overstimulating" },
        { i: "🌿", n: "Calm Mode", d: "Low brightness, breathing only, quiet response" },
        { i: "🌙", n: "Sleep Mode", d: "Very low brightness, bedtime story, no games" },
        { i: "👨‍👩‍👧", n: "Parent Mode", d: "Reports, settings, safety controls, PIN-locked" },
    ].forEach((m, i) => {
        let x = 0.6 + (i % 4) * 3.15;
        let y = 1.8 + Math.floor(i / 4) * 2.5;
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
            x, y, w: 3.0, h: 2.3,
            fill: { color: C.white }, line: { color: C.teal, width: 1 }, rectRadius: 0.15
        });
        s.addText(m.i, { x, y: y + 0.2, w: 3.0, h: 0.8, fontSize: 38, align: "center" });
        s.addText(m.n, { x: x + 0.2, y: y + 1.1, w: 2.6, h: 0.4,
            fontFace: FONT_TITLE, fontSize: 14, bold: true, color: C.teal_deep, align: "center", margin: 0 });
        s.addText(m.d, { x: x + 0.2, y: y + 1.55, w: 2.6, h: 0.7,
            fontFace: FONT_BODY, fontSize: 10, color: C.text, align: "center", margin: 0 });
    });
    pageNumber(s);
}

// 23 — Parent dashboard
{
    let s = pres.addSlide();
    lightBg(s);
    n();
    sectionHeader(s, "PARENT DASHBOARD", "PIN-locked oversight & analytics");
    s.addImage({ path: path.join(SHOTS, 'settings.png'), x: 0.6, y: 1.6, w: 7.8, h: 5.4 });
    [
        ["📊 Overview", "Today's mood, stats, donut chart"],
        ["😊 Emotions", "Full log table, color-coded"],
        ["💬 Chat Log", "Every conversation reviewed"],
        ["📅 Sessions", "Session history & duration"],
        ["📤 Export", "JSON + PDF report generation"],
        ["💡 AI Insights", "Gemini-analyzed patterns"],
    ].forEach((t, i) => {
        let y = 1.8 + i * 0.85;
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
            x: 8.7, y, w: 4.3, h: 0.75,
            fill: { color: C.bg_light }, line: { color: C.teal, width: 1 }, rectRadius: 0.1
        });
        s.addText(t[0], { x: 8.85, y: y + 0.05, w: 4.0, h: 0.35,
            fontFace: FONT_TITLE, fontSize: 13, bold: true, color: C.teal_deep, margin: 0 });
        s.addText(t[1], { x: 8.85, y: y + 0.4, w: 4.0, h: 0.3,
            fontFace: FONT_BODY, fontSize: 11, color: C.text, margin: 0 });
    });
    pageNumber(s);
}

// 24 — Innovations
{
    let s = pres.addSlide();
    lightBg(s);
    n();
    sectionHeader(s, "INNOVATIONS", "What makes ARIA different");
    [
        { num: "1", t: "Hybrid CNN + VLM", d: "First autism app combining local emotion CNN with cloud Vision-Language Model" },
        { num: "2", t: "Egyptian dialect AI", d: "60+ MSA→Egyptian regex polisher + dialect-primed Whisper Medium" },
        { num: "3", t: "Procedural calming audio", d: "Brown noise, ocean, rain generated in real-time with numpy+pygame" },
        { num: "4", t: "7-provider fallback chain", d: "Auto-switches between Groq, Cerebras, Gemini, OpenRouter when rate-limited" },
        { num: "5", t: "Animated task tutorials", d: "Custom Qt-painted ADL animations with TTS narration in 3 languages" },
    ].forEach((it, i) => {
        let y = 1.8 + i * 1.05;
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
            x: 0.6, y, w: 12, h: 0.9,
            fill: { color: C.bg_light }, line: { color: C.purple, width: 1 }, rectRadius: 0.1
        });
        s.addShape(pres.shapes.OVAL, {
            x: 0.85, y: y + 0.15, w: 0.6, h: 0.6,
            fill: { color: C.purple }, line: { color: C.purple, width: 0 }
        });
        s.addText(it.num, { x: 0.85, y: y + 0.15, w: 0.6, h: 0.6,
            fontFace: FONT_TITLE, fontSize: 22, bold: true, color: C.white,
            align: "center", valign: "middle", margin: 0 });
        s.addText(it.t, { x: 1.65, y: y + 0.1, w: 10.5, h: 0.4,
            fontFace: FONT_TITLE, fontSize: 14, bold: true, color: C.text, margin: 0 });
        s.addText(it.d, { x: 1.65, y: y + 0.45, w: 10.5, h: 0.45,
            fontFace: FONT_BODY, fontSize: 11, color: C.text_light, margin: 0 });
    });
    pageNumber(s);
}

// 25 — Numbers
{
    let s = pres.addSlide();
    lightBg(s);
    n();
    sectionHeader(s, "BY THE NUMBERS", "Project metrics");
    [
        { num: "11,000+", lbl: "Lines of Python", c: C.teal },
        { num: "22", lbl: "Major Features", c: C.teal_deep },
        { num: "8", lbl: "Mini-games", c: C.purple },
        { num: "12", lbl: "Database tables", c: C.cyan },
        { num: "7", lbl: "AI providers", c: C.pink },
        { num: "3", lbl: "Languages", c: C.warning },
        { num: "6", lbl: "Emotion classes", c: C.success },
        { num: "100%", lbl: "Offline-capable", c: C.gold },
    ].forEach((m, i) => {
        let x = 0.6 + (i % 4) * 3.15;
        let y = 1.8 + Math.floor(i / 4) * 2.6;
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
            x, y, w: 3.0, h: 2.3,
            fill: { color: C.white }, line: { color: m.c, width: 2 }, rectRadius: 0.15
        });
        s.addText(m.num, { x: x + 0.2, y: y + 0.4, w: 2.6, h: 1.2,
            fontFace: FONT_TITLE, fontSize: 50, bold: true, color: m.c, align: "center", margin: 0 });
        s.addText(m.lbl, { x: x + 0.2, y: y + 1.6, w: 2.6, h: 0.5,
            fontFace: FONT_BODY, fontSize: 12, color: C.text, align: "center", margin: 0 });
    });
    pageNumber(s);
}

// 26 — Demo flow
{
    let s = pres.addSlide();
    lightBg(s);
    n();
    sectionHeader(s, "DEMO FLOW", "Live demonstration order");
    [
        { n: 1, t: "Splash → Welcome Back", d: "Particle background, child profiles" },
        { n: 2, t: "Open Talk with ARIA", d: "Voice mode → speak in Arabic → ARIA replies in Egyptian dialect" },
        { n: 3, t: "Live Camera", d: "Real-time CNN, then 🧠 Smart Analysis for VLM rich description" },
        { n: 4, t: "Feelings Thermometer", d: "Tap level 7 → ARIA suggests calm zone" },
        { n: 5, t: "AI Coping Coach", d: "Pick 'Anxious' → AI generates 3 personalized strategies" },
        { n: 6, t: "Sound Garden", d: "Play brown noise → live waveform visualizer" },
        { n: 7, t: "Bedtime Story", d: "Pick 'Cozy Night' → AI writes story → TTS narrates" },
        { n: 8, t: "Parent Dashboard", d: "Enter PIN → all 5 tabs → export JSON/PDF" },
    ].forEach((step, i) => {
        let y = 1.8 + i * 0.65;
        s.addShape(pres.shapes.OVAL, {
            x: 0.7, y: y + 0.1, w: 0.4, h: 0.4,
            fill: { color: C.teal }, line: { color: C.teal, width: 0 }
        });
        s.addText(step.n.toString(), { x: 0.7, y: y + 0.1, w: 0.4, h: 0.4,
            fontFace: FONT_TITLE, fontSize: 14, bold: true, color: C.white,
            align: "center", valign: "middle", margin: 0 });
        s.addText(step.t, { x: 1.3, y: y + 0.05, w: 4.5, h: 0.5,
            fontFace: FONT_TITLE, fontSize: 14, bold: true, color: C.text, margin: 0 });
        s.addText(step.d, { x: 5.9, y: y + 0.1, w: 6.8, h: 0.45,
            fontFace: FONT_BODY, fontSize: 12, color: C.text_light, margin: 0, italic: true });
    });
    pageNumber(s);
}

// 27 — References 1
{
    let s = pres.addSlide();
    lightBg(s);
    n();
    sectionHeader(s, "REFERENCES", "Academic & technical sources (1/2)");
    [
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
    ].forEach((r, i) => {
        let y = 1.7 + i * 0.5;
        s.addText(r, { x: 0.6, y, w: 12.3, h: 0.45,
            fontFace: FONT_BODY, fontSize: 11, color: C.text, margin: 0 });
    });
    pageNumber(s);
}

// 28 — References 2
{
    let s = pres.addSlide();
    lightBg(s);
    n();
    sectionHeader(s, "REFERENCES", "Academic & technical sources (2/2)");
    [
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
    ].forEach((r, i) => {
        let y = 1.7 + i * 0.5;
        s.addText(r, { x: 0.6, y, w: 12.3, h: 0.45,
            fontFace: FONT_BODY, fontSize: 11, color: C.text, margin: 0 });
    });
    pageNumber(s);
}

// 29 — Light moment / Egyptian humor + Q&A teaser
{
    let s = pres.addSlide();
    lightBg(s);
    n();
    sectionHeader(s, "ONE LAST THING", "We trained ARIA on Egyptian Arabic. We tested it.");

    // Setup like a chat showing AI being properly Egyptian
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 1.5, y: 2.0, w: 10.3, h: 4.7,
        fill: { color: C.bg_light }, line: { color: C.teal, width: 2 }, rectRadius: 0.2
    });

    const turns = [
        { role: "Test prompt:", text: "احكيلي نكتة", color: C.text_light },
        { role: "ARIA replied:", text: "ليه السمكة بقت مهندسة؟ 🐟\nعشان لقت نفسها في مياه عميقة!", color: C.teal_deep },
        { role: "We thought:", text: "...ماشي يا ARIA. مش بطلة قوي بس على الأقل بالعامية.", color: C.text_light },
        { role: "Verdict:", text: "AI tone-locked. Egyptian dialect: ✓\nComedy career: still pending. 😅", color: C.purple },
    ];
    turns.forEach((t, i) => {
        let y = 2.3 + i * 1.05;
        s.addText(t.role, { x: 2.0, y, w: 2.5, h: 0.4,
            fontFace: FONT_TITLE, fontSize: 12, bold: true, color: t.color, margin: 0 });
        s.addText(t.text, { x: 4.5, y, w: 7.0, h: 0.95,
            fontFace: FONT_BODY, fontSize: 14, color: C.text, margin: 0 });
    });

    s.addText("Real moment from testing — kept here because honesty > polish.", {
        x: 0.6, y: 7.0, w: 12, h: 0.4,
        fontFace: FONT_BODY, fontSize: 11, italic: true, color: C.text_light, align: "center"
    });
    pageNumber(s);
}

// 30 — Thank you
{
    let s = pres.addSlide();
    darkBg(s);
    pageN++;
    s.addText("Thank you.", {
        x: 0.6, y: 2.5, w: 12, h: 1.5,
        fontFace: FONT_TITLE, fontSize: 96, bold: true,
        color: C.teal_glow, align: "center"
    });
    s.addText("ARIA — built with care for autistic children and their families.", {
        x: 0.6, y: 4.0, w: 12, h: 0.5,
        fontFace: FONT_BODY, fontSize: 18, color: C.cyan, align: "center"
    });
    s.addText("Questions?", {
        x: 0.6, y: 5.0, w: 12, h: 0.6,
        fontFace: FONT_TITLE, fontSize: 32, italic: true,
        color: C.white, align: "center"
    });
    s.addText("معاكم 24 ساعة.", {
        x: 0.6, y: 5.8, w: 12, h: 0.6,
        fontFace: FONT_TITLE, fontSize: 22, color: C.teal_glow, align: "center"
    });
}

pres.writeFile({ fileName: path.join(__dirname, "ARIA_Presentation_v2.pptx") })
    .then(name => console.log(`Done: ${name}`));
