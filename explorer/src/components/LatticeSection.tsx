import { motion } from "framer-motion";
import { useMemo } from "react";
import { bit, cell, contexts, has, LABELS, members, popcount, RECORDS, shapleyWeight, signed, v } from "../lib/model";
import { radioKeys } from "../lib/radio";
import { useMediaQuery, type View } from "../lib/state";
import type { Label, RecordId, Scenario } from "../lib/types";

export const PAPER_COLOR: Record<Label, string> = { Positive: "var(--royal)", Neutral: "var(--neutral)", Negative: "var(--copper)" };
const SPRING = { type: "spring" as const, stiffness: 170, damping: 26 };

/**
 * Node positions of the 16-subset lattice, grouped by number of records shown (0 to 4):
 * columns left to right on wide screens, rows top to bottom on narrow ones (so the text stays legible).
 */
function layout(narrow: boolean) {
  const W = narrow ? 360 : 600, H = narrow ? 540 : 470;
  const levels: number[][] = [[], [], [], [], []];
  for (let m = 0; m < 16; m++) levels[popcount(m)].push(m);
  const pos: Record<number, { x: number; y: number }> = {};
  const level: { x: number; y: number; anchor: "middle" | "start" }[] = [];
  levels.forEach((lv, k) => {
    if (narrow) {
      const y = 62 + k * 112;
      level.push({ x: 2, y: y - 34, anchor: "start" });
      lv.forEach((m, i) => { pos[m] = { x: W / 2 + (i - (lv.length - 1) / 2) * 58, y }; });
    } else {
      const x = 44 + k * ((W - 88) / 4);
      level.push({ x, y: 18, anchor: "middle" });
      lv.forEach((m, i) => { pos[m] = { x, y: H / 2 + (i - (lv.length - 1) / 2) * 70 }; });
    }
  });
  return { W, H, pos, level };
}

