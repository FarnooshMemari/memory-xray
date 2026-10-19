import { cell, DATA, has, scenarioById } from "../lib/model";
import { Tag } from "./Tag";

export function AboutSection() {
  const m = DATA.meta;
  const conflict = scenarioById("s_conflict");
  const conflictFailed = conflict.checks.recovery.filter((c) => !c.passed).length;
  // per ordering: in how many of the prompts holding both conflicting records the answer matched the stated rule
  const ruleWith = conflict.orderings.map((o) => {
    let of = 0, match = 0;
    for (let k = 0; k < 16; k++) {
      if (!has(k, "E1") || !has(k, "E2")) continue;
      of++;
      if (cell(o, k).argmax === cell(o, k).rule) match++;
    }
    return { index: o.index, of, match, cutLast: o.order.indexOf("E1") > o.order.indexOf("E2") };
  });
  return (
    <section className="section about" id="about" aria-labelledby="about-title">
      <div className="wrap">
        <div className="section-head">
          <h2 id="about-title">About the data</h2>
          <p>
            Nothing on this page is simulated. Every probability, Shapley value and citation is read from the saved files of
            the v0.2 run; the page only looks them up.
          </p>
        </div>
        <div className="about-grid">
          <div>
            <h3>What was run</h3>
            <p>
              Model: {m.model}, pinned to commit <span className="hash">{m.commit.slice(0, 12)}</span>, scored on a {m.device}
              {" "}({m.precision}). Run {m.runId}.
            </p>
            <p>
              Six scenarios, each with four records. All 16 combinations of the records were scored in 3 fixed orders: 48
              prompts per scenario. The answer is the probability of Positive, Neutral or Negative after the prompt; no sampling.
            </p>
            <p>
              d* is the scenario&rsquo;s decision: the answer with all four records, averaged over the three orderings. A record&rsquo;s
              pull is measured on the probability of d*.
            </p>
          </div>
          <div>
            <h3>How to read the numbers</h3>
            <ul>
              <li>There are six scenarios, so n = 6. The 288 scored prompts are structured measurements of six cases, not independent samples.</li>
              <li>Differences between the three orderings show sensitivity to order. They are not confidence intervals, and no significance tests were run.</li>
              <li>Shapley values and leave-one-out describe how the output changes when evidence is removed. They are behavioral, not a view inside the model.</li>
              <li>A citation&rsquo;s beat fraction compares it with every other set of the same size; ties count half.</li>
              <li>Labels: <Tag kind="observed" /> read from the results, <Tag kind="posthoc" /> defined after the results were seen, <Tag kind="interpretation" /> what we think it means, <Tag kind="limitation" /> what it cannot show.</li>
            </ul>
          </div>
          <div>
            <h3>Limits worth knowing</h3>
            <ul>
              <li>
                The conflict control (S-conflict) failed {conflictFailed} of its {conflict.checks.recovery.length} pre-registered recovery checks.
                In prompts with both conflicting records, the answer followed the stated rule in{" "}
                {ruleWith.map((x, i) => `${i === ruleWith.length - 1 ? "and " : ""}${x.match} of ${x.of} (ordering ${x.index}${x.cutLast ? ", rate cut after the inflation report" : ""})`).join(", ")}.
                The difference rests on one ordering contrast, where position and adjacency change together.
              </li>
              <li>Citations were collected with all four records shown and the scenario decision d* in the prompt; in 3 of 18 orderings d* was not the model&rsquo;s own answer there.</li>
              <li>14 of 60 sampled citation replies could not be parsed and are shown as such.</li>
              <li>Realistic reference answers come from a rubric written with an AI assistant and checked by two AI models, not by people. Scenario texts are synthetic.</li>
              <li>Short record labels and scenario descriptions on this page are editorial summaries; the full record texts are shown on each slip.</li>
            </ul>
          </div>
        </div>
        <p className="lattice-caption" style={{ marginTop: 28 }}>
          Built from {m.sources.length} saved files (SHA-256 recorded in the data file) by <code>scripts/build_data.py</code> and checked
          against the raw run and an independent reanalysis by <code>scripts/verify_data.py</code>.
        </p>
      </div>
    </section>
  );
}
