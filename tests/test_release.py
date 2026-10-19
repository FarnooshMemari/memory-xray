"""Tests for files added in the public release (see CHANGES.md). CPU only, no model.

They check the release tooling against the saved results; none of them changes a saved file.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "full_20261017T223452Z"
sys.path.insert(0, str(ROOT / "analysis_full"))
sys.path.insert(0, str(ROOT / "scripts"))


def _scenario(sid):
    return json.loads((ROOT / "scenarios" / f"{sid}.json").read_text())


@pytest.mark.parametrize("sid, expected", [
    ("s_single", ["E2"]),
    ("s_redundant", ["E1", "E3"]),          # largest member of the designed faithful family
    ("s_conflict", ["E1"]),
    ("macro_a", ["E1", "E2", "E4"]),        # rubric +1 records; reference Positive
    ("macro_b", ["E1", "E2", "E4"]),        # rubric -1 records; reference Negative
    ("macro_c", ["E2", "E3", "E4"]),        # rubric -1 records; reference Negative (rate cut E1 excluded)
])
def test_content_only_rule_never_uses_model_behavior(sid, expected):
    from content_only_baseline import content_only_set
    sc = _scenario(sid)
    assert content_only_set(sc) == expected


def test_content_only_baseline_json_is_reproducible(tmp_path, monkeypatch):
    import content_only_baseline as cob
    fake_root = tmp_path / "repo"
    for rel in ("results/reanalysis.json", "results/report_numbers.json"):
        (fake_root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, fake_root / rel)
    shutil.copytree(ROOT / "scenarios", fake_root / "scenarios")
    monkeypatch.setattr(cob, "ROOT", fake_root)
    cob.main()
    new = (fake_root / "results/post_hoc/content_only_baseline.json").read_text()
    assert new == (ROOT / "results/post_hoc/content_only_baseline.json").read_text()
    data = json.loads(new)
    cmp_ = data["pooled"]["scenario_metric_comparisons"]
    assert (cmp_["content_only_ge_model"], cmp_["of"]) == (17, 18)
    assert [(e["scenario"], e["metric"]) for e in cmp_["exceptions"]] == [("s_redundant", "mean_beat_suf")]


def test_reanalyze_full_run_scenario_folder_uses_run_root_manifest(tmp_path):
    """The original reanalyze.py failed here with FileNotFoundError (no manifest.json in scenario folders)."""
    import reanalyze
    assert not (RUN / "s_conflict" / "manifest.json").exists()
    before = sorted(p.name for p in (RUN / "s_conflict").iterdir())
    code = reanalyze.main([str(RUN / "s_conflict"), "--out", str(tmp_path / "out")])
    assert code == 0                                    # recomputed checks equal the saved ones
    saved = json.loads((RUN / "s_conflict" / "checks.json").read_text())
    new = json.loads((tmp_path / "out" / "s_conflict" / "checks.json").read_text())
    assert [(c["id"], c["passed"]) for c in new["behavioral"]] == [(c["id"], c["passed"]) for c in saved["behavioral"]]
    assert {c["id"] for c in new["behavioral"] if not c["passed"]} == {"BC1", "BC3", "BC4", "BC5"}
    assert sorted(p.name for p in (RUN / "s_conflict").iterdir()) == before   # saved run untouched


def test_reanalyze_whole_full_run(tmp_path):
    import reanalyze
    assert reanalyze.main([str(RUN), "--out", str(tmp_path / "all")]) == 0
    assert sorted(p.name for p in (tmp_path / "all").iterdir()) == sorted(
        json.loads((RUN / "manifest.json").read_text())["scenarios"])


def test_compare_runs_identical_and_detects_differences(tmp_path, capsys):
    import compare_runs
    assert compare_runs.main([str(RUN)]) == 0
    copy = tmp_path / "full_copy"
    shutil.copytree(RUN, copy)
    # perturb one cell probability: reported; accepted within --tol, rejected above it
    cells = (copy / "macro_b" / "cells.jsonl").read_text().splitlines()
    c0 = json.loads(cells[0])
    c0["score"]["p_norm"]["Neutral"] += 0.005
    (copy / "macro_b" / "cells.jsonl").write_text("\n".join([json.dumps(c0)] + cells[1:]) + "\n")
    out = tmp_path / "cmp.json"
    assert compare_runs.main([str(copy), "--json", str(out)]) == 0
    assert abs(json.loads(out.read_text())["macro_b"]["max_abs_diff_p_norm"] - 0.005) < 1e-9
    assert compare_runs.main([str(copy), "--tol", "0.001"]) == 1
    # a missing cell is detected
    (copy / "macro_b" / "cells.jsonl").write_text("\n".join([json.dumps(c0)] + cells[1:-1]) + "\n")
    assert compare_runs.main([str(copy)]) == 1
    (copy / "macro_b" / "cells.jsonl").write_text("\n".join([json.dumps(c0)] + cells[1:]) + "\n")
    # flip one check outcome: must be detected
    ch = json.loads((copy / "s_single" / "checks.json").read_text())
    ch["behavioral"][0]["passed"] = not ch["behavioral"][0]["passed"]
    (copy / "s_single" / "checks.json").write_text(json.dumps(ch))
    assert compare_runs.main([str(copy)]) == 1
    assert "check outcomes differ" in capsys.readouterr().out


def test_key_numbers_file_matches_results():
    import make_key_numbers
    assert make_key_numbers.main(["--check"]) == 0


def test_original_package_files_are_preserved():
    import verify_release
    verify_release.RESULTS.clear()
    verify_release.check_original_files()
    verify_release.check_run_sums()
    assert all(r["passed"] for r in verify_release.RESULTS), verify_release.RESULTS


def test_original_files_check_detects_a_changed_edited_file(tmp_path, monkeypatch):
    import verify_release
    fake_root = tmp_path / "repo"
    shutil.copytree(ROOT, fake_root, ignore=shutil.ignore_patterns("outputs", ".git", "__pycache__", ".pytest_cache"))
    monkeypatch.setattr(verify_release, "ROOT", fake_root)
    verify_release.RESULTS.clear()
    verify_release.check_original_files()
    assert verify_release.RESULTS[-1]["passed"], verify_release.RESULTS
    report = fake_root / "results" / "RESULTS_AND_DISCUSSION.md"
    report.write_text(report.read_text() + "\n")
    verify_release.RESULTS.clear()
    verify_release.check_original_files()
    assert not verify_release.RESULTS[-1]["passed"]
    assert "results/RESULTS_AND_DISCUSSION.md" in verify_release.RESULTS[-1]["detail"]
