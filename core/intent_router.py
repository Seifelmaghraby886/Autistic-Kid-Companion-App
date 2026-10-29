"""
ARIA Intent Router
==================
Turns a transcribed voice line into an action decision. Pure functions — no
Qt, no I/O — so it is trivially testable and fast.

    route(text) -> (kind, payload)
        kind == "navigate"  payload = a destination key for main._navigate()
        kind == "command"   payload = a global command ("stop" / "repeat")
        kind == "talk"      payload = cleaned text to send to the AI companion

Design intent: the router is deliberately conservative. A bare keyword inside
a sentence ("I like to play with my dog") must NOT hijack the conversation and
open a screen. Navigation fires only when the child clearly asks for it —
either with the wake word ("ARIA, open games") or an explicit open verb
("open games", "I want the calm zone", "عايز ألعب").

Languages: English, Egyptian Arabic (عامية), German.
"""

import re

__all__ = ["route", "normalize", "detect_navigation"]


# ── Arabic normalisation ──────────────────────────────────────────────
# Strip tashkeel/diacritics and the tatweel, unify alef/ya/ta-marbuta so
# that STT spelling variants all match the same keyword.
_AR_DIACRITICS = re.compile(r"[ؗ-ًؚ-ْٰـ]")


def normalize(text: str) -> str:
    """Lower-case, de-punctuate and normalise Arabic letter variants."""
    t = (text or "").strip().lower()
    t = _AR_DIACRITICS.sub("", t)
    t = (t.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
           .replace("ى", "ي").replace("ة", "ه").replace("ﻻ", "لا"))
    t = re.sub(r"[^\w؀-ۿ\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


# ── Vocabularies ──────────────────────────────────────────────────────
WAKE_WORDS = ["aria", "ariya", "areya", "ariia", "arya", "اريا", "ارىا", "اريه"]
_STRIP_TOKENS = set(WAKE_WORDS) | {"os", "يا"}

OPEN_VERBS = [
    "open", "show", "show me", "go to", "go", "start", "launch", "take me to",
    "i want", "i wanna", "wanna", "can i", "let's", "lets", "bring",
    "tell me", "tell", "read me", "give me", "play me",
    "افتح", "افتحي", "افتحلي", "وريني", "ورني", "روح", "روحي", "عايز", "عايزه",
    "عاوز", "عاوزه", "نفتح", "ابدا", "يلا", "هات", "ممكن", "وري",
    "احكيلي", "احكي", "احكيلى", "اقرالي", "اقرا", "شغللي", "شغل",
    "öffne", "zeig", "zeige", "starte", "ich will", "geh", "erzähl", "erzähle",
]

# destination key -> trigger keywords (must match main.py nav_map keys)
NAV_KEYWORDS = {
    "talk":       ["talk", "chat", "speak", "conversation", "reden", "sprechen",
                   "unterhalten", "اتكلم", "نتكلم", "كلام", "كلمني", "اكلمك",
                   "احكي", "تكلم", "حوار"],
    "calm":       ["calm", "calm zone", "relax", "quiet zone", "ruhe", "beruhig",
                   "هدوء", "الهدوء", "اهدا", "ركن الهدوء", "ركن الهدا", "ارتاح",
                   "استرخاء"],
    "schedule":   ["schedule", "routine", "my plan", "my day", "plan", "zeitplan",
                   "جدول", "روتين", "برنامج", "برنامجي", "جدولي", "مهامي"],
    "games":      ["game", "games", "play game", "spiel", "spielen", "لعبه",
                   "العب", "نلعب", "العاب", "لعب"],
    "camera":     ["emotion room", "emotion", "camera", "my face", "face camera",
                   "feelings camera", "kamera", "gefuhle", "gefuhl", "كاميرا",
                   "مشاعر", "غرفه المشاعر", "وشي", "وشك"],
    "photo":      ["photo", "picture", "image", "foto", "bild", "صوره", "صور"],
    "comms":      ["communication board", "talk board", "comm board", "board",
                   "kommunikation", "لوحه التواصل", "تواصل", "البورد"],
    "aac":        ["aac", "aac builder", "word builder", "sentence builder",
                   "picture words", "باني الجمل", "بناء الجمل", "صور الكلمات"],
    "sensory":    ["sensory", "sensory toolkit", "senses", "حواس", "الحواس",
                   "حسي", "ادوات حسيه", "حسيه"],
    "journal":    ["journal", "mood journal", "diary", "tagebuch", "يوميات",
                   "المذكرات", "مذكرات", "يومياتي"],
    "story":      ["story", "tell me a story", "social story", "geschichte",
                   "قصه", "حكايه", "قصص"],
    "bedtime":    ["bedtime", "bedtime story", "good night", "sleep story",
                   "schlafenszeit", "gute nacht", "وقت النوم", "قصه قبل النوم",
                   "تصبح على خير", "قصه النوم"],
    "rewards":    ["reward", "rewards", "stars", "star jar", "prize", "belohnung",
                   "مكافاه", "مكافات", "نجوم", "نجومي", "الجوايز", "جوايز"],
    "timer":      ["timer", "countdown", "stopwatch", "wecker", "مؤقت",
                   "الميقاتي", "عداد الوقت"],
    "transition": ["transition", "transition helper", "change activity",
                   "ubergang", "انتقال", "تغيير النشاط"],
    "coach":      ["coach", "coping coach", "ai coach", "calm coach", "مدرب",
                   "المدرب", "مدرب الهدوء"],
    "insights":   ["insights", "ai insights", "my progress", "analysis",
                   "einblicke", "تحليلات", "رؤى", "تقدمي"],
    "music":      ["music", "song", "songs", "sound garden", "sounds",
                   "play music", "musik", "lied", "موسيقى", "اغنيه", "اغاني",
                   "اصوات", "حديقه الاصوات"],
    "tutorials":  ["tutorial", "tutorials", "how to", "task tutorial", "learn to",
                   "anleitung", "تعليم", "تعليمات", "ازاي اعمل", "اتعلم", "شرح",
                   "الدروس"],
    "thermometer":["thermometer", "feelings thermometer", "feeling meter",
                   "ترمومتر", "مقياس المشاعر", "ترمومتر المشاعر"],
    "firstthen":  ["first then", "first and then", "first-then",
                   "zuerst dann", "الاول وبعدين", "الأول وبعدين"],
    "social":     ["social", "social coach", "social skills", "make friends",
                   "sozial", "اجتماعي", "المهارات الاجتماعيه", "اصحاب", "اصدقاء"],
    "biometric":  ["biometric", "heart rate", "heartbeat", "my heart", "pulse",
                   "herzfrequenz", "نبض", "نبضات", "نبض القلب"],
    "settings":   ["settings", "setting", "options", "preferences",
                   "einstellungen", "اعدادات", "الاعدادات", "الضبط", "ضبط"],
    "providers":  ["control center", "provider center", "providers", "provider",
                   "control panel", "ai control", "switch provider",
                   "مركز التحكم", "لوحه التحكم", "المزودين", "البروفايدر"],
    "parent":     ["parent", "parents", "parent mode", "mom", "dad", "mommy",
                   "grown up", "eltern", "بابا", "ماما", "ولي الامر", "وضع الاهل",
                   "حد كبير"],
    "dashboard":  ["dashboard", "all tools", "all features", "menu", "more",
                   "ubersicht", "كل الادوات", "كل الحاجات", "القائمه", "المزيد"],
}

# Most-specific destinations first so multi-word phrases win over their
# substrings (e.g. "bedtime story" beats bare "story").
_PRIORITY = ["firstthen", "bedtime", "thermometer", "aac", "biometric", "insights",
             "transition", "sensory", "rewards", "journal", "coach", "social",
             "tutorials", "music", "story", "games", "calm", "schedule",
             "comms", "camera", "photo", "talk", "providers", "settings",
             "parent", "dashboard"]

# ── Global commands ───────────────────────────────────────────────────
HOME_WORDS = ["go back", "back", "home", "go home", "exit", "close this",
              "close", "return", "main screen", "ارجع", "رجوع", "البيت",
              "الرئيسيه", "اقفل", "قفل", "اخرج", "خروج", "ارجعني",
              "zuruck", "nach hause"]
STOP_WORDS = ["stop", "be quiet", "quiet", "hush", "stop talking", "stop it",
              "enough", "بطل", "بطلي", "اسكت", "اسكتي", "وقف", "كفايه",
              "stopp", "sei still"]
REPEAT_WORDS = ["repeat", "say again", "again", "come again", "one more time",
                "what did you say", "تاني", "كرر", "كرري", "قول تاني",
                "قولي تاني", "عيد", "wiederhole", "nochmal"]


# ── Matching helpers ──────────────────────────────────────────────────
def _has_phrase(text: str, phrases) -> bool:
    """True if any phrase appears as a whole word / word-sequence in text."""
    words = text.split()
    wset = set(words)
    padded = " " + text + " "
    for p in phrases:
        if " " in p:
            if (" " + p + " ") in padded:
                return True
        elif p in wset:
            return True
    return False


def _strip_wake(text: str) -> str:
    words = text.split()
    while words and words[0] in _STRIP_TOKENS:
        words.pop(0)
    while words and words[-1] in _STRIP_TOKENS:
        words.pop()
    return " ".join(words)


def detect_navigation(text: str):
    """Return a destination key if `text` is an explicit open request, else None."""
    norm = normalize(text)
    if not norm:
        return None
    has_wake = _has_phrase(norm, WAKE_WORDS)
    body = _strip_wake(norm) if has_wake else norm
    if not (has_wake or _has_phrase(body, OPEN_VERBS)):
        return None
    for dest in _PRIORITY:
        for kw in NAV_KEYWORDS[dest]:
            if kw in body:
                return dest
    return None


def route(text: str):
    """Classify a transcribed line. See module docstring for the contract."""
    raw = (text or "").strip()
    norm = normalize(raw)
    if not norm:
        return ("talk", raw)

    short = len(norm.split()) <= 4  # commands are terse, full of intent

    # 1) Global commands — only when the utterance is essentially the command.
    if short and _has_phrase(norm, HOME_WORDS):
        return ("navigate", "home")
    if short and _has_phrase(norm, STOP_WORDS):
        return ("command", "stop")
    if short and _has_phrase(norm, REPEAT_WORDS):
        return ("command", "repeat")

    # 2) Explicit navigation ("ARIA open games", "I want the calm zone").
    dest = detect_navigation(raw)
    if dest:
        return ("navigate", dest)

    # 3) Everything else is conversation for the AI companion.
    return ("talk", raw)
