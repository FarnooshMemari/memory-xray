# Validation record

Latest full run: 2026-10-19. Environment: Node 22.22.0 (npm 10.9.4), Python 3.13 and Chromium 141
(Playwright 1.56.1). Toolchain: Vite 7.3.7 and Vitest 4.1.12. `npm audit` reports no known
vulnerabilities.

## Data accuracy

| Check | Result |
|---|---|
| `npm run data:verify` (93 independent checks against the raw run, the reanalysis and the reports) | all pass |
| 288 saved states (6 scenarios × 3 orderings × 16 combinations) vs the independent reanalysis | max difference 0 |
| Shapley values recomputed from all 24 permutations | max difference 2.2e-16 |
| Probabilities in every state sum to 1; argmax matches the saved label | pass |
| Citation replies (78): status, cited records, scores and raw text match the run files | pass |
| Sampled reply statuses: 45 ok, 14 unparseable, 1 empty | pass |
| Pooled scores: model 0.896 / 0.848 / 0.883; content-only 1.000 / 0.939 / 1.000; 10 higher, 7 tied, 1 lower | pass |
| Per-scenario content-only scores, Shapley means and ranges, record texts | pass |
| Misaligned (injected-decision) orderings: S-conflict 0 and 1, Macro A 0 | 3 of 18, pass |
| Scored citations in those orderings | 8 of 40, pass |
| Post hoc aligned / misaligned pools (0.91 vs 0.85 on necessity) | pass |
| Rebuilding the data file from the source repository | byte-identical |

## Automated tests

| Suite | Result |
|---|---|
| `npm run typecheck` | pass |
| `npm test` (Vitest: data structure and recomputation) | 8 passed |
| `npm run test:e2e`, desktop 1440×900 | 11 passed |
| `npm run test:e2e`, phone (Pixel 7) | 2 passed |
| `npm ci` → `npm run build` from a clean copy | pass; reproduces the shipped `dist/` |

The browser tests drive every one of the 288 states through the page. For each state they
compare the gauge probabilities, the three bar values and the pull of all four traces with the
data file.

They also cover:

- toggling, "Show all four" and the URL state;
- reordering;
- the citation layer, the injected-decision banner and the ledger flags;
- lattice clicks and the Shapley callout;
- the tour;
- keyboard use: arrow keys in every radio group, the tour not taking over other controls, and
  focus returning when the tour closes;
- reduced motion;
- on phones: the pinned answer and no horizontal overflow.

## Accessibility

axe-core (WCAG 2 A and AA) reports no violations in these states:

| Layout | States |
|---|---|
| Desktop | `s_conflict/o0/m15` with and without the citation layer and with the tour open, `s_redundant/o0/m10`, `macro_a/o0/m15`, `macro_b/o1/m13` |
| Phone | the same states |

There is no horizontal overflow at 320, 412, 768, 870, 1024, 1180, 1280 or 1440 px wide.

## Independent review

A separate reviewer, who had not seen the page being built, checked every claim on the page
against the data and the source repository. It also tested the README from a clean copy. It
found no critical issues. Its findings were fixed as follows:

- **Injected-decision citations in the summary charts.** They are now flagged wherever
  citations are summarised:
  - a hatched segment on the "what it says" bars;
  - a note giving the counts;
  - a diamond on the affected rows of the "catch" chart, with counts (S-conflict 5 of 8,
    Macro A 3 of 5, all six 8 of 40);
  - a banner and marked ticks in the instrument;
  - the count in the tour's last step.
- **A post hoc claim tagged as observed.** The aligned/misaligned comparison is now tagged
  Post hoc.
- **Missing caveats on the content-only citer.** A Limitation now states that it is an oracle,
  since it reads the design or rubric the model never sees. It also states that its top-k
  score of 1 is built in for the realistic cases. The heading now reads "scores just as well".
