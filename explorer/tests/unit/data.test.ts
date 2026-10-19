import { describe, expect, it } from "vitest";
import { contexts, DATA, FULL, LABELS, marginal, members, RECORDS, shapleyFromLattice, shapleyWeight, v } from "../../src/lib/model";

// These tests check the explorer's data and math against the saved v0.2 values it ships with.
// (scripts/verify_data.py checks the same file against the raw run files and the independent reanalysis.)

describe("explorer data", () => {
  it("has six scenarios, three orderings each, and all 16 subsets per ordering", () => {
    expect(DATA.scenarios.map((s) => s.id)).toEqual(["s_single", "s_redundant", "s_conflict", "macro_a", "macro_b", "macro_c"]);
    for (const s of DATA.scenarios) {
      expect(s.orderings).toHaveLength(3);
      for (const o of s.orderings) {
        expect(Object.keys(o.subsets).sort((a, b) => +a - +b)).toEqual([...Array(16).keys()].map(String));
        expect([...o.order].sort()).toEqual(RECORDS);
      }
    }
  });

  it("stores probabilities that sum to 1 and argmax labels that match them", () => {
    for (const s of DATA.scenarios) for (const o of s.orderings) for (const c of Object.values(o.subsets)) {
      expect(Math.abs(c.p[0] + c.p[1] + c.p[2] - 1)).toBeLessThan(1e-9);
      expect(c.argmax).toBe(LABELS[c.p.indexOf(Math.max(...c.p))]);
    }
  });

  it("recomputes every saved Shapley value from the 16 saved subset probabilities", () => {
    for (const s of DATA.scenarios) for (const o of s.orderings) for (const r of RECORDS) {
      expect(Math.abs(shapleyFromLattice(s, o, r) - o.shapley[r])).toBeLessThan(1e-12);
    }
  });

  it("recovers every saved leave-one-out value as the marginal effect with all four records shown", () => {
    for (const s of DATA.scenarios) for (const o of s.orderings) for (const r of RECORDS) {
      expect(Math.abs(marginal(s, o, FULL, r) - o.loo[r])).toBeLessThan(1e-12);
    }
  });

  it("uses Shapley weights that sum to 1 over the 8 contexts of a record", () => {
    for (const r of RECORDS) {
      const ctx = contexts(r);
      expect(new Set(ctx).size).toBe(8);
      expect(ctx.every((m) => !members(m).includes(r))).toBe(true);
      expect(ctx.reduce((a, m) => a + shapleyWeight(members(m).length), 0)).toBeCloseTo(1, 12);
    }
  });

  it("matches the decision d* to the ordering-averaged full-evidence distribution", () => {
    for (const s of DATA.scenarios) {
      const mean = LABELS.map((_, i) => s.orderings.reduce((a, o) => a + o.subsets["15"].p[i], 0) / 3);
      expect(LABELS[mean.indexOf(Math.max(...mean))]).toBe(s.dStar);
      mean.forEach((m, i) => expect(Math.abs(m - s.meanFullDist[i])).toBeLessThan(1e-12));
      expect(Math.abs(v(s, s.orderings[0], FULL) - s.orderings[0].subsets["15"].p[LABELS.indexOf(s.dStar)])).toBe(0);
    }
  });

  it("flags exactly the 3 orderings where the label shown in the citation prompt was not the model's own answer", () => {
    let misaligned = 0;
    for (const s of DATA.scenarios) {
      expect(s.citations).toHaveLength(13);
      for (const c of s.citations) {
        expect(c.ownAnswer).toBe(s.orderings[c.ordering].fullArgmax);
        expect(c.shownLabel).toBe(s.dStar);
        expect(c.aligned).toBe(c.shownLabel === c.ownAnswer);
      }
      misaligned += s.misalignedOrderings.length;
      expect(s.misalignedOrderings).toEqual(s.orderings.filter((o) => o.fullArgmax !== s.dStar).map((o) => o.index));
    }
    expect(misaligned).toBe(3);
  });

  it("carries the pooled numbers reported for the study", () => {
    const p = DATA.pooled;
    expect(p.model.n_partial).toBe(40);
    expect(p.model.mean_beat_nec.toFixed(3)).toBe("0.896");
    expect(p.model.mean_beat_suf.toFixed(3)).toBe("0.848");
    expect(p.model.mean_topk.toFixed(3)).toBe("0.883");
    expect(p.contentOnly.mean_beat_suf.toFixed(3)).toBe("0.939");
    expect([p.contentOnlyComparison.higher, p.contentOnlyComparison.tied, p.contentOnlyComparison.lower]).toEqual([10, 7, 1]);
    expect(p.sampledStatus).toEqual({ ok: 45, unparseable: 14, empty: 1 });
    expect(p.misaligned.n_partial).toBe(8);
  });
});
