"""Render the right-side panel for the 'AI APIs' slide.

Drop this PNG onto the right side of the slide, under the
'WHAT WE CHOSE AND WHY' heading. Colors match the slide:
teal headings + light blue panel background.

Run: py -3.11 scripts/render_ai_apis_right_panel.py
"""
from __future__ import annotations

import os
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle

# --------------------------------------------------------------------------- #
# Canvas — proportions match the right panel of the slide
# --------------------------------------------------------------------------- #
FIG_W, FIG_H = 8, 10
DPI = 200

fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=DPI)
ax.set_xlim(0, 100)
ax.set_ylim(0, 125)
ax.axis("off")

# Match the slide's palette
PAGE_BG    = "#F4FAFC"
PANEL_BG   = "#E2F1F6"   # light cyan-blue like the other panel
TEAL       = "#1A6A7E"   # heading teal
TEAL_DARK  = "#0F4D5C"
INK        = "#0E2D4A"
SUBTLE     = "#4A5568"
ACCENT     = "#D97757"   # Anthropic-ish terracotta for the circle
CARD_BG    = "#FFFFFF"
CHECK      = "#1A6A7E"

ax.set_facecolor(PAGE_BG)
fig.patch.set_facecolor(PAGE_BG)

# Light-blue rounded panel that fills the area
ax.add_patch(FancyBboxPatch(
    (2, 2), 96, 121,
    boxstyle="round,pad=0,rounding_size=2.5",
    facecolor=PANEL_BG, edgecolor="none",
))

# --------------------------------------------------------------------------- #
# Big "Claude / Anthropic" circle at the top
# --------------------------------------------------------------------------- #
cx, cy, r = 50, 110, 9
# soft shadow
ax.add_patch(Circle((cx + 0.3, cy - 0.5), r,
                    facecolor="#C4D8DE", edgecolor="none", alpha=0.6))
# white face
ax.add_patch(Circle((cx, cy), r, facecolor=CARD_BG, edgecolor="none"))
# 'A' mark in Anthropic terracotta
ax.text(cx, cy, "A", ha="center", va="center",
        color=ACCENT, fontsize=36, fontweight="bold",
        family="DejaVu Sans")
# Label below the circle (not inside it)
ax.text(cx, cy - r - 3.5, "Claude  ·  Anthropic",
        ha="center", va="center",
        color=INK, fontsize=14, fontweight="bold")

# --------------------------------------------------------------------------- #
# 4 reason cards
# --------------------------------------------------------------------------- #
reasons = [
    ("SAFEST BY DEFAULT",
     "Refuses 73% of risky prompts",
     "vs only 10% for GPT-3.5"),
    ("PROVEN SAFETY TRAINING",
     "Uses Constitutional AI",
     "40.8% drop in harmful replies (peer-reviewed)"),
    ("STRONG ACCURACY",
     "88.7% knowledge   ·   92% coding",
     "Matches or beats GPT-4o on every test"),
    ("REMEMBERS THE SESSION",
     "200,000-token memory window",
     "Full child history fits in one conversation"),
]

card_w   = 84
card_h   = 14.5
gap      = 2
start_y  = 88   # top of first card

for i, (head, big, small) in enumerate(reasons):
    y_top = start_y - i * (card_h + gap)
    y_bot = y_top - card_h
    y_mid = (y_top + y_bot) / 2
    cx0 = 50 - card_w / 2

    # subtle shadow
    ax.add_patch(FancyBboxPatch(
        (cx0 + 0.4, y_bot - 0.4), card_w, card_h,
        boxstyle="round,pad=0,rounding_size=1.2",
        facecolor="#C4D8DE", edgecolor="none", alpha=0.55,
    ))
    # white card
    ax.add_patch(FancyBboxPatch(
        (cx0, y_bot), card_w, card_h,
        boxstyle="round,pad=0,rounding_size=1.2",
        facecolor=CARD_BG, edgecolor="#CFDEE4", linewidth=0.5,
    ))
    # left teal accent bar
    ax.add_patch(FancyBboxPatch(
        (cx0 + 0.4, y_bot + 0.7), 0.9, card_h - 1.4,
        boxstyle="round,pad=0,rounding_size=0.4",
        facecolor=TEAL, edgecolor="none",
    ))
    # check mark
    ax.text(cx0 + 4.5, y_mid + 3.2, "✓", ha="left", va="center",
            color=TEAL, fontsize=18, fontweight="bold")
    # heading
    ax.text(cx0 + 9, y_mid + 3.2, head, ha="left", va="center",
            color=TEAL_DARK, fontsize=11, fontweight="bold")
    # big line
    ax.text(cx0 + 9, y_mid - 0.4, big, ha="left", va="center",
            color=INK, fontsize=11, fontweight="bold")
    # small line
    ax.text(cx0 + 9, y_mid - 3.8, small, ha="left", va="center",
            color=SUBTLE, fontsize=9, style="italic")

# --------------------------------------------------------------------------- #
# Save
# --------------------------------------------------------------------------- #
out_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "slides",
)
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "ai_apis_right_panel.png")
plt.savefig(out_path, dpi=DPI, bbox_inches="tight",
            facecolor=fig.get_facecolor(), pad_inches=0.05)
plt.close(fig)
print(f"Wrote {out_path}")
