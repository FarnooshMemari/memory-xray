# Full experiment: macro_c

- Run ID: `full_20261017T223452Z/macro_c`
- Model: `microsoft/Phi-3-mini-4k-instruct` on Tesla T4
- Commit: `f39ac1d28e925b323eae81227eaba4464caced4e` (source: pinned_sha, verified: True)
- Precision: float16 storage / float32 compute; logits torch.float32
- Design fingerprint: `8533ac1724e5bcb4...`
- Scored cells: 48 (forward passes: 192)

**Infrastructure checks: PASS**  
**Behavioral recovery: n/a (realistic scenario; descriptive analysis only)**

## Infrastructure checks

| ID | Check | Result | Detail |
|---|---|---|---|
| I1 | chat-template round trip | pass | 48/48 cells match |
| I2 | label token boundaries, prefix-free labels, identical label ids across cells | pass | 0 tokenization errors; 1 distinct label-id sets |
| I3 | finite log-probs; consistent multi-token recomputation | pass | 0 non-finite cells; max first-token recompute diff 1.08e-04 |
| I4 | label mass >= 0.95 in every cell | pass | min 0.9792, median 0.9936 |
| I5 | greedy decoding reproduces the scored argmax (cells with margin >= 0.1) | pass | 48/48 eligible cells match; 48/48 of all cells |
| I6 | re-scoring repeatability (max \|delta log p\| <= 0.001) | pass | 3 cells re-scored; max diff 0.00e+00 |
| I7 | completeness: 16 subsets x 3 orderings | pass | 48 cells, 48 unique |
| I8 | model commit pinned and verified | pass | commit f39ac1d28e925b323eae81227eaba4464caced4e (pinned_sha); verified in cache: True |
| I9 | float32 logits; stored weights unchanged | pass | logits torch.float32; storage float16, compute float32; layer weight dtypes after forward ['torch.float16'] |

## Decision and baseline

- d* (argmax of ordering-averaged full-evidence distribution): **Negative**; designed answer: Negative
- Full-set argmax per ordering: ['Negative', 'Negative', 'Negative']
- v(full) = P(d* | all records): 0.941 [0.934, 0.952]
- v(empty) = P(d* | no records): 0.014 [0.014, 0.014]

Values are mean [min, max] across the 3 fixed orderings: a description of ordering sensitivity, not a confidence interval.

## Behavioral attribution

Shapley values and leave-one-out effects on P(d*), in probability units. These attribute the model's output to the supplied records; they are not evidence about internal reasoning.

| Record | Shapley mean [min, max] | Leave-one-out mean [min, max] |
|---|---|---|
| E1 | -0.021 [-0.043, -0.002] | -0.021 [-0.030, -0.008] |
| E2 | 0.347 [0.332, 0.361] | 0.065 [0.054, 0.071] |
| E3 | 0.281 [0.267, 0.298] | 0.038 [0.029, 0.048] |
| E4 | 0.320 [0.293, 0.352] | 0.049 [0.014, 0.114] |

Shapley sums per ordering (should equal v(full) - v(empty)): 0.9203, 0.9385, 0.9234

## Subset lattice

