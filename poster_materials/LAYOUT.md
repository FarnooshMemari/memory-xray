# Suggested poster layout

This is a content plan for the design step, not a final design. All sizes are suggestions.

## Recommended format: 36 × 24 in, landscape

It is above the 24 × 24 in minimum, and it is the most common academic poster size. The same grid scales by 4/3 to
48 × 36 in: multiply every size below by 1.33.

- **Margins:** 0.6 in on all sides.
- **Columns:** 3 × 11.2 in, with 0.6 in gutters.
- **Title band:** 3.2 in tall, full width.
- **Content area:** 19.2 in tall below the title band (after a 0.4 in gap).

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ TITLE: Does a language model cite the evidence it actually uses?               [QR code] │
│ Subtitle · Farnoosh Memari · Duke University · Independent research · [date]              │  3.2 in
├─────────────────────────────┬─────────────────────────────┬──────────────────────────────┤
│ 1 THE QUESTION (box)        │ 5 IS THE MEASUREMENT        │ 8 FINDING 3: CITATIONS LOOK  │
│                             │   TRUSTWORTHY?              │   RIGHT…                     │
│ 2 WHY IT MATTERS            │                             │ 9 FINDING 4: …BUT LOOKING    │
│                             │ 6 FINDING 1: LEAVE-ONE-OUT  │   RIGHT ≠ FAITHFUL           │
│ 3 KEY IDEA                  │   MISSES BACKUPS            │   [poster_fig4 citations vs  │
│   + glossary box            │   [poster_fig2 redundancy]  │    content-only citer]       │
│                             │                             │                              │
│ 4 HOW WE TESTED IT          │ 7 FINDING 2: ORDER DECIDES  │ 11 TAKEAWAYS (highlight box) │
│   [poster_fig1b workflow,   │   CONFLICTS                 │                              │
│    vertical]                │   [poster_fig3 conflict]    │ 12 LIMITATIONS · 13 NEXT     │
│                             │                             │    STEPS                     │
├─────────────────────────────┴─────────────────────────────┴──────────────────────────────┤
│ 14 Reproducibility strip + QR · 15 References (8) · 16 Acknowledgments / AI-use statement │  1.2 in
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### Space budget

Heights are in inches, within the 19.2 in columns. The footer takes about 1.2 in, so the columns have about 18 in.

| Column 1 (motivation and method) | in | Column 2 (measurement findings) | in | Column 3 (explanation findings and conclusion) | in |
|---|---|---|---|---|---|
| 1 Question (highlight box) | 1.8 | 5 Trustworthy? | 1.9 | 8 Finding 3 text | 1.8 |
| 2 Why it matters | 2.3 | 6 Finding 1 text | 1.6 | 9 Finding 4 text | 2.9 |
| 3 Key idea + glossary | 3.6 | poster_fig2 at 10.8 in wide | 5.8 | poster_fig4 at 10.5 in wide | 7.4 |
| 4 How we tested (text) | 2.9 | 7 Finding 2 text + caveat | 2.4 | 11 Takeaways (box) | 3.4 |
| poster_fig1b at 10.5 in wide | 7.5 | poster_fig3 at 8.2 in wide | 6.3 | 12–13 Limitations + next steps | 2.5 |
| **total** | **18.1** | **total** | **18.0** | **total** | **18.0** |

### If it does not fit

Cut in this order:
1. the glossary box (move the three definitions into section 3 as one line each);
2. sections 12–13, merged into four bullets;
3. section 2, cut to two sentences.

Leave out the optional Finding 5 (poster_fig5) at this size. Use it at 48 × 36, or keep it for questions.

### Alternative wide-workflow arrangement

Place `poster_fig1_workflow` as a band across columns 1–2, at about 22.9 × 7.7 in, directly under the title. Section 4's
text then goes below it in column 1, and Finding 1 moves to the top of column 2.

## Typography (36 × 24 in; multiply by 1.33 for 48 × 36)

| Element | Size | Notes |
|---|---|---|
| Title | 80–90 pt bold | One line if possible, at most two |
| Subtitle | 40 pt | |
| Authors / affiliation | 30–32 pt | |
| Section headings | 40–44 pt bold | Lead each finding with its claim, e.g. "Order decides conflicts" |
| Body text | 24–26 pt | About 10–12 words per line in an 11 in column; left-aligned, not justified |
| Figure captions | 20 pt | Use the short captions from `FIGURE_CAPTIONS.md` |
| Tags (pre-registered / post hoc) | 18–20 pt small caps or pill labels | Keep them visible: they carry the scientific status |
| References, footer | 16–18 pt | |

- **Fonts:** one sans-serif family throughout. The figures use DejaVu Sans; Inter, Source Sans or Helvetica are close
  matches.
- **Word budget:** about 850 words of main text at 24 pt fits the plan above. Above about 950 words, cut, following the
  order in the previous section.

## Colors

Use the figure palette so that the text and figures read as one system:

| Role | Hex |
|---|---|
| Background | `#fcfcfb` (warm white), or pure white |
| Main text | `#0b0b0b` |
| Secondary text | `#52514e` |
| Rules, box borders | `#c3c2b7` |
| Light panel fill | `#f1f0eb` or `#e1e0d9` at 50% |
| Accent 1, "what the model does" / Shapley / model citations | blue `#2a78d6` |
| Accent 2, "what it says" / leave-one-out / content-only citer | orange `#eb6834` |

- Section headings work well in near-black, with a thin blue or orange rule that matches the workflow color of that half
  of the story: methods and measurement in blue, citations in orange.
- Highlight boxes (the Question and the Takeaways) should use the light panel fill, not a saturated color.

## Square format: 24 × 24 in (the minimum size)

Use two columns of 11.1 in (0.6 in margins and gutter), a 2.6 in title band, and the **short versions** at the end of
`POSTER_TEXT.md`. Keep about 450 words.

| Column 1 | Column 2 |
|---|---|
| Question (short) · Key idea (2 sentences) · poster_fig1b (10 in wide) | Finding 2 (one sentence) + poster_fig3 (8 in) · Finding 3 + 4 (three sentences) + poster_fig4 (10 in) |
| Finding 1 (one sentence) | Takeaways (3 bullets) · Limitations (one line) · QR |

At this size, use 22 pt body text and 60–70 pt for the title. Drop poster_fig2 and keep its result as one sentence with
the numbers 0.48 vs ≈ 0.

## Accessibility checklist

- Contrast: body text `#0b0b0b` or `#52514e` on `#fcfcfb` passes WCAG AA at these sizes.
- No meaning carried by color alone: the figures use shapes, positions and direct labels.
- Each figure has a caption that states its main point in words.
- Spell out "Shapley value" and "leave-one-out" once, near their first use.
- Put the QR code at least 1.2 in square, with its URL printed under it.
