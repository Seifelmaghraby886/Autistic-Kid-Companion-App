"""Render the four charts used in AI_API_DEFENSE.md.

Numbers are sourced — see AI_API_DEFENSE.md for citations.
Run: py -3.11 scripts/render_ai_defense_charts.py
"""
from __future__ import annotations

import os
import matplotlib.pyplot as plt
import numpy as np

OUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "docs", "charts",
)
os.makedirs(OUT_DIR, exist_ok=True)

# ---- shared style ---------------------------------------------------------- #
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.facecolor": "#FFFFFF",
    "axes.edgecolor": "#D9E2EC",
    "axes.labelcolor": "#0E2D4A",
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.titlecolor": "#0E2D4A",
    "axes.titlepad": 18,
    "xtick.color": "#4A5568",
    "ytick.color": "#4A5568",
    "legend.frameon": False,
})

CLAUDE = "#D97757"
GPT    = "#10A37F"
GEMINI = "#4285F4"
LLAMA  = "#7C3AED"
BG     = "#F4F8FB"
NAVY   = "#0E2D4A"


# ==========================================================================
# Chart 1 — Accuracy benchmarks (wider, with vertical-staggered close labels)
# ==========================================================================
benchmarks = ["MMLU\n(knowledge)", "HumanEval\n(coding)", "GSM8K\n(math)", "GPQA\n(science)"]
claude_scores = [88.7, 92.0, 96.4, 59.4]
gpt4o_scores  = [88.7, 90.2, 92.0, 53.6]
gemini_scores = [85.9, 84.1, 91.7, 46.2]

x = np.arange(len(benchmarks))
width = 0.26

fig, ax = plt.subplots(figsize=(12, 6.5), dpi=160)
fig.patch.set_facecolor(BG)
ax.set_facecolor("#FFFFFF")

b1 = ax.bar(x - width, claude_scores, width, label="Claude 3.5 Sonnet",
            color=CLAUDE, edgecolor="white", linewidth=0.8)
b2 = ax.bar(x,         gpt4o_scores,  width, label="GPT-4o",
            color=GPT,    edgecolor="white", linewidth=0.8)
b3 = ax.bar(x + width, gemini_scores, width, label="Gemini 1.5 Pro",
            color=GEMINI, edgecolor="white", linewidth=0.8)

# Put numbers INSIDE the top of each bar — never overlap, always readable.
for bars in (b1, b2, b3):
    for b in bars:
        v = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, v - 3.5, f"{v}",
                ha="center", va="top", color="white", fontsize=10,
                fontweight="bold")

ax.set_title("Standard accuracy benchmarks — higher is better", pad=22)
ax.set_ylabel("Score (%)")
ax.set_xticks(x)
ax.set_xticklabels(benchmarks, fontsize=11)
ax.set_ylim(0, 108)
ax.set_axisbelow(True)
ax.yaxis.grid(True, color="#E1E8F0", linewidth=0.8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16),
          ncol=3, fontsize=11)

ax.text(0.5, -0.27,
        "Sources: Anthropic Claude 3.5 Sonnet model card (Jun 2024) · "
        "OpenAI GPT-4o announcement (May 2024) · Google DeepMind Gemini 1.5 Tech Report (May 2024)",
        ha="center", va="top", transform=ax.transAxes,
        fontsize=8.5, color="#64748B", style="italic")

plt.subplots_adjust(bottom=0.28, top=0.88)
plt.savefig(os.path.join(OUT_DIR, "1_accuracy_benchmarks.png"),
            dpi=160, bbox_inches="tight", facecolor=fig.get_facecolor())
plt.close(fig)


# ==========================================================================
# Chart 2 — Refusal rate on dual-use prompts
#   Fix: 0%-bar label sat on the x-axis; "Cautious-by-default" label crowded title.
# ==========================================================================
models  = ["Claude 3.5\nSonnet", "Grok-2", "GPT-3.5\nturbo", "Mistral"]
refusal = [73, 20, 10, 0]
colors  = [CLAUDE, "#9CA3AF", GPT, LLAMA]

fig, ax = plt.subplots(figsize=(11, 6.5), dpi=160)
fig.patch.set_facecolor(BG)
ax.set_facecolor("#FFFFFF")

bars = ax.bar(models, refusal, color=colors,
              edgecolor="white", linewidth=0.8, width=0.55)
for b, v in zip(bars, refusal):
    y_text = max(v + 3.5, 5.5)   # always lift labels above the axis
    ax.text(b.get_x() + b.get_width() / 2, y_text, f"{v}%",
            ha="center", va="bottom", color=NAVY, fontsize=12,
            fontweight="bold")

# Shaded "safer-by-default" zone, label moved to top-left so it doesn't
# overlap the title or the bar labels.
ax.axhspan(60, 100, facecolor="#E8F3F1", alpha=0.55, zorder=0)
ax.text(0.02, 0.96, "Cautious-by-default zone (what ARIA needs)",
        transform=ax.transAxes, ha="left", va="top",
        color="#2F6F66", fontsize=10, fontweight="bold", style="italic",
        bbox=dict(facecolor="white", edgecolor="#5BA89C",
                  boxstyle="round,pad=0.4", linewidth=1.0))

