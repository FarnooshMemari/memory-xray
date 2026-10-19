# Figures and captions

All figures are generated from the saved result files. Nothing in them is drawn by hand.

| Folder | Contents |
|---|---|
| `poster_materials/figures/` | Poster figures, drawn at print size with large type (`analysis_full/poster_figures.py`) |
| `results/figures/publication/` | Report figures fig1–fig7 and fig8 as 300-dpi PNG, PDF and SVG, plus the wide workflow fig0 (`analysis_full/export_figures.py`) |

Every figure comes in three formats:
- **PDF** (vector, fonts embedded) for print;
- **SVG** (vector, text editable) for layout tools;
- **PNG** at 300 dpi.

Use the PDF or SVG in the poster file wherever the layout tool accepts it.

**Print width.** At the minimum print width given for each figure, the smallest text is at least 13 pt and the main
labels are 14–18 pt, readable from about 1–1.5 m. Print larger if the layout allows; do not print smaller. The text
sizes are fixed in points, so the native size is the size at which the text is exactly as designed (16–18 pt).

Colors are the same in every figure:
- blue `#2a78d6`: Shapley value, the model's own citations, and the Positive label;
- orange `#eb6834`: leave-one-out, and the content-only citer;
- red `#e34948`: the Negative label;
- gray `#a3a29a`: Neutral.

The blue/orange and blue/red pairs were checked for color-blind separation. Every figure also uses shape, position or
direct labels, so no meaning depends on color alone.

---

## Poster figures (recommended)

### P1. Workflow: `poster_fig1_workflow` (wide) or `poster_fig1b_workflow_vertical` (one column)

- **Native size:** 16.3 × 5.5 in (wide) and 9.9 × 7.1 in (vertical).
- **Minimum print width:** 22 in for the wide version, so that it spans two or three columns; 9.5 in for the vertical
  version, in one column (10.5 in recommended).
- **Data:** none (diagram).

**Short caption:** How Memory X-Ray works. Steps 1–4 measure which evidence actually moves the model's answer. Steps 5–6
ask the model which evidence it used and compare the two.

**Long caption:** Each scenario gives the model a question and four evidence records. We score the model's answer
probabilities on all 16 combinations of the records in 3 fixed orders (48 prompts per scenario). We then compute each
record's Shapley value and leave-one-out effect. Next, the model is asked which records it relied on, and each cited set
is compared with every other set of the same size. Validation checks run throughout. A post hoc content-only citer is
scored the same way for comparison.

### P2. Redundancy: `poster_fig2_redundancy` · **pre-registered quantities**

- **Native size:** 13.2 × 7.1 in. **Minimum print width:** 10.5 in.
- **Data:** `results/report_numbers.json` (S-redundant and Macro C, Shapley and leave-one-out).

**Short caption:** Removing one record at a time misses backups. When two records each settle the answer, leave-one-out
scores both about 0, while Shapley values credit each with about 0.48.

**Long caption:** Bars show the mean over 3 evidence orderings and lines show the range across them. These are not
confidence intervals. In the designed redundancy control (top), two official reports of the same rate hike are each
sufficient alone. In realistic scenario Macro C (bottom), three records each point to Negative and the model treats them
as largely interchangeable.

### P3. Conflict: `poster_fig3_order_decides_conflict` · **pre-registered control; descriptive count**

- **Native size:** 9.7 × 7.5 in. **Minimum print width:** 8 in.
- **Data:** the saved S-conflict prompts (`runs/full_20261017T223452Z/s_conflict/cells.jsonl`).

**Short caption:** When two rules conflict, the later record wins. The instruction says a rate cut overrides an
inflation report, but the model's answer follows whichever of the two comes later, in 12 of 12 prompts.

