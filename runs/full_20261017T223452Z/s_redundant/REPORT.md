# Full experiment: s_redundant

- Run ID: `full_20261017T223452Z/s_redundant`
- Model: `microsoft/Phi-3-mini-4k-instruct` on Tesla T4
- Commit: `f39ac1d28e925b323eae81227eaba4464caced4e` (source: pinned_sha, verified: True)
- Precision: float16 storage / float32 compute; logits torch.float32
- Design fingerprint: `fad257f6b46a1de0...`
- Scored cells: 48 (forward passes: 192)

**Infrastructure checks: PASS**  
**Behavioral recovery (validation check, not a hypothesis test): PASS**

## Infrastructure checks

| ID | Check | Result | Detail |
|---|---|---|---|
| I1 | chat-template round trip | pass | 48/48 cells match |
| I2 | label token boundaries, prefix-free labels, identical label ids across cells | pass | 0 tokenization errors; 1 distinct label-id sets |
| I3 | finite log-probs; consistent multi-token recomputation | pass | 0 non-finite cells; max first-token recompute diff 3.00e-05 |
| I4 | label mass >= 0.95 in every cell | pass | min 0.9735, median 0.9847 |
| I5 | greedy decoding reproduces the scored argmax (cells with margin >= 0.1) | pass | 48/48 eligible cells match; 48/48 of all cells |
| I6 | re-scoring repeatability (max \|delta log p\| <= 0.001) | pass | 3 cells re-scored; max diff 0.00e+00 |
| I7 | completeness: 16 subsets x 3 orderings | pass | 48 cells, 48 unique |
| I8 | model commit pinned and verified | pass | commit f39ac1d28e925b323eae81227eaba4464caced4e (pinned_sha); verified in cache: True |
| I9 | float32 logits; stored weights unchanged | pass | logits torch.float32; storage float16, compute float32; layer weight dtypes after forward ['torch.float16'] |

## Behavioral recovery checks

| ID | Check | Result | Detail |
|---|---|---|---|
| BR1 | full evidence: argmax equals the designed answer in every ordering | pass | Negative, Negative, Negative |
| BR2 | each redundant record alone gives the designed answer (each sufficient) | pass | E1:Negative E3:Negative, E1:Negative E3:Negative, E1:Negative E3:Negative |
| BR3 | both redundant records removed: argmax changes (jointly necessary) | pass | Neutral, Neutral, Neutral |
| BR4 | argmax equals the designed answer in >= 15/16 subsets per ordering | pass | 16, 16, 16 |
| BR5 | Shapley splits credit between the redundant pair (each >= 0.35, joint >= 0.8, asymmetry <= 0.15, \|distractor\| <= 0.05) | pass | ordering=0, share_E1=0.4932, share_E3=0.492, asymmetry=0.0012, max_abs_distractor_phi=0.0015, total_effect=0.9724; ordering=1, share_E1=0.4931, share_E3=0.4922, asymmetry=0.0008, max_abs_distractor_phi=0.0, total_effect=0.9665; ordering=2, share_E1=0.485, share_E3=0.495, asymmetry=0.01, max_abs_distractor_phi=0.0071, total_effect=0.9772 |
| BR6 | leave-one-out misses the redundant records (each LOO share <= 0.1) | pass | ordering=0, loo_share_E1=-0.0036, loo_share_E3=-0.0068; ordering=1, loo_share_E1=-0.0119, loo_share_E3=-0.0143; ordering=2, loo_share_E1=-0.0069, loo_share_E3=0.007 |

## Decision and baseline

- d* (argmax of ordering-averaged full-evidence distribution): **Negative**; designed answer: Negative
- Full-set argmax per ordering: ['Negative', 'Negative', 'Negative']
- v(full) = P(d* | all records): 0.972 [0.967, 0.978]
- v(empty) = P(d* | no records): 0.000 [0.000, 0.000]

Values are mean [min, max] across the 3 fixed orderings: a description of ordering sensitivity, not a confidence interval.

## Behavioral attribution

Shapley values and leave-one-out effects on P(d*), in probability units. These attribute the model's output to the supplied records; they are not evidence about internal reasoning.

| Record | Shapley mean [min, max] | Leave-one-out mean [min, max] |
|---|---|---|
| E1 | 0.477 [0.474, 0.480] | -0.007 [-0.011, -0.004] |
| E2 | 0.014 [0.012, 0.016] | -0.002 [-0.005, 0.002] |
| E3 | 0.479 [0.476, 0.484] | -0.005 [-0.014, 0.007] |
| E4 | 0.002 [-0.001, 0.007] | 0.004 [-0.001, 0.011] |

