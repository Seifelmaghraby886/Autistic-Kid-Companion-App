"""Render the WANEES LinkedIn announcement poster — v3 (real logos).

If real logo files are present at:
    assets/logos/aast.png        (AASTMT institutional logo)
    assets/logos/autism.png      (puzzle-heart autism awareness logo)
they are embedded. Otherwise, drawn approximations are used as a fallback
so the poster always renders.

Output: slides/wanees_linkedin_poster.png  (1920x1080, 200 DPI)
"""
from __future__ import annotations

import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import (
    Circle, Rectangle, FancyBboxPatch, PathPatch,
)
from matplotlib.path import Path
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.image as mpimg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --------------------------------------------------------------------------- #
# Canvas — 16:9 banner
# --------------------------------------------------------------------------- #
FIG_W, FIG_H = 19.2, 10.8
DPI = 200

fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=DPI)
ax.set_xlim(0, 192)
ax.set_ylim(0, 108)
ax.axis("off")

# Calm palette — printed feel
BG       = "#FAF4EC"
PRIMARY  = "#2F7A7A"
PRIMARY2 = "#4F9C99"
NAVY     = "#0E2D4A"
DARK     = "#1A3A52"
ACCENT   = "#D97757"
GOLD     = "#C9A55C"
SUBTLE   = "#4A5566"
HAIRLINE = "#D7CFC0"

ax.set_facecolor(BG)
fig.patch.set_facecolor(BG)

# Outer hairline border
ax.add_patch(Rectangle((2, 2), 188, 104,
                       facecolor="none", edgecolor=HAIRLINE, linewidth=0.8))

# --------------------------------------------------------------------------- #
# Real-logo embedder (falls back to drawn placeholder if file missing)
# --------------------------------------------------------------------------- #
def embed_image(path, x, y, zoom):
    """Place an image centered on (x, y) in data coordinates. Returns True
    if the file existed and was embedded, False otherwise."""
    if not os.path.exists(path):
        return False
    img = mpimg.imread(path)
    oi  = OffsetImage(img, zoom=zoom)
    ab  = AnnotationBbox(oi, (x, y), frameon=False,
                         xycoords="data", pad=0)
    ax.add_artist(ab)
    return True


# --------------------------------------------------------------------------- #
# AAST logo  (top-left)
# --------------------------------------------------------------------------- #
AAST_PATH = os.path.join(ROOT, "assets", "logos", "aast.png")
aast_drawn = not embed_image(AAST_PATH, 11, 96.5, zoom=0.12)

# Fallback — stylized institutional seal
if aast_drawn:
    cx, cy, r = 11, 96.5, 6.0
    ax.add_patch(Circle((cx, cy), r,            facecolor=NAVY))
    ax.add_patch(Circle((cx, cy), r * 0.86,     facecolor=GOLD))
    ax.add_patch(Circle((cx, cy), r * 0.78,     facecolor=NAVY))
    ax.add_patch(Circle((cx, cy), r * 0.66,     facecolor=BG))
    wx = np.linspace(-r * 0.45, r * 0.45, 50)
    wy = np.sin(wx / (r * 0.10)) * (r * 0.07) - (r * 0.30)
    ax.plot(cx + wx, cy + wy,                color=NAVY, linewidth=1.4)
    ax.plot(cx + wx, cy + wy - 0.8,          color=GOLD, linewidth=1.0)
    ax.text(cx, cy + r * 0.12, "AASTMT",
            color=NAVY, fontsize=8.5, fontweight="bold",
            ha="center", va="center")

# AAST caption (right of the logo)
ax.text(20, 99.6, "AASTMT", color=NAVY, fontsize=13, fontweight="bold")
ax.text(20, 96.6,
        "Arab Academy for Science, Technology  &  Maritime Transport",
        color=SUBTLE, fontsize=8.5)
ax.text(20, 94.0,
        "Dept. of Mechanical  &  Computer Engineering   ·   2026 — 2027",
        color=SUBTLE, fontsize=8.2, style="italic")

# --------------------------------------------------------------------------- #
# Autism logo (top-right)
# --------------------------------------------------------------------------- #
AUTISM_PATH = os.path.join(ROOT, "assets", "logos", "autism.png")
autism_drawn = not embed_image(AUTISM_PATH, 178, 96.5, zoom=0.07)

