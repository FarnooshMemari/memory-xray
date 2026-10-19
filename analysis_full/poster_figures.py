#!/usr/bin/env python3
"""Poster figures: simplified versions of the key results, drawn at print size with large type.

Each figure is designed to be printed at the width given in poster_materials/FIGURE_CAPTIONS.md (about
11 in for a 36 x 24 in poster), where the smallest text is >= 16 pt. Vector PDF/SVG scale to larger posters.

Reads only saved results (results/*.json, results/post_hoc/, the saved S-conflict cells); no model, no GPU.
Output: poster_materials/figures/<name>.{png,pdf,svg} (300 dpi PNG; text kept editable in SVG/PDF).
Same palette as analysis_full/make_figures.py (validated dataviz reference palette).
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_figures as mf  # noqa: E402  (shared palette and style; draws nothing on import)

plt = mf.plt
from matplotlib.lines import Line2D  # noqa: E402

ROOT = mf.ROOT
OUT = ROOT / "poster_materials" / "figures"
PRE = mf.PRE
FORMATS = ("png", "pdf", "svg")
METADATA = {"png": None, "pdf": {"CreationDate": None}, "svg": {"Date": None}}
BASE = 18
plt.rcParams.update({"font.size": BASE, "axes.titlesize": BASE + 2, "axes.labelsize": BASE, "xtick.labelsize": BASE - 1,
                     "ytick.labelsize": BASE - 1, "legend.fontsize": BASE - 2, "svg.fonttype": "none", "pdf.fonttype": 42,
                     "svg.hashsalt": "memory-xray-poster"})


def save(fig, stem):
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in FORMATS:
        fig.savefig(OUT / f"{stem}.{ext}", dpi=300, bbox_inches="tight", pad_inches=0.2, metadata=METADATA[ext])
    plt.close(fig)
    print("wrote", OUT / f"{stem}.{{png,pdf,svg}}")


# ---------- P1: workflow (copied from the publication export; regenerate with export_figures.py) ----------
def p1_workflow():
    src = ROOT / "results" / "figures" / "publication"
    for ext in FORMATS:
        shutil.copyfile(src / f"fig0_workflow.{ext}", OUT / f"poster_fig1_workflow.{ext}")
    print("copied", OUT / "poster_fig1_workflow.{png,pdf,svg}")


# ---------- P1b: workflow, vertical (fits one poster column) ----------
def p1b_workflow_vertical():
    from matplotlib.patches import FancyBboxPatch
    steps = [
        ("1", "Scenario", "A question + 4 evidence records (6 scenarios:\n3 designed controls, 3 realistic)"),
        ("2", "Remove evidence", "Every combination of the 4 records (16)\n× 3 fixed orders = 48 prompts"),
        ("3", "Score the model", "Probability of Positive / Neutral / Negative\nfrom Phi-3-mini (no sampling)"),
        ("4", "Attribute", "Shapley value and leave-one-out effect\nof each record on the answer"),
        ("5", "Ask for citations", "\u201cWhich records did your answer rely on?\u201d\n13 replies per scenario"),
        ("6", "Compare", "Do the cited records beat same-size\nalternative sets? (chance = 0.5)"),
    ]
    W, H = 12.3, 8.7
    fig, ax = plt.subplots(figsize=(W, H))
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")
    x0, bw, bh, gap, top = 0.85, 11.35, 0.92, 0.3, 8.6
    ys = []
    for i, (num, title, body) in enumerate(steps):
        y = top - bh - i * (bh + gap)
        ys.append(y)
        edge = mf.ORANGE if num in ("5", "6") else mf.BLUE
        ax.add_patch(FancyBboxPatch((x0, y), bw, bh, boxstyle="round,pad=0.02,rounding_size=0.1",
                                    facecolor="white", edgecolor=edge, linewidth=2.2))
        ax.add_patch(FancyBboxPatch((x0 + 0.2, y + bh / 2 - 0.24), 0.48, 0.48, boxstyle="circle,pad=0.0",
                                    facecolor=edge, edgecolor=edge))
        ax.text(x0 + 0.44, y + bh / 2, num, ha="center", va="center", color="white", fontsize=17, fontweight="bold")
        ax.text(x0 + 0.85, y + bh / 2, title, ha="left", va="center", color=mf.INK, fontsize=17, fontweight="bold")
        ax.text(x0 + 4.1, y + bh / 2, body, ha="left", va="center", color=mf.INK2, fontsize=16, linespacing=1.3)
        if i < len(steps) - 1:
            ax.annotate("", xy=(x0 + 0.44, y - gap + 0.02), xytext=(x0 + 0.44, y - 0.02),
                        arrowprops=dict(arrowstyle="-|>", color=mf.INK2, linewidth=1.6, mutation_scale=16))
    for (lo, hi, color, label) in ((ys[3], ys[0] + bh, mf.BLUE, "What the model does"),
                                   (ys[5], ys[4] + bh, mf.ORANGE, "What it says")):
        ax.plot([0.5, 0.5], [lo + 0.05, hi - 0.05], color=color, linewidth=3, solid_capstyle="round")
        ax.text(0.28, (lo + hi) / 2, label, rotation=90, ha="center", va="center", color=color, fontsize=15,
                fontweight="bold")
    bands = [("Validation", "infrastructure checks · designed controls · independent re-analysis"),
             ("Post hoc", "content-only citer from the design or rubric; never sees the model")]
    for j, (head, text) in enumerate(bands):
        by = ys[-1] - 0.42 - 0.62 * (j + 1) + 0.1
        ax.add_patch(FancyBboxPatch((x0, by), bw, 0.5, boxstyle="round,pad=0.02,rounding_size=0.08",
                                    facecolor=mf.SURFACE, edgecolor=mf.AXIS, linewidth=1.2))
        ax.text(x0 + 0.2, by + 0.25, head, ha="left", va="center", color=mf.INK, fontsize=16, fontweight="bold")
        ax.text(x0 + 2.05, by + 0.25, text, ha="left", va="center", color=mf.INK2, fontsize=15)
    save(fig, "poster_fig1b_workflow_vertical")


# ---------- P2: redundancy (Shapley vs leave-one-out) ----------
def p2_redundancy():
    rows = [("s_redundant", "E1", "Official report A"), ("s_redundant", "E3", "Official report B"),
            ("macro_c", "E2", "Jobs weakening"), ("macro_c", "E3", "Credit tightening"), ("macro_c", "E4", "Earnings cut")]
    fig, ax = plt.subplots(figsize=(11, 6.6))
    mf.style(ax, "x")
    ys = [5.6, 4.6, 2.2, 1.2, 0.2]
    for y, (sid, e, label) in zip(ys, rows):
        sh, lo = PRE[sid]["shapley"][e], PRE[sid]["loo"][e]
        ax.barh(y + 0.19, sh["mean"], height=0.36, color=mf.BLUE, zorder=3)
        ax.barh(y - 0.19, lo["mean"], height=0.36, color=mf.ORANGE, zorder=3)
        ax.plot([sh["min"], sh["max"]], [y + 0.19] * 2, color=mf.INK, linewidth=2, zorder=4)
        ax.plot([lo["min"], lo["max"]], [y - 0.19] * 2, color=mf.INK, linewidth=2, zorder=4)
        fmt = lambda v: "≈ 0" if abs(v) < 0.01 else f"{v:.2f}"  # noqa: E731
        ax.text(max(sh["max"], 0) + 0.015, y + 0.19, fmt(sh["mean"]), va="center", fontsize=BASE - 2, color=mf.INK)
        ax.text(max(lo["max"], 0) + 0.015, y - 0.19, fmt(lo["mean"]), va="center", fontsize=BASE - 2, color=mf.INK)
        ax.text(-0.03, y, label, ha="right", va="center", fontsize=BASE - 1, color=mf.INK)
    ax.text(-0.03, 6.45, "Designed control: two reports\nof the same rate hike", ha="right", va="center",
            fontsize=BASE - 1, color=mf.INK2, fontweight="bold")
    ax.text(-0.03, 3.05, "Realistic: three records that\neach point to Negative", ha="right", va="center",
            fontsize=BASE - 1, color=mf.INK2, fontweight="bold")
    ax.axvline(0, color=mf.AXIS, linewidth=1.2)
    ax.set_yticks([])
    ax.set_xlim(-0.02, 0.6)
    ax.set_ylim(-0.4, 6.9)
    ax.set_xlabel("Effect on the probability of the model's answer")
    ax.legend(handles=[Line2D([], [], color=mf.BLUE, linewidth=10, label="Shapley value (all 16 subsets)"),
                       Line2D([], [], color=mf.ORANGE, linewidth=10, label="Leave-one-out (remove one record)"),
                       Line2D([], [], color=mf.INK, linewidth=2, label="range across the 3 orderings")],
              loc="upper center", bbox_to_anchor=(0.42, -0.16), ncol=2, handlelength=1.2)
    save(fig, "poster_fig2_redundancy")


# ---------- P3: the later record decides the conflict ----------
def p3_order():
    cells = [json.loads(line) for line in
             (ROOT / "runs" / mf.RE["run_id"] / "s_conflict" / "cells.jsonl").read_text().splitlines()]
    subsets = ("E1+E2", "E1+E2+E3", "E1+E2+E4", "E1+E2+E3+E4")
    fig, ax = plt.subplots(figsize=(11, 6.4))
    mf.style(ax, "y")
    xs_center = {0: 0, 1: 1.25, 2: 2.75}
    offsets = (-0.3, -0.1, 0.1, 0.3)
    for k in range(3):
        for off, subset in zip(offsets, subsets):
            c = next(c for c in cells if c["ordering"] == k and c["subset"] == subset)
            p, lab = c["score"]["p_norm"]["Positive"], c["score"]["argmax"]
            ax.scatter(xs_center[k] + off, p, s=260, color=mf.LABEL_COLOR[lab], edgecolor=mf.SURFACE, linewidth=2.5, zorder=4)
    ax.axvspan(2.25, 3.25, color=mf.GRID, alpha=0.45, zorder=0, linewidth=0)
    ax.set_xticks([0, 1.25, 2.75])
    ax.set_xticklabels(["Ordering 0\nrate cut first,\ninflation later", "Ordering 1\nrate cut first,\ninflation later",
                        "Ordering 2\ninflation first,\nrate cut later"], fontsize=BASE - 2)
    ax.set_xlim(-0.6, 3.35)
    ax.set_ylim(0, 1)
    ax.set_ylabel("P(Positive)")
    ax.set_title("The instruction says the rate cut takes precedence: Positive in all 12", loc="left",
                 fontsize=BASE - 1, fontweight="normal", color=mf.INK2, pad=14)
    ax.text(0.62, 0.12, "Negative in 8/8: inflation (later) wins", ha="center", fontsize=BASE - 2, color=mf.NEG,
            fontweight="bold")
    ax.text(2.75, 0.86, "Positive in 4/4:\nrate cut (later) wins", ha="center", fontsize=BASE - 2, color=mf.POS,
            fontweight="bold")
    ax.legend(handles=[Line2D([], [], marker="o", color="w", markerfacecolor=mf.POS, markersize=15, label="model answers Positive"),
                       Line2D([], [], marker="o", color="w", markerfacecolor=mf.NEG, markersize=15, label="model answers Negative")],
              loc="upper center", bbox_to_anchor=(0.5, -0.27), ncol=2)
    save(fig, "poster_fig3_order_decides_conflict")


# ---------- P4: citation consistency vs the content-only citer (post hoc) ----------
def p4_citations():
    B = json.loads((ROOT / "results" / "post_hoc" / "content_only_baseline.json").read_text())
    rows = list(mf.ORDER) + ["pooled"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 7), sharey=True)
    fig.subplots_adjust(wspace=0.08)
    for ax, (key, title) in zip(axes, (("mean_beat_nec", "Necessity"), ("mean_beat_suf", "Sufficiency"))):
        mf.style(ax, "x")
        for i, sid in enumerate(reversed(rows)):
            if sid == "pooled":
                m = B["pooled"]["model_pre_registered_40_partial_sampled"][key]
                c = B["pooled"]["content_only_18_ordering_citations"][key]
                ax.axhspan(i - 0.45, i + 0.45, color=mf.GRID, alpha=0.5, zorder=0, linewidth=0)
            else:
                m = B["scenarios"][sid]["model_pre_registered"][key]
                c = B["scenarios"][sid]["content_only"][key]
            ax.scatter(m, i + 0.16, s=230, color=mf.BLUE, edgecolor=mf.SURFACE, linewidth=2.5, zorder=4)
            ax.scatter(c, i - 0.16, s=210, color=mf.ORANGE, marker="s", edgecolor=mf.SURFACE, linewidth=2.5, zorder=4)
        ax.axvline(0.5, color=mf.MUTED, linewidth=1.5)
        ax.text(0.51, len(rows) - 0.45, "chance", fontsize=BASE - 2, color=mf.MUTED)
        ax.set_xlim(0.4, 1.05)
        ax.set_xticks([0.5, 0.75, 1.0])
        ax.set_ylim(-0.6, len(rows) - 0.2)
        ax.set_title(title, loc="left")
    axes[0].set_yticks(range(len(rows)))
    axes[0].set_yticklabels([("All (pooled)" if s == "pooled" else mf.NAMES[s]) for s in reversed(rows)])
    axes[0].get_yticklabels()[0].set_fontweight("bold")
    fig.supxlabel("Beat fraction: share of same-size alternative sets the citation beats", fontsize=BASE - 1, y=0.0)
    fig.legend(handles=[Line2D([], [], marker="o", color="w", markerfacecolor=mf.BLUE, markersize=16,
                               label="Model's own citations (pre-registered)"),
                        Line2D([], [], marker="s", color="w", markerfacecolor=mf.ORANGE, markersize=15,
                               label="Citer that never looks at the model (post hoc)")],
               loc="upper center", bbox_to_anchor=(0.5, -0.04), ncol=1)
    save(fig, "poster_fig4_citations_vs_content_only")


# ---------- P5: flips move probabilities more than labels ----------
def p5_flips():
    fig, ax = plt.subplots(figsize=(11, 6))
    mf.style(ax, "x")
    y = 8
    labels = []
    for sid in ("macro_a", "macro_b", "macro_c"):
        for f in PRE[sid]["flips"]:
            changed = f["argmax"] != f["orig_argmax"]
            col = mf.BLUE if changed else mf.MUTED
            ax.annotate("", xy=(f["p_dstar_flip"], y), xytext=(f["p_dstar_orig"], y),
                        arrowprops=dict(arrowstyle="-|>", color=col, linewidth=3, mutation_scale=22), zorder=3)
            ax.scatter(f["p_dstar_orig"], y, s=120, color=mf.INK, zorder=4)
            ax.text(1.02, y, f"{f['orig_argmax']} → {f['argmax']}", va="center", fontsize=BASE - 1,
                    color=mf.INK if changed else mf.MUTED, fontweight="bold" if changed else "normal")
            labels.append(f"{mf.NAMES[sid]} · ord. {f['ordering']}")
            y -= 1
    ax.set_yticks(range(8, -1, -1))
    ax.set_yticklabels(labels, fontsize=BASE - 1)
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.7, 8.7)
    ax.set_xlabel("Probability of the scenario's decision d*: before (dot) → after one record is reversed (arrow)")
    ax.text(1.02, 9.0, "Label", fontsize=BASE - 1, color=mf.INK2, fontweight="bold")
    flips = [f for sid in ("macro_a", "macro_b", "macro_c") for f in PRE[sid]["flips"]]
    n_changed = sum(f["argmax"] != f["orig_argmax"] for f in flips)
    ax.legend(handles=[Line2D([], [], color=mf.BLUE, linewidth=4, label=f"label changed ({n_changed}/{len(flips)})"),
                       Line2D([], [], color=mf.MUTED, linewidth=4,
                              label=f"label unchanged ({len(flips) - n_changed}/{len(flips)})")],
              loc="upper center", bbox_to_anchor=(0.45, -0.17), ncol=2)
    save(fig, "poster_fig5_flips")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    p1_workflow()
    p1b_workflow_vertical()
    p2_redundancy()
    p3_order()
    p4_citations()
    p5_flips()


if __name__ == "__main__":
    main()