- **Workflow trigger.** The `paths` filter that tied the workflow to `explorer/` was removed.
- **Wording.**
  - The S-conflict limitation now gives the per-ordering counts (0 of 4, 0 of 4, 4 of 4)
    rather than "did not follow the rule".
  - The tour's order-effect step names the confound.
  - Rubric scores read "points to Positive/Negative" instead of ±1.
  - The citation scores are described as "from the sampled replies only".
  - The top-k description and its chance line were corrected.
- **Traces.** "No pull" now means |pull| < 0.005, which matches the 2-decimal labels.
- **Accessibility.**
  - Arrow keys work in every radio group.
  - The tour no longer captures arrow keys from other controls, and it returns focus when it
    closes.
  - The tour has a stable live region.
  - The dumbbell chart's text alternative includes its values.
  - The failed-check note is visible on phones.
- **Tooling.**
  - Vite and Vitest were upgraded to patched versions.
  - `verify_data.py` now also checks every field the page displays.
  - The browser tests start their own server unless told otherwise.

## Visual review

Screenshots in `screenshots/` were reviewed at desktop (1440×900, 2×) and phone (Pixel 7)
sizes, and spot-checked at 768–1280 px. The visual passes fixed the following:

- Dotted and dashed traces were drawing as solid lines after the opening draw-in animation.
- Dash gaps on thick "if added" traces were invisible. The dashes now scale with the trace, and
  the key explains the dashed style.
- At 861–1180 px, the probability bars sat below the ring, where incoming traces crossed them.
  They now stay beside a smaller ring.
- Between 860 and 940 px the masthead wrapped. The navigation now hides below 940 px.
- On phones, chart text shrank below a legible size. The lattice, the context chart and the
  dumbbell chart now switch to layouts drawn for narrow screens.
- Legend markers sat too close to their text.

## Deployment (2026-10-19)

The explorer is published at **https://farnooshmemari.github.io/memory-xray/** by
`.github/workflows/explorer-pages.yml`.

**The deploy run.** On GitHub's runner it installed with `npm ci`, ran the unit tests and
`npm run data:verify` against the saved run files in the repository, built the site and
deployed it. Every step passed.

**What the public URL serves.** This was checked by fetching the URL directly:

- The page has the new title and description, without the old version label.
- It serves the fingerprinted bundle `assets/index-DBgYY84E.js` and stylesheet
  `assets/index-9aJtXRXr.css`. These are the same content-hashed files as the build tested here.

**Click-through on the deployed files.** The test environment cannot open github.io, so the
interaction checks were run on those same files, served at the same `/memory-xray/` path as
GitHub Pages. In Chromium at 1440×900 and on a Pixel 7, 63 of 63 checks passed:

- every scenario shows its saved answer;
- removing and restoring records, "Remove all", "Show all four" and changing the ordering all
  match the saved probabilities;
- the traces, the answer ring and its bars, the 16-node lattice, the Shapley context chart, the
  citation bars and ledger (with their injected-decision flags), the "catch" chart and the
  citation banner all render;
- all eight tour steps load their saved states and the tour closes;
- on the phone, the answer stays pinned;
- there is no horizontal overflow, no failed request and no console error.

**Repository checks.** With `explorer/` added, the repository's own `scripts/verify_release.py`
passed 18 of 18 checks on a clean checkout. Its pytest suite passed 123 tests, with 1 skipped.

## Scope checks

- The integration adds `explorer/` and `.github/workflows/explorer-pages.yml`, plus a demo link
  near the top of the main README. No frozen experiment, result, report or poster file was
  modified.
- No external client or organization is named anywhere in the source, docs or build (checked by text search).

## Not covered

- **Browsers.** Only Chromium was run, not Firefox or Safari. The page uses only standard SVG,
  CSS grid and `position: sticky`, so it is expected to work there, but this has not been
  checked.
- **Screen readers.** The page has not been tested with a physical screen reader. It was checked
  only with axe and by reviewing its roles and labels.
- **Live clicks.** The interaction checks ran on the deployed files, not through the github.io
  host itself (see Deployment above).
