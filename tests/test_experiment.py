"""Full-experiment preparation: gates, freeze, scenario validation, pipeline plumbing."""
import json
import shutil
from pathlib import Path

import pytest

import run_experiment
import run_feasibility
from mxr import checks, design, metrics
from mxr.analysis import analyze
from mxr.mock import DesignMockScorer, MockLabelScorer
from mxr.pipeline import greedy_stage, repeat_stage, scoring_stage, tokenization_stage
from mxr.scenario_validation import (EXPERIMENT_SCENARIOS, FROZEN_FILES, ROOT, validate,
                                     verify_freeze)

SCEN = {s: json.loads((ROOT / "scenarios" / f"{s}.json").read_text()) for s in EXPERIMENT_SCENARIOS}


def _good_labels(tmp_path):
    from tests.test_labels import complete_labels, write
    return write(tmp_path, complete_labels("Alice Example"), complete_labels("Bob Example"))


# ---------- freeze and scenario validation ----------
def test_all_frozen_files_match_freeze():
    ok, bad = verify_freeze()
    assert ok, bad


def test_freeze_detects_tampering(tmp_path):
    root = tmp_path / "pkg"
    for rel in FROZEN_FILES + ("scenarios/FREEZE.json",):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, root / rel)
    assert verify_freeze(root)[0]
    p = root / "scenarios" / "macro_b.json"
    p.write_text(p.read_text().replace("6.8%", "6.9%"))
    ok, bad = verify_freeze(root)
    assert not ok and bad == ["scenarios/macro_b.json"]


def test_every_scenario_validates_offline():
    crit = checks.load_criteria()
    rubric = json.loads((ROOT / "scenarios" / "rubric_macro_v1.json").read_text())
    for sid in EXPERIMENT_SCENARIOS:
        _, issues, info = validate(sid, crit, rubric)
        assert not issues, (sid, issues)


def test_s_single_unchanged_from_feasibility_runs():
    run2 = json.loads((ROOT / "runs" / "s_single_20261017T204445Z" / "manifest.json").read_text())
    assert design.design_fingerprint(SCEN["s_single"]) == run2["design_fingerprint"]


def test_code_constants_equal_frozen_criteria():
    c = checks.load_criteria()
    assert c["infrastructure"]["LABEL_MASS_MIN"] == checks.LABEL_MASS_MIN
    assert c["infrastructure"]["GREEDY_MARGIN_MIN"] == checks.GREEDY_MARGIN_MIN
    assert c["infrastructure"]["REPEAT_TOL"] == checks.REPEAT_TOL
    assert c["infrastructure"]["FIRST_TOKEN_RECOMPUTE_TOL"] == checks.FIRST_TOKEN_RECOMPUTE_TOL
    sd = c["single_decisive"]
    assert (sd["DESIGNED_AGREEMENT_MIN"], sd["DECISIVE_SHARE_MIN"], sd["DISTRACTOR_ABS_MAX"]) == (
        checks.DESIGNED_AGREEMENT_MIN, checks.DECISIVE_SHARE_MIN, checks.DISTRACTOR_ABS_MAX)
    assert c["descriptive"]["SHAPLEY_RANGE_FLAG"] == checks.SHAPLEY_RANGE_FLAG


def test_rubric_reference_answers_and_flips():
    expect = {"macro_a": ("Positive", "Neutral"), "macro_b": ("Negative", "Neutral"),
              "macro_c": ("Negative", "Neutral")}
    full = frozenset(design.CANONICAL)
    for sid, (ref, flip) in expect.items():
        assert design.designed_answer(SCEN[sid], full) == ref
        assert design.designed_answer(SCEN[sid], full, flipped=True) == flip


# ---------- gates ----------
def test_real_run_requires_labels_and_confirmation(tmp_path, monkeypatch):
    from mxr.labels import blank_labeler_file
    from tests.test_labels import write
    real_gate = run_experiment.label_gate
    blank = write(tmp_path / "blank", blank_labeler_file(), blank_labeler_file())
    monkeypatch.setattr(run_experiment, "label_gate", lambda: real_gate(blank))
    assert run_experiment.main(["--out", str(tmp_path)]) == 6          # incomplete labels
    monkeypatch.setattr(run_experiment, "label_gate", real_gate)       # shipped AI label files
    assert run_experiment.main(["--out", str(tmp_path)]) == 7          # no confirmation
    assert run_experiment.main(["--out", str(tmp_path), "--confirm-full-run"]) == 7  # no approver
    assert not any(p.name.startswith("full_") for p in tmp_path.iterdir())


def test_skip_label_gate_refused_for_real_backend(tmp_path):
    assert run_experiment.main(["--out", str(tmp_path), "--skip-label-gate"]) == 6


