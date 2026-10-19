import { useCallback, useEffect, useState } from "react";
import { DATA, FULL } from "./model";
import type { RecordId } from "./types";

export interface View {
  scenario: string;
  ordering: number;
  mask: number;
  focus: RecordId | null;
  showCitations: boolean;
}

const DEFAULT: View = { scenario: "s_single", ordering: 0, mask: FULL, focus: null, showCitations: false };

/** URL hash format: #s_redundant/o0/m15 (scenario / ordering / record mask). */
function parse(hash: string): Partial<View> {
  const m = hash.replace(/^#/, "").match(/^([a-z_]+)\/o([0-2])\/m(\d{1,2})$/);
  if (!m) return {};
  const scenario = DATA.scenarios.some((s) => s.id === m[1]) ? m[1] : undefined;
  const mask = Number(m[3]);
  return { ...(scenario ? { scenario } : {}), ordering: Number(m[2]), ...(mask >= 0 && mask <= 15 ? { mask } : {}) };
}

export function useView() {
  const [view, setView] = useState<View>(() => ({ ...DEFAULT, ...parse(window.location.hash) }));

  useEffect(() => {
    const h = `#${view.scenario}/o${view.ordering}/m${view.mask}`;
    if (window.location.hash !== h) window.history.replaceState(null, "", h);
  }, [view.scenario, view.ordering, view.mask]);

  useEffect(() => {
    const onHash = () => setView((v) => ({ ...v, ...parse(window.location.hash) }));
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const update = useCallback((patch: Partial<View>) => setView((v) => ({ ...v, ...patch })), []);
  return [view, update] as const;
}

export function usePrefersReducedMotion() {
  const q = "(prefers-reduced-motion: reduce)";
  const [reduced, setReduced] = useState(() => typeof window !== "undefined" && window.matchMedia(q).matches);
  useEffect(() => {
    const mq = window.matchMedia(q);
    const on = () => setReduced(mq.matches);
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);
  return reduced;
}

export function useMediaQuery(q: string) {
  const [match, setMatch] = useState(() => typeof window !== "undefined" && window.matchMedia(q).matches);
  useEffect(() => {
    const mq = window.matchMedia(q);
    const on = () => setMatch(mq.matches);
    on();
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, [q]);
  return match;
}
