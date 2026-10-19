# Research summary: Memory X-Ray

**Farnoosh Memari · Duke University · Independent research project in explainable and responsible AI · 2026**

## Question

When a language model answers from supplied evidence and then says which evidence it relied on, do the records it names
match the records that actually drive its answer?

## Why it matters

Retrieval-augmented and memory-based assistants routinely cite their sources, and users read those citations as
explanations. A citation can be **plausible** (the cited record supports the answer) without being **faithful** (the cited
record is what moved the model). Checking this requires a behavioral ground truth for "what moved the model", measured
independently of what the model says.

## Approach

- **Model:** Phi-3-mini-4k-instruct, pinned to one commit; deterministic label-probability scoring on a Colab T4.
- **Scenarios (n = 6):**
  - 3 designed controls with a known structure: one decisive record, two redundant records, and two conflicting records
    with an instructed precedence rule;
  - 3 realistic, de-identified macro-finance cases, with reference answers from a written rubric the model never sees.
- **Behavioral attribution:** every subset of the 4 records (16) in 3 fixed orderings, giving 48 prompts per scenario.
  From these come exact Shapley values, leave-one-out effects, and the necessity and sufficiency of any record set, all
  computed on P(decision).
- **Self-reports:** the model is asked which records its answer relied on (10 sampled and 3 greedy replies per scenario).
  Each cited set is compared with every other set of the same size. A beat fraction above 0.5 means the citation is more
  influential than chance.
- **Rigor:**
  - protocol, scenarios, thresholds and parser frozen before the run;
  - infrastructure checks I1–I9;
  - an independent re-implementation;
  - every run, including a failed feasibility run, preserved with checksums.

## Findings

| # | Finding | Evidence | Status |
|---|---|---|---|
| 1 | The measurement is sound | I1–I9 pass in 6/6 scenarios; independent re-implementation exact (max Shapley difference 2.2 × 10⁻¹⁶); single-cause and redundancy controls recovered | pre-registered |
| 2 | Leave-one-out misses redundancy; Shapley does not | S-redundant: Shapley ≈ 0.48 per report, leave-one-out ≈ 0. Macro C: Shapley 0.28–0.35, leave-one-out 0.04–0.07 | pre-registered |
| 3 | The model does not follow an instructed precedence rule; in this test the later record won | S-conflict fails BC1, BC3, BC4, BC5; the later of the two conflicting records decides in 12/12 prompts, the rule holds in 4/12 (one ordering contrast, confounded) | pre-registered checks; descriptive count |
| 4 | Realistic weights differ from the rubric | Signs match the rubric 12/12. Macro A contrary record −0.48 vs −0.25; Macro C rate cut −0.02 vs −0.25. Macro A decision margin 0.020 | rubric values fixed before the run; comparison descriptive |
| 5 | Probabilities move more than labels | Flipping one record lowers P(decision) in 9/9 cases, but changes the label in only 5/9 | post hoc (descriptive) |
| 6 | Citations name influential records | Necessity beat 0.896 (37/40 above chance), sufficiency 0.848 (38/40). Planted cause cited 8/8 and 6/6, but 2/8 in S-conflict | pre-registered |
| 7 | Citations still back a label the model did not choose | In 3/18 orderings the shown label was not the model's own answer for that ordering. Those 8 partial citations all beat chance for the shown label, though lower on average (0.85 / 0.73 vs 0.91 / 0.88 for aligned orderings) | pre-registered metric; post hoc split |
| 8 | A citer that never sees the model does as well | A content-only citer built from the experimenter's design and rubric scores 1.000 / 0.939 / 1.000 vs the model's 0.896 / 0.848 / 0.883 (necessity / sufficiency / top-k): higher in 10 of 18 comparisons, tied in 7, lower in 1 | **post hoc** |

## Interpretation

- **Exact subset-based attribution is a usable measurement.** It is deterministic, reproducible, and catches redundancy
  that leave-one-out misses.
- **The model's citations agree with that measurement on average**, which a casual evaluation would read as faithful
  self-explanation.
- **Two results block that reading:**
  - citations for a label the model did not choose in that ordering still beat chance;
  - a citer with no access to the model's behavior scores as well.
- **What the citation metrics measure here** is the ability to name records that push toward a given label
  (**label-conditional rationales**), not faithful introspection.

## What this does not show

- It does not show that the model's citations are unfaithful.
- It does not show anything about the model's internal mechanisms.
- It does not show that the pattern holds for other models, prompts or domains.
- With six scenarios and three fixed orderings, the results are case studies, and the ordering ranges are not
  confidence intervals.

## Practical lessons for evidence-grounded systems

1. Use subset-based (Shapley) attribution, not leave-one-out, when sources may be redundant.
2. Control or average evidence order, because order can decide conflicts.
3. Report probability shifts, not only label flips.
4. Do not accept a model's own citations as faithful without a behavioral check. Make sure the check can tell a faithful
   citer from one that merely reads the content.

## Future work

- Scenarios in which the records that support the answer by content differ from the records that actually drive the
  model, so that the citation metrics can separate faithful from plausible citers.
- Orderings that vary the order of conflicting records while holding position fixed.
- Per-ordering decisions in the citation prompt.
- More models.

---
Full report: `results/RESULTS_AND_DISCUSSION.md` · Post hoc baseline: `docs/POST_HOC_ADDENDUM.md` · All numbers:
`poster_materials/KEY_NUMBERS.md` · Protocol: `docs/PROTOCOL_v0.2.md`
