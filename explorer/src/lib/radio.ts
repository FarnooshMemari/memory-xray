import type { KeyboardEvent } from "react";

/**
 * Arrow-key handling for a radiogroup of buttons (the WAI-ARIA radio pattern): arrows, Home and End
 * move both the selection and the focus. Attach to the element with role="radiogroup".
 */
export function radioKeys<T>(e: KeyboardEvent<HTMLElement>, values: T[], current: T, select: (v: T) => void) {
  const i = values.indexOf(current);
  let j = -1;
  if (e.key === "ArrowRight" || e.key === "ArrowDown") j = (i + 1) % values.length;
  else if (e.key === "ArrowLeft" || e.key === "ArrowUp") j = (i - 1 + values.length) % values.length;
  else if (e.key === "Home") j = 0;
  else if (e.key === "End") j = values.length - 1;
  if (j < 0) return;
  e.preventDefault();
  select(values[j]);
  e.currentTarget.querySelectorAll<HTMLElement>('[role="radio"]')[j]?.focus();
}
