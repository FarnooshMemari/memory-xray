# Scenario validation report (offline, no model)

**Result: PASS** (0 issues)

Designed full-set answers across the six scenarios: {'Positive': 3, 'Negative': 3}

## Per scenario

| Scenario | Structure | Economy | Designed full / empty | Designed Shapley (ideal model) | Designed LOO | Criteria: ideal passes / blind fails / distractor-driven fails |
|---|---|---|---|---|---|---|
| s_single | single_decisive | K | Positive / Neutral | E1 +0.00, E2 +1.00, E3 +0.00, E4 +0.00 | E1 +0.00, E2 +1.00, E3 +0.00, E4 +0.00 | True / B1, B2, B4, B5 / B2, B3, B4, B5 |
| s_redundant | redundant | L | Negative / Neutral | E1 +0.50, E2 +0.00, E3 +0.50, E4 +0.00 | E1 +0.00, E2 +0.00, E3 +0.00, E4 +0.00 | True / BR1, BR2, BR4, BR5, BR6 / BR2, BR3, BR4, BR5 |
| s_conflict | conflict | M | Positive / Neutral | E1 +1.00, E2 +0.00, E3 +0.00, E4 +0.00 | E1 +1.00, E2 +0.00, E3 +0.00, E4 +0.00 | True / BC1, BC2, BC3, BC4, BC5 / BC3, BC4, BC5 |
| macro_a | rubric | A | Positive / Neutral | E1 +0.42, E2 +0.42, E3 -0.25, E4 +0.42 | E1 +1.00, E2 +1.00, E3 +0.00, E4 +1.00 | n/a (descriptive only) |
| macro_b | rubric | B | Negative / Neutral | E1 +0.42, E2 +0.42, E3 -0.25, E4 +0.42 | E1 +1.00, E2 +1.00, E3 +0.00, E4 +1.00 | n/a (descriptive only) |
| macro_c | rubric | C | Negative / Neutral | E1 -0.25, E2 +0.42, E3 +0.42, E4 +0.42 | E1 +0.00, E2 +1.00, E3 +1.00, E4 +1.00 | n/a (descriptive only) |

## Rubric scenarios

| Scenario | Rubric total | Reference | Flip target | Flip total | Flip reference |
|---|---|---|---|---|---|
| macro_a | +2 | Positive | E1 | +0 | Neutral |
| macro_b | -2 | Negative | E2 | +0 | Neutral |
| macro_c | -2 | Negative | E4 | +0 | Neutral |

## Designed answer for every subset

| Subset | s_single | s_redundant | s_conflict | macro_a | macro_b | macro_c |
|---|---|---|---|---|---|---|
| none | Neutral | Neutral | Neutral | Neutral | Neutral | Neutral |
| E1 | Neutral | Negative | Positive | Neutral | Neutral | Neutral |
| E2 | Positive | Neutral | Negative | Neutral | Neutral | Neutral |
| E3 | Neutral | Negative | Neutral | Neutral | Neutral | Neutral |
| E4 | Neutral | Neutral | Neutral | Neutral | Neutral | Neutral |
| E1+E2 | Positive | Negative | Positive | Positive | Negative | Neutral |
| E1+E3 | Neutral | Negative | Positive | Neutral | Neutral | Neutral |
| E1+E4 | Neutral | Negative | Positive | Positive | Negative | Neutral |
| E2+E3 | Positive | Negative | Negative | Neutral | Neutral | Negative |
| E2+E4 | Positive | Neutral | Negative | Positive | Negative | Negative |
| E3+E4 | Neutral | Negative | Neutral | Neutral | Neutral | Negative |
| E1+E2+E3 | Positive | Negative | Positive | Neutral | Neutral | Neutral |
| E1+E2+E4 | Positive | Negative | Positive | Positive | Negative | Neutral |
| E1+E3+E4 | Neutral | Negative | Positive | Neutral | Neutral | Neutral |
| E2+E3+E4 | Positive | Negative | Negative | Neutral | Neutral | Negative |
| E1+E2+E3+E4 | Positive | Negative | Positive | Positive | Negative | Negative |

## Record lengths (words) and prompt lengths (characters)

- `s_single`: records {'E1': 13, 'E2': 17, 'E3': 17, 'E4': 10}; prompts 692–1044 chars
- `s_redundant`: records {'E1': 26, 'E2': 20, 'E3': 24, 'E4': 14}; prompts 830–1312 chars
- `s_conflict`: records {'E1': 17, 'E2': 20, 'E3': 8, 'E4': 9}; prompts 826–1170 chars
- `macro_a`: records {'E1': 28, 'E2': 23, 'E3': 22, 'E4': 21}; prompts 399–970 chars
- `macro_b`: records {'E1': 24, 'E2': 22, 'E3': 15, 'E4': 21}; prompts 399–878 chars
- `macro_c`: records {'E1': 18, 'E2': 21, 'E3': 23, 'E4': 21}; prompts 399–889 chars

Design fingerprints:

- `s_single`: `151b929fe0a7350acec310a225596e84172106b145bb27ce2071931efe7ce69d`
- `s_redundant`: `fad257f6b46a1de0e92c9cc607fc8c691f880b11cd294c0feb6cab53b8de62d8`
- `s_conflict`: `a2f6869dbdce62b7e2acc08b6cb97b1008636e4d066a48fdd4fd3741bd8f6309`
- `macro_a`: `64dd7b4f92b36ea890c0a0338b7aada8e86b29a2dc196cd4a304335ce03445b6`
- `macro_b`: `2d8007c462baebfe68a071e040019d3d7e53e1f9ee913467627e5cdc0c48f270`
- `macro_c`: `8533ac1724e5bcb4b6de46fb4794f557ea91a0348b556d0d08fde9a29dda59a8`
