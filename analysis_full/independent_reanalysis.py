#!/usr/bin/env python3
"""Independent reanalysis of the full experiment from the saved JSONL files.

Deliberately does NOT import the pipeline's metric, analysis, check or
citation code (mxr.metrics, mxr.analysis, mxr.checks, mxr.citations,
mxr.citation_analysis). Everything is recomputed from the raw saved values:
  * label probabilities from the saved per-label log-probs;
  * Shapley values by averaging marginal contributions over all 24 orderings
    of the four records (the pipeline uses the subset-weight formula);
  * leave-one-out, necessity and sufficiency;
  * every frozen validation check, from scenarios/validation_criteria.json;
  * citation parsing from the raw generated text, and citation consistency.
It then compares each result with the saved pipeline outputs, and adds the
focused diagnostics used in the Results and Discussion report.

Inputs (read-only): runs/full_20261017T223452Z/, scenarios/*.json
Output: results/reanalysis.json
"""
from __future__ import annotations

import itertools
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "full_20261017T223452Z"
OUT = ROOT / "results" / "reanalysis.json"
P = ("E1", "E2", "E3", "E4")
LABELS = ("Positive", "Neutral", "Negative")
ORDERINGS = ((0, 1, 2, 3), (2, 0, 3, 1), (3, 2, 1, 0))      # from the frozen design (mxr/design.py)
TIE = 0.01                                                  # pre-registered full-run tie tolerance
CRIT = json.loads((ROOT / "scenarios" / "validation_criteria.json").read_text())
SCEN_IDS = ("s_single", "s_redundant", "s_conflict", "macro_a", "macro_b", "macro_c")


def jl(path):
    return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]


def key(s):
    return "+".join(p for p in P if p in s) or "none"


def subsets():
    return [frozenset(c) for r in range(5) for c in itertools.combinations(P, r)]


def norm_from_logprobs(score):
    raw = {l: math.exp(score["labels"][l]["logprob"]) for l in LABELS}
    z = sum(raw.values())
    return {l: raw[l] / z for l in LABELS}, z


def designed(sc, s, flipped=False):
    rule = sc["designed"]["answer_rule"]
    if rule["type"] == "contains_any":
        return rule["if_true"] if any(r in s for r in rule["records"]) else rule["if_false"]
    if rule["type"] == "precedence":
        for step in rule["order"]:
            if step["record"] in s:
                return step["answer"]
        return rule["default"]
    scores = {r: v["score"] for r, v in sc["rubric"]["scores"].items()}
    if flipped:
        scores[sc["flip"]["target"]] = sc["flip"]["score"]
    t = sum(scores[r] for r in s)
    th = rule["thresholds"]
    return "Positive" if t >= th["positive_min"] else "Negative" if t <= th["negative_max"] else "Neutral"


def shapley_perm(v):
    phi = {p: 0.0 for p in P}
    perms = list(itertools.permutations(P))
    for perm in perms:
        s = frozenset()
        for p in perm:
            phi[p] += (v[s | {p}] - v[s]) / len(perms)
            s = s | {p}
    return phi


def beat(x, others):
    if not others:
        return None
    return (sum(1 for o in others if o < x - TIE) + 0.5 * sum(1 for o in others if abs(o - x) <= TIE)) / len(others)


def parse_raw(text, shown, id_map):
    """Independent re-implementation of the frozen citation parser rules."""
    m = re.search(r"\[[^\[\]]*\]", text or "", re.S)
    if not m:
        return "unparseable", None
    try:
        items = json.loads(m.group(0))
    except json.JSONDecodeError:
        return "unparseable", None
    if not isinstance(items, list) or not all(isinstance(x, str) for x in items):
        return "unparseable", None
    ids = list(dict.fromkeys(x.strip() for x in items))
    if any(i not in shown for i in ids):
        return "invalid_id", None
    return ("empty" if not ids else "ok"), sorted(id_map[i] for i in ids)