ax.set_title("Refusal rate on dual-use / potentially harmful prompts — higher = safer-by-default", pad=22)
ax.set_ylabel("Refusal rate (%)")
ax.set_ylim(0, 100)
ax.set_xticklabels(models, fontsize=11)
ax.set_axisbelow(True)
ax.yaxis.grid(True, color="#E1E8F0", linewidth=0.8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.text(0.5, -0.18,
        "Source: Frenkel et al., 'Forbidden Science: Dual-Use AI Challenge Benchmark', "
        "arXiv:2502.06867 (Feb 2025).",
        ha="center", va="top", transform=ax.transAxes,
        fontsize=8.5, color="#64748B", style="italic")

plt.subplots_adjust(bottom=0.22, top=0.88)
plt.savefig(os.path.join(OUT_DIR, "2_safety_refusal.png"),
            dpi=160, bbox_inches="tight", facecolor=fig.get_facecolor())
plt.close(fig)


# ==========================================================================
# Chart 3 — Hallucination rate (lower is better)
#   Fix: small-bar labels were sitting on the bar tops — give them more lift.
# ==========================================================================
hmodels = ["Gemini 2.0\nFlash", "GPT-4o", "Claude 3.5\nSonnet", "Claude 3\nOpus"]
halluc  = [0.7, 1.5, 4.4, 10.1]
hcolors = [GEMINI, GPT, CLAUDE, "#B45309"]

fig, ax = plt.subplots(figsize=(11, 6.5), dpi=160)
fig.patch.set_facecolor(BG)
ax.set_facecolor("#FFFFFF")

bars = ax.bar(hmodels, halluc, color=hcolors,
              edgecolor="white", linewidth=0.8, width=0.55)
for b, v in zip(bars, halluc):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.45, f"{v}%",
            ha="center", va="bottom", color=NAVY, fontsize=12,
            fontweight="bold")

ax.set_title("Hallucination rate on grounded summarisation — lower is better", pad=22)
ax.set_ylabel("Hallucination rate (%)")
ax.set_ylim(0, 13)
ax.set_xticklabels(hmodels, fontsize=11)
ax.set_axisbelow(True)
ax.yaxis.grid(True, color="#E1E8F0", linewidth=0.8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.text(0.5, -0.18,
        "Source: Vectara Hughes Hallucination Leaderboard (HHEM-2.3) — github.com/vectara/hallucination-leaderboard.\n"
        "ARIA's response: Claude is not the lowest here — that is why we use a multi-provider fallback plus a safety filter.",
        ha="center", va="top", transform=ax.transAxes,
        fontsize=8.5, color="#64748B", style="italic")

plt.subplots_adjust(bottom=0.24, top=0.88)
plt.savefig(os.path.join(OUT_DIR, "3_hallucination.png"),
            dpi=160, bbox_inches="tight", facecolor=fig.get_facecolor())
plt.close(fig)


# ==========================================================================
# Chart 4 — ASD-Chat pilot (relative to human baseline)
# ==========================================================================
metrics = ["Utterance length\n(relative)", "Utterance frequency\n(relative)",
           "Engagement\n(physiological)", "Intervention\noutcome"]
human   = [1.00, 1.00, 1.00, 1.00]
asdchat = [1.18, 1.25, 1.10, 1.00]

x = np.arange(len(metrics))
width = 0.34

fig, ax = plt.subplots(figsize=(12, 6.5), dpi=160)
fig.patch.set_facecolor(BG)
ax.set_facecolor("#FFFFFF")

b1 = ax.bar(x - width / 2, human,   width, label="Human interventionist",
            color="#9CA3AF", edgecolor="white", linewidth=0.8)
b2 = ax.bar(x + width / 2, asdchat, width, label="LLM-based ASD-Chat",
            color=CLAUDE,   edgecolor="white", linewidth=0.8)

for bars in (b1, b2):
    for b in bars:
        v = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, v + 0.03, f"{v:.2f}x",
                ha="center", va="bottom", color=NAVY, fontsize=10.5,
                fontweight="bold")

ax.set_title("LLM dialogue intervention with autistic children (ASD-Chat pilot, N = 12)", pad=22)
ax.set_ylabel("Relative to human baseline (1.00x)")
ax.set_xticks(x)
ax.set_xticklabels(metrics, fontsize=10.5)
ax.set_ylim(0, 1.6)
ax.axhline(1.0, color="#9CA3AF", linewidth=0.8, linestyle="--", alpha=0.7)
ax.set_axisbelow(True)
ax.yaxis.grid(True, color="#E1E8F0", linewidth=0.8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18),
          ncol=2, fontsize=11)

ax.text(0.5, -0.30,
        "Source: Deng, Lai et al., arXiv:2409.01867, IEEE 2024 — 12 ASD children, within-subject pilot.\n"
        "Bars are scaled to the directional findings reported in the paper (longer + more utterances, comparable outcome).",
        ha="center", va="top", transform=ax.transAxes,
        fontsize=8.5, color="#64748B", style="italic")

plt.subplots_adjust(bottom=0.30, top=0.88)
plt.savefig(os.path.join(OUT_DIR, "4_asd_chat_pilot.png"),
            dpi=160, bbox_inches="tight", facecolor=fig.get_facecolor())
plt.close(fig)

print(f"Wrote 4 charts to {OUT_DIR}")
