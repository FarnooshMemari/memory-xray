import raw from "../data/explorer-data.json";
import type { ExplorerData, Label, Ordering, RecordId, Scenario } from "./types";

export const DATA = raw as unknown as ExplorerData;
export const LABELS: Label[] = ["Positive", "Neutral", "Negative"];
export const RECORDS: RecordId[] = ["E1", "E2", "E3", "E4"];
export const FULL = 15;

export const bit = (r: RecordId) => 1 << RECORDS.indexOf(r);
export const has = (mask: number, r: RecordId) => (mask & bit(r)) !== 0;
export const toggle = (mask: number, r: RecordId) => mask ^ bit(r);
export const members = (mask: number) => RECORDS.filter((r) => has(mask, r));
export const popcount = (mask: number) => members(mask).length;

export function scenarioById(id: string): Scenario {
  return DATA.scenarios.find((s) => s.id === id) ?? DATA.scenarios[0];
}

export function cell(o: Ordering, mask: number) {
  return o.subsets[String(mask)];
}

/** v(S) = probability of the scenario decision d* for the records in S, in one ordering (saved value). */
export function v(s: Scenario, o: Ordering, mask: number): number {
  return cell(o, mask).p[LABELS.indexOf(s.dStar)];
}

/**
 * Effect of one record in the current combination, read from the saved lattice:
 * if the record is in, the drop in P(d*) when it is taken out, i.e. v(S) - v(S without it);
 * if it is out, the change when it is put in, i.e. v(S with it) - v(S).
 * With all four records in, this is exactly the leave-one-out value.
 */
export function marginal(s: Scenario, o: Ordering, mask: number, r: RecordId): number {
  const withR = mask | bit(r);
  const withoutR = mask & ~bit(r);
  return v(s, o, withR) - v(s, o, withoutR);
}

/** Shapley weight of a context (the other records present) of a given size, for 4 players. */
export function shapleyWeight(contextSize: number): number {
  const f = [1, 1, 2, 6, 24];
  return (f[contextSize] * f[3 - contextSize]) / f[4];
}

/** The 8 contexts (subsets of the other three records) in which a record can be added. */
export function contexts(r: RecordId): number[] {
  const others = RECORDS.filter((x) => x !== r);
  const out: number[] = [];
  for (let m = 0; m < 8; m++) {
    let mask = 0;
    others.forEach((o, i) => { if (m >> i & 1) mask |= bit(o); });
    out.push(mask);
  }
  return out.sort((a, b) => popcount(a) - popcount(b) || a - b);
}

/** Shapley value recomputed from the lattice as the weighted mean of the 8 marginal effects. */
export function shapleyFromLattice(s: Scenario, o: Ordering, r: RecordId): number {
  return contexts(r).reduce((acc, ctx) => acc + shapleyWeight(popcount(ctx)) * (v(s, o, ctx | bit(r)) - v(s, o, ctx)), 0);
}

export const fmt = (x: number, d = 2) => (Math.abs(x) < 0.5 * 10 ** -d ? (0).toFixed(d) : x.toFixed(d));
export const signed = (x: number, d = 2) => {
  const t = fmt(Math.abs(x), d);
  if (Number(t) === 0) return t;
  return (x < 0 ? "−" : "+") + t;
};

export function orderingLabel(o: Ordering): string {
  return `Order ${o.index + 1}`;
}
