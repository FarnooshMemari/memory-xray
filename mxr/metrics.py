"""Behavioral attribution metrics over an exhaustively enumerated subset lattice.

All functions take ``v``: a dict mapping every frozenset of players (records)
to a real value, here v(S) = normalized P(d* | S). These are measures of how
the model's *output* responds to evidence interventions. They are behavioral
attributions, not ground truth about the model's internal reasoning.
"""
from __future__ import annotations

from itertools import combinations
from math import factorial

TIE_TOL = 1e-9  # exact ties only (feasibility runs)

# Full experiment (amendment 2): differences in P(d*) below one percentage point
# are treated as ties in beat fractions and Shapley top-k agreement, so that
# ranks are never decided by noise-level differences.
FULL_RUN_TIE_TOL = 0.01


def _check_lattice(v, players):
    n = len(players)
    if len(v) != 2 ** n:
        raise ValueError(f"expected {2 ** n} subsets, got {len(v)}")


def shapley(v, players):
    """Exact Shapley values. Sum equals v(full) - v(empty) (efficiency)."""
    _check_lattice(v, players)
    n = len(players)
    phi = {}
    for i in players:
        others = [p for p in players if p != i]
        total = 0.0
        for r in range(n):
            weight = factorial(r) * factorial(n - r - 1) / factorial(n)
            for combo in combinations(others, r):
                s = frozenset(combo)
                total += weight * (v[s | {i}] - v[s])
        phi[i] = total
    return phi


def leave_one_out(v, players):
    full = frozenset(players)
    return {i: v[full] - v[full - {i}] for i in players}


def necessity(v, cited, players):
    """SelfCite Prob-Drop analog: v(full) - v(full minus cited). Higher = more necessary."""
    full = frozenset(players)
    return v[full] - v[full - frozenset(cited)]


def sufficiency(v, cited, players):
    """SelfCite Prob-Hold analog: v(cited only) - v(full). Higher = more sufficient."""
    full = frozenset(players)
    return v[frozenset(cited)] - v[full]


def beat_fraction(score, other_scores, tol=TIE_TOL):
    """Share of alternative sets the cited set beats (ties count half). Chance = 0.5."""
    if not other_scores:
        return None
    less = sum(1 for s in other_scores if s < score - tol)
    ties = sum(1 for s in other_scores if abs(s - score) <= tol)
    return (less + 0.5 * ties) / len(other_scores)


def top_k_agreement(cited, phi, tol=TIE_TOL):
    """Fraction of cited records that rank in the top-|C| by Shapley value.

    Tie-inclusive: a record tied with the k-th largest value counts as top-k.
    """
    k = len(cited)
    if k == 0:
        return None
    ranked = sorted(phi.values(), reverse=True)
    cutoff = ranked[k - 1] - tol
    top = {p for p, val in phi.items() if val >= cutoff}
    return sum(1 for p in cited if p in top) / k


def citation_consistency(v, cited, players, phi=None, tol=TIE_TOL):
    """Score one citation set against the behavioral lattice.

    Empty and all-record citation sets are separate categories. For them the
    necessity and sufficiency values follow trivially from the definitions,
    there is no same-size alternative to compare against, and they are
    excluded from the beat-fraction metrics.
    """
    c = frozenset(cited)
    players = tuple(players)
    unknown = c - set(players)
    if unknown:
        raise ValueError(f"cited records not in players: {sorted(unknown)}")
    if phi is None:
        phi = shapley(v, players)
    result = {
        "cited": [p for p in players if p in c],
        "size": len(c),
        "necessity": necessity(v, c, players),
        "sufficiency": sufficiency(v, c, players),
        "beat_necessity": None,
        "beat_sufficiency": None,
        "n_alternatives": 0,
        "shapley_top_k_agreement": None,
        "tie_tolerance": tol,
    }
    if len(c) == 0:
        result["category"] = "empty"
        result["note"] = (
            "Empty citation: necessity is 0 and sufficiency is v(empty)-v(full) "
            "by definition. Reported separately; excluded from beat fractions."
        )
        return result
    if len(c) == len(players):
        result["category"] = "all"
        result["note"] = (
            "All-record citation: sufficiency is 0 and necessity is "
            "v(full)-v(empty) by definition. Reported separately; excluded "
            "from beat fractions."
        )
        return result
    result["category"] = "partial"
    alternatives = [
        frozenset(s) for s in combinations(players, len(c)) if frozenset(s) != c
    ]
    result["n_alternatives"] = len(alternatives)
    result["beat_necessity"] = beat_fraction(
        result["necessity"], [necessity(v, s, players) for s in alternatives], tol=tol
    )
    result["beat_sufficiency"] = beat_fraction(
        result["sufficiency"], [sufficiency(v, s, players) for s in alternatives], tol=tol
    )
    result["shapley_top_k_agreement"] = top_k_agreement(c, phi, tol=tol)
    return result


def spread(values):
    """Mean and min-max range across fixed orderings.

    With only three fixed orderings this is a description of ordering
    sensitivity, not a confidence interval.
    """
    vals = list(values)
    return {
        "per_ordering": vals,
        "mean": sum(vals) / len(vals),
        "min": min(vals),
        "max": max(vals),
        "range": max(vals) - min(vals),
    }
