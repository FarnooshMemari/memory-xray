# Feasibility run 2: S-single, PASSED (independent verification)

| | |
|---|---|
| Run ID | `s_single_20261017T204445Z` |
| Date | 2026-10-17, 20:44 UTC; 265 s elapsed |
| Protocol | v0.2 + amendment 1 |
| Hardware / software | Google Colab Tesla T4; torch 2.11.0+cu130, transformers 5.18.0, Python 3.13.15 |
| Model | `microsoft/Phi-3-mini-4k-instruct` @ `f39ac1d28e925b323eae81227eaba4464caced4e` (source: pinned sha; snapshot verified) |
| Precision | float16 storage, float32 compute, float32 logits. Stored weight dtypes are unchanged after a forward pass. 0.144% of weights fall in the float16 subnormal range; only these can differ from the bf16 checkpoint. |
| Design fingerprint | Identical to run 1 (the scenario and prompts are unchanged) |
| Preserved files | `runs/s_single_20261017T204445Z/` plus the original upload `.zip`, byte-identical; checksums in `run2_SHA256SUMS.txt` |

## Independent reanalysis

`reanalyze.py` was run on the saved files. The recomputed `analysis.json` and `checks.json` are **identical** to the Colab outputs.

| Check | Result | Detail |
|---|---|---|
| I1 | pass | 48/48 template round trips |
| I2 | pass | 0 tokenization errors; 1 label-id set |
| I3 | pass | max first-token recomputation difference 8.3e-05 (threshold 1e-3; run 1 was 6.2e-02) |
| I4 | pass | label mass min 0.9703 |
| I5 | pass | 48/48 greedy token matches |
| I6 | pass | re-scoring difference 0.0 |
| I7 | pass | 48 cells |
| I8 | pass | commit pinned and verified in the cache |
| I9 | pass | float32 logits; weights remain float16 |
| B1–B4 | pass | Positive at the full set and at {E2}; Neutral at {E1,E3,E4}; 16/16 designed agreement in every ordering |
| B5 | pass | φ(E2) = 0.9989, 0.9992 and 0.9991 by ordering; \|φ(distractor)\| ≤ 0.0003 |

**Shapley values, recomputed with a different algorithm.** Averaging marginal contributions over all 24 orderings of the four records reproduces the reported subset-formula values to within 1.1e-16.

**Run 1 compared with run 2.** The largest difference in P_norm over all 48 cells and 3 labels is 5.9e-05, inside the worst-case bound of 2.3e-04 estimated for run 1. This confirms that run 1's float16 error did not affect its behavioral conclusions, although run 1 still stands as a failed run.

**Conclusion.** Gate A is satisfied. The pipeline measures influence correctly on the single-decisive control.
