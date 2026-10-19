# Changes in this public release

This repository is a publication copy of the original **Memory X-Ray** results package. The original package
(`memory_xray_v02_results.zip`, SHA-256 `a17bc1859d501ed3877413955cfa393107240eedfbed30a1df882ce3c5edf6ea`,
160 files) is kept unchanged outside this repository. Inside the repository:

- **No experimental data, scenario, threshold, criterion, label, run output, result number, method, conclusion or
  report figure was changed.**
- 158 of the 160 original files are present byte-identical, either at their original path, at a new path (3 moved
  documents), or as a preserved original copy (3 replaced files).
- The other 2 files, the report and its HTML copy, received one wording edit for the public release (§3). It touches no
  number, result or conclusion.
- Every change is listed below and is checked by `python scripts/verify_release.py` (check 1), using
  [`records/original_package/release_path_map.json`](records/original_package/release_path_map.json) and the original
  checksums in [`records/original_package/SHA256SUMS_original_package.txt`](records/original_package/SHA256SUMS_original_package.txt).

The `mxr` experiment package is unchanged at version 0.2.4, the version recorded in the run manifests. Version
identifiers that are part of the recorded evidence (the protocol identifier "v0.2" in `scenarios/FREEZE.json`, the
run manifests and the frozen documents, the protocol file name `PROTOCOL_v0.2.md`, and the package version) are kept
unchanged.

## 1. Moved (byte-identical)

| Original path | Release path | Why |
|---|---|---|
| `PROTOCOL_v0.2.md` | `docs/PROTOCOL_v0.2.md` | keep the repository root short |
| `APPROVAL_PACKET_full_experiment.md` | `docs/APPROVAL_PACKET_full_experiment.md` | same |
| `README.md` | `docs/history/README_pre_run_infrastructure.md` | the original README described the pre-run infrastructure stage (package 0.2.1, before the full run) and is superseded by the new `README.md`; kept as a historical record |

The report (`results/RESULTS_AND_DISCUSSION.md`) and other frozen documents still refer to `PROTOCOL_v0.2.md` and
`APPROVAL_PACKET_full_experiment.md` by file name; those documents are now in `docs/`.

## 2. Replaced (original preserved in `records/original_package/replaced_files/`)

### `reanalyze.py` — fixes the missing-`manifest.json` failure

| | SHA-256 |
|---|---|
| original (`replaced_files/reanalyze.py.orig`) | `e7c451078b6707d8242fdba8a6d73e613be3d5dc2a3235e787fece88e891a250` |

- **Problem.** The original script required `<folder>/manifest.json`. The full run keeps a single `manifest.json` at the
  run root and none in its six scenario folders, so `python reanalyze.py runs/full_20261017T223452Z/<scenario>` failed
  with `FileNotFoundError`, and the run root failed with `KeyError: 'scenario_id'`. Only the two single-scenario
  feasibility runs could be reanalyzed.
- **Fix.** For full-run scenario folders the script now reads the run-root manifest and uses the same settings as
  `run_experiment.py`: the design fingerprint for that scenario, the full-run tie tolerance, the frozen criteria in
  `scenarios/validation_criteria.json`, and the lattice-only tokenization rows. Passing the run root reanalyzes all six
  scenarios.
- **Comparison with the saved run.** Recomputed check outcomes are compared with each saved `checks.json`. Checks that
  did not exist when a run was made (I8 and I9 postdate feasibility run 1) are reported, not compared.
- **Output location.** Command-line output goes to `outputs/reanalysis/` (git-ignored) instead of a new folder inside
  `runs/`. The original Python call `reanalyze.main("<run folder>")`, used by `tests/test_pipeline.py`, keeps its original
  behavior and return value.
- **Verified.** All six full-run scenarios and both feasibility runs reproduce their saved check outcomes, including
  S-conflict's failed BC1, BC3, BC4, BC5 and run 1's failed I3 (`tests/test_release.py`, `scripts/verify_release.py`).
- Flip and citation results are not recomputed by this script (as in the original); `analysis_full/independent_reanalysis.py`
  recomputes them with separate code.

