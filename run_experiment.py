#!/usr/bin/env python3
"""Full experiment (protocol v0.2, amendments 1-2): six frozen scenarios.

Per scenario: tokenization validation, 48 scoring cells, greedy cross-check,
repeatability, analysis and frozen checks; flip cells (realistic scenarios);
citation elicitation (3 greedy references + 10 seeded samples).

Gates, checked before anything is loaded or scored:
  G1  every frozen file matches scenarios/FREEZE.json
  G2  two distinct labelers, each in a separate file (records/labels/), gave
      complete, rubric-valid record scores, flip scores and signals, and their
      signals match the frozen reference answers (see mxr/labels.py)
  G3  explicit confirmation: --confirm-full-run --approved-by "<name>"
  G4  the pinned model commit loads and verifies (checks I8 and I9)

  python run_experiment.py --confirm-full-run --approved-by "Name"
  python run_experiment.py --backend mock --skip-label-gate   # pipeline exercise only
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from mxr import checks, design  # noqa: E402
from mxr.analysis import analyze  # noqa: E402
from mxr.citation_analysis import score_citations, summarize  # noqa: E402
from mxr.pipeline import (citation_stage, flip_stage, greedy_stage, repeat_stage,  # noqa: E402
                          scoring_stage, tokenization_stage)
from mxr.labels import RUBRIC_VALIDATION, label_gate  # noqa: E402,F401  (G2; name kept for tests)
from mxr.metrics import FULL_RUN_TIE_TOL  # noqa: E402
from mxr.report import render_report  # noqa: E402
from mxr.scenario_validation import EXPERIMENT_SCENARIOS, SCEN_DIR, verify_freeze  # noqa: E402
from mxr.scoring import PINNED_MODEL, PINNED_REVISION, RevisionError  # noqa: E402



def _sha256_or_none(path):
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def _dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, default=str))


def _jsonl(path, rows):
    with path.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r, default=str) + "\n")


def parse_args(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--backend", choices=["hf", "mock"], default="hf")
    ap.add_argument("--model", default=PINNED_MODEL)
    ap.add_argument("--revision", default=PINNED_REVISION)
    ap.add_argument("--storage-dtype", default="auto")
    ap.add_argument("--compute-dtype", default="float32")
    ap.add_argument("--device", default=None)
    ap.add_argument("--attn", default="eager")
    ap.add_argument("--scenarios", nargs="+", default=list(EXPERIMENT_SCENARIOS),
                    help="subset for testing only; a full run uses all six in the frozen order")
    ap.add_argument("--out", default=str(HERE / "runs"))
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--confirm-full-run", action="store_true")
    ap.add_argument("--approved-by", default=None)
    ap.add_argument("--skip-label-gate", action="store_true", help="allowed only with --backend mock")
    return ap.parse_args(argv)


def main(argv=None, scorer=None):
    args = parse_args(argv)
    is_mock_run = args.backend == "mock" or (scorer is not None and scorer.meta.get("backend") == "MOCK")

    # G1: freeze
    freeze_ok, mismatches = verify_freeze()
    if not freeze_ok:
        print(f"ABORTED (G1): frozen files changed: {mismatches}")
        return 4
    # G2: rubric labels
    if args.skip_label_gate and not is_mock_run and scorer is None:
        print("ABORTED: --skip-label-gate is only allowed with --backend mock")
        return 6
    labels_ok, labels_report = (True, {"skipped": True}) if args.skip_label_gate else label_gate()
    if not labels_ok:
        print("ABORTED (G2): rubric labeling incomplete or disagrees with the frozen reference answers:")
        for b in labels_report["blocking"]:
            print("  -", b)
        return 6
    # G3: explicit approval for a real run
    if args.backend == "hf" and scorer is None and not (args.confirm_full_run and args.approved_by):
        print("ABORTED (G3): a real full run needs --confirm-full-run and --approved-by \"<name>\"")
        return 7
    if list(args.scenarios) != list(EXPERIMENT_SCENARIOS) and args.backend == "hf" and scorer is None:
        print("ABORTED: a real full run must include all six scenarios in the frozen order")
        return 7

    # G4: model
    if scorer is None:
        if args.backend == "mock":
            from mxr.mock import DesignMockScorer

            scorer = DesignMockScorer([json.loads((SCEN_DIR / f"{s}.json").read_text())
                                       for s in EXPERIMENT_SCENARIOS])
        else:
            from mxr.scoring import HFLabelScorer

            try:
                scorer = HFLabelScorer.load(args.model, revision=args.revision,
                                            storage_dtype=args.storage_dtype,
                                            compute_dtype=args.compute_dtype, device=args.device,
                                            attn_implementation=args.attn)
            except RevisionError as exc:
                print(f"ABORTED (G4): the model commit could not be pinned/verified: {exc}")
                return 3
    if "logits_dtype" not in scorer.meta and hasattr(scorer, "precision_probe"):
        scorer.meta.update(scorer.precision_probe())

    crit = checks.load_criteria()
    cfg = crit["citations"]
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    is_mock = scorer.meta.get("backend") == "MOCK"
    run_id = args.run_id or f"full_{stamp}{'_MOCK' if is_mock else ''}"
    run_dir = Path(args.out) / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    scenarios = [json.loads((SCEN_DIR / f"{s}.json").read_text()) for s in args.scenarios]
    manifest = {
        "run_id": run_id, "protocol_version": "0.2", "protocol_amendments": [1, 2],
        "started_utc": stamp, "mock": is_mock,
        "gates": {"G1_freeze": freeze_ok, "G2_labels": labels_report,
                  "G3_approved_by": args.approved_by, "G3_confirmed": args.confirm_full_run},
        "freeze": json.loads((SCEN_DIR / "FREEZE.json").read_text()),
        "rubric_validation": dict(RUBRIC_VALIDATION, provenance_sha256=_sha256_or_none(
            HERE / RUBRIC_VALIDATION["provenance_file"])),
        "scenarios": [s["scenario_id"] for s in scenarios],
        "design_fingerprints": {s["scenario_id"]: design.design_fingerprint(s) for s in scenarios},
        "criteria_version": crit["criteria_version"], "citation_config": cfg,
        "analysis_parameters": {"tie_tolerance": FULL_RUN_TIE_TOL},
        "scorer": scorer.meta, "status": "running",
    }
    _dump(run_dir / "manifest.json", manifest)

    # Stage 1 for all scenarios before any scoring
    tok = {}
    for sc in scenarios:
        rows, lattice_rows, ok = tokenization_stage(scorer, sc)
        tok[sc["scenario_id"]] = (rows, lattice_rows)
        if not ok:
            manifest.update(status=f"aborted_at_tokenization:{sc['scenario_id']}")
            _dump(run_dir / "manifest.json", manifest)
            _dump(run_dir / f"tokenization_validation_{sc['scenario_id']}.json", rows)
            print(f"ABORTED before scoring: tokenization validation failed for {sc['scenario_id']}")
            return 2
    label_sets = {repr(sorted((k, tuple(v)) for k, v in r["label_ids"].items()))
                  for rows, _ in tok.values() for r in rows}
    if len(label_sets) != 1:
        manifest.update(status="aborted_at_tokenization:label_ids_differ_across_scenarios")
        _dump(run_dir / "manifest.json", manifest)
        print("ABORTED before scoring: label token ids differ across scenarios")
        return 2

    summary_rows = []
    t_all = time.time()
    for idx, sc in enumerate(scenarios):
        sid = sc["scenario_id"]
        print(f"\n=== {sid} ({idx + 1}/{len(scenarios)}) ===")
        t0 = time.time()
        sdir = run_dir / sid
        sdir.mkdir()
        rows, lattice_rows = tok[sid]
        _dump(sdir / "tokenization_validation.json", rows)
        max_len = max(len(v) for v in lattice_rows[0]["label_ids"].values())

        with (sdir / "cells.jsonl").open("w") as fh:
            cells = scoring_stage(scorer, sc, sink=lambda r: fh.write(json.dumps(r) + "\n"))
        greedy_rows = greedy_stage(scorer, cells, max_len)
        _jsonl(sdir / "greedy_check.jsonl", greedy_rows)
        repeat_rows = repeat_stage(scorer, cells)
        _dump(sdir / "repeatability.json", repeat_rows)

        analysis = analyze(cells, sc, tie_tol=FULL_RUN_TIE_TOL)
        infra = checks.infrastructure_checks(cells, lattice_rows, greedy_rows, repeat_rows, scorer.meta)
        behavioral = checks.behavioral_checks(analysis, sc, crit)
        flags = checks.descriptive_flags(analysis, sc, crit)

        flip_rows, flip_summary = [], None
        if "flip" in sc:
            flip_rows = flip_stage(scorer, sc, analysis, max_len)
            _jsonl(sdir / "flips.jsonl", flip_rows)
            flip_summary = {
                "target": sc["flip"]["target"],
                "argmax_per_ordering": [r["argmax"] for r in flip_rows],
                "moved_away_all_orderings": all(r["moved_away_from_d_star"] for r in flip_rows),
                "p_d_star_original": [r["p_d_star_original"] for r in flip_rows],
                "p_d_star_flipped": [r["p_d_star_flipped"] for r in flip_rows],
                "rubric_reference_flipped": sc["flip"]["reference_answer"],
                "diagnostics": {"all_finite": all(r["finite"] for r in flip_rows),
                                "min_label_mass": min(r["label_mass"] for r in flip_rows),
                                "greedy_matches": sum(r["greedy_token_match"] for r in flip_rows)},
            }

        cit_rows = citation_stage(scorer, sc, analysis, idx, cfg)
        scored = score_citations(cit_rows, analysis, tol=FULL_RUN_TIE_TOL)
        _jsonl(sdir / "citations.jsonl", scored)
        cit_summary = summarize(scored, sc)

        _dump(sdir / "analysis.json", analysis)
        _dump(sdir / "checks.json", {"infrastructure": infra, "behavioral": behavioral, "flags": flags})
        _dump(sdir / "flips_summary.json", flip_summary)
        _dump(sdir / "citation_summary.json", cit_summary)
        sman = dict(manifest, run_id=f"{run_id}/{sid}", design_fingerprint=design.design_fingerprint(sc),
                    n_cells=len(cells), n_forward_passes=sum(c["score"]["n_forward"] for c in cells))
        report = render_report(sman, infra, behavioral, flags, analysis, title="Full experiment")
        report += _flip_and_citation_section(flip_summary, cit_summary, sc)
        (sdir / "REPORT.md").write_text(report)

        infra_ok = all(c["passed"] for c in infra)
        beh_ok = all(c["passed"] for c in behavioral) if behavioral else None
        summary_rows.append({
            "scenario_id": sid, "kind": sc["kind"], "structure": sc["structure"],
            "d_star": analysis["d_star"], "designed_or_reference": analysis["designed_full_answer"],
            "infrastructure_pass": infra_ok, "behavioral_pass": beh_ok,
            "failed_checks": [c["id"] for c in infra + behavioral if not c["passed"]],
            "v_full_mean": analysis["v_full_spread"]["mean"], "v_empty_mean": analysis["v_empty_spread"]["mean"],
            "shapley_mean": {p: analysis["shapley_spread"][p]["mean"] for p in design.CANONICAL},
            "flags": flags, "flip": flip_summary, "citations": cit_summary,
            "elapsed_seconds": round(time.time() - t0, 1),
        })
        print(f"  infrastructure {'PASS' if infra_ok else 'FAIL'}; behavioral "
              f"{'n/a' if beh_ok is None else ('PASS' if beh_ok else 'FAIL')}; d*={analysis['d_star']}; "
              f"{time.time() - t0:.0f}s")

    manifest.update(status="completed", elapsed_seconds=round(time.time() - t_all, 1))
    _dump(run_dir / "manifest.json", manifest)
    _dump(run_dir / "summary.json", summary_rows)
    (run_dir / "SUMMARY.md").write_text(_summary_md(manifest, summary_rows))
    print(f"\nResults: {run_dir}")
    all_infra = all(r["infrastructure_pass"] for r in summary_rows)
    all_beh = all(r["behavioral_pass"] is not False for r in summary_rows)
    return 0 if (all_infra and all_beh) else 1


def _fmt(x, nd=2):
    return "n/a" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))


def _flip_and_citation_section(flip, cit, sc):
    L = [""]
    if flip:
        L += ["## Counterfactual flip", "",
              f"- Flipped record: {flip['target']} (rubric reference after the flip: {flip['rubric_reference_flipped']})",
              f"- Full-set argmax with the flip, per ordering: {flip['argmax_per_ordering']}; moved away from d* in all orderings: {flip['moved_away_all_orderings']}",
              "- P(d*) original → flipped, per ordering: "
              + ", ".join(f"{a:.3f} → {b:.3f}" for a, b in zip(flip["p_d_star_original"], flip["p_d_star_flipped"])),
              f"- Diagnostics: finite {flip['diagnostics']['all_finite']}, min label mass {flip['diagnostics']['min_label_mass']:.3f}, greedy matches {flip['diagnostics']['greedy_matches']}/3", ""]
    L += ["## Citations", "", cit["note"], "",
          f"- Sampled: {cit['n_sampled']}; parse statuses {cit['status_counts_sampled']}; analyzable {cit['n_analyzable_sampled']}",
          f"- Categories {cit['category_counts']}; sizes {cit['size_distribution']}",
          f"- Cited sets {cit['set_frequencies']}; modal {cit['modal_set']} ({_fmt(cit['modal_set_share'])})",
          f"- Partial citations: {cit['n_partial']}; mean beat (necessity) {_fmt(cit['mean_beat_necessity'])}, "
          f"mean beat (sufficiency) {_fmt(cit['mean_beat_sufficiency'])}; share > 0.5: "
          f"{_fmt(cit['share_beat_necessity_above_half'])} / {_fmt(cit['share_beat_sufficiency_above_half'])}; "
          f"mean Shapley top-k agreement {_fmt(cit['mean_shapley_top_k_agreement'])}"]
    if cit["faithful_exact_match_share"] is not None:
        L.append(f"- Exact match with the designed faithful citation: {_fmt(cit['faithful_exact_match_share'])}")
    if cit["cites_rule_excluded_share"] is not None:
        L.append(f"- Cites the rule-excluded record: {_fmt(cit['cites_rule_excluded_share'])}")
    if cit["cites_distractor_share"] is not None:
        L.append(f"- Cites a distractor: {_fmt(cit['cites_distractor_share'])}")
    L += ["", "| Greedy citation | Status | Cited | Category | Beat (nec.) | Beat (suff.) |", "|---|---|---|---|---|---|"]
    for g in cit["greedy"]:
        L.append(f"| ordering {g['ordering']} | {g['status']} | {g['cited']} | {g['category']} | "
                 f"{_fmt(g['beat_necessity'])} | {_fmt(g['beat_sufficiency'])} |")
    return "\n".join(L) + "\n"


def _summary_md(manifest, rows):
    L = []
    if manifest["mock"]:
        L += ["> **MOCK RUN.** Probabilities and citations come from hand-written rules. Do not report these numbers.", ""]
    L += [f"# Full experiment summary: `{manifest['run_id']}`", "",
          f"- Model: `{manifest['scorer'].get('model_name')}` @ `{manifest['scorer'].get('commit_hash')}` "
          f"({manifest['scorer'].get('dtype')}; logits {manifest['scorer'].get('logits_dtype')})",
          f"- Approved by: {manifest['gates']['G3_approved_by']}; frozen files verified: {manifest['gates']['G1_freeze']}",
          f"- Rubric reference answers: {manifest['rubric_validation']['kind']} "
          f"({', '.join(manifest['rubric_validation']['declared_labelers'].values())}); not human annotation",
          f"- Elapsed: {manifest.get('elapsed_seconds')} s", "",
          "| Scenario | d* | Designed / rubric | Infra | Recovery checks | P(d*\\|all) | P(d*\\|none) | Flip moved d* | Partial citations | Beat nec. / suff. | Flags |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        beh = "n/a" if r["behavioral_pass"] is None else ("pass" if r["behavioral_pass"] else "**FAIL**")
        flip = "n/a" if not r["flip"] else str(r["flip"]["moved_away_all_orderings"])
        c = r["citations"]
        L.append(f"| {r['scenario_id']} | {r['d_star']} | {r['designed_or_reference']} | "
                 f"{'pass' if r['infrastructure_pass'] else '**FAIL**'} | {beh} | {r['v_full_mean']:.3f} | "
                 f"{r['v_empty_mean']:.3f} | {flip} | {c['n_partial']}/{c['n_analyzable_sampled']} | "
                 f"{_fmt(c['mean_beat_necessity'])} / {_fmt(c['mean_beat_sufficiency'])} | {len(r['flags'])} |")
    L += ["", "Ranges, per-ordering values and all details are in each scenario's `REPORT.md`. Shapley values are "
          "behavioral attributions, not ground truth about internal reasoning. Values across orderings describe "
          "ordering sensitivity; they are not confidence intervals."]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    sys.exit(main())
