# Feasibility test: s_single

- Run ID: `s_single_20261017T180509Z`
- Model: `microsoft/Phi-3-mini-4k-instruct` (commit `None`, float16, Tesla T4)
- Design fingerprint: `151b929fe0a7350a...`
- Scored cells: 48 (forward passes: 192)

**Infrastructure checks: FAIL**  
**Behavioral recovery (validation check, not a hypothesis test): PASS**

## Infrastructure checks

| ID | Check | Result | Detail |
|---|---|---|---|
| I1 | chat-template round trip | pass | 48/48 cells match |
| I2 | label token boundaries, prefix-free labels, identical label ids across cells | pass | 0 tokenization errors; 1 distinct label-id sets |
| I3 | finite log-probs; consistent multi-token recomputation | **FAIL** | 0 non-finite cells; max first-token recompute diff 6.17e-02 |
| I4 | label mass >= 0.95 in every cell | pass | min 0.9703, median 0.9803 |
| I5 | greedy decoding reproduces the scored argmax (cells with margin >= 0.1) | pass | 48/48 eligible cells match; 48/48 of all cells |
| I6 | re-scoring repeatability (max \|delta log p\| <= 0.001) | pass | 3 cells re-scored; max diff 0.00e+00 |
| I7 | completeness: 16 subsets x 3 orderings | pass | 48 cells, 48 unique |

## Behavioral recovery checks

| ID | Check | Result | Detail |
|---|---|---|---|
| B1 | full evidence: argmax equals the designed answer in every ordering | pass | Positive, Positive, Positive |
| B2 | decisive record alone: argmax equals the designed answer (sufficiency) | pass | Positive, Positive, Positive |
| B3 | decisive record removed: argmax changes (necessity) | pass | Neutral, Neutral, Neutral |
| B4 | argmax equals the designed answer in >= 15/16 subsets per ordering | pass | 16, 16, 16 |
| B5 | Shapley recovers the design (decisive largest, share >= 0.8, \|distractor\| <= 0.05) | pass | ordering=0, decisive_is_max=True, decisive_share=0.9998, max_abs_distractor_phi=0.0003, total_effect=0.9991; ordering=1, decisive_is_max=True, decisive_share=0.9997, max_abs_distractor_phi=0.0001, total_effect=0.9994; ordering=2, decisive_is_max=True, decisive_share=0.9997, max_abs_distractor_phi=0.0002, total_effect=0.9995 |

## Decision and baseline

- d* (argmax of ordering-averaged full-evidence distribution): **Positive**; designed answer: Positive
- Full-set argmax per ordering: ['Positive', 'Positive', 'Positive']
- v(full) = P(d* | all records): 0.999 [0.999, 1.000]
- v(empty) = P(d* | no records): 0.000 [0.000, 0.000]

Values are mean [min, max] across the 3 fixed orderings: a description of ordering sensitivity, not a confidence interval.

## Behavioral attribution

Shapley values and leave-one-out effects on P(d*), in probability units. These attribute the model's output to the supplied records; they are not evidence about internal reasoning.

| Record | Shapley mean [min, max] | Leave-one-out mean [min, max] |
|---|---|---|
| E1 | -0.000 [-0.000, 0.000] | -0.000 [-0.000, 0.000] |
| E2 | 0.999 [0.999, 0.999] | 0.999 [0.999, 0.999] |
| E3 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| E4 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.001] |

Shapley sums per ordering (should equal v(full) - v(empty)): 0.9991, 0.9994, 0.9995

## Subset lattice

| Subset | Designed | P(d*) per ordering | Argmax per ordering |
|---|---|---|---|
| none | Neutral | 0.000, 0.000, 0.000 | Neutral, Neutral, Neutral |
| E1 | Neutral | 0.000, 0.000, 0.000 | Neutral, Neutral, Neutral |
| E2 | Positive | 0.999, 0.999, 0.999 | Positive, Positive, Positive |
| E3 | Neutral | 0.000, 0.000, 0.000 | Neutral, Neutral, Neutral |
| E4 | Neutral | 0.000, 0.000, 0.000 | Neutral, Neutral, Neutral |
| E1+E2 | Positive | 0.998, 0.999, 0.999 | Positive, Positive, Positive |
| E1+E3 | Neutral | 0.000, 0.000, 0.000 | Neutral, Neutral, Neutral |
| E1+E4 | Neutral | 0.000, 0.000, 0.000 | Neutral, Neutral, Neutral |
| E2+E3 | Positive | 0.999, 0.999, 0.999 | Positive, Positive, Positive |
| E2+E4 | Positive | 0.999, 0.999, 0.999 | Positive, Positive, Positive |
| E3+E4 | Neutral | 0.000, 0.000, 0.000 | Neutral, Neutral, Neutral |
| E1+E2+E3 | Positive | 0.999, 0.999, 0.999 | Positive, Positive, Positive |
| E1+E2+E4 | Positive | 0.999, 0.999, 0.999 | Positive, Positive, Positive |
| E1+E3+E4 | Neutral | 0.000, 0.000, 0.000 | Neutral, Neutral, Neutral |
| E2+E3+E4 | Positive | 1.000, 0.999, 0.999 | Positive, Positive, Positive |
| E1+E2+E3+E4 | Positive | 0.999, 0.999, 1.000 | Positive, Positive, Positive |

## Reference: how candidate citation sets would score

Not model citations (citation sampling is not part of this test). This shows the metric on this lattice. Empty and all-four sets are separate categories with no beat fractions.

| Cited | Category | Necessity | Sufficiency | Beat (necessity) | Beat (sufficiency) |
|---|---|---|---|---|---|
| none | empty | 0.000 [0.000, 0.000] | -0.999 [-0.999, -0.999] | n/a | n/a |
| E1 | partial | -0.000 [-0.000, 0.000] | -0.999 [-0.999, -0.999] | 0.11 [0.00, 0.33] | 0.33 [0.33, 0.33] |
| E2 | partial | 0.999 [0.999, 0.999] | 0.000 [-0.000, 0.000] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] |
| E3 | partial | 0.000 [0.000, 0.000] | -0.999 [-0.999, -0.999] | 0.22 [0.00, 0.33] | 0.67 [0.67, 0.67] |
| E4 | partial | 0.000 [0.000, 0.001] | -0.999 [-0.999, -0.999] | 0.67 [0.67, 0.67] | 0.00 [0.00, 0.00] |
| E1+E2+E3+E4 | all | 0.999 [0.999, 0.999] | 0.000 [0.000, 0.000] | n/a | n/a |

All 16 rows are in `analysis.json`.
