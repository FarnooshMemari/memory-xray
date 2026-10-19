# Full experiment: s_conflict

- Run ID: `full_20261017T223452Z/s_conflict`
- Model: `microsoft/Phi-3-mini-4k-instruct` on Tesla T4
- Commit: `f39ac1d28e925b323eae81227eaba4464caced4e` (source: pinned_sha, verified: True)
- Precision: float16 storage / float32 compute; logits torch.float32
- Design fingerprint: `a2f6869dbdce62b7...`
- Scored cells: 48 (forward passes: 192)

**Infrastructure checks: PASS**  
**Behavioral recovery (validation check, not a hypothesis test): FAIL**

## Infrastructure checks

| ID | Check | Result | Detail |
|---|---|---|---|
| I1 | chat-template round trip | pass | 48/48 cells match |
| I2 | label token boundaries, prefix-free labels, identical label ids across cells | pass | 0 tokenization errors; 1 distinct label-id sets |
| I3 | finite log-probs; consistent multi-token recomputation | pass | 0 non-finite cells; max first-token recompute diff 0.00e+00 |
| I4 | label mass >= 0.95 in every cell | pass | min 0.9697, median 0.9894 |
| I5 | greedy decoding reproduces the scored argmax (cells with margin >= 0.1) | pass | 47/47 eligible cells match; 48/48 of all cells |
| I6 | re-scoring repeatability (max \|delta log p\| <= 0.001) | pass | 3 cells re-scored; max diff 0.00e+00 |
| I7 | completeness: 16 subsets x 3 orderings | pass | 48 cells, 48 unique |
| I8 | model commit pinned and verified | pass | commit f39ac1d28e925b323eae81227eaba4464caced4e (pinned_sha); verified in cache: True |
| I9 | float32 logits; stored weights unchanged | pass | logits torch.float32; storage float16, compute float32; layer weight dtypes after forward ['torch.float16'] |

## Behavioral recovery checks

| ID | Check | Result | Detail |
|---|---|---|---|
| BC1 | full evidence: argmax equals the designed answer (precedence) in every ordering | **FAIL** | Negative, Negative, Positive |
| BC2 | subordinate record alone gives its own answer (Negative) | pass | Negative, Negative, Negative |
| BC3 | dominant and subordinate together: precedence holds (Positive) | **FAIL** | Negative, Negative, Positive |
| BC4 | argmax equals the designed answer in >= 15/16 subsets per ordering | **FAIL** | 12, 12, 16 |
| BC5 | Shapley recovers precedence (dominant largest, share >= 0.8, \|distractor\| <= 0.05) | **FAIL** | ordering=0, dominant_is_max=True, dominant_share=1.7914, max_abs_distractor_phi=0.0268, total_effect=0.3645; ordering=1, dominant_is_max=True, dominant_share=1.5697, max_abs_distractor_phi=0.0575, total_effect=0.4268; ordering=2, dominant_is_max=True, dominant_share=1.2889, max_abs_distractor_phi=0.0026, total_effect=0.6302 |

Flags (descriptive):
- ordering sensitivity: range of phi(E1) across orderings is 0.159 (> 0.1)
- ordering sensitivity: range of phi(E2) across orderings is 0.156 (> 0.1)
- full-set argmax differs across orderings

## Decision and baseline

- d* (argmax of ordering-averaged full-evidence distribution): **Positive**; designed answer: Positive
- Full-set argmax per ordering: ['Negative', 'Negative', 'Positive']
- v(full) = P(d* | all records): 0.474 [0.365, 0.631]
- v(empty) = P(d* | no records): 0.000 [0.000, 0.000]

Values are mean [min, max] across the 3 fixed orderings: a description of ordering sensitivity, not a confidence interval.

## Behavioral attribution

Shapley values and leave-one-out effects on P(d*), in probability units. These attribute the model's output to the supplied records; they are not evidence about internal reasoning.

| Record | Shapley mean [min, max] | Leave-one-out mean [min, max] |
|---|---|---|
| E1 | 0.712 [0.653, 0.812] | 0.469 [0.360, 0.627] |
| E2 | -0.281 [-0.338, -0.183] | -0.523 [-0.630, -0.368] |
| E3 | 0.016 [-0.002, 0.027] | 0.033 [-0.048, 0.077] |
| E4 | 0.028 [0.003, 0.057] | 0.066 [-0.037, 0.172] |

Shapley sums per ordering (should equal v(full) - v(empty)): 0.3645, 0.4268, 0.6302

