/** The wordmark: "Memory X-Ray", where the X is two crossing traces. */
export function Wordmark() {
  return (
    <span className="wordmark-name">
      <span className="sr-only">Memory X-Ray</span>
      <span aria-hidden="true">Memory </span>
      <svg className="wordmark-x" viewBox="0 0 20 20" aria-hidden="true">
        <path d="M2 3 C9 3 11 17 18 17" stroke="var(--navy)" strokeWidth="2.6" fill="none" strokeLinecap="round" />
        <path d="M2 17 C9 17 11 3 18 3" stroke="var(--royal)" strokeWidth="2.6" fill="none" strokeLinecap="round" opacity="0.75" />
      </svg>
      <span aria-hidden="true">-Ray</span>
    </span>
  );
}

export function KeyGlyph({ kind }: { kind: "slip" | "raise" | "lower" | "marker" | "zero" | "added" }) {
  if (kind === "slip") {
    return (
      <svg width="22" height="16" aria-hidden="true">
        <rect x="1" y="2" width="20" height="12" rx="3" fill="#eef2f8" stroke="#b9c2d1" />
        <rect x="4" y="5.5" width="5" height="5" rx="1.2" fill="var(--navy)" />
      </svg>
    );
  }
  if (kind === "marker") {
    return (
      <svg width="14" height="14" aria-hidden="true">
        <rect x="1.5" y="2.5" width="10" height="10" rx="2" fill="#f2c94c" stroke="#b98f00" strokeWidth="1.5" />
      </svg>
    );
  }
  if (kind === "added") {
    return (
      <svg width="30" height="16" aria-hidden="true">
        <path d="M3 8 H22" stroke="var(--trace)" strokeWidth="5" strokeDasharray="5 4" opacity="0.5" />
        <path d="M21 3 L28 8 L21 13 z" fill="var(--trace)" opacity="0.5" />
      </svg>
    );
  }
  if (kind === "zero") {
    return (
      <svg width="30" height="16" aria-hidden="true">
        <path d="M3 8 H27" stroke="var(--trace)" strokeWidth="1" strokeDasharray="3 3" opacity="0.7" />
      </svg>
    );
  }
  return (
    <svg width="30" height="16" aria-hidden="true">
      <path d="M3 8 H22" stroke="var(--trace)" strokeWidth="3" strokeLinecap="round" />
      {kind === "raise" ? <path d="M21 3.5 L28 8 L21 12.5 z" fill="var(--trace)" /> : <rect x="23" y="2" width="3" height="12" rx="1" fill="var(--trace)" />}
    </svg>
  );
}