def consistency(v, phi, cited):
    full = frozenset(P)
    c = frozenset(cited)
    nec = lambda s: v[full] - v[full - s]
    suf = lambda s: v[s] - v[full]
    out = {"size": len(c), "necessity": nec(c), "sufficiency": suf(c)}
    if len(c) in (0, 4):
        out.update(category="empty" if not c else "all", beat_nec=None, beat_suf=None, topk=None)
        return out
    alts = [frozenset(x) for x in itertools.combinations(P, len(c)) if frozenset(x) != c]
    ranked = sorted(phi.values(), reverse=True)
    top = {p for p, val in phi.items() if val >= ranked[len(c) - 1] - TIE}
    out.update(category="partial", beat_nec=beat(nec(c), [nec(a) for a in alts]),
               beat_suf=beat(suf(c), [suf(a) for a in alts]),
               topk=sum(1 for p in c if p in top) / len(c))
    return out


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def checks_for(sc, per, d_star, designed_full):
    """Frozen recovery checks, re-implemented from validation_criteria.json."""
    st = sc["structure"]
    full = frozenset(P)
    res = {}

    def arg(o, s):
        return o["argmax"][key(s)]

    def agree_all(o):
        return sum(1 for s in subsets() if arg(o, s) == designed(sc, s))
    if st == "single_decisive":
        c = CRIT["single_decisive"]; dec = sc["designed"]["decisive"][0]; dis = sc["designed"]["distractors"]
        res["B1"] = all(arg(o, full) == designed_full for o in per)
        res["B2"] = all(arg(o, frozenset([dec])) == designed_full for o in per)
        res["B3"] = all(arg(o, full - {dec}) != designed_full for o in per)
        res["B4"] = all(agree_all(o) >= c["DESIGNED_AGREEMENT_MIN"] for o in per)
        res["B5"] = all((o["total"] > 0 and o["phi"][dec] >= max(o["phi"].values())
                         and o["phi"][dec] / o["total"] >= c["DECISIVE_SHARE_MIN"]
                         and max(abs(o["phi"][d]) for d in dis) <= c["DISTRACTOR_ABS_MAX"]) for o in per)
    elif st == "redundant":
        c = CRIT["redundant"]; r1, r2 = sc["designed"]["redundant"]; dis = sc["designed"]["distractors"]
        res["BR1"] = all(arg(o, full) == designed_full for o in per)
        res["BR2"] = all(arg(o, frozenset([r1])) == designed_full and arg(o, frozenset([r2])) == designed_full for o in per)
        res["BR3"] = all(arg(o, full - {r1, r2}) != designed_full for o in per)
        res["BR4"] = all(agree_all(o) >= c["DESIGNED_AGREEMENT_MIN"] for o in per)
        res["BR5"] = all(o["total"] > 0 and o["phi"][r1] / o["total"] >= c["EACH_REDUNDANT_SHARE_MIN"]
                         and o["phi"][r2] / o["total"] >= c["EACH_REDUNDANT_SHARE_MIN"]
                         and (o["phi"][r1] + o["phi"][r2]) / o["total"] >= c["JOINT_REDUNDANT_SHARE_MIN"]
                         and abs(o["phi"][r1] - o["phi"][r2]) / o["total"] <= c["REDUNDANT_ASYMMETRY_MAX"]
                         and max(abs(o["phi"][d]) for d in dis) <= c["DISTRACTOR_ABS_MAX"] for o in per)
        res["BR6"] = all(o["total"] > 0 and o["loo"][r1] / o["total"] <= c["LOO_SHARE_MAX"]
                         and o["loo"][r2] / o["total"] <= c["LOO_SHARE_MAX"] for o in per)
    elif st == "conflict":
        c = CRIT["conflict"]; dom = sc["designed"]["dominant"][0]; sub = sc["designed"]["subordinate"][0]
        dis = sc["designed"]["distractors"]
        res["BC1"] = all(arg(o, full) == designed_full for o in per)
        res["BC2"] = all(arg(o, frozenset([sub])) == designed(sc, frozenset([sub])) for o in per)
        res["BC3"] = all(arg(o, frozenset([dom, sub])) == designed(sc, frozenset([dom, sub])) for o in per)
        res["BC4"] = all(agree_all(o) >= c["DESIGNED_AGREEMENT_MIN"] for o in per)
        res["BC5"] = all(o["total"] > 0 and o["phi"][dom] >= max(o["phi"].values())
                         and o["phi"][dom] / o["total"] >= c["DOMINANT_SHARE_MIN"]
                         and max(abs(o["phi"][d]) for d in dis) <= c["DISTRACTOR_ABS_MAX"] for o in per)
    return res


