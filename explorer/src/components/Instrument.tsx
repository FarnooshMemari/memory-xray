import { motion } from "framer-motion";
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { cell, FULL, has, LABELS, marginal, members, RECORDS, signed, toggle, v } from "../lib/model";
import { radioKeys } from "../lib/radio";
import type { View } from "../lib/state";
import type { Label, Ordering, RecordId, Scenario } from "../lib/types";
import { Gauge } from "./Gauge";
import { KeyGlyph } from "./Glyphs";

const ORD = ["1st", "2nd", "3rd", "4th"];
const SPRING = { type: "spring" as const, stiffness: 170, damping: 26, mass: 0.9 };

interface Geo {
  w: number;
  h: number;
  start: Partial<Record<RecordId, { x: number; y: number }>>;
  ring: { cx: number; cy: number; r: number } | null;
}

function offsetWithin(el: HTMLElement, root: HTMLElement) {
  let x = 0, y = 0;
  let node: HTMLElement | null = el;
  while (node && node !== root) {
    x += node.offsetLeft;
    y += node.offsetTop;
    node = node.offsetParent as HTMLElement | null;
  }
  return { x, y };
}

export function Instrument({ s, view, update, reduced, narrow, rail }: {
  s: Scenario; view: View; update: (p: Partial<View>) => void; reduced: boolean; narrow: boolean; rail: React.ReactNode;
}) {
  const o = s.orderings[view.ordering];
  const mask = view.mask;
  const effects = useMemo(() => Object.fromEntries(RECORDS.map((r) => [r, marginal(s, o, mask, r)])) as Record<RecordId, number>,
    [s, o, mask]);
  const stageRef = useRef<HTMLDivElement>(null);
  const slipRefs = useRef<Partial<Record<RecordId, HTMLButtonElement | null>>>({});
  const ringRef = useRef<HTMLDivElement>(null);
  const [geo, setGeo] = useState<Geo>({ w: 0, h: 0, start: {}, ring: null });
  const [hover, setHover] = useState<RecordId | null>(null);
  const [fullQuestion, setFullQuestion] = useState(false);
  const pulseKey = `${s.id}-${view.ordering}-${mask}`;
  // Traces glide only when the visitor changed something; pure layout changes (resize, fonts) apply at once.
  const lastChange = useRef(0);
  useEffect(() => { lastChange.current = performance.now(); }, [pulseKey]);
  // One orchestrated moment on first load: the traces draw in from the records toward the answer.
  const [intro, setIntro] = useState(!reduced);
  useEffect(() => { const t = setTimeout(() => setIntro(false), 1600); return () => clearTimeout(t); }, []);

  const measure = useCallback(() => {
    const root = stageRef.current;
    if (!root) return;
    const start: Geo["start"] = {};
    for (const r of RECORDS) {
      const el = slipRefs.current[r];
      if (!el) continue;
      const p = offsetWithin(el, root);
      start[r] = { x: p.x + el.offsetWidth, y: p.y + el.offsetHeight / 2 };
    }
    let ring: Geo["ring"] = null;
    if (ringRef.current) {
      const p = offsetWithin(ringRef.current, root);
      const size = ringRef.current.offsetWidth;
      ring = { cx: p.x + size / 2, cy: p.y + size / 2, r: size / 2 - 14 };
    }
    setGeo({ w: root.offsetWidth, h: root.offsetHeight, start, ring });
  }, []);

  useLayoutEffect(() => {
    measure();
    const ro = new ResizeObserver(measure);
    if (stageRef.current) ro.observe(stageRef.current);
    document.fonts?.ready.then(measure);
    return () => ro.disconnect();
  }, [measure, s.id, view.ordering, view.showCitations, mask, narrow, fullQuestion]);

  const c = cell(o, mask);
  const repliesHere = s.citations.filter((x) => x.ordering === o.index);
  const misaligned = s.misalignedOrderings.includes(o.index);
  const failedChecks = s.checks.recovery.filter((x) => !x.passed).length;
  const dIdx = LABELS.indexOf(s.dStar);
  const shown = members(mask).length;

  return (
    <section className="film" aria-labelledby="instrument-title">
      <h2 id="instrument-title" className="sr-only">Evidence to decision instrument for {s.name}</h2>
      {rail}
      <div className="film-head">
        <p className="film-blurb">{s.blurb}</p>
        {failedChecks > 0 && (
          <p className="film-flag">
            <b>Failed check.</b> The model did not follow this rule reliably: {failedChecks} of {s.checks.recovery.length} pre-registered
            recovery checks failed.
          </p>
        )}
        <p className={`film-question ${fullQuestion ? "" : "clamped"}`} id="film-question"><b>The question</b>{s.question}</p>
        <button className="linkbtn film-more" aria-expanded={fullQuestion} aria-controls="film-question"
          onClick={() => setFullQuestion(!fullQuestion)}>{fullQuestion ? "Show less" : "Read the full question"}</button>
        {view.showCitations && misaligned && (
          <p className="inject-banner" role="note">
            <b>Injected decision.</b> When asked what it relied on, the model was told the answer was {s.dStar}. In this ordering its
            own answer was {o.fullArgmax}, so these citations justify a label it did not choose.
          </p>
        )}
      </div>

      <div className="stage" ref={stageRef}>
        {!narrow && (
          <Traces s={s} o={o} mask={mask} geo={geo} effects={effects} hover={hover} pulseKey={pulseKey}
            reduced={reduced} glide={performance.now() - lastChange.current < 900} intro={intro} />
        )}
        <div className="slips" role="group" aria-label="Evidence records, in the order shown to the model. Press to remove or restore.">
          {o.order.map((r, i) => {
            const on = has(mask, r);
            const rec = s.records[r];
            const e = effects[r];
            const replies = repliesHere;
            return (
              <motion.button
                layout={!reduced}
                transition={SPRING}
                key={r}
                ref={(el: HTMLButtonElement | null) => { slipRefs.current[r] = el; }}
                className="slip"
                aria-pressed={on}
                data-record={r}
                onClick={() => update({ mask: toggle(mask, r) })}
                onMouseEnter={() => { setHover(r); update({ focus: r }); }}
                onMouseLeave={() => setHover(null)}
                onFocus={() => { setHover(r); update({ focus: r }); }}
                onBlur={() => setHover(null)}
                onLayoutAnimationComplete={measure}
                aria-label={`${r}, ${rec.short}. ${on ? "In the prompt" : "Removed"}. Shown ${ORD[i]} in this ordering. `
                  + `${on ? "Removing" : "Adding"} it changes the probability of ${s.dStar} by ${signed(on ? -e : e)}. `
                  + `Press to ${on ? "remove" : "restore"} it.`}
              >
                <span className="slip-pos" aria-hidden="true">
                  <span className="slip-chip">{r}</span>
                  <span className="slip-ord">{ORD[i]}</span>
                </span>
                <span className="slip-body">
                  <span className="slip-title">
                    <span className="slip-short">{rec.short}</span>
                    <span className="slip-state">{on ? "In the prompt" : "Removed"}</span>
                  </span>
                  <span className="slip-text" style={{ display: "block" }}>{rec.text}</span>
                  <span className="slip-meta">
                    <span className="slip-id">Shown as [{o.ids[r]}]</span>
                    {rec.role && <span>{rec.role}</span>}
                    {rec.rubric && (
                      <span>Rubric points to {rec.rubric.score > 0 ? "Positive" : "Negative"}: {rec.rubric.why}</span>
                    )}
                    {view.showCitations && <CiteTicks r={r} replies={replies} injected={misaligned} />}
                  </span>
                  <span className="effect-inline" aria-hidden="true">
                    <span>{on ? "Pull now" : "Pull if added"}</span>
                    <span className="effect-track">
                      <span className="effect-zero" />
                      <span className="effect-fill" style={{
                        left: `${50 + Math.min(0, e) * 50}%`,
                        width: `${Math.abs(e) * 50}%`,
                      }} />
                    </span>
                    <span className="effect-val">{signed(e)}</span>
                  </span>
                </span>
              </motion.button>
            );
          })}
        </div>

        <div className="decision">
          <Gauge s={s} cell={c} ringRef={ringRef} reduced={reduced} mask={mask} />
        </div>
      </div>

      <div className="film-foot">
        <OrderingPicker s={s} view={view} update={update} />
        <div className="actions">
          <button className="chipbtn" onClick={() => update({ mask: FULL })} disabled={mask === FULL}>Show all four</button>
          <button className="chipbtn" onClick={() => update({ mask: 0 })} disabled={mask === 0}>Remove all</button>
          <button className="chipbtn" aria-pressed={view.showCitations} onClick={() => update({ showCitations: !view.showCitations })}>
            What the model cited
          </button>
        </div>
      </div>
      <div className="film-note" aria-live="polite">
        <span className="film-key" aria-hidden="true">
          <span><KeyGlyph kind="raise" />raises P({s.dStar})</span>
          <span><KeyGlyph kind="lower" />lowers it</span>
          <span><KeyGlyph kind="zero" />no pull</span>
          {members(mask).length < 4 && <span><KeyGlyph kind="added" />removed: if added back</span>}
          {view.showCitations && <span><KeyGlyph kind="marker" />cited by the model</span>}
          {view.showCitations && misaligned && <span><span className="inject-mark" />given for an injected decision</span>}
        </span>
        <StateLine s={s} o={o} mask={mask} shown={shown} p={c.p[dIdx]} answer={c.argmax} />
        {view.showCitations && (
          <span className="cite-note">
            {" "}Squares show the {repliesHere.length} citation replies in this ordering (gold: the record was cited;
            hatched: the reply could not be parsed). They were collected with all four records shown
            {misaligned ? <>, for an injected decision (see the note above)</> : null}.
          </span>
        )}
      </div>
    </section>
  );
}

