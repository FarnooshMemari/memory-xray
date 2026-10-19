#!/usr/bin/env python3
"""Derive every number used in the Results and Discussion report and figures.

Reads results/reanalysis.json (from independent_reanalysis.py) and writes
results/report_numbers.json. Pre-registered quantities and post hoc
(exploratory) quantities are kept in separate keys.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from independent_reanalysis import P, consistency  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
R = json.loads((ROOT / "results" / "reanalysis.json").read_text())
S = R["scenarios"]
L = ("Positive", "Neutral", "Negative")
# Rubric-ideal Shapley from scenarios/VALIDATION_REPORT.md (offline, pre-run)
RUBRIC_IDEAL = {
    "macro_a": {"E1": 0.4167, "E2": 0.4167, "E3": -0.25, "E4": 0.4167},
    "macro_b": {"E1": 0.4167, "E2": 0.4167, "E3": -0.25, "E4": 0.4167},
    "macro_c": {"E1": -0.25, "E2": 0.4167, "E3": 0.4167, "E4": 0.4167},
}
_LIST_ONLY = re.compile(r"\s*[\[\{]?\s*(\"?R\d\"?\s*(,\s*)?|\[R\d\]\s*,?\s*)*[\]\}]?\s*")


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def spread(xs):
    return {"mean": mean(xs), "min": min(xs), "max": max(xs), "per_ordering": xs}


def lenient(raw, shown, id_map):
    """POST HOC exploratory recovery: a final line containing only record IDs and list punctuation."""
    last = raw.split("\n")[-1]
    if len(raw) >= 40 or not _LIST_ONLY.fullmatch(last):
        return None
    ids = list(dict.fromkeys(re.findall(r"R\d", last)))
    if any(i not in shown for i in ids):
        return None
    return sorted(id_map[i] for i in ids)


def cit_summary(rows):
    part = [r for r in rows if r["c"]["category"] == "partial"]
    return {"n_analyzable": len(rows), "n_partial": len(part),
            "categories": dict(Counter(r["c"]["category"] for r in rows)),
            "mean_beat_nec": mean(r["c"]["beat_nec"] for r in part),
            "mean_beat_suf": mean(r["c"]["beat_suf"] for r in part),
            "share_beat_nec_gt_half": mean(float(r["c"]["beat_nec"] > 0.5) for r in part) if part else None,
            "share_beat_suf_gt_half": mean(float(r["c"]["beat_suf"] > 0.5) for r in part) if part else None,
            "mean_topk": mean(r["c"]["topk"] for r in part)}


out = {"pre_registered": {}, "post_hoc": {}, "run_id": R["run_id"]}
cits_all, raw_unparseable = [], []
for sid, s in S.items():
    sc = json.loads((ROOT / "scenarios" / f"{sid}.json").read_text())
    po = s["per_ordering"]
    entry = {
        "kind": s["kind"], "structure": s["structure"], "d_star": s["d_star"], "reference": s["designed_full"],
        "mean_full_dist": s["mean_full_dist"],
        "full_dist_per_ordering": [o["full_dist"] for o in po],
        "full_argmax_per_ordering": [o["full_argmax"] for o in po],
        "v_full": spread([o["v_full"] for o in po]), "v_empty": spread([o["v_empty"] for o in po]),
        "total_effect": spread([o["total"] for o in po]),
        "shapley": {p: spread([o["phi"][p] for o in po]) for p in P},
        "loo": {p: spread([o["loo"][p] for o in po]) for p in P},
        "designed_agreement_per_ordering": [o["designed_agreement"] for o in po],
        "checks": s["checks"], "infra": {k: v for k, v in s["infra"].items()},
        "flags": s["saved_flags"],
        "accuracy_per_ordering": sum(o["full_argmax"] == s["designed_full"] for o in po),
        "misaligned_orderings": [o["ordering"] for o in po if o["full_argmax"] != s["d_star"]],
    }
    if s["flips"]:
        entry["flips"] = [{k: f[k] for k in ("ordering", "orig_argmax", "argmax", "p_dstar_orig", "p_dstar_flip",
                                            "delta_p_dstar", "tv_distance", "moved_away", "orig_dist", "dist")}
                          for f in s["flips"]]
        entry["flip_summary"] = {
            "label_changed": sum(f["argmax"] != f["orig_argmax"] for f in s["flips"]),
            "moved_away_from_d_star": sum(f["moved_away"] for f in s["flips"]),
            "p_dstar_decreased": sum(f["delta_p_dstar"] < 0 for f in s["flips"]),
            "p_neutral_increased": sum(f["dist"]["Neutral"] > f["orig_dist"]["Neutral"] for f in s["flips"]),
            "delta_p_dstar": spread([f["delta_p_dstar"] for f in s["flips"]]),
            "pre_registered_C4_all_orderings": all(f["moved_away"] for f in s["flips"]),
        }
        entry["rubric_ideal_shapley"] = RUBRIC_IDEAL[sid]
    # citations
    rows = []
    for r in s["citations"]:
        rr = {"sid": sid, "ordering": r["ordering"], "kind": r["kind"], "seed": r["seed"], "status": r["status"],
              "cited": r["cited"], "aligned": r["aligned"], "own_argmax": r["own_full_argmax"], "raw": r["raw"]}
        if "consistency" in r:
            rr["c"] = r["consistency"]
        rows.append(rr)
        cits_all.append(rr)
    samp = [r for r in rows if r["kind"] == "sampled"]
    an = [r for r in samp if "c" in r]
    faithful = sc["designed"].get("faithful_citations") or ([sc["designed"]["faithful_citation"]]
                                                           if "faithful_citation" in sc.get("designed", {}) else [])
    fk = {"+".join(sorted(x)) for x in faithful}
    entry["citations"] = {
        "sampled_status": dict(Counter(r["status"] for r in samp)),
        "greedy_status": dict(Counter(r["status"] for r in rows if r["kind"] == "greedy")),
        "sampled_sets": dict(Counter("+".join(r["cited"]) or "none" for r in an)),
        "all": cit_summary(an),
        "aligned": cit_summary([r for r in an if r["aligned"]]),
        "misaligned": cit_summary([r for r in an if not r["aligned"]]),
        "greedy": [{"ordering": r["ordering"], "aligned": r["aligned"], "cited": "+".join(r["cited"]) or "none",
                    "category": r["c"]["category"], "beat_nec": r["c"]["beat_nec"], "beat_suf": r["c"]["beat_suf"],
                    "topk": r["c"]["topk"], "necessity": r["c"]["necessity"], "sufficiency": r["c"]["sufficiency"]}
                   for r in rows if r["kind"] == "greedy"],
        "faithful_sets": sorted(fk) if fk else None,
        "faithful_match_sampled": (sum(("+".join(r["cited"])) in fk for r in an), len(an)) if fk else None,
        "faithful_match_greedy": sum(("+".join(r["cited"])) in fk for r in rows if r["kind"] == "greedy") if fk else None,
    }
    for role in ("weak", "distractors"):
        recs = set(sc.get("designed", {}).get(role, []))
        if recs and s["kind"] == "synthetic_control":
            entry["citations"][f"cites_{role}_sampled"] = (sum(bool(recs & set(r["cited"])) for r in an), len(an))
    out["pre_registered"][sid] = entry
    # post hoc lenient recovery of malformed citation lists
    rec = []
    raw_rows = {(x["ordering"], x["kind"], x["seed"]): x for x in
                (json.loads(l) for l in (ROOT / "runs" / R["run_id"] / sid / "citations.jsonl").read_text().splitlines())}
    for r in s["citations"]:
        if r["status"] == "unparseable":
            src = raw_rows[(r["ordering"], r["kind"], r["seed"])]
            assert src["raw"] == r["raw"]
            canon = lenient(r["raw"], src["shown_ids"], src["id_to_canonical"])
            v = {frozenset(k.split("+")) if k != "none" else frozenset(): val
                 for k, val in s["per_ordering"][r["ordering"]]["v"].items()}
            item = {"sid": sid, "ordering": r["ordering"], "seed": r["seed"], "raw": r["raw"], "recovered": canon}
            if canon is not None:
                item["c"] = consistency(v, s["per_ordering"][r["ordering"]]["phi"], canon)
                item["aligned"] = r["aligned"]
            rec.append(item)
    out["post_hoc"].setdefault("unparseable", []).extend(rec)

# pooled citation numbers
samp = [r for r in cits_all if r["kind"] == "sampled"]
greedy = [r for r in cits_all if r["kind"] == "greedy"]
an = [r for r in samp if "c" in r]
out["pre_registered"]["_pooled_citations"] = {
    "sampled_total": len(samp), "sampled_status": dict(Counter(r["status"] for r in samp)),
    "greedy_total": len(greedy), "greedy_status": dict(Counter(r["status"] for r in greedy)),
    "all": cit_summary(an),
}
out["post_hoc"]["aligned_only_pooled"] = cit_summary([r for r in an if r["aligned"]])
out["post_hoc"]["misaligned_only_pooled"] = cit_summary([r for r in an if not r["aligned"]])
unp = out["post_hoc"]["unparseable"]
recovered = [u for u in unp if u["recovered"] is not None]
truncated_with_ids = [u for u in unp if u["recovered"] is None and re.search(r"\bR\d\b", u["raw"])]
no_ids = [u for u in unp if u["recovered"] is None and not re.search(r"\bR\d\b", u["raw"])]
out["post_hoc"]["unparseable_categories"] = {
    "malformed_but_complete_list": len(recovered), "prose_with_ids_truncated": len(truncated_with_ids),
    "no_record_ids": len(no_ids)}
for u in unp:
    u["category"] = ("malformed_but_complete_list" if u["recovered"] is not None else
                     "prose_with_ids_truncated" if re.search(r"\bR\d\b", u["raw"]) else "no_record_ids")
    u["n_chars"] = len(u["raw"])
with_rec = an + [{"c": u["c"], "aligned": u["aligned"]} for u in recovered]
out["post_hoc"]["pooled_with_recovered_lists"] = cit_summary(with_rec)


# POST HOC sensitivity (issue 5): rescore misaligned citations against the model's OWN per-ordering
# full-set argmax instead of the injected d*. Uses saved cell probabilities only; no model calls.
def own_shapley(v):
    from itertools import permutations
    from math import factorial
    phi = {p: 0.0 for p in P}
    for perm in permutations(P):
        cur = frozenset()
        for p in perm:
            phi[p] += v[cur | {p}] - v[cur]
            cur = cur | {p}
    return {p: x / factorial(len(P)) for p, x in phi.items()}


own = []
for sid, s in S.items():
    cells = [json.loads(l) for l in (ROOT / "runs" / R["run_id"] / sid / "cells.jsonl").read_text().splitlines()]
    for o in s["per_ordering"]:
        if o["full_argmax"] == s["d_star"]:
            continue
        lab = o["full_argmax"]
        v = {frozenset(c["subset_members"]): c["score"]["p_norm"][lab] for c in cells if c["ordering"] == o["ordering"]}
        phi = own_shapley(v)
        for r in s["citations"]:
            if r["ordering"] == o["ordering"] and "consistency" in r:
                c = consistency(v, phi, r["cited"])
                own.append({"sid": sid, "ordering": o["ordering"], "kind": r["kind"], "cited": "+".join(r["cited"]),
                            "own_decision": lab, "injected": s["d_star"], "category": c["category"],
                            "beat_nec_own": c["beat_nec"], "beat_suf_own": c["beat_suf"],
                            "beat_nec_injected": r["consistency"]["beat_nec"],
                            "beat_suf_injected": r["consistency"]["beat_suf"],
                            "phi_own": phi})
own_part = [x for x in own if x["category"] == "partial"]
out["post_hoc"]["own_decision_rescoring"] = {
    "note": "Exploratory. Citations were elicited to justify the injected d*, so scoring them against the model's own "
            "decision tests a question the model was not asked; reported only to show how far conclusions depend on it.",
    "rows": own,
    "n_partial": len(own_part),
    "mean_beat_nec_own": mean(x["beat_nec_own"] for x in own_part),
    "mean_beat_suf_own": mean(x["beat_suf_own"] for x in own_part),
    "mean_beat_nec_injected": mean(x["beat_nec_injected"] for x in own_part),
    "mean_beat_suf_injected": mean(x["beat_suf_injected"] for x in own_part),
}
(ROOT / "results" / "report_numbers.json").write_text(json.dumps(out, indent=1))
print("written results/report_numbers.json")
print("unparseable categories:", out["post_hoc"]["unparseable_categories"])
print("pooled (pre-registered):", out["pre_registered"]["_pooled_citations"]["all"])
print("aligned only:", out["post_hoc"]["aligned_only_pooled"])
print("misaligned only:", out["post_hoc"]["misaligned_only_pooled"])
print("with recovered lists:", out["post_hoc"]["pooled_with_recovered_lists"])
for sid in ("macro_a", "macro_b", "macro_c"):
    print(sid, out["pre_registered"][sid]["flip_summary"])
