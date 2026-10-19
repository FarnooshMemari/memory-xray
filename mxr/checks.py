"""Pre-specified validation checks for the feasibility test.

These are pass/fail validation checks with thresholds fixed in protocol v0.2
before any model is run. They are not statistical hypothesis tests.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from .design import CANONICAL, ORDERINGS, all_subsets, designed_answer, subset_key

CRITERIA_PATH = Path(__file__).resolve().parents[1] / "scenarios" / "validation_criteria.json"


def load_criteria(path=CRITERIA_PATH):
    """Frozen validation criteria (amendment 2)."""
    return json.loads(Path(path).read_text())

# Thresholds (protocol v0.2, section 9). Change only by amending the protocol.
LABEL_MASS_MIN = 0.95
GREEDY_MARGIN_MIN = 0.10
REPEAT_TOL = 1e-3
FIRST_TOKEN_RECOMPUTE_TOL = 1e-3
DESIGNED_AGREEMENT_MIN = 15          # of 16 subsets, in every ordering
DECISIVE_SHARE_MIN = 0.80            # phi(decisive) / (v(full) - v(empty))
DISTRACTOR_ABS_MAX = 0.05            # |phi(distractor)|, probability units
SHAPLEY_RANGE_FLAG = 0.10            # descriptive flag only, not pass/fail


def _check(cid, name, passed, detail):
    return {"id": cid, "name": name, "passed": bool(passed), "detail": detail}


def infrastructure_checks(cells, tokval, greedy_rows, repeat_rows, scorer_meta=None):
    out = []
    meta = scorer_meta or {}
    n_expected = len(ORDERINGS) * 2 ** len(CANONICAL)

    rt_fail = [t for t in tokval if not t["roundtrip_ok"]]
    out.append(_check("I1", "chat-template round trip", not rt_fail,
                      f"{len(tokval) - len(rt_fail)}/{len(tokval)} cells match"))

    tok_err = [t for t in tokval if t.get("error")]
    label_sets = {repr(sorted((k, tuple(v)) for k, v in t["label_ids"].items()))
                  for t in tokval if not t.get("error")}
    out.append(_check(
        "I2", "label token boundaries, prefix-free labels, identical label ids across cells",
        not tok_err and len(label_sets) == 1,
        f"{len(tok_err)} tokenization errors; {len(label_sets)} distinct label-id sets",
    ))

    nonfinite = [c for c in cells if not c["score"]["finite"]]
    recompute = max((c["score"]["max_first_token_recompute_diff"] for c in cells), default=0.0)
    out.append(_check("I3", "finite log-probs; consistent multi-token recomputation",
                      not nonfinite and recompute <= FIRST_TOKEN_RECOMPUTE_TOL,
                      f"{len(nonfinite)} non-finite cells; max first-token recompute diff {recompute:.2e}"))

    masses = [c["score"]["label_mass"] for c in cells]
    min_mass = min(masses) if masses else float("nan")
    out.append(_check("I4", f"label mass >= {LABEL_MASS_MIN} in every cell",
                      masses and min_mass >= LABEL_MASS_MIN,
                      f"min {min_mass:.4f}, median {sorted(masses)[len(masses) // 2]:.4f}" if masses else "no cells"))

    eligible = [g for g in greedy_rows if g["margin"] >= GREEDY_MARGIN_MIN]
    mismatched = [g for g in eligible if not g["token_match"]]
    all_match = sum(1 for g in greedy_rows if g["token_match"])
    out.append(_check("I5", f"greedy decoding reproduces the scored argmax (cells with margin >= {GREEDY_MARGIN_MIN})",
                      eligible and not mismatched,
                      f"{len(eligible) - len(mismatched)}/{len(eligible)} eligible cells match; "
                      f"{all_match}/{len(greedy_rows)} of all cells"))

    max_rep = max((r["max_abs_diff"] for r in repeat_rows), default=float("nan"))
    out.append(_check("I6", f"re-scoring repeatability (max |delta log p| <= {REPEAT_TOL})",
                      repeat_rows and max_rep <= REPEAT_TOL,
                      f"{len(repeat_rows)} cells re-scored; max diff {max_rep:.2e}"))

    keys = {(c["subset"], c["ordering"]) for c in cells}
    out.append(_check("I7", "completeness: 16 subsets x 3 orderings",
                      len(cells) == n_expected and len(keys) == n_expected,
                      f"{len(cells)} cells, {len(keys)} unique"))

    # Added in amendment 1.
    backend = meta.get("backend")
    if backend == "MOCK":
        out.append(_check("I8", "model commit pinned and verified", True, "n/a: MOCK scorer"))
        out.append(_check("I9", "float32 logits; stored weights unchanged", True, "n/a: MOCK scorer"))
        return out
    src = meta.get("revision_source")
    if src == "local_path":
        ok8, d8 = True, "n/a: local test model (no Hub commit)"
    else:
        ok8 = bool(meta.get("commit_hash")) and meta.get("revision_verified") is True
        d8 = (f"commit {meta.get('commit_hash')} ({src}); verified in cache: "
              f"{meta.get('revision_verified')}")
    out.append(_check("I8", "model commit pinned and verified", ok8, d8))
    ok9 = meta.get("logits_dtype") == "torch.float32" and meta.get("weights_unchanged_dtype") is True
    out.append(_check("I9", "float32 logits; stored weights unchanged", ok9,
                      f"logits {meta.get('logits_dtype')}; storage {meta.get('storage_dtype')}, "
                      f"compute {meta.get('compute_dtype')}; layer weight dtypes after forward "
                      f"{meta.get('layer_weight_dtypes_after')}"))
    return out


def behavioral_checks_single(analysis, scenario):
    """Recovery checks for the single-decisive synthetic control."""
    dec = scenario["designed"]["decisive"]
    assert len(dec) == 1, "single-decisive checks need exactly one decisive record"
    dec = dec[0]
    distractors = scenario["designed"]["distractors"]
    designed_full = analysis["designed_full_answer"]
    full_key = subset_key(frozenset(CANONICAL))
    dec_key = subset_key(frozenset([dec]))
    minus_key = subset_key(frozenset(CANONICAL) - {dec})
    per = analysis["per_ordering"]
    out = []

    ok = all(o["argmax"][full_key] == designed_full for o in per)
    out.append(_check("B1", "full evidence: argmax equals the designed answer in every ordering", ok,
                      [o["argmax"][full_key] for o in per]))

    ok = all(o["argmax"][dec_key] == designed_full for o in per)
    out.append(_check("B2", "decisive record alone: argmax equals the designed answer (sufficiency)", ok,
                      [o["argmax"][dec_key] for o in per]))

    ok = all(o["argmax"][minus_key] != designed_full for o in per)
    out.append(_check("B3", "decisive record removed: argmax changes (necessity)", ok,
                      [o["argmax"][minus_key] for o in per]))

    counts = [o["designed_agreement"] for o in per]
    out.append(_check("B4", f"argmax equals the designed answer in >= {DESIGNED_AGREEMENT_MIN}/16 subsets per ordering",
                      all(c >= DESIGNED_AGREEMENT_MIN for c in counts), counts))

    details, ok = [], True
    for o in per:
        phi = o["shapley"]
        total = o["v_full"] - o["v_empty"]
        share = phi[dec] / total if total > 0 else float("nan")
        is_max = phi[dec] >= max(phi.values())
        dmax = max(abs(phi[d]) for d in distractors)
        good = is_max and total > 0 and share >= DECISIVE_SHARE_MIN and dmax <= DISTRACTOR_ABS_MAX
        ok = ok and good
        details.append({"ordering": o["ordering"], "decisive_is_max": is_max,
                        "decisive_share": None if math.isnan(share) else round(share, 4),
                        "max_abs_distractor_phi": round(dmax, 4), "total_effect": round(total, 4)})
    out.append(_check("B5", f"Shapley recovers the design (decisive largest, share >= {DECISIVE_SHARE_MIN}, "
                      f"|distractor| <= {DISTRACTOR_ABS_MAX})", ok, details))
    return out


def _share(x, total):
    return x / total if total > 0 else float("nan")


def _r(x):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(x, 4)


def behavioral_checks_redundant(analysis, scenario, crit=None):
    """Recovery checks for the redundant-evidence control (amendment 2)."""
    c = (crit or load_criteria())["redundant"]
    r1, r2 = scenario["designed"]["redundant"]
    distractors = scenario["designed"]["distractors"]
    full = frozenset(CANONICAL)
    designed_full = analysis["designed_full_answer"]
    per = analysis["per_ordering"]
    out = []
    fk = subset_key(full)
    out.append(_check("BR1", "full evidence: argmax equals the designed answer in every ordering",
                      all(o["argmax"][fk] == designed_full for o in per), [o["argmax"][fk] for o in per]))
    k1, k2 = subset_key(frozenset([r1])), subset_key(frozenset([r2]))
    out.append(_check("BR2", "each redundant record alone gives the designed answer (each sufficient)",
                      all(o["argmax"][k1] == designed_full and o["argmax"][k2] == designed_full for o in per),
                      [f"{r1}:{o['argmax'][k1]} {r2}:{o['argmax'][k2]}" for o in per]))
    kb = subset_key(full - {r1, r2})
    out.append(_check("BR3", "both redundant records removed: argmax changes (jointly necessary)",
                      all(o["argmax"][kb] != designed_full for o in per), [o["argmax"][kb] for o in per]))
    counts = [o["designed_agreement"] for o in per]
    out.append(_check("BR4", f"argmax equals the designed answer in >= {c['DESIGNED_AGREEMENT_MIN']}/16 subsets per ordering",
                      all(n >= c["DESIGNED_AGREEMENT_MIN"] for n in counts), counts))
    ok5, ok6, d5, d6 = True, True, [], []
    for o in per:
        phi, loo = o["shapley"], o["loo"]
        total = o["v_full"] - o["v_empty"]
        s1, s2 = _share(phi[r1], total), _share(phi[r2], total)
        asym = abs(phi[r1] - phi[r2]) / total if total > 0 else float("nan")
        dmax = max(abs(phi[d]) for d in distractors)
        g5 = (total > 0 and s1 >= c["EACH_REDUNDANT_SHARE_MIN"] and s2 >= c["EACH_REDUNDANT_SHARE_MIN"]
              and s1 + s2 >= c["JOINT_REDUNDANT_SHARE_MIN"] and asym <= c["REDUNDANT_ASYMMETRY_MAX"]
              and dmax <= c["DISTRACTOR_ABS_MAX"])
        l1, l2 = _share(loo[r1], total), _share(loo[r2], total)
        g6 = total > 0 and l1 <= c["LOO_SHARE_MAX"] and l2 <= c["LOO_SHARE_MAX"]
        ok5, ok6 = ok5 and g5, ok6 and g6
        d5.append({"ordering": o["ordering"], f"share_{r1}": _r(s1), f"share_{r2}": _r(s2),
                   "asymmetry": _r(asym), "max_abs_distractor_phi": _r(dmax), "total_effect": _r(total)})
        d6.append({"ordering": o["ordering"], f"loo_share_{r1}": _r(l1), f"loo_share_{r2}": _r(l2)})
    out.append(_check("BR5", f"Shapley splits credit between the redundant pair (each >= {c['EACH_REDUNDANT_SHARE_MIN']}, "
                      f"joint >= {c['JOINT_REDUNDANT_SHARE_MIN']}, asymmetry <= {c['REDUNDANT_ASYMMETRY_MAX']}, "
                      f"|distractor| <= {c['DISTRACTOR_ABS_MAX']})", ok5, d5))
    out.append(_check("BR6", f"leave-one-out misses the redundant records (each LOO share <= {c['LOO_SHARE_MAX']})",
                      ok6, d6))
    return out


def behavioral_checks_conflict(analysis, scenario, crit=None):
    """Recovery checks for the conflicting-evidence control (amendment 2)."""
    c = (crit or load_criteria())["conflict"]
    dom = scenario["designed"]["dominant"][0]
    sub = scenario["designed"]["subordinate"][0]
    distractors = scenario["designed"]["distractors"]
    full = frozenset(CANONICAL)
    designed_full = analysis["designed_full_answer"]
    per = analysis["per_ordering"]
    out = []
    fk = subset_key(full)
    out.append(_check("BC1", "full evidence: argmax equals the designed answer (precedence) in every ordering",
                      all(o["argmax"][fk] == designed_full for o in per), [o["argmax"][fk] for o in per]))
    ks = subset_key(frozenset([sub]))
    want_sub = designed_answer(scenario, frozenset([sub]))
    out.append(_check("BC2", f"subordinate record alone gives its own answer ({want_sub})",
                      all(o["argmax"][ks] == want_sub for o in per), [o["argmax"][ks] for o in per]))
    kp = subset_key(frozenset([dom, sub]))
    want_pair = designed_answer(scenario, frozenset([dom, sub]))
    out.append(_check("BC3", f"dominant and subordinate together: precedence holds ({want_pair})",
                      all(o["argmax"][kp] == want_pair for o in per), [o["argmax"][kp] for o in per]))
    counts = [o["designed_agreement"] for o in per]
    out.append(_check("BC4", f"argmax equals the designed answer in >= {c['DESIGNED_AGREEMENT_MIN']}/16 subsets per ordering",
                      all(n >= c["DESIGNED_AGREEMENT_MIN"] for n in counts), counts))
    ok, details = True, []
    for o in per:
        phi = o["shapley"]
        total = o["v_full"] - o["v_empty"]
        share = _share(phi[dom], total)
        is_max = phi[dom] >= max(phi.values())
        dmax = max(abs(phi[d]) for d in distractors)
        good = total > 0 and is_max and share >= c["DOMINANT_SHARE_MIN"] and dmax <= c["DISTRACTOR_ABS_MAX"]
        ok = ok and good
        details.append({"ordering": o["ordering"], "dominant_is_max": is_max, "dominant_share": _r(share),
                        "max_abs_distractor_phi": _r(dmax), "total_effect": _r(total)})
    out.append(_check("BC5", f"Shapley recovers precedence (dominant largest, share >= {c['DOMINANT_SHARE_MIN']}, "
                      f"|distractor| <= {c['DISTRACTOR_ABS_MAX']})", ok, details))
    return out


def behavioral_checks(analysis, scenario, crit=None):
    """Structure-specific recovery checks. Realistic scenarios have none (pass/fail)."""
    structure = scenario["structure"]
    if structure == "single_decisive":
        return behavioral_checks_single(analysis, scenario)
    if structure == "redundant":
        return behavioral_checks_redundant(analysis, scenario, crit)
    if structure == "conflict":
        return behavioral_checks_conflict(analysis, scenario, crit)
    if structure == "rubric":
        return []
    raise ValueError(f"unknown structure {structure!r}")


def descriptive_flags(analysis, scenario, crit=None):
    """Descriptive flags (never pass/fail)."""
    crit = crit or load_criteria()
    flags = []
    for rec, sp in analysis["shapley_spread"].items():
        if sp["range"] > SHAPLEY_RANGE_FLAG:
            flags.append(f"ordering sensitivity: range of phi({rec}) across orderings is "
                         f"{sp['range']:.3f} (> {SHAPLEY_RANGE_FLAG})")
    if analysis["d_star_disagreement"]:
        flags.append("full-set argmax differs across orderings")
    structure = scenario["structure"]
    if structure == "redundant":
        for w in scenario["designed"].get("weak", []):
            mean_phi = analysis["shapley_spread"][w]["mean"]
            if abs(mean_phi) > crit["redundant"]["WEAK_ABS_FLAG"]:
                flags.append(f"rule-excluded record {w} has influence: mean phi {mean_phi:.3f}")
    if structure == "rubric":
        prior = analysis["v_empty_spread"]["mean"]
        if prior > crit["realistic"]["PRIOR_DOMINANCE_MAX"]:
            flags.append(f"prior-dominated: P(d* | no records) = {prior:.3f} "
                         f"(> {crit['realistic']['PRIOR_DOMINANCE_MAX']}); low identifiability")
        if analysis["d_star"] != analysis["designed_full_answer"]:
            flags.append(f"d* ({analysis['d_star']}) differs from the rubric reference "
                         f"({analysis['designed_full_answer']})")
    return flags
