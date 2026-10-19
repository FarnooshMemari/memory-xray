"""Citation consistency summaries (descriptive; no significance tests)."""
from __future__ import annotations

from collections import Counter

from .design import CANONICAL, faithful_citations, parse_subset_key, subset_key
from .metrics import FULL_RUN_TIE_TOL, citation_consistency

ANALYZABLE = ("ok", "empty")


def _lattice(analysis, k):
    o = analysis["per_ordering"][k]
    return {parse_subset_key(key): val for key, val in o["v"].items()}, o["shapley"]


def score_citations(rows, analysis, tol=FULL_RUN_TIE_TOL):
    """Attach citation-consistency results to every analyzable citation row."""
    out = []
    for row in rows:
        row = dict(row)
        if row["parse"]["status"] in ANALYZABLE:
            v, phi = _lattice(analysis, row["ordering"])
            cited = frozenset(row["parse"]["canonical"])
            row["cited_key"] = subset_key(cited)
            row["consistency"] = citation_consistency(v, cited, CANONICAL, phi=phi, tol=tol)
        out.append(row)
    return out


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return (sum(xs) / len(xs)) if xs else None


def summarize(scored_rows, scenario):
    sampled = [r for r in scored_rows if r["kind"] == "sampled"]
    greedy = [r for r in scored_rows if r["kind"] == "greedy"]
    analyzable = [r for r in sampled if "consistency" in r]
    partial = [r for r in analyzable if r["consistency"]["category"] == "partial"]
    sets = Counter(r["cited_key"] for r in analyzable)
    modal = sets.most_common(1)[0] if sets else (None, 0)
    faithful = {subset_key(frozenset(f)) for f in faithful_citations(scenario)}
    designed = scenario.get("designed", {})
    weak = set(designed.get("weak", []))
    distractors = set(designed.get("distractors", []))

    def share(pred, rows):
        return (sum(1 for r in rows if pred(r)) / len(rows)) if rows else None

    return {
        "n_sampled": len(sampled),
        "status_counts_sampled": dict(Counter(r["parse"]["status"] for r in sampled)),
        "n_analyzable_sampled": len(analyzable),
        "category_counts": dict(Counter(r["consistency"]["category"] for r in analyzable)),
        "size_distribution": dict(Counter(r["consistency"]["size"] for r in analyzable)),
        "set_frequencies": dict(sets),
        "modal_set": modal[0],
        "modal_set_share": (modal[1] / len(analyzable)) if analyzable else None,
        "n_partial": len(partial),
        "mean_beat_necessity": _mean(r["consistency"]["beat_necessity"] for r in partial),
        "mean_beat_sufficiency": _mean(r["consistency"]["beat_sufficiency"] for r in partial),
        "share_beat_necessity_above_half": share(lambda r: r["consistency"]["beat_necessity"] > 0.5, partial),
        "share_beat_sufficiency_above_half": share(lambda r: r["consistency"]["beat_sufficiency"] > 0.5, partial),
        "mean_shapley_top_k_agreement": _mean(r["consistency"]["shapley_top_k_agreement"] for r in partial),
        "faithful_exact_match_share": share(lambda r: r["cited_key"] in faithful, analyzable) if faithful else None,
        "cites_rule_excluded_share": share(lambda r: bool(weak & set(r["parse"]["canonical"])), analyzable) if weak else None,
        "cites_distractor_share": share(lambda r: bool(distractors & set(r["parse"]["canonical"])), analyzable) if distractors else None,
        "greedy": [{"ordering": r["ordering"], "status": r["parse"]["status"],
                    "cited": r.get("cited_key"),
                    "category": r["consistency"]["category"] if "consistency" in r else None,
                    "beat_necessity": r["consistency"]["beat_necessity"] if "consistency" in r else None,
                    "beat_sufficiency": r["consistency"]["beat_sufficiency"] if "consistency" in r else None,
                    "faithful": (r.get("cited_key") in faithful) if faithful and "consistency" in r else None}
                   for r in greedy],
        "note": ("Descriptive summaries of 10 sampled citations and 3 greedy reference citations. "
                 "Beat fractions use the exact same-size null (chance = 0.5) with differences under 0.01 in "
                 "P(d*) counted as ties; empty and all-record "
                 "citations are counted separately and excluded from beat fractions. No significance tests."),
    }
