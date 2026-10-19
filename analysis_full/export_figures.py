#!/usr/bin/env python3
"""Publication and poster exports (added for the public release; see CHANGES.md).

1. Re-renders the seven report figures from analysis_full/make_figures.py, unchanged in content and
   design, as 300-dpi PNG plus vector PDF and SVG.
2. Adds two figures that are not in the original report:
   fig0_workflow      the experiment workflow (diagram; no data)
   fig8_content_only  POST HOC content-only citation baseline vs the model's own citations
                      (reads results/post_hoc/content_only_baseline.json; run content_only_baseline.py first)

Output: results/figures/publication/<name>.{png,pdf,svg}. Reads saved results only; no model, no GPU.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_figures as mf  # noqa: E402  (module import sets the shared style; it draws nothing by itself)

plt = mf.plt
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

ROOT = mf.ROOT
PUB = ROOT / "results" / "figures" / "publication"
FORMATS = ("png", "pdf", "svg")
plt.rcParams.update({"svg.fonttype": "none", "pdf.fonttype": 42,   # keep text editable in vector files
                     "svg.hashsalt": "memory-xray"})               # deterministic SVG ids
METADATA = {"png": None, "pdf": {"CreationDate": None}, "svg": {"Date": None}}   # no timestamps: reproducible bytes


def save(fig, name):
    PUB.mkdir(parents=True, exist_ok=True)
    stem = Path(name).stem
    for ext in FORMATS:
        fig.savefig(PUB / f"{stem}.{ext}", dpi=300, bbox_inches="tight", pad_inches=0.25, metadata=METADATA[ext])
    plt.close(fig)
    print("wrote", PUB / f"{stem}.{{{','.join(FORMATS)}}}")


# ---------- Fig 0: workflow ----------
def fig0():
    steps = [
        ("1", "Scenario", "A question plus four\nevidence records (E1–E4).\n6 scenarios: 3 designed\ncontrols, 3 realistic\nmacro-finance cases."),
        ("2", "Remove evidence", "Show every subset of the\n4 records (16 subsets)\nin 3 fixed orderings:\n48 prompts per scenario."),
        ("3", "Score the model", "Phi-3-mini (pinned).\nRead P(Positive / Neutral /\nNegative) after “Signal:”.\nNo sampling."),
        ("4", "Attribute", "Decision d*. Exact Shapley\nvalues and leave-one-out\neffects of each record\non P(d*)."),
        ("5", "Ask for citations", "“Which records did your\nanswer rely on?”\n10 sampled + 3 greedy\nreplies per scenario."),
        ("6", "Compare", "Do the cited records drive\nP(d*)? Beat fraction vs\nsame-size alternative\nsets (chance = 0.5)."),
    ]
    w, h, gap, x0, y0 = 3.05, 3.15, 0.38, 0.12, 2.45
    width = x0 * 2 + 6 * w + 5 * gap
    fig, ax = plt.subplots(figsize=(width, 6.5))
    ax.set_xlim(0, width)
    ax.set_ylim(0, 6.5)
    ax.axis("off")
    x = x0
    for i, (num, title, body) in enumerate(steps):
        edge = mf.ORANGE if num in ("5", "6") else mf.BLUE
        ax.add_patch(FancyBboxPatch((x, y0), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
                                    facecolor="white", edgecolor=edge, linewidth=2))
        ax.add_patch(FancyBboxPatch((x + 0.18, y0 + h - 0.66), 0.46, 0.46, boxstyle="circle,pad=0.0",
                                    facecolor=edge, edgecolor=edge))
        ax.text(x + 0.41, y0 + h - 0.43, num, ha="center", va="center", color="white", fontsize=14, fontweight="bold")
        ax.text(x + 0.8, y0 + h - 0.43, title, ha="left", va="center", color=mf.INK, fontsize=12.5, fontweight="bold")
        ax.text(x + 0.2, y0 + h - 0.95, body, ha="left", va="top", color=mf.INK2, fontsize=11.5, linespacing=1.4)
        if i < len(steps) - 1:
            ax.annotate("", xy=(x + w + gap - 0.02, y0 + h / 2), xytext=(x + w + 0.02, y0 + h / 2),
                        arrowprops=dict(arrowstyle="-|>", color=mf.INK2, linewidth=1.6, mutation_scale=16))
        x += w + gap
    ax.text(x0, 6.15, "What the model does with the evidence (steps 1–4)", color=mf.BLUE, fontsize=13, fontweight="bold")
    ax.text(x0 + 4 * (w + gap), 6.15, "What the model says it used (steps 5–6)", color=mf.ORANGE, fontsize=13,
            fontweight="bold")
    bands = [
        ("Validation", "Infrastructure checks I1–I9 in every scenario · recovery checks on the 3 designed controls · "
                       "an independent re-implementation reproduces every saved number"),
        ("Post hoc", "Content-only baseline: a citer that never sees the model cites the records that the design or rubric "
                     "marks as supporting the decision; same metrics"),
    ]
    for j, (head, text) in enumerate(bands):
        by = 1.45 - j * 0.9
        ax.add_patch(FancyBboxPatch((x0, by), width - 2 * x0, 0.7, boxstyle="round,pad=0.02,rounding_size=0.1",
                                    facecolor=mf.SURFACE, edgecolor=mf.AXIS, linewidth=1.2))
        ax.text(x0 + 0.25, by + 0.35, head, ha="left", va="center", color=mf.INK, fontsize=12, fontweight="bold")
        ax.text(x0 + 1.85, by + 0.35, text, ha="left", va="center", color=mf.INK2, fontsize=11.5)
    save(fig, "fig0_workflow")


# ---------- Fig 8: content-only baseline (post hoc) ----------
def fig8():
    path = ROOT / "results" / "post_hoc" / "content_only_baseline.json"
    B = json.loads(path.read_text())
    rows = list(mf.ORDER) + ["pooled"]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.6), sharey=True)
    fig.subplots_adjust(wspace=0.06)
    metrics = (("mean_beat_nec", "C1 necessity: mean beat fraction"), ("mean_beat_suf", "C2 sufficiency: mean beat fraction"))
    for ax, (key, title) in zip(axes, metrics):
        mf.style(ax, "x")
        for i, sid in enumerate(reversed(rows)):
            if sid == "pooled":
                m = B["pooled"]["model_pre_registered_40_partial_sampled"][key]
                c = B["pooled"]["content_only_18_ordering_citations"][key]
            else:
                m = B["scenarios"][sid]["model_pre_registered"][key]
                c = B["scenarios"][sid]["content_only"][key]
            ax.scatter(m, i + 0.14, s=90, color=mf.BLUE, edgecolor=mf.SURFACE, linewidth=2, zorder=4)
            ax.scatter(c, i - 0.14, s=90, color=mf.ORANGE, marker="s", edgecolor=mf.SURFACE, linewidth=2, zorder=4)
        ax.axhline(0.5, color=mf.AXIS, linewidth=1)
        ax.axvline(0.5, color=mf.MUTED, linewidth=1)
        ax.text(0.505, len(rows) - 0.35, "chance (0.5)", ha="left", fontsize=9, color=mf.MUTED)
        ax.set_xlim(0.4, 1.04)
        ax.set_ylim(-0.6, len(rows) - 0.2)
        ax.set_title(title, loc="left", fontsize=11.5)
        ax.set_xlabel("Beat fraction vs same-size alternative citation sets")
    axes[0].set_yticks(range(len(rows)))
    axes[0].set_yticklabels([("Pooled" if s == "pooled" else mf.NAMES[s]) for s in reversed(rows)])
    axes[0].get_yticklabels()[0].set_fontweight("bold")
    exc = B["pooled"]["scenario_metric_comparisons"]
    axes[1].annotate(f"only exception: content-only {exc['exceptions'][0]['content_only']:.3f}\nvs model "
                     f"{exc['exceptions'][0]['model']:.3f}", xy=(exc["exceptions"][0]["content_only"], 5 - 0.14),
                     xytext=(0.70, 4.95), va="center", fontsize=9.5, color=mf.INK2,
                     arrowprops=dict(arrowstyle="-", color=mf.MUTED, linewidth=1)) if exc["exceptions"] else None
    fig.legend(handles=[Line2D([], [], marker="o", color="w", markerfacecolor=mf.BLUE, markersize=10,
                               label="Phi-3's own citations (pre-registered; sampled partial citations, n = 5–8 per scenario)"),
                        Line2D([], [], marker="s", color="w", markerfacecolor=mf.ORANGE, markersize=10,
                               label="Content-only citer that never sees the model (post hoc; one fixed set per scenario)")],
               loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=1, fontsize=10)
    fig.suptitle(f"Post hoc: a citer that never looks at the model matches or beats its citations in "
                 f"{exc['content_only_ge_model']} of {exc['of']} scenario × metric comparisons\n",
                 x=0.02, ha="left", fontsize=13, fontweight="bold", y=1.07)
    fig.text(0.02, 0.985, "Necessity and sufficiency shown; the third metric, Shapley top-k agreement, is equal or higher for "
             "the content-only citer in every scenario. Content-only sets come from the design (controls) or rubric (realistic).",
             ha="left", fontsize=9.5, color=mf.INK2)
    save(fig, "fig8_content_only_baseline")


def main():
    mf.save = save                     # the original figure functions call the module-level save()
    for f in (mf.fig1, mf.fig2, mf.fig3, mf.fig4, mf.fig5, mf.fig6, mf.fig7):
        f()
    fig0()
    fig8()


if __name__ == "__main__":
    main()