### `tests/test_precision.py` — makes a host-dependent assertion host-aware

| | SHA-256 |
|---|---|
| original (`replaced_files/test_precision.py.orig`) | `1f3c7a4b2c7e8e40b865438b899fe767f982e50931d1c9d14bd0beb29104ffa5` |

- **Problem.** `test_reproduces_run1_I3_failure_and_fix_clears_it` (parametrized over two tiny architectures, `phi3` and
  `llama`) asserted that float16 *math* makes the I3 first-token recompute difference exceed 1e-3. Whether it does
  depends on the host's float16 kernels (oneDNN ISA, ATen dispatch) and on the architecture, not on the code under test.
  - In the environment used to prepare this release, the `phi3` case gives exactly 0.0, while `llama` gives more than
    1e-3.
  - The original suite therefore gives **1 failed, 106 passed** here, and the same failure with
    `ONEDNN_MAX_CPU_ISA=AVX512_CORE`. The same failure stopped the suite on a Colab CPU host in an earlier phase.
- **Fix.** The test is split. Nothing that can be checked on the host is dropped:
  - `test_float16_math_reproduces_run1_I3_failure_where_the_host_shows_it` keeps the original assertion (> 1e-3) for
    every case where the host's float16 kernels produce any difference. It **skips**, with a reason, only when the
    difference is exactly 0.0, which means the effect cannot be reproduced on that host. Here the `llama` case passes
    and the `phi3` case is skipped.
  - `test_fix_clears_I3_recompute_difference` keeps the original second assertion: float32 compute gives an I3
    difference < 1e-4.
  - A new, host-independent `test_I3_recompute_check_detects_a_length_dependent_difference` shows that the I3 check
    is live. An injected logit shift that grows with sequence length must be detected above 1e-3.
  - The float16 numerical error itself is still tested by the unchanged
    `test_float16_math_is_measurably_off_at_phi3_logit_scale`. All other tests in the file are unchanged.
- This does not affect any result: the published run used float32 compute and passed I3 in all scenarios.

### `requirements.txt` — split by purpose

| | SHA-256 |
|---|---|
| original (`replaced_files/requirements.txt.orig`) | `f5ed6172e7a9c01591fa37fa416ebdd407a06c6f38e41512be48b1d91d8fa28f` |

The original file (`torch>=2.1`, `transformers>=4.41.2`, `accelerate>=0.31`, `pytest`) mixed GPU and analysis needs and did
not include matplotlib, which the figure scripts use. It is split into:

- `requirements.txt`: CPU only (matplotlib, pytest, and huggingface_hub, which the offline model-revision tests import;
  nothing is downloaded). Enough for exploration, reanalysis, figures, verification and every test that does not need
  PyTorch.
- `requirements-dev.txt`: adds PyTorch and transformers for the tiny-model tests, plus notebook tooling.
- `requirements-experiment.txt`: re-running the GPU experiment, with `transformers==5.18.0` pinned to the version recorded
  in the run's manifest.

## 3. Edited for the public release

| File | Change |
|---|---|
| `results/RESULTS_AND_DISCUSSION.md` | One parenthetical cross-reference to a separate, non-public project was removed from the heading of the "Practical implications for evidence-grounded systems" bullet in §6. The heading now ends with a colon. |
| `results/RESULTS_AND_DISCUSSION.html` | The same edit, in the HTML copy. |

- Nothing else in either file changed: one line differs in each, and the four implication bullets under that heading
  are unchanged.
- The edited files' SHA-256 checksums are recorded under `edited_for_public_release` in
  [`records/original_package/release_path_map.json`](records/original_package/release_path_map.json) and checked by
  `scripts/verify_release.py`.
- The unedited originals are kept, with their checksums, in the author's private archive of the original package.

## 4. Added