# Fallback — drawn puzzle heart
if autism_drawn:
    cx, cy, r = 174, 96.5, 6.2
    YELLOW = "#F5C518"
    GREEN  = "#27AE60"
    BLUE   = "#3498DB"
    RED    = "#E74C3C"

    # Heart shape (parametric)
    n = 240
    t = np.linspace(0, 2 * np.pi, n)
    hx_raw = 16 * np.sin(t) ** 3
    hy_raw = 13 * np.cos(t) - 5 * np.cos(2*t) - 2 * np.cos(3*t) - np.cos(4*t)
    s = r / 16
    hx = hx_raw * s + cx
    hy = hy_raw * s + cy

    # Invisible heart-shaped clip path
    heart_path = Path(np.column_stack([hx, hy]), closed=True)
    clip_patch = PathPatch(heart_path, facecolor="none", edgecolor="none")
    ax.add_patch(clip_patch)

    # 4 colored quadrant rectangles, each clipped to the heart
    half = r * 1.4
    quads = [
        (YELLOW, cx - half, cy,         half, half),  # top-left
        (GREEN,  cx,        cy,         half, half),  # top-right
        (BLUE,   cx - half, cy - half,  half, half),  # bottom-left
        (RED,    cx,        cy - half,  half, half),  # bottom-right
    ]
    for color, rx, ry, rw, rh in quads:
        rect = Rectangle((rx, ry), rw, rh,
                         facecolor=color, edgecolor="none")
        ax.add_patch(rect)
        rect.set_clip_path(clip_patch)

    # Thick white seams (vertical + horizontal through center)
    ax.plot([cx, cx], [cy - r * 1.3, cy + r * 1.2],
            color="white", linewidth=4.5, solid_capstyle="round")
    ax.plot([cx - r * 1.2, cx + r * 1.2], [cy, cy],
            color="white", linewidth=4.5, solid_capstyle="round")
    # Center "puzzle bump"
    ax.add_patch(Circle((cx, cy), 1.0,
                        facecolor="white", edgecolor="none"))

    # Heart outline on top for crispness
    ax.plot(hx, hy, color="white", linewidth=2.2)

# Autism caption — only when the drawn placeholder is used; the real logo
# already carries its own wordmark.
if autism_drawn:
    ax.text(174, 89.0, "AUTISM AWARENESS", color="#3498DB", fontsize=8.6,
            fontweight="bold", ha="center")
    ax.text(174, 87.0, "Neurodiversity  ·  ASD", color="#E74C3C", fontsize=7.5,
            ha="center", style="italic")

# --------------------------------------------------------------------------- #
# Divider
# --------------------------------------------------------------------------- #
ax.add_patch(Rectangle((6, 83.5), 180, 0.18,
                       facecolor=HAIRLINE, edgecolor="none"))

# --------------------------------------------------------------------------- #
# LEFT — hero badge (W medallion)
# --------------------------------------------------------------------------- #
cx, cy, r = 42, 50, 22
ax.add_patch(Circle((cx, cy), r + 2.6, facecolor=PRIMARY, alpha=0.07))
ax.add_patch(Circle((cx, cy), r + 1.2, facecolor=PRIMARY, alpha=0.14))
ax.add_patch(Circle((cx, cy), r, facecolor="#FFFFFF",
                    edgecolor=PRIMARY, linewidth=2.6))
ax.add_patch(Circle((cx, cy), r - 1.5,
                    facecolor="none", edgecolor=PRIMARY,
                    alpha=0.35, linewidth=0.8))
ax.text(cx, cy + 1.2, "W", color=PRIMARY, fontsize=138, fontweight="bold",
        ha="center", va="center")

# 6-color autism spectrum dots
spectrum = ["#E74C3C", "#F39C12", "#F1C40F", "#27AE60", "#3498DB", "#9B59B6"]
for i, col in enumerate(spectrum):
    dx = cx - 6.5 + i * 2.6
    ax.add_patch(Circle((dx, cy - r + 4), 0.85, facecolor=col, edgecolor="none"))

ax.text(cx, cy - r - 6.5, "WANEES", color=NAVY, fontsize=30,
        fontweight="bold", ha="center")
ax.text(cx, cy - r - 10.8, '" a calm companion "', color=ACCENT,
        fontsize=11.5, ha="center", style="italic", fontweight="bold")

