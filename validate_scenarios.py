#!/usr/bin/env python3
"""Validate all six scenarios offline (no model) and optionally freeze them.

  python validate_scenarios.py                  # validate and write scenarios/VALIDATION_REPORT.md
  python validate_scenarios.py --freeze         # validate, then write scenarios/FREEZE.json (refuses to overwrite)
  python validate_scenarios.py --verify-freeze  # check every frozen file against FREEZE.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from mxr import design  # noqa: E402
from mxr.checks import load_criteria  # noqa: E402
from mxr.scenario_validation import (EXPERIMENT_SCENARIOS, SCEN_DIR, freeze_manifest,  # noqa: E402
                                     validate, verify_freeze)


def run_validation():
    crit = load_criteria()
    rubric = json.loads((SCEN_DIR / "rubric_macro_v1.json").read_text())
    results, all_issues, letters = [], [], {}
    for sid in EXPERIMENT_SCENARIOS:
        sc, issues, info = validate(sid, crit, rubric)
        info["design_fingerprint"] = design.design_fingerprint(sc)
        results.append(info)
        all_issues += issues
        for l in info["economy_label"]:
            letters.setdefault(l, []).append(sid)
    for l, sids in letters.items():
        if len(sids) > 1:
            all_issues.append({"scenario": ",".join(sids), "code": "deid",
                               "message": f"economy label {l} reused across scenarios"})
    balance = {}
    for r in results:
        balance[r["designed_full"]] = balance.get(r["designed_full"], 0) + 1
    return results, all_issues, balance


def render_report(results, issues, balance):
    L = ["# Scenario validation report (offline, no model)", "",
         f"**Result: {'PASS' if not issues else 'FAIL'}** ({len(issues)} issues)", "",
         f"Designed full-set answers across the six scenarios: {balance}", ""]
    if issues:
        L += ["## Issues", ""] + [f"- `{i['scenario']}` [{i['code']}] {i['message']}" for i in issues] + [""]
    L += ["## Per scenario", "",
          "| Scenario | Structure | Economy | Designed full / empty | Designed Shapley (ideal model) | Designed LOO | Criteria: ideal passes / blind fails / distractor-driven fails |",
          "|---|---|---|---|---|---|---|"]
    for r in results:
        crit = "n/a (descriptive only)"
        if "criteria_ideal_pass" in r:
            crit = f"{r['criteria_ideal_pass']} / {', '.join(r['criteria_blind_fail'])} / {', '.join(r['criteria_swapped_fail'])}"
        L.append(f"| {r['scenario_id']} | {r['structure']} | {', '.join(r['economy_label'])} | "
                 f"{r['designed_full']} / {r['designed_empty']} | "
                 + ", ".join(f"{k} {v:+.2f}" for k, v in r["designed_shapley"].items()) + " | "
                 + ", ".join(f"{k} {v:+.2f}" for k, v in r["designed_loo"].items()) + f" | {crit} |")
    L += ["", "## Rubric scenarios", "", "| Scenario | Rubric total | Reference | Flip target | Flip total | Flip reference |",
          "|---|---|---|---|---|---|"]
    for r in results:
        if "rubric_total" in r:
            L.append(f"| {r['scenario_id']} | {r['rubric_total']:+d} | {r['reference_answer']} | "
                     f"{r['flip']['target']} | {r['flip']['total']:+d} | {r['flip']['reference_answer']} |")
    L += ["", "## Designed answer for every subset", "",
          "| Subset | " + " | ".join(r["scenario_id"] for r in results) + " |",
          "|---|" + "---|" * len(results)]
    for s in design.all_subsets():
        k = design.subset_key(s)
        L.append(f"| {k} | " + " | ".join(r["designed_answers"][k] for r in results) + " |")
    L += ["", "## Record lengths (words) and prompt lengths (characters)", ""]
    for r in results:
        L.append(f"- `{r['scenario_id']}`: records {r['record_words']}; prompts {r['prompt_chars'][0]}–{r['prompt_chars'][1]} chars")
    L += ["", "Design fingerprints:", ""] + [f"- `{r['scenario_id']}`: `{r['design_fingerprint']}`" for r in results]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--verify-freeze", action="store_true")
    args = ap.parse_args(argv)
    if args.verify_freeze:
        ok, bad = verify_freeze()
        print("FREEZE OK: all frozen files match" if ok else f"FREEZE MISMATCH: {bad}")
        return 0 if ok else 4
    results, issues, balance = run_validation()
    (SCEN_DIR / "VALIDATION_REPORT.md").write_text(render_report(results, issues, balance))
    print(f"{'PASS' if not issues else 'FAIL'}: {len(issues)} issues; report at scenarios/VALIDATION_REPORT.md")
    for i in issues:
        print(" ", i)
    if args.freeze:
        if issues:
            print("not freezing: validation failed")
            return 1
        path = SCEN_DIR / "FREEZE.json"
        if path.exists():
            print("FREEZE.json already exists; refusing to overwrite (amend the protocol and re-freeze deliberately)")
            return 5
        frozen = {
            "frozen_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "protocol": "v0.2 + amendments 1-2",
            "before_any_model_test_of": [s for s in EXPERIMENT_SCENARIOS if s != "s_single"],
            "files": freeze_manifest(),
            "design_fingerprints": {r["scenario_id"]: r["design_fingerprint"] for r in results},
            "validation_report_sha256": __import__("hashlib").sha256(
                (SCEN_DIR / "VALIDATION_REPORT.md").read_bytes()).hexdigest(),
        }
        path.write_text(json.dumps(frozen, indent=2) + "\n")
        print(f"frozen: {path}")
    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
