# Memory X-Ray v0.2 (amendments 1–4): experiment infrastructure

This is the code for protocol v0.2 (`PROTOCOL_v0.2.md`; amendments in §17). It is a standalone folder: it reads and writes nothing outside itself and never touches the v0.1 protocol or the earlier Gemini results.

**Current stage:** the full experiment has been **run and analyzed** (`runs/full_20261017T223452Z/`, record in `records/full_run_record.md`). Results, discussion and presentation figures are in `results/RESULTS_AND_DISCUSSION.md` and `results/figures/`. To reproduce the analysis without a model, run `analysis_full/independent_reanalysis.py`, then `report_numbers.py`, then `make_figures.py`. The rest of this README describes the pre-run setup.
- Feasibility run 1 failed (I3, float16 arithmetic) and run 2 passed Gate A. Both are preserved unmodified in `runs/`, with records in `records/`.
- Six scenarios, a shared rubric and the validation criteria were validated offline and frozen (`scenarios/FREEZE.json`) before any model test of the five new scenarios.
- The full run needs gates G1–G4: freeze verified, rubric labels, explicit approval, and the pinned commit.
- G2 is satisfied by independent AI-assisted rubric validation (GPT-6 and Gemini; amendment 4). This is not human annotation.

**Model:** `microsoft/Phi-3-mini-4k-instruct`, pinned to commit `f39ac1d28e925b323eae81227eaba4464caced4e`. Weights are stored in float16, and all arithmetic runs in float32.

## Full experiment (after approval)

1. The rubric labels are done (AI-assisted, amendment 4). `python check_labels.py` should print OK.
2. Zip the folder, open `colab/full_experiment.ipynb` on a T4, upload the zip, set `APPROVED_BY` and run all cells.
3. Results are written to `runs/full_<UTC>/` (`SUMMARY.md`, plus one folder per scenario).

Other commands:

```bash
python validate_scenarios.py --verify-freeze                   # G1
python check_labels.py                                         # G2 (read-only)
python run_experiment.py --backend mock --skip-label-gate      # pipeline exercise only (MOCK)
```

## Feasibility test (historical: runs 1–2)

1. Open `colab/feasibility_s_single.ipynb, colab/full_experiment.ipynb` in Colab and choose **Runtime → Change runtime type → T4 GPU**.
2. Run all cells. When asked, upload the new `memory_xray_v02.zip`. The notebook checks that the package version is `0.2.1`, so stale code can't run.
3. The notebook does the following, in order:
   - installs dependencies;
   - runs the offline unit tests;
   - downloads `microsoft/Phi-3-mini-4k-instruct` (about 7.6 GB);
   - runs the test and shows `REPORT.md`;
   - downloads the run folder as a zip.
4. Send back the zipped run folder. `python reanalyze.py runs/<run_id>` recomputes every number from the saved files without a model.

Float32 arithmetic is slower than run 1 was, but the test should still take a few minutes on a T4 once the model is downloaded.

## Run locally instead

You need about 16 GB of free RAM for float32 on CPU, or a GPU with 8 GB or more.

```bash
pip install -r requirements.txt
python -m pytest -q
python run_feasibility.py   # defaults: pinned model + commit, float16 storage on GPU, float32 compute
```

A branch name passed as `--revision` is resolved to a commit before loading. The run aborts if the commit can't be resolved, loaded and verified.

## What the runner does

| Stage | What happens | Stops the run on failure? |
|---|---|---|
| 0 | Resolve and verify the model commit; precision probe (float32 logits, stored weights unchanged) | Yes, before loading or scoring |
| 1 | Tokenization validation for all 48 prompts: chat-template round trip, clean label token boundaries, prefix-free labels, identical label ids everywhere | Yes, before any scoring |
| 2 | Scores ` Positive`, ` Neutral`, ` Negative` after the forced `Signal:` prefix (sum of token log-probs) | No |
| 3 | Greedy decoding of each cell to confirm it reproduces the scored argmax label | No |
| 4 | Re-scores 3 cells to check repeatability | No |
| 5 | Computes d\*, the lattice of P(d\*), exact Shapley values, leave-one-out effects and a reference citation table; evaluates checks I1–I9 and B1–B5 (protocol §9); writes `REPORT.md` | — |

Every run writes to a new `runs/<run_id>/` folder and refuses to overwrite an existing one.

### Outputs in `runs/<run_id>/`

| File | Contents |
|---|---|
| `manifest.json` | Model, verified commit, storage and compute dtypes, logits dtype, device, versions, design fingerprint, pass/fail |
| `tokenization_validation.json` | Label token ids and tokens for every cell |
| `cells.jsonl` | One line per cell: rendered prompt, per-token log-probs, raw and normalized label probabilities, label mass, top-5 next tokens |
| `greedy_check.jsonl` | Greedy cross-check of each cell |
| `repeatability.json` | Re-scoring differences |
| `analysis.json` | Lattice, Shapley and leave-one-out per ordering, spreads, reference citation table |
| `checks.json` | The I and B checks |
| `REPORT.md` | Human-readable summary of all of the above |

## Layout

```
PROTOCOL_v0.2.md            approved design, thresholds, gates, amendments (§17)
APPROVAL_PACKET_full_experiment.md   scenarios, expected behavior, criteria, execution plan
scenarios/                  six frozen scenarios, rubric, criteria, FREEZE.json, VALIDATION_REPORT.md
validate_scenarios.py       offline scenario validation, freeze and freeze verification
run_experiment.py           full experiment (gates G1-G4; not run yet)
mxr/pipeline.py, citation_analysis.py, scenario_validation.py
records/                    run log, run-1 failure record, run-1 checksums
runs/                       preserved runs (never modified)
scenarios/s_single.json     frozen S-single control
mxr/design.py               subsets, fixed orderings, opaque IDs, prompt templates, fingerprint
mxr/scoring.py              label-probability scorer + tokenization validation
mxr/metrics.py              necessity, sufficiency, exact Shapley, LOO, citation consistency
mxr/citations.py            citation turn + strict parser (implemented; not run yet)
mxr/analysis.py, checks.py, report.py
mxr/mock.py                 rule-based MOCK scorer for pipeline tests only
run_feasibility.py          feasibility runner
reanalyze.py                recompute everything from a saved run (writes a sibling folder)
tests/                      unit tests and offline end-to-end tests (tiny random HF model)
colab/feasibility_s_single.ipynb, colab/full_experiment.ipynb
```

## Interpreting the numbers

- Shapley, leave-one-out, necessity and sufficiency are **behavioral attributions** of the model's output to the supplied records. They are not ground truth about internal reasoning.
- Ranges are min–max across the 3 fixed orderings. They describe ordering sensitivity and are **not** confidence intervals.
- The B checks are **validation checks** that the measurement recovers the planted structure. They are not statistical hypothesis tests.
- The empty and all-four citation sets are separate categories with no beat fractions.