export function LatticeSection({ s, view, update, reduced }: {
  s: Scenario; view: View; update: (p: Partial<View>) => void; reduced: boolean;
}) {
  const o = s.orderings[view.ordering];
  const biggest = useMemo(() => RECORDS.reduce((a, r) => (Math.abs(o.shapley[r]) > Math.abs(o.shapley[a]) ? r : a), "E1" as RecordId), [o]);
  const focus: RecordId = view.focus ?? biggest;
  const narrow = useMediaQuery("(max-width: 560px)");
  const { W, H, pos, level } = layout(narrow);
  const dIdx = LABELS.indexOf(s.dStar);

  const edges: { from: number; to: number; r: RecordId }[] = [];
  for (let m = 0; m < 16; m++) for (const r of RECORDS) if (!has(m, r)) edges.push({ from: m, to: m | bit(r), r });

  return (
    <section className="section" id="combinations" aria-labelledby="combinations-title">
      <div className="wrap">
        <div className="section-head">
          <h2 id="combinations-title">Every combination, and why removing one record at a time can mislead</h2>
          <p>
            Each dot is one of the 16 ways to show the records. A record&rsquo;s Shapley value averages its pull over all eight
            combinations of the other records. Leave-one-out looks only at the one where all others are present.
          </p>
        </div>

        <div className="controls-row">
          <div className="chips" role="radiogroup" aria-label="Record to examine"
            onKeyDown={(e) => radioKeys(e, [...RECORDS], focus, (r) => update({ focus: r }))}>
            {RECORDS.map((r) => (
              <button key={r} role="radio" aria-checked={focus === r} tabIndex={focus === r ? 0 : -1} className="chip" onClick={() => update({ focus: r })}>
                <b>{r}</b>{s.records[r].short}
              </button>
            ))}
          </div>
          <span>{s.name}, ordering {o.index} (change both in the instrument)</span>
        </div>

        <div className="lattice-grid">
          <figure style={{ margin: 0 }}>
            <svg className="lattice-svg" viewBox={`0 0 ${W} ${H}`} role="group" aria-label="Lattice of the 16 record combinations">
              <defs>
                <marker id="l-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto">
                  <path d="M0,0 L10,5 L0,10 z" fill="var(--navy)" />
                </marker>
                <marker id="l-tbar" viewBox="0 0 4 14" refX="2" refY="7" markerWidth="4" markerHeight="13" markerUnits="userSpaceOnUse" orient="auto">
                  <rect width="4" height="14" rx="1" fill="var(--navy)" />
                </marker>
              </defs>
              {level.map((l, k) => (
                <text key={k} x={l.x} y={l.y} textAnchor={l.anchor} fontSize="12" fill="var(--ink-3)"
                  stroke="var(--paper)" strokeWidth={4} paintOrder="stroke">
                  {k === 0 ? "no records" : k === 1 ? "1 record" : `${k} records`}
                </text>
              ))}
              {edges.map(({ from, to, r }) => {
                const a = pos[from], b = pos[to];
                const isF = r === focus;
                const d = v(s, o, to) - v(s, o, from);
                const mag = Math.abs(d);
                const ux = (b.x - a.x), uy = (b.y - a.y), L = Math.hypot(ux, uy);
                // narrow layout runs top to bottom: start below the membership squares so thick edges do not cover them
                const s0 = narrow ? 34 : 21;
                const x1 = a.x + (ux / L) * s0, y1 = a.y + (uy / L) * s0, x2 = b.x - (ux / L) * 23, y2 = b.y - (uy / L) * 23;
                return (
                  <motion.line key={`${from}-${to}`} x1={x1} y1={y1} x2={x2} y2={y2}
                    initial={false}
                    animate={{ strokeWidth: isF ? 1 + 9 * mag : 1, opacity: isF ? (mag < 0.005 ? 0.45 : 0.9) : 0.18 }}
                    transition={reduced ? { duration: 0 } : SPRING}
                    stroke={isF ? "var(--navy)" : "var(--ink-3)"} strokeLinecap="round"
                    strokeDasharray={isF && mag < 0.005 ? "3 4" : undefined}
                    markerEnd={isF && mag >= 0.005 ? (d >= 0 ? "url(#l-arrow)" : "url(#l-tbar)") : undefined} />
                );
              })}
              {Object.entries(pos).map(([mk, p]) => {
                const m = Number(mk);
                const c = cell(o, m);
                const current = m === view.mask;
                const pd = c.p[dIdx];
                return (
                  <g key={m} className="lattice-node" transform={`translate(${p.x},${p.y})`} role="button" tabIndex={0}
                    aria-label={`${members(m).length ? members(m).join(", ") : "No records"}: answer ${c.argmax}, P(${s.dStar}) ${pd.toFixed(2)}. Show in the instrument.`}
                    aria-pressed={current}
                    onClick={() => update({ mask: m })}
                    onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); update({ mask: m }); } }}
                    >
                    <circle r={24} fill="transparent" />
                    {current && <circle r={22.5} fill="none" stroke="var(--ink)" strokeWidth={2} />}
                    <circle r={17} fill={PAPER_COLOR[c.argmax]} stroke="var(--paper)" strokeWidth={2} />
                    <text y={4} textAnchor="middle" fontSize="11" fontWeight={600} fill="#fff" style={{ fontVariantNumeric: "tabular-nums" }}>
                      {pd.toFixed(2).replace(/^0/, "")}
                    </text>
                    <g transform="translate(-13,24)">
                      {RECORDS.map((r, i) => (
                        <rect key={r} x={i * 7} y={0} width={5} height={5} rx={1}
                          fill={has(m, r) ? (r === focus ? "var(--navy)" : "var(--ink-2)") : "none"}
                          stroke={r === focus ? "var(--navy)" : "var(--ink-3)"} strokeWidth={0.8} />
                      ))}
                    </g>
                  </g>
                );
              })}
            </svg>
            <figcaption className="lattice-caption">
              Dot color: the model&rsquo;s answer for that combination. Number inside: P({s.dStar}). The four squares under each dot
              show which of E1 to E4 are in. Ringed: the combination shown in the instrument; select any dot to load it.
            </figcaption>
            <div className="ctx-legend">
              {LABELS.map((l) => (
                <span key={l}><svg width="12" height="12" aria-hidden="true"><circle cx="6" cy="6" r="5.5" fill={PAPER_COLOR[l]} /></svg>{l}</span>
              ))}
              <span>Highlighted links: adding {focus}, sized by how much it moves P({s.dStar})</span>
            </div>
          </figure>

          <ContextChart s={s} oIndex={o.index} r={focus} reduced={reduced} narrow={narrow} />
        </div>
      </div>
    </section>
  );
}