**Long caption:** Each dot is one of the 4 evidence combinations that contain both conflicting records, in one of the 3
fixed orders. The y-axis is the model's probability of Positive, and the color is its answer. The designed answer is
Positive in all 12. Only one order (shaded) puts the rate cut after the inflation report, so "later wins" rests on one
ordering contrast, confounded with last position. The S-conflict control failed its pre-registered recovery checks
BC1, BC3 and BC4 for this reason. BC5 also failed, marginally, for a separate reason.

### P4. Citations vs a citer that never looks at the model: `poster_fig4_citations_vs_content_only` · **model: pre-registered; content-only citer: post hoc**

- **Native size:** 11.3 × 8.0 in. **Minimum print width:** 9.5 in.
- **Data:** `results/post_hoc/content_only_baseline.json`.

**Short caption:** The model's citations beat chance, but a rule that never looks at the model, built from our design
and rubric, does as well or better in 17 of 18 comparisons.

**Long caption:** The beat fraction is the share of same-size alternative record sets that the cited set beats on
necessity (left) and sufficiency (right); 0.5 is chance.
- **Blue circles:** the model's own sampled partial citations (n = 5–8 per scenario; 40 pooled).
- **Orange squares:** a post hoc rule that cites the records whose content supports the answer, judged from the design or
  rubric (one fixed set per scenario).

The "17 of 18" counts three metrics per scenario. Two are plotted; the third, Shapley top-k agreement, is equal or
higher for the content-only citer in every scenario. The content-only citer is higher in 10 comparisons, tied in 7 and
lower in 1 (S-redundant sufficiency, 0.633 vs 0.656). It is not a like-for-like comparison: one fixed set per scenario,
against the model's sampled citations. The comparison is descriptive, and no statistical test was run.

### P5 (optional). Flips: `poster_fig5_flips` · **post hoc, descriptive**

- **Native size:** 13.6 × 6.6 in. **Minimum print width:** 10.5 in.
- **Data:** `results/report_numbers.json` (flips).

**Short caption:** Reversing one key record lowers the probability of the scenario's decision in 9 of 9 cases, but
changes the one-word answer in only 5 of 9.

**Long caption:** Each row is one realistic scenario in one evidence order. The dot is the probability of the
scenario's decision d\* with all evidence, and the arrowhead is that probability after one pre-chosen record is reversed
(for example, a rate cut becomes a rate hike). Blue arrows mark cases where the model's answer label changed. In Macro A
ordering 0 the model's answer was already Neutral, not d\* = Positive.

---

## Report figures (for a handout, an appendix panel or Q&A)

Each figure is in `results/figures/publication/` (and at 200 dpi in `results/figures/`). It is drawn for reading at about
11–14 in wide, so on a poster use it only at that size or larger.

| File | Short caption | Status |
|---|---|---|
| `fig0_workflow` | Workflow (same as P1) | diagram |
| `fig1_validation_overview` | All infrastructure checks pass in 6/6 scenarios; S-single and S-redundant pass recovery; S-conflict fails BC1, BC3, BC4, BC5 | pre-registered |
| `fig2_controls_shapley_vs_loo` | Shapley values and leave-one-out in the three designed controls | pre-registered |
| `fig3_s_conflict_ordering_effect` | Full label distributions for the 12 S-conflict prompts containing both conflicting records | pre-registered control; descriptive |
| `fig4_macro_a_decision` | Macro A: the full-evidence answer is Neutral in one order and Positive in two; d\* = Positive by a mean margin of 0.020 | pre-registered |
| `fig5_flip_effects` | Counterfactual flips: probability shifts and label changes | C4 pre-registered; ΔP post hoc |
| `fig6_realistic_shapley_vs_rubric` | Realistic scenarios: observed Shapley values vs rubric-following values (signs agree 12/12; weights differ) | pre-registered |
| `fig7_citations` | Citation parse outcomes (46/60 sampled analyzable) and beat fractions by scenario | pre-registered; aligned split post hoc |
| `fig8_content_only_baseline` | Content-only citer vs the model's citations (report-style version of P4) | post hoc |
