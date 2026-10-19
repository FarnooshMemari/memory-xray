import { useState } from "react";
import { Instrument } from "./components/Instrument";
import { ScenarioRail } from "./components/ScenarioRail";
import { LatticeSection } from "./components/LatticeSection";
import { CitationsSection } from "./components/CitationsSection";
import { InsightSection } from "./components/InsightSection";
import { AboutSection } from "./components/AboutSection";
import { Tour } from "./components/Tour";
import { Wordmark } from "./components/Glyphs";
import { FULL, scenarioById } from "./lib/model";
import { useMediaQuery, usePrefersReducedMotion, useView } from "./lib/state";

export function App() {
  const [view, update] = useView();
  const reduced = usePrefersReducedMotion();
  const narrow = useMediaQuery("(max-width: 860px)");
  const [touring, setTouring] = useState(false);
  const s = scenarioById(view.scenario);

  return (
    <>
      <a className="sr-only" href="#instrument">Skip to the instrument</a>
      <header className="masthead">
        <div className="wrap">
          <a className="wordmark" href="#top" onClick={(e) => { e.preventDefault(); window.scrollTo({ top: 0 }); }}>
            <Wordmark />
          </a>
          <nav className="nav" aria-label="Sections">
            <a href="#instrument">Instrument</a>
            <a href="#combinations">Every combination</a>
            <a href="#citations">What it says</a>
            <a href="#catch">The catch</a>
            <a href="#about">About the data</a>
          </nav>
        </div>
      </header>

      <main id="top">
        <section className="intro">
          <div className="wrap">
            <h1>Does a language model cite the evidence it actually uses?</h1>
            <div className="intro-side">
              <p>
                A small model read four evidence records and gave a one-word answer. We removed the records in every
                combination and saved how its answer moved. Then we asked which records it relied on.
              </p>
              <div className="intro-actions">
                <button className="btn" onClick={() => setTouring(true)}>
                  <span className="btn-play" aria-hidden="true" />Take the 40-second tour
                </button>
                <span className="intro-hint">or press any record below to remove it</span>
              </div>
            </div>
          </div>
        </section>

        <section className="instrument-section" id="instrument" aria-label="Instrument">
          <div className="wrap">
            <Instrument s={s} view={view} update={update} reduced={reduced} narrow={narrow}
              rail={<ScenarioRail current={s.id} onSelect={(id) => update({ scenario: id, mask: FULL })} />} />
          </div>
        </section>

        <LatticeSection s={s} view={view} update={update} reduced={reduced} />
        <CitationsSection s={s} view={view} update={update} />
        <InsightSection />
        <AboutSection />
      </main>

      <footer className="footer">
        <div className="wrap">
          <span>
            Memory X-Ray. Every number shown is read from the saved experiment files.{" "}
            <a href="https://github.com/FarnooshMemari/memory-xray">Code, data and report on GitHub</a>
          </span>
          <span>Farnoosh Memari, 2026</span>
        </div>
      </footer>

      {touring && <Tour onClose={() => setTouring(false)} update={update} reduced={reduced} />}
    </>
  );
}
