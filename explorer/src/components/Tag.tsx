const TEXT = { observed: "Observed", interpretation: "Interpretation", limitation: "Limitation", posthoc: "Post hoc" } as const;
const TITLE = {
  observed: "Read directly from the saved experiment results",
  interpretation: "What we think the results mean; not itself a measurement",
  limitation: "What the study cannot show",
  posthoc: "Defined after the results were seen; exploratory",
} as const;

export function Tag({ kind }: { kind: keyof typeof TEXT }) {
  return (
    <span className={`tag tag-${kind}`} title={TITLE[kind]}>
      <i aria-hidden="true" />{TEXT[kind]}
    </span>
  );
}