function StateLine({ s, o, mask, shown, p, answer }: { s: Scenario; o: Ordering; mask: number; shown: number; p: number; answer: Label }) {
  const rule = cell(o, mask).rule;
  return (
    <span>
      {shown === 0 ? "No records shown" : shown === 4 ? "All four records shown" : `${shown} of 4 records shown`},
      ordering {o.index}: the model answers <b className="ans">{answer}</b>; P({s.dStar}) = <span className="num">{p.toFixed(2)}</span>.
      {" "}The {s.kind === "control" ? "designed rule" : "rubric"} gives {rule} for these records.
      {" "}Pull: how much P({s.dStar}) drops when a record is removed, or rises when a removed one is added back, in the saved results.
    </span>
  );
}

function CiteTicks({ r, replies, injected }: { r: RecordId; replies: Scenario["citations"]; injected: boolean }) {
  const parsed = replies.filter((x) => x.status !== "unparseable");
  const n = parsed.filter((x) => x.cited?.includes(r)).length;
  const what = `Cited in ${n} of ${parsed.length} parsed replies in this ordering${injected ? ", given for an injected decision" : ""}`;
  return (
    <span className={`cite-ticks ${injected ? "is-injected" : ""}`} title={what}>
      {injected && <span className="inject-mark" aria-hidden="true" />}
      {replies.map((x, i) => (
        <span key={i} className={`cite-tick ${x.status === "unparseable" ? "x" : x.cited?.includes(r) ? "on" : ""}`} />
      ))}
      <span className="sr-only">{what}</span>
    </span>
  );
}

