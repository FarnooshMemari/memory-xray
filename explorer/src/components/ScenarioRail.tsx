import { DATA, RECORDS } from "../lib/model";
import type { Scenario } from "../lib/types";

/** A record-by-record fingerprint: mean Shapley value of each record (its average pull on P(d*)). */
function Fingerprint({ s, active }: { s: Scenario; active: boolean }) {
  const w = 30, h = 22, mid = h / 2;
  return (
    <svg width={w} height={h} aria-hidden="true" className="fingerprint">
      <line x1={0} x2={w} y1={mid} y2={mid} stroke="rgba(160,185,240,0.35)" strokeWidth={1} />
      {RECORDS.map((r, i) => {
        const x = 1 + i * 7.5;
        const val = s.shapleySummary[r].mean;
        const len = Math.max(1, Math.abs(val) * (mid - 1));
        return (
          <rect key={r} x={x} width={5} rx={1} y={val >= 0 ? mid - len : mid} height={len}
            fill={active ? "var(--trace)" : "var(--film-ink-3)"} />
        );
      })}
    </svg>
  );
}

export function ScenarioRail({ current, onSelect }: { current: string; onSelect: (id: string) => void }) {
  const groups: [string, Scenario[]][] = [
    ["Designed controls", DATA.scenarios.filter((s) => s.kind === "control")],
    ["Realistic cases", DATA.scenarios.filter((s) => s.kind === "realistic")],
  ];
  const onKey = (e: React.KeyboardEvent, id: string) => {
    const ids = DATA.scenarios.map((s) => s.id);
    const i = ids.indexOf(id);
    let next: string | null = null;
    if (e.key === "ArrowRight" || e.key === "ArrowDown") next = ids[(i + 1) % ids.length];
    if (e.key === "ArrowLeft" || e.key === "ArrowUp") next = ids[(i + ids.length - 1) % ids.length];
    if (e.key === "Home") next = ids[0];
    if (e.key === "End") next = ids[ids.length - 1];
    if (next) {
      e.preventDefault();
      onSelect(next);
      requestAnimationFrame(() => (document.querySelector(`.tab[data-scenario="${next}"]`) as HTMLElement | null)?.focus());
    }
  };
  return (
    <div className="tabs" role="radiogroup" aria-label="Scenario">
      {groups.map(([head, list]) => (
        <div className="tab-group" key={head} role="presentation">
          <span className="tab-group-head" aria-hidden="true">{head}</span>
          {list.map((s) => {
            const active = s.id === current;
            const failed = s.checks.recovery.some((c) => !c.passed);
            return (
              <button key={s.id} role="radio" aria-checked={active} tabIndex={active ? 0 : -1} className="tab"
                onClick={() => onSelect(s.id)} onKeyDown={(e) => onKey(e, s.id)} data-scenario={s.id}
                aria-label={`${s.name}: ${s.blurb}${s.kind === "control" ? (failed ? " Recovery checks failed." : " Recovery checks passed.") : ""}`}>
                <Fingerprint s={s} active={active} />
                <span className="tab-name">{s.name}</span>
                {failed && <span className="tab-flag" title="This control failed its pre-registered recovery checks">failed check</span>}
              </button>
            );
          })}
        </div>
      ))}
    </div>
  );
}
