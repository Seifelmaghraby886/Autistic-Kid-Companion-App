"""Render the 'System Architecture at a Glance' slide.

Same design + colors as the source slide: title, 6 numbered teal circles,
4 white cards with teal top accents, teal safety-boundary callout.

Run: py -3.11 scripts/render_architecture_slide.py
"""
from __future__ import annotations

import os
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle
import matplotlib.patheffects as pe

# --------------------------------------------------------------------------- #
# Canvas (16:9 slide)
# --------------------------------------------------------------------------- #
FIG_W, FIG_H = 16, 9
DPI = 180

fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=DPI)
ax.set_xlim(0, 100)
ax.set_ylim(0, 56.25)  # 100 : 56.25 == 16 : 9
ax.axis("off")

# Page background
BG = "#F4F8FB"
ax.set_facecolor(BG)
fig.patch.set_facecolor(BG)

# Palette from the source slide
NAVY        = "#0E2D4A"
TEAL        = "#5B9BB7"
DARK_GRAY   = "#4A5568"
WHITE       = "#FFFFFF"
CARD_EDGE   = "#D9E2EC"
SAFETY_FILL = "#E8F3F1"
SAFETY_LINE = "#5BA89C"
SAFETY_TEXT = "#2F6F66"

# --------------------------------------------------------------------------- #
# Title
# --------------------------------------------------------------------------- #
ax.text(
    4.5, 50.5,
    "How ARIA Works",
    ha="left", va="center",
    color=NAVY, fontsize=28, fontweight="bold",
)

# --------------------------------------------------------------------------- #
# Step 1-6 — numbered circles
# --------------------------------------------------------------------------- #
steps = [
    ("1", "See & Hear", "Watches the face,\nlistens to the voice"),
    ("2", "Understand", "Reads feeling, words,\nand tone together"),
    ("3", "Combine",    "Weighs all the signals\ninto one clear read"),
    ("4", "Decide",     "Picks a reply that fits\nthe child and is safe"),
    ("5", "Reply",      "Speaks in Arabic, shows\npictures, or calms down"),
    ("6", "Remember",   "Saves today's session\nfor next time"),
]

# 6 circles spaced evenly across the slide
xs = [9.5, 24, 38.5, 53, 67.5, 82]
circle_y = 41.5
r = 3.4

for x, (num, name, desc) in zip(xs, steps):
    # Soft shadow under circle
    shadow = Circle((x + 0.15, circle_y - 0.25), r,
                    facecolor="#BFD4DF", edgecolor="none", alpha=0.55)
    ax.add_patch(shadow)
    # Teal circle
    ax.add_patch(Circle((x, circle_y), r, facecolor=TEAL, edgecolor="none"))
    # Big white number
    ax.text(x, circle_y, num, ha="center", va="center",
            color=WHITE, fontsize=24, fontweight="bold")
    # Step name (bold navy)
    ax.text(x, circle_y - r - 2.4, name, ha="center", va="center",
            color=NAVY, fontsize=14, fontweight="bold")
    # Description (gray, two lines for step 6)
    ax.text(x, circle_y - r - 5.4, desc, ha="center", va="top",
            color=DARK_GRAY, fontsize=9)

# --------------------------------------------------------------------------- #
# 4 white cards with teal top accent
# --------------------------------------------------------------------------- #
cards = [
    ("Child Profile",
     "Their age, language, what they\nenjoy, and how much help they need"),
    ("ARIA's Voice",
     "Talks back in Arabic, English, or\nGerman. Short, clear, never sarcastic"),
    ("Activities",
     "Picture cards, visual schedule,\nshort stories, Calm Zone, games"),
    ("Parent View",
     "A log of every session, mood\ntrends, and goals for next time"),
]

card_w = 21.5
card_h = 11
n = len(cards)
total_gap = 100 - n * card_w
gap = total_gap / (n + 1)
card_y_center = 18.5
top = card_y_center + card_h / 2
bottom = card_y_center - card_h / 2

for i, (header, desc) in enumerate(cards):
    cx = gap + (card_w + gap) * i + card_w / 2

    # Subtle shadow behind card
    ax.add_patch(FancyBboxPatch(
        (cx - card_w / 2 + 0.2, bottom - 0.25), card_w, card_h,
        boxstyle="round,pad=0,rounding_size=0.35",
        facecolor="#D9E2EC", edgecolor="none", alpha=0.55,
    ))
    # White card body
    ax.add_patch(FancyBboxPatch(
        (cx - card_w / 2, bottom), card_w, card_h,
        boxstyle="round,pad=0,rounding_size=0.35",
        facecolor=WHITE, edgecolor=CARD_EDGE, linewidth=0.6,
    ))
    # Teal top accent bar (inside the card)
    ax.add_patch(Rectangle(
        (cx - card_w / 2 + 0.55, top - 1.05), card_w - 1.1, 0.55,
        facecolor=TEAL, edgecolor="none",
    ))
    # Header
    ax.text(cx, top - 3.0, header, ha="center", va="center",
            color=NAVY, fontsize=12, fontweight="bold")
    # Description body
    ax.text(cx, bottom + 3.6, desc, ha="center", va="center",
            color=DARK_GRAY, fontsize=9.2)

# --------------------------------------------------------------------------- #
# Safety-boundary callout
# --------------------------------------------------------------------------- #
safety_text = (
    "ARIA is a companion, not a clinician. "
    "When it isn't sure how the child feels, it pauses and lets the parent step in. "
    "It does not diagnose anything."
)
safety_x = 4.5
safety_w = 91
safety_y_center = 6.5
safety_h = 4.4

ax.add_patch(FancyBboxPatch(
    (safety_x, safety_y_center - safety_h / 2), safety_w, safety_h,
    boxstyle="round,pad=0,rounding_size=0.3",
    facecolor=SAFETY_FILL, edgecolor=SAFETY_LINE, linewidth=1.6,
))
ax.text(safety_x + safety_w / 2, safety_y_center, safety_text,
        ha="center", va="center",
        color=SAFETY_TEXT, fontsize=10.5)

# --------------------------------------------------------------------------- #
# Save
# --------------------------------------------------------------------------- #
out_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "slides",
)
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "system_architecture_at_a_glance.png")

plt.savefig(out_path, dpi=DPI, bbox_inches="tight",
            facecolor=fig.get_facecolor(), pad_inches=0.15)
plt.close(fig)
print(f"Wrote {out_path}")