function OrderingPicker({ s, view, update }: { s: Scenario; view: View; update: (p: Partial<View>) => void }) {
  return (
    <div className="orderings" role="radiogroup" aria-label="Order in which the records were shown"
      onKeyDown={(e) => radioKeys(e, s.orderings.map((o) => o.index), view.ordering, (i) => update({ ordering: i }))}>
      <span className="orderings-label">Same records, three fixed orders. P({s.dStar}) for the records shown above, in each order:</span>
      {s.orderings.map((o) => (
        <button key={o.index} role="radio" aria-checked={view.ordering === o.index} tabIndex={view.ordering === o.index ? 0 : -1} className="ord"
          onClick={() => update({ ordering: o.index })}>
          <span className="ord-name">Ordering {o.index}</span>
          <span className="ord-seq">
            <span className="sr-only">shown in the order </span>
            {o.order.map((r) => <span key={r} className={has(view.mask, r) ? "" : "off"}>{r}</span>)}
          </span>
          <span className="ord-p">{v(s, o, view.mask).toFixed(2)}<small>{cell(o, view.mask).argmax}</small></span>
          {view.mask === FULL && o.fullArgmax !== s.dStar && (
            <span className="ord-mismatch">Answer here differs from d*</span>
          )}
        </button>
      ))}
    </div>
  );
}

/* ---------------- traces ---------------- */

