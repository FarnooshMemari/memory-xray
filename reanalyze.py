#!/usr/bin/env python3
"""Recompute analysis, checks and report from a saved run (no model needed).

Usage:
  python reanalyze.py runs/<feasibility_run>                      # single-scenario feasibility run
  python reanalyze.py runs/full_20261017T223452Z                  # every scenario of the full run
  python reanalyze.py runs/full_20261017T223452Z/macro_a          # one scenario of the full run
  python reanalyze.py <run> --out <dir>                           # choose the output folder

Outputs go to outputs/reanalysis/<run>__<UTC time>/ by default (outside runs/, so the saved run
folders are never modified). For each scenario the recomputed checks are compared with the saved
checks.json and the result is printed. Exit code 0 means every recomputed check outcome equals the
saved one (a run whose checks FAILED, such as feasibility run 1, still exits 0 if it reproduces).

Python API kept from the original script: main("<run folder>") reanalyzes one feasibility run, writes a sibling
folder <run>__reanalysis_<UTC>, and returns (0 if all checks pass else 1, output folder).

Publication copy, changed from the original file preserved in records/original_package/replaced_files/ (see CHANGES.md):
  * The full run keeps ONE manifest.json at the run root; its scenario folders have none. The original
    script required <folder>/manifest.json and so failed on every full-run scenario with
    FileNotFoundError. It now reads the run-root manifest for full-run scenarios and uses the same
    settings as run_experiment.py (tie tolerance, frozen criteria, lattice-only tokenization rows).
  * Command-line output moved from a sibling folder inside runs/ to outputs/ (git-ignored); the original
    Python call main("<run folder>") keeps its original behavior and return value.
  * Recomputed checks are compared with the saved ones.

The lattice analysis, checks and the analysis part of REPORT.md are recomputed. Flip and citation results
are not recomputed here; analysis_full/independent_reanalysis.py recomputes those (and everything else)
with separate code.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from mxr import checks, design  # noqa: E402
from mxr.analysis import analyze  # noqa: E402
from mxr.metrics import FULL_RUN_TIE_TOL  # noqa: E402
from mxr.report import render_report  # noqa: E402


def _jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _scenario(sid):
    return json.loads((HERE / "scenarios" / f"{sid}.json").read_text())


def _strip(cs):
    """Comparable form of a check list: id -> passed."""
    return {c["id"]: c["passed"] for c in cs}


def _common(d, scenario, manifest, expected_fp, full_run):
    if design.design_fingerprint(scenario) != expected_fp:
        print(f"WARNING [{scenario['scenario_id']}]: design fingerprint differs from the run's; the scenario "
              "or a prompt constant changed since this run.")
    cells = _jsonl(d / "cells.jsonl")
    tokval = json.loads((d / "tokenization_validation.json").read_text())
    greedy = _jsonl(d / "greedy_check.jsonl")
    repeat = json.loads((d / "repeatability.json").read_text())
    if full_run:
        crit = checks.load_criteria()
        analysis = analyze(cells, scenario, tie_tol=FULL_RUN_TIE_TOL)
        lattice_rows = [t for t in tokval if not t.get("flipped")]
        infra = checks.infrastructure_checks(cells, lattice_rows, greedy, repeat, manifest.get("scorer"))
        behavioral = checks.behavioral_checks(analysis, scenario, crit)
        flags = checks.descriptive_flags(analysis, scenario, crit)
    else:
        analysis = analyze(cells, scenario)
        infra = checks.infrastructure_checks(cells, tokval, greedy, repeat, manifest.get("scorer"))
        behavioral = checks.behavioral_checks_single(analysis, scenario)
        flags = checks.descriptive_flags(analysis, scenario)
    return cells, analysis, infra, behavioral, flags


def reanalyze_folder(d, out):
    """Reanalyze one scenario folder (feasibility run root, or full-run scenario folder) into `out`.

    Returns (recomputed checks equal the saved checks, all recomputed checks pass, out)."""
    d = Path(d)
    if (d / "manifest.json").exists():               # feasibility run: manifest in the folder itself
        manifest = json.loads((d / "manifest.json").read_text())
        sid, full_run = manifest["scenario_id"], False
        expected_fp = manifest["design_fingerprint"]
        sman = manifest
        title = None
    elif (d.parent / "manifest.json").exists():      # full run: one manifest at the run root
        manifest = json.loads((d.parent / "manifest.json").read_text())
        sid, full_run = d.name, True
        if sid not in manifest.get("design_fingerprints", {}):
            raise SystemExit(f"{d}: not a scenario of run {manifest.get('run_id')}")
        expected_fp = manifest["design_fingerprints"][sid]
        sman = dict(manifest, run_id=f"{manifest['run_id']}/{sid}", design_fingerprint=expected_fp)
        title = "Full experiment (reanalysis)"
    else:
        raise SystemExit(f"{d}: no manifest.json in the folder or its parent")
    scenario = _scenario(sid)
    cells, analysis, infra, behavioral, flags = _common(d, scenario, manifest, expected_fp, full_run)
    sman = dict(sman, n_cells=len(cells), n_forward_passes=sum(c["score"]["n_forward"] for c in cells))

    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "analysis.json").write_text(json.dumps(analysis, indent=2, default=str))
    (out / "checks.json").write_text(json.dumps(
        {"infrastructure": infra, "behavioral": behavioral, "flags": flags}, indent=2, default=str))
    report = render_report(sman, infra, behavioral, flags, analysis, **({"title": title} if title else {}))
    (out / "REPORT.md").write_text(report)

    saved = json.loads((d / "checks.json").read_text())
    saved_all = {**_strip(saved["infrastructure"]), **_strip(saved["behavioral"])}
    now_all = {**_strip(infra), **_strip(behavioral)}
    added = sorted(set(now_all) - set(saved_all))     # checks added by a later protocol amendment
    same = set(saved_all) <= set(now_all) and all(now_all[k] == v for k, v in saved_all.items())
    failed = [c["id"] for c in infra + behavioral if not c["passed"]]

    def status(cs):
        if not cs:
            return "n/a"
        bad = [c["id"] for c in cs if not c["passed"] and c["id"] not in added]
        later = [c["id"] for c in cs if not c["passed"] and c["id"] in added]
        txt = "PASS" if not bad else f"FAIL ({', '.join(bad)})"
        if later:
            txt += f" [{', '.join(later)} not defined when this run was made]"
        return txt

    note = (f"; checks {', '.join(added)} were added by a later amendment and are not compared") if added else ""
    print(f"{sid:12s} infrastructure {status(infra)}; recovery checks {status(behavioral)}; d*={analysis['d_star']}; "
          f"matches saved checks.json: {same}{note}")
    return same, not failed, out


def main(argv=None):
    if isinstance(argv, (str, Path)):                # original Python API (used by tests/test_pipeline.py)
        d = Path(argv)
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        _, passed, out = reanalyze_folder(d, d.parent / f"{d.name}__reanalysis_{stamp}")
        print(f"{'PASS' if passed else 'FAIL'}: wrote {out}")
        return (0 if passed else 1), out

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run")
    ap.add_argument("--out", default=None, help="output folder (default outputs/reanalysis/<run>__<UTC>)")
    a = ap.parse_args(argv)
    d = Path(a.run).resolve()
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    name = d.name if (d / "manifest.json").exists() or not (d.parent / "manifest.json").exists() else f"{d.parent.name}_{d.name}"
    out_root = Path(a.out) if a.out else HERE / "outputs" / "reanalysis" / f"{name}__{stamp}"
    if (d / "manifest.json").exists() and json.loads((d / "manifest.json").read_text()).get("scenarios"):
        folders = [d / sid for sid in json.loads((d / "manifest.json").read_text())["scenarios"]]   # whole full run
    else:
        folders = [d]
    # feasibility run -> out_root itself; full-run scenario folder -> out_root/<scenario>
    results = [reanalyze_folder(f, out_root if (f / "manifest.json").exists() else out_root / f.name) for f in folders]
    ok = all(same for same, _, _ in results)
    print(f"{'ALL RECOMPUTED CHECKS MATCH THE SAVED RUN' if ok else 'MISMATCH WITH THE SAVED RUN'}; wrote {out_root}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
