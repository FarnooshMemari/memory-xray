#!/usr/bin/env python3
"""Presentation figures for the Results and Discussion report.

Inputs: results/report_numbers.json, results/reanalysis.json and the saved
S-conflict cells. Output: results/figures/fig*.png (16:9, light surface).
Palette: dataviz reference palette (validated); Positive/Neutral/Negative use
the blue-red diverging pair with a neutral gray midpoint.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
NUM = json.loads((ROOT / "results" / "report_numbers.json").read_text())
RE = json.loads((ROOT / "results" / "reanalysis.json").read_text())
PRE = NUM["pre_registered"]
OUT = ROOT / "results" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
POS, NEU, NEG = "#2a78d6", "#a3a29a", "#e34948"
GOOD, CRIT = "#0ca30c", "#d03b3b"
LABEL_COLOR = {"Positive": POS, "Neutral": NEU, "Negative": NEG}
L = ("Positive", "Neutral", "Negative")
P = ("E1", "E2", "E3", "E4")
NAMES = {"s_single": "S-single", "s_redundant": "S-redundant", "s_conflict": "S-conflict",
         "macro_a": "Macro A", "macro_b": "Macro B", "macro_c": "Macro C"}
ORDER = ("s_single", "s_redundant", "s_conflict", "macro_a", "macro_b", "macro_c")

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": AXIS, "axes.linewidth": 1,
    "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
    "axes.facecolor": SURFACE, "figure.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
    "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlecolor": INK,
})


def style(ax, grid_axis="y"):
    ax.grid(axis=grid_axis, color=GRID, linewidth=1, linestyle="-")
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def save(fig, name):
    fig.savefig(OUT / name, dpi=200, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    print("wrote", OUT / name)


# ---------- Fig 1: validation overview ----------
def fig1():
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.set_xlim(0, 10.6)
    ax.set_ylim(0, 7)
    ax.axis("off")
    cols = [("Infrastructure\nI1–I9", 0.0, 1.5),
            ("Recovery checks (frozen thresholds;\neach must hold in all 3 orderings)", 1.6, 6.25),
            ("Descriptive flags", 7.95, 2.6)]
    for title, x, w in cols:
        ax.text(x + w / 2 if w < 2.6 else x + w / 2, 6.55, title, ha="center", va="center", fontsize=9.5, color=INK2)
    flags_txt = {
        "s_conflict": "φ(E1), φ(E2) vary by ordering;\nfull-set argmax varies",
        "macro_a": "φ(E3) varies by ordering;\nfull-set argmax varies",
        "macro_b": "φ(E1) range 0.101",
    }
    for r, sid in enumerate(ORDER):
        y = 5.4 - r * 0.95
        e = PRE[sid]
        ax.text(-0.15, y + 0.4, NAMES[sid], ha="right", va="center", fontsize=11, fontweight="bold")
        infra_ok = all(e["infra"][f"I{i}"] for i in range(1, 10))
        ax.add_patch(Rectangle((0, y), 1.5, 0.8, facecolor=GOOD if infra_ok else CRIT, alpha=0.16, linewidth=0))
        ax.text(0.75, y + 0.4, ("✓ 9/9" if infra_ok else "✗"), ha="center", va="center", fontsize=10.5)
        checks = list(e["checks"].items())
        if not checks:
            ax.add_patch(Rectangle((1.6, y), 6.25, 0.8, facecolor=GRID, alpha=0.6, linewidth=0))
            ax.text(1.6 + 3.125, y + 0.4, "realistic scenario: descriptive only (no pass/fail recovery checks)",
                    ha="center", va="center", fontsize=9.5, color=INK2)
        for i, (cid, ok) in enumerate(checks):
            x = 1.6 + i * 1.05
            ax.add_patch(Rectangle((x, y), 1.0, 0.8, facecolor=GOOD if ok else CRIT, alpha=0.16 if ok else 0.22, linewidth=0))
            ax.text(x + 0.5, y + 0.4, f"{'✓' if ok else '✗'} {cid}", ha="center", va="center", fontsize=10,
                    fontweight="normal" if ok else "bold")
        ax.text(7.95, y + 0.4, flags_txt.get(sid, "none"), ha="left", va="center", fontsize=9, color=INK2)
    ax.text(0, 0.05, "✓ pass   ✗ fail.  Recovery checks: B = single decisive, BR = redundant, BC = conflict (frozen thresholds). "
            "Infrastructure checks passed in every scenario.", fontsize=9, color=INK2)
    fig.suptitle("Validation: the measurement pipeline passed everywhere; one designed control (S-conflict) failed",
                 x=0.02, ha="left", fontsize=13, fontweight="bold")
    save(fig, "fig1_validation_overview.png")


# ---------- Fig 2: Shapley vs leave-one-out on the synthetic controls ----------
def fig2():
    roles = {
        "s_single": ["distractor", "rate cut\n(decisive)", "distractor", "distractor"],
        "s_redundant": ["official\nreport A", "commentary\n(excluded)", "official\nreport B", "distractor"],
        "s_conflict": ["rate cut\n(dominant)", "inflation\n(subord.)", "distractor", "distractor"],
    }
    fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.9), sharey=True)
    for ax, sid in zip(axes, ("s_single", "s_redundant", "s_conflict")):
        e = PRE[sid]
        style(ax)
        xs = range(4)
        for j, (key, color, off) in enumerate((("shapley", BLUE, -0.19), ("loo", ORANGE, 0.19))):
            m = [e[key][p]["mean"] for p in P]
            lo = [e[key][p]["min"] for p in P]
            hi = [e[key][p]["max"] for p in P]
            ax.bar([x + off for x in xs], m, width=0.36, color=color, edgecolor=SURFACE, linewidth=2, zorder=3)
            ax.vlines([x + off for x in xs], lo, hi, color=INK2, linewidth=1.2, zorder=4)
        ax.axhline(0, color=AXIS, linewidth=1)
        ax.set_xticks(list(xs))
        ax.set_xticklabels([f"{p}\n{r}" for p, r in zip(P, roles[sid])], fontsize=9)
        ax.set_title(f"{NAMES[sid]} (d* = {e['d_star']})", loc="left")
        ax.set_ylim(-0.7, 1.12)
    axes[0].set_ylabel("Effect on P(d*) (probability units)")
    for xloo in (0.19, 2.19):
        axes[1].text(xloo, 0.03, "≈0", ha="center", va="bottom", fontsize=8.5, color=INK2)
    axes[1].text(1.2, 0.78, "Leave-one-out ≈ 0 for both official reports\n(each is redundant with the other);\n"
                 "Shapley splits the credit ≈ 0.48 / 0.48", ha="center", va="bottom", fontsize=9, color=INK2)
    axes[2].annotate("Inflation record still lowers P(Positive)\nwhen the rate cut is present:\n"
                     "the precedence rule is not applied", xy=(1.0, -0.2), xytext=(1.55, 0.62),
                     fontsize=9, color=INK2, arrowprops=dict(arrowstyle="-", color=MUTED, linewidth=1))
    fig.legend(handles=[Patch(color=BLUE, label="Shapley value"), Patch(color=ORANGE, label="Leave-one-out"),
                        Line2D([], [], color=INK2, linewidth=1.2, label="range across 3 orderings")],
               loc="upper right", ncol=3, fontsize=10, bbox_to_anchor=(0.99, 1.02))
    fig.suptitle("Synthetic controls: Shapley recovers single and redundant causes that leave-one-out can miss",
                 x=0.02, ha="left", fontsize=13, fontweight="bold", y=1.04)
    save(fig, "fig2_controls_shapley_vs_loo.png")


# ---------- Fig 3: S-conflict ordering effect ----------
def fig3():
    cells = [json.loads(l) for l in (ROOT / "runs" / RE["run_id"] / "s_conflict" / "cells.jsonl").read_text().splitlines()]
    rows = []
    for k in range(3):
        for subset in ("E1+E2", "E1+E2+E3", "E1+E2+E4", "E1+E2+E3+E4"):
            x = next(c for c in cells if c["ordering"] == k and c["subset"] == subset)
            order = x["shown_canonical"]
            later = "E1" if order.index("E1") > order.index("E2") else "E2"
            rows.append((k, subset, later, x["score"]["p_norm"], x["score"]["argmax"], " → ".join(order)))
    fig, ax = plt.subplots(figsize=(12, 6.2))
    style(ax, "x")
    ys = []
    for i, (k, subset, later, p, arg, order) in enumerate(rows):
        y = len(rows) - 1 - i - (k * 0.6)
        ys.append(y)
        left = 0
        for lab in L:
            ax.barh(y, p[lab], left=left, color=LABEL_COLOR[lab], edgecolor=SURFACE, linewidth=2, height=0.7, zorder=3)
            if p[lab] > 0.09:
                ax.text(left + p[lab] / 2, y, f"{p[lab]:.2f}", ha="center", va="center", fontsize=8.5,
                        color="white" if lab != "Neutral" else INK)
            left += p[lab]
        ax.text(-0.02, y, f"ordering {k} · {order}", ha="right", va="center", fontsize=8.5, color=INK2)
        ax.text(1.02, y, f"later: {later}  →  {arg}", ha="left", va="center", fontsize=9,
                fontweight="bold" if arg == "Positive" else "normal")
    ax.set_xlim(0, 1)
    ax.set_yticks([])
    ax.set_xlabel("Label probability (normalized over the three labels)")
    ax.legend(handles=[Patch(color=POS, label="Positive (designed answer: the rate cut takes precedence)"),
                       Patch(color=NEU, label="Neutral"), Patch(color=NEG, label="Negative (inflation record)")],
              loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3, fontsize=9.5)
    ax.set_title("S-conflict: in all 12 cells containing both conflicting records, the label follows whichever came later",
                 loc="left", fontsize=12.5)
    save(fig, "fig3_s_conflict_ordering_effect.png")


# ---------- Fig 4: Macro A decision instability ----------
def fig4():
    e = PRE["macro_a"]
    dists = e["full_dist_per_ordering"] + [e["mean_full_dist"]]
    names = ["ordering 0", "ordering 1", "ordering 2", "mean over\norderings"]
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    style(ax)
    for i, d in enumerate(dists):
        bottom = 0
        for lab in L:
            ax.bar(i, d[lab], bottom=bottom, width=0.5, color=LABEL_COLOR[lab], edgecolor=SURFACE, linewidth=2, zorder=3)
            if d[lab] > 0.08:
                ax.text(i, bottom + d[lab] / 2, f"{d[lab]:.2f}", ha="center", va="center", fontsize=9.5,
                        color="white" if lab != "Neutral" else INK)
            bottom += d[lab]
        srt = sorted(d.values(), reverse=True)
        top = max(d, key=d.get)
        ax.text(i, 1.03, f"argmax {top}\nmargin {srt[0] - srt[1]:.3f}", ha="center", va="bottom", fontsize=9.5,
                fontweight="bold" if i == 3 else "normal")
    ax.set_xticks(range(4))
    ax.set_xticklabels(names)
    ax.set_ylim(0, 1.18)
    ax.set_ylabel("Full-evidence label probability")
    ax.legend(handles=[Patch(color=c, label=l) for l, c in LABEL_COLOR.items()], loc="upper right",
              bbox_to_anchor=(1.0, -0.1), ncol=3, fontsize=10)
    ax.set_title("Macro A: the full-evidence decision is Neutral in one ordering; d* = Positive by a 0.02 mean margin",
                 loc="left", fontsize=12.5)
    save(fig, "fig4_macro_a_decision.png")


# ---------- Fig 5: flip effects ----------
def fig5():
    fig, ax = plt.subplots(figsize=(11, 5.6))
    style(ax, "x")
    y = 0
    yt, yl = [], []
    for sid in ("macro_c", "macro_b", "macro_a"):
        e = PRE[sid]
        for f in reversed(e["flips"]):
            changed = f["argmax"] != f["orig_argmax"]
            ax.plot([f["p_dstar_orig"], f["p_dstar_flip"]], [y, y], color=AXIS, linewidth=2, zorder=2)
            ax.scatter(f["p_dstar_orig"], y, s=70, color=MUTED, edgecolor=SURFACE, linewidth=2, zorder=3)
            ax.scatter(f["p_dstar_flip"], y, s=80, color=BLUE if changed else SURFACE, edgecolor=BLUE,
                       linewidth=2, zorder=4)
            ax.text(1.02, y, f"Δ {f['delta_p_dstar']:+.2f}   {f['orig_argmax']} → {f['argmax']}".replace("-", "−"), va="center",
                    fontsize=9, color=INK if changed else INK2)
            yt.append(y)
            yl.append(f"{NAMES[sid]} · ordering {f['ordering']}")
            y += 1
        y += 0.6
    ax.set_yticks(yt)
    ax.set_yticklabels(yl, fontsize=9.5)
    ax.set_xlim(0, 1)
    ax.set_xlabel("P(d*) with the original evidence → with one record flipped (full evidence set)")
    ax.legend(handles=[Line2D([], [], marker="o", color="w", markerfacecolor=MUTED, markersize=9, label="original"),
                       Line2D([], [], marker="o", color="w", markerfacecolor=BLUE, markeredgecolor=BLUE, markersize=9,
                              label="flipped: label changed"),
                       Line2D([], [], marker="o", color="w", markerfacecolor=SURFACE, markeredgecolor=BLUE,
                              markersize=9, markeredgewidth=2, label="flipped: label unchanged")],
              loc="upper center", bbox_to_anchor=(0.45, -0.12), ncol=3, fontsize=9.5)
    ax.set_title("Counterfactual flips: P(d*) falls in all 9 cells (−0.17 to −0.54); the label changes in 5 of 9",
                 loc="left", fontsize=12.5)
    save(fig, "fig5_flip_effects.png")


# ---------- Fig 6: realistic Shapley vs rubric-ideal ----------
def fig6():
    labels = {
        "macro_a": ["E1\nrate\ncut\n(supports)", "E2\ninflation\neasing\n(supports)", "E3\nPMI\ncontraction\n(contrary)",
                    "E4\nearnings\nupgrade\n(supports)"],
        "macro_b": ["E1\nrate\nhike\n(supports)", "E2\ninflation\nrising\n(supports)", "E3\nservices\nPMI\n(contrary)",
                    "E4\nearnings\ncut\n(supports)"],
        "macro_c": ["E1\nrate\ncut\n(contrary)", "E2\njobs\nweakening\n(supports)", "E3\ncredit\ntightening\n(supports)",
                    "E4\nearnings\ncut\n(supports)"],
    }
    fig, axes = plt.subplots(1, 3, figsize=(14.5, 5.4), sharey=True)
    fig.subplots_adjust(wspace=0.12)
    for ax, sid in zip(axes, ("macro_a", "macro_b", "macro_c")):
        e = PRE[sid]
        style(ax)
        m = [e["shapley"][p]["mean"] for p in P]
        ax.bar(range(4), m, width=0.5, color=BLUE, edgecolor=SURFACE, linewidth=2, zorder=3)
        ax.vlines(range(4), [e["shapley"][p]["min"] for p in P], [e["shapley"][p]["max"] for p in P],
                  color=INK2, linewidth=1.2, zorder=4)
        ax.hlines([e["rubric_ideal_shapley"][p] for p in P], [x - 0.34 for x in range(4)],
                  [x + 0.34 for x in range(4)], color=INK, linewidth=2, zorder=5)
        for x, val in enumerate(m):
            if abs(val) >= 0.12:
                ax.text(x - 0.13, val / 2 if val > 0 else val * 0.7, f"{val:+.2f}".replace("-", "−"), ha="center", va="center", fontsize=9,
                        color="white", rotation=90, zorder=6)
            else:
                ax.text(x + 0.3, -0.06, f"{val:+.2f}".replace("-", "−"), ha="left", va="center", fontsize=9, color=INK)
        ax.axhline(0, color=AXIS, linewidth=1)
        ax.set_xticks(range(4))
        ax.set_xticklabels(labels[sid], fontsize=8)
        ax.set_title(f"{NAMES[sid]}\nd* = {e['d_star']} (rubric reference: {e['reference']})", loc="left", fontsize=11)
        ax.set_ylim(-0.65, 0.6)
    axes[0].set_ylabel("Shapley value on P(d*)")
    fig.legend(handles=[Patch(color=BLUE, label="model: mean over 3 orderings"),
                        Line2D([], [], color=INK2, linewidth=1.2, label="range across orderings"),
                        Line2D([], [], color=INK, linewidth=2, label="rubric-following ideal (computed offline, pre-run)")],
               loc="upper center", ncol=3, fontsize=10, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("Realistic scenarios: Macro A's contrary record is over-weighted; Macro C's salient rate cut is ignored",
                 x=0.02, ha="left", fontsize=13, fontweight="bold", y=1.03)
    save(fig, "fig6_realistic_shapley_vs_rubric.png")


# ---------- Fig 7: citations ----------
def fig7():
    fig, (a, b) = plt.subplots(1, 2, figsize=(14, 5.4), sharey=True, gridspec_kw={"width_ratios": [1, 1.2]})
    fig.subplots_adjust(wspace=0.08)
    style(a, "x")
    status_colors = (("ok", BLUE, "parsed list"), ("empty", AQUA, "empty list []"), ("unparseable", ORANGE, "unparseable"))
    for i, sid in enumerate(reversed(ORDER)):
        st = PRE[sid]["citations"]["sampled_status"]
        left = 0
        for k, c, _ in status_colors:
            n = st.get(k, 0)
            if n:
                a.barh(i, n, left=left, color=c, edgecolor=SURFACE, linewidth=2, height=0.6, zorder=3)
                a.text(left + n / 2, i, str(n), ha="center", va="center", fontsize=9.5,
                       color="white" if c != AQUA else INK)
            left += n
    a.set_yticks(range(6))
    a.set_yticklabels([NAMES[s] for s in reversed(ORDER)])
    a.set_xlim(0, 10)
    a.set_xticks([0, 2, 4, 6, 8, 10])
    a.set_xlabel("Sampled replies (10 per scenario, temperature 1.0)")
    a.set_title("A. Parse outcome: 46/60 sampled analyzable\n(greedy references: 18/18 parsed)", loc="left", fontsize=11)
    a.legend(handles=[Patch(color=c, label=l) for _, c, l in status_colors], loc="upper center",
             bbox_to_anchor=(0.5, -0.14), ncol=3, fontsize=9.5)

    style(b, "x")
    for i, sid in enumerate(reversed(ORDER)):
        c = PRE[sid]["citations"]
        b.scatter(c["all"]["mean_beat_nec"], i + 0.13, s=80, color=BLUE, edgecolor=SURFACE, linewidth=2, zorder=4)
        b.scatter(c["all"]["mean_beat_suf"], i - 0.13, s=80, color=ORANGE, marker="s", edgecolor=SURFACE,
                  linewidth=2, zorder=4)
        if c["misaligned"]["n_partial"]:
            b.scatter(c["aligned"]["mean_beat_nec"], i + 0.13, s=80, facecolor=SURFACE, edgecolor=BLUE, linewidth=2, zorder=5)
            b.scatter(c["aligned"]["mean_beat_suf"], i - 0.13, s=80, facecolor=SURFACE, marker="s", edgecolor=ORANGE,
                      linewidth=2, zorder=5)
        txt = f"n = {c['all']['n_partial']} partial"
        if c["misaligned"]["n_partial"]:
            txt += f"\n({c['aligned']['n_partial']} aligned, {c['misaligned']['n_partial']} misaligned)"
        b.text(1.04, i, txt, va="center", fontsize=8.5, color=INK2)
    b.axvline(0.5, color=MUTED, linewidth=1)
    b.text(0.505, 5.45, "chance (0.5)", ha="left", fontsize=9, color=MUTED)
    b.set_xlim(0.3, 1.02)
    b.set_ylim(-0.6, 5.7)
    b.tick_params(axis="y", left=False)
    b.set_xlabel("Mean beat fraction vs same-size alternative sets")
    b.set_title("B. Partial citations vs alternatives (C1 necessity, C2 sufficiency)", loc="left", fontsize=11)
    b.legend(handles=[Line2D([], [], marker="o", color="w", markerfacecolor=BLUE, markersize=9, label="necessity (all)"),
                      Line2D([], [], marker="s", color="w", markerfacecolor=ORANGE, markersize=9, label="sufficiency (all)"),
                      Line2D([], [], marker="o", color="w", markerfacecolor=SURFACE, markeredgecolor=INK2,
                             markeredgewidth=2, markersize=9, label="aligned orderings only (post hoc)")],
             loc="upper center", bbox_to_anchor=(0.45, -0.14), ncol=3, fontsize=9.5)
    fig.suptitle("Explanation consistency: self-reported citations mostly name records that drive P(d*)",
                 x=0.02, ha="left", fontsize=13, fontweight="bold", y=1.04)
    save(fig, "fig7_citations.png")


if __name__ == "__main__":
    fig1(); fig2(); fig3(); fig4(); fig5(); fig6(); fig7()
