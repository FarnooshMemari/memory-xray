# Full experiment: macro_a

- Run ID: `full_20261017T223452Z/macro_a`
- Model: `microsoft/Phi-3-mini-4k-instruct` on Tesla T4
- Commit: `f39ac1d28e925b323eae81227eaba4464caced4e` (source: pinned_sha, verified: True)
- Precision: float16 storage / float32 compute; logits torch.float32
- Design fingerprint: `64dd7b4f92b36ea8...`
- Scored cells: 48 (forward passes: 192)

**Infrastructure checks: PASS**  
**Behavioral recovery: n/a (realistic scenario; descriptive analysis only)**

## Infrastructure checks

| ID | Check | Result | Detail |
|---|---|---|---|
| I1 | chat-template round trip | pass | 48/48 cells match |
| I2 | label token boundaries, prefix-free labels, identical label ids across cells | pass | 0 tokenization errors; 1 distinct label-id sets |
| I3 | finite log-probs; consistent multi-token recomputation | pass | 0 non-finite cells; max first-token recompute diff 1.40e-05 |
| I4 | label mass >= 0.95 in every cell | pass | min 0.9790, median 0.9889 |
| I5 | greedy decoding reproduces the scored argmax (cells with margin >= 0.1) | pass | 44/44 eligible cells match; 48/48 of all cells |
| I6 | re-scoring repeatability (max \|delta log p\| <= 0.001) | pass | 3 cells re-scored; max diff 0.00e+00 |
| I7 | completeness: 16 subsets x 3 orderings | pass | 48 cells, 48 unique |
| I8 | model commit pinned and verified | pass | commit f39ac1d28e925b323eae81227eaba4464caced4e (pinned_sha); verified in cache: True |
| I9 | float32 logits; stored weights unchanged | pass | logits torch.float32; storage float16, compute float32; layer weight dtypes after forward ['torch.float16'] |

Flags (descriptive):
- ordering sensitivity: range of phi(E3) across orderings is 0.124 (> 0.1)
- full-set argmax differs across orderings

## Decision and baseline

- d* (argmax of ordering-averaged full-evidence distribution): **Positive**; designed answer: Positive
- Full-set argmax per ordering: ['Neutral', 'Positive', 'Positive']
- v(full) = P(d* | all records): 0.406 [0.236, 0.554]
- v(empty) = P(d* | no records): 0.000 [0.000, 0.000]

Values are mean [min, max] across the 3 fixed orderings: a description of ordering sensitivity, not a confidence interval.

## Behavioral attribution

Shapley values and leave-one-out effects on P(d*), in probability units. These attribute the model's output to the supplied records; they are not evidence about internal reasoning.

| Record | Shapley mean [min, max] | Leave-one-out mean [min, max] |
|---|---|---|
| E1 | 0.233 [0.191, 0.283] | 0.187 [0.072, 0.302] |
| E2 | 0.286 [0.255, 0.318] | 0.184 [0.093, 0.258] |
| E3 | -0.479 [-0.542, -0.418] | -0.507 [-0.665, -0.355] |
| E4 | 0.365 [0.332, 0.393] | 0.179 [0.125, 0.242] |

Shapley sums per ordering (should equal v(full) - v(empty)): 0.2362, 0.5535, 0.4275

## Subset lattice

