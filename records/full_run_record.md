# Record: full experiment run `full_20261017T223452Z`

- **Received:** 2026-10-17, as the results ZIP uploaded by the investigator (Farnoosh Memari).
- **Preserved:** `runs/full_20261017T223452Z/` and `runs/full_20261017T223452Z.zip`, both byte-identical to the upload. The 67 file checksums are in `records/full_run_SHA256SUMS.txt`; verify from the `runs/` folder with `sha256sum -c ../records/full_run_SHA256SUMS.txt`.
- **Not modified:** the run folder, the frozen scenarios, the thresholds, the parser, and every pipeline module.

## Verification

- **Gates:**
  - G1: the freeze hashes and design fingerprints match the package.
  - G2: AI-assisted rubric validation (GPT-6 and Gemini, 15/15 agreement); this is not human annotation.
  - G3: approved by Farnoosh Memari.
  - G4: the pinned commit was loaded and verified (I8).
- **Independent reanalysis.** `analysis_full/independent_reanalysis.py` was written separately from the `mxr` metric, check and citation code and recomputes everything from the raw log-probabilities and the raw citation text. It agrees with the pipeline in all 6 scenarios: probabilities and leave-one-out values match exactly, Shapley values differ by at most 2.2e-16, and the check outcomes, parse statuses and consistency values are identical.

## Outcome (pre-registered)

| Scenario | Infrastructure (I1–I9) | Recovery checks |
|---|---|---|
| S-single | pass | B1–B5 pass |
| S-redundant | pass | BR1–BR6 pass |
| S-conflict | pass | **BC1, BC3, BC4 and BC5 fail**; BC2 passes |
| Macro A, B, C | pass | descriptive only |

Full analysis: `results/RESULTS_AND_DISCUSSION.md`.

## Metadata inaccuracy (documented, not corrected in the run)

`manifest.json` reports `"protocol_amendments": [1, 2]`. The value is hard-coded in `run_experiment.py`. The run itself executed the amendment-3 G2 gate (`declared_labelers_match`, `inter_labeler_disagreements`), and its manifest carries the amendment-4 `rubric_validation` block (`"protocol_amendment": 4`). The correct list is `[1, 2, 3, 4]`.

The field is descriptive only. It feeds no computation, and every result is unaffected. The run file is left as written. If the code is touched again, the hard-coded value should be fixed for future runs.
