"""Markdown report for a feasibility run."""
from __future__ import annotations

from .design import CANONICAL


def _f(x, nd=3):
    return "n/a" if x is None else f"{x:.{nd}f}"


def _cell(x):
    """Format a table cell: readable lists/dicts, pipes escaped."""
    if isinstance(x, list) and x and all(isinstance(i, dict) for i in x):
        x = "; ".join(", ".join(f"{k}={v}" for k, v in d.items()) for d in x)
    elif isinstance(x, list):
        x = ", ".join(str(i) for i in x)
    return str(x).replace("|", "\\|")


def _rng(s, nd=3):
    if s is None:
        return "n/a"
    return f"{s['mean']:.{nd}f} [{s['min']:.{nd}f}, {s['max']:.{nd}f}]"


def render_report(manifest, infra, behavioral, flags, analysis, title="Feasibility test"):
    mock = manifest["scorer"].get("backend") == "MOCK"
    infra_ok = all(c["passed"] for c in infra)
    beh_ok = all(c["passed"] for c in behavioral)
    lines = []
    if mock:
        lines += ["> **MOCK RUN.** Probabilities come from a hand-written rule, not a language "
                  "model. This only exercises the pipeline. Do not report these numbers.", ""]
    lines += [
        f"# {title}: {analysis['scenario_id']}",
        "",
        f"- Run ID: `{manifest['run_id']}`",
        f"- Model: `{manifest['scorer'].get('model_name')}` on {manifest['scorer'].get('device_name')}",
        f"- Commit: `{manifest['scorer'].get('commit_hash')}` "
        f"(source: {manifest['scorer'].get('revision_source')}, verified: {manifest['scorer'].get('revision_verified')})",
        f"- Precision: {manifest['scorer'].get('dtype')}; logits {manifest['scorer'].get('logits_dtype')}",
        f"- Design fingerprint: `{manifest['design_fingerprint'][:16]}...`",
        f"- Scored cells: {manifest['n_cells']} (forward passes: {manifest['n_forward_passes']})",
        "",
        f"**Infrastructure checks: {'PASS' if infra_ok else 'FAIL'}**  ",
        ("**Behavioral recovery (validation check, not a hypothesis test): "
         + ("PASS" if beh_ok else "FAIL") + "**") if behavioral else
        "**Behavioral recovery: n/a (realistic scenario; descriptive analysis only)**",
        "",
        "## Infrastructure checks",
        "",
        "| ID | Check | Result | Detail |",
        "|---|---|---|---|",
    ]
    for c in infra:
        lines.append(f"| {c['id']} | {_cell(c['name'])} | {'pass' if c['passed'] else '**FAIL**'} | {_cell(c['detail'])} |")
    if behavioral:
        lines += ["", "## Behavioral recovery checks", "", "| ID | Check | Result | Detail |", "|---|---|---|---|"]
    for c in behavioral:
        lines.append(f"| {c['id']} | {_cell(c['name'])} | {'pass' if c['passed'] else '**FAIL**'} | {_cell(c['detail'])} |")
    if flags:
        lines += ["", "Flags (descriptive):"] + [f"- {f}" for f in flags]

    lines += [
        "",
        "## Decision and baseline",
        "",
        f"- d* (argmax of ordering-averaged full-evidence distribution): **{analysis['d_star']}**; "
        f"designed answer: {analysis['designed_full_answer']}",
        f"- Full-set argmax per ordering: {analysis['full_argmax_per_ordering']}",
        f"- v(full) = P(d* | all records): {_rng(analysis['v_full_spread'])}",
        f"- v(empty) = P(d* | no records): {_rng(analysis['v_empty_spread'])}",
        "",
        "Values are mean [min, max] across the 3 fixed orderings: a description of ordering "
        "sensitivity, not a confidence interval.",
        "",
        "## Behavioral attribution",
        "",
        "Shapley values and leave-one-out effects on P(d*), in probability units. These "
        "attribute the model's output to the supplied records; they are not evidence about "
        "internal reasoning.",
        "",
        "| Record | Shapley mean [min, max] | Leave-one-out mean [min, max] |",
        "|---|---|---|",
    ]
    for p in CANONICAL:
        lines.append(f"| {p} | {_rng(analysis['shapley_spread'][p])} | {_rng(analysis['loo_spread'][p])} |")
    sums = [o["shapley_sum"] for o in analysis["per_ordering"]]
    lines += ["", f"Shapley sums per ordering (should equal v(full) - v(empty)): "
              + ", ".join(f"{s:.4f}" for s in sums), ""]

    lines += ["## Subset lattice", "", "| Subset | Designed | P(d*) per ordering | Argmax per ordering |",
              "|---|---|---|---|"]
    for r in analysis["lattice"]:
        lines.append(f"| {r['subset']} | {r['designed']} | "
                     + ", ".join(f"{x:.3f}" for x in r["p_d_star"]) + " | "
                     + ", ".join(r["argmax"]) + " |")

    lines += ["", "## Reference: how candidate citation sets would score", "",
              "Not model citations (citation sampling is not part of this test). This shows the "
              "metric on this lattice. Empty and all-four sets are separate categories with no "
              "beat fractions.", "",
              "| Cited | Category | Necessity | Sufficiency | Beat (necessity) | Beat (sufficiency) |",
              "|---|---|---|---|---|---|"]
    shown = {"none", "E1+E2+E3+E4"} | {"+".join([p]) for p in CANONICAL}
    for r in analysis["reference_citations"]:
        if r["cited"] in shown:
            lines.append(f"| {r['cited']} | {r['category']} | {_rng(r['necessity'])} | "
                         f"{_rng(r['sufficiency'])} | {_rng(r['beat_necessity'], 2)} | "
                         f"{_rng(r['beat_sufficiency'], 2)} |")
    lines += ["", "All 16 rows are in `analysis.json`."]
    return "\n".join(lines) + "\n"