| Subset | Designed | P(d*) per ordering | Argmax per ordering |
|---|---|---|---|
| none | Neutral | 0.014, 0.014, 0.014 | Neutral, Neutral, Neutral |
| E1 | Neutral | 0.168, 0.167, 0.166 | Neutral, Neutral, Neutral |
| E2 | Neutral | 0.952, 0.949, 0.956 | Negative, Negative, Negative |
| E3 | Neutral | 0.891, 0.888, 0.891 | Negative, Negative, Negative |
| E4 | Neutral | 0.919, 0.916, 0.920 | Negative, Negative, Negative |
| E1+E2 | Neutral | 0.826, 0.854, 0.783 | Negative, Negative, Negative |
| E1+E3 | Neutral | 0.819, 0.569, 0.534 | Negative, Negative, Negative |
| E1+E4 | Neutral | 0.800, 0.805, 0.819 | Negative, Negative, Negative |
| E2+E3 | Negative | 0.962, 0.966, 0.954 | Negative, Negative, Negative |
| E2+E4 | Negative | 0.940, 0.957, 0.952 | Negative, Negative, Negative |
| E3+E4 | Negative | 0.897, 0.913, 0.941 | Negative, Negative, Negative |
| E1+E2+E3 | Neutral | 0.921, 0.934, 0.823 | Negative, Negative, Negative |
| E1+E2+E4 | Neutral | 0.898, 0.904, 0.908 | Negative, Negative, Negative |
| E1+E3+E4 | Neutral | 0.880, 0.882, 0.867 | Negative, Negative, Negative |
| E2+E3+E4 | Negative | 0.958, 0.961, 0.967 | Negative, Negative, Negative |
| E1+E2+E3+E4 | Negative | 0.934, 0.952, 0.937 | Negative, Negative, Negative |

## Reference: how candidate citation sets would score

Not model citations (citation sampling is not part of this test). This shows the metric on this lattice. Empty and all-four sets are separate categories with no beat fractions.

| Cited | Category | Necessity | Sufficiency | Beat (necessity) | Beat (sufficiency) |
|---|---|---|---|---|---|
| none | empty | 0.000 [0.000, 0.000] | -0.927 [-0.938, -0.920] | n/a | n/a |
| E1 | partial | -0.021 [-0.030, -0.008] | -0.774 [-0.785, -0.766] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| E2 | partial | 0.065 [0.054, 0.071] | 0.011 [-0.003, 0.019] | 0.89 [0.67, 1.00] | 1.00 [1.00, 1.00] |
| E3 | partial | 0.038 [0.029, 0.048] | -0.051 [-0.065, -0.043] | 0.56 [0.33, 0.67] | 0.33 [0.33, 0.33] |
| E4 | partial | 0.049 [0.014, 0.114] | -0.023 [-0.036, -0.015] | 0.56 [0.33, 1.00] | 0.67 [0.67, 0.67] |
| E1+E2+E3+E4 | all | 0.927 [0.920, 0.938] | 0.000 [0.000, 0.000] | n/a | n/a |

All 16 rows are in `analysis.json`.

## Counterfactual flip

- Flipped record: E4 (rubric reference after the flip: Neutral)
- Full-set argmax with the flip, per ordering: ['Neutral', 'Negative', 'Negative']; moved away from d* in all orderings: False
- P(d*) original → flipped, per ordering: 0.934 → 0.398, 0.952 → 0.563, 0.937 → 0.494
- Diagnostics: finite True, min label mass 0.985, greedy matches 3/3

## Citations

Descriptive summaries of 10 sampled citations and 3 greedy reference citations. Beat fractions use the exact same-size null (chance = 0.5) with differences under 0.01 in P(d*) counted as ties; empty and all-record citations are counted separately and excluded from beat fractions. No significance tests.

- Sampled: 10; parse statuses {'unparseable': 3, 'ok': 7}; analyzable 7
- Categories {'all': 2, 'partial': 5}; sizes {4: 2, 3: 5}
- Cited sets {'E1+E2+E3+E4': 2, 'E2+E3+E4': 5}; modal E2+E3+E4 (0.71)
- Partial citations: 5; mean beat (necessity) 1.00, mean beat (sufficiency) 1.00; share > 0.5: 1.00 / 1.00; mean Shapley top-k agreement 1.00

| Greedy citation | Status | Cited | Category | Beat (nec.) | Beat (suff.) |
|---|---|---|---|---|---|
| ordering 0 | ok | E2+E4 | partial | 0.70 | 0.80 |
| ordering 1 | ok | E1+E2+E4 | partial | 0.67 | 0.33 |
| ordering 2 | ok | E1+E2+E3+E4 | all | n/a | n/a |
