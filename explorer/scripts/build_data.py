#!/usr/bin/env python3
"""Build src/data/explorer-data.json from the saved Memory X-Ray v0.2 results (read-only).

  python3 scripts/build_data.py            # from explorer/, reading the repository root (..)

Every number in the explorer comes from this file, and every value in this file is copied from a saved
v0.2 file: nothing is estimated, interpolated or re-run. The only hand-written content is presentational:
short record labels and one-line scenario descriptions (SHORT, BLURB below), which restate the scenario
texts. Source files and their SHA-256 hashes are recorded in meta.sources.

Sources (relative to --repo):
  runs/full_20261017T223452Z/manifest.json                 run metadata
  runs/full_20261017T223452Z/<scenario>/cells.jsonl        label probabilities for all 16 subsets x 3 orderings
  runs/full_20261017T223452Z/<scenario>/analysis.json      Shapley values, leave-one-out, decision d*
  runs/full_20261017T223452Z/<scenario>/checks.json        infrastructure and recovery checks, flags
  runs/full_20261017T223452Z/<scenario>/citations.jsonl    the model's citation replies and their scores
  runs/full_20261017T223452Z/<scenario>/flips.jsonl        counterfactual flips (realistic scenarios)
  scenarios/<scenario>.json                                question, records, design or rubric
  results/report_numbers.json                              pooled pre-registered numbers, post hoc splits
  results/post_hoc/content_only_baseline.json              POST HOC content-only citation baseline
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

RUN = "runs/full_20261017T223452Z"
ORDER = ["s_single", "s_redundant", "s_conflict", "macro_a", "macro_b", "macro_c"]
LABELS = ["Positive", "Neutral", "Negative"]
REC = ["E1", "E2", "E3", "E4"]

NAME = {"s_single": "S-single", "s_redundant": "S-redundant", "s_conflict": "S-conflict",
        "macro_a": "Macro A", "macro_b": "Macro B", "macro_c": "Macro C"}
# Presentational, hand-written: what each scenario is built to test (restates the design / rubric).
BLURB = {
    "s_single": "One record decides the answer; three are noise.",
    "s_redundant": "Two official reports of the same rate hike: either one is enough.",
    "s_conflict": "A rate cut and high inflation conflict; the rule says the rate cut wins.",
    "macro_a": "Three positive signals and one negative one.",
    "macro_b": "Three negative signals and one positive one.",
    "macro_c": "A rate cut against three negative signals.",
}
# Presentational short labels; full texts are shown alongside them.
SHORT = {
    "s_single": {"E1": "National accounts released", "E2": "Rate cut, 50 bp", "E3": "Early market close",
                 "E4": "New communications head"},
    "s_redundant": {"E1": "Press release: rate hike", "E2": "Commentators expect tightening",
                    "E3": "Official gazette: rate hike", "E4": "Statistics office moves"},
    "s_conflict": {"E1": "Rate cut, 25 bp", "E2": "Inflation 5.8% vs 2% target", "E3": "Regulator renames an office",
                   "E4": "Ministry website redesign"},
    "macro_a": {"E1": "Rate cut, 50 bp", "E2": "Core inflation eases to 2.4%", "E3": "Manufacturing PMI 47.6",
                "E4": "Earnings forecasts up 4%"},
    "macro_b": {"E1": "Rate hike, 75 bp", "E2": "Inflation rises to 6.8%", "E3": "Services PMI 55.2",
                "E4": "Earnings forecasts down 6%"},
    "macro_c": {"E1": "Rate cut, 25 bp", "E2": "Unemployment rises to 6.1%", "E3": "Credit spreads widen 180 bp",
                "E4": "Earnings forecasts down 9%"},
}
# Presentational paraphrases of the designed roles in scenarios/*.json (controls only).
ROLE = {
    "s_single": {"E1": "Distractor", "E2": "Decisive: sets the answer", "E3": "Distractor", "E4": "Distractor"},
    "s_redundant": {"E1": "Official report: enough on its own", "E2": "Commentary: the rule says ignore it",
                    "E3": "Official report: enough on its own", "E4": "Distractor"},
    "s_conflict": {"E1": "Rate decision: the rule says it wins", "E2": "Inflation: counts only without a rate decision",
                   "E3": "Distractor", "E4": "Distractor"},
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def jsonl(p: Path):
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def mask_of(members) -> int:
    return sum(1 << REC.index(m) for m in members)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))  # the repository root, above explorer/
    ap.add_argument("--out", default=str(Path(__file__).resolve().parents[1] / "src" / "data" / "explorer-data.json"))
    a = ap.parse_args()
    repo = Path(a.repo)
    sources = []

    def load(rel, kind="json"):
        p = repo / rel
        sources.append({"path": rel, "sha256": sha(p)})
        return json.loads(p.read_text()) if kind == "json" else jsonl(p)

    man = load(f"{RUN}/manifest.json")
    numbers = load("results/report_numbers.json")
    base = load("results/post_hoc/content_only_baseline.json")
    pre, post = numbers["pre_registered"], numbers["post_hoc"]

    scen_out = []
    for sid in ORDER:
        sc = load(f"scenarios/{sid}.json")
        cells = load(f"{RUN}/{sid}/cells.jsonl", "jsonl")
        an = load(f"{RUN}/{sid}/analysis.json")
        ch = load(f"{RUN}/{sid}/checks.json")
        cit = load(f"{RUN}/{sid}/citations.jsonl", "jsonl")
        realistic = sc["kind"] == "realistic"
        flips = load(f"{RUN}/{sid}/flips.jsonl", "jsonl") if realistic else []
        d_star = an["d_star"]
        own = an["full_argmax_per_ordering"]

        orderings = []
        for k in range(3):
            po = an["per_ordering"][k]
            assert po["ordering"] == k
            full = next(c for c in cells if c["ordering"] == k and c["mask"] == 15)
            sub = {}
            for c in (c for c in cells if c["ordering"] == k):
                assert c["mask"] == mask_of(c["subset_members"])
                p = c["score"]["p_norm"]
                sub[str(c["mask"])] = {"p": [p[lab] for lab in LABELS], "argmax": c["score"]["argmax"],
                                       "rule": c["designed_answer"]}
            assert len(sub) == 16
            orderings.append({
                "index": k,
                "order": full["shown_canonical"],               # record order as shown to the model, first to last
                "ids": dict(zip(full["shown_canonical"], full["shown_ids"])),
                "subsets": sub,
                "shapley": {e: po["shapley"][e] for e in REC},
                "loo": {e: po["loo"][e] for e in REC},
                "fullArgmax": own[k],
                "designedAgreement": po["designed_agreement"],
            })

        records = {}
        for e in REC:
            r = {"text": sc["records"][e], "short": SHORT[sid][e]}
            if realistic:
                s = sc["rubric"]["scores"][e]
                r["rubric"] = {"score": s["score"], "component": s["component"], "why": s["why"]}
            else:
                r["role"] = ROLE[sid][e]
            records[e] = r

        rep = pre[sid]
        cites = []
        for c in cit:
            st = c["parse"]["status"]
            con = c.get("consistency") or {}
            cites.append({
                "ordering": c["ordering"], "kind": c["kind"], "seed": c["seed"], "status": st,
                "raw": c["raw"],
                "cited": c["parse"]["canonical"] if st in ("ok", "empty") else None,
                "category": con.get("category") if st in ("ok", "empty") else None,
                "beatNec": con.get("beat_necessity"), "beatSuf": con.get("beat_sufficiency"),
                "topk": con.get("shapley_top_k_agreement"),
                "shownLabel": c["decision_in_context"], "ownAnswer": own[c["ordering"]],
                "aligned": c["decision_in_context"] == own[c["ordering"]],
            })

        out = {
            "id": sid, "name": NAME[sid], "blurb": BLURB[sid],
            "kind": "realistic" if realistic else "control", "structure": sc["structure"],
            "question": sc["question"], "records": records,
            "dStar": d_star, "reference": rep["reference"], "meanFullDist": [an["mean_full_distribution"][lab] for lab in LABELS],
            "orderings": orderings,
            "shapleySummary": rep["shapley"], "looSummary": rep["loo"],
            "checks": {
                "infraPass": all(x["passed"] for x in ch["infrastructure"]),
                "recovery": [{"id": x["id"], "name": x["name"], "passed": x["passed"]} for x in ch["behavioral"]],
                "flags": ch["flags"],
            },
            "citations": cites,
            "citationMetrics": {k: rep["citations"]["all"][k] for k in
                                ("n_analyzable", "n_partial", "mean_beat_nec", "mean_beat_suf", "mean_topk",
                                 "share_beat_nec_gt_half", "share_beat_suf_gt_half")},
            "misalignedOrderings": rep["misaligned_orderings"],
            "contentOnly": {"set": base["scenarios"][sid]["content_only_set"],
                            **{k: base["scenarios"][sid]["content_only"][k] for k in ("mean_beat_nec", "mean_beat_suf", "mean_topk")}},
        }
        if realistic:
            out["rubricIdealShapley"] = rep["rubric_ideal_shapley"]
            out["flip"] = {
                "target": sc["flip"]["target"], "text": sc["flip"]["record"], "why": sc["flip"]["why"],
                "referenceAfter": sc["flip"]["reference_answer"],
                "perOrdering": [{"ordering": f["ordering"], "pAfter": [f["p_norm"][lab] for lab in LABELS],
                                 "argmaxAfter": f["argmax"], "pDStarBefore": f["p_d_star_original"],
                                 "pDStarAfter": f["p_d_star_flipped"]} for f in sorted(flips, key=lambda f: f["ordering"])],
            }
        scen_out.append(out)

    pc = pre["_pooled_citations"]
    pb = base["pooled"]
    hi = tie = 0
    for sid in ORDER:
        for k in ("mean_beat_nec", "mean_beat_suf", "mean_topk"):
            c, m = base["scenarios"][sid]["content_only"][k], base["scenarios"][sid]["model_pre_registered"][k]
            tie += abs(c - m) <= 1e-12
            hi += c > m + 1e-12
    rows = [r for r in post["own_decision_rescoring"]["rows"] if r["category"] == "partial"]
    mean = lambda key: sum(r[key] for r in rows) / len(rows)  # noqa: E731
    data = {
        "meta": {
            "title": "Memory X-Ray v0.2",
            "runId": man["run_id"], "model": man["scorer"]["model_name"], "commit": man["scorer"]["commit_hash"],
            "device": man["scorer"]["device_name"], "elapsedSeconds": man["elapsed_seconds"],
            "precision": man["scorer"]["dtype"], "labels": LABELS, "records": REC,
            "subsetEncoding": "subset key = bitmask over records: E1=1, E2=2, E3=4, E4=8 (0 = no records, 15 = all four)",
            "valueFunction": "v(S) = normalized probability of the scenario decision d* given the records in S",
            "sources": sources,
            "handWritten": "short record labels, role paraphrases and one-line scenario descriptions (presentational only)",
        },
        "pooled": {
            "model": {k: pc["all"][k] for k in ("n_analyzable", "n_partial", "mean_beat_nec", "mean_beat_suf", "mean_topk",
                                                 "share_beat_nec_gt_half", "share_beat_suf_gt_half")},
            "sampledStatus": pc["sampled_status"], "sampledTotal": pc["sampled_total"],
            "greedyStatus": pc["greedy_status"], "greedyTotal": pc["greedy_total"],
            "aligned": {k: post["aligned_only_pooled"][k] for k in ("n_partial", "mean_beat_nec", "mean_beat_suf", "mean_topk")},
            "misaligned": {k: post["misaligned_only_pooled"][k] for k in ("n_partial", "mean_beat_nec", "mean_beat_suf",
                                                                           "mean_topk", "share_beat_nec_gt_half",
                                                                           "share_beat_suf_gt_half")},
            "ownDecisionRescoring": {"n": len(rows), "shown": [mean("beat_nec_injected"), mean("beat_suf_injected")],
                                     "own": [mean("beat_nec_own"), mean("beat_suf_own")]},
            "contentOnly": {k: pb["content_only_18_ordering_citations"][k] for k in ("mean_beat_nec", "mean_beat_suf", "mean_topk")},
            "contentOnlyComparison": {"higher": hi, "tied": tie, "lower": pb["scenario_metric_comparisons"]["of"] - hi - tie,
                                      "of": pb["scenario_metric_comparisons"]["of"],
                                      "exceptions": pb["scenario_metric_comparisons"]["exceptions"]},
            "modelEqualsContentSet": pb["model_citations_equal_to_content_set"],
        },
        "scenarios": scen_out,
    }
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {out} ({out.stat().st_size / 1024:.0f} KB) from {len(sources)} source files")


if __name__ == "__main__":
    main()
