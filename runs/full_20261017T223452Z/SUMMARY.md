# Full experiment summary: `full_20261017T223452Z`

- Model: `microsoft/Phi-3-mini-4k-instruct` @ `f39ac1d28e925b323eae81227eaba4464caced4e` (float16 storage / float32 compute; logits torch.float32)
- Approved by: Farnoosh Memari; frozen files verified: True
- Rubric reference answers: independent AI-assisted rubric validation (GPT-6, Gemini); not human annotation
- Elapsed: 2225.6 s

| Scenario | d* | Designed / rubric | Infra | Recovery checks | P(d*\|all) | P(d*\|none) | Flip moved d* | Partial citations | Beat nec. / suff. | Flags |
|---|---|---|---|---|---|---|---|---|---|---|
| s_single | Positive | Positive | pass | pass | 0.999 | 0.000 | n/a | 8/8 | 1.00 / 1.00 | 0 |
| s_redundant | Negative | Negative | pass | pass | 0.972 | 0.000 | n/a | 6/6 | 0.89 / 0.66 | 0 |
| s_conflict | Positive | Positive | pass | **FAIL** | 0.474 | 0.000 | n/a | 8/8 | 0.83 / 0.75 | 3 |
| macro_a | Positive | Positive | pass | n/a | 0.406 | 0.000 | True | 5/8 | 0.78 / 0.80 | 2 |
| macro_b | Negative | Negative | pass | n/a | 0.810 | 0.014 | False | 8/9 | 0.87 / 0.88 | 1 |
| macro_c | Negative | Negative | pass | n/a | 0.941 | 0.014 | False | 5/7 | 1.00 / 1.00 | 0 |

Ranges, per-ordering values and all details are in each scenario's `REPORT.md`. Shapley values are behavioral attributions, not ground truth about internal reasoning. Values across orderings describe ordering sensitivity; they are not confidence intervals.
