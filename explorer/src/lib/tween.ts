import { useEffect, useRef, useState } from "react";

const easeOutCubic = (t: number) => 1 - Math.pow(1 - t, 3);

/** Animates an array of numbers toward new targets (no animation when `instant`). */
export function useTween(target: number[], duration = 650, instant = false, startFromZero = false): number[] {
  const initial = startFromZero && !instant ? target.map(() => 0) : target;
  const [value, setValue] = useState(initial);
  const from = useRef(initial);
  const current = useRef(initial);
  const raf = useRef<number | null>(null);
  const key = target.map((x) => x.toFixed(9)).join(",");

  useEffect(() => {
    if (raf.current) cancelAnimationFrame(raf.current);
    if (instant) {
      current.current = target;
      setValue(target);
      return;
    }
    from.current = current.current;
    const start = performance.now();
    const step = (now: number) => {
      // requestAnimationFrame timestamps can precede `start` slightly; clamp so values never overshoot.
      const t = Math.min(1, Math.max(0, (now - start) / duration));
      const e = easeOutCubic(t);
      const next = target.map((x, i) => (from.current[i] ?? x) + (x - (from.current[i] ?? x)) * e);
      current.current = next;
      setValue(next);
      if (t < 1) raf.current = requestAnimationFrame(step);
    };
    raf.current = requestAnimationFrame(step);
    return () => { if (raf.current) cancelAnimationFrame(raf.current); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, instant, duration]);

  return value;
}
