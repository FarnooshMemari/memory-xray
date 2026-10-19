# Poster materials

Content and visuals for the Memory X-Ray research poster. The final poster design is not included; these files are
the inputs for the layout and design step.

| File | What it is |
|---|---|
| [`POSTER_TEXT.md`](POSTER_TEXT.md) | Text for every poster section, written for readers new to XAI, with word targets, pre-registered / post hoc tags and short versions |
| [`KEY_NUMBERS.md`](KEY_NUMBERS.md) | Every number used on the poster, generated from the result files (`python scripts/make_key_numbers.py --check` confirms it is current) |
| [`figures/`](figures/) | Poster figures at print size, each as PDF (vector), SVG (editable) and 300-dpi PNG; regenerate with `python analysis_full/poster_figures.py` |
| [`FIGURE_CAPTIONS.md`](FIGURE_CAPTIONS.md) | Short and long captions, minimum print widths, data sources and the pre-registered / post hoc status of each figure |
| [`LAYOUT.md`](LAYOUT.md) | Suggested 36 × 24 in layout (also 48 × 36 and a 24 × 24 minimum variant), space budget, typography, colors and accessibility notes |
| [`TAKEAWAY_AND_TALK.md`](TAKEAWAY_AND_TALK.md) | Key takeaway at three lengths, a 30-second pitch, a timed 5-minute talk outline and anticipated questions |
| [`REFERENCES.md`](REFERENCES.md), [`references.bib`](references.bib) | 29 verified references with a relevance note for each, a suggested short list of 8, and BibTeX |

## Figures

| File | Use |
|---|---|
| `poster_fig1_workflow` | Workflow diagram, wide (spans 2–3 columns) |
| `poster_fig1b_workflow_vertical` | Workflow diagram, one column |
| `poster_fig2_redundancy` | Finding 1: Shapley vs leave-one-out |
| `poster_fig3_order_decides_conflict` | Finding 2: the later record decides the conflict |
| `poster_fig4_citations_vs_content_only` | Findings 3–4: citations vs a citer that never looks at the model (post hoc) |
| `poster_fig5_flips` | Optional: probabilities move more than labels |

The seven report figures, and a report-style version of the content-only figure, are in `results/figures/publication/`.

## Before printing

- Fill in the bracketed fields in `POSTER_TEXT.md`: the date and the acknowledgments, and generate the QR code for
  <https://github.com/FarnooshMemari/memory-xray>.
- Edit the AI-use statement to match any policy that applies (Duke's or the venue's).
- Keep the **pre-registered** / **post hoc** tags next to the findings.
- If you change any number, change it in the result files and regenerate. Do not edit `KEY_NUMBERS.md` by hand.
