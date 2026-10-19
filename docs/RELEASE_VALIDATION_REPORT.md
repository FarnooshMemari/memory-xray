# Release validation report

**Release:** Memory X-Ray public release (of the original results package) · **Prepared:** 2026-10-18, updated 2026-10-19 · No GPU was
used, no model was run, and nothing was pushed.

## Verdict

**The release reproduces every published result from its own files.**
- All 160 original files are accounted for: 158 byte-identical, and 2 (the report and its HTML copy) with one
  wording edit for the public release that changes no number, result or conclusion (`CHANGES.md` §3).
- All 89 run and label checksums verify.
- The independent reanalysis, every report number and the post hoc baseline regenerate identically: byte-for-byte on
  Python ≥ 3.12 on x86-64, and within 1e-12 on Python 3.10 and on macOS (Apple Silicon).
- The pipeline's own checks recompute to the saved outcomes for all three runs, including the failed ones.
- Every documented command runs from a fresh extraction in a clean environment.

Section 1 records the final public-release pass. Sections 2–6 record the validation of the release candidate before
that pass, on an x86-64 host. Section 7 lists what was not verified.

## 1. Final public-release pass

**Changes in this pass** (all listed in `CHANGES.md`):
- The report (`results/RESULTS_AND_DISCUSSION.md`) and its HTML copy: one wording edit, as described in `CHANGES.md`
  §3. One line differs in each file, and no number, method, result or conclusion changed. The edited files' SHA-256 values are
  recorded in `records/original_package/release_path_map.json`.
- `scripts/verify_release.py` check 1 now accounts for all 160 original files: 158 byte-identical and 2 that must
  match their recorded public-release SHA-256. A new test (`tests/test_release.py`) confirms that check 1 fails if an
  edited file is changed again.
- The project is described as an independent research project in explainable and responsible AI at Duke University
  (README, research summary, poster text and layout, `CITATION.cff` affiliation).
- Verified fill-ins: the repository URL `https://github.com/FarnooshMemari/memory-xray` (account confirmed; the
  repository does not exist yet) is used in the README, `CITATION.cff`, both notebooks and the poster text.
- The internal pre-release checklist was moved out of the repository; references to it were removed from `NOTICE.md`
  and `CHANGES.md`.
- Reproducibility statements now say that byte-for-byte JSON regeneration holds on x86-64. On Apple Silicon, 4 values
  differ by at most 4 × 10⁻¹⁸.
- `notebooks/explore_results.ipynb` was re-executed (its embedded verification output changed). Every text output is
  unchanged except the verification lines. No cell raised an error, and the outputs contain no local paths.

- **Version labels removed from the public presentation (2026-10-19).** The project is presented as "Memory X-Ray".
  - Version labels were removed from the README, research summary, post hoc addendum, poster materials, notebook
    titles, `CITATION.cff` (title; the `version` field was dropped), `requirements.txt`, and the messages and docstrings
    of the release scripts and tests.
  - Release-created paths were renamed: `records/original_v0.2/` → `records/original_package/` (checksum list
    `SHA256SUMS_original_package.txt`), and `docs/history/README_v0.2_infrastructure.md` →
    `docs/history/README_pre_run_infrastructure.md`. Contents are unchanged, and the path map was updated.
  - **Kept as recorded evidence:**
    - the protocol identifier "v0.2" in `scenarios/FREEZE.json` (hash-locked), the run manifests and the frozen
      documents;
    - the frozen protocol's file name `docs/PROTOCOL_v0.2.md`, which the frozen report and approval packet cite by
      name;
    - the `mxr` package version 0.2.4, which the run manifests record and the Colab re-run notebook asserts;
    - the original upload's file name and SHA-256 in the path map.

**No file under `runs/`, `scenarios/`, `results/*.json`, `results/figures/` or `poster_materials/figures/` changed in
this pass.** This was checked by comparing every file against the release candidate.

**Verification results** (macOS 26, Apple Silicon):

| Environment | `python scripts/verify_release.py --tests` |
|---|---|
| Python 3.13.15, torch 2.14.1 (CPU), transformers 5.20.1, matplotlib 3.11.2; release candidate before this pass (baseline) | 19/19 checks; pytest 121 passed, 2 skipped |
| same environment, final tree | **19/19 checks; pytest 122 passed, 2 skipped** |
| same environment, fresh extraction of the final ZIP | **19/19 checks; pytest 122 passed, 2 skipped** |
| fresh extraction, clean venv, **Python 3.12.11**, `requirements.txt` only (no PyTorch) | **19/19 checks; pytest 94 passed, 5 skipped** |
| fresh extraction, clean venv, **Python 3.10.21**, `requirements.txt` only (no PyTorch) | **19/19 checks; pytest 94 passed, 5 skipped** (all three JSON files equal within 1e-12) |