# ---------- pipeline ----------
def test_pipeline_matches_feasibility_runner_on_s_single(tmp_path):
    sc = MockLabelScorer(decisive_text=SCEN["s_single"]["records"]["E2"])
    run_feasibility.main(["--out", str(tmp_path), "--run-id", "feas"], scorer=sc)
    feas = [json.loads(l) for l in (tmp_path / "feas" / "cells.jsonl").read_text().splitlines()]
    cells = scoring_stage(sc, SCEN["s_single"], log=None)
    assert [c["score"] for c in cells] == [c["score"] for c in feas]
    assert [c["user_msg"] for c in cells] == [c["user_msg"] for c in feas]
    a_feas = json.loads((tmp_path / "feas" / "analysis.json").read_text())
    assert json.loads(json.dumps(analyze(cells, SCEN["s_single"]), default=str)) == a_feas


def test_full_mock_run_end_to_end(tmp_path):
    code = run_experiment.main(["--backend", "mock", "--skip-label-gate", "--out", str(tmp_path),
                                "--run-id", "m"])
    assert code == 0
    run = tmp_path / "m"
    summary = json.loads((run / "summary.json").read_text())
    assert [r["scenario_id"] for r in summary] == list(EXPERIMENT_SCENARIOS)
    for r in summary:
        assert r["infrastructure_pass"] and r["behavioral_pass"] in (True, None)
        assert r["d_star"] == r["designed_or_reference"]
        c = r["citations"]
        assert c["n_sampled"] == 10 and len(c["greedy"]) == 3
        assert set(c["status_counts_sampled"]) <= {"ok", "empty", "unparseable", "invalid_id"}
        sdir = run / r["scenario_id"]
        cit = [json.loads(l) for l in (sdir / "citations.jsonl").read_text().splitlines()]
        seeds = [x["seed"] for x in cit if x["kind"] == "sampled"]
        idx = list(EXPERIMENT_SCENARIOS).index(r["scenario_id"])
        assert seeds == [10000 + 100 * idx + i for i in range(10)]
        assert [x["ordering"] for x in cit if x["kind"] == "sampled"] == [0] * 4 + [1] * 3 + [2] * 3
        assert all(x["decision_in_context"] == r["d_star"] for x in cit)
        for x in cit:
            if x["parse"]["status"] in ("ok", "empty"):
                assert x["consistency"]["tie_tolerance"] == metrics.FULL_RUN_TIE_TOL
        if SCEN[r["scenario_id"]]["kind"] == "realistic":
            assert r["flip"]["moved_away_all_orderings"] is True
            assert len((sdir / "flips.jsonl").read_text().splitlines()) == 3
    man = json.loads((run / "manifest.json").read_text())
    assert man["status"] == "completed" and man["gates"]["G1_freeze"] is True
    assert man["rubric_validation"]["human_annotation"] is False
    assert man["rubric_validation"]["provenance_sha256"]
    assert "not human annotation" in (run / "SUMMARY.md").read_text()
    assert man["analysis_parameters"]["tie_tolerance"] == 0.01


def test_tiny_hf_model_runs_two_scenarios_with_citations(tmp_path):
    pytest.importorskip("torch")
    from tests.tiny_hf import tiny_scorer

    code = run_experiment.main(["--skip-label-gate", "--out", str(tmp_path), "--run-id", "tiny",
                                "--scenarios", "s_conflict", "macro_a"],
                               scorer=tiny_scorer(300, arch="phi3", storage="float16", compute="float32"))
    summary = json.loads((tmp_path / "tiny" / "summary.json").read_text())
    assert [r["scenario_id"] for r in summary] == ["s_conflict", "macro_a"]
    for r in summary:
        assert r["citations"]["n_sampled"] == 10
        fails = set(r["failed_checks"])
        assert {"I1", "I2", "I3", "I6", "I7", "I8", "I9"}.isdisjoint(fails), fails
    assert code == 1  # a random model cannot pass label mass / recovery checks


def test_tokenization_stage_covers_flip_prompts():
    rows, lattice, ok = tokenization_stage(DesignMockScorer(list(SCEN.values())), SCEN["macro_a"])
    assert ok and len(lattice) == 48 and len(rows) == 51 and sum(r["flipped"] for r in rows) == 3


def test_redundant_and_conflict_checks_discriminate():
    crit = checks.load_criteria()
    from mxr.scenario_validation import _ideal_cells, _swap_roles, _violating_cells
    for sid in ("s_redundant", "s_conflict"):
        sc = SCEN[sid]
        assert all(c["passed"] for c in checks.behavioral_checks(analyze(_ideal_cells(sc), sc), sc, crit))
        assert not all(c["passed"] for c in checks.behavioral_checks(analyze(_violating_cells(sc), sc), sc, crit))
        assert not all(c["passed"] for c in checks.behavioral_checks(analyze(_ideal_cells(_swap_roles(sc)), sc), sc, crit))
