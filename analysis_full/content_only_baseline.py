#!/usr/bin/env python3
"""POST HOC (exploratory; defined after the results were seen): a content-only citation baseline.

Question: could a "citer" that NEVER observes the model's behavior score as well as Phi-3's own
citations on the pre-registered citation-consistency metrics (C1 necessity beat fraction, C2
sufficiency beat fraction, C3 Shapley top-k agreement)?

Content-only citer (fixed rule, one citation per scenario, identical in every ordering):
  * synthetic controls: the designed faithful citation from the scenario file (for S-redundant, whose
    design accepts {E1}, {E3} or {E1, E3}, the largest member {E1, E3});
  * realistic scenarios: every record whose rubric score has the sign of the rubric reference answer
    (the records whose CONTENT supports the decision).
It is scored with exactly the pre-registered metrics, against the model's own behavioral value
function v(S) = P(d* | S) in each ordering (code reused from independent_reanalysis.py).

Reads results/reanalysis.json, results/report_numbers.json and scenarios/*.json.
Writes results/post_hoc/content_only_baseline.json. No model, no GPU.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from independent_reanalysis import consistency  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ORDER = ("s_single", "s_redundant", "s_conflict", "macro_a", "macro_b", "macro_c")


def content_only_set(sc):
    des = sc["designed"]
    if sc["kind"] == "synthetic_control":
        fam = des.get("faithful_citations") or [des["faithful_citation"]]
        return sorted(max(fam, key=len))
    scores = {r: v["score"] for r, v in sc["rubric"]["scores"].items()}
    total = sum(scores.values())
    th = des["answer_rule"]["thresholds"]
    sign = 1 if total >= th["positive_min"] else (-1 if total <= th["negative_max"] else 0)
    if sign == 0:
        raise ValueError(f"{sc['scenario_id']}: rubric reference is Neutral; no supporting records")
    return sorted(r for r, s in scores.items() if s * sign > 0)


def vmap(o):
    return {frozenset(k.split("+")) if k != "none" else frozenset(): x for k, x in o["v"].items()}


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def _comparisons(out):
    """Scenario x metric comparisons (6 x 3): content-only >= model, and the exceptions."""
    ge, exceptions = 0, []
    for sid in ORDER:
        c, m = out["scenarios"][sid]["content_only"], out["scenarios"][sid]["model_pre_registered"]
        for k in ("mean_beat_nec", "mean_beat_suf", "mean_topk"):
            if c[k] >= m[k] - 1e-12:
                ge += 1
            else:
                exceptions.append({"scenario": sid, "metric": k, "content_only": c[k], "model": m[k]})
    return {"content_only_ge_model": ge, "of": 3 * len(ORDER), "exceptions": exceptions,
            "note": "Model values are means over that scenario's sampled partial citations (n = 5-8); content-only values are "
                    "means over the 3 orderings for one fixed set. Descriptive comparison only; no test."}


def main():
    R = json.loads((ROOT / "results" / "reanalysis.json").read_text())
    N = json.loads((ROOT / "results" / "report_numbers.json").read_text())["pre_registered"]
    out = {"POST_HOC": "Exploratory analysis defined after the results were seen. It qualifies the pre-registered "
                       "citation results and does not replace them.",
           "rule": "synthetic: designed faithful citation (largest designed set); realistic: records whose rubric score "
                   "has the sign of the rubric reference answer. Never observes model behavior.",
           "scenarios": {}}
    rows_c, rows_m = [], []
    for sid in ORDER:
        sc = json.loads((ROOT / "scenarios" / f"{sid}.json").read_text())
        s = R["scenarios"][sid]
        cset = content_only_set(sc)
        per = [consistency(vmap(o), o["phi"], cset) for o in s["per_ordering"]]
        model = N[sid]["citations"]["all"]
        analyzable = [r for r in s["citations"] if r.get("consistency") is not None and r["status"] in ("ok", "empty")]
        same = sum(sorted(r["cited"]) == cset for r in analyzable)
        out["scenarios"][sid] = {
            "content_only_set": cset,
            "content_only": {"mean_beat_nec": mean(p["beat_nec"] for p in per), "mean_beat_suf": mean(p["beat_suf"] for p in per),
                             "mean_topk": mean(p["topk"] for p in per),
                             "per_ordering": [{k: p[k] for k in ("beat_nec", "beat_suf", "topk")} for p in per]},
            "model_pre_registered": {k: model[k] for k in ("n_partial", "mean_beat_nec", "mean_beat_suf", "mean_topk")},
            "model_citations_equal_to_content_set": {"n": same, "of_analyzable_sampled_plus_greedy": len(analyzable)},
        }
        rows_c += per
        rows_m.append(model)
    pooled_model = N["_pooled_citations"]["all"]
    out["pooled"] = {
        "content_only_18_ordering_citations": {"mean_beat_nec": mean(p["beat_nec"] for p in rows_c),
                                               "mean_beat_suf": mean(p["beat_suf"] for p in rows_c),
                                               "mean_topk": mean(p["topk"] for p in rows_c)},
        "model_pre_registered_40_partial_sampled": {k: pooled_model[k] for k in ("n_partial", "mean_beat_nec", "mean_beat_suf",
                                                                                 "mean_topk")},
        "scenario_metric_comparisons": _comparisons(out),
        "model_citations_equal_to_content_set": {
            "n": sum(v["model_citations_equal_to_content_set"]["n"] for v in out["scenarios"].values()),
            "of": sum(v["model_citations_equal_to_content_set"]["of_analyzable_sampled_plus_greedy"] for v in out["scenarios"].values())},
    }
    dest = ROOT / "results" / "post_hoc"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "content_only_baseline.json").write_text(json.dumps(out, indent=2) + "\n")

    f = lambda x: "n/a" if x is None else f"{x:.3f}"  # noqa: E731
    print("POST HOC content-only citation baseline (never sees model behavior) vs the model's own citations")
    print(f"{'scenario':12s} {'content set':10s} | content-only nec / suf / top-k | model nec / suf / top-k (n partial)")
    for sid in ORDER:
        v = out["scenarios"][sid]
        c, m = v["content_only"], v["model_pre_registered"]
        print(f"{sid:12s} {'+'.join(v['content_only_set']):10s} | {f(c['mean_beat_nec'])} / {f(c['mean_beat_suf'])} / "
              f"{f(c['mean_topk'])} | {f(m['mean_beat_nec'])} / {f(m['mean_beat_suf'])} / {f(m['mean_topk'])} ({m['n_partial']})")
    p = out["pooled"]
    pc, pm = p["content_only_18_ordering_citations"], p["model_pre_registered_40_partial_sampled"]
    print(f"pooled       content-only {f(pc['mean_beat_nec'])} / {f(pc['mean_beat_suf'])} / {f(pc['mean_topk'])}  |  "
          f"model {f(pm['mean_beat_nec'])} / {f(pm['mean_beat_suf'])} / {f(pm['mean_topk'])}")
    cmp_ = p["scenario_metric_comparisons"]
    print(f"content-only >= model in {cmp_['content_only_ge_model']}/{cmp_['of']} scenario-metric comparisons; exceptions: "
          + "; ".join(f"{e['scenario']} {e['metric']} {e['content_only']:.3f} vs {e['model']:.3f}" for e in cmp_["exceptions"]))
    e = p["model_citations_equal_to_content_set"]
    print(f"model citations identical to the content-only set: {e['n']}/{e['of']} analyzable (sampled + greedy)")
    print(f"wrote {dest / 'content_only_baseline.json'}")


if __name__ == "__main__":
    main()
