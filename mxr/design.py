"""Fixed experimental design for protocol v0.2.

Everything that defines a condition lives here as a literal constant, so the
design is reproducible without any random seed: the 16 evidence subsets, the
three fixed orderings, the opaque record IDs used in each ordering, and the
prompt templates.
"""
from __future__ import annotations

import hashlib
import json
from itertools import combinations

CANONICAL = ("E1", "E2", "E3", "E4")
LABELS = ("Positive", "Neutral", "Negative")

# The assistant turn is forced to start with this prefix; each label is then
# scored as the continuation " <Label>".
ANSWER_PREFIX = "Signal:"
LABEL_CONTINUATIONS = tuple(" " + label for label in LABELS)

# Three fixed orderings (indices into CANONICAL). Across the three orderings
# every record occupies three different positions:
#   E1 -> 0,1,3   E2 -> 1,3,2   E3 -> 2,0,1   E4 -> 3,2,0
ORDERINGS = (
    (0, 1, 2, 3),
    (2, 0, 3, 1),
    (3, 2, 1, 0),
)

# Opaque IDs shown to the model, re-mapped in each ordering so that an ID label,
# a position and a record's content never coincide across orderings.
OPAQUE_IDS = (
    {"E1": "R7", "E2": "R3", "E3": "R9", "E4": "R5"},
    {"E1": "R2", "E2": "R8", "E3": "R4", "E4": "R6"},
    {"E1": "R5", "E2": "R1", "E3": "R7", "E4": "R3"},
)

USER_TEMPLATE = (
    "You are a macro-financial analyst. Read the question and the evidence "
    "records, then give a signal.\n"
    "Base your answer only on the evidence records below. If the records do "
    "not settle the question, answer Neutral.\n"
    "\n"
    "Question: {question}\n"
    "\n"
    "Evidence records:\n"
    "{records_block}\n"
    "\n"
    "Answer with exactly one word: Positive, Neutral, or Negative."
)
EMPTY_RECORDS_LINE = "(no evidence records provided)"

CITATION_FOLLOWUP = (
    "Which evidence records did your answer rely on? Reply with only a JSON "
    "list of the record IDs, written exactly as they appear in brackets "
    '(for example: ["Rx", "Ry"]). Reply [] if your answer did not rely on '
    "any record."
)


def all_subsets(players=CANONICAL):
    """All 2^n subsets as frozensets, ordered by size then canonical order."""
    out = []
    for r in range(len(players) + 1):
        for combo in combinations(players, r):
            out.append(frozenset(combo))
    return out


def subset_key(subset) -> str:
    """Stable ASCII key, e.g. 'E1+E3' or 'none'."""
    members = [p for p in CANONICAL if p in subset]
    return "+".join(members) if members else "none"


def parse_subset_key(key: str) -> frozenset:
    return frozenset() if key == "none" else frozenset(key.split("+"))


def subset_mask(subset) -> int:
    return sum(1 << i for i, p in enumerate(CANONICAL) if p in subset)


def render(scenario: dict, subset, ordering_idx: int, records: dict | None = None) -> dict:
    """Render the user message for one (subset, ordering) cell.

    Removed records are deleted (not replaced by placeholders); the remaining
    records keep their relative order from the chosen fixed ordering.
    ``records`` overrides the scenario's record texts (used for flip variants).
    """
    texts = scenario["records"] if records is None else records
    order = [CANONICAL[i] for i in ORDERINGS[ordering_idx]]
    ids = OPAQUE_IDS[ordering_idx]
    shown = [rec for rec in order if rec in subset]
    if shown:
        records_block = "\n".join(
            f"[{ids[rec]}] {texts[rec]}" for rec in shown
        )
    else:
        records_block = EMPTY_RECORDS_LINE
    user_msg = USER_TEMPLATE.format(
        question=scenario["question"], records_block=records_block
    )
    return {
        "user_msg": user_msg,
        "shown_canonical": shown,
        "shown_ids": [ids[rec] for rec in shown],
        "id_to_canonical": {ids[rec]: rec for rec in CANONICAL},
        "positions": {rec: shown.index(rec) for rec in shown},
    }


def flip_records(scenario: dict) -> dict:
    """Record texts with the pre-specified flip applied (realistic scenarios)."""
    flip = scenario["flip"]
    out = dict(scenario["records"])
    out[flip["target"]] = flip["record"]
    return out


def rubric_total(scenario: dict, subset, flipped: bool = False) -> int:
    scores = {r: v["score"] for r, v in scenario["rubric"]["scores"].items()}
    if flipped:
        scores[scenario["flip"]["target"]] = scenario["flip"]["score"]
    return sum(scores[r] for r in subset)


def designed_answer(scenario: dict, subset, flipped: bool = False) -> str:
    """Answer implied by the scenario's predefined rule (synthetic) or rubric (realistic)."""
    rule = scenario["designed"]["answer_rule"]
    kind = rule["type"]
    if flipped and kind != "rubric":
        raise ValueError("flips exist only for rubric scenarios")
    if kind == "contains_any":
        hit = any(rec in subset for rec in rule["records"])
        return rule["if_true"] if hit else rule["if_false"]
    if kind == "precedence":
        for step in rule["order"]:
            if step["record"] in subset:
                return step["answer"]
        return rule["default"]
    if kind == "rubric":
        total = rubric_total(scenario, subset, flipped)
        th = rule["thresholds"]
        if total >= th["positive_min"]:
            return "Positive"
        if total <= th["negative_max"]:
            return "Negative"
        return "Neutral"
    raise NotImplementedError(f"rule type {kind!r} not implemented")


def design_fingerprint(scenario: dict) -> str:
    """SHA-256 over the scenario and every design constant that shapes a prompt."""
    payload = {
        "scenario": scenario,
        "labels": LABELS,
        "answer_prefix": ANSWER_PREFIX,
        "label_continuations": LABEL_CONTINUATIONS,
        "orderings": ORDERINGS,
        "opaque_ids": OPAQUE_IDS,
        "user_template": USER_TEMPLATE,
        "empty_line": EMPTY_RECORDS_LINE,
        "citation_followup": CITATION_FOLLOWUP,
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=True).encode()
    return hashlib.sha256(blob).hexdigest()


def faithful_citations(scenario: dict) -> list:
    """Designed faithful citation sets (synthetic controls). S-single, frozen before
    amendment 2, stores a single set under 'faithful_citation'."""
    d = scenario.get("designed", {})
    if "faithful_citations" in d:
        return [list(x) for x in d["faithful_citations"]]
    if "faithful_citation" in d:
        return [list(d["faithful_citation"])]
    return []
