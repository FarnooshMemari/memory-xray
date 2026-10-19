import { motion } from "framer-motion";
import { useState } from "react";
import { DATA } from "../lib/model";
import { radioKeys } from "../lib/radio";
import { useMediaQuery } from "../lib/state";
import { Tag } from "./Tag";

type Metric = "mean_beat_nec" | "mean_beat_suf" | "mean_topk";
const METRICS: { key: Metric; label: string; long: string }[] = [
  { key: "mean_beat_nec", label: "Necessity", long: "Removing the cited records lowers P(d*) more than removing other sets of the same size" },
  { key: "mean_beat_suf", label: "Sufficiency", long: "Keeping only the cited records preserves P(d*) better than other sets of the same size" },
  { key: "mean_topk", label: "Top-k agreement", long: "Share of the cited records that are among the records with the largest Shapley values (as many as were cited)" },
];
const SPRING = { type: "spring" as const, stiffness: 150, damping: 24 };

export function InsightSection() {
  const [metric, setMetric] = useState<Metric>("mean_beat_nec");
  const P = DATA.pooled;
  // scored (sampled, partial) citations given in orderings where the prompt showed a label the model had not chosen
  const injectedScored = (id: string) => DATA.scenarios.find((s) => s.id === id)!.citations
    .filter((c) => c.kind === "sampled" && c.beatNec !== null && !c.aligned).length;
  const rows = [
    ...DATA.scenarios.map((s) => ({ id: s.id, name: s.name, model: s.citationMetrics[metric], content: s.contentOnly[metric], n: s.citationMetrics.n_partial, inj: injectedScored(s.id) })),
    { id: "pooled", name: "All six", model: P.model[metric], content: P.contentOnly[metric], n: P.model.n_partial, inj: P.misaligned.n_partial },
  ];
  const injRows = rows.filter((r) => r.inj > 0);
  // narrow screens get a narrower drawing so its text stays near its set size instead of shrinking with the SVG
  const narrow = useMediaQuery("(max-width: 560px)");
  const W = narrow ? 350 : 560, top = 26, rowH = 40, H = top + rows.length * rowH + 40;
  const x0 = narrow ? 92 : 120, x1 = W - 16;
  const lo = metric === "mean_topk" ? 0.5 : 0.4;
  const xs = (x: number) => x0 + ((x - lo) / (1 - lo)) * (x1 - x0);
  const cmp = P.contentOnlyComparison;
  const mis = P.misaligned;

  return (
    <section className="section" id="catch" aria-labelledby="catch-title">
      <div className="wrap">
        <div className="section-head">
          <h2 id="catch-title">The catch: a citer that never looks at the model scores just as well</h2>
          <p>
            After seeing the results, we built a simple rule that cites the records whose content supports the answer, as our own
            design or rubric judges it. It never sees the model&rsquo;s behavior. Then we scored it exactly like the model&rsquo;s citations.
          </p>
        </div>

        <div className="catch-grid">
          <figure style={{ margin: 0 }}>
            <div className="controls-row">
              <div className="seg" role="radiogroup" aria-label="Citation score"
                onKeyDown={(e) => radioKeys(e, METRICS.map((m) => m.key), metric, setMetric)}>
                {METRICS.map((m) => (
                  <button key={m.key} role="radio" aria-checked={metric === m.key} tabIndex={metric === m.key ? 0 : -1} onClick={() => setMetric(m.key)}>{m.label}</button>
                ))}
              </div>
            </div>
            <svg className="dumbbell" viewBox={`0 0 ${W} ${H}`} role="img"
              aria-label={`${METRICS.find((m) => m.key === metric)!.label}, model versus content-only citer: `
                + rows.map((r) => `${r.name} ${r.model.toFixed(2)} versus ${r.content.toFixed(2)}`).join("; ") + "."}>
              {[lo, 0.5, 0.75, 1].filter((t, i, a) => a.indexOf(t) === i).map((t) => (
                <g key={t}>
                  <line x1={xs(t)} x2={xs(t)} y1={top - 8} y2={top + rows.length * rowH} stroke={t === 0.5 && metric !== "mean_topk" ? "var(--ink-3)" : "var(--rule)"} strokeDasharray={t === 0.5 && metric !== "mean_topk" ? "3 3" : undefined} />
                  <text x={xs(t)} y={top + rows.length * rowH + 16} fontSize="11" textAnchor="middle" fill="var(--ink-3)">{t.toFixed(2)}</text>
                </g>
              ))}
              {metric !== "mean_topk" && <text x={xs(0.5) + 5} y={top - 12} fontSize="11" fill="var(--ink-3)">chance</text>}
              {rows.map((r, i) => {
                const y = top + i * rowH + rowH / 2;
                const pooled = r.id === "pooled";
                return (
                  <g key={r.id}>
                    {pooled && <rect x={0} y={y - rowH / 2 + 3} width={W} height={rowH - 6} rx={6} fill="rgba(1,33,105,0.06)" />}
                    <text x={8} y={y + 4} fontSize="12.5" fontWeight={pooled ? 650 : 500} fill="var(--ink)">
                      {r.name}{r.inj > 0 && <tspan dx={5} fill="var(--copper)" fontSize="10">&#9670;</tspan>}
                    </text>
                    <motion.line y1={y} y2={y} initial={false} animate={{ x1: xs(r.model), x2: xs(r.content) }} transition={SPRING}
                      stroke="var(--rule-strong)" strokeWidth={3} />
                    <motion.rect y={y - 8} width={16} height={16} rx={3} initial={false} animate={{ x: xs(r.content) - 8 }} transition={SPRING}
                      fill="var(--paper)" stroke="var(--navy)" strokeWidth={2.2} />
                    <motion.circle cy={y} r={5.5} initial={false} animate={{ cx: xs(r.model) }} transition={SPRING}
                      fill="#e0b021" stroke="#9c7400" strokeWidth={1} />
                    <motion.text y={y + 4} fontSize="11.5" fill="var(--ink-2)" initial={false} textAnchor="end"
                      animate={{ x: Math.min(xs(r.model), xs(r.content)) - 14 }} transition={SPRING}
                      style={{ fontVariantNumeric: "tabular-nums" }}>{r.model.toFixed(2)}</motion.text>
                  </g>
                );
              })}
            </svg>
            <figcaption className="ctx-legend">
              <span><svg width="14" height="14" aria-hidden="true"><circle cx="7" cy="7" r="5.5" fill="#e0b021" stroke="#9c7400" /></svg>The model&rsquo;s own citations (pre-registered score; value shown)</span>
              <span><svg width="16" height="16" aria-hidden="true"><rect x="1.5" y="1.5" width="13" height="13" rx="3" fill="none" stroke="var(--navy)" strokeWidth="2" /></svg>Content-only citer (post hoc). A dot inside a square: equal scores</span>
              <span><span className="inject-mark" aria-hidden="true" />Includes citations given for an injected decision: {injRows.map((r) => `${r.name} ${r.inj} of ${r.n}`).join(", ")}.</span>
              <span>{METRICS.find((m) => m.key === metric)!.long}. Not like-for-like: the model has 5 to 8 sampled citations per scenario; the content-only citer has one fixed set.</span>
            </figcaption>
          </figure>

          <div className="claims">
            <div className="claim">
              <Tag kind="observed" />
              <p>
                The model&rsquo;s cited records usually beat same-size alternatives: <span className="num">{P.model.mean_beat_nec.toFixed(2)}</span> on
                necessity and <span className="num">{P.model.mean_beat_suf.toFixed(2)}</span> on sufficiency, where 0.5 is chance
                ({P.model.n_partial} citations, six scenarios).
              </p>
            </div>
            <div className="claim">
              <Tag kind="observed" />
              <p>
                In 3 of 18 orderings the citation prompt showed a label that was not the model&rsquo;s own answer: an injected decision.
              </p>
            </div>
            <div className="claim">
              <Tag kind="posthoc" />
              <p>
                The {mis.n_partial} citations scored in those orderings still beat chance for the shown label{mis.share_beat_nec_gt_half === 1 && mis.share_beat_suf_gt_half === 1 ? ", every one of them," : ""} though by
                less on average (<span className="num">{mis.mean_beat_nec.toFixed(2)}</span> vs <span className="num">{P.aligned.mean_beat_nec.toFixed(2)}</span> on necessity).
              </p>
            </div>
            <div className="claim">
              <Tag kind="posthoc" />
              <p>
                The content-only citer scores <span className="num">{P.contentOnly.mean_beat_nec.toFixed(2)}</span>,{" "}
                <span className="num">{P.contentOnly.mean_beat_suf.toFixed(2)}</span> and <span className="num">{P.contentOnly.mean_topk.toFixed(2)}</span>{" "}
                on the three scores: higher than the model in {cmp.higher} of {cmp.of} comparisons, tied in {cmp.tied}, lower in {cmp.lower}.
              </p>
            </div>
            <div className="claim claim-big">
              <Tag kind="interpretation" />
              <p>
                In this design, high citation scores show the model can name evidence that pushes toward a given answer. They do not
                show that it reports what drove its own answer.
              </p>
            </div>
            <div className="claim">
              <Tag kind="limitation" />
              <p>
                The content-only citer is an oracle, not a fair competitor: it uses our design or rubric, which the model never sees. In
                the realistic cases its top-k score of 1 is built in, because there the rubric agrees in sign with every measured Shapley value.
              </p>
            </div>
            <div className="claim">
              <Tag kind="limitation" />
              <p>
                One small model, one prompt format, six scenarios. Everything here is measured from the outside, by removing evidence;
                nothing looks inside the network, so none of it shows whether the citations are internally faithful or not.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