- On this host, check 4 regenerates `reanalysis.json` and `report_numbers.json` equal within 1e-12, not
  byte-identical: 4 floats differ by at most 3.5 × 10⁻¹⁸, from the platform's math library. The post hoc JSON is
  byte-identical. All figures were regenerated; 0/7, 18/27 and 12/18 are byte-identical (font rendering differs from the
  x86-64 host).
- The 2 skipped tests are the float16 reproduction of run 1's I3 failure. This host's float16 kernels give a
  difference of exactly 0.0 for both tiny architectures, so the effect cannot be shown here. The companion test that
  the I3 check detects a length-dependent difference passes.
- Every documented command ran from the fresh 3.12 extraction with exit code 0: `verify_release.py`, the three
  `analysis_full` scripts, `reanalyze.py` on the full run, `export_figures.py`, `poster_figures.py`,
  `make_key_numbers.py --check`, `compare_runs.py`, the mock pipeline run, `validate_scenarios.py --verify-freeze`,
  `check_labels.py` and `make help`.
- Expected exception, as in section 5: if the in-place analysis scripts are run on a host that does not regenerate the
  JSON byte-for-byte (here, Apple Silicon), the two preservation tests then correctly report `results/reanalysis.json`
  and `results/report_numbers.json` as changed. `git checkout results/` restores them, as the README says.
- `CITATION.cff` validates against schema 1.2.0 (`cffconvert --validate`).

**Content review of the public files.** Every file was scanned for references that do not belong in the public release,
including:
- hidden files, file and folder names;
- the contents of nested ZIP archives;
- decompressed PDF streams;
- PNG text chunks;
- base64-embedded images in the HTML report and the notebooks;
- notebook metadata;
- PDF document metadata.

The scan also looked for local paths, e-mail addresses and API-key patterns. None remain.

**Publication provenance (2026-10-19).**
- At publication, macOS blocked this session's access to the Downloads folder that holds the final release ZIP
  (SHA-256 `50cd63a28bfb575bb3bc01ebc7070a573b7e2a83677039ce7bdea03605db0b20`). The repository was therefore published
  from the previously verified working copy.
- Earlier the same day, that working copy had been compared file by file with an extraction of the ZIP, made right
  after the ZIP's SHA-256 was checked: 241 files, byte-identical.
- **No fresh comparison against the ZIP was possible at publication.**
- Instead, the full verification was rerun on the published tree itself: `scripts/verify_release.py --tests` gave
  19/19 checks and pytest 122 passed, 2 skipped, with the saved run, label and original-package checksums all
  verifying. The content scan found no references that do not belong in the public release.
- The only change after the comparison with the ZIP is this paragraph.

## 2. Input audit

| Input | Finding |
|---|---|
| `memory_xray_v02_results.zip` (canonical package, 160 files) | Matches its own preservation checksums; used as the base of the release |
| Colab code package | Code identical to the package; not duplicated in the release |
| `full_20261017T223452Z.zip` (run) | Byte-identical to `runs/full_20261017T223452Z.zip` (SHA-256 `356bec3c…`); its 66 extracted files match `records/full_run_SHA256SUMS.txt` |
| `memory_xray_figures.zip`, 7 figure images | Byte-identical to `results/figures/fig1–fig7` |
| `RESULTS_AND_DISCUSSION.md` / `.html`, `full_experiment.ipynb` | Byte-identical to the package copies (before the public-release edit in section 1) |
| `exercise_dataframes.ipynb` | Unrelated notebook; **excluded** |
| Later pilot material, sealed pilot archive | Unfinished or sealed; **excluded** and not opened |

**Consistency of code, results and report.**
- The code that produced the run is the code in the package; the design fingerprints match `scenarios/FREEZE.json`.
- Every number in the frozen report is regenerated from the saved run by `analysis_full/report_numbers.py`.
- The independent re-implementation agrees with the pipeline everywhere (largest Shapley difference 2.2 × 10⁻¹⁶).

**Documentation problems found and fixed in the release copy** (details in `CHANGES.md`):
- The original README was outdated: it described package 0.2.1 and the pre-run stage. It was replaced, and the original is
  kept in `docs/history/`.
- `reanalyze.py` failed on the full run. Its scenario folders have no `manifest.json` (the "missing manifest" issue).
- The original test suite fails on some CPUs because of a host-dependent precision assertion.
- `requirements.txt` omitted matplotlib and mixed GPU and CPU needs.
- The manifest field `protocol_amendments: [1, 2]` is incomplete. This was already documented in the report; it is left
  unedited, as the file is frozen.

