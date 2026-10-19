# Key takeaway and 5-minute presentation

## Key takeaway

**One sentence (for the poster's highlight box):**
> A language model's citations can agree, on average, with the evidence that drives its answers without showing that
> they are faithful: they still pointed toward a label the model had not chosen in that ordering, and a citer that never
> looked at the model scored as well or better.

**Even shorter (≤ 12 words):**
> Citations that look right are not proof the model used them.

**Three-point version:**
1. Removing evidence in every combination reliably shows what drives a model's answer, and it catches backups that
   one-at-a-time removal misses.
2. The model's citations match that measure on average, but they still point toward a label it was shown even when
   that label was not its own answer in that ordering.
3. A citer that only reads the content scores as well, so in this design these metrics can't certify faithful
   citations.

## 30-second elevator pitch

> "When AI systems cite their sources, we tend to trust that those sources drove the answer. I tested that with a small
> open model. I gave it four pieces of evidence, removed them in every combination, and measured which ones really moved
> its answer. Then I asked the model which ones it used. Its citations usually pointed to the influential evidence. But
> when I showed it an answer it hadn't given for that ordering, it still cited evidence pushing toward that answer. And
> a simple rule that never looks at the model scored as well or better. So citations that look right aren't, on their
> own, evidence of faithful explanations, and we need tests that can tell the difference."

## 5-minute talk outline

Total: about 650 spoken words. **Point at** names what to gesture to on the poster.

| Time | Section | What to say (key lines) | Point at |
|---|---|---|---|
| 0:00–0:30 | **Hook and question** | "When a chatbot shows you its sources, do you assume those sources drove the answer? I tested whether a model's own citations match what actually changes its answer." | Title, Question box |
| 0:30–1:15 | **Why and the key idea** | "A citation can be plausible without being faithful. To know what really drives an answer, I don't ask the model; I remove evidence and watch the answer's probability. With four records there are 16 combinations, and Shapley values split the effect fairly among them. This is behavioral: it tells us what the output depends on, not what happens inside the network." | Key idea, glossary |
| 1:15–2:00 | **Method** | "Six scenarios. Three are controls where I built in the answer: one decisive record, two redundant records, two conflicting records with a tie-break rule. Three are realistic economic scenarios. Every combination in three orders gives 48 prompts per scenario, scored deterministically. Then I ask the model which records it relied on, 13 times per scenario. Everything was frozen before the run." | Workflow figure |
| 2:00–2:20 | **Trust the measurement** | "The checks pass in all six scenarios, and a separate re-implementation reproduces every number." | Validation line |
| 2:20–2:50 | **Finding 1: backups** | "When two records each settle the answer, removing one at a time says neither matters, about zero. Shapley gives each about half. So one-at-a-time removal can badly mislead." | Redundancy figure |
| 2:50–3:25 | **Finding 2: order** | "I told the model a rate cut overrides an inflation report. It didn't listen. Whichever of the two came later won, 12 out of 12. That's one ordering contrast, so I call it consistent with recency, not proof. But that control failed, and I report it as a failure." | Conflict figure |
| 3:25–4:25 | **Findings 3–4: citations** | "The citations look good: they beat same-size alternatives about 90% of the time on necessity. But two things. First, in 3 of 18 cases the answer I showed the model wasn't its own answer for that ordering, and it still cited evidence that pushes toward the answer it was shown: a bit less well on average, but above chance every time. Second, after seeing the results, I built a citer that never looks at the model and just cites evidence whose content supports the answer, according to my design and rubric. It scored as well or better in 17 of 18 comparisons. So these scores show the model can name supporting evidence. They don't show it's reporting what drove its decision." | Citations figure (blue vs orange) |
| 4:25–5:00 | **Takeaway and limits** | "So: measure influence by removal, in every combination; don't trust one-at-a-time removal; and don't treat plausible citations as faithful. This is one small model and six scenarios, so they're case studies. Next I want scenarios where supporting evidence and driving evidence differ, so a test can actually separate the two. Everything is public and reruns on a laptop in a minute." | Takeaways box, QR code |

**Timing tips.**
- If you are running long, compress Finding 1 to one sentence; the figure carries it.
- Do not cut the pre-registered vs post hoc distinction in Findings 3–4.

## Anticipated questions

**"Six scenarios is tiny. Can you generalize?"**
No, and I don't claim to. These are controlled case studies with one model. The value is in the design: known ground
truth in the controls, exact attribution, and pre-registration. It shows that these citation metrics, in this design, can't
separate faithful from plausible citations, even in this simple setting.

**"Why not 288 data points?"**
The 288 prompts are 16 combinations × 3 orders × 6 scenarios. They are structured measurements of six cases, not
independent samples, so I report per-scenario results and run no significance tests.

**"Is Shapley the ground truth for what the model used?"**
It is ground truth for *behavioral* dependence: how the output changes when evidence is present or absent. It is not a
view of internal mechanisms. Removing a record also changes the positions of the others, and the conflict result shows
that position matters.

**"Isn't the content-only citer unfair? It uses your rubric."**
Yes. It is an oracle content reader, not a competitor. The point is that information which says nothing about the model's
behavior is enough to score at the top of these metrics. So a high score can't, by itself, mean the model reported its
own reasoning. It was also defined after seeing the results, which is why it's labeled post hoc.

**"Does this mean the model's citations are unfaithful?"**
Not necessarily. A model that reads content well *and* reports faithfully would look the same. The result is that this
kind of test can't tell the difference.

**"Is the recency effect real?"**
It's consistent with recency, but my design can't isolate it. Only one of the three fixed orders put the overriding
record last, and that order also changes adjacency and last position. A clean test would vary the order of the two
conflicting records while holding positions fixed.

**"Why Phi-3-mini?"**
It is open-weight, so I can read exact label probabilities and pin the exact version, and it is small enough to run on
free Colab. The trade-off is that larger models might behave differently.

**"Who decided the right answers for the realistic scenarios?"**
A written rubric. Its scores were drafted with an AI assistant and checked by two separate AI models, which agreed 15/15.
That is AI-assisted validation, not human annotation, and I say so. The rubric sets the reference answers and the
rubric-following comparison values, and it defines the post hoc content-only citer. The attributions and the model's
citation scores are measured against the model's own behavior.

**"What's new here?"**
I don't claim a new method. Ablation-based context attribution (e.g. ContextCite) and self-consistency tests of
self-explanations (e.g. Madsen et al.) already exist. The contribution is a small, fully reproducible controlled study
with designed ground truth. It shows two specific pitfalls: label-conditional rationales, and a content-only baseline
that matches the model.

**"What went wrong along the way?"**
The first feasibility run failed a numerical-precision check (float16 rounding). I fixed it with float32 computation,
documented it as a protocol amendment, and kept the failed run. The conflict control failed and is reported as a failure.