def infra_for(sdir, cells, meta):
    c = CRIT["infrastructure"]
    tok = json.loads((sdir / "tokenization_validation.json").read_text())
    tok = [t for t in tok if not t.get("flipped")]
    greedy = jl(sdir / "greedy_check.jsonl")
    rep = json.loads((sdir / "repeatability.json").read_text())
    label_sets = {json.dumps(t["label_ids"], sort_keys=True) for t in tok if not t.get("error")}
    eligible = [g for g in greedy if g["margin"] >= c["GREEDY_MARGIN_MIN"]]
    return {
        "I1": all(t["roundtrip_ok"] for t in tok),
        "I2": not any(t.get("error") for t in tok) and len(label_sets) == 1,
        "I3": all(x["score"]["finite"] for x in cells)
              and max(x["score"]["max_first_token_recompute_diff"] for x in cells) <= c["FIRST_TOKEN_RECOMPUTE_TOL"],
        "I4": min(x["score"]["label_mass"] for x in cells) >= c["LABEL_MASS_MIN"],
        "I5": bool(eligible) and all(list(g["greedy_ids"][:len(g["argmax_ids"])]) == list(g["argmax_ids"]) for g in eligible),
        "I6": max(r["max_abs_diff"] for r in rep) <= c["REPEAT_TOL"],
        "I7": len(cells) == 48 and len({(x["subset"], x["ordering"]) for x in cells}) == 48,
        "I8": bool(meta.get("commit_hash")) and meta.get("revision_verified") is True,
        "I9": meta.get("logits_dtype") == "torch.float32" and meta.get("weights_unchanged_dtype") is True,
        "_max_recompute_diff": max(x["score"]["max_first_token_recompute_diff"] for x in cells),
        "_min_label_mass": min(x["score"]["label_mass"] for x in cells),
        "_greedy_matches": sum(list(g["greedy_ids"][:len(g["argmax_ids"])]) == list(g["argmax_ids"]) for g in greedy),
        "_max_repeat_diff": max(r["max_abs_diff"] for r in rep),
    }


