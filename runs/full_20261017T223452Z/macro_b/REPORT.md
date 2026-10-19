# Full experiment: macro_b

- Run ID: `full_20261017T223452Z/macro_b`
- Model: `microsoft/Phi-3-mini-4k-instruct` on Tesla T4
- Commit: `f39ac1d28e925b323eae81227eaba4464caced4e` (source: pinned_sha, verified: True)
- Precision: float16 storage / float32 compute; logits torch.float32
- Design fingerprint: `2d8007c462baebfe...`
- Scored cells: 48 (forward passes: 192)

**Infrastructure checks: PASS**  
**Behavioral recovery: n/a (realistic scenario; descriptive analysis only)**

## Infrastructure checks

| ID | Check | Result | Detail |
|---|---|---|---|
| I1 | chat-template round trip | pass | 48/48 cells match |
| I2 | label token boundaries, prefix-free labels, identical label ids across cells | pass | 0 tokenization errors; 1 distinct label-id sets |
| I3 | finite log-probs; consistent multi-token recomputation | pass | 0 non-finite cells; max first-token recompute diff 0.00e+00 |
| I4 | label mass >= 0.95 in every cell | pass | min 0.9792, median 0.9920 |
| I5 | greedy decoding reproduces the scored argmax (cells with margin >= 0.1) | pass | 46/46 eligible cells match; 48/48 of all cells |
| I6 | re-scoring repeatability (max \|delta log p\| <= 0.001) | pass | 3 cells re-scored; max diff 0.00e+00 |
| I7 | completeness: 16 subsets x 3 orderings | pass | 48 cells, 48 unique |
| I8 | model commit pinned and verified | pass | commit f39ac1d28e925b323eae81227eaba4464caced4e (pinned_sha); verified in cache: True |
| I9 | float32 logits; stored weights unchanged | pass | logits torch.float32; storage float16, compute float32; layer weight dtypes after forward ['torch.float16'] |

Flags (descriptive):
- ordering sensitivity: range of phi(E1) across orderings is 0.101 (> 0.1)

## Decision and baseline

- d* (argmax of ordering-averaged full-evidence distribution): **Negative**; designed answer: Negative
- Full-set argmax per ordering: ['Negative', 'Negative', 'Negative']
- v(full) = P(d* | all records): 0.810 [0.733, 0.854]
- v(empty) = P(d* | no records): 0.014 [0.014, 0.014]

Values are mean [min, max] across the 3 fixed orderings: a description of ordering sensitivity, not a confidence interval.

## Behavioral attribution

Shapley values and leave-one-out effects on P(d*), in probability units. These attribute the model's output to the supplied records; they are not evidence about internal reasoning.

| Record | Shapley mean [min, max] | Leave-one-out mean [min, max] |
|---|---|---|
| E1 | 0.231 [0.167, 0.268] | 0.109 [0.018, 0.193] |
| E2 | 0.436 [0.415, 0.469] | 0.240 [0.140, 0.387] |
| E3 | -0.220 [-0.277, -0.186] | -0.116 [-0.179, -0.083] |
| E4 | 0.349 [0.334, 0.360] | 0.143 [0.102, 0.215] |

Shapley sums per ordering (should equal v(full) - v(empty)): 0.7194, 0.8296, 0.8397

## Subset lattice

