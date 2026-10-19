import { RECORDS, signed } from "../lib/model";
import type { View } from "../lib/state";
import type { Citation, Scenario } from "../lib/types";
import { Tag } from "./Tag";

export function CitationsSection({ s, view, update }: { s: Scenario; view: View; update: (p: Partial<View>) => void }) {
  const parsed = s.citations.filter((c) => c.status !== "unparseable");
  const citedShare = Object.fromEntries(RECORDS.map((r) => [r, parsed.filter((c) => c.cited?.includes(r)).length])) as Record<string, number>;
  // replies from orderings where the citation prompt showed a label that was not the model's own answer
  const injected = parsed.filter((c) => !c.aligned);
  const citedInjected = Object.fromEntries(RECORDS.map((r) => [r, injected.filter((c) => c.cited?.includes(r)).length])) as Record<string, number>;
  const scored = s.citations.filter((c) => c.kind === "sampled" && c.beatNec !== null);
  const scoredInjected = scored.filter((c) => !c.aligned).length;
  const misOrders = s.misalignedOrderings;
  const ownAnswers = [...new Set(misOrders.map((i) => s.orderings[i].fullArgmax))];
  const orderWords = misOrders.length === 1 ? `ordering ${misOrders[0]}` : `orderings ${misOrders.slice(0, -1).join(", ")} and ${misOrders[misOrders.length - 1]}`;

  return (
    <section className="section" id="citations" aria-labelledby="citations-title">
      <div className="wrap">
        <div className="section-head">
          <h2 id="citations-title">What the model says it used, next to what moved it</h2>
          <p>
            With all four records shown and the scenario&rsquo;s answer in place, the model was asked: &ldquo;Which evidence records did
            your answer rely on?&rdquo; It replied 13 times per scenario: 10 sampled replies and 3 greedy ones, one per ordering.
          </p>
        </div>

        <div className="cite-grid">
          <div>
            <div className="saydo-row saydo-head" aria-hidden="true">
              <span>{s.name} <Tag kind="observed" /></span>
              <span>What it says: cited in parsed replies</span>
              <span>What moves it: average pull on P({s.dStar})</span>
            </div>
            {RECORDS.map((r) => {
              const n = citedShare[r];
              const share = parsed.length ? n / parsed.length : 0;
              const sh = s.shapleySummary[r];
              const scale = (x: number) => 50 + x * 50; // -1..1 -> 0..100%
              return (
                <div className="saydo-row" key={r} data-record={r}>
                  <span className="saydo-rec">{r} {s.records[r].short}<small>{s.records[r].role ?? (s.records[r].rubric ? `Rubric points to ${s.records[r].rubric!.score > 0 ? "Positive" : "Negative"}` : "")}</small></span>
                  <span className="saydo-cell">
                    <span className="hbar" aria-hidden="true">
                      <span className="hbar-fill hbar-gold" style={{ left: 0, width: `${share * 100}%` }} />
                      {citedInjected[r] > 0 && (
                        <span className="hbar-fill hbar-injected" style={{ left: `${((n - citedInjected[r]) / parsed.length) * 100}%`, width: `${(citedInjected[r] / parsed.length) * 100}%` }} />
                      )}
                    </span>
                    <span className="saydo-val">{n}/{parsed.length}</span>
                    {citedInjected[r] > 0 && <span className="sr-only">, {citedInjected[r]} of them given for an injected decision</span>}
                  </span>
                  <span className="saydo-cell">
                    <span className="hbar hbar-signed" aria-hidden="true">
                      <span className="hbar-zero" />
                      <span className="hbar-fill hbar-navy" style={{ left: `${Math.min(scale(0), scale(sh.mean))}%`, width: `${Math.abs(sh.mean) * 50}%` }} />
                      <span className="hbar-range" style={{ left: `${scale(sh.min)}%`, width: `${Math.max(0.6, (sh.max - sh.min) * 50)}%` }} />
                    </span>
                    <span className="saydo-val">{signed(sh.mean)}</span>
                  </span>
                </div>
              );
            })}
            {injected.length > 0 && (
              <p className="inject-note inject-block">
                Hatched: {injected.length} of the {parsed.length} parsed replies come from {orderWords}, where the prompt told the model the
                answer was {s.dStar} but its own answer was {ownAnswers.join(" or ")}. They justify an injected decision, not its own.
              </p>
            )}
            <p className="lattice-caption">
              Gold: how many of the {parsed.length} parsed replies (of 13, sampled and greedy) named the record. Navy: the record&rsquo;s
              Shapley value, mean over the three orderings, with a thin line for the range across orderings (not a confidence interval).
              Pre-registered scores for this scenario, from the sampled replies only: the cited sets beat same-size alternatives on necessity
              {" "}<span className="num">{s.citationMetrics.mean_beat_nec.toFixed(2)}</span> and sufficiency
              {" "}<span className="num">{s.citationMetrics.mean_beat_suf.toFixed(2)}</span> on average
              ({s.citationMetrics.n_partial} partial citations{scoredInjected > 0 ? `, ${scoredInjected} of them for an injected decision` : ""}; 0.5 is chance).
            </p>
          </div>

          <div>
            <div className="ledger-cols" aria-hidden="true">
              <span>Reply</span>{RECORDS.map((r) => <span key={r}>{r}</span>)}<span>Score or note</span>
            </div>
            <div className="ledger">
              {s.orderings.map((o) => {
                const replies = s.citations.filter((c) => c.ordering === o.index);
                const misaligned = !replies[0]?.aligned;
                return (
                  <div className={`ledger-group ${view.ordering === o.index ? "is-current" : ""}`} key={o.index}>
                    <div className="ledger-group-head">
                      <b>Ordering {o.index}</b>
                      <span>prompt showed {s.dStar}; the model&rsquo;s own answer here: {o.fullArgmax}</span>
                      {misaligned && (
                        <span className="inject-note">Injected decision: these replies justify a label the model did not choose in this ordering</span>
                      )}
                      {view.ordering !== o.index && (
                        <button className="linkbtn" onClick={() => {
                          update({ ordering: o.index, mask: 15, showCitations: true });
                          document.getElementById("instrument")?.scrollIntoView({ behavior: "smooth", block: "start" });
                        }}>Show in the instrument</button>
                      )}
                    </div>
                    {replies.map((c, i) => <Reply key={i} c={c} n={replies.filter((x, j) => x.kind === "sampled" && j <= i).length} />)}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function Reply({ c, n }: { c: Citation; n: number }) {
  const label = c.kind === "greedy" ? "Greedy" : `Sample ${n}`;
  let note: React.ReactNode;
  if (c.status === "unparseable") note = "Could not be parsed";
  else if (c.category === "empty") note = "Empty list: no score";
  else if (c.category === "all") note = "Cites all four: no score";
  else note = <span className="num">beats {pct(c.beatNec)} of alternatives on necessity, {pct(c.beatSuf)} on sufficiency</span>;
  return (
    <div className="reply" data-status={c.status}>
      <span className="reply-kind">{label}</span>
      {RECORDS.map((r) => (
        <span key={r} role="img" className={`reply-cell ${c.status === "unparseable" ? "na" : c.cited?.includes(r) ? "on" : "off"}`}
          aria-label={c.status === "unparseable" ? `${r}: reply not parsed` : c.cited?.includes(r) ? `${r} cited` : `${r} not cited`}>
          {c.cited?.includes(r) ? r : ""}
        </span>
      ))}
      <span className="reply-meta">
        <details>
          <summary>{note}</summary>
          <p className="reply-raw">&ldquo;{c.raw.trim()}&rdquo;</p>
        </details>
      </span>
    </div>
  );
}

const pct = (x: number | null) => (x === null ? "n/a" : `${Math.round(x * 100)}%`);