function ContextChart({ s, oIndex, r, reduced, narrow }: { s: Scenario; oIndex: number; r: RecordId; reduced: boolean; narrow: boolean }) {
  const o = s.orderings[oIndex];
  const ctx = contexts(r);
  const rows = ctx.map((m) => ({ m, d: v(s, o, m | bit(r)) - v(s, o, m), w: shapleyWeight(popcount(m)) }));
  const shap = o.shapley[r];
  const loo = o.loo[r];
  const W = narrow ? 350 : 540, rowH = 34, top = 18, H = top + rows.length * rowH + 50;
  const x0 = narrow ? 110 : 170, x1 = W - (narrow ? 42 : 48);
  const xs = (d: number) => x0 + ((d + 1) / 2) * (x1 - x0);
  const name = (m: number) => (members(m).length === 0 ? "alone" : members(m).length === 3 ? (narrow ? "with all three" : "with all three others") : `with ${members(m).join(", ")}`);

  return (
    <figure style={{ margin: 0 }}>
      <p className="ctx-title">Adding {r} ({s.records[r].short}) changes P({s.dStar}) by</p>
      <svg className="ctx-chart" viewBox={`0 0 ${W} ${H}`} role="img"
        aria-label={`Pull of ${r} on P(${s.dStar}) in each of its 8 contexts. Shapley ${signed(shap)}, leave-one-out ${signed(loo)}.`}>
        {[-1, -0.5, 0, 0.5, 1].map((t) => (
          <g key={t}>
            <line x1={xs(t)} x2={xs(t)} y1={top - 6} y2={top + rows.length * rowH} stroke={t === 0 ? "var(--rule-strong)" : "var(--rule)"} strokeWidth={1} />
            <text x={xs(t)} y={top + rows.length * rowH + 16} fontSize="11" textAnchor="middle" fill="var(--ink-3)">{t === 0 ? "0" : signed(t, 1)}</text>
          </g>
        ))}
        {rows.map((row, i) => {
          const y = top + i * rowH + rowH / 2;
          const isLoo = popcount(row.m) === 3;
          return (
            <g key={row.m}>
              {isLoo && <rect x={0} y={y - rowH / 2 + 2} width={W} height={rowH - 4} rx={6} fill="rgba(1,33,105,0.06)" />}
              <text x={8} y={y + 4} fontSize={narrow ? 12 : 12.5} fill={isLoo ? "var(--ink)" : "var(--ink-2)"} fontWeight={isLoo ? 600 : 400}>{name(row.m)}</text>
              <text x={x0 - 12} y={y + 4} fontSize="11" fill="var(--ink-3)" textAnchor="end">{row.w === 0.25 ? "1/4" : "1/12"}</text>
              <motion.line y1={y} y2={y} x1={xs(0)} initial={false} animate={{ x2: xs(row.d) }} transition={reduced ? { duration: 0 } : SPRING}
                stroke="var(--navy)" strokeWidth={2} />
              <motion.circle cy={y} initial={false} animate={{ cx: xs(row.d) }} transition={reduced ? { duration: 0 } : SPRING}
                r={row.w === 0.25 ? 7 : 4.5} fill="var(--navy)" stroke="var(--paper)" strokeWidth={2} />
              <motion.text y={y - 9} fontSize="11" fill="var(--ink-2)" initial={false} textAnchor={row.d >= 0 ? "start" : "end"}
                animate={{ x: xs(row.d) + (row.d >= 0 ? 8 : -8) }} transition={reduced ? { duration: 0 } : SPRING}
                style={{ fontVariantNumeric: "tabular-nums" }}>{signed(row.d)}</motion.text>
            </g>
          );
        })}
        <motion.g initial={false} animate={{ x: xs(shap) }} transition={reduced ? { duration: 0 } : SPRING}>
          <line y1={top - 10} y2={top + rows.length * rowH + 2} stroke="var(--ink)" strokeWidth={1.5} strokeDasharray="4 3" />
          <text y={H - 10} fontSize="12" fontWeight={600} fill="var(--ink)" textAnchor="middle">Shapley {signed(shap)}</text>
        </motion.g>
      </svg>
      <figcaption className="ctx-legend">
        <span>Each row: one combination of the other records. Weight (left) is that row&rsquo;s share of the Shapley average; large dots weigh 1/4, small ones 1/12.</span>
      </figcaption>
      <p className="callout">
        Leave-one-out sees only the shaded row: <b className="num">{signed(loo)}</b>. Shapley averages all eight:
        <b className="num"> {signed(shap)}</b>.
        {Math.abs(loo) < 0.1 && Math.abs(shap) > 0.2
          ? " Here the record moves the answer in some combinations but hardly in the one leave-one-out checks, so leave-one-out understates its average pull."
          : Math.abs(shap - loo) > 0.15
            ? " The two differ because this record's pull depends on which other records are present."
            : ""}
      </p>
    </figure>
  );
}