function Traces({ s, o, mask, geo, effects, hover, pulseKey, reduced, glide, intro }: {
  s: Scenario; o: Ordering; mask: number; geo: Geo; effects: Record<RecordId, number>; hover: RecordId | null;
  pulseKey: string; reduced: boolean; glide: boolean; intro: boolean;
}) {
  if (!geo.ring || !geo.w) return <svg className="stage-svg" aria-hidden="true" />;
  const T = reduced || !glide ? { duration: 0 } : SPRING;
  const { cx, cy, r } = geo.ring;
  const sorted = [...o.order];
  return (
    <svg className="stage-svg" width={geo.w} height={geo.h} aria-hidden="true">
      <defs>
        <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="3" />
        </filter>
      </defs>
      {sorted.map((rec, i) => {
        const st = geo.start[rec];
        if (!st) return null;
        const on = has(mask, rec);
        const e = effects[rec];
        const pull = e; // > 0: its presence raises P(d*) (for a removed record: adding it would)
        const mag = Math.abs(pull);
        const theta = Math.PI - (i - 1.5) * 0.26;
        const ex = cx + (r + 18) * Math.cos(theta);
        const ey = cy + (r + 18) * Math.sin(theta);
        const sx = st.x + 70;
        const sy = st.y;
        const dx = ex - sx;
        const zero = mag < 0.005; // rounds to 0.00, the value its label shows
        const width = zero ? 1 : 1.5 + 20 * mag;
        // terminal: arrowhead (presence raises P(d*)) or bar (presence lowers it), sized with the trace
        const head = 7 + width * 0.55;
        const tipX = ex, tipY = ey;
        const baseX = tipX - head * Math.cos(theta + Math.PI), baseY = tipY - head * Math.sin(theta + Math.PI);
        const lineEndX = pull >= 0 ? baseX : tipX - 3 * Math.cos(theta + Math.PI);
        const lineEndY = pull >= 0 ? baseY : tipY - 3 * Math.sin(theta + Math.PI);
        const d = `M${sx},${sy} C${sx + dx * 0.55},${sy} ${lineEndX - dx * 0.4},${lineEndY} ${lineEndX},${lineEndY}`;
        const nx = -Math.sin(theta + Math.PI), ny = Math.cos(theta + Math.PI); // normal to the incoming direction
        const hw = 3.5 + width * 0.6;
        const terminal = pull >= 0
          ? `M${tipX},${tipY} L${baseX + nx * hw},${baseY + ny * hw} L${baseX - nx * hw},${baseY - ny * hw} Z`
          : `M${tipX + nx * hw},${tipY + ny * hw} L${tipX - nx * hw},${tipY - ny * hw}`;
        const dim = (hover && hover !== rec) || !on;
        const opacity = zero ? 0.3 : on ? (dim ? 0.28 : 0.92) : 0.38;
        return (
          <g key={rec}>
            {!zero && on && !dim && (
              <motion.path d={d} initial={false} animate={{ d, strokeWidth: width + 8 }} transition={T}
                fill="none" stroke="var(--trace)" strokeOpacity={0.12} filter="url(#glow)" />
            )}
            {/* remounted after the draw-in: the pathLength used there would otherwise rescale the dash patterns below */}
            <motion.path key={intro ? "intro" : "live"}
              initial={intro && on && !zero ? { pathLength: 0, d, strokeWidth: width, opacity } : false}
              animate={intro && on && !zero ? { pathLength: 1, d, strokeWidth: width, opacity } : { d, strokeWidth: width, opacity }}
              transition={intro && on && !zero ? { pathLength: { duration: 1.1, ease: [0.3, 0, 0.2, 1], delay: 0.25 + i * 0.08 }, default: T } : T}
              fill="none" stroke="var(--trace)" strokeLinecap={on && !zero ? "round" : "butt"}
              // removed records: dashes scale with the trace so the gaps stay visible on thick traces
              strokeDasharray={on && !zero ? undefined : zero ? "2 5" : `${Math.max(6, width * 0.8).toFixed(1)} ${Math.max(5, width * 0.5).toFixed(1)}`}
              data-record={rec}
              data-effect={pull}
            />
            {!zero && (
              <motion.path initial={false} animate={{ d: terminal, opacity }} transition={T}
                fill={pull >= 0 ? "var(--trace)" : "none"} stroke="var(--trace)" strokeWidth={pull >= 0 ? 0 : 4} strokeLinecap="round" />
            )}
            {!reduced && on && !zero && (
              <motion.path key={pulseKey} d={d} fill="none" stroke="#ffffff" strokeWidth={Math.min(width, 6)} strokeLinecap="round"
                pathLength={1} strokeDasharray="0.06 1"
                initial={{ strokeDashoffset: 0.06, opacity: 0.9 }} animate={{ strokeDashoffset: -1, opacity: 0 }}
                transition={{ duration: 1.1, ease: [0.4, 0, 0.2, 1], delay: 0.15 + i * 0.05 }} />
            )}
            <motion.text className={`trace-label ${on && !zero ? "" : "dim"}`} initial={false}
              animate={{ x: st.x + 14, y: sy - 3 }} transition={T}>
              {signed(e)}
            </motion.text>
            <motion.text className="trace-caption" initial={false}
              animate={{ x: st.x + 14, y: sy + 12 }} transition={T}>
              {on ? "pull now" : "if added"}
            </motion.text>
          </g>
        );
      })}
      <text className="trace-caption" x={cx} y={cy - r - 24} textAnchor="middle">pull on P({s.dStar})</text>
    </svg>
  );
}
