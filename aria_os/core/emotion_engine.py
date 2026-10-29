"""Light-weight emotion estimation from text. Used by MockAI + as fallback."""

POSITIVE_AR = ["مبسوط", "فرحان", "سعيد", "تمام", "حلو"]
SAD_AR      = ["زعلان", "زعلانة", "بعيط", "حزين", "تعبان"]
ANGRY_AR    = ["زهقان", "متضايق", "غضبان", "غاضب"]
SCARED_AR   = ["خايف", "خايفة", "مرعوب"]

POSITIVE_EN = ["happy", "good", "great", "yay", "fun"]
SAD_EN      = ["sad", "cry", "miss", "tired"]
ANGRY_EN    = ["angry", "mad", "upset", "annoyed"]
SCARED_EN   = ["scared", "afraid", "fear", "worried"]


def quick_emotion(text: str) -> str:
    if not text:
        return "neutral"
    low = text.lower()
    for w in POSITIVE_EN + POSITIVE_AR:
        if w in low: return "happy"
    for w in SAD_EN + SAD_AR:
        if w in low: return "sad"
    for w in ANGRY_EN + ANGRY_AR:
        if w in low: return "angry"
    for w in SCARED_EN + SCARED_AR:
        if w in low: return "scared"
    return "neutral"