# Vertical divider between left and right
ax.add_patch(Rectangle((78, 14), 0.18, 66,
                       facecolor=HAIRLINE, edgecolor="none"))

# --------------------------------------------------------------------------- #
# RIGHT — title, supervisors, team
# --------------------------------------------------------------------------- #
x0 = 84

ax.text(x0, 78.5, "GRADUATION  PROJECT  ·  PHASE  I",
        color=ACCENT, fontsize=11.5, fontweight="bold")

ax.add_patch(Rectangle((x0 - 1.8, 60), 0.55, 15,
                       facecolor=ACCENT, edgecolor="none"))

ax.text(x0, 71.5, "AN  AI  COMPANION  ROBOT",
        color=DARK, fontsize=27, fontweight="bold")
ax.text(x0, 65.0, "FOR  CHILDREN  WITH  AUTISM",
        color=DARK, fontsize=27, fontweight="bold")

ax.text(x0, 59.0, "Affective Robot for Interactive Assistance",
        color=PRIMARY, fontsize=14.5, style="italic", fontweight="bold")

def pill(x, y, label, fill, fg):
    pw, ph = 9.6, 3.4
    ax.add_patch(FancyBboxPatch(
        (x, y - ph / 2), pw, ph,
        boxstyle="round,pad=0.0,rounding_size=1.5",
        facecolor=fill, edgecolor="none",
    ))
    ax.text(x + pw / 2, y, label, ha="center", va="center",
            color=fg, fontsize=10, fontweight="bold")

pill(x0,        52.6, "ARABIC",  "#E8F0EE", PRIMARY)
pill(x0 + 11.0, 52.6, "ENGLISH", "#E8F0EE", PRIMARY)
pill(x0 + 22.0, 52.6, "GERMAN",  "#E8F0EE", PRIMARY)
ax.text(x0 + 35, 52.6,
        "Multi-modal emotion AI   ·   ABA-aligned dialogue",
        color=SUBTLE, fontsize=10.5, va="center", style="italic")

ax.add_patch(Rectangle((x0, 47), 100, 0.18,
                       facecolor=HAIRLINE, edgecolor="none"))

ax.text(x0, 43.0, "SUPERVISED BY", color=ACCENT, fontsize=10.5,
        fontweight="bold")
ax.text(x0, 38.7, "Dr. Omneya Attallah", color=DARK, fontsize=15,
        fontweight="bold")
ax.text(x0, 35.0, "Dr. Dalia Sobhy", color=DARK, fontsize=15,
        fontweight="bold")

ax.text(x0, 28.0, "TEAM", color=ACCENT, fontsize=10.5, fontweight="bold")
ax.text(x0, 24.2,
        "Celine Ayman   ·   Mariam Onsy   ·   Seif Elmaghraby",
        color=DARK, fontsize=11.5, fontweight="bold")
ax.text(x0, 20.7,
        "Youssef Zohdy   ·   Mariam Yahia   ·   Jana Wael",
        color=DARK, fontsize=11.5, fontweight="bold")

ax.text(x0, 14.6,
        "Department of Mechanical  &  Computer Engineering   ·   AASTMT   ·   2026 — 2027",
        color=SUBTLE, fontsize=10, style="italic")

# --------------------------------------------------------------------------- #
# Bottom tagline band
# --------------------------------------------------------------------------- #
ax.add_patch(Rectangle((2, 2), 188, 5.5,
                       facecolor=PRIMARY, alpha=0.10))
ax.add_patch(Rectangle((2, 7.4), 188, 0.18,
                       facecolor=PRIMARY, alpha=0.45))
ax.text(96, 4.8,
        '"  Every Mind Matters.    Every Voice Deserves to Be Heard.  "',
        color=DARK, fontsize=13.5, fontweight="bold", ha="center",
        va="center", style="italic")

# --------------------------------------------------------------------------- #
# Save
# --------------------------------------------------------------------------- #
out_dir = os.path.join(ROOT, "slides")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "wanees_linkedin_poster.png")
plt.savefig(out_path, dpi=DPI, bbox_inches="tight",
            facecolor=fig.get_facecolor(), pad_inches=0.25)
plt.close(fig)

# Status report
print(f"Wrote {out_path}")
print(f"AAST  logo: {'drawn placeholder' if aast_drawn else 'real PNG embedded'}")
print(f"Autism logo: {'drawn placeholder' if autism_drawn else 'real PNG embedded'}")