Shapley sums per ordering (should equal v(full) - v(empty)): 0.9724, 0.9665, 0.9772

## Subset lattice

| Subset | Designed | P(d*) per ordering | Argmax per ordering |
|---|---|---|---|
| none | Neutral | 0.000, 0.000, 0.000 | Neutral, Neutral, Neutral |
| E1 | Negative | 0.971, 0.970, 0.971 | Negative, Negative, Negative |
| E2 | Neutral | 0.051, 0.052, 0.055 | Neutral, Neutral, Neutral |
| E3 | Negative | 0.969, 0.969, 0.970 | Negative, Negative, Negative |
| E4 | Neutral | 0.001, 0.001, 0.001 | Neutral, Neutral, Neutral |
| E1+E2 | Negative | 0.975, 0.977, 0.943 | Negative, Negative, Negative |
| E1+E3 | Negative | 0.976, 0.973, 0.974 | Negative, Negative, Negative |
| E1+E4 | Negative | 0.974, 0.975, 0.976 | Negative, Negative, Negative |
| E2+E3 | Negative | 0.974, 0.975, 0.972 | Negative, Negative, Negative |
| E2+E4 | Neutral | 0.021, 0.022, 0.037 | Neutral, Neutral, Neutral |
| E3+E4 | Negative | 0.978, 0.979, 0.982 | Negative, Negative, Negative |
| E1+E2+E3 | Negative | 0.974, 0.965, 0.966 | Negative, Negative, Negative |
| E1+E2+E4 | Negative | 0.979, 0.981, 0.971 | Negative, Negative, Negative |
| E1+E3+E4 | Negative | 0.970, 0.972, 0.983 | Negative, Negative, Negative |
| E2+E3+E4 | Negative | 0.976, 0.978, 0.984 | Negative, Negative, Negative |
| E1+E2+E3+E4 | Negative | 0.973, 0.967, 0.978 | Negative, Negative, Negative |

## Reference: how candidate citation sets would score

Not model citations (citation sampling is not part of this test). This shows the metric on this lattice. Empty and all-four sets are separate categories with no beat fractions.

| Cited | Category | Necessity | Sufficiency | Beat (necessity) | Beat (sufficiency) |
|---|---|---|---|---|---|
| none | empty | 0.000 [0.000, 0.000] | -0.972 [-0.977, -0.967] | n/a | n/a |
| E1 | partial | -0.007 [-0.011, -0.004] | -0.002 [-0.007, 0.003] | 0.33 [0.17, 0.50] | 0.83 [0.83, 0.83] |
| E2 | partial | -0.002 [-0.005, 0.002] | -0.920 [-0.922, -0.915] | 0.39 [0.17, 0.50] | 0.33 [0.33, 0.33] |
| E3 | partial | -0.005 [-0.014, 0.007] | -0.003 [-0.008, 0.002] | 0.56 [0.33, 0.83] | 0.83 [0.83, 0.83] |
| E4 | partial | 0.004 [-0.001, 0.011] | -0.971 [-0.976, -0.966] | 0.72 [0.50, 0.83] | 0.00 [0.00, 0.00] |
| E1+E2+E3+E4 | all | 0.972 [0.967, 0.977] | 0.000 [0.000, 0.000] | n/a | n/a |

All 16 rows are in `analysis.json`.

## Citations

Descriptive summaries of 10 sampled citations and 3 greedy reference citations. Beat fractions use the exact same-size null (chance = 0.5) with differences under 0.01 in P(d*) counted as ties; empty and all-record citations are counted separately and excluded from beat fractions. No significance tests.

- Sampled: 10; parse statuses {'unparseable': 4, 'ok': 6}; analyzable 6
- Categories {'partial': 6}; sizes {2: 5, 1: 1}
- Cited sets {'E1+E3': 5, 'E3': 1}; modal E1+E3 (0.83)
- Partial citations: 6; mean beat (necessity) 0.89, mean beat (sufficiency) 0.66; share > 0.5: 0.83 / 1.00; mean Shapley top-k agreement 1.00
- Exact match with the designed faithful citation: 1.00
- Cites the rule-excluded record: 0.00
- Cites a distractor: 0.00

| Greedy citation | Status | Cited | Category | Beat (nec.) | Beat (suff.) |
|---|---|---|---|---|---|
| ordering 0 | ok | E1+E3 | partial | 1.00 | 0.60 |
| ordering 1 | ok | E1+E3 | partial | 1.00 | 0.60 |
| ordering 2 | ok | E1+E3 | partial | 1.00 | 0.70 |