## 3. Test results

| Environment | Suite | Result |
|---|---|---|
| Python 3.13.16, torch 2.14.1 (CPU), transformers 5.20.1, matplotlib 3.11.2 | full suite (`python -m pytest -q`) | **122 passed, 1 skipped** (the run-1 float16 reproduction for the `phi3` tiny model: this host's float16 kernels give a difference of exactly 0.0; the `llama` case reproduces it and passes) |
| same host; `ONEDNN_MAX_CPU_ISA=AVX512_CORE`, `ATEN_CPU_CAPABILITY=avx2`, `ATEN_CPU_CAPABILITY=default` | `tests/test_precision.py` (the replaced test) | 13 passed, 1 skipped; 13 passed, 1 skipped; 12 passed, 2 skipped. No failures |
| same host, **original suite** (for comparison) | full suite | 106 passed, **1 failed**: the host-dependent precision assertion that the release replaces (also fails with `ONEDNN_MAX_CPU_ISA=AVX512_CORE`) |
| Fresh extraction, clean venv, **Python 3.10.22**, `requirements.txt` only (no PyTorch) | full suite | **93 passed, 5 skipped** (tiny-model tests need PyTorch) |
| Fresh extraction, clean venv, **Python 3.12.15**, `requirements.txt` only (no PyTorch) | full suite | **93 passed, 5 skipped** |

`tests/test_release.py` adds 12 tests:
- the content-only rule's sets;
- byte-identical regeneration of the post hoc JSON;
- the 17/18 count;
- full-run reanalysis, which the original could not do;
- detection of perturbed runs by `compare_runs.py`;
- `KEY_NUMBERS.md` being current;
- preservation of the original files.

## 4. Reproducibility checks (`python scripts/verify_release.py`)

| Check | 3.13 (release env) | 3.12 clean venv | 3.10 clean venv |
|---|---|---|---|
| 1. 160 original files at their release paths | pass | pass | pass |
| 2. 89 run and label checksums | pass | pass | pass |
| 3. Freeze (G1 files and fingerprints) and label gate (G2) | pass | pass | pass |
| 4. Independent reanalysis, report numbers, post hoc baseline regenerated in a temporary copy, with the committed outputs deleted first | byte-identical | byte-identical | equal within 1e-12 (last-digit float differences, from Python 3.12's change to `sum()`) |
| 4. Figure scripts regenerate every committed figure file (7 + 27 + 18), from deleted outputs | byte-identical | all regenerated; not all byte-identical (different matplotlib/font stack) | all regenerated; not byte-identical |
| 4. `KEY_NUMBERS.md` matches the data | pass | pass | pass |
| 5. `reanalyze.py` on the full run and both feasibility runs reproduces every saved check outcome | pass | pass | pass |
| 6. Hygiene: no weights, sealed or unfinished pilot material, unrelated files, or files > 25 MB | pass | pass | pass |
| **Total** | **18/18** | **18/18** | **18/18** |

## 5. Documented commands, run from a fresh extraction

Every command in the README "Quick start" table was run from the final ZIP, in a clean venv on Python 3.10 and 3.12,
and on 3.13. Each exited with code 0, with one expected exception, noted at the end of the list:
- `scripts/verify_release.py`
- `pytest`
- the three `analysis_full` analysis scripts
- `reanalyze.py` on the full run, one scenario folder and both feasibility runs
- `export_figures.py` and `poster_figures.py`
- `make_key_numbers.py --check`
- the mock pipeline run
- `compare_runs.py`
- `validate_scenarios.py --verify-freeze`
- `check_labels.py`
- `make help`
- `make verify`

The exception: on Python 3.10, `make verify` fails check 1 if it runs *after* the in-place analysis scripts. Those
scripts have rewritten `results/*.json` with last-digit float differences, which check 1 correctly reports as changed
files. Run first, as the README instructs, it passes.

**Side effects, checked by hashing every file under `runs/`, `scenarios/`, `results/` and `records/` before and after:**

| Area | Result |
|---|---|
| `runs/`, `scenarios/`, `records/` | never changed |
| `results/*.json` | unchanged on Python ≥ 3.12 |
| `results/*.json` on Python 3.10 | the in-place analysis scripts rewrite them with last-digit differences; documented in the README, with `git checkout results/` to restore |
| Report figures | `analysis_full/make_figures.py` (original) overwrites them, and they are not byte-identical under other matplotlib versions. The docs therefore point to `export_figures.py`, which writes new copies |

The executed notebook `notebooks/explore_results.ipynb` runs end to end on CPU with no errors and no local paths in its
outputs.

## 6. Independent review

A separate reviewer, which had not produced the work, checked the release:
- every numeric claim in the new documents, against the frozen report and the JSON files;
- claim discipline: behavioral vs internal faithfulness, pre-registered vs post hoc, novelty, n = 6, the S-conflict
  failure, the decision mismatch, and the AI-assisted rubric;
- links;
- every documented command;
- the changed and new code;
- packaging.

Findings and their resolution are summarized below.

The review found **no critical problems**.
- Every number it checked matched the JSON files and the frozen report.
- Every documented command ran.
- No command changed a file under `runs/`, `scenarios/` or `results/`.

It raised 3 major and 11 minor findings, plus nits. All were addressed before packaging:

| Finding | Resolution |
|---|---|
| **Major:** headline takeaways overstated the decision mismatch ("labels the model never chose", "equally convincing", "whichever label is shown") | Reworded everywhere to "a label it did not choose *in that ordering*". All 8 misaligned partial citations beat chance, but they score lower on average (0.85 / 0.73 vs 0.91 / 0.88); this is now stated |
| **Major:** `docs/RELEASE_VALIDATION_REPORT.md` was missing at review time | This file |
| **Major:** check 4 of `verify_release.py` could not fail, because committed outputs were copied into the temporary folder | Committed outputs are now deleted from the copy before each script runs, and every committed figure must be regenerated. Confirmed: replacing two scripts with no-ops now fails 3 checks |
| Minor: "to within 2 × 10⁻¹⁶" (it is 2.2 × 10⁻¹⁶); flips described as "probability of the original answer" (it is P(d\*)); fig8 says 17/18 while showing 2 of 3 metrics | Corrected in text, captions and figures (fig8 now notes the third metric) |
| Minor: content-only baseline under-qualified in headlines | README, summary, poster text, captions and both workflow figures now say it uses the experimenter's design or rubric, give the 10 higher / 7 tied / 1 lower breakdown, and say it is not like-for-like. The addendum notes that its realistic-scenario top-k score is built in |
| Minor: inconsistent pre-registered / post hoc / descriptive tags | Harmonized in README, RESEARCH_SUMMARY, POSTER_TEXT and the generated KEY_NUMBERS (new "descriptive" tag) |
| Minor: rubric scope described too narrowly | README and the talk Q&A now list every use of the rubric |
| Minor: wording generalized too far (poster title; "the order decides"; "ignored the rule") | Title changed to "Does a language model cite the evidence it actually uses?"; "in our conflict test…"; "did not follow" |
| Minor: replacement precision test weaker than claimed | The original assertion is restored wherever the host shows any float16 difference, and skipped only when the difference is exactly 0.0. CHANGES now describes this accurately |
| Minor: `compare_runs.py` could report success on a very different run | Now checks cell completeness, decisions, check outcomes and flips, and applies a 0.01 tolerance to probability and Shapley differences. Tests cover a perturbed value, a missing cell and a flipped check |
| Minor: confusing `reanalyze.py` status line for run 1 | Now prints "infrastructure FAIL (I3) [I8, I9 not defined when this run was made]" |
| Minor: CC BY grant covered AI-generated label files and model-generated text | Those are now excluded explicitly in `LICENSE-CONTENT.md`. `CITATION.cff` lists both MIT and CC-BY-4.0 and validates |
| Minor: Colab notebook picked the wrong folder on a re-run | It now selects only folders with a `manifest.json`, and reanalysis writes to a fresh `outputs/reanalysis/` folder |
| Minor: README said gates G1–G4 are in the manifest | Corrected: G1–G3 are in the manifest; G4 is verified by I8/I9 |
| Nits: reference count, leftover markers, `.gitignore` comment, run-time wording, I1–I9 list, figure commands, Shapley glossary, "pre-registered code path", "parsed" replies, BC5 nuance, local folder name in the notebook | All fixed |

## 7. Not verified

- **GPU re-run.** It was not performed, as instructed. `notebooks/colab_full_experiment.ipynb` was validated as a notebook
  file and its commands were exercised with the mock backend, but it has not been run on Colab.
- **The pinned experiment environment** (`transformers==5.18.0` with Colab's PyTorch) was not installed here. The
  tiny-model tests were run with transformers 5.20.1.
- **Windows** was not tested. macOS (Apple Silicon) was tested in section 1. The `Makefile` needs `make`; every target
  has a plain Python equivalent in the README.
- **Rendering on github.com** was not checked: the Markdown, the notebook preview, and the CITATION.cff "Cite this
  repository" button. CITATION.cff validates against schema 1.2.0 with `cffconvert`.
