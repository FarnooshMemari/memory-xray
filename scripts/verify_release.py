#!/usr/bin/env python3
"""Verify this release from the distributed files alone (CPU only; no model, no GPU, no network).

  python scripts/verify_release.py            # all checks (about 30 seconds)
  python scripts/verify_release.py --tests    # also run the pytest suite
  python scripts/verify_release.py --json outputs/verify_release.json

Checks
  1. Original package files: every one of the 160 files of the original results package is accounted for
     (records/original_package/release_path_map.json). 158 are present byte-identical at their release path
     (moved files are checked at their new path, replaced files through their preserved original copy);
     the 2 files edited for the public release (see CHANGES.md) must match their recorded SHA-256.
  2. Saved runs and labels: every checksum in records/{full_run,run1,run2,labels}_SHA256SUMS.txt.
  3. Frozen design and rubric labels: validate_scenarios.py --verify-freeze and check_labels.py.
  4. Analysis reproduction: in a temporary copy of the repository, re-run
     independent_reanalysis.py, report_numbers.py and content_only_baseline.py, and require the
     regenerated JSON to equal the committed results (byte-identical, or equal within 1e-12). Generated
     outputs are deleted from the copy first, so a script that writes nothing fails.
     make_figures.py, export_figures.py and poster_figures.py are also run there and must regenerate every committed
     figure file (byte identity of images depends on the matplotlib version and is reported only).
     poster_materials/KEY_NUMBERS.md must match the committed result files.
  5. Pipeline reanalysis: reanalyze.py on the full run and both feasibility runs must reproduce
     every saved check outcome.
  6. Release hygiene: no model weights, no sealed or unfinished pilot material, no unrelated files,
     no file larger than 25 MB.
Exit code 0 only if every check passes. Nothing in the repository is modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
RESULTS = []


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def record(name, ok, detail):
    RESULTS.append({"check": name, "passed": bool(ok), "detail": detail})
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}", flush=True)


def read_sums(path):
    out = []
    for line in path.read_text().splitlines():
        if line.strip():
            digest, name = line.split(maxsplit=1)
            out.append((digest, name.lstrip("*")))
    return out


def check_original_files():
    m = json.loads((ROOT / "records/original_package/release_path_map.json").read_text())
    sums = read_sums(ROOT / "records/original_package/SHA256SUMS_original_package.txt")
    bad = []
    for digest, name in sums:
        rel = m["moved"].get(name) or m["replaced"].get(name) or name
        p = ROOT / rel
        if not p.is_file() or sha256(p) != digest:
            bad.append(rel)
    edited = m.get("edited_for_public_release", {})
    for rel, info in edited.items():
        p = ROOT / rel
        if rel in dict((b, a) for a, b in sums) or not p.is_file() or sha256(p) != info["sha256"]:
            bad.append(rel)
    replaced_now = [n for n in m["replaced"] if (ROOT / n).is_file() and sha256(ROOT / n) !=
                    dict((b, a) for a, b in sums)[n]]
    record("1 original package files preserved", not bad and len(sums) + len(edited) == m["original_package"]["files"] == 160,
           f"{len(sums) + len(edited) - len(bad)}/{len(sums) + len(edited)} accounted for: {len(sums)} byte-identical at "
           f"their release paths, {len(edited)} edited for the public release and matching their recorded SHA-256 "
           f"({', '.join(edited)})"
           + (f"; MISSING OR CHANGED: {bad} (if you regenerated results or figures in place, restore them with "
              "`git checkout -- results/`)" if bad else "")
           + f"; {len(replaced_now)} replaced in the release (documented in CHANGES.md): {', '.join(replaced_now)}")


def check_run_sums():
    total, bad = 0, []
    for sums, base in (("full_run_SHA256SUMS.txt", "runs"), ("run1_SHA256SUMS.txt", "runs"),
                       ("run2_SHA256SUMS.txt", "runs"), ("labels_SHA256SUMS.txt", "records")):
        for digest, name in read_sums(ROOT / "records" / sums):
            total += 1
            p = ROOT / base / name
            if not p.is_file() or sha256(p) != digest:
                bad.append(f"{base}/{name}")
    record("2 saved runs and labels match their checksums", not bad,
           f"{total - len(bad)}/{total} files verified" + (f"; FAILED: {bad}" if bad else ""))


def run(cmd, cwd, timeout=900):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", MPLBACKEND="Agg")
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)


def check_freeze_and_labels():
    a = run([PY, "validate_scenarios.py", "--verify-freeze"], ROOT)
    record("3a frozen scenario files and design fingerprints", a.returncode == 0,
           (a.stdout.strip().splitlines() or ["(no output)"])[-1])
    b = run([PY, "check_labels.py"], ROOT)
    record("3b rubric label gate (G2)", b.returncode == 0, (b.stdout.strip().splitlines() or ["(no output)"])[-1])


def _close(a, b, tol=1e-12):
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_close(a[k], b[k], tol) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_close(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, float) or isinstance(b, float):
        return isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(a - b) <= tol
    return a == b


def check_analysis(tmp):
    copy = tmp / "repo"
    shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns("outputs", "__pycache__", ".pytest_cache", ".git", ".venv",
                                                              "venv", ".ipynb_checkpoints"))
    # Delete every generated output in the copy first, so a script that writes nothing cannot pass.
    for rel in ("results/reanalysis.json", "results/report_numbers.json", "results/post_hoc/content_only_baseline.json"):
        (copy / rel).unlink()
    for folder in ("results/figures", "results/figures/publication", "poster_materials/figures"):
        for f in (copy / folder).glob("*.*"):
            if f.suffix in (".png", ".pdf", ".svg"):
                f.unlink()
    steps = [("independent_reanalysis.py", "INDEPENDENT REANALYSIS AGREES WITH PIPELINE: True"),
             ("report_numbers.py", None), ("content_only_baseline.py", None)]
    for script, must_print in steps:
        r = run([PY, f"analysis_full/{script}"], copy)
        ok = r.returncode == 0 and (must_print is None or must_print in r.stdout)
        record(f"4 run analysis_full/{script}", ok, "exit 0" + (f", printed '{must_print}'" if must_print and ok else "")
               if ok else f"exit {r.returncode}: {(r.stderr or r.stdout)[-400:]}")
    for rel in ("results/reanalysis.json", "results/report_numbers.json", "results/post_hoc/content_only_baseline.json"):
        a, b = ROOT / rel, copy / rel
        if not b.exists():
            record(f"4 regenerated {rel} equals committed", False, "not regenerated")
            continue
        same_bytes = sha256(a) == sha256(b)
        same = same_bytes or _close(json.loads(a.read_text()), json.loads(b.read_text()))
        record(f"4 regenerated {rel} equals committed", same,
               "byte-identical" if same_bytes else ("equal within 1e-12" if same else "DIFFERENT"))
    for script, folder, n in (("make_figures.py", "results/figures", 7), ("export_figures.py", "results/figures/publication", 27),
                              ("poster_figures.py", "poster_materials/figures", 18)):
        r = run([PY, f"analysis_full/{script}"], copy)
        files = sorted(f for f in (copy / folder).glob("*.*") if f.suffix in (".png", ".pdf", ".svg"))
        committed = sorted(f.name for f in (ROOT / folder).glob("*.*") if f.suffix in (".png", ".pdf", ".svg"))
        same = sum(1 for f in files if (ROOT / folder / f.name).exists() and sha256(f) == sha256(ROOT / folder / f.name))
        ok = r.returncode == 0 and len(files) == n and [f.name for f in files] == committed
        record(f"4 run analysis_full/{script}", ok,
               f"exit {r.returncode}; regenerated all {len(files)} committed files; {same} byte-identical (byte identity depends on "
               f"the matplotlib and font versions)"
               if ok else f"exit {r.returncode}: {(r.stderr or r.stdout)[-400:]}")


def check_key_numbers():
    r = run([PY, "scripts/make_key_numbers.py", "--check"], ROOT)
    record("4 poster_materials/KEY_NUMBERS.md matches the result files", r.returncode == 0,
           (r.stdout.strip().splitlines() or ["(no output)"])[-1])


def check_reanalyze(tmp):
    for run_dir in ("runs/full_20261017T223452Z", "runs/s_single_20261017T204445Z", "runs/s_single_20261017T180509Z"):
        out = tmp / ("re_" + Path(run_dir).name)
        r = run([PY, "reanalyze.py", run_dir, "--out", str(out)], ROOT)
        last = (r.stdout.strip().splitlines() or ["(no output)"])[-1]
        record(f"5 reanalyze.py {run_dir}", r.returncode == 0, last.split(";")[0] if r.returncode == 0 else (r.stderr or r.stdout)[-400:])


def check_hygiene():
    bad = []
    skip = {"outputs", ".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache", ".ipynb_checkpoints", "site-packages"}
    for p in ROOT.rglob("*"):
        if not p.is_file() or skip & set(p.relative_to(ROOT).parts):
            continue
        rel = p.relative_to(ROOT).as_posix()
        low = rel.lower()
        if p.suffix in (".safetensors", ".bin", ".gguf", ".pt", ".pth", ".ckpt"):
            bad.append(f"{rel} (model weights)")
        elif "sealed" in low or "pilot_2026" in low or "v0.3" in low or "v03" in low:
            bad.append(f"{rel} (sealed or unfinished pilot material)")
        elif "exercise_dataframes" in low:
            bad.append(f"{rel} (unrelated file)")
        elif p.stat().st_size > 25 * 1024 * 1024:
            bad.append(f"{rel} (> 25 MB)")
    record("6 release hygiene", not bad, "no weights, sealed or unfinished pilot material, unrelated files or files > 25 MB"
           if not bad else f"found: {bad}")


def check_tests():
    r = run([PY, "-m", "pytest", "-q", "-p", "no:cacheprovider"], ROOT, timeout=1800)
    last = (r.stdout.strip().splitlines() or ["(no output)"])[-1]
    record("7 pytest", r.returncode == 0, last)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tests", action="store_true", help="also run the pytest suite")
    ap.add_argument("--json", default=None, help="write the results to this JSON file")
    a = ap.parse_args(argv)
    print(f"Verifying {ROOT} with Python {sys.version.split()[0]}\n")
    check_original_files()
    check_run_sums()
    check_freeze_and_labels()
    with tempfile.TemporaryDirectory(prefix="mxr_verify_") as t:
        tmp = Path(t)
        check_analysis(tmp)
        check_key_numbers()
        check_reanalyze(tmp)
    check_hygiene()
    if a.tests:
        check_tests()
    n_ok = sum(r["passed"] for r in RESULTS)
    print(f"\n{n_ok}/{len(RESULTS)} checks passed: {'RELEASE VERIFIED' if n_ok == len(RESULTS) else 'VERIFICATION FAILED'}")
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps({"python": sys.version, "results": RESULTS}, indent=2))
    return 0 if n_ok == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
