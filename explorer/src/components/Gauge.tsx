import { AnimatePresence, motion } from "framer-motion";
import { arc as d3arc } from "d3-shape";
import type { RefObject } from "react";
import { LABELS } from "../lib/model";
import { useTween } from "../lib/tween";
import type { Label, Scenario, SubsetCell } from "../lib/types";

export const FILM_COLOR: Record<Label, string> = { Positive: "var(--pos-film)", Neutral: "var(--neu-film)", Negative: "var(--neg-film)" };
const SPRING = { type: "spring" as const, stiffness: 170, damping: 26, mass: 0.9 };

export function Gauge({ s, cell, ringRef, reduced, mask }: {
  s: Scenario; cell: SubsetCell; ringRef: RefObject<HTMLDivElement | null>; reduced: boolean; mask: number;
}) {
  const p = useTween(cell.p, 900, reduced, true);
  const size = 208;
  const R = size / 2 - 14;
  const gap = 0.035;
  const arcs: { label: Label; d: string }[] = [];
  let a0 = 0;
  const mk = d3arc<{ a: number; b: number }>().innerRadius(R - 15).outerRadius(R).cornerRadius(3)
    .startAngle((x) => x.a).endAngle((x) => x.b);
  LABELS.forEach((label, i) => {
    const span = Math.max(0, p[i]) * Math.PI * 2;
    const a = a0 + (span > gap * 2 ? gap / 2 : 0);
    const b = a0 + span - (span > gap * 2 ? gap / 2 : 0);
    if (b > a) arcs.push({ label, d: mk({ a, b }) ?? "" });
    a0 += span;
  });
  const top = cell.argmax;
  const iTop = LABELS.indexOf(top);
  const dIdx = LABELS.indexOf(s.dStar);
  const ruleWord = s.kind === "control" ? "Designed rule" : "Rubric";

  return (
    <div className="gauge" data-testid="gauge" data-answer={top} data-p={cell.p.join(",")} data-mask={mask}>
      <div className="gauge-ring" ref={ringRef}>
        <svg width={size} height={size} viewBox={`${-size / 2} ${-size / 2} ${size} ${size}`} role="img"
          aria-label={`Model answer ${top}. Probabilities: ${LABELS.map((l, i) => `${l} ${cell.p[i].toFixed(2)}`).join(", ")}.`}>
          <circle r={R - 7.5} fill="none" stroke="rgba(160,185,240,0.12)" strokeWidth={15} />
          {arcs.map((x) => (
            <path key={x.label} d={x.d} fill={FILM_COLOR[x.label]} opacity={x.label === top ? 1 : 0.55} />
          ))}
          <circle r={R - 24} fill="none" stroke="rgba(160,185,240,0.18)" strokeWidth={1} />
          {/* tick at 12 o'clock: where the Positive arc starts */}
          <line x1={0} y1={-R - 6} x2={0} y2={-R + 1} stroke="rgba(233,238,248,0.6)" strokeWidth={1.5} />
        </svg>
        <div className="gauge-center">
          <AnimatePresence mode="popLayout" initial={false}>
            <motion.div key={top} className="gauge-word" style={{ color: FILM_COLOR[top] === "var(--neu-film)" ? "var(--film-ink)" : "var(--film-ink)" }}
              initial={reduced ? false : { opacity: 0, y: 8, filter: "blur(4px)" }} animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
              exit={reduced ? undefined : { opacity: 0, y: -8, filter: "blur(4px)" }} transition={{ duration: 0.35 }}>
              {top}
            </motion.div>
          </AnimatePresence>
          <div className="gauge-p">P = <strong className="num">{p[iTop].toFixed(2)}</strong></div>
        </div>
      </div>

      <div className="bars" role="list" aria-label="Label probabilities for the records shown">
        {LABELS.map((label, i) => (
          <div key={label} role="listitem" className={`bar-row ${label === top ? "is-top" : ""}`} data-label={label}>
            <span className="bar-label">
              <span>{label}</span>
              {i === dIdx && <span className="pill pill-dstar" title="The scenario decision: the answer with all four records, averaged over the three orderings">d*</span>}
              {label === cell.rule && <span className="pill pill-rule" title={`${ruleWord}'s answer for these records`}>{s.kind === "control" ? "rule" : "rubric"}</span>}
            </span>
            <span className="bar-val" data-value={cell.p[i]}>{p[i].toFixed(2)}</span>
            <span className="bar-track">
              <motion.span className="bar-fill" style={{ display: "block", background: FILM_COLOR[label], opacity: label === top ? 1 : 0.6 }}
                initial={false} animate={{ scaleX: cell.p[i] }} transition={reduced ? { duration: 0 } : SPRING} />
            </span>
          </div>
        ))}
        <p className="verdict">
          {ruleWord} for these records: <b>{cell.rule}</b>.{" "}
          {cell.rule === top ? <>The model agrees.</> : <span className="differs">The model answers {top} instead.</span>}
        </p>
      </div>
    </div>
  );
}
