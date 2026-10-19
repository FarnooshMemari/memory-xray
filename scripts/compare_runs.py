#!/usr/bin/env python3
"""Compare a NEW full-experiment run with the saved reference run (no model needed).

Use this after re-running the GPU experiment (notebooks/colab_full_experiment.ipynb) to see how
closely the re-run reproduces the published one.

  python scripts/compare_runs.py outputs/runs/full_<UTC>                 # vs the saved run
  python scripts/compare_runs.py <new run> --reference runs/full_20261017T223452Z

What is compared, per scenario:
  * deterministic part (48 lattice cells): that all 48 cells are present in both runs, d*, the
    full-evidence argmax per ordering, every check outcome (I1-I9, recovery checks), the max |difference|
    in normalized label probabilities over all cells, and the max |difference| in Shapley values;
  * counterfactual flips (realistic scenarios): flipped argmax per ordering and max |difference| in the
    flipped label probabilities;
  * citation stage: parse-status counts and the cited sets of the 3 greedy replies. Sampled replies
    (temperature 1.0) depend on the random-number stream and GPU kernels and are NOT expected to repeat
    exactly, so they are summarized, not required to match.

A re-run on different hardware or library versions should give the same decisions and check outcomes
with small numerical differences; it is not expected to be bit-identical.
Exit code 0 only if, in every scenario, all cells are present, d*, the per-ordering argmaxes, the flip
argmaxes and all check outcomes agree, and the largest probability and Shapley differences are <= --tol
(default 0.01). Otherwise 1, with the reason printed.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REF = ROOT / "runs" / "full_20261017T223452Z"


def _jsonl(p):
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def _checks(d):
    c = json.loads((d / "checks.json").read_text())
    return {x["id"]: x["passed"] for x in c["infrastructure"] + c["behavioral"]}


def _cells(d):
    return {(c["ordering"], c["subset"]): c["score"]["p_norm"] for c in _jsonl(d / "cells.jsonl")}


def _flips(d):
    p = d / "flips.jsonl"
    return {f["ordering"]: f for f in _jsonl(p)} if p.exists() else {}


def compare_scenario(new, ref, tol=0.01):
    an, ar = json.loads((new / "analysis.json").read_text()), json.loads((ref / "analysis.json").read_text())
    cn, cr = _cells(new), _cells(ref)
    common = set(cn) & set(cr)
    dp = max(abs(cn[k][lab] - cr[k][lab]) for k in common for lab in cr[k]) if common else None
    dphi = max(abs(on["shapley"][e] - orr["shapley"][e])
               for on, orr in zip(an["per_ordering"], ar["per_ordering"]) for e in orr["shapley"])
    kn, kr = _checks(new), _checks(ref)
    out = {
        "d_star": (an["d_star"], ar["d_star"]),
        "argmax_per_ordering": (an["full_argmax_per_ordering"], ar["full_argmax_per_ordering"]),
        "checks_differ": sorted(k for k in set(kn) | set(kr) if kn.get(k) != kr.get(k)),
        "cells_compared": len(common),
        "cells_complete": len(common) == len(cr) == len(cn) == 48,
        "max_abs_diff_p_norm": dp,
        "max_abs_diff_shapley": dphi,
    }
    fn, fr = _flips(new), _flips(ref)
    if fr:
        out["flip_argmax"] = ([fn[k]["argmax"] if k in fn else None for k in sorted(fr)], [fr[k]["argmax"] for k in sorted(fr)])
        out["max_abs_diff_flip_p_norm"] = max((abs(fn[k]["p_norm"][lab] - fr[k]["p_norm"][lab])
                                               for k in fr if k in fn for lab in fr[k]["p_norm"]), default=None)
    if (new / "citations.jsonl").exists() and (ref / "citations.jsonl").exists():
        cit_n, cit_r = _jsonl(new / "citations.jsonl"), _jsonl(ref / "citations.jsonl")
        g = lambda cs: [c.get("cited_key") for c in sorted((c for c in cs if c["kind"] == "greedy"),  # noqa: E731
                                                          key=lambda c: c["ordering"])]
        out["greedy_cited"] = (g(cit_n), g(cit_r))
        st = lambda cs: dict(Counter(c["parse"]["status"] for c in cs if c["kind"] != "greedy"))  # noqa: E731
        out["sampled_status"] = (st(cit_n), st(cit_r))
    reasons = []
    if not out["cells_complete"]:
        reasons.append(f"cells present: {len(cn)} new / {len(cr)} reference")
    if out["d_star"][0] != out["d_star"][1]:
        reasons.append("d* differs")
    if out["argmax_per_ordering"][0] != out["argmax_per_ordering"][1]:
        reasons.append("per-ordering argmax differs")
    if out["checks_differ"]:
        reasons.append("check outcomes differ: " + ", ".join(out["checks_differ"]))
    if "flip_argmax" in out and out["flip_argmax"][0] != out["flip_argmax"][1]:
        reasons.append("flip argmax differs")
    for key in ("max_abs_diff_p_norm", "max_abs_diff_shapley", "max_abs_diff_flip_p_norm"):
        if out.get(key) is None and key != "max_abs_diff_flip_p_norm":
            reasons.append(f"{key} not computable")
        elif out.get(key) is not None and out[key] > tol:
            reasons.append(f"{key} {out[key]:.2e} > {tol}")
    out["reasons"] = reasons
    out["agrees"] = not reasons
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("new_run")
    ap.add_argument("--reference", default=str(DEFAULT_REF))
    ap.add_argument("--json", default=None, help="also write the comparison to this JSON file")
    ap.add_argument("--tol", type=float, default=0.01, help="largest acceptable probability / Shapley difference")
    a = ap.parse_args(argv)
    new, ref = Path(a.new_run), Path(a.reference)
    man_n = json.loads((new / "manifest.json").read_text())
    man_r = json.loads((ref / "manifest.json").read_text())
    print(f"new run:       {man_n['run_id']}  ({man_n['scorer'].get('device_name')}, torch {man_n['scorer'].get('torch_version')}, "
          f"transformers {man_n['scorer'].get('transformers_version')})")
    print(f"reference run: {man_r['run_id']}  ({man_r['scorer'].get('device_name')}, torch {man_r['scorer'].get('torch_version')}, "
          f"transformers {man_r['scorer'].get('transformers_version')})")
    if man_n.get("design_fingerprints") != man_r.get("design_fingerprints"):
        print("WARNING: design fingerprints differ: the scenarios or prompt constants are not the same as in the reference run.")
    res = {}
    for sid in man_r["scenarios"]:
        if not (new / sid).is_dir():
            print(f"{sid:12s} missing in the new run")
            res[sid] = {"agrees": False, "missing": True}
            continue
        r = res[sid] = compare_scenario(new / sid, ref / sid, a.tol)
        line = (f"{sid:12s} d* {r['d_star'][0]} vs {r['d_star'][1]}; argmax/ordering {'same' if r['argmax_per_ordering'][0] == r['argmax_per_ordering'][1] else 'DIFFERENT ' + str(r['argmax_per_ordering'])}; "
                f"checks {'same' if not r['checks_differ'] else 'DIFFER: ' + ', '.join(r['checks_differ'])}; "
                f"max |dp| {r['max_abs_diff_p_norm']:.2e} over {r['cells_compared']} cells; max |dphi| {r['max_abs_diff_shapley']:.2e}")
        if "flip_argmax" in r:
            line += f"; flips {'same' if r['flip_argmax'][0] == r['flip_argmax'][1] else 'DIFFERENT'}"
        if "greedy_cited" in r:
            line += f"; greedy citations {'same' if r['greedy_cited'][0] == r['greedy_cited'][1] else 'differ'}"
        print(line + ("" if r["agrees"] else "  <-- " + "; ".join(r["reasons"])))
    ok = all(r["agrees"] for r in res.values())
    print(f"REPRODUCED: decisions, check outcomes and flips agree; all differences <= {a.tol}" if ok
          else "NOT REPRODUCED (see the reasons marked above)")
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=2, default=str))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
