#!/usr/bin/env python3
"""Verify src/data/explorer-data.json against the saved v0.2 files, independently of build_data.py.

  python3 scripts/verify_data.py            # from explorer/, checking against the repository root (..)

Checks, for every scenario:
  * the recorded SHA-256 of every source file still matches (the data was built from these exact files);
  * every one of the 288 subset probabilities equals the independent reanalysis (results/reanalysis.json)
    value v(S) = P(d* | S), and every argmax label matches;
  * the three probabilities of each subset sum to 1;
  * Shapley values recomputed here from the 16 subset values (24-permutation definition) equal the saved
    Shapley values, and leave-one-out equals v(all) - v(all without the record);
  * every citation's status, cited set, beat fractions and aligned/misaligned flag equal the reanalysis;
  * pooled citation numbers equal results/report_numbers.json and the post hoc baseline file.
Prints PASS/FAIL per check; exit code 0 only if everything passes.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import sys
from pathlib import Path

REC = ["E1", "E2", "E3", "E4"]
LABELS = ["Positive", "Neutral", "Negative"]
TOL = 1e-12
FAIL = []


def check(name, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}{': ' + detail if detail else ''}")
    if not ok:
        FAIL.append(name)


def key_of(mask):
    members = [e for i, e in enumerate(REC) if mask >> i & 1]
    return "+".join(members) if members else "none"


def shapley_perm(v):
    """Exact Shapley values by averaging marginal contributions over all 24 orders of joining."""
    phi = {e: 0.0 for e in REC}
    perms = list(itertools.permutations(range(4)))
    for perm in perms:
        mask = 0
        for i in perm:
            phi[REC[i]] += v[mask | 1 << i] - v[mask]
            mask |= 1 << i
    return {e: x / len(perms) for e, x in phi.items()}


def main():
    ap = argparse.ArgumentParser()
    root = Path(__file__).resolve().parents[1]
    ap.add_argument("--repo", default=str(root.parent))  # the repository root, above explorer/
    ap.add_argument("--data", default=str(root / "src" / "data" / "explorer-data.json"))
    a = ap.parse_args()
    repo = Path(a.repo)
    D = json.loads(Path(a.data).read_text())
    R = json.loads((repo / "results" / "reanalysis.json").read_text())
    N = json.loads((repo / "results" / "report_numbers.json").read_text())
    B = json.loads((repo / "results" / "post_hoc" / "content_only_baseline.json").read_text())

    bad = [s["path"] for s in D["meta"]["sources"] if hashlib.sha256((repo / s["path"]).read_bytes()).hexdigest() != s["sha256"]]
    check("source files unchanged since the data was built", not bad, f"{len(D['meta']['sources'])} files" + (f"; changed: {bad}" if bad else ""))
    check("run id", D["meta"]["runId"] == R["run_id"], D["meta"]["runId"])

    n_cells = max_dv = max_dphi = max_dloo = max_sum = 0.0
    argmax_bad = 0
    for s in D["scenarios"]:
        rs = R["scenarios"][s["id"]]
        dstar = s["dStar"]
        check(f"{s['id']}: d* matches reanalysis", dstar == rs["d_star"], dstar)
        for o in s["orderings"]:
            ro = rs["per_ordering"][o["index"]]
            v = {}
            for m in range(16):
                cell = o["subsets"][str(m)]
                p = dict(zip(LABELS, cell["p"]))
                v[m] = p[dstar]
                max_dv = max(max_dv, abs(v[m] - ro["v"][key_of(m)]))
                max_sum = max(max_sum, abs(sum(cell["p"]) - 1))
                argmax_bad += cell["argmax"] != ro["argmax"][key_of(m)] or cell["argmax"] != max(p, key=p.get)
                n_cells += 1
            phi = shapley_perm(v)
            for e in REC:
                max_dphi = max(max_dphi, abs(phi[e] - o["shapley"][e]), abs(o["shapley"][e] - ro["phi"][e]))
                loo = v[15] - v[15 & ~(1 << REC.index(e))]
                max_dloo = max(max_dloo, abs(loo - o["loo"][e]), abs(o["loo"][e] - ro["loo"][e]))
            check(f"{s['id']} ordering {o['index']}: full-evidence argmax", o["fullArgmax"] == ro["full_argmax"], o["fullArgmax"])
        # citations
        rc = rs["citations"]
        ok = len(s["citations"]) == len(rc) == 13
        mism = []
        for c, r in zip(s["citations"], rc):
            same = (c["ordering"] == r["ordering"] and c["kind"] == r["kind"] and c["status"] == r["status"]
                    and c["cited"] == (r["cited"] if r["status"] in ("ok", "empty") else None)
                    and c["aligned"] == r["aligned"] and c["ownAnswer"] == r["own_full_argmax"]
                    and c["shownLabel"] == r["decision_in_context"])
            rcon = r.get("consistency") or {}
            for k_d, k_r in (("beatNec", "beat_nec"), ("beatSuf", "beat_suf"), ("topk", "topk")):
                x, y = c[k_d], rcon.get(k_r)
                same &= (x is None and y is None) or (x is not None and y is not None and abs(x - y) <= TOL)
            if not same:
                mism.append((c["ordering"], c["kind"], c["seed"]))
        check(f"{s['id']}: 13 citation replies match the reanalysis", ok and not mism, f"mismatches: {mism}" if mism else "")
        cm = N["pre_registered"][s["id"]]["citations"]["all"]
        check(f"{s['id']}: citation metrics", all(abs(s["citationMetrics"][k] - cm[k]) <= TOL for k in ("mean_beat_nec", "mean_beat_suf", "mean_topk")))
        co = B["scenarios"][s["id"]]
        check(f"{s['id']}: content-only set (post hoc)", s["contentOnly"]["set"] == co["content_only_set"], "+".join(s["contentOnly"]["set"]))
        mis = [k for k in range(3) if s["orderings"][k]["fullArgmax"] != dstar]
        check(f"{s['id']}: misaligned orderings", mis == s["misalignedOrderings"], str(mis))
        # fields the page displays directly
        check(f"{s['id']}: content-only scores (post hoc)",
              all(abs(s["contentOnly"][k] - co["content_only"][k]) <= TOL for k in ("mean_beat_nec", "mean_beat_suf", "mean_topk")))
        check(f"{s['id']}: number of partial citations", s["citationMetrics"]["n_partial"] == co["model_pre_registered"]["n_partial"],
              str(s["citationMetrics"]["n_partial"]))
        summ_ok = True
        for e in REC:
            vals = [o["shapley"][e] for o in s["orderings"]]
            sm = s["shapleySummary"][e]
            # the summary is copied from report_numbers.json; it must agree with the per-ordering values to float precision
            summ_ok &= (abs(sm["mean"] - sum(vals) / 3) <= 1e-12 and abs(sm["min"] - min(vals)) <= 1e-12
                        and abs(sm["max"] - max(vals)) <= 1e-12)
        check(f"{s['id']}: Shapley mean and range across orderings", summ_ok)
        sc = json.loads((repo / "scenarios" / f"{s['id']}.json").read_text())
        check(f"{s['id']}: record texts equal the scenario file", all(s["records"][e]["text"] == sc["records"][e] for e in REC))
        src = [json.loads(line) for line in (repo / "runs" / D["meta"]["runId"] / s["id"] / "citations.jsonl").read_text().splitlines() if line.strip()]
        by_key = {(r["ordering"], r["kind"], r["seed"]): r["raw"] for r in src}
        check(f"{s['id']}: raw reply texts equal the run files",
              len(by_key) == 13 and all(by_key.get((c["ordering"], c["kind"], c["seed"])) == c["raw"] for c in s["citations"]))

    check("288 subset probabilities equal the reanalysis", n_cells == 288 and max_dv <= TOL, f"{int(n_cells)} cells, max |diff| {max_dv:.1e}")
    check("probabilities sum to 1", max_sum <= 1e-9, f"max |sum - 1| {max_sum:.1e}")
    check("argmax labels match", argmax_bad == 0, f"{argmax_bad} mismatches")
    check("Shapley values recomputed from the lattice match", max_dphi <= 1e-12, f"max |diff| {max_dphi:.1e}")
    check("leave-one-out values match", max_dloo <= 1e-12, f"max |diff| {max_dloo:.1e}")

    P = D["pooled"]
    pc = N["pre_registered"]["_pooled_citations"]["all"]
    check("pooled citation metrics (pre-registered)", all(abs(P["model"][k] - pc[k]) <= TOL for k in ("mean_beat_nec", "mean_beat_suf", "mean_topk")),
          f"{P['model']['mean_beat_nec']:.3f} / {P['model']['mean_beat_suf']:.3f} / {P['model']['mean_topk']:.3f}")
    cb = B["pooled"]["content_only_18_ordering_citations"]
    check("pooled content-only metrics (post hoc)", all(abs(P["contentOnly"][k] - cb[k]) <= TOL for k in cb),
          f"{cb['mean_beat_nec']:.3f} / {cb['mean_beat_suf']:.3f} / {cb['mean_topk']:.3f}")
    cmp_ = P["contentOnlyComparison"]
    check("content-only comparison counts", (cmp_["higher"], cmp_["tied"], cmp_["lower"]) == (10, 7, 1)
          and cmp_["higher"] + cmp_["tied"] == B["pooled"]["scenario_metric_comparisons"]["content_only_ge_model"], str(cmp_))
    for pool, key in (("aligned", "aligned_only_pooled"), ("misaligned", "misaligned_only_pooled")):
        src = N["post_hoc"][key]
        check(f"{pool} citation pool (post hoc split)", P[pool]["n_partial"] == src["n_partial"]
              and all(abs(P[pool][k] - src[k]) <= TOL for k in ("mean_beat_nec", "mean_beat_suf", "mean_topk")
                      + (("share_beat_nec_gt_half", "share_beat_suf_gt_half") if pool == "misaligned" else ())),
              f"n = {P[pool]['n_partial']}, necessity {P[pool]['mean_beat_nec']:.3f}")
    n_inj = sum(1 for s in D["scenarios"] for c in s["citations"] if c["kind"] == "sampled" and c["beatNec"] is not None and not c["aligned"])
    check("scored citations given for an injected decision: 8 of 40", n_inj == P["misaligned"]["n_partial"] == 8
          and sum(s["citationMetrics"]["n_partial"] for s in D["scenarios"]) == P["model"]["n_partial"] == 40, f"{n_inj} of {P['model']['n_partial']}")
    mis_total = sum(len(s["misalignedOrderings"]) for s in D["scenarios"])
    check("decision mismatch: 3 of 18 orderings", mis_total == 3, str(mis_total))
    allc = [c for s in D["scenarios"] for c in s["citations"]]
    st = {}
    for c in allc:
        if c["kind"] == "sampled":
            st[c["status"]] = st.get(c["status"], 0) + 1
    check("sampled reply statuses", st == P["sampledStatus"] == {"ok": 45, "unparseable": 14, "empty": 1}, str(st))
    print(f"\n{'ALL DATA CHECKS PASS' if not FAIL else 'DATA CHECKS FAILED: ' + ', '.join(FAIL)}")
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