| Subset | Designed | P(d*) per ordering | Argmax per ordering |
|---|---|---|---|
| none | Neutral | 0.014, 0.014, 0.014 | Neutral, Neutral, Neutral |
| E1 | Neutral | 0.636, 0.645, 0.639 | Negative, Negative, Negative |
| E2 | Neutral | 0.949, 0.947, 0.951 | Negative, Negative, Negative |
| E3 | Neutral | 0.006, 0.006, 0.006 | Positive, Positive, Positive |
| E4 | Neutral | 0.893, 0.886, 0.892 | Negative, Negative, Negative |
| E1+E2 | Negative | 0.901, 0.908, 0.943 | Negative, Negative, Negative |
| E1+E3 | Neutral | 0.087, 0.264, 0.265 | Positive, Positive, Positive |
| E1+E4 | Negative | 0.841, 0.848, 0.891 | Negative, Negative, Negative |
| E2+E3 | Neutral | 0.435, 0.549, 0.431 | Negative, Negative, Negative |
| E2+E4 | Negative | 0.941, 0.946, 0.943 | Negative, Negative, Negative |
| E3+E4 | Neutral | 0.299, 0.377, 0.283 | Neutral, Neutral, Positive |
| E1+E2+E3 | Neutral | 0.518, 0.741, 0.742 | Negative, Negative, Negative |
| E1+E2+E4 | Negative | 0.913, 0.929, 0.937 | Negative, Negative, Negative |
| E1+E3+E4 | Neutral | 0.347, 0.651, 0.714 | Neutral, Negative, Negative |
| E2+E3+E4 | Neutral | 0.716, 0.650, 0.737 | Negative, Negative, Negative |
| E1+E2+E3+E4 | Negative | 0.733, 0.844, 0.854 | Negative, Negative, Negative |

## Reference: how candidate citation sets would score

Not model citations (citation sampling is not part of this test). This shows the metric on this lattice. Empty and all-four sets are separate categories with no beat fractions.

| Cited | Category | Necessity | Sufficiency | Beat (necessity) | Beat (sufficiency) |
|---|---|---|---|---|---|
| none | empty | 0.000 [0.000, 0.000] | -0.796 [-0.840, -0.719] | n/a | n/a |
| E1 | partial | 0.109 [0.018, 0.193] | -0.170 [-0.215, -0.097] | 0.56 [0.33, 0.83] | 0.33 [0.33, 0.33] |
| E2 | partial | 0.240 [0.140, 0.387] | 0.139 [0.097, 0.216] | 0.94 [0.83, 1.00] | 1.00 [1.00, 1.00] |
| E3 | partial | -0.116 [-0.179, -0.083] | -0.804 [-0.848, -0.728] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| E4 | partial | 0.143 [0.102, 0.215] | 0.080 [0.039, 0.159] | 0.50 [0.33, 0.67] | 0.67 [0.67, 0.67] |
| E1+E2+E3+E4 | all | 0.796 [0.719, 0.840] | 0.000 [0.000, 0.000] | n/a | n/a |

All 16 rows are in `analysis.json`.

## Counterfactual flip

- Flipped record: E2 (rubric reference after the flip: Neutral)
- Full-set argmax with the flip, per ordering: ['Neutral', 'Neutral', 'Negative']; moved away from d* in all orderings: False
- P(d*) original → flipped, per ordering: 0.733 → 0.330, 0.844 → 0.366, 0.854 → 0.688
- Diagnostics: finite True, min label mass 0.986, greedy matches 3/3

## Citations

Descriptive summaries of 10 sampled citations and 3 greedy reference citations. Beat fractions use the exact same-size null (chance = 0.5) with differences under 0.01 in P(d*) counted as ties; empty and all-record citations are counted separately and excluded from beat fractions. No significance tests.

- Sampled: 10; parse statuses {'empty': 1, 'ok': 8, 'unparseable': 1}; analyzable 9
- Categories {'empty': 1, 'partial': 8}; sizes {0: 1, 3: 4, 2: 3, 1: 1}
- Cited sets {'none': 1, 'E1+E2+E3': 1, 'E2+E4': 1, 'E1+E2': 2, 'E1+E2+E4': 3, 'E2': 1}; modal E1+E2+E4 (0.33)
- Partial citations: 8; mean beat (necessity) 0.87, mean beat (sufficiency) 0.88; share > 0.5: 0.88 / 0.88; mean Shapley top-k agreement 0.83

| Greedy citation | Status | Cited | Category | Beat (nec.) | Beat (suff.) |
|---|---|---|---|---|---|
| ordering 0 | ok | E1+E2+E3+E4 | all | n/a | n/a |
| ordering 1 | ok | E1+E2+E4 | partial | 1.00 | 1.00 |
| ordering 2 | ok | E1+E4 | partial | 0.60 | 0.60 |
