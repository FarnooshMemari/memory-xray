#!/usr/bin/env python3
"""Check the two rubric label files (gate G2) without running anything else.

  python check_labels.py

Read-only: prints what blocks the run and any disagreements; never edits the files.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mxr.labels import label_gate  # noqa: E402


def main():
    ok, rep = label_gate()
    print(f"G2 rubric labels: {'OK - the full run may start' if ok else 'BLOCKED'}")
    for who, info in rep["labelers"].items():
        print(f"  {who}: {info.get('name')} ({info.get('date')})")
    print(f"  Validation kind (amendment 4): {rep['validation_kind']}; human annotation: "
          f"{rep['human_annotation']}; files match declared labelers: {rep['declared_labelers_match']}")
    if rep["blocking"]:
        print(f"\nMust fix ({len(rep['blocking'])}):")
        for b in rep["blocking"]:
            print("  -", b)
    if rep["agreement"]:
        print("\nAgreement:", ", ".join(f"{k} {v}" for k, v in rep["agreement"].items()))
    if rep["record_disagreements"]:
        print("\nRecord-level differences from the frozen rubric scores (reported, not blocking):")
        for d in rep["record_disagreements"]:
            print("  -", d)
    if rep["inter_labeler_disagreements"]:
        print("\nDifferences between the two labelers (reported, not blocking):")
        for d in rep["inter_labeler_disagreements"]:
            print("  -", d)
    return 0 if ok else 6


if __name__ == "__main__":
    sys.exit(main())
