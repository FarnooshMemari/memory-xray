import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useMemo, useRef, useState } from "react";
import { bit, cell, DATA, FULL, has, scenarioById, signed, v } from "../lib/model";
import { useMediaQuery, type View } from "../lib/state";

interface Step { title: string; body: string; view: Partial<View>; scrollTo: string }

/** Tour steps. All numbers are looked up in the saved data, never typed in. */
function buildSteps(narrow: boolean): Step[] {
  const red = scenarioById("s_redundant");
  const ro = red.orderings[0];
  const noA = FULL & ~bit("E1");
  const noBoth = FULL & ~bit("E1") & ~bit("E3");
  const con = scenarioById("s_conflict");
  const c0 = con.orderings[0], c2 = con.orderings[2];
  let both = 0, later = 0;
  for (const o of con.orderings) {
    for (let m = 0; m < 16; m++) {
      if (!has(m, "E1") || !has(m, "E2")) continue;
      both++;
      const e1Later = o.order.indexOf("E1") > o.order.indexOf("E2");
      if (cell(o, m).argmax === (e1Later ? "Positive" : "Negative")) later++;
    }
  }
  const rep0 = con.citations.filter((c) => c.ordering === 0 && c.status !== "unparseable");
  const bothCited = rep0.filter((c) => c.cited?.includes("E1") && c.cited?.includes("E2")).length;
  const P = DATA.pooled;
  const p = (x: number) => x.toFixed(2);

  return [
    {
      title: "Four records in, one answer",
      body: `The model reads four records about Economy L and answers ${cell(ro, FULL).argmax}, with probability ${p(v(red, ro, FULL))}. `
        + (narrow ? "The bar under each record shows its pull on that probability." : "Each luminous trace is one record's pull on that probability."),
      view: { scenario: "s_redundant", ordering: 0, mask: FULL, showCitations: false }, scrollTo: "instrument",
    },
    {
      title: "Remove one official report",
      body: `Taking out the press release moves P(${red.dStar}) from ${p(v(red, ro, FULL))} to ${p(v(red, ro, noA))}. `
        + "Almost nothing changes: the official gazette reports the same rate hike.",
      view: { scenario: "s_redundant", ordering: 0, mask: noA }, scrollTo: "instrument",
    },
    {
      title: "Remove the second report too",
      body: `Now the answer becomes ${cell(ro, noBoth).argmax}: P(${red.dStar}) falls to ${p(v(red, ro, noBoth))}. Either report was enough on its own.`,
      view: { scenario: "s_redundant", ordering: 0, mask: noBoth }, scrollTo: "instrument",
    },
    {
      title: "So which report mattered?",
      body: `With both present, removing one changes P(${red.dStar}) by only ${signed(ro.loo.E1)}. That is all leave-one-out can see. `
        + `Averaged over every combination, Shapley credits the press release with ${signed(ro.shapley.E1)}.`,
      view: { scenario: "s_redundant", ordering: 0, mask: FULL, focus: "E1" }, scrollTo: "combinations",
    },
    {
      title: "Order can decide a conflict",
      body: `Here the rule says the rate cut wins over the inflation report, so the answer should be Positive. With the rate cut shown first, `
        + `the model answers ${cell(c0, FULL).argmax}.`,
      view: { scenario: "s_conflict", ordering: 0, mask: FULL, showCitations: false }, scrollTo: "instrument",
    },
    {
      title: "Show the rate cut last",
      body: `Same records, rate cut last: the answer is ${cell(c2, FULL).argmax}. In ${later} of ${both} prompts with both records, the later one decided. `
        + "But only one ordering puts the rate cut last, and its position and neighbors change with it: a pattern, not a proven rule.",
      view: { scenario: "s_conflict", ordering: 2, mask: FULL }, scrollTo: "instrument",
    },
    {
      title: "Now ask the model what it used",
      body: `In ordering 0, ${bothCited} of ${rep0.length} parsed replies cite both the rate cut and the inflation report. The prompt asked it to justify `
        + `${con.dStar}, which was not its own answer in this ordering (${c0.fullArgmax}).`,
      view: { scenario: "s_conflict", ordering: 0, mask: FULL, showCitations: true }, scrollTo: "instrument",
    },
    {
      title: "Plausible is not the same as faithful",
      body: `Across all six scenarios, the model's citations beat chance (${p(P.model.mean_beat_nec)} on necessity; ${P.misaligned.n_partial} of the `
        + `${P.model.n_partial} were for an injected decision). A rule that only reads the content, using our design or rubric, scores `
        + `${p(P.contentOnly.mean_beat_nec)}. Citations that look right are not proof of what drove the answer.`,
      view: { showCitations: false }, scrollTo: "catch",
    },
  ];
}

