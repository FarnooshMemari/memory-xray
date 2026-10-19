# Feasibility run 1: S-single, FAILED (infrastructure)

| | |
|---|---|
| Run ID | `s_single_20261017T180509Z` |
| Date | 2026-10-17, 18:05 UTC |
| Protocol | v0.2 (before amendment 1) |
| Hardware | Google Colab, Tesla T4 |
| Software | torch 2.11.0+cu130, transformers 5.18.0, Python 3.13.15 |
| Model | `microsoft/Phi-3-mini-4k-instruct`, float16 weights **and float16 arithmetic**, eager attention |
| Model commit | **Not recorded** (`null`). Inferred as `f39ac1d28e925b323eae81227eaba4464caced4e`: the Hub's `main` commit, last modified 2025-12-10, before the run. This is inferred, not verified. |
| Outcome | **FAILED.** Infrastructure check I3 failed. Behavioral recovery B1–B5 passed. |
| Preserved files | `runs/s_single_20261017T180509Z/` and the original upload `runs/s_single_20261017T180509Z.zip`, byte-identical to each other; checksums in `records/run1_SHA256SUMS.txt`. Nothing in them has been or will be modified. |

Run 1 does not count as a passed feasibility test. Its behavioral numbers are kept for the record only.

## 1. Independent reanalysis

`reanalyze.py` recomputed the lattice, Shapley values, leave-one-out effects, the reference citation table and all checks from the saved `cells.jsonl`, `tokenization_validation.json`, `greedy_check.jsonl` and `repeatability.json`. The design fingerprint matched, and the recomputed `analysis.json` is **identical** to the one written on Colab.

| Check | Run 1 | Note |
|---|---|---|
| I1 template round trip | pass | 48/48 |
| I2 label boundaries / prefix-free / identical ids | pass | Labels are multi-token: ` Positive` = `▁Pos`+`itive`, ` Neutral` = `▁Ne`+`ut`+`ral`, ` Negative` = `▁Neg`+`ative` |
| **I3 multi-token first-token recomputation ≤ 1e-3** | **FAIL** | max 0.0617; 27/48 cells above 1e-3 |
| I4 label mass ≥ 0.95 | pass | min 0.9703, median 0.9803. Most of the remainder sits on a newline token, then `Pos` without a leading space, `<|end|>`, and `▁Un` |
| I5 greedy reproduces scored argmax | pass | 48/48 token-level matches (greedy text `Positive<|end|>` or `Neutral<|end|>`) |
| I6 repeatability | pass | max diff 0.0 |
| I7 completeness | pass | 48 cells |
| I8 commit pinned and verified (added in amendment 1) | FAIL | commit not recorded |
| I9 float32 logits (added in amendment 1) | FAIL | run used float16 arithmetic |
| B1–B5 | pass | Decisive-record share of the total effect is 0.9997 or more; distractor \|φ\| ≤ 0.0003 |

## 2. What caused the I3 discrepancy

**It is float16 rounding of the logits, not an indexing error.**

The evidence:

1. **The differences are quantized at the float16 spacing.** Phi-3's logits are around 30–60, and in float16 adjacent representable values in [32, 64) are 2⁻⁵ = 0.03125 apart.
   - All 48 recomputation differences lie within 0.027 of a whole number of these steps: 21 cells differ by 0 steps, 26 by 1 step and 1 by 2 steps (the 0.0617 maximum).
   - The 27 cells above 1e-3 are exactly the cells off by one or two steps.
2. **Why the two passes differ at all.** I3 compares the first label token's log-prob from the prompt-only forward pass with the same value recomputed in the longer prompt+label pass. The two passes have different sequence lengths, so the GPU kernels accumulate in a different order, and results near a rounding boundary land on neighboring float16 values.
3. **It is not an indexing error.** A wrong position or token would cause errors of several nats, not one float16 step. Indexing is also cross-checked independently:
   - I5: greedy decoding matched the scored label tokens in 48/48 cells;
   - I6: re-scoring was exactly repeatable;
   - offline tests: scores match an independent full-sequence computation, and the scored position matches `generate()`.
4. **Reproduced offline on the real `Phi3ForCausalLM` class**, using a tiny model with its output head scaled so the logits are about 50:

| Setup | Max label log-prob error vs. a float32 reference | I3 recompute difference |
|---|---|---|
| float16 weights, float16 arithmetic (run 1) | 0.0605 nats | 0.0020 (fails 1e-3) |
| float16 weights, float32 arithmetic (amendment 1) | 0 (bit-identical) | 1.9e-06 |

This is locked in as a regression test (`tests/test_precision.py`, `tests/test_pipeline.py`).

## 3. Impact on run 1's numbers

Every label log-prob was perturbed by ±0.0617 nats, the observed maximum, in the worst-case direction:

- **P(d\*):** changes by at most 2.3 × 10⁻⁴ in any cell.
- **Shapley values:** change by at most 4.6 × 10⁻⁴ (Shapley is linear in v, so the bound is twice the largest change in v).

All B1–B5 conclusions are therefore unaffected. This is only because S-single's probabilities are close to 0 or 1.

The same rounding at mid-range probabilities would be material. A 0.0617-nat error shifts P = 0.5 by up to 0.031, P = 0.7 by 0.025 and P = 0.9 by 0.011, which is large enough to distort Shapley values in the realistic scenarios. So the threshold was not relaxed; the arithmetic was fixed.

## 4. Why the commit was not recorded

The scorer read `model.config._commit_hash`. Transformers 5.18 leaves that field empty, so the manifest recorded `null`, and the run was not pinned because no revision was passed.

## 5. Fixes (protocol v0.2, amendment 1)

1. **Float32 arithmetic with float16 storage.**
   - Weights stay in float16 so the model fits a T4. Each decoder layer is cast to float32 just for its forward pass and cast back afterwards; float16 → float32 → float16 is exact, so stored weights never change.
   - The embedding output is upcast, and the final norm and output head run in float32, so logits are float32.
   - Converting the bf16 checkpoint to float16 is exact except for weights below the float16 normal range (|w| < 2⁻¹⁴). Their fraction is recorded in the manifest.
2. **Pinned, verified commit.**
   - The default revision is `f39ac1d28e925b323eae81227eaba4464caced4e`. A branch name is resolved to a commit before loading, and the tokenizer and weights load from that commit.
   - After loading, the code verifies that the config came from that commit's snapshot folder.
   - The run aborts before loading if any of this fails.
3. **New checks I8 and I9**, which add requirements; no existing threshold was relaxed:
   - I8: the commit is recorded and verified;
   - I9: logits are float32 and stored weight dtypes are unchanged after a forward pass.
4. `reanalyze.py` now writes to a sibling folder and never adds files inside a run folder.

The scenario, every I1–I7 threshold and every B1–B5 threshold are unchanged.

## 6. Status

- Run 1: preserved as a failed feasibility record.
- Corrected S-single rerun: prepared (`colab/feasibility_s_single.ipynb`), **not launched**.
- Full experiment: not started.
