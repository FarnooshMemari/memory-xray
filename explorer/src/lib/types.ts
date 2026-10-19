export type Label = "Positive" | "Neutral" | "Negative";
export type RecordId = "E1" | "E2" | "E3" | "E4";

export interface SubsetCell {
  /** Normalized probabilities in the order Positive, Neutral, Negative. */
  p: [number, number, number];
  argmax: Label;
  /** Answer the designed rule (controls) or the rubric (realistic) gives for this subset. */
  rule: Label;
}

export interface Ordering {
  index: number;
  /** Records in the order they were shown to the model, first to last. */
  order: RecordId[];
  /** Opaque IDs the model saw, e.g. E1 -> "R7". */
  ids: Record<RecordId, string>;
  /** Keyed by bitmask string "0".."15" (E1=1, E2=2, E3=4, E4=8). */
  subsets: Record<string, SubsetCell>;
  shapley: Record<RecordId, number>;
  loo: Record<RecordId, number>;
  fullArgmax: Label;
  designedAgreement: number;
}

export interface Range {
  mean: number;
  min: number;
  max: number;
  per_ordering: number[];
}

export interface Citation {
  ordering: number;
  kind: "sampled" | "greedy";
  seed: number | null;
  status: "ok" | "empty" | "unparseable";
  raw: string;
  cited: RecordId[] | null;
  category: "partial" | "all" | "empty" | null;
  beatNec: number | null;
  beatSuf: number | null;
  topk: number | null;
  shownLabel: Label;
  ownAnswer: Label;
  aligned: boolean;
}

export interface Scenario {
  id: string;
  name: string;
  blurb: string;
  kind: "control" | "realistic";
  structure: string;
  question: string;
  records: Record<RecordId, {
    text: string;
    short: string;
    role?: string;
    rubric?: { score: number; component: string; why: string };
  }>;
  dStar: Label;
  reference: Label;
  meanFullDist: [number, number, number];
  orderings: Ordering[];
  shapleySummary: Record<RecordId, Range>;
  looSummary: Record<RecordId, Range>;
  checks: { infraPass: boolean; recovery: { id: string; name: string; passed: boolean }[]; flags: string[] };
  citations: Citation[];
  citationMetrics: {
    n_analyzable: number; n_partial: number; mean_beat_nec: number; mean_beat_suf: number; mean_topk: number;
    share_beat_nec_gt_half: number; share_beat_suf_gt_half: number;
  };
  misalignedOrderings: number[];
  contentOnly: { set: RecordId[]; mean_beat_nec: number; mean_beat_suf: number; mean_topk: number };
  rubricIdealShapley?: Record<RecordId, number>;
  flip?: {
    target: RecordId; text: string; why: string; referenceAfter: Label;
    perOrdering: { ordering: number; pAfter: [number, number, number]; argmaxAfter: Label; pDStarBefore: number; pDStarAfter: number }[];
  };
}

export interface ExplorerData {
  meta: {
    title: string; runId: string; model: string; commit: string; device: string; elapsedSeconds: number;
    precision: string; labels: Label[]; records: RecordId[]; subsetEncoding: string; valueFunction: string;
    sources: { path: string; sha256: string }[]; handWritten: string;
  };
  pooled: {
    model: { n_analyzable: number; n_partial: number; mean_beat_nec: number; mean_beat_suf: number; mean_topk: number;
      share_beat_nec_gt_half: number; share_beat_suf_gt_half: number };
    sampledStatus: Record<string, number>; sampledTotal: number;
    greedyStatus: Record<string, number>; greedyTotal: number;
    aligned: { n_partial: number; mean_beat_nec: number; mean_beat_suf: number; mean_topk: number };
    misaligned: { n_partial: number; mean_beat_nec: number; mean_beat_suf: number; mean_topk: number;
      share_beat_nec_gt_half: number; share_beat_suf_gt_half: number };
    ownDecisionRescoring: { n: number; shown: [number, number]; own: [number, number] };
    contentOnly: { mean_beat_nec: number; mean_beat_suf: number; mean_topk: number };
    contentOnlyComparison: { higher: number; tied: number; lower: number; of: number;
      exceptions: { scenario: string; metric: string; content_only: number; model: number }[] };
    modelEqualsContentSet: { n: number; of: number };
  };
  scenarios: Scenario[];
}