| Subset | Designed | P(d*) per ordering | Argmax per ordering |
|---|---|---|---|
| none | Neutral | 0.000, 0.000, 0.000 | Neutral, Neutral, Neutral |
| E1 | Neutral | 0.633, 0.648, 0.624 | Positive, Positive, Positive |
| E2 | Neutral | 0.776, 0.763, 0.794 | Positive, Positive, Positive |
| E3 | Neutral | 0.001, 0.001, 0.000 | Negative, Negative, Negative |
| E4 | Neutral | 0.966, 0.963, 0.963 | Positive, Positive, Positive |
| E1+E2 | Positive | 0.915, 0.923, 0.754 | Positive, Positive, Positive |
| E1+E3 | Neutral | 0.008, 0.027, 0.034 | Negative, Negative, Negative |
| E1+E4 | Positive | 0.838, 0.871, 0.919 | Positive, Positive, Positive |
| E2+E3 | Neutral | 0.002, 0.028, 0.016 | Negative, Negative, Negative |
| E2+E4 | Positive | 0.902, 0.935, 0.935 | Positive, Positive, Positive |
| E3+E4 | Neutral | 0.094, 0.168, 0.071 | Neutral, Neutral, Neutral |
| E1+E2+E3 | Neutral | 0.111, 0.382, 0.186 | Negative, Positive, Negative |
| E1+E2+E4 | Positive | 0.901, 0.909, 0.930 | Positive, Positive, Positive |
| E1+E3+E4 | Neutral | 0.143, 0.296, 0.227 | Neutral, Neutral, Neutral |
| E2+E3+E4 | Neutral | 0.164, 0.252, 0.240 | Neutral, Neutral, Neutral |
| E1+E2+E3+E4 | Positive | 0.236, 0.554, 0.428 | Neutral, Positive, Positive |

## Reference: how candidate citation sets would score

Not model citations (citation sampling is not part of this test). This shows the metric on this lattice. Empty and all-four sets are separate categories with no beat fractions.

| Cited | Category | Necessity | Sufficiency | Beat (necessity) | Beat (sufficiency) |
|---|---|---|---|---|---|
| none | empty | 0.000 [0.000, 0.000] | -0.406 [-0.554, -0.236] | n/a | n/a |
| E1 | partial | 0.187 [0.072, 0.302] | 0.229 [0.094, 0.397] | 0.56 [0.33, 1.00] | 0.33 [0.33, 0.33] |
| E2 | partial | 0.184 [0.093, 0.258] | 0.372 [0.210, 0.539] | 0.67 [0.67, 0.67] | 0.67 [0.67, 0.67] |
| E3 | partial | -0.507 [-0.665, -0.355] | -0.405 [-0.553, -0.236] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| E4 | partial | 0.179 [0.125, 0.242] | 0.558 [0.410, 0.729] | 0.78 [0.33, 1.00] | 1.00 [1.00, 1.00] |
| E1+E2+E3+E4 | all | 0.406 [0.236, 0.554] | 0.000 [0.000, 0.000] | n/a | n/a |

All 16 rows are in `analysis.json`.

## Counterfactual flip

- Flipped record: E1 (rubric reference after the flip: Neutral)
- Full-set argmax with the flip, per ordering: ['Neutral', 'Neutral', 'Neutral']; moved away from d* in all orderings: True
- P(d*) original → flipped, per ordering: 0.236 → 0.069, 0.554 → 0.205, 0.428 → 0.127
- Diagnostics: finite True, min label mass 0.984, greedy matches 3/3

## Citations

Descriptive summaries of 10 sampled citations and 3 greedy reference citations. Beat fractions use the exact same-size null (chance = 0.5) with differences under 0.01 in P(d*) counted as ties; empty and all-record citations are counted separately and excluded from beat fractions. No significance tests.

- Sampled: 10; parse statuses {'ok': 8, 'unparseable': 2}; analyzable 8
- Categories {'partial': 5, 'all': 3}; sizes {2: 2, 3: 3, 4: 3}
- Cited sets {'E2+E4': 1, 'E1+E2+E4': 3, 'E1+E2+E3+E4': 3, 'E1+E3': 1}; modal E1+E2+E4 (0.38)
- Partial citations: 5; mean beat (necessity) 0.78, mean beat (sufficiency) 0.80; share > 0.5: 0.80 / 0.80; mean Shapley top-k agreement 0.80

| Greedy citation | Status | Cited | Category | Beat (nec.) | Beat (suff.) |
|---|---|---|---|---|---|
| ordering 0 | ok | E1+E2+E3+E4 | all | n/a | n/a |
| ordering 1 | ok | E1+E2+E4 | partial | 1.00 | 1.00 |
| ordering 2 | ok | E1+E4 | partial | 1.00 | 0.80 |
