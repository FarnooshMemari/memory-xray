"""End-to-end runner tests: MOCK scorer (rule-following and evidence-blind) and tiny HF model."""
import json

import pytest

import run_feasibility
from mxr.mock import MockLabelScorer

SCEN = json.loads((run_feasibility.HERE / "scenarios" / "s_single.json").read_text())


def _read(run_dir):
    checks = json.loads((run_dir / "checks.json").read_text())
    cells = [json.loads(l) for l in (run_dir / "cells.jsonl").read_text().splitlines()]
    return checks, cells


def test_mock_rule_follower_passes_everything(tmp_path):
    sc = MockLabelScorer(decisive_text=SCEN["records"]["E2"])
    code = run_feasibility.main(["--out", str(tmp_path), "--run-id", "mock_ok"], scorer=sc)
    checks, cells = _read(tmp_path / "mock_ok")
    assert code == 0 and len(cells) == 48
    assert all(c["passed"] for c in checks["infrastructure"] + checks["behavioral"])
    report = (tmp_path / "mock_ok" / "REPORT.md").read_text()
    assert report.startswith("> **MOCK RUN.**")


def test_reanalysis_reproduces_saved_analysis(tmp_path):
    import reanalyze

    sc = MockLabelScorer(decisive_text=SCEN["records"]["E2"])
    run_feasibility.main(["--out", str(tmp_path), "--run-id", "re"], scorer=sc)
    before = sorted(p.name for p in (tmp_path / "re").iterdir())
    code, out = reanalyze.main(str(tmp_path / "re"))
    assert code == 0 and out.parent == tmp_path
    assert sorted(p.name for p in (tmp_path / "re").iterdir()) == before  # run folder untouched
    a = json.loads((tmp_path / "re" / "analysis.json").read_text())
    b = json.loads((out / "analysis.json").read_text())
    assert a == b


def test_evidence_blind_mock_fails_behavioral_checks(tmp_path):
    sc = MockLabelScorer(decisive_text="text that never appears")
    code = run_feasibility.main(["--out", str(tmp_path), "--run-id", "mock_blind"], scorer=sc)
    checks, _ = _read(tmp_path / "mock_blind")
    assert code == 1
    assert all(c["passed"] for c in checks["infrastructure"])
    failed = {c["id"] for c in checks["behavioral"] if not c["passed"]}
    assert {"B1", "B2", "B5"} <= failed


def test_refuses_to_overwrite_existing_run(tmp_path):
    sc = MockLabelScorer(decisive_text=SCEN["records"]["E2"])
    run_feasibility.main(["--out", str(tmp_path), "--run-id", "same"], scorer=sc)
    with pytest.raises(FileExistsError):
        run_feasibility.main(["--out", str(tmp_path), "--run-id", "same"], scorer=sc)


def test_tiny_hf_model_end_to_end(tmp_path):
    pytest.importorskip("torch")
    from tests.tiny_hf import tiny_scorer

    code = run_feasibility.main(["--out", str(tmp_path), "--run-id", "tiny"], scorer=tiny_scorer(300))
    checks, cells = _read(tmp_path / "tiny")
    infra = {c["id"]: c for c in checks["infrastructure"]}
    assert len(cells) == 48
    for cid in ("I1", "I2", "I3", "I6", "I7"):
        assert infra[cid]["passed"], (cid, infra[cid]["detail"])
    # A random model puts almost no mass on the three labels, so its greedy
    # output is not a label either: I4 and I5 must both catch that. (Indexing
    # agreement with generate() is tested directly in test_scoring_hf.py.)
    assert not infra["I4"]["passed"]
    assert not infra["I5"]["passed"]
    assert code == 1


def test_tiny_phi3_float16_math_fails_I3_and_float32_compute_passes(tmp_path):
    """Pipeline-level reproduction of run 1 (float16 math) and of the amendment-1 fix."""
    pytest.importorskip("torch")
    from tests.tiny_hf import tiny_scorer

    run_feasibility.main(["--out", str(tmp_path), "--run-id", "f16"],
                         scorer=tiny_scorer(300, arch="phi3", max_logit=50.0,
                                            storage="float16", compute="float16"))
    run_feasibility.main(["--out", str(tmp_path), "--run-id", "f32c"],
                         scorer=tiny_scorer(300, arch="phi3", max_logit=50.0,
                                            storage="float16", compute="float32"))
    f16 = {c["id"]: c["passed"] for c in _read(tmp_path / "f16")[0]["infrastructure"]}
    f32c = {c["id"]: c["passed"] for c in _read(tmp_path / "f32c")[0]["infrastructure"]}
    assert f16["I3"] is False and f16["I9"] is False
    assert f32c["I3"] is True and f32c["I9"] is True
    for cid in ("I1", "I2", "I6", "I7", "I8"):
        assert f32c[cid], cid
