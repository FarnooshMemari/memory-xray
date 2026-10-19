import math

import pytest

from mxr.design import all_subsets
from mxr.metrics import (beat_fraction, citation_consistency, leave_one_out, necessity,
                         shapley, spread, sufficiency, top_k_agreement)

P = ("E1", "E2", "E3", "E4")


def game(fn):
    return {s: fn(s) for s in all_subsets(P)}


def test_efficiency_on_arbitrary_game():
    vals = [0.11, 0.5, 0.2, 0.9, 0.33, 0.47, 0.05, 0.6, 0.71, 0.18, 0.29, 0.82, 0.4, 0.66, 0.13, 0.95]
    v = dict(zip(all_subsets(P), vals))
    phi = shapley(v, P)
    assert math.isclose(sum(phi.values()), v[frozenset(P)] - v[frozenset()], abs_tol=1e-12)


def test_additive_game_recovers_weights_and_null_player_is_zero():
    w = {"E1": 0.0, "E2": 0.6, "E3": 0.1, "E4": -0.2}
    v = game(lambda s: 0.3 + sum(w[p] for p in s))
    phi = shapley(v, P)
    for p in P:
        assert math.isclose(phi[p], w[p], abs_tol=1e-12)
    assert math.isclose(phi["E1"], 0.0, abs_tol=1e-12)


def test_single_decisive_game():
    v = game(lambda s: 0.9 if "E2" in s else 0.1)
    phi = shapley(v, P)
    assert math.isclose(phi["E2"], 0.8) and all(abs(phi[p]) < 1e-12 for p in ("E1", "E3", "E4"))


def test_redundant_pair_splits_credit_and_loo_misses_it():
    v = game(lambda s: 0.9 if ("E1" in s or "E2" in s) else 0.1)
    phi = shapley(v, P)
    loo = leave_one_out(v, P)
    assert math.isclose(phi["E1"], 0.4) and math.isclose(phi["E2"], 0.4)
    assert loo["E1"] == 0 and loo["E2"] == 0


def test_symmetry():
    v = game(lambda s: 0.2 + 0.3 * ("E3" in s) * ("E4" in s))
    phi = shapley(v, P)
    assert math.isclose(phi["E3"], phi["E4"]) and math.isclose(phi["E3"], 0.15)


def test_necessity_and_sufficiency_definitions():
    v = game(lambda s: 0.9 if "E2" in s else 0.1)
    assert math.isclose(necessity(v, {"E2"}, P), 0.8)
    assert math.isclose(sufficiency(v, {"E2"}, P), 0.0)
    assert math.isclose(necessity(v, {"E1"}, P), 0.0)
    assert math.isclose(sufficiency(v, {"E1"}, P), -0.8)


def test_beat_fraction_with_ties():
    assert beat_fraction(0.5, [0.1, 0.5, 0.9]) == pytest.approx(0.5)
    assert beat_fraction(1.0, [0.1, 0.2, 0.3]) == 1.0
    assert beat_fraction(0.0, []) is None


def test_top_k_agreement_tie_inclusive():
    phi = {"E1": 0.5, "E2": 0.5, "E3": 0.0, "E4": 0.0}
    assert top_k_agreement({"E1"}, phi) == 1.0
    assert top_k_agreement({"E3"}, phi) == 0.0
    assert top_k_agreement(set(), phi) is None


def test_citation_consistency_categories():
    v = game(lambda s: 0.9 if "E2" in s else 0.1)
    empty = citation_consistency(v, set(), P)
    allr = citation_consistency(v, set(P), P)
    good = citation_consistency(v, {"E2"}, P)
    bad = citation_consistency(v, {"E1"}, P)
    assert empty["category"] == "empty" and empty["beat_necessity"] is None
    assert math.isclose(empty["necessity"], 0.0) and math.isclose(empty["sufficiency"], -0.8)
    assert allr["category"] == "all" and allr["beat_sufficiency"] is None
    assert math.isclose(allr["sufficiency"], 0.0) and math.isclose(allr["necessity"], 0.8)
    assert good["category"] == "partial" and good["n_alternatives"] == 3
    assert good["beat_necessity"] == 1.0 and good["beat_sufficiency"] == 1.0
    assert good["shapley_top_k_agreement"] == 1.0
    assert bad["beat_necessity"] == pytest.approx(1 / 3)  # ties with E3, E4; loses to E2
    with pytest.raises(ValueError):
        citation_consistency(v, {"E9"}, P)


def test_size_two_null_has_five_alternatives():
    v = game(lambda s: 0.9 if "E2" in s else 0.1)
    r = citation_consistency(v, {"E2", "E3"}, P)
    assert r["n_alternatives"] == 5


def test_spread_is_min_max_not_ci():
    s = spread([0.1, 0.3, 0.2])
    assert s["mean"] == pytest.approx(0.2) and s["range"] == pytest.approx(0.2)
    assert set(s) == {"per_ordering", "mean", "min", "max", "range"}
