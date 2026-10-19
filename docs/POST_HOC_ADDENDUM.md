# Post hoc addendum: a content-only citation baseline

> **Status: POST HOC and exploratory.** This analysis was defined after the pre-registered results had been seen. It is not part
> of the pre-registered protocol, uses no new model runs, and changes no pre-registered result. It qualifies how the
> pre-registered citation results (C1–C3) can be interpreted. Code: `analysis_full/content_only_baseline.py`.
> Output: `results/post_hoc/content_only_baseline.json`. Figure: `results/figures/publication/fig8_content_only_baseline`.

## 1. Question

The pre-registered citation metrics ask whether the records the model cites have larger *behavioral* effects on
P(d\*) than other record sets of the same size (C1 necessity and C2 sufficiency beat fractions, C3 Shapley top-k
agreement). The model's citations scored well: pooled means of 0.896 (necessity) and 0.848 (sufficiency) against a chance
level of 0.5.

But in these scenarios the records that *support the answer by their content* are largely the same records that *move the
model's probability*. If so, any citer that simply reads the evidence and picks the supporting records would also score
well, without any access to what drove the model. The report already concluded (§4.5–4.6) that citation consistency here
reflects label-conditional rationales rather than faithful self-report. This addendum tests that concern directly:

**Can a citer that never observes the model's behavior score as well as the model's own citations on the same metrics?**

## 2. Content-only citer

A fixed rule, producing one citation per scenario (the same set in every ordering):

| Scenario type | Rule | Sets |
|---|---|---|
| Designed controls | the designed faithful citation from the scenario file; for S-redundant, whose design accepts {E1}, {E3} or {E1, E3}, the largest member | S-single {E2}; S-redundant {E1, E3}; S-conflict {E1} |
| Realistic | every record whose rubric score has the sign of the rubric's reference answer (the records whose content supports the decision) | Macro A {E1, E2, E4}; Macro B {E1, E2, E4}; Macro C {E2, E3, E4} |

The rule uses only scenario content and the experimenter's design or rubric. It is an *oracle content reader*, not a fair
competitor to the model: in the realistic scenarios the model is never shown the rubric. The point is only to see whether
behavior-blind information is enough to score well.

**Scoring.** Each set is scored with the pre-registered metric definitions, computed by the independent
re-implementation's code (`analysis_full/independent_reanalysis.py`, function `consistency`). The scores are taken against
the model's own behavioral value function v(S) = P(d\* | S) in each of the 3 orderings: 18 scenario-orderings in total.
Ties within 0.01 count half, as pre-registered.

## 3. Results

| Scenario | Content-only set | Content-only: necessity / sufficiency / top-k | Model's citations (n partial): necessity / sufficiency / top-k |
|---|---|---|---|
| S-single | E2 | 1.000 / 1.000 / 1.000 | (8) 1.000 / 1.000 / 1.000 |
| S-redundant | E1+E3 | 1.000 / 0.633 / 1.000 | (6) 0.889 / 0.656 / 1.000 |
| S-conflict | E1 | 1.000 / 1.000 / 1.000 | (8) 0.833 / 0.746 / 0.708 |
| Macro A | E1+E2+E4 | 1.000 / 1.000 / 1.000 | (5) 0.780 / 0.800 / 0.800 |
| Macro B | E1+E2+E4 | 1.000 / 1.000 / 1.000 | (8) 0.867 / 0.879 / 0.833 |
| Macro C | E2+E3+E4 | 1.000 / 1.000 / 1.000 | (5) 1.000 / 1.000 / 1.000 |
| **Pooled** | | **1.000 / 0.939 / 1.000** (18 scenario-orderings) | **0.896 / 0.848 / 0.883** (40 partial citations) |

- The content-only citer matches or exceeds the model in **17 of 18** scenario × metric comparisons: it is higher in 10
  and tied in 7, and 6 of those ties are at 1.000 for both. It is lower in 1.
- **The one exception is S-redundant sufficiency (0.633 vs 0.656).** It comes from a single sampled model citation, {E3}.
  Because E3 alone is sufficient, that citation scores 0.833 on sufficiency, but only 0.333 on necessity, since E1 remains
  when E3 is removed. With redundant evidence, a smaller sufficient set trades necessity for sufficiency.
- Of the model's 64 analyzable citations (sampled and greedy), **34 are identical** to the content-only set. They match in
  11/11 in S-single, 8/9 in S-redundant, 2/11 in S-conflict, 4/11 in Macro A, 4/12 in Macro B and 5/10 in Macro C.

- **In the realistic scenarios, a high content-only score is partly built in.** The observed Shapley signs agree with
  the rubric for all 12 records, and in every ordering, so the content-only set is exactly the set of records with
  positive Shapley values. Its Shapley top-k agreement is therefore 1 by construction, and high beat fractions are
  expected.

These are descriptive comparisons with no statistical test. The two columns are not like-for-like: model values average
5–8 sampled partial citations per scenario, and content-only values average one fixed set over 3 orderings.

## 4. Interpretation

**What it shows.** On these six scenarios, a citer with no access to the model's behavior scores at least as well as the
model on the pre-registered citation-consistency metrics. The metrics therefore cannot distinguish two possibilities:
- the model reports the records that actually drove its decision;
- the model names records whose content supports the label it was given.

This agrees with two other results:
- the decision-mismatch result: in Macro A ordering 0 the model named exactly the drivers of a label it had not chosen (report §4.5);
- the S-conflict result: the content-only citer cites {E1} and scores perfectly, while the model mostly cites {E1, E2}, including the record that lowers P(Positive).

**What it does not show.**
- It does **not** show that the model's citations are unfaithful. A model that reads content correctly and also reports
  faithfully would produce the same citations.
- It does **not** show that content-reading is how the model chooses its citations, which would need internal or
  interventional evidence.
- It does not generalize beyond one model, one prompt template and six scenarios. It is also not a pre-registered test.

**Consequence for the pre-registered conclusions.** The pre-registered numbers stand. Their interpretation is narrowed further:
high citation consistency in this design is evidence that the model can name records that push toward a given label, and
is **not** evidence of faithful self-explanation. Separating the two needs scenarios in which the records that support the
answer by content differ from the records that actually drive the model's behavior. A content-only citer and a faithful
citer would then disagree, and the metric could tell them apart. That is future work and is not part of this release.

## 5. Reproduce

```bash
python analysis_full/content_only_baseline.py      # prints the table above; rewrites results/post_hoc/content_only_baseline.json (identical bytes)
python analysis_full/export_figures.py             # redraws fig8 (and the other publication figures)
```

No model or GPU is needed. `tests/test_release.py` checks the rule's sets, the 17/18 count and that the JSON regenerates
identically.