| Path | What | Status |
|---|---|---|
| `README.md` | new project README | documentation |
| `CHANGES.md`, `NOTICE.md`, `LICENSE`, `LICENSE-CONTENT.md`, `CITATION.cff`, `.gitignore`, `Makefile` | release files | |
| `requirements-dev.txt`, `requirements-experiment.txt` | see above | |
| `analysis_full/content_only_baseline.py` → `results/post_hoc/content_only_baseline.json` | content-only citation baseline | **POST HOC** (defined after the results were seen) |
| `analysis_full/export_figures.py` → `results/figures/publication/` | the seven report figures re-rendered at 300 dpi PNG plus PDF and SVG (same code and data as `make_figures.py`), plus two new figures: `fig0_workflow` (diagram, no data) and `fig8_content_only_baseline` (**post hoc**) | the original 200-dpi figures in `results/figures/` are unchanged |
| `analysis_full/poster_figures.py` → `poster_materials/figures/` | six poster figures drawn at print size with large type (workflow, vertical workflow, redundancy, conflict order, citations vs content-only citer, flips) from the same result files | figure 4 shows the **post hoc** baseline |
| `scripts/verify_release.py` | verifies the release from the distributed files; regenerates every result and figure in a temporary copy from which the committed outputs were deleted | |
| `scripts/compare_runs.py` | compares a re-run of the GPU experiment with the published run: cell completeness, decisions, check outcomes, flips, probability and Shapley differences (tolerance 0.01) | |
| `scripts/make_key_numbers.py` → `poster_materials/KEY_NUMBERS.md` | poster numbers generated from the result files | |
| `tests/test_release.py` | 13 tests for the added and changed code | |
| `notebooks/explore_results.ipynb` | CPU-only exploration notebook, executed with outputs | |
| `notebooks/colab_full_experiment.ipynb` | GitHub version of the Colab runner: clones the repository, pins transformers, writes to `outputs/runs/`, compares with the published run | `colab/` notebooks are kept unchanged |
| `docs/RESEARCH_SUMMARY.md`, `docs/POST_HOC_ADDENDUM.md` | research summary; post hoc content-only baseline write-up | |
| `docs/RELEASE_VALIDATION_REPORT.md` | tests and reproducibility checks for this release | |
| `records/original_package/` | original checksums, path map (including the edited files' checksums), preserved originals of replaced files | |
| `poster_materials/` | poster text, key numbers, figures, captions, references, layout, talk outline | |

## 5. Not included

- Duplicate uploads: the Colab code package (its code is identical to the code here), the figure ZIP (identical to
  `results/figures/`) and the separately uploaded run ZIP, report and figure images
  (identical to the copies here).
- `exercise_dataframes.ipynb`: an unrelated notebook.
- Later pilot experiments (pilot designs, pilot runs and sealed archives): unfinished and out of scope for this
  release.
- An earlier pilot (Gemini, IT troubleshooting): a separate study.
- Model weights or caches of any kind.

## 6. Known issues documented, not changed (frozen files)

- `runs/full_20261017T223452Z/manifest.json` lists `protocol_amendments: [1, 2]`, a value hard-coded in
  `run_experiment.py`; the run executed under amendments 1–4. Documented in the report (§2.1, limitation 9); no computed
  quantity is affected.
- The frozen documents (`docs/PROTOCOL_v0.2.md`, the report) refer to files by their original names; see §1.
- `colab/full_experiment.ipynb` (the notebook that produced the published run) expects the package ZIP upload, installs
  unpinned `transformers>=4.41.2` and runs the original test suite, which includes the host-dependent precision test above.
  Use `notebooks/colab_full_experiment.ipynb` for a re-run.
- `docs/history/README_pre_run_infrastructure.md` describes the pre-run state of the project and is outdated by design.
- `analysis_full/independent_reanalysis.py`, `report_numbers.py` and `make_figures.py` write their outputs into
  `results/` in place (as in the original package). With Python ≥ 3.12 on x86-64 they regenerate byte-identical JSON. On Python 3.10–3.11 the
  floats differ in the last digit (about 1e-16), because Python 3.12 changed `sum()` to compensated summation. On
  macOS on Apple Silicon (Python 3.13), 4 values differ by at most 4e-18, from the platform's math library. No
  decision, check or reported number changes. `scripts/verify_release.py` runs them in a temporary copy and compares
  within 1e-12.
