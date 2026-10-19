# Poster text: Memory X-Ray

Ready-to-place text for each poster section, written for readers without an XAI background. It is consistent with
`results/RESULTS_AND_DISCUSSION.md`, `docs/POST_HOC_ADDENDUM.md` and the generated `KEY_NUMBERS.md`.

- **Word targets** are given per block. The full main text is about 850 words, which suits a 36 × 24 in poster at 26–28 pt
  body text.
- **Tags:** keep the small **pre-registered** / **post hoc** tags in the printed text. They are part of the scientific
  claim, not decoration.
- **Bracketed fields** such as `[date]` are for you to fill in.

---

## Title block

**Title (pick one):**
- **Does a language model cite the evidence it actually uses?** *(recommended)*
- Memory X-Ray: testing whether a language model's citations match what drives its answers

**Subtitle:** A controlled evidence-removal study of a small language model's self-reported citations

**Authors / affiliation:** Farnoosh Memari · Duke University · Independent research in explainable and responsible AI · [date]

**Contact / code:** github.com/FarnooshMemari/memory-xray · [QR code to https://github.com/FarnooshMemari/memory-xray]

---

## 1. The question  *(≈ 45 words)*

When an AI assistant answers from evidence and then tells you which evidence it used, is it telling you what actually
drove its answer, or just naming evidence that sounds right? We tested this directly by comparing a model's citations
with what really changes its answer.

## 2. Why it matters  *(≈ 70 words)*

Chatbots that search documents or remember past conversations increasingly show "sources" for their answers, and people
trust answers more when sources are shown. But a citation can be **plausible** (the cited text supports the answer)
without being **faithful** (the cited text is what the model relied on). If citations are only plausible, they can hide
what the model actually used, and they cannot be relied on to audit it.

## 3. The key idea: measure influence by removing evidence  *(≈ 90 words)*

We give the model four short evidence records and ask for a one-word answer: Positive, Neutral or Negative. Then we
remove records, in every possible combination, and watch how the probability of the model's answer changes.

- A record that **matters** changes that probability when it is removed.
- A **Shapley value** fairly divides the total change among the four records, averaging over all combinations.

This tells us which records drive the answer **from the outside**, by behavior. It does not look inside the network.

> **Glossary box (optional, ≈ 60 words)**
> - **Leave-one-out:** remove one record and see what changes.
> - **Shapley value:** a record's fair share of the effect: its average added effect when it joins the other records,
>   weighted over all combinations of them.
> - **Beat fraction:** how often the cited set is more influential than other sets of the same size. 0.5 is chance; 1.0 is
>   best.
> - **Pre-registered:** fixed before the experiment ran. **Post hoc:** added after seeing the results.

## 4. How we tested it  *(≈ 110 words; next to the workflow figure)*

- **Model:** Phi-3-mini, a small open model, pinned to one exact version. Its answers were scored as probabilities, with
  no randomness.
- **Six scenarios:**
  - three designed **controls** whose correct answer and decisive evidence we built in (one decisive record; two
    redundant records; two conflicting records with a stated tie-break rule);
  - three **realistic** economic scenarios, checked against a written rubric that the model never sees.
- **48 prompts per scenario:** all 16 combinations of the four records × 3 fixed orders.
- **Citations:** the model is asked "Which evidence records did your answer rely on?" (13 replies per scenario). Each
  cited set is compared with every other set of the same size.
- Protocol, scenarios and thresholds were **frozen before the run** (pre-registered).

## 5. Is the measurement trustworthy?  *(≈ 55 words)*

Yes, within its scope. Nine infrastructure checks pass in all six scenarios. A separate re-implementation reproduces every
number (largest difference 2.2 × 10⁻¹⁶). In the single-cause and redundancy controls, the attribution recovers the
structure we built in. **pre-registered**

## 6. Finding 1: Removing one record at a time misses backups  *(≈ 60 words; with poster_fig2)*

When two records each settle the answer on their own, removing either one changes almost nothing, so leave-one-out scores
both near **0**. Shapley values credit each with about **0.48**. The same masking appears in a realistic scenario (0.28–0.35
vs 0.04–0.07). **pre-registered**

→ *Use subset-based attribution when sources may overlap.*

## 7. Finding 2: In our conflict test, the order of the evidence decided  *(≈ 70 words; with poster_fig3)*

We told the model that a rate cut overrides an inflation report. It did not follow this rule. In all **12 of 12**
prompts containing both records, the answer followed whichever record came **later**; the rule held in only 4. This
control **failed** its pre-registered recovery checks (one of the four failures, BC5, is marginal and has a separate cause).
**pre-registered checks; descriptive count**

*Caveat:* only one of our three orders put the rate cut last, so this is one contrast, not a proven recency effect.

## 8. Finding 3: The citations look right…  *(≈ 55 words; with poster_fig4, blue dots)*

The records the model cites are usually the influential ones. Its cited sets beat same-size alternatives with a mean beat
fraction of **0.90** for necessity and **0.85** for sufficiency (chance = 0.5). In the two simplest controls, every parsed
reply cited the planted cause. **pre-registered**

## 9. Finding 4: …but looking right is not the same as being faithful  *(≈ 100 words; with poster_fig4, orange squares)*

- **It also backs a label it did not choose.** In 3 of 18 cases, the answer we showed the model was not its own answer for
  that order of the evidence. Its citations still pointed toward the shown label: all 8 beat chance, though they scored
  lower on average. **post hoc split**
- **A citer that never looks at the model does as well.** A simple rule cites the records whose *content* supports the
  answer, judged from our design and rubric. It scores **1.00 / 0.94**, against the model's 0.90 / 0.85; this is not a
  like-for-like comparison (one fixed set vs the model's sampled citations). Across 18 comparisons it is higher in 10,
  tied in 7 and lower in 1. **post hoc**

So these scores show the model can **name evidence that supports an answer**, not that it **reports what drove its own
answer**.

## 10. Optional finding: probabilities move more than labels  *(≈ 45 words; with poster_fig5)*

Reversing one key record (for example, a rate cut becomes a hike) lowered the probability of the scenario's decision in
**9 of 9** cases, by 0.17 to 0.54. But the one-word answer changed in only **5 of 9**. Label-only tests understate
influence. **post hoc, descriptive**

## 11. Takeaways  *(≈ 75 words)*

1. **Removing evidence, in every combination, is a sound and reproducible way to measure which evidence drives a model's
   answer.** It catches redundancy that one-at-a-time removal misses.
2. **The model's citations agree with this measurement on average, but agreement is not faithfulness.** Citations for a
   label the model had not chosen in that ordering still scored above chance, and simply reading the content scored as
   well.
3. **To audit AI citations, use a test that can tell a faithful citer from a plausible one.** Report probability shifts,
   not just label flips, and control evidence order.

## 12. Limitations  *(≈ 75 words)*

- **Scope:** one small model, one prompt format, six scenarios. These are case studies, not general claims. There are no
  significance tests, and ranges across the three orders are not confidence intervals.
- **Measurement:** attribution is behavioral, not a view of the model's internals. Removing a record also shifts the others'
  positions.
- **Rubric and texts:** the reference answers come from an AI-written rubric checked by two AI models, not by humans. The
  scenario texts are synthetic.
- **Post hoc analyses** qualify, and do not replace, the pre-registered results.

## 13. Next steps  *(≈ 40 words)*

- Design scenarios where the records that *support* the answer differ from the records that *drive* it, so that a
  faithful citer and a plausible citer would disagree.
- Vary the order of conflicting records independently of position.
- Test more models.

## 14. Reproducibility strip  *(≈ 35 words)*

All code, frozen scenarios, raw model outputs and analysis are public. Every number on this poster regenerates on a laptop
CPU in about a minute: `python scripts/verify_release.py`. [QR code to https://github.com/FarnooshMemari/memory-xray]

## 15. References  *(short list; full list in REFERENCES.md)*

1. Shapley, L. S. (1953). A value for n-person games. *Contributions to the Theory of Games II*.
2. Jacovi, A. & Goldberg, Y. (2020). Towards faithfully interpretable NLP systems. *ACL*.
3. Turpin, M. et al. (2023). Language models don't always say what they think. *NeurIPS*.
4. Madsen, A., Chandar, S. & Reddy, S. (2024). Are self-explanations from large language models faithful? *Findings of ACL*.
5. Cohen-Wang, B. et al. (2024). ContextCite: Attributing model generation to context. *NeurIPS*.
6. Wallat, J. et al. (2025). Correctness is not faithfulness in retrieval augmented generation attributions. *ICTIR*.
7. Liu, N. F. et al. (2024). Lost in the middle: How language models use long contexts. *TACL*.
8. Abdin, M. et al. (2024). Phi-3 technical report. *arXiv:2404.14219*.

## 16. Acknowledgments and AI-use statement  *(≈ 45 words; edit to match any policy that applies, e.g. Duke's or the venue's)*

[Acknowledgments.] The rubric scores were drafted with an AI assistant and validated by two AI models (not human
annotators). Code, packaging and poster drafting were assisted by Claude (Anthropic); all results come from the saved
experiment files and were reviewed by the author.

---

## Short versions (for tight space)

- **One-sentence takeaway:** A model's citations can match the evidence that drives its answers on average without
  showing that they are faithful. In our tests they still pointed toward a label the model had not chosen in that
  ordering, and a citer that never looked at the model scored as well or better.
- **Headline under the title (≤ 20 words):** We removed evidence in every combination to see what really drives a model's
  answer, then checked its citations.
- **Figure-free abstract (≈ 110 words):** We asked whether a small language model (Phi-3-mini) cites the evidence that
  actually drives its decisions. In six scenarios, we scored the model's answer on every combination of four evidence
  records in three orders, computed exact Shapley values, and compared them with the records the model said it relied on.
  - The measurement was validated and fully reproducible, and it exposed redundancy that leave-one-out misses.
  - The model did not follow a stated precedence rule: in our conflict test, the later of two conflicting records decided.
  - Its citations beat same-size alternatives (0.90 necessity, 0.85 sufficiency), and they still favored a shown label
    that was not its own answer in that ordering. A post hoc content-only citer, built from our design and rubric,
    scored as well or better in 17 of 18 comparisons.

  Citation consistency of this kind is therefore not evidence of faithful self-explanation.