def main():
    man = json.loads((RUN / "manifest.json").read_text())
    meta = man["scorer"]
    out = {"run_id": man["run_id"], "scenarios": {}, "comparison_with_pipeline": {}}
    for idx, sid in enumerate(SCEN_IDS):
        sc = json.loads((ROOT / "scenarios" / f"{sid}.json").read_text())
        sdir = RUN / sid
        cells = jl(sdir / "cells.jsonl")
        saved = json.loads((sdir / "analysis.json").read_text())
        saved_checks = json.loads((sdir / "checks.json").read_text())

        # label probabilities recomputed from saved log-probs
        lat, masses, pn_diff = {k: {} for k in range(3)}, [], 0.0
        for x in cells:
            pn, z = norm_from_logprobs(x["score"])
            pn_diff = max(pn_diff, max(abs(pn[l] - x["score"]["p_norm"][l]) for l in LABELS))
            lat[x["ordering"]][frozenset(x["subset_members"])] = pn
            masses.append(z)
        full = frozenset(P)
        mean_full = {l: sum(lat[k][full][l] for k in range(3)) / 3 for l in LABELS}
        d_star = max(mean_full, key=mean_full.get)
        designed_full = designed(sc, full)

        per = []
        for k in range(3):
            v = {s: lat[k][s][d_star] for s in subsets()}
            phi = shapley_perm(v)
            loo = {p: v[full] - v[full - {p}] for p in P}
            argmax = {key(s): max(lat[k][s], key=lat[k][s].get) for s in subsets()}
            per.append({"ordering": k, "v": {key(s): v[s] for s in subsets()}, "phi": phi, "loo": loo,
                        "argmax": argmax, "v_full": v[full], "v_empty": v[frozenset()],
                        "total": v[full] - v[frozenset()],
                        "full_dist": lat[k][full], "full_argmax": argmax[key(full)],
                        "designed_agreement": sum(1 for s in subsets() if argmax[key(s)] == designed(sc, s))})
        checks = checks_for(sc, per, d_star, designed_full)
        infra = infra_for(sdir, cells, meta)

        # flips
        flips = None
        if "flip" in sc:
            fr = jl(sdir / "flips.jsonl")
            flips = []
            for r in fr:
                pn, z = norm_from_logprobs(r["score"])
                k = r["ordering"]
                flips.append({"ordering": k, "argmax": max(pn, key=pn.get), "dist": pn,
                              "orig_dist": lat[k][full], "orig_argmax": per[k]["full_argmax"],
                              "p_dstar_orig": per[k]["v_full"], "p_dstar_flip": pn[d_star],
                              "delta_p_dstar": pn[d_star] - per[k]["v_full"],
                              "moved_away": max(pn, key=pn.get) != d_star, "mass": z,
                              "tv_distance": 0.5 * sum(abs(pn[l] - lat[k][full][l]) for l in LABELS)})

        # citations: re-parse raw text and recompute consistency
        cits = jl(sdir / "citations.jsonl")
        crow = []
        for r in cits:
            status, canon = parse_raw(r["raw"], r["shown_ids"], r["id_to_canonical"])
            k = r["ordering"]
            row = {"ordering": k, "kind": r["kind"], "seed": r["seed"], "raw": r["raw"],
                   "status": status, "saved_status": r["parse"]["status"], "cited": canon,
                   "own_full_argmax": per[k]["full_argmax"], "decision_in_context": r["decision_in_context"],
                   "aligned": per[k]["full_argmax"] == r["decision_in_context"]}
            if status in ("ok", "empty"):
                v = {frozenset(s.split("+")) if s != "none" else frozenset(): val for s, val in per[k]["v"].items()}
                row["consistency"] = consistency(v, per[k]["phi"], canon)
                saved_c = r.get("consistency", {})
                row["matches_saved"] = all(
                    (saved_c.get(a) is None and row["consistency"][b] is None) or
                    (saved_c.get(a) is not None and row["consistency"][b] is not None and abs(saved_c[a] - row["consistency"][b]) < 1e-9)
                    for a, b in (("necessity", "necessity"), ("sufficiency", "sufficiency"),
                                 ("beat_necessity", "beat_nec"), ("beat_sufficiency", "beat_suf"),
                                 ("shapley_top_k_agreement", "topk")))
            crow.append(row)

        # pipeline comparison
        sp = saved["per_ordering"]
        phi_diff = max(abs(per[k]["phi"][p] - sp[k]["shapley"][p]) for k in range(3) for p in P)
        loo_diff = max(abs(per[k]["loo"][p] - sp[k]["loo"][p]) for k in range(3) for p in P)
        v_diff = max(abs(per[k]["v"][s] - sp[k]["v"][s]) for k in range(3) for s in per[k]["v"])
        saved_pass = {c["id"]: c["passed"] for c in saved_checks["infrastructure"] + saved_checks["behavioral"]}
        mine = {**{k2: v2 for k2, v2 in infra.items() if not k2.startswith("_")}, **checks}
        out["comparison_with_pipeline"][sid] = {
            "d_star_equal": d_star == saved["d_star"],
            "max_abs_diff_p_norm_from_logprobs": pn_diff,
            "max_abs_diff_v": v_diff, "max_abs_diff_shapley": phi_diff, "max_abs_diff_loo": loo_diff,
            "checks_equal": mine == saved_pass,
            "citation_status_equal": all(r["status"] == r["saved_status"] for r in crow),
            "citation_consistency_equal": all(r.get("matches_saved", True) for r in crow),
        }
        out["scenarios"][sid] = {
            "kind": sc["kind"], "structure": sc["structure"], "d_star": d_star, "designed_full": designed_full,
            "mean_full_dist": mean_full, "per_ordering": per, "checks": checks, "infra": infra,
            "saved_flags": saved_checks["flags"], "flips": flips, "citations": crow,
            "order_positions": {k: {CANON: ORDERINGS[k].index(i) for i, CANON in enumerate(P)} for k in range(3)},
        }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, default=lambda o: sorted(o) if isinstance(o, frozenset) else str(o)))
    ok = all(all(v for k, v in c.items() if k != "max_abs_diff_p_norm_from_logprobs" and not k.startswith("max_abs"))
             and c["max_abs_diff_shapley"] < 1e-12 and c["max_abs_diff_v"] < 1e-12
             for c in out["comparison_with_pipeline"].values())
    for sid, c in out["comparison_with_pipeline"].items():
        print(sid, c)
    print("INDEPENDENT REANALYSIS AGREES WITH PIPELINE:", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
