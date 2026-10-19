#!/usr/bin/env python3
"""S-single feasibility test (protocol v0.2): 16 subsets x 3 fixed orderings.

Stages
  1. Tokenization validation for every cell (aborts before scoring on failure).
  2. Label-probability scoring of all 48 cells.
  3. Greedy-decoding cross-check of every cell.
  4. Re-scoring of 3 cells for repeatability.
  5. Analysis, pre-specified checks, report.

Every run writes to a new directory under --out and refuses to overwrite an
existing one, so earlier results are never touched.

Examples
  python run_feasibility.py --model microsoft/Phi-3-mini-4k-instruct
  python run_feasibility.py --backend mock          # pipeline exercise only
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
from mxr.report import render_report  # noqa: E402
from mxr.scoring import PINNED_MODEL, PINNED_REVISION, RevisionError, TokenizationError  # noqa: E402

REPEAT_CELLS = (("E1+E2+E3+E4", 0), ("none", 1), ("E2", 2))


def _dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=False, default=str))


def make_scorer(args, scenario):
    if args.backend == "mock":
        from mxr.mock import MockLabelScorer

        decisive = scenario["designed"]["decisive"][0]
        return MockLabelScorer(decisive_text=scenario["records"][decisive])
    from mxr.scoring import HFLabelScorer

    return HFLabelScorer.load(args.model, revision=args.revision, storage_dtype=args.storage_dtype,
                              compute_dtype=args.compute_dtype, device=args.device,
                              attn_implementation=args.attn)


def parse_args(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scenario", default=str(HERE / "scenarios" / "s_single.json"))
    ap.add_argument("--backend", choices=["hf", "mock"], default="hf")
    ap.add_argument("--model", default=PINNED_MODEL)
    ap.add_argument("--revision", default=PINNED_REVISION,
                    help="model commit (40-hex sha); a branch name is resolved to a sha before loading")
    ap.add_argument("--storage-dtype", default="auto",
                    help="weight storage dtype; auto = float16 on CUDA, float32 on CPU")
    ap.add_argument("--compute-dtype", default="float32",
                    help="arithmetic dtype; float32 (default) or equal to the storage dtype")
    ap.add_argument("--device", default=None)
    ap.add_argument("--attn", default="eager", help="attention implementation")
    ap.add_argument("--out", default=str(HERE / "runs"))
    ap.add_argument("--run-id", default=None)
    return ap.parse_args(argv)


def main(argv=None, scorer=None):
    args = parse_args(argv)
    scenario = json.loads(Path(args.scenario).read_text())
    if scorer is None:
        try:
            scorer = make_scorer(args, scenario)
        except RevisionError as exc:
            print(f"ABORTED before loading: the model commit could not be pinned/verified: {exc}")
            return 3
    if "logits_dtype" not in scorer.meta and hasattr(scorer, "precision_probe"):
        scorer.meta.update(scorer.precision_probe())
    is_mock = scorer.meta.get("backend") == "MOCK"
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = args.run_id or f"{scenario['scenario_id']}_{stamp}{'_MOCK' if is_mock else ''}"
    run_dir = Path(args.out) / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    manifest = {
        "run_id": run_id,
        "protocol_version": "0.2",
        "protocol_amendment": 1,
        "started_utc": stamp,
        "scenario_id": scenario["scenario_id"],
        "design_fingerprint": design.design_fingerprint(scenario),
        "orderings": design.ORDERINGS,
        "opaque_ids": design.OPAQUE_IDS,
        "answer_prefix": design.ANSWER_PREFIX,
        "label_continuations": design.LABEL_CONTINUATIONS,
        "scorer": scorer.meta,
        "mock": is_mock,
    }
    spec = [(s, k) for k in range(len(design.ORDERINGS)) for s in design.all_subsets()]
    t0 = time.time()

    # Stage 1: tokenization validation (no scoring yet)
    tokval = []
    for s, k in spec:
        r = design.render(scenario, s, k)
        row = {"subset": design.subset_key(s), "ordering": k}
        try:
            rt = scorer.template_roundtrip(r["user_msg"])
            lt = scorer.label_tokenization(r["user_msg"])
            row.update(roundtrip_ok=bool(rt["ok"]), roundtrip=rt, label_ids=lt["label_ids"],
                       label_tokens=lt["label_tokens"], prompt_len=lt["prompt_len"])
        except TokenizationError as exc:
            row.update(roundtrip_ok=False, error=str(exc), label_ids={})
        tokval.append(row)
    _dump(run_dir / "tokenization_validation.json", tokval)
    bad = [t for t in tokval if t.get("error") or not t["roundtrip_ok"]]
    label_sets = {repr(sorted((k, tuple(v)) for k, v in t["label_ids"].items()))
                  for t in tokval if not t.get("error")}
    if bad or len(label_sets) != 1:
        manifest.update(status="aborted_at_tokenization", n_bad_cells=len(bad),
                        n_label_id_sets=len(label_sets))
        _dump(run_dir / "manifest.json", manifest)
        print(f"ABORTED before scoring: {len(bad)} cells failed tokenization validation; "
              f"{len(label_sets)} distinct label-id sets. See {run_dir / 'tokenization_validation.json'}")
        return 2
    label_info = tokval[0]
    print("Label tokenization:", {k: v for k, v in label_info["label_tokens"].items()})

    # Stage 2: scoring
    cells = []
    with (run_dir / "cells.jsonl").open("w") as fh:
        for i, (s, k) in enumerate(spec, 1):
            r = design.render(scenario, s, k)
            sc = scorer.score(r["user_msg"])
            rec = {
                "scenario_id": scenario["scenario_id"],
                "subset": design.subset_key(s),
                "subset_members": sorted(s),
                "mask": design.subset_mask(s),
                "ordering": k,
                "shown_canonical": r["shown_canonical"],
                "shown_ids": r["shown_ids"],
                "designed_answer": design.designed_answer(scenario, s),
                "user_msg": r["user_msg"],
                "score": sc,
            }
            fh.write(json.dumps(rec) + "\n")
            cells.append(rec)
            print(f"[{i:2d}/{len(spec)}] ordering {k} {rec['subset']:<12} "
                  f"argmax={sc['argmax']:<8} mass={sc['label_mass']:.3f} "
                  + " ".join(f"{l[:3]}={sc['p_norm'][l]:.3f}" for l in design.LABELS))

    # Stage 3: greedy cross-check
    max_len = max(len(v) for v in label_info["label_ids"].values())
    greedy_rows = []
    for rec in cells:
        g = scorer.greedy(rec["user_msg"], max_new_tokens=max_len + 1)
        arg = rec["score"]["argmax"]
        arg_ids = rec["score"]["labels"][arg]["token_ids"]
        greedy_rows.append({
            "subset": rec["subset"], "ordering": rec["ordering"], "argmax": arg,
            "argmax_ids": arg_ids, "greedy_ids": g["token_ids"], "greedy_text": g["text"],
            "token_match": list(g["token_ids"][: len(arg_ids)]) == list(arg_ids),
            "margin": rec["score"]["top2_margin"],
        })
    with (run_dir / "greedy_check.jsonl").open("w") as fh:
        for row in greedy_rows:
            fh.write(json.dumps(row) + "\n")

    # Stage 4: repeatability
    index = {(c["subset"], c["ordering"]): c for c in cells}
    repeat_rows = []
    for key, k in REPEAT_CELLS:
        rec = index[(key, k)]
        sc2 = scorer.score(rec["user_msg"])
        diff = max(abs(sc2["labels"][l]["logprob"] - rec["score"]["labels"][l]["logprob"])
                   for l in design.LABELS)
        repeat_rows.append({"subset": key, "ordering": k, "max_abs_diff": diff})
    _dump(run_dir / "repeatability.json", repeat_rows)

    # Stage 5: analysis and checks
    analysis = analyze(cells, scenario)
    infra = checks.infrastructure_checks(cells, tokval, greedy_rows, repeat_rows, scorer.meta)
    behavioral = checks.behavioral_checks_single(analysis, scenario)
    flags = checks.descriptive_flags(analysis, scenario)
    infra_ok = all(c["passed"] for c in infra)
    beh_ok = all(c["passed"] for c in behavioral)
    manifest.update(
        status="completed",
        elapsed_seconds=round(time.time() - t0, 1),
        n_cells=len(cells),
        n_forward_passes=sum(c["score"]["n_forward"] for c in cells),
        label_tokens=label_info["label_tokens"],
        label_ids=label_info["label_ids"],
        infrastructure_pass=infra_ok,
        behavioral_recovery_pass=beh_ok,
    )
    _dump(run_dir / "manifest.json", manifest)
    _dump(run_dir / "analysis.json", analysis)
    _dump(run_dir / "checks.json", {"infrastructure": infra, "behavioral": behavioral, "flags": flags})
    (run_dir / "REPORT.md").write_text(render_report(manifest, infra, behavioral, flags, analysis))

    print()
    print(f"Infrastructure checks: {'PASS' if infra_ok else 'FAIL'}")
    for c in infra:
        print(f"  {c['id']} {'pass' if c['passed'] else 'FAIL'}  {c['name']}: {c['detail']}")
    print(f"Behavioral recovery (validation check): {'PASS' if beh_ok else 'FAIL'}")
    for c in behavioral:
        print(f"  {c['id']} {'pass' if c['passed'] else 'FAIL'}  {c['name']}")
    for f in flags:
        print(f"  flag: {f}")
    print(f"Results: {run_dir}")
    return 0 if (infra_ok and beh_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
