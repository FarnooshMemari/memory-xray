# Feasibility run log

Every run is kept, including failed ones. Run folders are never modified after they are written, and checksums are in `records/run<N>_SHA256SUMS.txt`.

| # | Run ID | Date (UTC) | Protocol | Model / commit | Precision | Result | Record |
|---|---|---|---|---|---|---|---|
| 1 | `s_single_20261017T180509Z` | 2026-10-17 18:05 | v0.2 | Phi-3-mini-4k-instruct; commit not recorded (inferred `f39ac1d2…`) | float16 storage, float16 compute | **FAILED** (I3; I8 and I9 under amendment 1). B1–B5 passed. | `run1_FAILED_feasibility_record.md` |
| 2 | `s_single_20261017T204445Z` | 2026-10-17 20:44 | v0.2 + amendment 1 | Phi-3-mini-4k-instruct @ `f39ac1d28e925b323eae81227eaba4464caced4e` (pinned, verified) | float16 storage, float32 compute, float32 logits | **PASSED Gate A**: I1–I9 and B1–B5 all pass | `run2_PASSED_verification.md` |
| 3 | `full_20261017T223452Z` (full experiment, 6 scenarios) | 2026-10-17 22:34 | v0.2 + amendments 1–4 (manifest field lists `[1, 2]`; see record) | same pinned commit, verified | float16 storage, float32 compute, float32 logits | **COMPLETED.** G1–G4 pass; I1–I9 pass in all 6 scenarios; S-single and S-redundant recovery pass; **S-conflict recovery FAILED** (BC1, BC3, BC4, BC5); realistic scenarios descriptive | `full_run_record.md`; results in `results/RESULTS_AND_DISCUSSION.md` |

**Gate A** (protocol §12): all infrastructure checks I1–I9 and all behavioral checks B1–B5 must pass in one run. **Satisfied by run 2.** The full experiment still needs explicit approval.

**Gate G2 (rubric labels):** satisfied on 2026-10-17 by independent **AI-assisted** rubric validation (GPT-6 and Gemini; amendment 4; `rubric_validation_record.md`). This is not human annotation.