export function Tour({ onClose, update, reduced }: { onClose: () => void; update: (p: Partial<View>) => void; reduced: boolean }) {
  const narrow = useMediaQuery("(max-width: 860px)");
  const steps = useMemo(() => buildSteps(narrow), [narrow]);
  const [i, setI] = useState(0);
  const step = steps[i];

  useEffect(() => {
    update(step.view);
    // on phones the instrument's answer panel is pinned at the top, so bring the records themselves into view
    const el = narrow && step.scrollTo === "instrument"
      ? document.querySelector<HTMLElement>("#instrument .slips")
      : document.getElementById(step.scrollTo);
    if (el) {
      const pinned = narrow && step.scrollTo === "instrument" ? (document.querySelector<HTMLElement>("#instrument .decision")?.offsetHeight ?? 0) : 0;
      const y = el.getBoundingClientRect().top + window.scrollY - 70 - pinned;
      window.scrollTo({ top: y, behavior: reduced ? "auto" : "smooth" });
    }
  }, [i, step, update, reduced, narrow]);

  // return focus to whatever opened the tour (the tour button) when it closes; captured during the
  // first render, before "Next" takes focus
  const opener = useRef(typeof document !== "undefined" ? (document.activeElement as HTMLElement | null) : null);
  useEffect(() => {
    const el = opener.current;
    return () => { el?.focus?.({ preventScroll: true }); };
  }, []);

  const panel = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      // arrow keys page the tour only when focus is in the tour, so other controls keep their own arrow keys
      const t = e.target as HTMLElement | null;
      if (t && t !== document.body && !panel.current?.contains(t)) return;
      if (e.key === "ArrowRight") setI((x) => Math.min(steps.length - 1, x + 1));
      if (e.key === "ArrowLeft") setI((x) => Math.max(0, x - 1));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose, steps.length]);

  return (
    <div className="tour" role="dialog" aria-modal="false" aria-labelledby="tour-title" ref={panel}>
      <p className="sr-only" aria-live="polite">Step {i + 1} of {steps.length}. {step.title}. {step.body}</p>
      <div className="tour-step">
        <span>Step {i + 1} of {steps.length}</span>
        <span className="tour-dots" aria-hidden="true">{steps.map((_, k) => <i key={k} className={k <= i ? "on" : ""} />)}</span>
      </div>
      <AnimatePresence mode="wait" initial={false}>
        <motion.div key={i} initial={reduced ? false : { opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }}
          exit={reduced ? undefined : { opacity: 0, x: -12 }} transition={{ duration: 0.22 }}>
          <h3 id="tour-title">{step.title}</h3>
          <p>{step.body}</p>
        </motion.div>
      </AnimatePresence>
      <div className="tour-nav">
        <button className="linkbtn" onClick={onClose}>Close tour</button>
        <span style={{ display: "flex", gap: 8 }}>
          <button className="btn btn-ghost" onClick={() => setI(i - 1)} disabled={i === 0}>Back</button>
          {i < steps.length - 1
            ? <button className="btn" onClick={() => setI(i + 1)} autoFocus>Next</button>
            : <button className="btn" onClick={onClose}>Explore on your own</button>}
        </span>
      </div>
    </div>
  );
}