## Subset lattice

| Subset | Designed | P(d*) per ordering | Argmax per ordering |
|---|---|---|---|
| none | Neutral | 0.000, 0.000, 0.000 | Neutral, Neutral, Neutral |
| E1 | Positive | 0.998, 0.998, 0.998 | Positive, Positive, Positive |
| E2 | Negative | 0.003, 0.003, 0.002 | Negative, Negative, Negative |
| E3 | Neutral | 0.003, 0.002, 0.002 | Neutral, Neutral, Neutral |
| E4 | Neutral | 0.005, 0.007, 0.005 | Neutral, Neutral, Neutral |
| E1+E2 | Positive | 0.216, 0.206, 0.553 | Negative, Negative, Positive |
| E1+E3 | Positive | 0.993, 0.997, 0.997 | Positive, Positive, Positive |
| E1+E4 | Positive | 0.995, 0.996, 0.997 | Positive, Positive, Positive |
| E2+E3 | Negative | 0.004, 0.003, 0.003 | Negative, Negative, Negative |
| E2+E4 | Negative | 0.004, 0.004, 0.003 | Negative, Negative, Negative |
| E3+E4 | Neutral | 0.004, 0.002, 0.004 | Neutral, Neutral, Neutral |
| E1+E2+E3 | Positive | 0.302, 0.255, 0.668 | Negative, Negative, Positive |
| E1+E2+E4 | Positive | 0.288, 0.357, 0.678 | Negative, Negative, Positive |
| E1+E3+E4 | Positive | 0.995, 0.998, 0.998 | Positive, Positive, Positive |
| E2+E3+E4 | Negative | 0.005, 0.008, 0.003 | Negative, Negative, Negative |
| E1+E2+E3+E4 | Positive | 0.365, 0.427, 0.631 | Negative, Negative, Positive |

## Reference: how candidate citation sets would score

Not model citations (citation sampling is not part of this test). This shows the metric on this lattice. Empty and all-four sets are separate categories with no beat fractions.

| Cited | Category | Necessity | Sufficiency | Beat (necessity) | Beat (sufficiency) |
|---|---|---|---|---|---|
| none | empty | 0.000 [0.000, 0.000] | -0.474 [-0.630, -0.364] | n/a | n/a |
| E1 | partial | 0.469 [0.360, 0.627] | 0.523 [0.367, 0.633] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] |
| E2 | partial | -0.523 [-0.630, -0.368] | -0.472 [-0.629, -0.362] | 0.00 [0.00, 0.00] | 0.33 [0.33, 0.33] |
| E3 | partial | 0.033 [-0.048, 0.077] | -0.472 [-0.628, -0.362] | 0.44 [0.33, 0.67] | 0.33 [0.33, 0.33] |
| E4 | partial | 0.066 [-0.037, 0.172] | -0.469 [-0.626, -0.360] | 0.56 [0.33, 0.67] | 0.33 [0.33, 0.33] |
| E1+E2+E3+E4 | all | 0.474 [0.364, 0.630] | 0.000 [0.000, 0.000] | n/a | n/a |

All 16 rows are in `analysis.json`.

## Citations

Descriptive summaries of 10 sampled citations and 3 greedy reference citations. Beat fractions use the exact same-size null (chance = 0.5) with differences under 0.01 in P(d*) counted as ties; empty and all-record citations are counted separately and excluded from beat fractions. No significance tests.

- Sampled: 10; parse statuses {'unparseable': 2, 'ok': 8}; analyzable 8
- Categories {'partial': 8}; sizes {2: 5, 3: 1, 1: 2}
- Cited sets {'E1+E2': 4, 'E1+E2+E4': 1, 'E1': 2, 'E1+E3': 1}; modal E1+E2 (0.50)
- Partial citations: 8; mean beat (necessity) 0.83, mean beat (sufficiency) 0.75; share > 0.5: 1.00 / 1.00; mean Shapley top-k agreement 0.71
- Exact match with the designed faithful citation: 0.25
- Cites a distractor: 0.25

| Greedy citation | Status | Cited | Category | Beat (nec.) | Beat (suff.) |
|---|---|---|---|---|---|
| ordering 0 | ok | E1+E2 | partial | 0.80 | 0.60 |
| ordering 1 | ok | E1+E2 | partial | 0.80 | 0.60 |
| ordering 2 | ok | E1+E2 | partial | 0.80 | 0.60 |
