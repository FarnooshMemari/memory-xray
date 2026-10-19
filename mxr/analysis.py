"""Turn scored cells into lattices, behavioral attributions and summaries."""
from __future__ import annotations

from .design import CANONICAL, LABELS, ORDERINGS, all_subsets, designed_answer, subset_key
from .metrics import TIE_TOL, citation_consistency, leave_one_out, shapley, spread


def build_lattices(cells):
    """{ordering: {frozenset subset: p_norm dict}}"""
    lat = {k: {} for k in range(len(ORDERINGS))}
    for c in cells:
        subset = frozenset(c["subset_members"])
        lat[c["ordering"]][subset] = c["score"]["p_norm"]
    return lat


def analyze(cells, scenario, tie_tol=TIE_TOL):
    players = CANONICAL
    full = frozenset(players)
    empty = frozenset()
    lat = build_lattices(cells)
    n_ord = len(ORDERINGS)

    # d* = argmax of the ordering-averaged full-evidence distribution.
    mean_full = {l: sum(lat[k][full][l] for k in range(n_ord)) / n_ord for l in LABELS}
    d_star = max(mean_full, key=mean_full.get)
    per_ord_full_argmax = [max(lat[k][full], key=lat[k][full].get) for k in range(n_ord)]

    per_ordering = []
    for k in range(n_ord):
        v = {s: lat[k][s][d_star] for s in all_subsets(players)}
        phi = shapley(v, players)
        loo = leave_one_out(v, players)
        argmax = {subset_key(s): max(lat[k][s], key=lat[k][s].get) for s in all_subsets(players)}
        agreement = sum(1 for s in all_subsets(players)
                        if argmax[subset_key(s)] == designed_answer(scenario, s))
        per_ordering.append({
            "ordering": k,
            "v": {subset_key(s): v[s] for s in v},
            "v_full": v[full],
            "v_empty": v[empty],
            "shapley": phi,
            "shapley_sum": sum(phi.values()),
            "loo": loo,
            "argmax": argmax,
            "designed_agreement": agreement,
            "_v_raw": v,
        })

    shapley_spread = {p: spread(o["shapley"][p] for o in per_ordering) for p in players}
    loo_spread = {p: spread(o["loo"][p] for o in per_ordering) for p in players}

    # Reference table: how every possible citation set would score on this
    # lattice. A reference for interpreting real citations, not a model output.
    reference_citations = []
    for s in all_subsets(players):
        per = [citation_consistency(o["_v_raw"], s, players, phi=o["shapley"], tol=tie_tol) for o in per_ordering]
        row = {"cited": subset_key(s), "category": per[0]["category"]}
        for key in ("necessity", "sufficiency", "beat_necessity", "beat_sufficiency",
                    "shapley_top_k_agreement"):
            vals = [p[key] for p in per]
            row[key] = None if any(x is None for x in vals) else spread(vals)
        reference_citations.append(row)

    for o in per_ordering:
        del o["_v_raw"]

    lattice_rows = []
    for s in all_subsets(players):
        lattice_rows.append({
            "subset": subset_key(s),
            "designed": designed_answer(scenario, s),
            "p_d_star": [lat[k][s][d_star] for k in range(n_ord)],
            "argmax": [max(lat[k][s], key=lat[k][s].get) for k in range(n_ord)],
        })

    return {
        "scenario_id": scenario["scenario_id"],
        "d_star": d_star,
        "mean_full_distribution": mean_full,
        "full_argmax_per_ordering": per_ord_full_argmax,
        "d_star_disagreement": len(set(per_ord_full_argmax)) > 1,
        "designed_full_answer": designed_answer(scenario, full),
        "per_ordering": per_ordering,
        "shapley_spread": shapley_spread,
        "loo_spread": loo_spread,
        "v_full_spread": spread(o["v_full"] for o in per_ordering),
        "v_empty_spread": spread(o["v_empty"] for o in per_ordering),
        "lattice": lattice_rows,
        "reference_citations": reference_citations,
        "variability_note": ("Ranges are min-max across 3 fixed orderings. They describe "
                             "ordering sensitivity; they are not confidence intervals."),
        "attribution_note": ("Shapley, LOO, necessity and sufficiency are behavioral "
                             "attributions of the model's output to the supplied records. "
                             "They are not ground truth about internal reasoning."),
    }
